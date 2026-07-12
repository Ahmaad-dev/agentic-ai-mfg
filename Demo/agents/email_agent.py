"""Conversational email agent: draft, revise, preview, then explicitly send."""
from __future__ import annotations

import html
import json
import logging
import os
import re
from typing import Dict, Optional

from agent_config import CHAT_HISTORY_CONFIG, DEFAULT_EMAIL_SYSTEM_PROMPT
from db import repository as repo
from mcp_connections import tools as email_tools

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_PROPOSAL_ID_RE = re.compile(r"[0-9a-fA-F-]{36}__iteration-\d+")
_SNAPSHOT_ID_RE = re.compile(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b")
_CASE_WORDS_RE = re.compile(
    r"\b(snapshot|fehler|validierung|review|proposal|vorschlag|case|korrektur|problem|"
    r"dazu|darüber|hierzu|damit)\b",
    re.IGNORECASE,
)
_SEND_RE = re.compile(
    r"\b(absenden|versenden|jetzt\s+senden|bitte\s+senden|schick(?:e)?\s+.*\s+ab)\b",
    re.IGNORECASE,
)
_CANCEL_RE = re.compile(
    r"\b(abbrechen|verwerfen|entwurf\s+löschen|nicht\s+(?:ab)?senden|doch\s+nicht)\b",
    re.IGNORECASE,
)
_APPROVAL_ONLY_RE = re.compile(
    r"^\s*(?:(?:ja|passt|okay|ok|in ordnung|sieht gut aus)[,;.!\s]*)+$",
    re.IGNORECASE,
)


class EmailAgent(BaseAgent):
    """Creates persistent previews and sends only after an explicit second-turn command."""

    def __init__(
        self,
        aoai_client,
        model_name: str,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        routing_description: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1800,
        max_history_pairs: int = 5,
    ):
        super().__init__(
            name="Email",
            system_prompt=system_prompt or DEFAULT_EMAIL_SYSTEM_PROMPT,
            description=description,
            routing_description=routing_description,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_pairs=max_history_pairs,
        )
        self.aoai_client = aoai_client
        self.model_name = model_name

    @staticmethod
    def _html_from_plain(body: str) -> str:
        paragraphs = []
        for part in re.split(r"\n\s*\n", body.strip()):
            paragraphs.append(f"<p>{html.escape(part).replace(chr(10), '<br>')}</p>")
        return "".join(paragraphs)

    @staticmethod
    def _preview(draft: dict, intro: str = "Hier ist der E-Mail-Entwurf:") -> str:
        return (
            f"{intro}\n\n"
            f"**Empfänger:** `{draft['recipient']}`  \n"
            f"**Betreff:** {draft['subject']}  \n"
            f"**Entwurf:** `{draft['draft_id']}` · Version {draft['version']}\n\n"
            f"---\n\n{draft['body_plain']}\n\n---\n\n"
            "Bitte prüfe Empfänger, Betreff und Inhalt. Du kannst Änderungen nennen. "
            "Gesendet wird erst, wenn du ausdrücklich **„Bitte absenden“** schreibst."
        )

    def _case_context(self, user_input: str, chat_history: list) -> str:
        if not _CASE_WORDS_RE.search(user_input):
            return ""
        combined = "\n".join(
            [msg.get("content", "") for msg in chat_history[-10:]] + [user_input]
        )
        proposal_ids = list(dict.fromkeys(_PROPOSAL_ID_RE.findall(combined)))
        snapshot_ids = list(dict.fromkeys(_SNAPSHOT_ID_RE.findall(combined)))
        context: dict = {"proposals": [], "snapshots": []}
        base_url = (os.getenv("APP_BASE_URL") or "http://localhost:8000").rstrip("/")

        for proposal_id in proposal_ids[:3]:
            result = email_tools.get_review_details(proposal_id)
            if result.get("ok"):
                proposal = result["proposal"]
                context["proposals"].append(
                    {
                        "proposal_id": proposal_id,
                        "snapshot_id": proposal.get("snapshot_id"),
                        "error_type": proposal.get("error_type"),
                        "target_path": proposal.get("target_path"),
                        "status": proposal.get("status"),
                        "reasoning": proposal.get("reasoning"),
                        "suggested_value": proposal.get("suggested_value"),
                        "review_link": f"{base_url}/review.html?id={proposal_id}",
                    }
                )
                snapshot_id = proposal.get("snapshot_id")
                if snapshot_id and snapshot_id not in snapshot_ids:
                    snapshot_ids.append(snapshot_id)

        for snapshot_id in snapshot_ids[:3]:
            result = email_tools.get_snapshot_status(snapshot_id)
            if result.get("ok"):
                context["snapshots"].append(result)

        if not context["proposals"] and not context["snapshots"]:
            return ""
        return json.dumps(context, ensure_ascii=False, default=str)[:12000]

    def _compose(self, user_input: str, chat_history: list, active: Optional[dict]) -> tuple[dict, dict]:
        case_context = self._case_context(user_input, chat_history)
        operation = "revise" if active else "create"
        prompt = f"""
Operation: {operation}
User request: {user_input}

Recent conversation:
{json.dumps(chat_history[-10:], ensure_ascii=False)}

Current draft (null means create a new one):
{json.dumps(active, ensure_ascii=False, default=str) if active else 'null'}

Structured snapshot/review context (empty means do not invent any):
{case_context or 'none'}

Return ONLY one JSON object with:
{{
  "needs_clarification": false,
  "clarification": "",
  "recipient": "email address",
  "subject": "concise subject",
  "body_plain": "complete send-ready email body",
  "context_summary": "short note naming which context was used"
}}

Rules:
- Follow the current user request; do not include snapshot information unless requested.
- For revise, preserve every current-draft field the user did not ask to change.
- Never invent an email address, case fact, decision, value, or link.
- If recipient or purpose is missing, set needs_clarification=true and ask one clear question.
- Produce a draft only. Never claim that it was sent.
"""
        response = self.aoai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.choices[0].message.content)
        usage = {
            "tokens_prompt": getattr(response.usage, "prompt_tokens", None),
            "tokens_completion": getattr(response.usage, "completion_tokens", None),
            "tokens_total": getattr(response.usage, "total_tokens", None),
        }
        return payload, usage

    def execute(self, user_input: str, context: Dict = None) -> Dict:
        context = context or {}
        session_id = context.get("db_session_id")
        if session_id is None:
            return {
                "response": "Für einen E-Mail-Entwurf fehlt die persistente Chat-Session.",
                "metadata": {"agent": "email", "success": True, "email_status": "error"},
            }
        session_id = int(session_id)
        chat_history = self._get_chat_history(context)
        active = repo.get_latest_email_draft_for_session(session_id, status="draft")

        # A negative instruction must win even if it also contains "absenden".
        if active and _CANCEL_RE.search(user_input):
            result = email_tools.cancel_email_draft(active["draft_id"])
            return {
                "response": "Der E-Mail-Entwurf wurde verworfen.",
                "metadata": {
                    "agent": "email",
                    "success": True,
                    "email_status": "cancelled",
                    "draft_id": active["draft_id"],
                },
            }

        if active and _SEND_RE.search(user_input):
            result = email_tools.send_email_draft(active["draft_id"], confirmed=True)
            if result.get("ok"):
                sent = result["draft"]
                return {
                    "response": (
                        f"E-Mail wurde an `{sent['recipient']}` gesendet.  \n"
                        f"**Betreff:** {sent['subject']}"
                    ),
                    "metadata": {
                        "agent": "email",
                        "success": True,
                        "email_status": "sent",
                        "draft_id": sent["draft_id"],
                    },
                }
            return {
                "response": f"Die E-Mail wurde nicht gesendet: {result.get('error', 'unbekannter Fehler')}",
                "metadata": {
                    "agent": "email",
                    "success": True,
                    "email_status": "send_failed",
                    "draft_id": active["draft_id"],
                },
            }

        if active and _APPROVAL_ONLY_RE.match(user_input):
            return {
                "response": self._preview(
                    active,
                    "Der Entwurf bleibt unverändert. Zum Versand fehlt noch deine explizite Freigabe:",
                ),
                "metadata": {
                    "agent": "email",
                    "success": True,
                    "email_status": "draft",
                    "draft_id": active["draft_id"],
                },
            }

        try:
            payload, usage = self._compose(user_input, chat_history, active)
        except Exception as exc:
            logger.exception("Email composition failed")
            return {
                "response": f"Der E-Mail-Entwurf konnte nicht erstellt werden: {exc}",
                "metadata": {"agent": "email", "success": True, "email_status": "error"},
            }

        if payload.get("needs_clarification"):
            return {
                "response": payload.get("clarification") or "Welche Empfängeradresse soll ich verwenden?",
                "metadata": {
                    "agent": "email",
                    "success": True,
                    "email_status": "needs_clarification",
                    **usage,
                },
            }

        body_plain = str(payload.get("body_plain") or "").strip()
        values = {
            "recipient": str(payload.get("recipient") or "").strip(),
            "subject": str(payload.get("subject") or "").strip(),
            "body_plain": body_plain,
            "body_html": self._html_from_plain(body_plain),
            "context_summary": str(payload.get("context_summary") or "").strip(),
        }
        if active:
            result = email_tools.revise_email_draft(active["draft_id"], **values)
        else:
            result = email_tools.create_email_draft(session_id=session_id, **values)
        if not result.get("ok"):
            return {
                "response": f"Der E-Mail-Entwurf konnte nicht gespeichert werden: {result.get('error')}",
                "metadata": {"agent": "email", "success": True, "email_status": "error", **usage},
            }
        draft = result["draft"]
        return {
            "response": self._preview(draft),
            "metadata": {
                "agent": "email",
                "success": True,
                "email_status": "draft",
                "draft_id": draft["draft_id"],
                **usage,
            },
        }
