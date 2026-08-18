# Literaturbasis — Bachelorarbeit

**16 Quellen.** Stand 2026-08-16, jede einzeln gegen die Primärquelle geprüft.
Sortiert **nach Verwendungsstelle in der Arbeit**, nicht alphabetisch — damit beim Schreiben
klar ist, welche Quelle welchen Satz trägt.

> **Instrumentenbelege kommen verpflichtend hinzu, sobald die zugehörige Messung stattfindet.**
> Sie konkurrieren nicht um einen Platz in diesen 16, weil sie keine Argumente sind, sondern
> Nachweise eines verwendeten Werkzeugs — siehe Abschnitt 7.

**Zitat-Status:** ✔ = Titel, Autoren und Venue an der Quelle verifiziert.
Alle 16 sind ✔. Autorenlisten trotzdem als BibTeX von der Primärquelle ziehen, nicht hier
abschreiben.

---

## Die vier, die den Rest tragen

| # | Quelle | Warum sie zählt |
|---|---|---|
| **L05** | Wu, Terry & Cai (2022) — *AI Chains*, CHI | **Die nächstverwandte Vorarbeit überhaupt.** Ohne Abgrenzung ist die Neuheit der Arbeit angreifbar |
| **L11** | Turpin et al. (2023) — *Unfaithful CoT*, NeurIPS | Der stärkste Einwand gegen UF3 — **und, richtig gedreht, das beste Argument dafür** |
| **L13** | Baltes et al. (2026) — *Guidelines*, EmSE | Acht Berichtspflichten **plus Checkliste** für genau diesen Studientyp |
| **L15** | Tam et al. (2024) — *Let Me Speak Freely?*, EMNLP | Gegenbefund, der einen **möglichen Nachteil der eigenen Variante** benennt |

---

## 1. Kapitel 2 und 4 — warum Zerlegung helfen sollte

| # | Quelle | Venue | Link | Verwendung |
|---|---|---|---|---|
| **L01** | Besta, M. et al. (2024). *Graph of Thoughts: Solving Elaborate Problems with LLMs.* | **AAAI 38(16)**, 17682–17690 · DOI `10.1609/aaai.v38i16.29720` | [arXiv](https://arxiv.org/abs/2308.09687) | *(Exposé)* Theoretische Grundlage der Graphmodellierung. **Auch die Begründung, warum das GoT-Referenzframework NICHT eingesetzt wird** (Masterplan Kap. 5.2) |
| **L02** | Wen, Y., Wang, Z. & Sun, J. (2024). *MindMap: Knowledge Graph Prompting Sparks Graph of Thoughts in LLMs.* | **ACL** · DOI `10.18653/v1/2024.acl-long.558` | [Code](https://github.com/wyl-willing/MindMap) | *(Exposé)* Vorbild für die **lesbare Trace-Darstellung** statt rohem JSON |
| **L05** | **Wu, T., Terry, M. & Cai, C. J. (2022).** *AI Chains: Transparent and Controllable Human-AI Interaction by Chaining Large Language Model Prompts.* | **CHI 2022** · DOI `10.1145/3491102.3517582` | [ACM DL](https://dl.acm.org/doi/10.1145/3491102.3517582) · [PDF](https://arxiv.org/pdf/2110.01691) | **Empirischer Beleg, dass Verkettung Transparenz und Kontrollierbarkeit erhöht.** Siehe Abgrenzungskasten |
| **L06** | **Khot, T. et al. (2023).** *Decomposed Prompting: A Modular Approach for Solving Complex Tasks.* | **ICLR 2023** | [arXiv](https://arxiv.org/abs/2210.02406) | Zerlegung in Teilaufgaben schlägt End-to-End — **die Wirksamkeitsbehauptung der Graph-Variante** |
| **L07** | Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* | **NeurIPS 2023** | [arXiv](https://arxiv.org/abs/2303.17651) · [Code](https://github.com/madaan/self-refine) | Die **Rück-Kante Knoten 8→2** ist ein benanntes Muster, keine Eigenerfindung |

> **Die Abgrenzung zu L05, die im Text stehen muss.** Ein Gutachter, der AI Chains kennt, fragt
> sofort: *„Was ist bei Ihnen neu?"* Die Antwort ist gut, aber sie muss dastehen:
>
> AI Chains untersucht **wahrgenommene** Transparenz und Kontrollierbarkeit in einer
> Nutzerstudie an **allgemeinen NLP-Aufgaben**. Diese Arbeit misst **Halluzinationsrate gegen
> objektive Ground Truth**, **Nachvollziehbarkeit an einem maschinell aufgezeichneten Trace** und
> **Robustheit über Wiederholungsläufe** — an **strukturierten JSON-Daten in einem
> produktionskritischen System**, bewertet von **Domänenexperten**.
> Anderer Gegenstand, härtere Messung, anderes Erkenntnisinteresse. Verschweigen wäre fatal.

---

## 2. Kapitel 6 und 7 — die drei Messdimensionen

| # | Quelle | Venue | Link | Verwendung |
|---|---|---|---|---|
| **L03** | Ji, Z. et al. (2023). *Survey of Hallucination in Natural Language Generation.* | **ACM CSUR 55(12)** · DOI `10.1145/3571730` | — | *(Exposé)* Grundbegriff Halluzination |
| **L08** | **Huang, L. et al. (2025).** *A Survey on Hallucination in LLMs: Principles, Taxonomy, Challenges, and Open Questions.* | **ACM TOIS 43(2)** · DOI `10.1145/3703155` | [PDF](https://arxiv.org/pdf/2311.05232) | **Der aktuelle Referenzsurvey (UF1).** Ji allein ist 2026 zu alt. **Die vier Kategorien aus Masterplan Kap. 15.1 sichtbar hieraus ableiten**, sonst wirken sie erfunden |
| **L09** | **Sclar, M., Choi, Y., Tsvetkov, Y. & Suhr, A. (2024).** *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design.* | **ICLR 2024** | [OpenReview](https://openreview.net/forum?id=RIu5lyNXjT) · [arXiv](https://arxiv.org/pdf/2310.11324) | **UF2-Motivation:** bedeutungserhaltende Formatänderungen bewegen die Leistung um bis zu 76 Punkte. Der Beleg, dass Instabilität real und messwürdig ist |
| **L10** | Wang, X. et al. (2023). *Self-Consistency Improves Chain of Thought Reasoning in Language Models.* | **ICLR 2023** | [arXiv](https://arxiv.org/abs/2203.11171) | **UF2-Methodik:** etabliert Streuung über Wiederholungen als legitimes Messobjekt — die Rechtfertigung der 3–5 Wiederholungen |
| **L11** | **Turpin, M., Michael, J., Perez, E. & Bowman, S. (2023).** *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting.* | **NeurIPS 2023** | [arXiv](https://arxiv.org/abs/2305.04388) · [NeurIPS-PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/ed3fea9033a80fea1376299fa7863f4a-Paper-Conference.pdf) | **UF3, siehe Kasten** |
| **L12** | Jacovi, A. & Goldberg, Y. (2020). *Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?* | **ACL 2020** | [ACL Anthology](https://aclanthology.org/2020.acl-main.386/) | **Liefert die Begriffe für UF3:** *faithfulness* vs. *plausibility* — exakt die Unterscheidung „echte vs. bloss plausible Begründung". Plädiert für eine **graduelle** statt binäre Auffassung, was zum Experten-Rating 1–5 passt |

> **Das Argument aus L11 — es ist die stärkste Stelle der Arbeit.**
>
> Turpin zeigt: Was ein Modell als Begründung *ausgibt*, kann den echten Entscheidungsweg
> systematisch falsch darstellen. Ein Gutachter wird das gegen die Arbeit wenden:
> *„Dann ist der Trace Ihres Graphen auch nur Prosa."*
>
> **Ist er nicht — und genau darin liegt der Beitrag.** Der `trace` wird **vom Code
> aufgezeichnet**, nicht **vom Modell erzählt**: `matched_rules` hält fest, welche Regelkarte der
> Loader tatsächlich geladen hat; `technical_check`, was der Schema-Validator tatsächlich
> zurückgab; `applied`, was die Re-Validierung tatsächlich meldete. Das sind **Beobachtungen,
> keine Selbstauskünfte.** Der Monolith hat nur die Selbstauskunft.
>
> Damit wird L11 vom Einwand zum **Verstärker**: Die Architektur liefert Nachvollziehbarkeit
> genau dort, wo die Literatur zeigt, dass man Modellbegründungen nicht trauen darf.
> **Gehört in Kapitel 4 und in Kapitel 8.**

---

## 3. Kapitel 5 — Forschungsdesign und Berichtspflichten

| # | Quelle | Venue | Link | Verwendung |
|---|---|---|---|---|
| **L13** | **Baltes, S. et al. (2026).** *Guidelines for Empirical Studies in Software Engineering involving Large Language Models.* | **Empirical Software Engineering** (angenommen 06/2026) | [arXiv](https://arxiv.org/abs/2508.15503) · [llm-guidelines.org](https://llm-guidelines.org) | **Acht Leitlinien plus Berichts-Checkliste.** Siehe Kasten |
| **L14** | Runeson, P. & Höst, M. (2009). *Guidelines for Conducting and Reporting Case Study Research in Software Engineering.* | **EmSE 14(2)**, 131–164 · DOI `10.1007/s10664-008-9102-8` | [dblp](https://dblp.org/rec/journals/ese/RunesonH09.html) | Der Standard für „praxisnahe Fallstudie mit experimentellen Elementen" — **genau das Design dieser Arbeit**. Legitimiert die kleine Fallzahl als Methodenwahl statt als Mangel |

> **Was L13 konkret bedeutet.** Die acht Leitlinien decken sich weitgehend mit Masterplan
> Kap. 17: Modellversion und Konfiguration berichten (✔), Prompt-Design dokumentieren (✔),
> **Session-Traces berichten** (✔ — der `trace` *ist* das), geeignete Baselines (✔), Grenzen
> benennen (✔).
>
> **Zwei Leitlinien erfüllt die Arbeit nicht. Beide gehören in die Limitationen:**
> * **„Include an open LLM baseline"** — es läuft ausschliesslich GPT-4.1, weil das Exposé das
>   Modell als Kontrollbedingung fixiert. Begründbar, aber eine Abweichung, die zu benennen ist.
> * **„Validate LLM outputs against human judgment"** — erfüllt über die Expertenbewertung,
>   **aber nur, wenn sie stattfindet.** Fällt sie aus, fällt eine Leitlinie mit.
>
> Die Checkliste im Anhang abzuarbeiten ist billige, hochwirksame Punktesicherung.

---

## 4. Kapitel 8 — Gegenbefund

| # | Quelle | Venue | Link | Verwendung |
|---|---|---|---|---|
| **L15** | **Tam, Z. R. et al. (2024).** *Let Me Speak Freely? A Study on the Impact of Format Restrictions on LLM Performance.* | **EMNLP 2024 Industry** | [ACL Anthology](https://aclanthology.org/2024.emnlp-industry.91/) · [arXiv](https://arxiv.org/abs/2408.02442) | **Formatzwang senkt Reasoning-Leistung messbar.** Betrifft **beide** Varianten — aber die Graph-Variante erzwingt Struktur **häufiger** (je Knoten). **Ein möglicher systematischer Nachteil der eigenen Variante**, der diskutiert gehört, statt entdeckt zu werden |

---

## 5. Kapitel 1 und 3 — Kontext und Forschungslücke

| # | Quelle | Venue | Link | Verwendung |
|---|---|---|---|---|
| **L04** | Es, S. et al. (2024). *RAGAs: Automated Evaluation of Retrieval Augmented Generation.* | **EACL** · DOI `10.18653/v1/2024.eacl-demo.16` | — | *(Exposé)* **Nur** für den RAG-Teilaspekt. Zugleich der Beleg, **warum ein Standardframework als Hauptmethode nicht genügt** — das begründet den methodischen Beitrag (UF1) |
| **L16** | **Henkel, V. et al. (2026).** *Foundation-Model-Based Agents in Industrial Automation: Purposes, Capabilities, and Open Challenges.* | **Preprint** (eingereicht: J. Intelligent Manufacturing) | [arXiv-PDF](https://arxiv.org/pdf/2605.02592) | **Der Zahlenbeleg der Forschungslücke.** PRISMA-2020-Übersicht: 2.341 gesichtet, 88 ausgewertet, **75 % auf TRL 4–6, nur 9,1 % mit einsatzorientierter Evidenz** |

> **Ehrlich bleiben bei L16:** Es ist ein **Preprint**. Als Kennzeichnung mitschreiben und die
> tragende Aussage zusätzlich auf L03/L08 stützen. Vor Abgabe prüfen, ob er begutachtet
> erschienen ist.
>
> **Und die Lücke eng formulieren.** Nicht „LLMs in der Industrie sind unerforscht" — das
> widerlegt L16 mit 2.341 gesichteten Publikationen sofort. Sondern: *für die **Korrektur**
> strukturierter Planungsdaten unter Revisionssicherheit fehlt empirische Evidenz zum
> Architektureinfluss.* Zu dieser engen Frage lieferte die Recherche **keine begutachtete
> Quelle** — das ist der Beitrag der Arbeit.

---

## 6. Vor dem Übernehmen ins Literaturverzeichnis

1. **BibTeX von der Primärquelle holen** (ACL Anthology, ACM DL, NeurIPS/ICLR Proceedings), nicht
   von Aggregatoren — Semantic Scholar und ResearchGate tragen regelmässig falsche Jahre.
2. **Preprint-Status von L16 vor Abgabe erneut prüfen.**
3. **PDFs beschaffen** — `docs/03_Expose-extern/source-1/` enthält bislang nur L01–L04.
4. **Instrumentenbelege ergänzen**, sobald die Messung stattfindet — siehe Abschnitt 7.
   Ein SUS-Score ohne Brooke-Zitat ist ein Formfehler.

---

## 7. Instrumentenbelege — verpflichtend, sobald gemessen wird

Diese zählen **nicht** zu den 16. Sie sind keine Argumente, sondern Nachweise eines verwendeten
Werkzeugs: **wer ein Instrument einsetzt, muss es zitieren.** Autorenangaben vor der Verwendung
an der Primärquelle prüfen — hier bewusst nicht geraten.

| Quelle | Wird verpflichtend, wenn … |
|---|---|
| Brooke, J. (1996). *SUS: A Quick and Dirty Usability Scale.* Taylor & Francis | … die Nutzertests (F7) stattfinden |
| Laugwitz, B., Held, T. & Schrepp, M. (2008). *Construction and Evaluation of a User Experience Questionnaire.* USAB, LNCS 5298 | … UEQ eingesetzt wird |
| Cohen, J. (1960). *A Coefficient of Agreement for Nominal Scales.* Educ. and Psych. Measurement | … die Übereinstimmung der 2–4 Experten als κ berichtet wird |

**Präzedenzfall für κ in genau diesem Kontext:** *Why Do Multi-Agent LLM Systems Fail?* (MAST),
NeurIPS 2025, [arXiv:2503.13657](https://arxiv.org/abs/2503.13657) — berichtet κ = 0,88 über 150
annotierte Traces. Nützlich als Beleg, dass Expertenannotation von Traces ein etabliertes
Vorgehen ist.

---

## 8. Recherchelücke — bewusst festgehalten

**Zu LLM-gestützter Korrektur strukturierter ERP- und Produktionsplanungsdaten existiert keine
begutachtete Literatur.** Die Suche am 16.08.2026 lieferte dazu ausschliesslich Anbieter- und
Beratungsinhalte, nichts Zitierfähiges. **Das ist kein Mangel der Recherche, sondern der Beitrag
der Arbeit** — die Lücke ist in Kapitel 1 eng zu formulieren, siehe die Anmerkung zu L16.


---
## zusätzlich: 
Deine vier aus dem Exposé (gesetzt)
Besta et al. 2024 — Graph of Thoughts, AAAI → arxiv.org/abs/2308.09687 · DOI 10.1609/aaai.v38i16.29720
Wen et al. 2024 — MindMap, ACL → DOI 10.18653/v1/2024.acl-long.558 · Code
Ji et al. 2023 — Hallucination Survey, ACM CSUR → DOI 10.1145/3571730
Es et al. 2024 — RAGAS, EACL → DOI 10.18653/v1/2024.eacl-demo.16
Warum Zerlegung hilft (Kap. 2/4)
Wu, Terry & Cai 2022 — AI Chains, CHI → ACM DL · arXiv-PDF
Khot et al. 2023 — Decomposed Prompting, ICLR → arxiv.org/abs/2210.02406
Madaan et al. 2023 — Self-Refine, NeurIPS → arxiv.org/abs/2303.17651 · Code
Die drei Dimensionen (Kap. 6/7)
Huang et al. 2025 — Hallucination Survey, ACM TOIS → PDF · DOI 10.1145/3703155
Sclar et al. 2024 — Prompt-Format-Sensitivität, ICLR → OpenReview · arXiv
Wang et al. 2023 — Self-Consistency, ICLR → arxiv.org/abs/2203.11171
Turpin et al. 2023 — Unfaithful CoT, NeurIPS → arxiv.org/abs/2305.04388 · NeurIPS-PDF
Jacovi & Goldberg 2020 — Faithfulness, ACL → ACL Anthology
Methodik (Kap. 5)
Baltes et al. 2026 — Guidelines für empirische LLM-Studien, EmSE → arxiv.org/abs/2508.15503 · llm-guidelines.org
Runeson & Höst 2009 — Fallstudien-Leitlinien, EmSE → dblp · DOI 10.1007/s10664-008-9102-8
Gegenbefund + Lücke (Kap. 8 / Kap. 1)
Tam et al. 2024 — Let Me Speak Freely?, EMNLP → ACL Anthology · arXiv
Henkel et al. 2026 — Industrial Automation SLR (Preprint) → arxiv.org/pdf/2605.02592
Ein Hinweis, der nicht um einen Slot konkurriert: Führst du die Nutzertests (F7) durch, musst du Brooke (SUS) und Laugwitz (UEQ) zitieren — das sind Instrumentenbelege, keine Argumente. Gleiches gilt für Cohen (κ), falls du die Experten-Übereinstimmung berechnest. Die kommen automatisch dazu und stehen im Archiv.

