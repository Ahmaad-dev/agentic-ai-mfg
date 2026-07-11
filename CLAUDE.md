# Claude Code Project Instructions

Bitte berücksichtige diese Projekt-Instructions immer:

---
description: Global project instructions for the PT4 Agentic AI project. Always loaded.
applyTo: "**"
---

# PT4 Project — Agent Instructions

## Project context
This repository (`demo/`) contains a multi-agent system for Smart Planning snapshot
validation and correction. Phase 3 is complete (autonomous correction). We are now in
**PT4**, evolving it into an enterprise solution with Human-in-the-Loop governance,
confidence scoring, MCP integration, monitoring dashboard, and a memory system.

All application code lives under `demo/`. There is NO `src/` layout. Runtime tools are
under `demo/smart-planning/runtime/` and are invoked via subprocess by `sp_agent.py`.

## How to work — hard rules
1. **Read `docs/PT4_PLAN.md` before starting any work package.** It defines milestones,
   work packages, and Definitions of Done. Do not invent scope beyond it.
2. **Work strictly one sub-package at a time.** Do not combine steps or "helpfully" do
   the next one. Change only the files named in the current task.
3. **Never apply a correction without explicit human approval.** The core PT4 change is
   that the system proposes and waits; it does not auto-apply.
4. **Additive changes only** unless told otherwise. Preserve backward compatibility with
   existing JSON files and existing pipeline behavior not in scope.
5. **Distinguish clearly** in all explanations: implemented / partially implemented /
   planned / conceptual / not yet done. Do not claim something exists if it doesn't.
6. **If information is missing, state an assumption explicitly** — do not guess silently.
7. **After finishing a sub-package, append an entry to `docs/PROJECT_LOG.md`** using the
   format defined at the top of that file.

## Scope guardrails
- First vertical slice covers ONE error type only: empty `demandId` (`EMPTY_FIELD`).
- Out of scope for PT4: Continuous Learning Agent / GitHub PR automation, Azure AD,
  security hardening, resilience/automation beyond MCP.
- One confidence score and one approval per whole proposal (including additional_updates).

## Security note
`demo/.env` currently holds secrets in plaintext. Never print secret values in output.
Never commit `.env`.

## Reporting — keep it short (token discipline)
When reporting a finished task, DO NOT output full file diffs or re-print whole files.
Report only:
1. One sentence: what changed + which file(s) (names only, no code).
2. The functional test result (the actual behavior that proves the DoD is met).
3. A confirmation that only the agreed files were touched.
Only show a specific code snippet if I explicitly ask for it, or if you are BLOCKED and
need to show the exact conflicting lines to explain the problem.