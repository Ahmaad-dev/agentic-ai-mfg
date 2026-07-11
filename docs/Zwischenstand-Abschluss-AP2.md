Gesamtstand PT4 — 2026-07-08
Milestones
Milestone	Status	AP
M0 Baseline & Scope	✅ abgeschlossen	—
M1 Correction Proposal Layer	✅ abgeschlossen	AP1
M2 Persistence Layer	✅ abgeschlossen	AP2
M3 HitL Backend	⬜ offen	AP3
M4 HitL Frontend (Demo-ready)	⬜ offen	AP4
M5 MCP Integration	⬜ offen	AP5
M6 Dashboard	⬜ offen	AP6
M7 Memory System	⬜ offen	AP7
M8 Evaluation & Demo	⬜ offen	AP-E
Detailstand abgeschlossener Pakete
AP1 — Correction Proposal Layer (M1) ✅

Sub-Paket	Status	Abweichung vom Plan
AP1.1 Schema (confidence_score, status)	✅	keine
AP1.2 Pipeline-Stopp / HitL-Toggle	✅	Toggle-Ansatz statt Pipeline-Split — funktional äquivalent, deferred Pipeline-Split zu AP3
AP1.3 Confidence-Formel (0.5·llm + 0.3·schema + 0.2·mem)	✅	keine
AP1.4 Zentraler Proposal-Record (stable proposal_id)	✅	keine
AP1.5 schema_valid als explizites Feld	✅	war nicht im Plan, wurde empfohlen und umgesetzt
Was wirklich passiert: Jeder erzeugte Vorschlag trägt confidence_score=0.775, schema_valid=true, status=pending_review. Nichts wird automatisch angewendet (4 Pfade blockiert). Proposals sind zentral auffindbar in Snapshots/_proposals/ und in der DB.

AP2 — Persistence Layer (M2) ✅

Sub-Paket	Status
ORM-Modelle (7 Tabellen)	✅
Alembic-Migration	✅
Repository-Layer + web_server.py eingehängt	✅
SQLite↔Azure SQL via DATABASE_URL	✅
Live-Nachweis: Echter Chat-Lauf mit Azure OpenAI GPT-4o erzeugt sessions=4, messages=12, agent_runs=6, proposals=1. Alle Tabellen stehen, reviews/memory_items leer (korrekt, warten auf AP3/AP7).

Was als nächstes kommt (Critical Path)
AP3 → AP4 → (AP5 + AP6 parallel) → AP7 → AP-E
AP3 — HitL Backend (nächster Schritt):

Flask-Blueprint demo/routes/review.py
5 Endpoints: GET /api/review/proposals, GET …/<id>, POST …/approve, POST …/reject, POST …/modify
Voraussetzung: Pipeline apply_after_review in sp_tools_config.py (deferred aus AP1.2)
Apply erst nach Freigabe, dann Re-Validierung, dann DB-Eintrag in reviews
AP4 — HitL UI: Review-Page mit Before/After-Diff, Confidence-Anzeige, Approve/Reject/Modify-Buttons → erst hier ist das System demo-fähig.

Offene technische Hinweise (kleine Schulden)
Token/Cost-Felder in agent_runs sind immer NULL — Daten liegen vor, werden aber noch nicht extrahiert. Relevant für AP6 (Kosten-KPI).
proposals.affected_entity ist aktuell identisch mit target_path — sollte in AP3 verfeinert werden.
Pipeline-Split (generate_proposal/apply_after_review in sp_tools_config.py) fehlt noch — ist Voraussetzung für AP3 Approve-Pfad und sollte als erster Schritt dort erledigt werden.
Zusammenfassung in einem Satz
2 von 8 Meilensteinen abgeschlossen (M0, M1, M2); das Fundament steht (Governance, Confidence-Score, DB-Backbone); der nächste demoable Zustand kommt nach AP3 + AP4 (HitL-Loop vollständig schließbar).