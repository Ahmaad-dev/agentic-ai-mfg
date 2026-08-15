# Graph-based System Architecture vs. Monolithic System-Prompt Structure
### An Empirical Evaluation of Hallucination Rate, Traceability, and Robustness in LLM-assisted Validation and Correction Systems in a Production Environment

**Author:** Ahmad Alsayad · **Supervisor:** DI Michael Macher · **Program:** Smart Engineering, FH St. Pölten
**Industry context:** CANCOM Austria AG — Digital Makers · **Model (fixed):** Azure OpenAI GPT-4.1

> **This is a BACHELOR THESIS scaffold, NeurIPS section *style* + thesis *depth*.** It carries three kinds of author aids that are **removed before submission**: (a) the **Writing Guide** (§0), (b) per-section `<INSERT>` blocks stating *what to write* + *which papers to cite*, and (c) `TODO` markers for data. Citation keys `[Key]` resolve in §References and map 1:1 to `pdf/` (48 PDFs).
>
> **Thesis vs. paper:** a thesis adds what a paper compresses away — a **Mathematical Background** (§4), an **Implementation** chapter (§7), and deeper Background/Discussion. Section *naming* stays NeurIPS-clean.

> **Alignment:** two-way comparison — **monolithic RAG** vs. **graph-based LATS+RAG** (LATS = search layer over the exposé's step decomposition; needs Macher sign-off, see Deviation ledger at end).

---

## 0 Writing Guide *(remove before submission)*

> **Purpose.** A reusable blueprint so every section is written to the same concept and structure. Exemplars to imitate are in `pdf/`: **[LATS]** (NeurIPS-style method+search), **[GoT]** (AAAI method), **[RAG-Origin]** (NeurIPS method+eval), **[RAGSurvey]** (survey structure). Open them and mirror their paragraph flow.

### 0.1 How to write the **Abstract** (6 moves, ~200 words, one paragraph)
Write it **last**. Follow this fixed order — each move = 1–2 sentences:
1. **Context** — the domain and why it matters (Smart Planning, JSON snapshots, production-critical).
2. **Problem / gap** — the monolith's three failure modes; the missing empirical + methodical evidence.
3. **Approach** — what you built (monolithic RAG vs. LATS+RAG; verifier as value function).
4. **Method** — how you evaluated (2-way controlled comparison; hybrid eval framework).
5. **Results** — the headline numbers (fill after runs).
6. **Contribution / impact** — empirical + methodical + practical.
*Rule: no citations in the abstract; no undefined acronyms; past tense for what you did.*

### 0.2 How to write the **Introduction** (CARS "funnel" model — Swales)
Move from broad to specific, then to your work:
1. **Establish the territory** — why the area matters (Industry 4.0, LLMs in production). *(§1.1)*
2. **Establish a niche** — what's wrong / missing (the reliability gap; RAG's limits; the research gap). *(§1.2–1.3)*
3. **Occupy the niche** — your approach, research question, contributions, scope. *(§1.4–1.7)*
End §1 with an explicit **contributions list** (NeurIPS convention) and a **thesis-structure roadmap** (§1.8).
*Rule: the introduction promises exactly what later sections deliver — no orphan promises.*

### 0.3 Per-section blueprint (applies throughout)
- **Open** each section with 1 sentence stating its job. **Close** with 1 sentence bridging to the next.
- **One claim → one citation.** Load-bearing claims cite a **renowned-venue** paper (NeurIPS/ICLR/ICML/ACL/EMNLP/AAAI), not a 2026 preprint.
- **Figures/tables** are referenced in text before they appear; every table has a takeaway sentence.
- **Background vs. Method:** Background = *others' work*; Method = *your work*. Never mix.
- **Past tense** for what you did; **present tense** for general truths.

### 0.4 Thesis page budget (~30–40 pages body; front matter + appendix excluded)
| Section | Pages | Draftable now |
|---|--:|---|
| Abstract | 0.5 | after results |
| 1 Introduction | 3 | ✅ |
| 2 Background & Related Work | 6 | ✅ |
| 3 (folded into 2) | — | — |
| 4 Mathematical Background | 3 | ✅ |
| 5 Problem Formulation | 3 | ✅ |
| 6 Method (LATS) | 5 | ✅ (needs diagram) |
| 7 Implementation | 3 | 🟡 during build |
| 8 Experimental Setup | 3 | 🟡 needs catalog counts |
| 9 Results + Ablation | 6 | ❌ needs runs |
| 10 Discussion | 2 | 🟡 partial |
| 11 Conclusion & Future Outlook | 1.5 | ❌ after results |
| References | 2 | ✅ |
> **~20 pages (§1,2,4,5,6 + refs) writable before any experiment.**

---

## Abstract

> `<INSERT>` **What to write:** the 6 moves from §0.1, ≤ 250 words, one paragraph, no citations. **Cite:** none.

*(Draft placeholder — rewrite last.)* (1) LLM-assisted correction of large JSON production snapshots in Smart Planning; (2) a monolithic 425-line prompt shows hallucinations, poor traceability, instability; (3) we compare it against a **graph-based LATS+RAG** variant whose search tree over corrections is scored by the deterministic validation engine (structural) + a rubric judge (semantic); (4) a controlled **two-way** comparison, identical model/RAG/verifier/test-cases, hybrid evaluation (deterministic + expert-rubric + SUS/UEQ); (5) `TODO: results`; (6) empirical + methodical + practical contributions.

**Keywords:** LLM agents, graph-based architecture, Graph of Thoughts, Language Agent Tree Search, retrieval-augmented generation, hallucination, structured-output validation, production planning, Industry 4.0.

---

## 1 Introduction

### 1.1 Motivation: LLM-assisted correction in production planning

> `<INSERT>` **What to write:** CARS move 1 — establish territory. Add 1–2 sentences grounding *Industry 4.0 / LLMs in manufacturing* with real citations (currently uncited). **Cite:** `[Industry40]` (foundational Industry 4.0), `[ManufLLM]` (LLMs in manufacturing survey), `[IndLLM]` (agentic industrial automation).

The digital transformation of manufacturing — commonly framed as *Industry 4.0* — has moved
artificial intelligence from a purely analytical role into operational decision loops on the
shopfloor. A representative instance of this shift is *Smart Planning*, a production-planning
system that acts as an integration layer between a customer's ERP system and the operational
production process. Smart Planning represents the current planning state as large **JSON
snapshot files** — a single snapshot ranges from roughly 70,000 to over 200,000 entries and
encodes products, machine identifiers, product types, employee availabilities and
qualifications, and the full set of process-relevant parameters. The quality of a snapshot
directly determines the quality of the resulting production plan: inconsistent input yields
faulty scheduling and resource allocation.

Smart Planning ships with a validation engine that *detects and localizes* errors in a
snapshot, but cannot *correct* them. Correction was, until recently, a fully manual task
performed by specialized domain personnel, requiring between two and more than six hours per
snapshot. The LLM-assisted, four-agent correction system developed in the underlying practical
project automates this step: it retrieves a faulty snapshot, analyzes and corrects it via an
LLM-driven agent pipeline, and writes the corrected snapshot back — reducing the effort for a
typical snapshot from hours to one to three minutes, a 95–99 % saving. In production, however,
the system exhibited three recurring failure modes that motivate this thesis.

### 1.2 The reliability gap in production-critical LLM systems

Large Language Models are known to produce *hallucinations* — factually incorrect yet
syntactically plausible outputs. The phenomenon is not an edge case but a structural property
of current architectures that grows with task complexity and context length [Ji, Tonmoy]. In a
production-critical setting this risk is acute: a **syntactically valid but factually wrong**
JSON correction can pass downstream checks unnoticed and enter the ERP system, triggering
faulty manufacturing orders or scheduling. The project surfaced two further problems alongside
hallucination: a lack of **traceability** (*Nachvollziehbarkeit*) of correction decisions, which
makes quality assurance and targeted debugging nearly impossible; and a lack of **robustness**
to structurally varying inputs, where identical inputs occasionally yield different factual
corrections and cascade effects lengthen the iterative correction loop. These three
dimensions — *hallucination rate, traceability, robustness* — form the scientific core of this
work.

### 1.3 Retrieval-augmented generation and its limits in this setting

The canonical remedy for hallucination, outdated knowledge, and opaque reasoning is
**Retrieval-Augmented Generation (RAG)**, which grounds generation in an external knowledge
base and thereby improves factual accuracy and traceability for knowledge-intensive tasks
[RAG-Origin, RAGSurvey]. The deployed system already relies on RAG: its RAG-agent retrieves
domain documents and validation rulesets — deliberately authored in natural language so that
domain experts without programming skills can maintain them — from Azure AI Search, and the
quality of these retrieval results proved to be a decisive factor for the factual correctness of
the system's output. RAG is therefore not incidental to this thesis but part of its substrate,
and its design space bounds what retrieval alone can contribute.

The RAG literature has matured well beyond the *naive* retrieve-then-read pattern. Gao et al.
[RAGSurvey] organize the field into *naive*, *advanced* (pre-/post-retrieval optimization,
re-ranking, refined chunking), and *modular* RAG (retrieval decomposed into configurable
modules). Three sub-lines are directly relevant here. First, **hierarchical and graph-based
retrieval** — RAPTOR's recursive summarization tree [RAPTOR], Microsoft's GraphRAG with
community-level summaries [GraphRAG], HippoRAG's Personalized-PageRank associative retrieval
[HippoRAG], LightRAG [LightRAG], and hierarchical-knowledge RAG [HiRAG] — targets multi-hop
reasoning and the structural dependencies that flat vector retrieval dilutes. Second,
**self-reflective and corrective RAG** — Self-RAG's on-demand retrieval and reflection tokens
[SelfRAG], Corrective RAG's retrieval-quality evaluator [CRAG], and Adaptive-RAG's
complexity-based routing [AdaptiveRAG] — embeds verification into the retrieval loop. Third,
**agentic RAG** replaces static pipelines with autonomous agents that decide *when, what, and
how* to retrieve [AgenticRAG, ReasoningRAG]. Crucially for the present use case, a nascent line
applies RAG to **structured outputs**: retrieving candidate JSON objects before generation
measurably reduces hallucination and improves executability of the emitted JSON [StructRAG],
while structured/enterprise and text-and-table RAG address row–column integrity and the
"vector dilution" that afflicts serialized tables [EntRAG, T2RAG].

Two limits of retrieval frame the thesis. (i) These advances are evaluated almost exclusively
on open-domain question answering, not on **structured JSON correction in a verifier-rich
production loop**; their transferability is unestablished. (ii) More fundamentally, retrieval
does not repair the *architectural* weakness of a monolithic prompt: even when the correct rule
is present in the RAG context, an overloaded single-prompt model still neglects constraints and
hallucinates references [Ji]. Retrieval improves *what the model knows*; it does not, by itself,
make the *decision process* decomposable, inspectable, or stable. That is the gap a system
architecture must close.

### 1.4 From monolithic prompts to a graph-based LATS architecture

The deployed system bundles all processing logic — role definition, validation rules,
correction instructions, output formatting, and examples — into a single monolithic system
prompt (425 lines / 20,284 characters for the Smart-Planning agent). This was pragmatic
initially but scales poorly: constraints are silently dropped, there are no explicit
intermediate states to inspect, and every prompt edit risks destabilizing previously stable
behavior. Following the exposé, the comparison variant models the correction process as an
explicit **directed processing graph** — decomposing the bundled logic into discrete steps
(input analysis, error classification, **context search (RAG)**, rule mapping, correction
generation, result evaluation) whose intermediate results are visible, validatable, and locally
correctable, in the *Graph of Thoughts* tradition [GoT, MindMap].

This thesis realizes that graph as a **Language Agent Tree Search (LATS)** [LATS]: the decomposed
steps form the node/action structure of a search over correction trajectories, and the
**deterministic Smart Planning validation engine serves as the value function** (structural
reward), complemented by a rubric judge for semantic reward. Retrieval-augmented generation is
held constant across both systems as the shared grounding substrate [RAGSurvey]. The verifier is
the decisive asset: the self-correction literature shows that *intrinsic* self-correction is
unreliable because error *detection* is the bottleneck [Kamoi, Shinn, Madaan, Pan], and an
external deterministic verifier is precisely what makes search-based correction effective —
while removing LATS's main weakness, the noisy LLM value estimate [PAC-MCTS]. Knowledge-graph
grounding of the ruleset is a compatible extension left to future work (§11).

### 1.5 Problem statement and research question

**Main research question.** *To what extent does a graph-based system architecture differ from a
monolithic system-prompt structure with respect to hallucination rate, traceability, and
robustness for the automated validation and correction of structured JSON data in a
production-critical environment?*

- **UF1 (hallucination + measurability).** Effect of modularizing the prompt into a graph-based
  workflow on hallucination reduction — and how to measure it, given that text-oriented
  frameworks such as RAGAS [RAGAS] do not transfer to structured JSON corrections.
- **UF2 (consistency / robustness).** Does decomposition into discrete graph-modeled steps yield
  more consistent decisions under varying inputs; can architectural instability be separated from
  the model's inherent stochasticity?
- **UF3 (debugging / maintainability).** Do explicit intermediate states and decision points
  enable more targeted error analysis and more maintainable evolution under iterative loops?

### 1.6 Contributions

- **C1 — Empirical.** A methodically controlled, **two-way** comparison (*monolithic RAG vs.
  graph-based LATS+RAG*) on a real industrial JSON-correction case — model, RAG substrate,
  verifier, and test cases held constant — quantified along hallucination rate, traceability, and
  robustness.
- **C2 — Methodical.** An evaluation framework for **structured** LLM outputs combining
  deterministic technical validation, expert-rubric LLM-as-judge assessment [LLMJudge, GEval,
  CaseAwareJudge, RubricRAG], and repetition-based variance — where text metrics [RAGAS] alone
  are insufficient.
- **C3 — Practical.** A prototype graph-based variant integrated with the existing system, plus
  design guidelines for prompt/graph architectures in production-critical industrial LLM systems.

### 1.7 Scope and delimitation

The study compares exactly two architectures on one use case (Smart Planning JSON snapshots): a
**monolithic RAG baseline** and a **graph-based LATS+RAG variant**. Model (Azure OpenAI GPT-4.1
[GPT4]), RAG substrate, verifier, and test cases are held fixed, so observed differences are
attributable to the *reasoning structure*, not model, retrieval, or data. It is neither LLM
foundational research nor mere prompt-wording optimization, and the LATS variant is a prototype,
not a productization. Knowledge-graph grounding is optional / future work. *(Supervisor note:
LATS is the search layer over the exposé's graph-of-thoughts decomposition — the named steps are
preserved as the graph's node/action structure; pending sign-off.)*

### 1.8 Thesis structure

> `<INSERT>` **What to write:** one sentence per chapter (§2–§12) as a roadmap. Update numbers if the structure changes. **Cite:** none.

Section 2 reviews the literature; Section 4 provides the mathematical background; Section 5
formalizes the problem and verifier; Section 6 presents the LATS method; Section 7 details the
implementation; Section 8 the experimental setup; Section 9 the results and ablation; Section 10
discusses findings and threats; Section 11 concludes with a future outlook.

---

## 2 Background and Related Work

> `<INSERT>` **What to write (thesis depth):** for each subsection, 1–2 paragraphs of *others' work*, ending with the gap sentence *"…but none address structured JSON correction in a verifier-rich production loop."* This is the longest theory section in a thesis — go deeper than a paper would. **Section-level cite spine below.**

- **2.1 Hallucination in LLMs.** Structural, not edge-case; grows with task complexity & context length `[Ji]`; mitigation taxonomy `[Tonmoy]`; verification-based mitigation e.g. Chain-of-Verification `[CoVe]`.
- **2.2 Prompting & reasoning.** Chain-of-Thought `[CoT]`; Self-Consistency `[SelfCons]`; in-context ability of the base model `[GPT4]`.
- **2.3 Self-correction and its limits.** Self-Refine `[Madaan]`, Reflexion `[Shinn]`, survey `[Pan]`; the critical finding that **intrinsic** self-correction is unreliable — error *detection* is the bottleneck `[Kamoi]` → motivates an **external verifier**.
- **2.4 Reasoning as a graph.** Graph of Thoughts `[GoT]`; knowledge-graph prompting `[MindMap]`; intermediate results become visible, validatable, correctable.
- **2.5 Search over actions.** ReAct (reason+act) `[ReAct]`; tool use `[Toolformer]`; Tree-of-Thoughts `[ToT]`; **LATS** `[LATS]`; bias-aware pruning for unreliable value estimates `[PAC-MCTS]`. *State: our deterministic verifier removes LATS's main weakness.*
- **2.6 Graph-structured agent execution (systems).** Workflow-as-graph `[GraphFlow]`; fixed-topology controllability `[AgentLoops]`; workflow-optimization survey `[WorkflowSurvey]`.
- **2.7 Knowledge grounding.** KG reduces hallucination `[KG-Survey]`; industrial KG data layer `[KG-Industrial]`.
- **2.8 Structured-output generation & its failure modes.** Grammar-constrained/JSON-schema decoding guarantees syntax `[GCD]`; but constraints can *hurt* reasoning/semantics `[SpeakFreely]`, and "structure snowballing" — perfect syntax, missed semantics `[Snowball]`.
- **2.9 Retrieval-Augmented Generation (RAG).** *The retrieval substrate — cover in depth (thesis).*
  - **2.9.1 Foundations & paradigms** `[RAG-Origin, RAGSurvey, RAGStack]`.
  - **2.9.2 Hierarchical & graph RAG** `[RAPTOR, GraphRAG, HippoRAG, LightRAG, HiRAG]`.
  - **2.9.3 Self-reflective / corrective / adaptive RAG** `[SelfRAG, CRAG, AdaptiveRAG]`.
  - **2.9.4 Agentic RAG** `[AgenticRAG, ReasoningRAG]`.
  - **2.9.5 RAG for structured data & outputs** `[StructRAG, EntRAG, T2RAG]` — closest prior work.
- **2.10 Evaluation of LLM outputs.** LLM-as-a-judge `[LLMJudge]`, G-Eval `[GEval]`; RAGAS and its limits for structured tasks `[RAGAS]`; rubric-based judging `[CaseAwareJudge, RubricRAG]`; faithfulness ≠ plausibility of explanations `[Faithful]`; usability instruments `[SUS, UEQ]`.

---

## 3 *(merged into §2 — thesis keeps a single Background chapter)*

---

## 4 Mathematical Background

> `<INSERT>` **What to write (THESIS-specific — a paper would omit this):** define notation once, then give the formal machinery the method rests on. Keep it rigorous but only as deep as §6 uses. Each formula gets a one-line intuition. **Cite each construct to its origin.**

- **4.1 Notation & basics.** Sets, the snapshot as a structured object, tokens/embeddings. *(§5 reuses this.)*
- **4.2 LLM decoding & constrained generation.** Autoregressive factorization `p(y)=∏ p(yₜ|y_<t)`; grammar/JSON-schema-constrained decoding as per-token logit masking (valid tokens kept, invalid → −∞) `[GCD]`; the accuracy cost of over-constraining `[SpeakFreely, Snowball]`.
- **4.3 Retrieval mathematics (RAG).** Dense embeddings; **cosine similarity** `sim(q,d)=⟨q,d⟩/(‖q‖‖d‖)`; top-k retrieval; (optional) BM25 sparse scoring; Personalized-PageRank for graph retrieval `[HippoRAG]`. Ground in the RAG formulation `[RAG-Origin]`.
- **4.4 Monte-Carlo Tree Search & LATS.** The four MCTS phases (selection, expansion, simulation, backpropagation); **UCT/UCB1 selection** `UCB(s,a)=Q(s,a)+c·√(ln N(s)/N(s,a))` `[UCT]`; value backup; LATS's use of an LLM value function + external feedback `[LATS]`; the noisy-value-estimate problem and bias-aware pruning `[PAC-MCTS]`. Lineage: MCTS in games `[AlphaZero]`.
- **4.5 Evaluation statistics.** Hallucination **rate as a proportion** with a **Wilson/Clopper–Pearson confidence interval**; repeat-run **variance** for robustness; **significance testing** for M-vs-L (`[SigTest]`); **inter-rater agreement** (Cohen's/Fleiss' κ) for the expert panel `[Kappa]`; **SUS** scoring formula `[SUS]` and **UEQ** scale aggregation `[UEQ]`.

---

## 5 Problem Formulation

> `<INSERT>` **What to write:** formalize crisply (a thesis is expected to). Define `S`, `V`, `C`, the metrics — reuse §4 notation. End by stating the exact quantities the experiment measures. **Cite:** `[Faithful]` (traceability = faithful not post-hoc), `[Ji]` (hallucination typology), `[GCD]` (structural validity).

- **5.1 System under study.** Snapshot `S` (JSON, |S| = 70k–200k entries); validation engine `V: S → {valid} ∪ Errors`; goal: correction operator `C` s.t. `V(C(S)) = valid` **and** `C` is factually rule-conformant.
- **5.2 The deterministic verifier.** What `V` decides deterministically (schema, references, required fields, re-validation) `[GCD]` vs. what it **cannot** (semantic/*fachliche* correctness → no ground truth). This boundary drives the method.
- **5.3 Operationalized metrics.**
  - *Hallucination rate* — proportion of outputs with factually incorrect / unprovable / rule-violating corrections, typed {factual, structural, rule, follow-up} `[Ji]`.
  - *Traceability* — degree the input→output path is reconstructable; counts only if it reflects the **real** decision process, not a post-hoc plausible story `[Faithful]`.
  - *Robustness* — consistency under repeated/varied inputs; separate **stochastic** vs **architectural** instability.
- **5.4 Deployed system (context).** Four-agent orchestration (Orchestrator; RAG-agent over Azure AI Search — advanced/agentic RAG `[RAGSurvey, AgenticRAG]`; Smart-Planning agent, 10 tools + 4 pipelines, monolithic 425-line prompt; Chat); iterative validate→correct→re-validate loop. Experimental baseline `M` (§6) isolates the monolithic correction agent from this orchestration.

---

## 6 Method: LATS as the Graph-based Architecture

> `<INSERT>` **What to write:** *your* system. Lead with the two-system definition, then the LATS formalization (reuse §4.4), then the honest controls/costs. Add the architecture figure. **Cite spine below.**

- **6.1 Two systems under comparison.**
  - **System 1 — Monolithic RAG (M).** The deployed Smart-Planning correction agent isolated from the orchestration: single monolithic prompt (425 lines) + RAG `[RAGSurvey]` + iterative validate→correct→re-validate loop; flat, no explicit intermediate states.
  - **System 2 — Graph-based LATS+RAG (L).** Same LLM, RAG substrate, verifier. Correction = a directed processing graph explored by **LATS** `[LATS]`; node/action structure = the exposé's step decomposition `[GoT, MindMap]`.
- **6.2 LATS formalization for JSON correction** (reuse §4.4).
  - *State* = (snapshot region, corrections so far, latest validation result, retrieved rules).
  - *Action* = a reason-and-act tool call (retrieve · map-rule · generate-correction · validate) `[ReAct, Toolformer]`.
  - *Value function* = verifier `V` (structural reward) + rubric LLM-judge (semantic) `[CaseAwareJudge, GEval]` — partial ground truth (§5.2).
  - *Search loop* = MCTS: selection (UCB `[UCT]`) → expansion → evaluation (`V`+judge) → backprop; self-reflection on failed branches `[LATS, Shinn]`.
  - *Termination* = `V=valid` ∧ semantic gate passes, or budget exhausted → best trajectory.
  - `TODO: architecture figure` — step graph, search tree at correction node, verifier gate, bounded loop.
- **6.3 Shared substrate (controlled).** Identical model `[GPT4]`, params, RAG `[RAGSurvey]`, verifier, test cases. **Only** independent variable = reasoning structure.
- **6.4 Structured-output risk handling.** Structural gate (syntax, constrained decoding `[GCD]`) separate from semantic gate — avoid over-constraining `[SpeakFreely, Snowball]`.
- **6.5 Cost/latency controls.** Bound tree depth/width; token budget; fall back to single expansion when `V` passes first try `[PAC-MCTS]`. Report M-vs-L trade-off honestly.
- **6.6 Traceability artifact.** The LATS tree (explored+pruned branches, per-node `V`/judge scores) *is* the revision-safe audit report `[Faithful]`.
- **6.7 Future extensions (not in the comparison).** KG grounding `[MindMap, GraphRAG, KG-Industrial]`; corrective re-retrieval `[CRAG, SelfRAG]`; hierarchical retrieval `[RAPTOR, StructRAG, EntRAG]` (§11).

---

## 7 Implementation

> `<INSERT>` **What to write (THESIS-specific chapter):** the engineering — enough for reproduction. A paper compresses this into a footnote; a thesis dedicates a chapter. **Cite:** framework/model docs; `[GPT4]` for the model; RAG stack `[RAGStack]`.

- **7.1 Tech stack & infra.** Azure (OpenAI GPT-4.1, AI Foundry, AI Search, Storage); Terraform IaC; Python; Git; logging/monitoring.
- **7.2 LATS engine.** Search implementation (framework or custom), node/state schema, action executors, value-function wiring to `V` + judge, budget controls.
- **7.3 RAG substrate.** Azure AI Search index, NL ruleset, chunking/retrieval config (shared by M and L).
- **7.4 Integration with Smart Planning.** Snapshot fetch/apply/re-validate; audit-report generation; metadata logging.
- **7.5 Reproducibility hooks.** Seeds/params, prompt versions, config; pointers to Appendix B.

---

## 8 Experimental Setup

> `<INSERT>` **What to write:** make it reproducible. Fill the catalog counts once the data is fixed. **Cite:** `[SigTest]` (stats), `[Kappa]` (agreement), `[SUS, UEQ]` (instruments), `[RAGAS]` (supplementary metric).

- **8.1 Test-case catalog.** Standard (single unambiguous error) vs Complex (multiple/nested/contradictory, cascade-prone). `TODO: N per class, provenance, error-type distribution.`
- **8.2 Conditions (2-way).** `M` monolithic RAG · `L` graph-based LATS+RAG. LATS internals isolated in §9 ablation, not as extra top-level systems.
- **8.3 Controls.** Identical inputs; constant model+params `[GPT4]`; randomized order; blind (architecture-agnostic) evaluation.
- **8.4 Evaluation framework (3 layers).**
  - *Technical* — schema/reference/required-field checks, re-validation via `V`; metrics: valid/invalid corrections, follow-up errors, iterations, repeat-run variance.
  - *Expert* — 2–4 domain experts, unified rubric, blind; κ agreement `[Kappa]`; protocols as qualitative data.
  - *User* — SUS `[SUS]` + UEQ `[UEQ]` (≥5). RAGAS `[RAGAS]` supplementary for NL-justification; structured judge `[GEval, CaseAwareJudge, RubricRAG]`.
- **8.5 Metrics & statistics.** Per-metric estimator; proportion CIs; repetition `k`; significance test M-vs-L `[SigTest]` (§4.5).

---

## 9 Results and Ablation

> `<INSERT>` **What to write:** report per dimension; lead with the headline `M vs L` table; each table has a takeaway sentence. **Fill after runs — do not invent numbers.** **Cite:** `[Ji]`, `[GoT]` for expected patterns.

- **9.1 Main result.** Table `M vs L` × {hallucination rate by type, traceability, robustness/variance, follow-up errors, iterations, latency, tokens}. `TODO`.
- **9.2 Hallucination (UF1).** Expect `L` advantage on **complex** cases; ~none on standard `[Ji]`.
- **9.3 Traceability (UF3).** Expect **largest** gain for `L` (explicit LATS tree) `[GoT]`.
- **9.4 Robustness (UF2).** Expect **moderate** gain; repeat-run consistency; stochastic vs architectural.
- **9.5 Qualitative.** Expert-protocol themes; new failure modes at node boundaries.

### 9.6 Ablation Study
> `<INSERT>` **What to write:** attribute gains via the M → greedy-`L` → full-`L` ladder. One row = one controlled run set; report Δ vs full `L`. **Cite in-table.**

*Separating the confound:* `M` and `L` differ in decomposition **and** search. Ladder: `M` (no decomp, no search) → **greedy `L`** (decomp, no search) → **full `L`** (decomp+search). `M`→greedy-`L` isolates *decomposition*; greedy-`L`→full-`L` isolates *search*.

| Ablation | Varies | Isolates | Expected |
|---|---|---|---|
| depth/width sweep (→ single-expansion ≈ greedy) | the search | search gain = full `L` − greedy `L` | largest on complex; ~0 on standard |
| verifier reward → LLM self-critique | external `V` → intrinsic | external-feedback value `[Kamoi]` | degradation |
| self-reflection on/off | Reflexion memory | reflection value `[Shinn]` | more repeated failures without |
| semantic gate (judge) on/off | semantic reward | semantic-pruning value `[CaseAwareJudge]` | more semantic hallucinations without |
| step-decomposition granularity | action-space grain | constraint-isolation `[Ji]` | U-shaped |
| constrained decoding tightness | syntax-only vs over-constrained | over-constraining cost `[SpeakFreely, Snowball]` | tight hurts semantics |
| RAG → KG grounding (optional) | vector vs KG | grounding value `[KG-Industrial]` | fewer invented refs |

---

## 10 Discussion

> `<INSERT>` **What to write:** interpret, don't repeat numbers. Answer "when does the graph help?" per complexity class; state costs; be adversarial about validity. **Cite:** `[CaseAwareJudge]` (judge bias), `[Kamoi]` (self-critique limits), `[SpeakFreely]` (constraint costs).

- **10.1 When does the graph help?** Differentiated (better / equal / conditionally) per complexity class.
- **10.2 Cost of the approach.** Latency/token overhead; engineering complexity; new failure modes.
- **10.3 Threats to validity.** Single use case; no semantic ground truth (mitigated by expert panel + κ `[Kappa]`); decomposition-vs-search confound (mitigated by ablation ladder); judge bias `[CaseAwareJudge]`; small user-N; construct validity of the metrics.
- **10.4 Design guidelines (C3).** Actionable rules for prompt/graph architectures in industrial LLM systems.

---

## 11 Conclusion and Future Outlook

> `<INSERT>` **What to write:** restate answer to the RQ + the 3 contributions in 1 paragraph; concrete recommendation for the Smart Planning system; then future work. **Cite:** future-work anchors only.

- **11.1 Conclusion.** Answer the RQ; restate C1–C3; recommend a path for the real system.
- **11.2 Future work.** KG grounding of the ruleset `[MindMap, GraphRAG, KG-Industrial]`; bias-aware pruning of the semantic value fn `[PAC-MCTS]`; a learned semantic verifier; online/multi-snapshot deployment; transfer of the eval framework to other structured-output domains.

---

## 12 Reproducibility Statement

Data (anonymized snapshots), test-case catalog, both prompts, graph/LATS config, judge rubric + JSON schema, aggregation code. `TODO: repo/appendix pointers.`

---

## References

*(48 PDFs in `pdf/`. Convert to the department's citation style at write-up. Load-bearing claims should cite the **renowned-venue** entries; 2026 arXiv preprints are supporting only.)*

**Hallucination, self-correction, reasoning, search**
- **[Ji]** Ji et al. (2023). *Survey of Hallucination in NLG.* ACM Computing Surveys 55(12). — `pdf/Ji-2023-Survey-Hallucination-NLG.pdf`
- **[Tonmoy]** Tonmoy et al. (2024). *A Comprehensive Survey of Hallucination Mitigation Techniques in LLMs.* — `pdf/Tonmoy-2024-Survey-Hallucination-Mitigation.pdf`
- **[CoVe]** Dhuliawala et al. (2024). *Chain-of-Verification Reduces Hallucination in LLMs.* **ACL 2024 Findings.** — `pdf/Dhuliawala-2023-Chain-of-Verification.pdf`
- **[Madaan]** Madaan et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* **NeurIPS 2023.** — `pdf/Madaan-2023-Self-Refine.pdf`
- **[Shinn]** Shinn et al. (2023). *Reflexion: Verbal Reinforcement Learning.* **NeurIPS 2023.** — `pdf/Shinn-2023-Reflexion.pdf`
- **[Pan]** Pan et al. (2023). *Automatically Correcting LLMs: A Survey of Self-Correction.* — `pdf/Pan-2023-Automatically-Correcting-LLMs-Survey.pdf`
- **[Kamoi]** Kamoi et al. (2024). *When Can LLMs Actually Correct Their Own Mistakes?* **TACL.** — `pdf/Kamoi-2024-When-Can-LLMs-Correct-Mistakes.pdf`
- **[CoT]** Wei et al. (2022). *Chain-of-Thought Prompting.* **NeurIPS 2022.** — `pdf/Wei-2022-Chain-of-Thought-NeurIPS.pdf`
- **[SelfCons]** Wang et al. (2023). *Self-Consistency Improves CoT Reasoning.* **ICLR 2023.** — `pdf/Wang-2022-Self-Consistency-ICLR.pdf`
- **[ReAct]** Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting.* **ICLR 2023.** — `pdf/Yao-2023-ReAct-ICLR.pdf`
- **[ToT]** Yao et al. (2023). *Tree of Thoughts.* **NeurIPS 2023.** — `pdf/Yao-2023-Tree-of-Thoughts-NeurIPS.pdf`
- **[Toolformer]** Schick et al. (2023). *Toolformer.* **NeurIPS 2023.** — `pdf/Schick-2023-Toolformer-NeurIPS.pdf`
- **[GoT]** Besta et al. (2024). *Graph of Thoughts.* **AAAI 2024.** — `pdf/Besta-2024-Graph-of-Thoughts.pdf`
- **[MindMap]** Wen et al. (2024). *MindMap: KG Prompting Sparks GoT.* **ACL 2024.** — `pdf/Wen-2024-MindMap-KG-Prompting.pdf`
- **[LATS]** Zhou et al. (2024). *Language Agent Tree Search.* **ICML 2024.** — `pdf/Zhou-2024-LATS-Language-Agent-Tree-Search.pdf`
- **[PAC-MCTS]** (2026). *PAC-MCTS: Bias-Aware Pruning for LLM-Guided Search.* — `pdf/PAC-MCTS-2026-Bias-Aware-Pruning.pdf`
- **[UCT]** Kocsis & Szepesvári (2006). *Bandit Based Monte-Carlo Planning (UCT).* **ECML 2006.** *(seminal MCTS; not on arXiv)*
- **[AlphaZero]** Silver et al. (2017). *Mastering Chess and Shogi by Self-Play (AlphaZero).* **Nature/arXiv.** *(MCTS lineage)*

**Structured output & constrained decoding**
- **[GCD]** Geng et al. (2023). *Grammar-Constrained Decoding for Structured NLP Tasks.* **EMNLP 2023 Findings.** — `pdf/Geng-2023-Grammar-Constrained-Decoding-EMNLP.pdf`
- **[SpeakFreely]** Tam et al. (2024). *Let Me Speak Freely? On the Cost of Format Restrictions.* **EMNLP 2024 Industry.** — `pdf/Tam-2024-Let-Me-Speak-Freely-Constraints-Hurt-EMNLP.pdf`
- **[Snowball]** (2026). *From Hallucination to Structure Snowballing.* — `pdf/Structure-Snowballing-2026-Constrained-Decoding.pdf`

**Retrieval-Augmented Generation**
- **[RAG-Origin]** Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP.* **NeurIPS 2020.** — `pdf/Lewis-2020-RAG-Original-NeurIPS.pdf`
- **[RAGSurvey]** Gao et al. (2024). *RAG for LLMs: A Survey.* — `pdf/Gao-2024-RAG-Survey-Naive-Advanced-Modular.pdf`
- **[RAGStack]** (2026). *Engineering the RAG Stack.* — `pdf/Engineering-the-RAG-Stack-Review-2026.pdf`
- **[RAPTOR]** Sarthi et al. (2024). *RAPTOR: Recursive Tree-Organized Retrieval.* **ICLR 2024.** — `pdf/Sarthi-2024-RAPTOR-Hierarchical-Tree-Retrieval.pdf`
- **[GraphRAG]** Edge et al. (2024). *From Local to Global: A Graph RAG Approach.* — `pdf/Edge-2024-GraphRAG-Microsoft.pdf`
- **[HippoRAG]** Gutiérrez et al. (2024). *HippoRAG.* **NeurIPS 2024.** — `pdf/Gutierrez-2024-HippoRAG.pdf`
- **[LightRAG]** Guo et al. (2024). *LightRAG.* — `pdf/Guo-2024-LightRAG.pdf`
- **[HiRAG]** (2025). *RAG with Hierarchical Knowledge.* — `pdf/HiRAG-2025-Hierarchical-Knowledge-RAG.pdf`
- **[SelfRAG]** Asai et al. (2024). *Self-RAG.* **ICLR 2024.** — `pdf/Asai-2024-Self-RAG.pdf`
- **[CRAG]** Yan et al. (2024). *Corrective RAG.* — `pdf/Yan-2024-CRAG-Corrective-RAG.pdf`
- **[AdaptiveRAG]** Jeong et al. (2024). *Adaptive-RAG.* **NAACL 2024.** — `pdf/Jeong-2024-Adaptive-RAG.pdf`
- **[AgenticRAG]** Singh et al. (2025). *Agentic RAG: A Survey.* — `pdf/Singh-2025-Agentic-RAG-Survey.pdf`
- **[ReasoningRAG]** (2025). *Reasoning RAG via System 1 or System 2.* — `pdf/Reasoning-Agentic-RAG-Survey-2025.pdf`
- **[StructRAG]** (2024). *Reducing Hallucination in Structured Outputs via RAG.* — `pdf/Bheel-2024-Reducing-Hallucination-Structured-Outputs-RAG.pdf`
- **[EntRAG]** Cheerla (2025). *RAG for Structured Enterprise Data.* — `pdf/Cheerla-2025-RAG-Structured-Enterprise-Data.pdf`
- **[T2RAG]** (2025). *T²-RAGBench: Text-and-Table Benchmark.* — `pdf/T2-RAGBench-2025-Text-and-Table.pdf`

**Evaluation & methodology**
- **[LLMJudge]** Zheng et al. (2023). *Judging LLM-as-a-Judge with MT-Bench & Chatbot Arena.* **NeurIPS 2023 D&B.** — `pdf/Zheng-2023-LLM-as-Judge-MT-Bench-NeurIPS.pdf`
- **[GEval]** Liu et al. (2023). *G-Eval: NLG Evaluation using GPT-4.* **EMNLP 2023.** — `pdf/Liu-2023-G-Eval-EMNLP.pdf`
- **[RAGAS]** Es et al. (2024). *RAGAs: Automated RAG Evaluation.* **EACL 2024.** — `pdf/Es-2024-RAGAS.pdf`
- **[CaseAwareJudge]** (2026). *Case-Aware LLM-as-a-Judge for Enterprise RAG.* — `pdf/Case-Aware-LLM-as-Judge-Enterprise-RAG-2026.pdf`
- **[RubricRAG]** (2026). *RubricRAG.* — `pdf/RubricRAG-2026.pdf`
- **[Faithful]** Jacovi & Goldberg (2020). *Towards Faithfully Interpretable NLP Systems.* **ACL 2020.** — `pdf/Jacovi-2020-Faithfully-Interpretable-NLP-ACL.pdf`
- **[SUS]** Brooke (1996). *SUS: A "Quick and Dirty" Usability Scale.* Taylor & Francis. *(not on arXiv)*
- **[UEQ]** Laugwitz, Held & Schrepp (2008). *Construction and Evaluation of a UEQ.* **USAB 2008, Springer LNCS 5298.** *(not on arXiv)*
- **[SigTest]** Dror et al. (2018). *The Hitchhiker's Guide to Testing Statistical Significance in NLP.* **ACL 2018.** *(not downloaded — add if needed)*
- **[Kappa]** Cohen (1960). *A Coefficient of Agreement for Nominal Scales.* Educ. & Psych. Measurement. *(seminal; not on arXiv)*
- **[DSR]** Hevner et al. (2004). *Design Science in IS Research.* **MIS Quarterly.** *(methodology; not on arXiv)*
- **[CaseStudy]** Runeson & Höst (2009). *Guidelines for Case Study Research in SE.* **Empirical Software Engineering (Springer).** *(methodology)*

**Knowledge graphs & industrial context**
- **[KG-Survey]** Agrawal et al. (2023). *Can KGs Reduce Hallucinations in LLMs? A Survey.* — `pdf/Agrawal-2023-Can-KG-Reduce-Hallucinations-Survey.pdf`
- **[KG-Industrial]** (2026). *KGs as the Missing Data Layer for Industrial LLM Ops.* — `pdf/KG-as-Data-Layer-Industrial-Ops-2026.pdf`
- **[GraphFlow]** (2026). *GraphFlow: Graph-Based Workflow Management for LLM Agents.* — `pdf/GraphFlow-2026-Graph-Workflow-Management.pdf`
- **[AgentLoops]** (2026). *From Agent Loops to Structured Graphs.* — `pdf/Agent-Loops-to-Structured-Graphs-2026.pdf`
- **[WorkflowSurvey]** (2026). *Survey of Workflow Optimization for LLM Agents.* — `pdf/Survey-Workflow-Optimization-LLM-Agents-2026.pdf`
- **[GPT4]** OpenAI (2023). *GPT-4 Technical Report.* — `pdf/OpenAI-2023-GPT-4-Technical-Report.pdf`
- **[Industry40]** Lasi et al. (2014). *Industry 4.0.* **Business & Information Systems Engineering.** *(foundational; not on arXiv)*
- **[ManufLLM]** (2024). *A Survey of Emerging Applications of LLMs in Mechanics, Product Design & Manufacturing.* **Advanced Engineering Informatics (Elsevier).** *(add PDF if licensed)*
- **[IndLLM]** (2025). *Autonomous Control Leveraging LLMs: An Agentic Framework for Industrial Automation.* — `pdf/Industrial-LLM-Agentic-Automation-2025.pdf`

---

## Appendix (planned)

- **A** Full test-case catalog + error-type taxonomy.
- **B** Both system prompts (monolithic) + graph/LATS definition (nodes/edges/state schemas) + configs.
- **C** Expert rubric + LLM-judge prompt + JSON verdict schema.
- **D** Per-case raw results, trace logs, pruned-subtree samples.
- **E** SUS/UEQ instruments and scores.

---

> **Section ↔ Exposé map:** §1↔Exposé 1+2 · §2↔Exposé 1.1/1.4 lit (+RAG/foundations depth) · §4 Math = **thesis-required, new** · §5↔Exposé 1.2/5.1 · §6↔Exposé 3/4.1 (System 2 = step-decomposition graph, **LATS as search layer**) · §7 Implementation = **thesis-required, new** · §8↔Exposé 4/5 (**2-way M vs L**) · §9↔Exposé 5.2/5.3/6 + ablation (isolates LATS internals) · §10↔Exposé 5.4/6 · §11↔Exposé 6 · §12/Equipment↔Exposé 9.
>
> **Deviation ledger (for supervisor):** (1) **LATS as search layer** — enhancement of the exposé's GoT-graph; step decomposition preserved; **needs sign-off.** (2) **§4 Mathematical Background & §7 Implementation** — added because this is a *thesis, not a paper* (expected by FH). (3) **RAG-family + foundational-venue citations** — additive breadth, no conflict. (4) **§9.6 Ablation** — new, standard for empirical rigor. Everything else is 1:1 with the exposé.
