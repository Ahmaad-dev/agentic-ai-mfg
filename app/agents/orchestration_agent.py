"""
OrchestrationAgent - Koordiniert alle Sub-Agenten
"""
import json
import logging
import re
from typing import Dict, List, Optional
from .base_agent import BaseAgent
# Die bekannten Werkzeug-/Pipeline-Namen — Grundlage fuer _intent_from_plan
from .sp_tools_config import SP_TOOLS, SP_PIPELINES
# Sitzungsgebundener Snapshot-Bezug (siehe _snapshot_in_focus)
from memory import short_term
from core.agent_config import (
    CHAT_HISTORY_CONFIG,
    DEFAULT_ORCHESTRATOR_SYSTEM_PROMPT,
    DEFAULT_ORCHESTRATOR_PLANNING_PROMPT,
    DEFAULT_ORCHESTRATOR_INTERPRETATION_PROMPT,
    DEFAULT_ORCHESTRATOR_MULTISTEP_SUMMARY_PROMPT,
    DEFAULT_ORCHESTRATOR_SUBAGENT_INTERPRETATION_PROMPT,
    DEFAULT_ORCHESTRATOR_SP_INTENT_PROMPT,
    DEFAULT_ORCHESTRATOR_SP_RESULT_INTERPRETATION_PROMPT,
    HUMAN_IN_THE_LOOP,
    APP_BASE_URL
)

logger = logging.getLogger(__name__)

_EMAIL_FOLLOWUP_RE = re.compile(
    r"\b(absenden|versenden|senden|abbrechen|verwerfen|ändern|aendern|anpassen|"
    r"ergänzen|ergaenzen|kürzer|kuerzer|länger|laenger|betreff|empfänger|empfaenger|"
    r"formeller|lockerer|passt|okay|ok|in ordnung)\b",
    re.IGNORECASE,
)


class OrchestrationAgent(BaseAgent):
    """Orchestration Agent - Koordiniert alle Sub-Agenten"""
    
    def __init__(
        self,
        aoai_client,
        model_name: str,
        agents: Dict[str, BaseAgent],
        router_temperature: float = None,
        router_max_tokens: int = None,
        system_prompt: str = None,
        interpretation_system_prompt: str = None
    ):
        """
        Args:
            aoai_client: Azure OpenAI Client
            model_name: Deployment-Name des Modells
            agents: Dictionary der verfügbaren Agenten {"chat": ChatAgent, "rag": RAGAgent, "sp": SPAgent}
            router_temperature: Temperature für Routing (default: 0 = deterministisch)
            router_max_tokens: Max Tokens für Router-Antwort
            system_prompt: System Prompt für Orchestrator-Routing (optional, default aus agent_config)
            interpretation_system_prompt: System Prompt für Sub-Agent-Interpretation (optional, default aus agent_config)
        """
        # System Prompt aus Config (zentralisiert)
        system_prompt = system_prompt or DEFAULT_ORCHESTRATOR_SYSTEM_PROMPT
        
        super().__init__(
            name="Orchestrator",
            system_prompt=system_prompt,
            temperature=router_temperature
        )
        
        self.aoai_client = aoai_client
        self.model_name = model_name
        self.agents = agents
        self.router_max_tokens = router_max_tokens or CHAT_HISTORY_CONFIG["router_max_tokens"]
        self.router_temperature = router_temperature if router_temperature is not None else CHAT_HISTORY_CONFIG["router_temperature"]
        # Interpretation Prompt aus Config (zentralisiert)
        self.interpretation_system_prompt = (
            interpretation_system_prompt or DEFAULT_ORCHESTRATOR_INTERPRETATION_PROMPT
        )
        self.agentic_mode = True  # Aktiviert Multi-Step Planning
        #: Sitzungs-id des laufenden Aufrufs. Wird in `execute()` gesetzt; alles, was den
        #: Snapshot-Bezug betrifft, haengt daran statt am Objekt (siehe short_term).
        self._session_id = None
        # AP2.5: Request-scoped token accumulator (reset in execute() per call)
        self._tok_prompt = 0
        self._tok_completion = 0

    def _track_usage(self, usage) -> None:
        """AP2.5: Add LLM usage to the per-request accumulator (safe if usage is None)."""
        if usage is None:
            return
        self._tok_prompt += getattr(usage, "prompt_tokens", 0) or 0
        self._tok_completion += getattr(usage, "completion_tokens", 0) or 0
    
    def _create_execution_plan(self, user_input: str, chat_history: List) -> Dict:
        """Erstellt einen Multi-Step Execution Plan für komplexe Anfragen"""
        
        # Kontext für bessere Planung
        # Nutze max_planning_pairs aus Config für konsistente History-Länge
        max_planning_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_planning_pairs * 2):]  # 2 Paare = 4 Messages
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:max_chars]}"
                for msg in recent
            ])
        
        # Verfügbare Agenten und ihre Capabilities (DETAILLIERT)
        agent_capabilities_list = []
        for key, agent in self.agents.items():
            # Vollständige routing_description für detaillierte Planning-Infos
            agent_capabilities_list.append(
                f"**Agent: {key}**\n{agent.routing_description}"
            )
        agent_capabilities = "\n".join(agent_capabilities_list)
        
        # Nutze zentralen Planning Prompt aus agent_config
        planning_prompt = DEFAULT_ORCHESTRATOR_PLANNING_PROMPT.format(
            context_summary=context_summary,
            user_input=user_input,
            agent_capabilities=agent_capabilities
        )
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Execution Planner. Antworte nur mit JSON."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=CHAT_HISTORY_CONFIG["planning_temperature"],
                max_tokens=CHAT_HISTORY_CONFIG["max_planning_tokens"] 
            )
            self._track_usage(response.usage)  # AP2.5
            
            output = response.choices[0].message.content.strip()
            
            # JSON bereinigen
            if output.startswith("```json"):
                output = output[7:]
            if output.startswith("```"):
                output = output[3:]
            if output.endswith("```"):
                output = output[:-3]
            
            plan = json.loads(output.strip())
            
            logger.info(f"[{self.name}] Execution Plan erstellt: {plan['type']}")
            if plan['type'] == 'multi_step':
                logger.info(f"[{self.name}] Plan mit {len(plan.get('steps', []))} Schritten")
            
            return plan
            
        except Exception as e:
            logger.error(f"[{self.name}] Planning fehlgeschlagen: {e}")
            # Fallback: Single-Step mit Chat
            return {
                "type": "single_step",
                "agent": "chat",
                "reasoning": f"Planning-Fehler, Fallback zu Chat: {str(e)}"
            }
    
    def _execute_plan(
        self, plan: Dict, user_input: str, chat_history: List, request_context: Dict = None
    ) -> Dict:
        """Führt einen Multi-Step Execution Plan aus"""
        
        plan_type = plan.get("type")
        
        # Single-Step: Direkt an Agent weiterleiten
        if plan_type == "single_step":
            agent_key = plan.get("agent")
            if agent_key not in self.agents:
                return {
                    "response": f"Fehler: Agent '{agent_key}' nicht gefunden",
                    "metadata": {"error": "unknown_agent"}
                }
            
            # SP_Agent → NEUE direkte Execution
            if agent_key == "sp":
                logger.info(f"[{self.name}] Single-Step Execution mit SP_Agent (NEUE Methode)")
                sp_context = dict(request_context or {})
                sp_context["chat_history"] = chat_history
                # Der Plan benennt das Werkzeug bereits — mitgeben, damit der SP-Pfad es
                # nicht ein zweites Mal per LLM herleiten muss.
                sp_context["execution_plan"] = plan
                return self._execute_sp_agent(user_input, chat_history, sp_context)
            
            # Chat/RAG → Alte Methode (behält execute())
            agent = self.agents[agent_key]
            
            # Erweitere Kontext mit letzten Snapshot-Metadaten (für Chat Agent)
            enhanced_context = dict(request_context or {})
            enhanced_context["chat_history"] = chat_history
            if agent_key == "chat":
                # FRISCH lesen, nicht zwischengespeichert: der Zustand aendert sich durch
                # Anwenden, Hochladen und Freigaben — und zwar ausserhalb dieses Objekts.
                meta = self._current_snapshot_metadata(chat_history, user_input)
                if meta:
                    enhanced_context["last_snapshot_metadata"] = meta
                    logger.info(f"[{self.name}] Snapshot-Metadaten (frisch gelesen) an Chat Agent")

            # Review-Entscheidungen mitgeben: Die Chat-History enthaelt nur den KI-VORSCHLAG.
            # Die menschliche Entscheidung faellt im Review Board, ausserhalb des Chats - ohne
            # diesen Kontext berichtet der Chat den verworfenen KI-Wert als "die Loesung".
            if agent_key == "chat":
                decisions = self._get_review_decisions(chat_history, user_input)
                if decisions:
                    enhanced_context["review_decisions"] = decisions
                    logger.info(
                        f"[{self.name}] {len(decisions)} Review-Entscheidung(en) an Chat Agent weitergegeben"
                    )
                offen = self._open_proposals_for_focus(chat_history, user_input)
                if offen:
                    enhanced_context["open_proposals"] = offen
                    logger.info(f"[{self.name}] {len(offen)} offene(r) Vorschlag/Vorschlaege an Chat Agent")


            result = agent.execute(user_input, enhanced_context)

            # DURCHREICHEN statt nachformulieren (15.08.2026).
            #
            # Der Grundgedanke der Nachformulierung war, dass der Orchestrator ergaenzen
            # kann, was der Sub-Agent nicht wusste. Gemessen ist es umgekehrt: der
            # Nachformulierungsschritt sieht 3 Nachrichten a 200 Zeichen, der Chat-Agent
            # 10 a 1000 — und der Chat-Agent bekommt zusaetzlich Snapshot-Zustand,
            # Review-Entscheidungen und offene Vorschlaege, von denen die Nachformulierung
            # nichts sieht. Sie kann also nichts hinzufuegen, nur weglassen oder
            # dazuerfinden. Beide Falschaussagen vom 14.08.2026 sind so entstanden.
            #
            # Fuer den SP-Pfad gilt das NICHT und dort bleibt die Schicht: der SP-Agent
            # waehlt nur das Werkzeug, die Antwort entsteht erst aus dem Werkzeugergebnis.
            # Siehe `_interpret_sp_result`.
            #
            # E-Mail war schon vorher ausgenommen: Entwuerfe sind Freigabe-Artefakte, an
            # denen kein Wort still veraendert werden darf.
            if agent_key in ("email", "chat", "rag"):
                result.setdefault("metadata", {})["execution_plan"] = plan
                return result
            
            # WICHTIG: Extrahiere recovery_suggestion BEVOR Interpretation (sonst geht sie verloren!)
            recovery_hint = None
            raw_response = result.get("response", {})
            if isinstance(raw_response, dict):
                recovery_hint = raw_response.get("recovery_suggestion")
                if recovery_hint:
                    logger.info(f"[{self.name}] Recovery-Suggestion gefunden: {recovery_hint[:100]}")
                    # Speichere in metadata für Re-Planning Loop
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["recovery_suggestion"] = recovery_hint
            
            # Interpretation
            interpreted_response = self._interpret_subagent_result(
                user_input=user_input,
                agent_name=agent_key,
                agent_result=result,
                chat_history=chat_history
            )
            result["response"] = interpreted_response
            result["metadata"]["execution_plan"] = plan
            
            return result
        
        # Multi-Step: Schrittweise Ausführung
        if plan_type == "multi_step":
            steps = plan.get("steps", [])
            step_results = []
            accumulated_context = dict(request_context or {})
            accumulated_context.update({"chat_history": chat_history, "step_outputs": {}})
            
            logger.info(f"[{self.name}] Starte Multi-Step Execution mit {len(steps)} Schritten")
            
            for step in steps:
                step_num = step.get("step")
                agent_key = step.get("agent")
                action = step.get("action")
                depends_on = step.get("depends_on", [])
                
                logger.info(f"[{self.name}] Schritt {step_num}/{len(steps)}: {action} (Agent: {agent_key})")
                
                # Prüfe ob Agent existiert
                if agent_key not in self.agents:
                    error_msg = f"Fehler in Schritt {step_num}: Agent '{agent_key}' nicht gefunden"
                    logger.error(f"[{self.name}] {error_msg}")
                    return {
                        "response": error_msg,
                        "metadata": {
                            "error": "plan_execution_failed",
                            "failed_step": step_num,
                            "completed_steps": step_results
                        }
                    }
                
                # Dependency Context erstellen
                dependency_context = ""
                if depends_on:
                    for dep_step in depends_on:
                        if dep_step in accumulated_context["step_outputs"]:
                            prev_result = accumulated_context["step_outputs"][dep_step]
                            dependency_context += f"\n\nErgebnis von Schritt {dep_step}:\n{prev_result[:500]}"
                
                # Agent-spezifischer Input erstellen
                agent_input = action
                if dependency_context:
                    agent_input = f"{action}\n\nKONTEXT AUS VORHERIGEN SCHRITTEN:{dependency_context}"
                
                # SP_Agent → NEUE direkte Execution
                if agent_key == "sp":
                    logger.info(f"[{self.name}] Multi-Step Schritt {step_num}: SP_Agent (NEUE Methode)")
                    result = self._execute_sp_agent(agent_input, chat_history, accumulated_context)
                else:
                    # Chat/RAG → Alte Methode
                    agent = self.agents[agent_key]
                    result = agent.execute(agent_input, accumulated_context)
                
                # Ergebnis speichern
                response_text = result.get("response", "")
                if isinstance(response_text, dict):
                    # Bei rohen Tool-Outputs (SP_Agent)
                    response_text = response_text.get("stdout", str(response_text))[:1000]
                
                step_results.append({
                    "step": step_num,
                    "agent": agent_key,
                    "action": action,
                    "success": result.get("metadata", {}).get("success", True),
                    "response": response_text
                })
                
                # Context für nächste Schritte aktualisieren
                accumulated_context["step_outputs"][step_num] = response_text
                
                # Bei Fehler: Prüfe recovery_suggestion
                if not result.get("metadata", {}).get("success", True):
                    logger.warning(f"[{self.name}] Schritt {step_num} fehlgeschlagen")
                    
                    # Hole recovery_suggestion aus der Response
                    recovery_hint = None
                    if isinstance(result.get("response"), dict):
                        recovery_hint = result["response"].get("recovery_suggestion")
                    
                    if recovery_hint:
                        logger.info(f"[{self.name}] Recovery-Vorschlag verfügbar: {recovery_hint[:200]}")
                        # Speichere für finale Interpretation
                        step_results[-1]["recovery_suggestion"] = recovery_hint
                    
                    # Breche ab (User kann dann basierend auf recovery_suggestion neu planen)
                    break
            
            # Finale Interpretation aller Schritte
            summary = self._summarize_multi_step_execution(
                user_input=user_input,
                plan=plan,
                step_results=step_results,
                chat_history=chat_history
            )
            
            # Prüfe ob ein Schritt eine recovery_suggestion hat
            final_recovery = None
            for step_result in step_results:
                if "recovery_suggestion" in step_result:
                    final_recovery = step_result["recovery_suggestion"]
                    break
            
            metadata = {
                "agent": "Orchestrator",  # Multi-Step → Orchestrator
                "execution_plan": plan,
                "completed_steps": step_results,
                "total_steps": len(steps),
                "agentic_execution": True
            }
            
            # Füge recovery_suggestion hinzu falls vorhanden
            if final_recovery:
                metadata["recovery_suggestion"] = final_recovery
                logger.info(f"[{self.name}] Multi-Step Recovery-Suggestion weitergeleitet: {final_recovery[:100]}")
            
            return {
                "response": summary,
                "metadata": metadata
            }
        
        # Unbekannter Plan-Typ
        return {
            "response": f"Fehler: Unbekannter Plan-Typ '{plan_type}'",
            "metadata": {"error": "invalid_plan_type"}
        }
    
    def _summarize_multi_step_execution(
        self,
        user_input: str,
        plan: Dict,
        step_results: List[Dict],
        chat_history: List
    ) -> str:
        """Fasst die Multi-Step Execution zusammen"""
        
        # Kontext - nutze zentrale Config
        max_summary_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_summary_pairs * 2):]
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:100]}"
                for msg in recent
            ])
        
        # Schritte zusammenfassen. Die Grenze steht in der Config, nicht hier: bei 200
        # Zeichen fiel der entscheidende Teil der Teilantwort weg (siehe Kommentar dort).
        max_step_chars = CHAT_HISTORY_CONFIG.get("max_step_result_chars", 1200)
        steps_summary = ""
        for step in step_results:
            status = "✅" if step.get("success", True) else "❌"
            text = step['response'] or ""
            gekuerzt = text[:max_step_chars] + ("…" if len(text) > max_step_chars else "")
            steps_summary += f"\n{status} Schritt {step['step']}: {step['action'][:100]}\n   Ergebnis: {gekuerzt}\n"
        
        # Nutze zentralen Summary Prompt
        prompt = DEFAULT_ORCHESTRATOR_MULTISTEP_SUMMARY_PROMPT.format(
            context_summary=context_summary,
            user_input=user_input,
            steps_summary=steps_summary
        )
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=CHAT_HISTORY_CONFIG["interpretation_temperature"],
                max_tokens=CHAT_HISTORY_CONFIG["max_interpretation_tokens"]
            )
            self._track_usage(response.usage)  # AP2.5
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"[{self.name}] Summarization fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück
            return f"[SUMMARIZATION ERROR] {str(e)}"
    
    def _interpret_subagent_result(
        self, 
        user_input: str, 
        agent_name: str, 
        agent_result: Dict,
        chat_history: List
    ) -> str:
        """Interpretiert Sub-Agent-Ergebnisse und generiert kontextbezogene Antwort"""
        
        metadata = agent_result.get("metadata", {})
        raw_response = agent_result.get("response", {})
        
        # Kontext für bessere Interpretation - nutze zentrale Config
        max_interpret_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        context_summary = ""
        if chat_history:
            recent = chat_history[-(max_interpret_pairs * 2):]
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            context_summary = "\n".join([
                f"{msg['role']}: {msg['content'][:max_chars]}"
                for msg in recent
            ])
        
        # === SP_Agent: Tool/Pipeline-Ergebnisse ===
        if metadata.get("intent") == "tool":
            tool_name = metadata.get("tool")
            tool_desc = metadata.get("tool_description")
            success = metadata.get("success")
            stdout = raw_response.get("stdout", "")
            stderr = raw_response.get("stderr", "")
            
            summary = f"""**Ausgeführtes Tool:** {tool_name}
**Beschreibung:** {tool_desc}
**Status:** {"Erfolgreich" if success else "Fehlgeschlagen"}
**Output:** {stdout[:1500]}
**Fehler:** {stderr[:500] if stderr else "Keine"}"""
            
        elif metadata.get("intent") == "pipeline":
            pipeline_name = metadata.get("pipeline")
            pipeline_desc = metadata.get("pipeline_description")
            success = metadata.get("success")
            
            if success:
                steps = raw_response.get("completed_steps", [])
                step_summary = "\n".join([
                    f"- {s['step']}: {'✅' if s['success'] else '❌'} (Versuche: {s.get('attempts', 1)}) {s.get('output', '')[:200]}"
                    for s in steps
                ])
                summary = f"""**Pipeline:** {pipeline_name}
**Beschreibung:** {pipeline_desc}
**Status:** Erfolgreich abgeschlossen
**Durchgeführte Schritte:**
{step_summary}"""
            else:
                failed_step = raw_response.get("failed_at", "unbekannt")
                error = raw_response.get("error", "Unbekannter Fehler")
                recovery_suggestion = raw_response.get("recovery_suggestion", "")
                attempts = max([s.get('attempts', 1) for s in raw_response.get("completed_steps", [])], default=1)
                
                summary = f"""**Pipeline:** {pipeline_name}
**Beschreibung:** {pipeline_desc}
**Status:** Fehlgeschlagen bei Schritt '{failed_step}' (nach {attempts} Versuchen)
**Fehler:** {error}
**Vorschlag:** {recovery_suggestion}"""
        
        # === ChatAgent: Allgemeine Konversation ===
        elif agent_name == "chat":
            confidence = metadata.get("confidence", "unknown")
            summary = f"""**Agent:** Chat Agent (Allgemeine Konversation)
**Antwort des Agents:**
{raw_response if isinstance(raw_response, str) else str(raw_response)[:1500]}
**Confidence:** {confidence}"""
        
        # === RAGAgent: Wissensbasis-gestützt ===
        elif agent_name == "rag":
            sources = metadata.get("sources", [])
            relevance = metadata.get("relevance_score", 0.0)
            retrieval_success = metadata.get("retrieval_success", False)
            
            sources_str = "\n".join([f"  - {s}" for s in sources]) if sources else "  Keine"
            summary = f"""**Agent:** RAG Agent (Wissensbasis)
**Retrieval Status:** {"Erfolgreich" if retrieval_success else "Keine relevanten Dokumente"}
**Relevanz-Score:** {relevance:.3f}
**Quellen:**
{sources_str}
**Antwort des Agents:**
{raw_response if isinstance(raw_response, str) else str(raw_response)[:1500]}"""
        
        else:
            # Fallback für unbekannte Agent-Typen
            summary = f"""**Agent:** {agent_name}
**Ergebnis:**
{str(raw_response)[:1000]}"""
        
        # LLM interpretiert und generiert natürliche Antwort
        prompt = DEFAULT_ORCHESTRATOR_SUBAGENT_INTERPRETATION_PROMPT.format(
            context_summary=context_summary,
            user_input=user_input,
            agent_name=agent_name,
            summary=summary
        )
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=CHAT_HISTORY_CONFIG["interpretation_temperature"],
                max_tokens=CHAT_HISTORY_CONFIG["max_interpretation_tokens"]
            )
            self._track_usage(response.usage)  # AP2.5
            
            interpretation = response.choices[0].message.content.strip()
            logger.info(f"[{self.name}] Interpretierte Antwort: {interpretation[:100]}...")
            
            return interpretation
            
        except Exception as e:
            logger.error(f"[{self.name}] Interpretation fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück
            return f"[INTERPRETATION ERROR] {str(e)}"
    
    def execute(self, user_input: str, context: Dict = None) -> Dict:
        """Orchestriert die Anfrage - mit agentic Planning und Adaptive Re-Planning"""
        logger.info(f"[{self.name}] Orchestriere Anfrage: {user_input[:100]}")
        
        # AP2.5: Reset per-request token accumulator
        self._tok_prompt = 0
        self._tok_completion = 0
        
        chat_history = context.get("chat_history", []) if context else []

        # Sitzungsbezug fuer diesen Aufruf. Ohne id faellt alles auf einen neutralen
        # Platzhalter zurueck, damit ein Aufruf ohne Sitzung (Tests, Skripte) nicht in den
        # Fokus einer echten Unterhaltung schreibt.
        self._session_id = (context or {}).get("db_session_id") or "_kein_sitzungsbezug"

        # Nennt der Nutzer eine Snapshot-ID, ist das ab jetzt DER Snapshot dieser Sitzung.
        genannt = self._extract_snapshot_id_from_history([{"content": user_input or ""}])
        if genannt:
            short_term.set_focus_snapshot(self._session_id, genannt)

        # AGENTIC MODE: Erstelle Execution Plan mit Adaptive Re-Planning
        if self.agentic_mode:
            max_replanning_attempts = 4  # Max 4 Re-Planning Versuche
            attempt = 0
            original_input = user_input
            
            while attempt <= max_replanning_attempts:
                attempt += 1
                logger.info(f"[{self.name}] Agentic Mode: Planning-Versuch {attempt}/{max_replanning_attempts + 1}")
                
                # A UI-selected capability is an explicit user routing instruction. Natural
                # language without a selection still goes through the normal planner.
                force_email = bool(
                    context
                    and "email" in self.agents
                    and (
                        context.get("selected_tool") == "email"
                        or (
                            context.get("active_email_draft")
                            and _EMAIL_FOLLOWUP_RE.search(user_input)
                        )
                    )
                )
                if force_email:
                    plan = {
                        "type": "single_step",
                        "agent": "email",
                        "reasoning": "User selected the Email capability",
                    }
                else:
                    plan = self._create_execution_plan(user_input, chat_history)
                
                # Plan ausführen
                result = self._execute_plan(plan, user_input, chat_history, context)
                
                # Metadata erweitern
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["agentic_mode"] = True
                result["metadata"]["plan_type"] = plan.get("type")
                result["metadata"]["planning_attempts"] = attempt
                
                # ERFOLG? → Prüfe explizit (KEIN Default=True, das wäre falsch!)
                success = result.get("metadata", {}).get("success")
                if success is None:
                    # Wenn success nicht gesetzt ist, betrachte als Erfolg (z.B. bei Info-Antworten)
                    success = True
                
                if success:
                    logger.info(f"[{self.name}] ✅ Execution erfolgreich nach {attempt} Versuch(en)")
                    # AP2.5: merge orchestrator-level token totals + sub-agent tokens into metadata
                    _sub = result.get("metadata", {})
                    _sub_p = _sub.get("tokens_prompt") or 0
                    _sub_c = _sub.get("tokens_completion") or 0
                    result["metadata"]["tokens_prompt"] = self._tok_prompt + _sub_p
                    result["metadata"]["tokens_completion"] = self._tok_completion + _sub_c
                    result["metadata"]["tokens_total"] = (
                        self._tok_prompt + _sub_p + self._tok_completion + _sub_c
                    )
                    return result
                
                # FEHLER → Prüfe ob Re-Planning möglich
                logger.warning(f"[{self.name}] ⚠️ Execution fehlgeschlagen (Versuch {attempt})")
                
                # Hole recovery_suggestion aus METADATA (nicht response, da response jetzt interpretiert ist!)
                recovery_hint = result.get("metadata", {}).get("recovery_suggestion")
                
                # Kein Re-Planning mehr möglich?
                if attempt > max_replanning_attempts:
                    logger.error(f"[{self.name}] Max Re-Planning Versuche erreicht")
                    break
                
                # Keine recovery_suggestion vorhanden?
                if not recovery_hint:
                    logger.warning(f"[{self.name}] Keine recovery_suggestion vorhanden, kann nicht re-planen")
                    logger.debug(f"[{self.name}] Result metadata: {result.get('metadata', {})}")
                    break
                
                # RE-PLANNING: Erstelle neuen Plan basierend auf recovery_suggestion
                logger.info(f"[{self.name}] 🔄 RE-PLANNING basierend auf: {recovery_hint[:100]}")
                
                # Modifiziere User-Input für Re-Planning
                user_input = (
                    f"{original_input}\n\n"
                    f"WICHTIG: Der vorherige Versuch schlug fehl. Recovery-Vorschlag: {recovery_hint}\n"
                    f"Erstelle einen neuen Plan der dieses Problem behebt."
                )
                
                # Füge Fehler-Context zur Chat-History hinzu
                chat_history.append({
                    "role": "assistant", 
                    "content": f"Fehler bei Versuch {attempt}: {recovery_hint[:200]}"
                })
            
            # Nach allen Versuchen: Gib letztes Ergebnis zurück
            result["metadata"]["replanning_exhausted"] = True
            # AP2.5: token totals also on exhausted path
            _sub = result.get("metadata", {})
            _sub_p = _sub.get("tokens_prompt") or 0
            _sub_c = _sub.get("tokens_completion") or 0
            result["metadata"]["tokens_prompt"] = self._tok_prompt + _sub_p
            result["metadata"]["tokens_completion"] = self._tok_completion + _sub_c
            result["metadata"]["tokens_total"] = (
                self._tok_prompt + _sub_p + self._tok_completion + _sub_c
            )
            return result
        
        return result
    
    def _intent_from_plan(self, plan: Optional[Dict],
                          snapshot_id: Optional[str]) -> Optional[Dict]:
        """Das Ziel aus dem Ausfuehrungsplan lesen — oder None, wenn es nicht eindeutig ist.

        Der Planer schreibt sein Ziel in `action`, teils mit Zusatz ("full_correction
        Pipeline"). Verglichen wird deshalb gegen die BEKANNTEN Namen aus `SP_TOOLS` und
        `SP_PIPELINES` statt zu raten: nur wenn genau EIN bekannter Name im Text vorkommt,
        gilt das Ziel als eindeutig. Alles andere geht den regulaeren Weg ueber die
        Intent-Analyse — eine gesparte Sekunde ist keine falsche Pipeline wert.
        """
        if not plan or plan.get("agent") != "sp":
            return None
        action = (plan.get("action") or "").strip()
        if not action:
            return None

        treffer = [(n, "pipeline") for n in SP_PIPELINES if n in action]
        treffer += [(n, "tool") for n in SP_TOOLS if n in action]
        if len(treffer) != 1:
            return None

        name, art = treffer[0]
        return {
            "action_type": art,
            "action_name": name,
            "snapshot_id": snapshot_id,
            "args": [snapshot_id] if snapshot_id else [],
        }

    def _execute_sp_agent(self, user_input: str, chat_history: List, context: Dict) -> Dict:
        """
        NEUE METHODE: Führt SP_Agent mit direkter Tool/Pipeline Auswahl aus
        - Analysiert User-Intent für Smart Planning
        - Ruft execute_tool() oder execute_pipeline() direkt auf
        - Interpretiert Ergebnisse im Orchestrator
        """
        sp_agent = self.agents.get("sp")
        if not sp_agent:
            return {
                "response": "SP_Agent nicht verfügbar",
                "metadata": {"error": "sp_agent_missing"}
            }
        
        # Extrahiere Snapshot-ID aus Historie
        snapshot_id_from_history = self._extract_snapshot_id_from_history(chat_history)

        # WELCHER Snapshot gemeint ist, entscheidet zuerst die AKTUELLE Nachricht.
        #
        # Der Kurzschluss unten nahm bis 15.08.2026 `snapshot_id_from_history` — also nur die
        # Historie. Nennt der Nutzer in seiner Nachricht eine NEUE ID ("hol mir 9faf89b1"),
        # stand die dort noch gar nicht drin, und heruntergeladen wurde der Snapshot aus dem
        # vorigen Gespraech. Gemessen am 15.08.2026: angefordert 9faf89b1, geladen a810d470.
        # Der alte Weg ueber die LLM-Intent-Analyse hatte den Nutzertext im Prompt und war
        # deshalb nicht betroffen — die Abkuerzung hat diese Quelle uebersprungen.
        snapshot_gemeint = self._snapshot_in_focus(chat_history, user_input)

        # Hat der Planer das Ziel schon eindeutig benannt, entfaellt der zweite LLM-Aufruf.
        intent = self._intent_from_plan(context.get("execution_plan"), snapshot_gemeint)

        # Nutze zentralen Intent Analysis Prompt
        intent_prompt = DEFAULT_ORCHESTRATOR_SP_INTENT_PROMPT.format(
            context_summary=self._get_context_summary(chat_history),
            user_input=user_input,
            snapshot_id_from_history=snapshot_id_from_history or "Keine gefunden"
        )

        try:
            if intent is not None:
                logger.info(f"[{self.name}] SP-Intent aus dem Plan uebernommen (ein LLM-Aufruf gespart)")
            else:
                response = self.aoai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "Du bist ein SP_Agent Intent Analyzer. Antworte nur mit JSON."},
                        {"role": "user", "content": intent_prompt}
                    ],
                    temperature=CHAT_HISTORY_CONFIG["sp_intent_temperature"],
                    max_tokens=CHAT_HISTORY_CONFIG["max_intent_tokens"]
                )
                self._track_usage(response.usage)  # AP2.5
                output = response.choices[0].message.content.strip()
                if output.startswith("```json"):
                    output = output[7:]
                if output.startswith("```"):
                    output = output[3:]
                if output.endswith("```"):
                    output = output[:-3]

                intent = json.loads(output.strip())
            logger.info(f"[{self.name}] SP_Agent Intent: {intent['action_type']} - {intent['action_name']}")
            
            # Führe Action aus
            if intent["action_type"] == "pipeline":
                # FALLBACK: Snapshot-ID aus Historie wenn LLM keine liefert (identisch zu Tool-Logik)
                pipeline_snapshot_id = intent.get("snapshot_id")
                if not pipeline_snapshot_id and snapshot_id_from_history:
                    pipeline_snapshot_id = snapshot_id_from_history
                    logger.info(f"[{self.name}] Pipeline Snapshot-ID aus Historie verwendet: {pipeline_snapshot_id}")

                # PT4 Human-in-the-Loop: apply_and_upload beginnt direkt mit apply_correction
                # (KEIN Vorschlags-Schritt) -> nicht auf analyze_only umbiegen, sondern blocken.
                if HUMAN_IN_THE_LOOP and intent["action_name"] == "apply_and_upload":
                    logger.info(
                        f"[{self.name}] HUMAN_IN_THE_LOOP aktiv: Pipeline 'apply_and_upload' blockiert "
                        f"(Anwenden nur nach Freigabe im Review Board)"
                    )
                    return {
                        "response": (
                            "Im Human-in-the-Loop-Modus wird nichts automatisch angewendet. "
                            "Die Korrektur wird erst nach deiner ausdrücklichen Freigabe übernommen."
                            + self._review_board_hint(pipeline_snapshot_id)
                        ),
                        "metadata": {
                            "agent": "sp",
                            "action_type": "pipeline",
                            "pipeline": "apply_and_upload",
                            "success": True,
                            "hitl_blocked": True
                        }
                    }

                # PT4 Human-in-the-Loop: Solange der Toggle an ist, niemals automatisch anwenden.
                # Korrektur-Pipelines (die apply_correction/update_snapshot enthalten) werden auf
                # analyze_only umgebogen -> es entsteht nur ein Vorschlag, nichts wird geschrieben.
                if HUMAN_IN_THE_LOOP and intent["action_name"] in ("full_correction", "correction_from_validation"):
                    logger.info(
                        f"[{self.name}] HUMAN_IN_THE_LOOP aktiv: Pipeline '{intent['action_name']}' "
                        f"wird auf 'analyze_only' umgebogen (Vorschlag statt Auto-Anwendung)"
                    )
                    intent["action_name"] = "analyze_only"

                result = sp_agent.execute_pipeline(
                    pipeline_name=intent["action_name"],
                    snapshot_id=pipeline_snapshot_id
                )

                # Wartet bereits ein Vorschlag auf eine Entscheidung, ist die Lage
                # eindeutig — dafuer braucht es kein Sprachmodell. Die Meldung kommt
                # woertlich aus dem Werkzeug, damit sie nicht beim Umformulieren
                # verwaessert wird.
                if result.get("waiting_for_decision"):
                    return {
                        "response": (
                            "Es wartet bereits ein Korrekturvorschlag zu diesem Snapshot auf "
                            "deine Entscheidung. Solange der offen ist, wird kein weiterer "
                            "erzeugt — er waere gegen einen Datenstand gerechnet, den deine "
                            "Entscheidung veraendert, und anwendbar ist ohnehin immer nur der "
                            "neueste."
                            + self._review_board_hint(pipeline_snapshot_id)
                        ),
                        "metadata": {
                            "agent": "sp",
                            "action_type": "pipeline",
                            "pipeline": intent["action_name"],
                            "success": True,
                            "waiting_for_decision": True,
                        }
                    }
                
                # Interpretiere Pipeline-Ergebnis
                interpreted = self._interpret_sp_result(
                    action_type="pipeline",
                    action_name=intent["action_name"],
                    result=result,
                    user_input=user_input,
                    chat_history=chat_history
                )

                # Ein Vorschlag ohne Wegweiser ist eine Sackgasse: analyze_only erzeugt einen
                # Vorschlag, der auf eine Entscheidung wartet - der Nutzer muss erfahren, WO.
                # Zahlen zuerst, Wegweiser danach.
                interpreted += self._facts_block("pipeline", intent["action_name"], result)

                if intent["action_name"] == "analyze_only" and result.get("success"):
                    interpreted += self._review_board_hint(pipeline_snapshot_id)

                return {
                    "response": interpreted,
                    "metadata": {
                        "agent": "sp",
                        "action_type": "pipeline",
                        "pipeline": intent["action_name"],
                        "success": result["success"],
                        "final_validation": result.get("final_validation")
                    }
                }
            
            elif intent["action_type"] == "tool":
                # PT4 Human-in-the-Loop: Einzel-Tool apply_correction schreibt direkt in
                # snapshot-data.json -> im HitL-Modus nicht ausführen, sondern blocken.
                if HUMAN_IN_THE_LOOP and intent["action_name"] == "apply_correction":
                    logger.info(
                        f"[{self.name}] HUMAN_IN_THE_LOOP aktiv: Tool 'apply_correction' blockiert "
                        f"(Anwenden nur nach Freigabe im Review Board)"
                    )
                    return {
                        "response": (
                            "Im Human-in-the-Loop-Modus wird nichts automatisch angewendet. "
                            "Die Korrektur wird erst nach deiner ausdrücklichen Freigabe übernommen."
                            + self._review_board_hint(snapshot_id_from_history)
                        ),
                        "metadata": {
                            "agent": "sp",
                            "action_type": "tool",
                            "tool": "apply_correction",
                            "success": True,
                            "hitl_blocked": True
                        }
                    }

                # Baue Argument-Liste mit Historie-Fallbacks
                args = []
                snapshot_id = intent.get("snapshot_id")
                
                # FALLBACK: Snapshot-ID aus Historie wenn LLM keine liefert
                if not snapshot_id and snapshot_id_from_history:
                    snapshot_id = snapshot_id_from_history
                    logger.info(f"[{self.name}] Snapshot-ID aus Historie verwendet: {snapshot_id}")
                
                if intent["action_name"] == "rename_snapshot":
                    new_name = intent.get("parameters", {}).get("new_name")
                    
                    # Kein Fallback für Namen - muss im aktuellen Input sein!
                    if snapshot_id and new_name:
                        args = [snapshot_id, new_name]
                    elif snapshot_id:
                        args = [snapshot_id]
                
                elif intent["action_name"] == "download_snapshot":
                    identifier = intent.get("parameters", {}).get("identifier")
                    
                    # Identifier MUSS vorhanden sein (ID oder Name)
                    if identifier:
                        args = [identifier]
                    else:
                        # Fallback: Nutze snapshot_id falls vorhanden
                        if snapshot_id:
                            args = [snapshot_id]
                
                elif snapshot_id:
                    args = [snapshot_id]
                
                result = sp_agent.execute_tool(
                    tool_name=intent["action_name"],
                    args=args
                )
                
                # Nur die ID merken — und zwar an DIESER Sitzung. Die Metadaten selbst
                # werden bei jeder Frage neu gelesen, damit kein ueberholter Zustand als
                # aktueller ausgegeben wird.
                if intent["action_name"] in ["create_snapshot", "download_snapshot"] and "snapshot_metadata" in result:
                    neue_id = (result["snapshot_metadata"] or {}).get("id") or snapshot_id
                    if neue_id:
                        short_term.set_focus_snapshot(self._session_id, neue_id)
                        logger.info(f"[{self.name}] Fokus-Snapshot dieser Sitzung: {neue_id}")
                
                # Interpretiere Tool-Ergebnis
                interpreted = self._interpret_sp_result(
                    action_type="tool",
                    action_name=intent["action_name"],
                    result=result,
                    user_input=user_input,
                    chat_history=chat_history
                )
                interpreted += self._facts_block("tool", intent["action_name"], result)

                return {
                    "response": interpreted,
                    "metadata": {
                        "agent": "sp",
                        "action_type": "tool",
                        "tool": intent["action_name"],
                        "success": result["success"]
                    }
                }
            
        except Exception as e:
            logger.error(f"[{self.name}] SP_Agent Execution fehlgeschlagen: {e}")
            return {
                "response": f"Fehler bei Smart Planning Operation: {str(e)}",
                "metadata": {"agent": "sp", "error": str(e)}
            }
    
    def _snapshot_in_focus(self, chat_history: List, user_input: str = "") -> Optional[str]:
        """Um welchen Snapshot geht es gerade?

        Reihenfolge: die aktuelle Nachricht, dann die Historie, dann der Fokus der Sitzung.
        Der letzte Schritt ist der Grund fuer diesen Helfer: die Historie wird vor jedem
        LLM-Aufruf auf wenige Nachrichtenpaare gekuerzt, und in einer wiederaufgenommenen
        Unterhaltung steht die UUID oft gar nicht mehr darin. Vorher fiel dann still jedes
        Zusatzwissen weg — Entscheidungen, Deep-Link, Zustand —, ohne dass irgendwo stand,
        dass der Bezug verloren ging.
        """
        return (
            self._extract_snapshot_id_from_history([{"content": user_input or ""}])
            or self._extract_snapshot_id_from_history(chat_history)
            or short_term.get_focus_snapshot(self._session_id)
        )

    def _current_snapshot_metadata(self, chat_history: List, user_input: str = "") -> Optional[Dict]:
        """Der AKTUELLE Zustand des Sitzungs-Snapshots, direkt aus der Ablage gelesen."""
        snapshot_id = self._snapshot_in_focus(chat_history, user_input)
        if not snapshot_id:
            return None
        try:
            return self.agents["sp"]._read_snapshot_metadata(snapshot_id)
        except Exception as exc:
            logger.warning(f"[{self.name}] Snapshot-Metadaten nicht lesbar: {exc}")
            return None

    def _extract_snapshot_id_from_history(self, chat_history: List) -> Optional[str]:
        """Extrahiert die letzte erwähnte Snapshot-ID (UUID) aus der Chat-Historie"""
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        
        for msg in reversed(chat_history):
            content = msg.get("content", "")
            matches = re.findall(uuid_pattern, content, re.IGNORECASE)
            if matches:
                return matches[-1]  # Neueste ID in dieser Message

        return None

    def _facts_block(self, action_type: str, action_name: str, result: Dict) -> str:
        """Die harten Zahlen eines Laufs — aus dem Code gerendert, nie durch ein Modell.

        Alles hier stammt unveraendert aus dem Ergebnis. Was nicht drinsteht, wird nicht
        gezeigt; gibt es gar nichts zu zeigen, entfaellt der Block. Er ERSETZT den
        erklaerenden Text nicht, er verankert ihn — wenn Prosa und Block sich
        widersprechen, gilt der Block, und der Widerspruch faellt sofort auf.
        """
        zeilen = []

        # Validierung (Werkzeug `validate_snapshot` und Pipeline-Abschluss)
        val = result.get("validation") or result.get("final_validation") or {}
        if isinstance(val, dict) and ("errors" in val or "warnings" in val):
            fehler = val.get("errors", 0)
            warnungen = val.get("warnings", 0)
            zeilen.append(f"- Validierung: **{fehler} Fehler**, {warnungen} Warnungen")
            if fehler:
                zeilen.append("- Snapshot ist damit **nicht** valide")

        # Reichweite eines Analyse-Laufs
        scope = result.get("analysis_scope")
        if isinstance(scope, dict):
            offen = scope.get("errors_not_addressed") or []
            zeilen.append(
                f"- Gefundene Fehler: **{scope.get('errors_found', 0)}** — "
                f"Vorschlag erzeugt für **1** davon, **{len(offen)}** unberührt"
            )
            zeilen.append("- Am Snapshot wurde **nichts** geändert und nichts hochgeladen")

        if not zeilen:
            return ""
        return "\n\n---\n**Gemessen:**\n" + "\n".join(zeilen)

    def _review_board_hint(self, snapshot_id: Optional[str] = None) -> str:
        """
        Wegweiser ins Review Board, inkl. Deep-Link auf den konkreten offenen Vorschlag.

        Ohne diesen Hinweis endet der HitL-Flow im Nichts: der Nutzer erfaehrt, dass nichts
        angewendet wurde, aber nicht, wo er entscheiden kann. Faellt bei DB-Problemen still
        auf den Link zur Liste zurueck.
        """
        if snapshot_id:
            try:
                from db import repository as repo
                open_ones = [
                    p for p in repo.list_open_proposals_as_dicts()
                    if p["snapshot_id"] == snapshot_id
                ]
                if open_ones:
                    p = open_ones[0]  # neuester zuerst
                    return (
                        f"\n\nDein Korrekturvorschlag wartet auf eine Entscheidung: "
                        f"[Im Review Board oeffnen]({APP_BASE_URL}/review.html"
                        f"?proposal={p['proposal_id']}) "
                        f"— {p.get('error_type') or 'Vorschlag'}, "
                        f"Konfidenz {round((p.get('confidence_score') or 0) * 100)} %. "
                        f"Dort kannst du Genehmigen, Ablehnen oder den Wert aendern."
                    )
            except Exception as exc:
                logger.warning(f"[{self.name}] Deep-Link nicht baubar: {exc}")
        return (
            "\n\nOffene Korrekturvorschlaege findest du im "
            f"[Review Board]({APP_BASE_URL}/review.html) — dort kannst du Genehmigen, Ablehnen "
            "oder den Wert aendern."
        )

    def _open_proposals_for_focus(self, chat_history: List, user_input: str = "") -> List[dict]:
        """Vorschlaege zum Sitzungs-Snapshot, die noch auf eine Entscheidung warten.

        Gab es bis 15.08.2026 nirgends im Agenten-Kontext: `list_open_proposals_as_dicts()`
        wurde nur von der Review-Seite und vom Deep-Link-Hinweis genutzt. Auf die Frage „was
        steht noch aus?" konnte der Agent es also nicht wissen — und schwieg darueber nicht,
        sondern antwortete aus der Unterhaltung.

        Bewusst auf den Snapshot dieser Sitzung eingegrenzt: die Liste kennt keine Mandanten,
        und offene Vorschlaege fremder Snapshots gehen diese Unterhaltung nichts an.
        """
        snapshot_id = self._snapshot_in_focus(chat_history, user_input)
        if not snapshot_id:
            return []
        try:
            from db import repository as repo
            offen = [p for p in repo.list_open_proposals_as_dicts()
                     if p["snapshot_id"] == snapshot_id]
            # Fertigen Link mitgeben, statt das Modell einen bauen zu lassen: es kennt den
            # Host nicht und kann ihn nicht erfinden.
            for p in offen:
                p["review_url"] = f"{APP_BASE_URL}/review.html?proposal={p['proposal_id']}"
            return offen
        except Exception as exc:  # DB darf den Chat nie brechen
            logger.warning(f"[{self.name}] Offene Vorschlaege nicht ladbar: {exc}")
            return []

    def _get_review_decisions(self, chat_history: List, user_input: str = "") -> List[dict]:
        """
        Menschliche Review-Entscheidungen zum aktuellen Snapshot (aus der DB).

        Die Entscheidung faellt im Review Board, nicht im Chat - sie steht also NICHT in der
        Chat-Historie. Ohne diese Bruecke antwortet der Chat auf "was war die Loesung?" mit
        dem KI-Vorschlag, auch wenn der Mensch ihn verworfen hat.

        Die Snapshot-ID wird zuerst in der AKTUELLEN Nachricht gesucht (die steht noch nicht
        in der Historie), dann in der Historie.

        Defensiv: jeder DB-Fehler wird geschluckt, der Chat funktioniert dann wie bisher.
        """
        snapshot_id = self._snapshot_in_focus(chat_history, user_input)
        if not snapshot_id:
            return []
        try:
            from db import repository as repo
            return repo.get_decisions_for_snapshot(snapshot_id)
        except Exception as exc:  # DB darf den Chat nie brechen
            logger.warning(f"[{self.name}] Review-Entscheidungen nicht ladbar: {exc}")
            return []

    def _get_context_summary(self, chat_history: List, max_messages: int = 3) -> str:
        """Erstellt eine kompakte Zusammenfassung der letzten Messages"""
        if not chat_history:
            return "Keine Historie"
        
        recent = chat_history[-max_messages:]
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Herkunft mitschreiben — sonst ist ein gemessenes Werkzeugergebnis von einem
            # dahingesagten Satz nicht zu unterscheiden.
            etikett = short_term.label_for(msg.get("agent_name")) if msg["role"] != "user" else None
            content = msg["content"][:200]
            lines.append(f"{role}{f' [{etikett}]' if etikett else ''}: {content}...")
        
        return "\n".join(lines)
    
    def _interpret_sp_result(self, action_type: str, action_name: str, result: Dict, user_input: str, chat_history: List) -> str:
        """Interpretiert SP_Agent Ergebnisse mit LLM (keine hartcodierten Antworten!)"""
        
        # Extrahiere relevante Daten aus Result
        success = result.get("success", False)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        error = result.get("error", "")
        
        # Kontext zusammenstellen
        context_parts = []
        
        if action_type == "pipeline":
            context_parts.append(f"Pipeline: {action_name}")
            context_parts.append(f"Status: {'success' if success else 'failed'}")
            
            if not success:
                failed_at = result.get("failed_at")
                context_parts.append(f"Failed at step: {failed_at}")
                context_parts.append(f"Error: {error or stderr}")
                
                # Recovery-Suggestion als Rohdaten
                recovery = result.get("recovery_suggestion")
                if recovery:
                    if isinstance(recovery, dict):
                        # Strukturierte Recovery-Daten
                        error_type = recovery.get("error_type", "unknown")
                        context_parts.append(f"Error type: {error_type}")
                        
                        if error_type == "missing_prerequisite":
                            context_parts.append(f"Missing step: {recovery.get('missing_step')}")
                            context_parts.append(f"Required file: {recovery.get('required_file')}")
                        elif error_type == "snapshot_not_found":
                            context_parts.append("Issue: snapshot ID invalid or non-existent")
                        elif error_type == "authentication_failed":
                            context_parts.append(f"Config issue: {recovery.get('config_issue')}")
                        
                        # Füge alle recovery-Felder hinzu als Rohdaten
                        for key, value in recovery.items():
                            if key not in ["error_type"]:
                                context_parts.append(f"{key}: {value}")
                    else:
                        # Fallback für alte String-Recovery
                        context_parts.append(f"Recovery data: {recovery}")
            else:
                completed = result.get("completed_steps", [])
                # completed_steps ist eine Liste von Dicts, extrahiere step-Namen
                step_names = [s.get("step", "unknown") for s in completed]
                context_parts.append(f"Completed steps ({len(step_names)}): {', '.join(step_names)}")
                
                final_validation = result.get("final_validation")
                if final_validation:
                    is_valid = final_validation.get("is_valid", False)
                    errors = final_validation.get("errors", 0)
                    warnings = final_validation.get("warnings", 0)
                    context_parts.append(f"Final validation: is_valid={is_valid}, errors={errors}, warnings={warnings}")

                # Reichweite der Analyse. Steht bewusst als eigener, sehr direkter Block da:
                # "Status: success" allein wurde als "alles korrigiert" gelesen.
                scope = result.get("analysis_scope")
                if scope:
                    offen = scope.get("errors_not_addressed") or []
                    context_parts.append("--- WHAT THIS RUN ACTUALLY DID (binding, do not embellish) ---")
                    context_parts.append(
                        "NOTHING WAS CHANGED: the snapshot was not modified and nothing was "
                        "uploaded to the server. Only a PROPOSAL was created."
                    )
                    context_parts.append(
                        f"Validation found {scope.get('errors_found', 0)} error(s) and "
                        f"{scope.get('warnings_found', 0)} warning(s)."
                    )
                    context_parts.append(
                        f"A proposal was created for EXACTLY ONE of them: {scope.get('handled_error')}"
                    )
                    if offen:
                        context_parts.append(
                            f"NOT addressed by this run ({len(offen)} error(s)) — they are still open:"
                        )
                        for m in offen:
                            context_parts.append(f"  - {m}")
                        context_parts.append(
                            "You MUST tell the user that only one error was handled and that "
                            f"{len(offen)} further error(s) remain open. Do NOT claim the snapshot "
                            "is fixed, valid, or ready to use."
                        )
                    context_parts.append(
                        "The proposal is NOT applied. It awaits a human decision in the review board."
                    )
        
        else:  # Tool
            context_parts.append(f"Tool: {action_name}")
            context_parts.append(f"Status: {'success' if success else 'failed'}")
            
            if not success:
                context_parts.append(f"Error: {error or stderr}")
            else:
                # Spezialfall: create_snapshot, download_snapshot haben Metadaten (ID, Name)
                if action_name in ["create_snapshot", "download_snapshot"] and "snapshot_metadata" in result:
                    import json
                    metadata = result["snapshot_metadata"]
                    
                    # NUR Rohdaten - LLM entscheidet wie sie es formuliert
                    action_label = "created" if action_name == "create_snapshot" else "downloaded"
                    context_parts.append(f"Action: snapshot_{action_label}")
                    context_parts.append(f"Snapshot-Metadaten:")
                    context_parts.append(json.dumps(metadata, indent=2, ensure_ascii=False))
                
                # Spezialfall: validate_snapshot hat strukturierte Validation-Daten
                elif action_name == "validate_snapshot" and "validation" in result:
                    validation = result["validation"]
                    is_valid = validation.get("is_valid", False)
                    errors = validation.get("errors", 0)
                    warnings = validation.get("warnings", 0)
                    
                    # WICHTIG: Zeige auch Snapshot-Metadata (Name, ID, etc.)
                    if "snapshot_metadata" in result:
                        import json
                        metadata = result["snapshot_metadata"]
                        context_parts.append("Snapshot-Metadaten:")
                        context_parts.append(json.dumps(metadata, indent=2, ensure_ascii=False))
                        
                        # Minimaler Hinweis für LLM (keine hardcoded Formatierung!)
                        if "llm_corrections" in metadata and metadata["llm_corrections"]:
                            context_parts.append("\nNote: llm_corrections array contains applied KI corrections.")
                    
                    # Status als Rohdaten - LLM interpretiert natürlich
                    if is_valid and errors == 0:
                        context_parts.append(f"Server validation: isSuccessfullyValidated=true")
                        context_parts.append(f"Metrics: errors={errors}, warnings={warnings}")
                    else:
                        context_parts.append(f"Server validation: snapshot has errors, cannot be used")
                        context_parts.append(f"Metrics: is_valid={is_valid}, errors={errors}, warnings={warnings}")
                    
                    # Fehler-Details als Rohdaten
                    if errors > 0:
                        error_details = validation.get("error_details", [])
                        context_parts.append("Error details:")
                        for err in error_details:
                            context_parts.append(f"  - {err.get('message', 'Unknown')}")
                    
                    # Warning-Details als Rohdaten
                    if warnings > 0:
                        warning_details = validation.get("warning_details", [])
                        context_parts.append(f"Warning details ({warnings} total):")
                        for warn in warning_details:
                            context_parts.append(f"  - {warn.get('message', 'Unknown')}")
                
                elif stdout:
                    context_parts.append(f"Output: {stdout[:500]}")
        
        # Menschliche Entscheidungen gehoeren in JEDE Interpretation, nicht nur in die des
        # Chat-Agenten. Sonst berichtet eine Frage wie „was war die Loesung?", die der Router
        # zum SP-Agenten schickt, weiterhin den KI-Vorschlag — genau der Fehler, gegen den
        # die Bruecke gebaut wurde. Sie war bis 15.08.2026 nur am Chat-Pfad angeschlossen.
        entscheidungen = self._get_review_decisions(chat_history, user_input)
        if entscheidungen:
            import json as _json
            context_parts.append(
                "--- HUMAN REVIEW DECISIONS (binding, they overrule the AI proposal) ---"
            )
            context_parts.append(_json.dumps(entscheidungen, ensure_ascii=False, default=str))
            context_parts.append(
                "`applied_value` is what was really applied; on decision='modify' the human "
                "REPLACED `ai_value` and it must not be presented as the solution. "
                "`revalidation.errors_after` is the CHECKED number of errors left afterwards — "
                "if it is above 0, the snapshot is NOT fixed, valid or ready to use."
            )

        # Offene Vorschlaege. Ohne sie kann auf „was steht noch aus?" niemand antworten —
        # die Entscheidung faellt im Review Board und steht nicht in der Unterhaltung.
        offen = self._open_proposals_for_focus(chat_history, user_input)
        if offen:
            context_parts.append(f"--- OPEN PROPOSALS awaiting a human decision ({len(offen)}) ---")
            for o in offen:
                context_parts.append(
                    f"  - {o['error_type']} at {o['target_path']} "
                    f"(confidence {round((o.get('confidence_score') or 0) * 100)} %) "
                    f"-> {APP_BASE_URL}/review.html?proposal={o['proposal_id']}"
                )

        result_context = "\n".join(context_parts)
        
        # LLM interpretiert das Ergebnis NATÜRLICH basierend auf User-Frage
        max_interpret_pairs = CHAT_HISTORY_CONFIG.get("max_planning_pairs", 2)
        
        recent_context = ""
        if chat_history:
            recent = chat_history[-(max_interpret_pairs * 2):]
            max_chars = CHAT_HISTORY_CONFIG.get("max_message_chars", 1000)
            recent_context = "Bisheriger Kontext:\n" + "\n".join(
                f"{m['role']}"
                + (f" [{short_term.label_for(m.get('agent_name'))}]"
                   if m['role'] != 'user' and short_term.label_for(m.get('agent_name')) else "")
                + f": {m['content'][:max_chars]}"
                for m in recent
            ) + "\n"
        
        # Nutze zentralen SP Result Interpretation Prompt
        interpret_prompt = DEFAULT_ORCHESTRATOR_SP_RESULT_INTERPRETATION_PROMPT.format(
            user_input=user_input,
            recent_context=recent_context,
            action_type=action_type,
            action_name=action_name,
            result_context=result_context
        )
        
        try:
            response = self.aoai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.interpretation_system_prompt},
                    {"role": "user", "content": interpret_prompt}
                ],
                temperature=CHAT_HISTORY_CONFIG["sp_result_temperature"],
                max_tokens=CHAT_HISTORY_CONFIG["max_interpretation_tokens"]
            )
            self._track_usage(response.usage)  # AP2.5
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"[{self.name}] Interpretation fehlgeschlagen: {e}")
            # KEIN hardcodierter Fallback - gebe technische Info zurück, App muss Error-Handling machen
            return f"[INTERPRETATION ERROR] {str(e)}"
