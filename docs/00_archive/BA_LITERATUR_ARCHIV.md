# Literatur-Archiv — recherchiert, nicht im Kern

**Stand 2026-08-16.** Diese Quellen wurden bei der Recherche am 16.08. gefunden und geprüft,
aber **nicht** in die 16 des Kerns aufgenommen (`BA_LITERATUR.md`).

**Nicht löschen.** Zwei Gründe: Der Abschnitt 1 wird **verpflichtend**, sobald die zugehörige
Messung stattfindet, und der Rest ist die naheliegende Reserve, falls ein Kapitel beim Schreiben
mehr Belege braucht als gedacht.

**Zitat-Status:** ✔ = an der Quelle verifiziert · ◐ = Titel, Venue und Kennung verifiziert,
**Autorenliste noch aus DOI/arXiv zu ziehen** — hier bewusst nicht geraten.

---

## 1. Instrumentenbelege — verpflichtend, sobald gemessen wird

Diese konkurrieren **nicht** mit den 16, weil sie keine Argumente sind, sondern Nachweise eines
verwendeten Werkzeugs. **Wer ein Instrument einsetzt, muss es zitieren.**

| # | Quelle | Zitat | Wird verpflichtend, wenn … |
|---|---|---|---|
| A01 | Brooke, J. (1996). *SUS: A Quick and Dirty Usability Scale.* Taylor & Francis | ◐ | … die Nutzertests (F7) stattfinden. **Ein SUS-Score ohne dieses Zitat ist ein Formfehler** |
| A02 | Laugwitz, B., Held, T. & Schrepp, M. (2008). *Construction and Evaluation of a User Experience Questionnaire.* USAB, LNCS 5298 | ◐ | … UEQ eingesetzt wird. Dasselbe gilt |
| A03 | Cohen, J. (1960). *A Coefficient of Agreement for Nominal Scales.* Educational and Psychological Measurement | ◐ | … die Übereinstimmung der 2–4 Experten als κ berichtet wird |

---

## 2. Reserve — belastbar, aber im Kern entbehrlich

| # | Quelle | Venue | Link | Wofür sie einspringen würde |
|---|---|---|---|---|
| A04 | Shinn, N., Labash, B. & Gopinath, A. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* | NeurIPS 2023 | [arXiv](https://arxiv.org/abs/2303.11366) | Zweiter Beleg für die Rück-Kante neben Madaan (L07). Nehmen, falls Kapitel 4 mehr Fundierung braucht |
| A05 | Paul, D. et al. (2023). *REFINER: Reasoning Feedback on Intermediate Representations.* | EACL 2024 | [arXiv](https://arxiv.org/abs/2304.01904) | dito. **Namensgebend für „Feedback auf Zwischenrepräsentationen"** — begrifflich nah an der Kernthese |
| A06 | Yao, S. et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* | ICLR 2023 | [Code](https://github.com/ysymyth/ReAct) | ✔ Begründet, warum die Knoten **heterogen und werkzeuggebunden** sind statt homogene „Thoughts" |
| A07 | *Why Do Multi-Agent LLM Systems Fail?* (MAST) | NeurIPS 2025 · arXiv:2503.13657 | [arXiv](https://arxiv.org/abs/2503.13657) | ◐ Zwei Nutzen: **Verification Gaps = 21,3 % aller Fehler** stützt die Betonung von Knoten 6/7; und sie berichten **κ = 0,88** — ein Präzedenzfall für Experten-Übereinstimmung in genau diesem Kontext |
| A08 | Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* | NeurIPS 2023 D&B | [arXiv](https://arxiv.org/abs/2306.05685) | ✔ **Nur** falls automatisierte Vorsortierung eingesetzt wird. Dann zwingend mitzitieren: Position-, Verbosity- und Self-Enhancement-Bias |
| A09 | Geng, S., Josifoski, M., Peyrard, M. & West, R. (2023). *Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning.* | EMNLP 2023 | [ACL Anthology](https://aclanthology.org/2023.emnlp-main.674/) | ✔ Die **Gegenposition zu L15**: Strukturzwang verbessert die Formtreue. Zusammen ergeben beide den ehrlichen Befund „Struktur hilft der Form, schadet ggf. dem Denken" |
| A10 | Ouyang, S. et al. *An Empirical Study of the Non-determinism of ChatGPT in Code Generation.* | arXiv:2308.02828 | [PDF](https://arxiv.org/pdf/2308.02828) | ◐ Belegt: **auch `temperature=0` ist nicht deterministisch.** Entkräftet den naheliegendsten Einwand gegen die gewählten 0,3 — nehmen, falls der Betreuer danach fragt |
| A11 | *JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models.* | arXiv:2501.10868 | [HTML](https://arxiv.org/html/2501.10868v3) | ◐ Stützt „strukturelle Halluzination" als **eigenständige, messbare Klasse**. Venue vor Verwendung prüfen |
| A12 | Wu, T. et al. (2022). *PromptChainer: Chaining Large Language Model Prompts through Visual Programming.* | CHI 2022 EA | [ACM DL](https://dl.acm.org/doi/10.1145/3491101.3519729) | ✔ Werkzeugseite von L05. Beleg „Verkettung ist etabliert, nicht neu" — nur nötig, wenn L05 allein zu dünn wirkt |

---

## 3. Ausdrücklich nicht Gegenstand

| # | Quelle | Warum hier |
|---|---|---|
| A13 | Zhou, A. et al. (2024). *Language Agent Tree Search (LATS).* ICML 2024 | **Nur für Kapitel 9 (Ausblick).** Die Baumsuche ist am 16.08.2026 ausdrücklich aus dem Vergleich ausgeschlossen worden (Masterplan Kap. 5.2). Als Ausblick zitierfähig, als Umsetzung nicht |

---

## 4. Recherchelücke — bewusst festgehalten

**Zu LLM-gestützter Korrektur strukturierter ERP-/Produktionsplanungsdaten existiert keine
begutachtete Literatur.** Die Suche am 16.08.2026 lieferte dazu ausschliesslich Anbieter- und
Beratungsinhalte (LLMOps-Plattformen, Data-Quality-Blogs), nichts Zitierfähiges.

**Das ist kein Mangel der Recherche, sondern der Beitrag der Arbeit** — aber die Lücke muss in
Kapitel 1 eng formuliert werden, siehe die Anmerkung zu L16 im Kern.
