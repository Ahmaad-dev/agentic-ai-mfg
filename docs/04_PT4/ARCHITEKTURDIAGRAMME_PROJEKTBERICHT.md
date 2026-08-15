# Architekturdiagramme für den PT4-Projektbericht

> **Dokumenttyp:** zitierfähige Architektur- und Ablaufdokumentation  
> **Stand:** 13.07.2026  
> **System:** *Agentic AI in der Produktion – Human-in-the-Loop Governance, MCP-Integration und lernendes Review-System*  
> **Geltungsbereich:** real implementierter Stand von AP1 bis AP7; AP-E und AP-X werden nur dort gezeigt, wo sie ausdrücklich als offen beziehungsweise als Zielbild gekennzeichnet sind.

## 1. Zweck und Leselogik

Dieses Dokument übersetzt den realen Quellcode, den Umsetzungsplan und das Projektlog in konsistente Architektursichten für einen Projektbericht. Es ist nicht als idealisierte Referenzarchitektur zu lesen. Jede als **IST** bezeichnete Beziehung ist im Repository implementiert oder durch einen dokumentierten Funktionsnachweis belegt. **ZIEL** bezeichnet ausschließlich einen empfohlenen Ausbau und darf im Bericht nicht als bereits umgesetzt dargestellt werden.

Die Diagramme folgen einer einheitlichen Leselogik:

- **Blau:** Bestandteil des eigenen Systems.
- **Grün:** persistente Daten- oder Wissensbasis.
- **Violett:** KI-, Integrations- oder Infrastrukturkomponente außerhalb des eigenen Codes.
- **Orange:** Human-in-the-Loop-Grenze oder kontrollierte Mutation.
- **Grau gestrichelt:** Zielbild, noch nicht implementiert.

Die Mermaid-Blöcke können direkt in Markdown-fähigen Dokumentationswerkzeugen gerendert oder für den Projektbericht als SVG/PNG exportiert werden.

## 2. Contract-Check und Quellenhierarchie

Die Diagramme wurden gegen folgende Primärquellen im Projekt geprüft:

1. [PT4_PLAN.md](PT4_PLAN.md) – Akzeptanzkriterien, Arbeitspakete und Meilensteine.
2. [PROJECT_LOG.md](PROJECT_LOG.md) – chronologischer Nachweis der Entscheidungen, Abweichungen, Tests und bekannten Grenzen.
3. Aktueller Code unter `demo/` – maßgeblich für tatsächlich vorhandene Komponenten und Aufrufpfade.
4. [AP5_AP6_DOCUMENTATION.md](AP5_AP6_DOCUMENTATION.md) – historische Detaildokumentation für MCP und Dashboard.
5. [README.md](../demo/README.md) und [README-PT4.md](../demo/README-PT4.md) – Ausgangs- und Zwischenstandsdokumentation.

Bei Widersprüchen gilt: **aktueller Code vor neuestem Projektlog vor Plan vor historischen Zwischenstandsdokumenten**. Das ist besonders relevant, weil:

- automatische Proposal-E-Mails nach dem AP5-Abnahmenachweis wieder deaktiviert wurden;
- E-Mails aktuell ausschließlich nach expliziter Chat-Freigabe versendet werden;
- M6 und M7 inzwischen als abgeschlossen markiert sind;
- die Confidence-Formel inzwischen `formula_version = v3` verwendet und `value_grounded` klassenabhängig berechnet;
- AP-E weiterhin nicht vollständig abgeschlossen ist.

## 3. Methodische und literarische Fundierung

Die Dokumentation verwendet mehrere Sichten, weil eine einzelne Grafik weder Stakeholder, statische Struktur, Laufzeitverhalten, Daten noch Deployment angemessen erklären kann. Das entspricht dem Grundgedanken von [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html), Architektur über zielgerichtete *Views* und *Viewpoints* für unterschiedliche Belange zu beschreiben.

Für die statische Zerlegung wird das [C4-Modell von Simon Brown](https://c4model.com/diagrams) verwendet: Systemkontext, Container und Komponenten bilden gestufte Detaillierungsebenen. C4 empfiehlt ausdrücklich, nur die Sichten einzusetzen, die einen konkreten Erkenntnisgewinn liefern. Dynamische Abläufe und Deployment werden als ergänzende Diagrammtypen genutzt. Die Gliederung ist zugleich kompatibel mit den Building-Block-, Runtime- und Deployment-Sichten des [arc42-Templates](https://arc42.org/).

Für die fachlichen Architekturentscheidungen sind zusätzlich relevant:

- Die [MCP-Architektur](https://modelcontextprotocol.io/docs/learn/architecture) unterscheidet Host, Client und Server. Diese Unterscheidung ist zentral, um den vorhandenen MCP-Server nicht fälschlich als bereits fertige Multi-Connection-Plattform darzustellen.
- Das CoALA-Paper [*Cognitive Architectures for Language Agents*](https://arxiv.org/abs/2309.02427) beschreibt Sprachagenten über modulare Gedächtniskomponenten, Entscheidungsprozesse und interne/externe Aktionen. Das Projekt lehnt seine Trennung von Arbeitsgedächtnis, episodischem Gedächtnis und Regelwissen daran an, verwendet die Begriffe aber bewusst nicht überdehnt.
- Das [NIST AI Risk Management Framework](https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction/) fordert klar definierte menschliche Rollen und Verantwortlichkeiten in Human-AI-Konfigurationen. Im Projekt wird diese Forderung technisch durch eine echte Schreibsperre und einen separaten Review-Commit umgesetzt.
- Die von Amershi et al. publizierten [Guidelines for Human-AI Interaction](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/) betonen unter anderem Korrigierbarkeit, Kontrolle und verständliches Systemverhalten. Review-Diff, Confidence-Begründungen, Modify und explizite Versandfreigabe setzen diese Prinzipien konkret um.
- Microsofts [Azure AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) unterscheiden spezialisierte Agenten, Orchestration und menschliche Freigabepunkte. Das reale System entspricht dabei am ehesten einer zentral gesteuerten Orchestrator-Architektur mit spezialisierten Sub-Agenten und deterministischen Governance-Gates.

## 4. Sichtenkatalog für den Projektbericht

| Nr. | Sicht | Leitfrage | Empfohlene Verwendung |
|---:|---|---|---|
| 1 | Systemkontext | Wer nutzt das System und mit welchen externen Systemen interagiert es? | Einleitung / Systemabgrenzung |
| 2 | Container | Welche deploybaren Anwendungen und Datenspeicher bilden die Lösung? | Architekturkapitel |
| 3 | Backend-Komponenten | Wie sind Orchestrator, Agenten, Governance, MCP und Repository intern getrennt? | Technische Umsetzung |
| 4 | Chat-Laufzeit | Wie wird eine natürliche Anfrage geplant, geroutet und protokolliert? | Agentenarchitektur |
| 5 | HitL-Korrekturlauf | Wo endet KI-Autonomie und wo beginnt menschlich autorisiertes Schreiben? | Kernbeitrag / Governance |
| 6 | Proposal-Zustände | Welche Zustände und Fehlerpfade besitzt ein Vorschlag? | Prozess- und Auditierbarkeit |
| 7 | Datenmodell | Welche Entitäten tragen Chat, Vorschlag, Entscheidung, Memory und Telemetrie? | Persistenz |
| 8 | Memory-Architektur | Wie wirken Session-Kontext, Regelkarten und menschliche Präzedenzfälle zusammen? | AP7 / wissenschaftlicher Bezug |
| 9 | MCP-Ist-Architektur | Was ist wirklich standardisiert und wo liegen die Grenzen? | AP5 |
| 10 | E-Mail-Workflow | Wie verhindert das System unbeabsichtigten Versand? | Enterprise-Fall AP5 |
| 11 | Dashboard-Datenfluss | Wie entstehen KPIs und Data-Quality-Hinweise? | AP6 |
| 12 | Deployment | Wie unterscheiden sich lokale und Azure-Ausführung? | Betrieb / Übertragbarkeit |
| 13 | Trust Boundaries | Wo liegen Secrets, externe Vertrauensgrenzen und kontrollierte Schreibpfade? | Security-Einordnung |
| 14 | CI/CD | Wie gelangen Backend und Frontend reproduzierbar nach Azure? | DevOps |
| 15 | MCP-Zielbild | Wie kann GitHub, Wikipedia oder SharePoint später ergänzt werden? | Ausblick |
| 16 | AP-Traceability | Welche Architekturbausteine erfüllen welche Arbeitspakete? | Ergebnissicherung |

---

## 5. Diagramm 1 – Systemkontext nach C4, Ebene 1 (IST)

**Aussage:** Das System vermittelt zwischen Produktionsplaner, Fachreviewer und mehreren Azure-/Smart-Planning-Diensten. Die fachlich entscheidende Systemgrenze ist: Die KI darf Vorschläge erzeugen, aber eine Mutation der Produktionsplanungsdaten wird im PT4-Modus erst nach einer persistierten menschlichen Entscheidung zugelassen.

```mermaid
flowchart LR
    USER["Produktionsplaner / Chat-Nutzer"]
    REVIEWER["Fachreviewer<br/>entscheidet Approve, Modify oder Reject"]
    EXPERT["Domänenexperte<br/>pflegt Regelkarten in Alltagssprache"]

    subgraph SYSTEM["Agentic-AI-Manufacturing-System · PT4"]
        AAI["Multi-Agent-Anwendung<br/>Chat, Review Board, Dashboard, MCP-Tools"]
    end

    SP["Smart-Planning-API<br/>Snapshots und serverseitige Validierung"]
    AOAI["Azure OpenAI<br/>Planung, Generierung, Interpretation"]
    SEARCH["Azure AI Search<br/>interne Dokumente für RAG"]
    ACS["Azure Communication Services Email<br/>explizit bestätigter Versand"]
    STORAGE["Lokales Dateisystem oder Azure Blob Storage<br/>Snapshots, Iterationen, Regelkarten"]
    SQL["SQLite lokal oder Azure SQL<br/>Audit-, Review- und Telemetriedaten"]

    USER -->|"natürliche Sprache, Tool-Auswahl"| AAI
    AAI -->|"Antwort, Entwurf, Deep-Link"| USER
    REVIEWER -->|"prüft Diff, Begründung, Evidenz und Confidence"| AAI
    AAI -->|"Review-Aufgabe und Revalidierung"| REVIEWER
    EXPERT -->|"Markdown-Regelkarte"| STORAGE

    AAI <-->|"Snapshot lesen, schreiben, Validierungsjob"| SP
    AAI <-->|"LLM-Aufrufe"| AOAI
    AAI -->|"semantische Suche"| SEARCH
    SEARCH -->|"Dokumentkontext und Quellen"| AAI
    AAI -->|"freigegebene E-Mail"| ACS
    AAI <-->|"Artefakte und Skills"| STORAGE
    AAI <-->|"fachlicher Systemzustand"| SQL

    classDef actor fill:#fff4ce,stroke:#8a6d1d,color:#222;
    classDef system fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef external fill:#ede9fe,stroke:#7c3aed,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    class USER,REVIEWER,EXPERT actor;
    class AAI system;
    class SP,AOAI,SEARCH,ACS external;
    class STORAGE,SQL data;
```

**Projektbezug:** `demo/web_server.py` stellt die Nutzeroberfläche und APIs bereit; `demo/agents/` enthält Orchestrator und Spezialagenten; `demo/routes/review.py` ist der freigegebene Schreibpfad; `demo/storage_manager.py` und `demo/db/session.py` abstrahieren Datei- und SQL-Persistenz.

**Geeignete Bildunterschrift:** *Systemkontext der PT4-Lösung: Die Agentenanwendung verbindet Nutzer, Smart Planning und Azure-Dienste; produktive Datenänderungen bleiben an eine menschliche Review-Entscheidung gebunden (eigene Darstellung in Anlehnung an C4).*

---

## 6. Diagramm 2 – Container-Sicht nach C4, Ebene 2 (IST)

**Aussage:** C4 verwendet „Container“ im Sinn einer separat laufenden Anwendung oder eines Datenspeichers, nicht nur im Sinn eines Docker-Containers. Der Python-Backend-Prozess enthält mehrere Komponenten, ist aber im aktuellen Deployment eine gemeinsame Anwendung. Der MCP-Server kann separat über `stdio` gestartet werden und verwendet dieselbe Tool- und Repository-Logik.

```mermaid
flowchart TB
    USER["Nutzer / Reviewer"]

    subgraph PT4["Software-System: Agentic AI Manufacturing"]
        UI["Web-Frontend<br/>HTML, CSS, JavaScript<br/>Chat · Review Board · Dashboard"]
        API["Python-Backend<br/>Flask + Gunicorn<br/>REST, Orchestration, Agenten, Governance"]
        MCP["MCP-Server-Prozess<br/>Python MCP SDK · FastMCP · stdio<br/>12 Review-/Dashboard-/E-Mail-Tools"]
        RUNTIME["Smart-Planning-Runtime<br/>Python-Tools als Subprozesse<br/>Analyse, Vorschlag, Apply, Upload"]
        DB[("Relationale Datenbank<br/>SQLAlchemy + Alembic<br/>SQLite oder Azure SQL")]
        STORE[("Artefakt- und Skill-Storage<br/>lokal oder Azure Blob Storage")]
    end

    AOAI["Azure OpenAI"]
    AISEARCH["Azure AI Search"]
    SPAPI["Smart-Planning-API"]
    EMAIL["Azure Communication Services Email"]

    USER <-->|"HTTPS / Browser"| UI
    UI <-->|"JSON über REST"| API
    API -->|"startet Tool/Pipeline"| RUNTIME
    API <-->|"Repository"| DB
    API <-->|"Snapshot- und Skill-Artefakte"| STORE
    RUNTIME <-->|"runtime_storage / StorageManager"| STORE
    API <-->|"LLM- und Embedding-Aufrufe"| AOAI
    API <-->|"Dokumentretrieval"| AISEARCH
    RUNTIME <-->|"REST, OAuth, Validierungsjobs"| SPAPI
    API -->|"explizit bestätigte Nachricht"| EMAIL

    MCP -->|"interne Tool-Fassade"| API
    MCP -->|"direkte Repository-Delegation"| DB

    classDef app fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    classDef external fill:#ede9fe,stroke:#7c3aed,color:#111;
    class UI,API,MCP,RUNTIME app;
    class DB,STORE data;
    class AOAI,AISEARCH,SPAPI,EMAIL external;
```

**Wichtige Präzisierung:** Die Linie `MCP → API` bezeichnet die Wiederverwendung derselben fachlichen Adapterlogik, nicht einen HTTP-Aufruf an Flask. `demo/mcp_connections/tools.py` importiert das Repository direkt; der E-Mail-Agent verwendet dieselben Tool-Funktionen in-process. Damit existiert nur eine Fachlogik, aber aktuell noch kein allgemeiner MCP-Host mit dynamischen Verbindungen zu externen MCP-Servern.

---

## 7. Diagramm 3 – Backend-Komponentensicht nach C4, Ebene 3 (IST)

**Aussage:** Der Backend-Container folgt einer klaren Schichtung: Eingangsadapter, Orchestration, spezialisierte Agenten, deterministische Fach-/Governance-Services und Persistenz. LLMs entscheiden über Routing und Vorschläge; harte Sicherheitsregeln wie Status-, Iterations-, Identitäts- und Action-Guards liegen dagegen in Python-Code.

```mermaid
flowchart LR
    subgraph ENTRY["Eingangsadapter"]
        CHATAPI["/api/chat"]
        REVIEWAPI["/api/review/*"]
        DASHAPI["/api/dashboard/metrics"]
        MCPSERVER["FastMCP server.py"]
    end

    subgraph ORCH["Agenten- und Orchestrationsschicht"]
        O["OrchestrationAgent<br/>Planning · Routing · Re-Planning · Interpretation"]
        C["ChatAgent"]
        R["RAGAgent"]
        S["SPAgent"]
        E["EmailAgent"]
    end

    subgraph DOMAIN["Deterministische Fach- und Governance-Schicht"]
        SPTOOLS["SP Tool-/Pipeline-Konfiguration"]
        REVIEW["Review-Service<br/>Decision commit + apply_after_review"]
        GUARDS["Apply Guards<br/>Status · Iteration · Identität · Action"]
        VALIDATION["Server Validation Trigger"]
        DASH["Dashboard Aggregation<br/>KPIs · Charts · Data Quality"]
        MCPTOOLS["MCP Tool Adapter"]
        EMAILTOOLS["Draft/Revise/Confirm/Send"]
        RULES["Rulebook Loader"]
        MEMORY["Short-term + episodisches Memory"]
        COST["Token-/Kostenmodell"]
    end

    subgraph PERSIST["Persistenz"]
        REPO["Repository<br/>einheitlicher DB-Zugriff"]
        DB[("SQL-Datenbank")]
        STORAGE[("Snapshot-/Skill-Storage")]
    end

    CHATAPI --> O
    O --> C
    O --> R
    O --> S
    O --> E
    S --> SPTOOLS
    SPTOOLS --> STORAGE
    SPTOOLS --> RULES
    SPTOOLS --> MEMORY

    REVIEWAPI --> REVIEW
    REVIEW --> GUARDS
    GUARDS --> S
    REVIEW --> VALIDATION
    REVIEW --> MEMORY

    DASHAPI --> DASH
    DASH --> REPO
    DASH --> COST

    MCPSERVER --> MCPTOOLS
    E --> MCPTOOLS
    MCPTOOLS --> REPO
    MCPTOOLS --> EMAILTOOLS
    EMAILTOOLS --> REPO

    CHATAPI --> REPO
    REVIEW --> REPO
    MEMORY --> REPO
    REPO --> DB

    classDef entry fill:#eff6ff,stroke:#3b82f6,color:#111;
    classDef agent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef domain fill:#ffedd5,stroke:#c2410c,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    class CHATAPI,REVIEWAPI,DASHAPI,MCPSERVER entry;
    class O,C,R,S,E agent;
    class SPTOOLS,REVIEW,GUARDS,VALIDATION,DASH,MCPTOOLS,EMAILTOOLS,RULES,MEMORY,COST domain;
    class REPO,DB,STORAGE data;
```

**Architekturargument für den Bericht:** Das System ist agentisch, aber nicht „prompt-only“. Nichtdeterministische Aufgaben – Sprachverständnis, Planung, Fehleranalyse, Korrekturvorschlag und Formulierung – werden LLM-gestützt ausgeführt. Zustandsübergänge, Persistenz, Berechtigungsgrenzen, Validierungstrigger, Action-Kompatibilität und Versandfreigabe werden deterministisch erzwungen. Diese Trennung ist der wesentliche Production-Readiness-Beitrag von PT4.

---

## 8. Diagramm 4 – Laufzeitsicht: allgemeine Chat-Anfrage (IST)

```mermaid
sequenceDiagram
    autonumber
    actor U as Nutzer
    participant UI as Chat-UI
    participant F as Flask /api/chat
    participant STM as Short-term Memory
    participant DB as Repository / DB
    participant O as Orchestrator
    participant L as Azure OpenAI
    participant A as gewählter Sub-Agent

    U->>UI: natürliche Anfrage oder + Tool-Auswahl
    UI->>F: message, session_id, selected_tool?
    F->>STM: DB-Session auflösen und Verlauf laden
    STM->>DB: Session/Nachrichten lesen
    F->>DB: User-Nachricht persistieren
    F->>O: execute(user_input, context)

    alt E-Mail explizit gewählt oder aktiver Draft-Follow-up
        O->>A: direkt zum EmailAgent routen
    else normale Anfrage
        O->>L: Single-/Multi-Step-Plan erzeugen
        L-->>O: strukturierter Ausführungsplan
        O->>A: passenden Agenten ausführen
    end

    A-->>O: Fachresultat + Tokenmetadaten
    opt Fachresultat benötigt Aufbereitung
        O->>L: Ergebnis kontextbezogen interpretieren
        L-->>O: Nutzerantwort
    end
    O-->>F: response + metadata
    F->>DB: Assistant-Nachricht und AgentRun persistieren
    F-->>UI: JSON-Antwort
    UI-->>U: Antwort / Vorschau / Link
```

**Codebezug:** `web_server.chat()` erzeugt den Kontext und persistiert Messages/AgentRun; `OrchestrationAgent.execute()` plant und kann bis zu viermal adaptiv neu planen; der E-Mail-Modus besitzt eine explizite Routing-Abkürzung, damit eine sichtbare Draft-Konversation nicht versehentlich zu einem anderen Agenten springt.

---

## 9. Diagramm 5 – Kernablauf: Human-in-the-Loop-Korrektur (IST)

**Aussage:** Der zentrale Kontrollpunkt liegt nicht nur in der UI. Der Orchestrator blockiert Auto-Apply, die Entscheidung wird transaktional persistiert und `_apply_after_review()` prüft die Autorisierung erneut aus der Datenbank. Erst danach darf die bestehende Apply-Pipeline schreiben.

```mermaid
sequenceDiagram
    autonumber
    actor P as Produktionsplaner
    actor H as Human Reviewer
    participant O as Orchestrator
    participant SP as SPAgent / analyze_only
    participant GEN as Correction Pipeline
    participant DB as Repository / DB
    participant UI as Review Board
    participant REV as Review-Service
    participant G as Apply Guards
    participant API as Smart-Planning-API
    participant MEM as Episodisches Memory

    P->>O: „Korrigiere den Snapshot“
    Note over O: HUMAN_IN_THE_LOOP=true
    O->>SP: full_correction wird auf analyze_only umgebogen
    SP->>GEN: validate → identify → generate → schema check
    GEN->>DB: Proposal status=pending_review speichern
    GEN-->>O: proposal_id und Review-Hinweis
    O-->>P: Deep-Link zum Review Board

    H->>UI: Vorschlag öffnen
    UI->>REV: Detail, Diff, Confidence, Evidence, Memory anfordern
    REV->>DB: Proposal, Entscheidung und Präzedenzfälle lesen
    DB-->>REV: reviewfähiger Datensatz
    REV-->>UI: Detail-Response
    H->>UI: Approve / Modify / Reject + Kommentar
    UI->>REV: Decision Endpoint
    REV->>DB: Entscheidung + Proposal-Status atomar committen

    alt Reject
        REV->>MEM: negativen menschlichen Präzedenzfall speichern
        REV-->>UI: applied=false
    else Approve oder Modify
        REV->>G: Status, Review-Zeile, Iteration, Identität, Action prüfen
        alt Guard blockiert
            G-->>REV: 409 oder 422, nichts angewendet
            REV->>MEM: entschiedenen Fall auditierbar speichern
            REV-->>UI: Entscheidung bleibt committed
        else Guards erfolgreich
            REV->>API: serverseitige Vorher-Validierung triggern
            API-->>REV: errors_before
            REV->>SP: apply_and_upload
            SP->>API: Korrektur anwenden und Snapshot hochladen
            REV->>API: serverseitige Nachher-Validierung triggern
            API-->>REV: errors_after
            REV->>DB: revalidation_result + status=applied
            REV->>MEM: menschlich entschiedenen Fall speichern
            REV-->>UI: applied=true + Revalidierung
        end
    end
```

**Fehlersemantik:** Fällt die Pipeline oder die Netzvalidierung aus, bleibt die menschliche Entscheidung absichtlich committed. Der Status bleibt `approved` beziehungsweise `modified`, `revalidation_result` dokumentiert `failed_at` und `error`, und der Endpunkt antwortet geordnet mit HTTP 502 statt mit einem ungefangenen 500. Der Recovery-Weg ist ein erneuter Apply-Versuch, kein Zurücksetzen der menschlichen Entscheidung.

**Literaturbezug:** NIST fordert klar definierte Rollen und Verantwortlichkeiten für Human-AI-Entscheidungen. Hier ist der Mensch nicht nur informell „in the loop“, sondern besitzt die exklusive Autorität für den Übergang vom Vorschlag zur Mutation. Die KI kann diesen Übergang nicht durch eine Prompt-Entscheidung umgehen.

---

## 10. Diagramm 6 – Zustandsautomat eines Korrekturvorschlags (IST)

```mermaid
stateDiagram-v2
    [*] --> pending_review: KI erzeugt und persistiert Proposal

    pending_review --> rejected: Reject + Pflichtkommentar
    pending_review --> approved: Approve committed
    pending_review --> modified: Modify + final_value committed

    approved --> applied: Guards + Apply + Upload erfolgreich
    modified --> applied: Guard-kompatibler Menschenwert + Apply erfolgreich

    approved --> approved: 409/422/502 · entschieden, nicht angewendet
    modified --> modified: 409/422/502 · entschieden, nicht angewendet

    rejected --> [*]: keine Mutation
    applied --> [*]: Revalidierung auditierbar

    note right of pending_review
      Nur dieser Zustand darf
      neu entschieden werden.
    end note

    note right of approved
      Bei technischem Fehler bleibt
      die Entscheidung erhalten.
    end note
```

**Invariante:** Eine wiederholte Generierung derselben deterministischen `proposal_id` darf eine bereits getroffene Entscheidung nicht auf `pending_review` zurücksetzen. Das Repository schützt diesen Fall ausdrücklich.

---

## 11. Diagramm 7 – Relationales Datenmodell (IST)

```mermaid
erDiagram
    SESSIONS ||--o{ MESSAGES : contains
    SESSIONS ||--o{ AGENT_RUNS : records
    SESSIONS ||--o{ EMAIL_DRAFTS : owns
    SNAPSHOTS_META ||--o{ PROPOSALS : groups
    PROPOSALS ||--o{ REVIEWS : receives
    PROPOSALS ||--o{ MEMORY_ITEMS : source_of

    SESSIONS {
        int id PK
        datetime started_at
        string snapshot_id
        string user_ref
    }
    MESSAGES {
        int id PK
        int session_id FK
        string role
        string agent_name
        text content
        datetime created_at
    }
    AGENT_RUNS {
        int id PK
        int session_id FK
        string agent_name
        string tool_name
        string status
        int tokens_prompt
        int tokens_completion
        float cost_estimate
        int duration_ms
    }
    SNAPSHOTS_META {
        string snapshot_id PK
        string name
        int errors_before
        int warnings_before
        int errors_after
        int warnings_after
        datetime last_validated_at
    }
    PROPOSALS {
        string proposal_id PK
        string snapshot_id FK
        string error_type
        string target_path
        json old_value
        json suggested_value
        text reasoning
        json evidence
        float confidence_score
        float value_grounded
        float memory_support
        string formula_version
        string status
    }
    REVIEWS {
        int id PK
        string proposal_id FK
        string decision
        json final_value
        text comment
        string reviewer_ref
        datetime decided_at
        json revalidation_result
    }
    EMAIL_DRAFTS {
        string id PK
        int session_id FK
        string recipient
        string subject
        text body_plain
        text body_html
        string status
        int version
        string provider_message_id
        datetime sent_at
    }
    MEMORY_ITEMS {
        int id PK
        string source_proposal_id FK
        string error_type
        string affected_entity_pattern
        json suggested_value
        json final_value
        string decision
        text comment
        boolean revalidation_ok
    }
```

**Architekturargument:** Die Datenbank ist nicht nur technischer Speicher, sondern der Governance-Backbone. `proposals` hält die KI-Behauptung, `reviews` die menschliche Entscheidung, `memory_items` den daraus abgeleiteten Präzedenzfall und `agent_runs` die Betriebsmetrik. Dadurch bleiben Vorschlag, Entscheidung, Lerneffekt und Kosten analytisch trennbar.

---

## 12. Diagramm 8 – Gedächtnis- und Wissensarchitektur (IST)

**Aussage:** Das System besitzt drei fachlich verschiedene Kontextquellen. Sie dürfen im Bericht nicht zu einem einzigen unscharfen „Memory“ zusammengezogen werden.

```mermaid
flowchart TB
    INPUT["Aktuelle Nutzeranfrage oder neuer Validierungsfehler"]
    ORCH["Orchestrator / Correction Generator"]

    subgraph WORKING["Arbeitsgedächtnis · short-term"]
        MSG[("sessions + messages")]
        WINDOW["Sliding Window<br/>max. 5 User/Assistant-Paare"]
    end

    subgraph RULEBOOK["Regelwissen · Rulebook Layer"]
        INDEX["Index aller Karten<br/>Dateiname + Beschreibung"]
        CORE["_core.md"]
        CARDS["selektiv geladene Markdown-Karten"]
        MONO["byte-identischer Monolith<br/>A/B-Rückfallebene"]
    end

    subgraph EPISODIC["Langzeitgedächtnis · episodische Fälle"]
        REVIEWS[("menschliche Reviews")]
        CASES[("memory_items")]
        RETRIEVAL["Ähnlichkeit über<br/>affected_entity_pattern"]
        SUPPORT["memory_support<br/>0 · 0,5 · 1"]
    end

    INPUT --> ORCH
    MSG --> WINDOW --> ORCH

    INDEX --> ORCH
    ORCH -->|"wählt relevante_cards"| CARDS
    CORE --> CARDS
    MONO -.->|"RULEBOOK_MODE=monolith"| ORCH
    CARDS -->|"Domänenheuristiken im Prompt"| ORCH

    REVIEWS -->|"record_case_safe"| CASES
    CASES --> RETRIEVAL
    INPUT --> RETRIEVAL
    RETRIEVAL -->|"Top-k menschlich entschiedene Präzedenzfälle"| ORCH
    RETRIEVAL --> SUPPORT
    SUPPORT -->|"deterministischer Confidence-Term"| ORCH

    ORCH --> OUTPUT["Korrekturvorschlag mit<br/>Reasoning, Evidence und Confidence v3"]

    classDef compute fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    classDef knowledge fill:#fef3c7,stroke:#b45309,color:#111;
    class INPUT,ORCH,WINDOW,RETRIEVAL,SUPPORT,OUTPUT compute;
    class MSG,REVIEWS,CASES data;
    class INDEX,CORE,CARDS,MONO knowledge;
```

### 12.1 Einordnung gegenüber CoALA

Das CoALA-Modell liefert eine nützliche Begriffsschablone für Arbeits- und Langzeitgedächtnis, Entscheidungsprozess und Aktionen. Die konkrete PT4-Implementierung ist jedoch kleiner und bewusst pragmatisch:

- `memory.short_term` ist persistierter Session-Kontext mit begrenztem Promptfenster.
- `memory_items` sind episodische, von echten menschlichen Entscheidungen abgeleitete Fälle.
- `demo/skills/*.md` bilden ein **Rulebook Layer**. Die Karten enthalten sowohl Handlungsregeln als auch Domänenwissen und werden deshalb im Plan bewusst nicht streng als „prozedurales Gedächtnis“ bezeichnet.
- Das System lernt nicht autonom neue Regeln. AP-X würde lediglich Regeländerungen vorschlagen; menschliche Freigabe und Versionierung blieben zwingend.

### 12.2 Confidence als nachvollziehbare Aggregation

```mermaid
flowchart LR
    SELF["LLM-Selbsteinschätzung<br/>llm_confidence"] --> W1["× 0,5"]
    GROUND["deterministische Datenbelegbarkeit<br/>value_grounded"] --> W2["× 0,3"]
    MEMORY["menschlich bestätigte Präzedenz<br/>memory_support"] --> W3["× 0,2"]
    W1 --> SUM["confidence_score<br/>formula_version v3"]
    W2 --> SUM
    W3 --> SUM
    MANUAL["manual_intervention_required"] --> ZERO["Confidence = 0"]

    classDef ai fill:#ede9fe,stroke:#7c3aed,color:#111;
    classDef det fill:#dcfce7,stroke:#15803d,color:#111;
    classDef result fill:#dbeafe,stroke:#2563eb,color:#111;
    class SELF ai;
    class GROUND,MEMORY,W1,W2,W3,MANUAL,ZERO det;
    class SUM result;
```

`value_grounded` stellt in v3 je Feldklasse eine andere deterministische Frage: neue Identitäten müssen eindeutig sein und der erkannten ID-Konvention folgen; Referenzen müssen existieren; Wertfelder müssen aus vergleichbaren Daten ableitbar sein; neue Array-Objekte werden auf Identität und Referenzen geprüft. Die Kennzahl misst bei Wertfeldern weiterhin Belegbarkeit, nicht garantierte fachliche Korrektheit – eine wichtige Einschränkung für die Evaluation.

---

## 13. Diagramm 9 – MCP-Ist-Architektur und reale Protokollgrenze (IST)

**Aussage:** AP5 implementiert einen echten FastMCP-Server mit standardisierten Tool-Schemas. Die laufende Webanwendung verwendet dieselben Tool-Funktionen intern. Ein universeller MCP-Host, der dynamisch mehrere externe MCP-Server verbindet, ist noch nicht Bestandteil des Systems.

```mermaid
flowchart LR
    subgraph CALLERS["Aufrufer"]
        EXT["Externer MCP-Client<br/>für PT4 nur lokaler Nachweis"]
        EMAILAGENT["EmailAgent<br/>In-Process-Aufruf"]
    end

    subgraph MCPBOUNDARY["demo/mcp_connections"]
        SERVER["server.py<br/>FastMCP · stdio"]
        TOOLS["tools.py<br/>standardisierte Tool-Fassade"]
        NOTIFIER["notifier.py<br/>ACS-/SendGrid-Provideradapter"]
    end

    REPO["db/repository.py<br/>bestehende Fach- und DB-Logik"]
    DB[("SQL-Datenbank")]
    ACS["Azure Communication Services Email"]

    EXT -->|"MCP / JSON-RPC über stdio"| SERVER
    SERVER --> TOOLS
    EMAILAGENT -->|"direkter Python-Aufruf"| TOOLS
    TOOLS -->|"keine eigene SQL-Implementierung"| REPO
    REPO --> DB
    TOOLS -->|"nur bei confirmed=true"| NOTIFIER
    NOTIFIER --> ACS

    AUTO["Proposal-Generator Hook"] -.->|"Kompatibilitätsaufruf,<br/>sendet absichtlich nie"| NOTIFIER

    classDef caller fill:#fff4ce,stroke:#8a6d1d,color:#111;
    classDef own fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    classDef external fill:#ede9fe,stroke:#7c3aed,color:#111;
    class EXT,EMAILAGENT caller;
    class SERVER,TOOLS,NOTIFIER,REPO,AUTO own;
    class DB data;
    class ACS external;
```

### 13.1 Registrierte MCP-Tools

| Domäne | Tools | Wirkung |
|---|---|---|
| Review lesen | `get_pending_reviews`, `get_review_details`, `get_snapshot_status` | Repository-Lesezugriff |
| Review entscheiden | `approve_correction`, `reject_correction`, `modify_correction` | Entscheidung persistieren; keine Apply-Pipeline starten |
| Dashboard | `get_dashboard_metrics` | kompakte Repository-Kennzahlen |
| E-Mail | `create_email_draft`, `get_email_draft`, `revise_email_draft`, `send_email_draft`, `cancel_email_draft` | persistenter Freigabe-Workflow |

### 13.2 Ehrliche Abgrenzung zur offiziellen MCP-Architektur

Die offizielle MCP-Architektur beschreibt einen **Host**, der für jeden verbundenen **Server** eine eigene **Client**-Instanz verwaltet. Im Projekt vorhanden sind:

- ein MCP-Server,
- standardisierte MCP-Tools,
- ein interner Adapteraufruf durch den E-Mail-Agenten.

Noch nicht vorhanden sind:

- ein allgemeiner MCP-Host/Client-Manager,
- dynamische Tool-Discovery über mehrere externe Server,
- eine deklarative Connection Registry,
- Remote-MCP über Streamable HTTP,
- OAuth- und rollenbasierte MCP-Autorisierung.

Diese Abgrenzung ist wichtig: AP5/M5 ist erfüllt, weil aufrufbare MCP-Tools und ein durchgehender Enterprise-Fall existieren. Die langfristige Vision einer beliebig erweiterbaren Connection-Plattform ist jedoch ein nachvollziehbares nächstes Architekturinkrement, nicht bereits der Ist-Zustand.

---

## 14. Diagramm 10 – Konversationeller E-Mail-Workflow (IST)

```mermaid
sequenceDiagram
    autonumber
    actor U as Nutzer
    participant UI as Chat-UI
    participant O as Orchestrator
    participant E as EmailAgent
    participant T as MCP Tool Adapter
    participant DB as Repository / email_drafts
    participant ACS as Azure Communication Services

    U->>UI: „Schreibe eine E-Mail an …“
    UI->>O: Nachricht + optional selected_tool=email
    O->>E: explizites oder natürlichsprachiges Routing

    opt Snapshot-/Review-Bezug angefordert
        E->>T: get_review_details / get_snapshot_status
        T->>DB: verifizierte Falldaten lesen
        DB-->>E: Problem, Vorschlag, Status, Deep-Link
    end

    E->>E: Empfänger, Betreff und Inhalt formulieren
    E->>T: create_email_draft
    T->>DB: Draft Version 1 persistieren
    T-->>E: persistierter Entwurf
    E-->>U: exakte Vorschau + Hinweis „Bitte absenden“

    alt Nutzer verlangt Änderung
        U->>E: Änderungswunsch
        E->>T: revise_email_draft
        T->>DB: Version erhöhen
        E-->>U: aktualisierte Vorschau
    else Nutzer sagt nur „Ja, passt“
        E-->>U: Entwurf bleibt offen, kein Versand
    else Nutzer sagt ausdrücklich „Bitte absenden“
        E->>T: send_email_draft(confirmed=true)
        T->>DB: aktuellen Draft und Status lesen
        T->>ACS: exakt persistierte Nachricht senden
        ACS-->>T: Provider Message ID
        T->>DB: status=sent, sent_at, provider_message_id
        E-->>U: Versand bestätigt
    else Nutzer bricht ab
        E->>T: cancel_email_draft
        T->>DB: status=cancelled
        E-->>U: Abbruch bestätigt
    end
```

### 14.1 Draft-Zustandsautomat

```mermaid
stateDiagram-v2
    [*] --> draft: create_email_draft
    draft --> draft: revise / version + 1
    draft --> draft: „Ja, passt“ / keine Mutation
    draft --> sent: explizites „Bitte absenden“
    draft --> cancelled: Abbruch
    sent --> sent: erneuter Send-Aufruf / already_sent
    sent --> [*]
    cancelled --> [*]
```

**Governance-Argument:** Die Versandfreigabe ist nicht nur eine höfliche Rückfrage des LLM. `send_email_draft()` verlangt technisch `confirmed=True`, lädt exakt den persistierten Entwurf und verhindert erneuten Versand eines bereits gesendeten Drafts. Der automatische Proposal-Notifier bleibt aus Kompatibilitätsgründen aufrufbar, liefert aber immer `skipped` und kann keine Nachricht senden.

---

## 15. Diagramm 11 – Dashboard-Datenfluss und Messlogik (IST)

```mermaid
flowchart LR
    subgraph SOURCES["Operative Primärdaten"]
        S[("snapshots_meta")]
        P[("proposals")]
        R[("reviews")]
        A[("agent_runs")]
    end

    REPO["repository.fetch_metrics_data()"]
    RANGE["Zeitbereich auflösen<br/>Preset · from/to · Granularität"]
    METRICS["compute_metrics()<br/>Flow-/Bestands-Trennung"]
    QUALITY["Data-Quality-Regeln<br/>keine stille Datenbereinigung"]
    COST["cost_model.py<br/>Input-/Output-Preise getrennt"]
    API["GET /api/dashboard/metrics"]

    subgraph UI["Dashboard-UI"]
        KPI["KPI-Karten + AK2-Meter"]
        SVG["Inline-SVG-Charts<br/>Zeitreihe · Fehlerarten · Confidence · Kalibrierung"]
        OPEN["aktuell offene Reviews<br/>mit Deep-Link"]
        FLAGS["sichtbare Belastbarkeitshinweise"]
    end

    S --> REPO
    P --> REPO
    R --> REPO
    A --> REPO
    REPO --> RANGE --> METRICS
    REPO --> METRICS
    A --> COST --> METRICS
    METRICS --> QUALITY
    METRICS --> API
    QUALITY --> API
    API --> KPI
    API --> SVG
    API --> OPEN
    API --> FLAGS

    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    classDef compute fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef quality fill:#ffedd5,stroke:#c2410c,color:#111;
    classDef view fill:#f3e8ff,stroke:#7e22ce,color:#111;
    class S,P,R,A data;
    class REPO,RANGE,METRICS,COST,API compute;
    class QUALITY quality;
    class KPI,SVG,OPEN,FLAGS view;
```

### 15.1 Fluss und Bestand

Das Zeitfenster darf nicht auf jede Kennzahl gleich angewandt werden:

- **Flussgrößen** wie erzeugte Proposals, Entscheidungen, Tokens und Kosten werden nach ihrem Ereigniszeitpunkt gefiltert.
- **Bestandsgrößen** wie die aktuell offenen Reviews beschreiben den momentanen Rückstand und bleiben unabhängig vom gewählten Zeitraum sichtbar.

### 15.2 Data Quality als Architekturmerkmal

Das Dashboard kennzeichnet unter anderem alte Confidence-Formeln, Legacy-Error-Labels, unzuverlässige Vor-AP3.3d-Revalidierungen, Test-Fixtures, unvollständige Tokens, Kostenschätzungen und kleine Stichproben. Diese Hinweise sind kein kosmetischer Zusatz: Sie verhindern, dass historisch heterogene Daten als scheinbar präzise Qualitätsaussage präsentiert werden.

**Wichtige Berichtsregel:** Für die AP-E-Kalibrierung muss genau eine `formula_version` – aktuell v3 – ausgewählt werden. Gemischte Formelgenerationen dürfen nicht als gemeinsame Kalibrierung interpretiert werden.

---

## 16. Diagramm 12 – Deployment-Sicht: lokal und Azure (IST-fähig)

**Aussage:** Derselbe Anwendungscode unterstützt lokale Entwicklung und ein getrenntes Azure-Deployment. Die Umschaltung von SQL- und Artefaktpersistenz erfolgt über Umgebungsvariablen, nicht durch Code-Forks.

```mermaid
flowchart TB
    subgraph LOCAL["Lokale Entwicklung"]
        LB["Browser<br/>localhost:8000"]
        LF["Flask Development Server<br/>web_server.py"]
        LM["optionaler FastMCP-stdio-Prozess"]
        LS[("SQLite<br/>demo/db/pt4.sqlite3")]
        LFS[("lokales Dateisystem<br/>smart-planning/Snapshots + skills")]
        LB --> LF
        LM --> LS
        LF --> LS
        LF --> LFS
    end

    subgraph AZURE["Azure-Zieltopologie"]
        USER["Browser"]
        SWA["Azure Static Web Apps<br/>demo/ui"]
        CA["Azure Container Apps<br/>Gunicorn + Flask<br/>non-root Docker-Image"]
        ACR["Azure Container Registry"]
        SQL[("Azure SQL<br/>DATABASE_URL")]
        BLOB[("Azure Blob Storage<br/>STORAGE_MODE=AZURE")]
        KV["Environment / Key Vault<br/>Secrets injizieren"]
        USER --> SWA
        SWA -->|"HTTPS REST"| CA
        ACR -->|"Container Image"| CA
        CA --> SQL
        CA --> BLOB
        KV --> CA
    end

    subgraph EXTERNAL["Gemeinsame externe Dienste"]
        AOAI["Azure OpenAI"]
        SEARCH["Azure AI Search"]
        ACS["Azure Communication Services"]
        SP["Smart-Planning-API"]
    end

    LF --> AOAI
    LF --> SEARCH
    LF --> ACS
    LF --> SP
    CA --> AOAI
    CA --> SEARCH
    CA --> ACS
    CA --> SP

    classDef local fill:#f8fafc,stroke:#64748b,color:#111;
    classDef azure fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef data fill:#dcfce7,stroke:#15803d,color:#111;
    classDef external fill:#ede9fe,stroke:#7c3aed,color:#111;
    class LB,LF,LM local;
    class USER,SWA,CA,ACR,KV azure;
    class LS,LFS,SQL,BLOB data;
    class AOAI,SEARCH,ACS,SP external;
```

**Nicht überzeichnen:** Das Repository enthält die Deployment-Workflows und die Zielkonfiguration. Ob jede dargestellte Azure-Ressource zum Abgabezeitpunkt produktiv provisioniert und dauerhaft betrieben wird, muss im Bericht anhand der tatsächlichen Azure-Umgebung belegt werden. Das Diagramm zeigt die durch Code und Workflows unterstützte Topologie.

---

## 17. Diagramm 13 – Trust Boundaries, Secrets und kontrollierte Seiteneffekte (IST)

```mermaid
flowchart LR
    subgraph CLIENT["Nicht vertrauenswürdige Eingabe"]
        BROWSER["Browser / Nutzereingabe"]
        MCPCLIENT["MCP-Client"]
    end

    subgraph APP["Anwendungs-Vertrauensgrenze"]
        FLASK["Flask API<br/>Request-Validierung"]
        MCPSERVER["FastMCP Server<br/>Tool-Schema und Dispatch"]
        ORCH["LLM-Orchestrator<br/>nichtdeterministische Entscheidung"]
        GATES["Deterministische Gates<br/>HitL · Status · Iteration · Identität · Action"]
        CONFIRM["E-Mail confirmed=true<br/>persistierter Draft"]
        REPO["Repository-Transaktionen"]
    end

    subgraph SECRETS["Secret-Grenze"]
        ENV[".env lokal / App Settings / Key Vault"]
    end

    subgraph EXTERNAL["Externe Vertrauensgrenzen"]
        AOAI["Azure OpenAI"]
        SP["Smart-Planning-API"]
        ACS["ACS Email"]
        SQL[("SQL / Blob Storage")]
    end

    BROWSER --> FLASK
    MCPCLIENT --> MCPSERVER
    FLASK --> ORCH
    MCPSERVER --> REPO
    MCPSERVER --> CONFIRM
    ORCH -->|"Vorschlag"| GATES
    GATES -->|"nur nach Review"| SP
    ORCH -->|"Draft"| CONFIRM
    CONFIRM -->|"nur nach expliziter Freigabe"| ACS
    FLASK --> REPO --> SQL
    ORCH --> AOAI
    ENV --> FLASK
    ENV --> ORCH
    ENV --> CONFIRM

    classDef untrusted fill:#fee2e2,stroke:#b91c1c,color:#111;
    classDef trusted fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef gate fill:#ffedd5,stroke:#c2410c,color:#111;
    classDef secret fill:#fef3c7,stroke:#a16207,color:#111;
    classDef ext fill:#ede9fe,stroke:#7c3aed,color:#111;
    class BROWSER,MCPCLIENT untrusted;
    class FLASK,MCPSERVER,ORCH,REPO trusted;
    class GATES,CONFIRM gate;
    class ENV secret;
    class AOAI,SP,ACS,SQL ext;
```

### 17.1 Bereits vorhandene Kontrollen

- Secrets werden aus Environment/.env gelesen und nicht im Quellcode hardcodiert.
- Der Docker-Prozess läuft als Non-Root-User.
- Das Backend setzt CSP-, Frame-, Content-Type- und Referrer-Header.
- Review-Entscheidung und Statusänderung werden transaktional geschrieben.
- Der Apply-Pfad revalidiert seine Autorisierung aus der DB.
- E-Mail-Versand erfordert einen persistierten Draft und explizite Freigabe.
- Fehler im ehemaligen automatischen Notification-Hook können keine Mail mehr auslösen.

### 17.2 Bewusst außerhalb des PT4-Scopes oder noch offen

- Authentifizierung und rollenbasierte Autorisierung der MCP-Tools.
- Produktiver Remote-MCP-Transport mit OAuth.
- Atomarer `draft → sending → sent`-Übergang für hochparallelen E-Mail-Versand.
- Outbox, Provider-Idempotency-Key und Delivery-/Bounce-Webhooks.
- Vollständige produktive Identity-Lösung für `reviewer_ref`.

---

## 18. Diagramm 14 – CI/CD- und Deployment-Pipeline (IST)

```mermaid
flowchart LR
    DEV["Git Repository"]

    subgraph BACKEND["GitHub Actions: deploy-backend"]
        B1["Checkout"] --> B2["Docker Buildx"]
        B2 --> B3["Azure Login via OIDC"]
        B3 --> B4["ACR dynamisch auflösen"]
        B4 --> B5["Docker-Image bauen"]
        B5 --> B6["Version + latest nach ACR pushen"]
    end

    subgraph FRONTEND["GitHub Actions: deploy-frontend"]
        F1["Checkout"] --> F2["Azure Login via OIDC"]
        F2 --> F3["Container-App-FQDN ermitteln"]
        F3 --> F4["BACKEND_URL_PLACEHOLDER ersetzen"]
        F4 --> F5["demo/ui zu Static Web Apps deployen"]
    end

    DEV --> B1
    DEV --> F1
    B6 --> ACR[("Azure Container Registry")]
    F5 --> SWA["Azure Static Web Apps"]
    F3 --> CA["bestehende Azure Container App"]
    ACR -.->|"Image-Rollout separat erforderlich"| CA

    classDef source fill:#f8fafc,stroke:#64748b,color:#111;
    classDef pipeline fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef target fill:#dcfce7,stroke:#15803d,color:#111;
    class DEV source;
    class B1,B2,B3,B4,B5,B6,F1,F2,F3,F4,F5 pipeline;
    class ACR,SWA,CA target;
```

**Wichtiger Befund:** Der Backend-Workflow baut und pusht das Image, zeigt im vorliegenden YAML aber keinen expliziten Schritt, der die Azure Container App auf den neuen Image-Tag aktualisiert. Für den Bericht sollte deshalb zwischen **Image-Bereitstellung** und **tatsächlichem Container-App-Rollout** unterschieden werden. Der Frontend-Workflow deployt dagegen direkt zu Azure Static Web Apps.

---

## 19. Diagramm 15 – Zukunftsbild für erweiterbare MCP-Connections (ZIEL, nicht implementiert)

**Aussage:** Für die Vision „GitHub, Wikipedia, SharePoint oder weitere Systeme einfach ergänzen“ reicht ein Ordner mit anwendungsspezifischen SDK-Adaptern nicht aus. Benötigt wird ein MCP-Host mit Client-Lifecycle, Discovery, Namespace- und Policy-Schicht. Die vorhandenen internen Tools können dabei kompatibel weiterlaufen.

```mermaid
flowchart LR
    USER["Nutzer"] --> ORCH["Orchestrator / MCP Host"]

    subgraph PLATFORM["ZIEL: demo/mcp Plattform"]
        REG["Connection Registry<br/>deklarative Konfiguration"]
        MANAGER["Client Manager<br/>stdio + Streamable HTTP"]
        CATALOG["dynamische Tool Discovery<br/>Namespacing"]
        POLICY["Policy Engine<br/>read · write · destructive · confirmation"]
        HEALTH["Lifecycle, Health, Timeout, Audit"]
    end

    ORCH --> CATALOG
    REG --> MANAGER
    MANAGER --> CATALOG
    CATALOG --> POLICY
    POLICY --> HEALTH

    subgraph SERVERS["MCP-Server"]
        INTERNAL["internal.*<br/>Review · Dashboard · E-Mail-Drafts"]
        GITHUB["github.*<br/>Repository, Issues, Pull Requests"]
        WIKI["wikipedia.*<br/>Recherche"]
        SHAREPOINT["sharepoint.*<br/>Unternehmensdokumente"]
    end

    HEALTH --> INTERNAL
    HEALTH --> GITHUB
    HEALTH --> WIKI
    HEALTH --> SHAREPOINT

    subgraph INTEGRATIONS["Domänenspezifische Integrationen außerhalb des MCP-Kerns"]
        EMAIL["integrations/email<br/>Service + ACS-/SendGrid-Provider"]
    end

    INTERNAL --> EMAIL

    classDef target fill:#f8fafc,stroke:#64748b,stroke-dasharray:6 4,color:#111;
    classDef current fill:#dbeafe,stroke:#2563eb,color:#111;
    class USER,ORCH current;
    class REG,MANAGER,CATALOG,POLICY,HEALTH,INTERNAL,GITHUB,WIKI,SHAREPOINT,EMAIL target;
```

### 19.1 Empfohlene Zielstruktur

```text
demo/
├── mcp/
│   ├── host/
│   │   ├── connection_manager.py
│   │   ├── registry.py
│   │   ├── tool_catalog.py
│   │   ├── router.py
│   │   └── policies.py
│   ├── servers/
│   │   └── internal/
│   │       ├── server.py
│   │       └── tools/
│   │           ├── review.py
│   │           ├── dashboard.py
│   │           └── email.py
│   ├── clients/
│   │   ├── stdio_client.py
│   │   └── http_client.py
│   └── connections/
│       ├── github.yaml
│       ├── wikipedia.yaml
│       └── sharepoint.yaml
└── integrations/
    └── email/
        ├── service.py
        └── providers/
            ├── acs.py
            └── sendgrid.py
```

**Begründung:** `mcp/` sollte Protokoll-, Client- und Serverinfrastruktur enthalten. ACS ist dagegen ein konkreter E-Mail-Provider und kein MCP-Protokollbaustein; seine natürliche Heimat ist `integrations/email/providers/acs.py`. Diese Trennung verhindert, dass jede neue Verbindung zu einem anders strukturierten Sonderfall wird.

**Migrationsprinzip:** Die bestehende Agentenfunktionalität bleibt erhalten, indem `demo/mcp_connections/` vorübergehend als Kompatibilitätsfassade bestehen bleibt. Erst wenn Chat-E-Mail, Review-Tools, Dashboard-Tool, Freigabegates und Idempotenztests grün sind, wird auf die neue interne Struktur umgestellt.

---

## 20. Diagramm 16 – Traceability von Arbeitspaketen zu Architekturbausteinen (IST)

```mermaid
flowchart LR
    AP1["AP1<br/>Proposal + Confidence"] --> GEN["Correction Generator"]
    AP2["AP2<br/>Persistenz"] --> DB["Repository + SQLAlchemy + Alembic"]
    AP3["AP3<br/>HitL Backend"] --> REVIEW["Review-Service + Apply Guards"]
    AP4["AP4<br/>HitL Frontend"] --> RUI["Review Board + Diff + Deep-Link"]
    AP5["AP5<br/>MCP + E-Mail"] --> MCP["FastMCP Tools + EmailAgent + ACS"]
    AP6["AP6<br/>Dashboard"] --> DASH["Metrics API + SVG Dashboard + Data Quality"]
    AP7["AP7<br/>Memory"] --> MEM["Rule Cards + Short-term + Episodic Cases"]
    APE["AP-E<br/>Evaluation · teilweise offen"] -.-> EVAL["Testkatalog + Seeding + A/B + Demo"]
    APX["AP-X<br/>geparkt"] -.-> DISTILL["menschlich freizugebende Rule Distillation"]

    GEN --> REVIEW
    DB --> REVIEW
    REVIEW --> RUI
    REVIEW --> MEM
    DB --> DASH
    DB --> MCP
    MEM --> GEN
    GEN --> EVAL
    DASH --> EVAL
    MEM -.-> DISTILL

    classDef done fill:#dcfce7,stroke:#15803d,color:#111;
    classDef comp fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef open fill:#f8fafc,stroke:#64748b,stroke-dasharray:6 4,color:#111;
    class AP1,AP2,AP3,AP4,AP5,AP6,AP7 done;
    class GEN,DB,REVIEW,RUI,MCP,DASH,MEM comp;
    class APE,APX,EVAL,DISTILL open;
```

**Akzeptanzkriterien:** AK1 wird primär durch AP1, AK2 durch Proposal-Qualität plus AP-E, AK3 durch AP3/AP4, AK4 durch AP5, AK5 durch AP6 und AK6 durch AP7 adressiert. M8 bleibt offen, solange Seeding, vollständige A/B-Auswertung und Abschlussdemo nicht finalisiert sind.

---

## 21. Empfohlene Auswahl und Platzierung im Projektbericht

Nicht alle Diagramme müssen in den Haupttext. Eine überzeugende, kompakte Auswahl wäre:

1. **Kapitel „Ausgangslage und Systemabgrenzung“:** Diagramm 1.
2. **Kapitel „Lösungsarchitektur“:** Diagramme 2 und 3.
3. **Kapitel „Human-in-the-Loop Governance“:** Diagramme 5 und 6.
4. **Kapitel „Persistenz und lernendes System“:** Diagramme 7 und 8.
5. **Kapitel „MCP und Enterprise-Integration“:** Diagramme 9 und 10.
6. **Kapitel „Messbarkeit und Dashboard“:** Diagramm 11.
7. **Kapitel „Deployment und Übertragbarkeit“:** Diagramm 12; optional 14.
8. **Kapitel „Grenzen und Ausblick“:** Diagramm 15.

Die übrigen Diagramme eignen sich für Anhang, technische Dokumentation oder Präsentation.

## 22. Empfohlene Struktur des Projektberichts

### 22.1 Problem und Ausgangslage

Den Ausgangspunkt nicht als „es fehlte ein Dashboard“ formulieren, sondern als Governance-Problem: Die bestehende Korrekturpipeline konnte Änderungen autonom anwenden, ohne reviewfähigen Vorschlag, persistierte Entscheidung, belastbare Revalidierung oder systemweite Qualitätsmetriken. Daraus leiten sich die Akzeptanzkriterien logisch ab.

### 22.2 Anforderungen und Qualitätsziele

Die Architekturentscheidungen an konkrete Qualitätsziele binden:

- **Kontrollierbarkeit:** kein Apply ohne menschliche Entscheidung.
- **Nachvollziehbarkeit:** getrennte Speicherung von KI-Vorschlag, Menschenwert, Kommentar und Revalidierung.
- **Robustheit:** geordnete 4xx/502-Fehler statt stiller Mutation oder ungefangener Exceptions.
- **Erweiterbarkeit:** Repository-Fassade, MCP-Tools, Storage- und DB-Abstraktion.
- **Messbarkeit:** Token, Kosten, Bearbeitungszeit, Acceptance und Kalibrierung.
- **Lernfähigkeit:** menschliche Entscheidungen werden als Präzedenzfälle genutzt, ohne Entscheidungen zu erfinden.

### 22.3 Architekturentscheidungen statt Dateiaufzählung

Im Haupttext nicht primär erklären, welche Datei geändert wurde. Stattdessen die Entscheidungen begründen:

- Warum ein persistierter Proposal-Status notwendig ist.
- Warum Entscheidung und Apply zwei getrennte Schritte sind.
- Warum Guards deterministischer Code und keine Prompt-Regeln sind.
- Warum `reviews` die Ground Truth für Memory bildet.
- Warum das Dashboard historische Qualitätsprobleme sichtbar macht statt sie still herauszufiltern.
- Warum MCP-Fassade und Providerintegration getrennte Verantwortlichkeiten haben sollten.

### 22.4 Evaluation ehrlich vom Implementierungsnachweis trennen

Der Bericht sollte drei Evidenzarten unterscheiden:

1. **Technischer Funktionsnachweis:** Endpunkt antwortet korrekt, E-Mail kam an, Deep-Link funktioniert, Guards blockieren, Dashboard rendert Live-Daten.
2. **Messung:** Tokenreduktion im A/B, Kosten, Laufzeit, Fehlerzahlen vorher/nachher.
3. **Qualitätsnachweis:** Akzeptanzrate und Kalibrierung auf ausreichend vielen echten menschlichen Entscheidungen.

AP5 und AP6 können technisch abgeschlossen sein, auch wenn AP-E für statistisch belastbare Aussagen noch offen ist. Diese Trennung erhöht die Glaubwürdigkeit.

### 22.5 Grenzen offen benennen

Besonders wertvoll für die Diskussion sind:

- kleine Zahl menschlicher Entscheidungen;
- Formelgenerationen dürfen nicht gemischt werden;
- `value_grounded` ist nicht für jede Feldklasse ein vollständiges Korrektheitsmaß;
- MCP besitzt noch keinen allgemeinen Host/Client-Layer;
- MCP-Auth war bewusst außerhalb des PT4-Scopes;
- der Apply-Pfad ist synchron und kann bei langsamen externen Jobs blockieren;
- der Backend-CI-Workflow pusht ein Image, zeigt aber keinen Rollout-Schritt;
- AP-X und die Konfliktprüfung zwischen Regelkarten bleiben geparkt.

## 23. Formulierungsvorschläge für den Bericht

### 23.1 Architektur-Kernaussage

> Die in PT4 entwickelte Lösung überführt eine autonome, LLM-gestützte Korrekturpipeline in eine kontrollierte Human-in-the-Loop-Architektur. Das Sprachmodell erzeugt weiterhin Analyse und Korrekturvorschlag; die Autorisierung einer Datenmutation wird jedoch durch persistierte menschliche Entscheidungen und deterministische Guards außerhalb des Modells erzwungen.

### 23.2 MCP-Kernaussage

> Die MCP-Integration standardisiert die vorhandenen Review-, Dashboard- und E-Mail-Funktionen als aufrufbare Tools, ohne eine zweite Datenzugriffsschicht einzuführen. Sämtliche Tools delegieren an das bestehende Repository. Damit ist AP5 als serverseitige MCP-Tool-Schicht erfüllt; eine allgemeine Host-/Client-Plattform für dynamisch angebundene externe MCP-Server ist als nächste Ausbaustufe abzugrenzen.

### 23.3 Memory-Kernaussage

> Das Gedächtnissystem trennt Gesprächskontext, selektiv geladenes Regelwissen und episodische Präzedenzfälle. Nur echte menschliche Review-Entscheidungen dürfen den episodischen Speicher befüllen. Dadurch verbessert Memory nicht nur die Vorschlagserzeugung, sondern macht den Einfluss früherer Entscheidungen auf den Confidence-Score auditierbar.

### 23.4 Dashboard-Kernaussage

> Das Dashboard wurde nicht als reine Visualisierungsschicht entworfen, sondern als Mess- und Transparenzkomponente. Neben operativen Kennzahlen liefert es maschinenlesbare Data-Quality-Flags, die historische Formelwechsel, Legacy-Daten, unvollständige Telemetrie und kleine Stichproben offenlegen und damit Fehlinterpretationen der Kennzahlen begrenzen.

## 24. Literatur- und Quellenhinweise

Für das Literaturverzeichnis können folgende Quellen verwendet werden:

1. Brown, S.: *The C4 model for visualising software architecture*. Offizielle Dokumentation: <https://c4model.com/diagrams>.
2. ISO/IEC/IEEE 42010:2022: *Software, systems and enterprise — Architecture description*. <https://www.iso.org/standard/74393.html>.
3. arc42: *Template for architecture documentation and communication*. <https://arc42.org/>.
4. Model Context Protocol: *Architecture overview*. <https://modelcontextprotocol.io/docs/learn/architecture>.
5. Sumers, T. R. et al. (2023): *Cognitive Architectures for Language Agents*. arXiv:2309.02427. <https://arxiv.org/abs/2309.02427>.
6. Amershi, S. et al. (2019): *Guidelines for Human-AI Interaction*. CHI 2019. <https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/>.
7. NIST (2023): *Artificial Intelligence Risk Management Framework 1.0*, Appendix C: Human-AI Interaction. <https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction/>.
8. Microsoft Learn: *AI Agent Orchestration Patterns*. <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns>.

## 25. Pflegehinweis

Diese Datei ist eine **Architektur-Baseline zum Cut vor Abschluss von AP-E und AP-X**. Nach der späteren Fortsetzung sollten nur folgende Stellen gezielt aktualisiert werden:

- Status und Messergebnisse in Diagramm 16;
- Formelversion und Evaluationsergebnisse in Abschnitt 12/15;
- MCP-Zielbild, falls der Host/Client-Umbau umgesetzt wird;
- Deployment-Sicht, sobald der produktive Container-App-Rollout eindeutig im Repository abgebildet ist.

Die historischen Diagramme zur implementierten PT4-Architektur sollten nicht rückwirkend überschrieben, sondern bei größeren Änderungen versioniert werden. So bleibt nachvollziehbar, welche Architektur zum Zeitpunkt des Projektberichts tatsächlich vorlag.
