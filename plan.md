# VedyaAI — Master Architecture & Product Plan

> **Version:** 2.0 (Architecture Review & Enhancement)  
> **Supersedes:** Version 1.0 (2026-07-18 initial plan)  
> **Document status:** Ready for dual-architect re-review  
> **Deliverable scope:** Planning only — no implementation until approved  
> **Last updated:** 2026-07-18

---

## Table of Contents

1. [Architecture Review (V1 Critique)](#1-architecture-review-v1-critique)
2. [Executive Summary](#2-executive-summary)
3. [Problem Discovery](#3-problem-discovery)
4. [Market & Competitor Analysis](#4-market--competitor-analysis)
5. [Product Definition](#5-product-definition)
6. [User Personas, Journeys & Stories](#6-user-personas-journeys--stories)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Product Features](#9-product-features)
10. [Knowledge Modeling](#10-knowledge-modeling)
11. [Data Strategy](#11-data-strategy)
12. [AI Strategy](#12-ai-strategy)
13. [Agent Architecture Decision](#13-agent-architecture-decision)
14. [System Architecture](#14-system-architecture)
15. [Technical Decision Records](#15-technical-decision-records)
16. [Recommended Technologies](#16-recommended-technologies)
17. [User Experience Design](#17-user-experience-design)
18. [Innovation Analysis](#18-innovation-analysis)
19. [Risks, Assumptions & Trade-offs](#19-risks-assumptions--trade-offs)
20. [Demo & Hackathon Strategy](#20-demo--hackathon-strategy)
21. [Development Roadmap & Milestones](#21-development-roadmap--milestones)
22. [Startup Vision Beyond the Hackathon](#22-startup-vision-beyond-the-hackathon)
23. [Team Operating Model](#23-team-operating-model)
24. [Success Metrics](#24-success-metrics)
25. [Open Questions](#25-open-questions)
26. [Final Architecture Audit](#26-final-architecture-audit)
27. [Immediate Next Steps](#27-immediate-next-steps)
28. [Document Control](#28-document-control)

---

## 1. Architecture Review (V1 Critique)

This section records a formal self-review of Version 1 before enhancement. Scores are deliberately strict.

### Scoring rubric

| Score | Meaning |
|-------|---------|
| 0–3 | Missing or misleading |
| 4–5 | Present but shallow / incomplete |
| 6–7 | Solid for hackathon; weak for production thinking |
| 8–9 | Strong; minor gaps |
| 10 | Would survive principal-engineer review with little change |

### Section-by-section review

#### Executive Summary — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Orient readers to the core thesis quickly |
| Complete? | Partially — thesis strong, business framing thin |
| Too shallow? | Yes on *why now*, market, and non-goals |
| Assumptions | Judges prefer discrimination over breadth; data exists |
| Missing | Mission, adoption thesis, explicit anti-patterns |
| Judge critique | “Sounds smart — prove it isn’t another RAG wrapper” |
| Architect critique | No explicit system boundary or success contract |

#### Problem Analysis — **6/10**

| Question | Answer |
|----------|--------|
| Why written? | Reframe search → discrimination |
| Complete? | No — weak on current workflow & why unsolved |
| Too shallow? | Challenges listed; root-cause economics missing |
| Assumptions | Pain is formulation selection, not diagnosis |
| Missing | Today’s tools, failure modes, willingness-to-pay proxies |
| Judge critique | “Where is evidence people actually struggle this way?” |
| Architect critique | No problem decomposition into solvable subproblems |

#### Product Vision — **6/10**

| Question | Answer |
|----------|--------|
| Why written? | Define what to build |
| Complete? | Feature-oriented; weak vision/mission/goals |
| Too shallow? | Personas later, journeys absent |
| Assumptions | Workbench UX beats chat |
| Missing | Value proposition hierarchy, adoption drivers, JTBD |
| Judge critique | “What is the memorable product story?” |
| Architect critique | MVP crisp; production product shape fuzzy |

#### User Personas — **5/10**

| Question | Answer |
|----------|--------|
| Why written? | Anchor users |
| Complete? | Sketches only |
| Too shallow? | Yes — no journeys, stories, or failure moments |
| Assumptions | Three personas cover market |
| Missing | Jobs-to-be-done, frequency, environment constraints |
| Judge critique | “Generic healthcare personas” |
| Architect critique | No prioritization of primary vs secondary user |

#### Functional / Non-Functional Requirements — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Spec behavior & quality bars |
| Complete? | FR decent; NFR incomplete (security, a11y, i18n, SLOs) |
| Too shallow? | FRs lack acceptance criteria |
| Assumptions | Demo latency 3–5s is enough |
| Missing | Error states, empty states, audit retention |
| Judge critique | Unlikely to criticize if demo works |
| Architect critique | No requirement IDs traced to tests |

#### Product Features — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Prioritize P0/P1/P2 |
| Complete? | Good prioritization |
| Too shallow? | No UX mapping of features to screens |
| Assumptions | Compare view is killer feature |
| Missing | Explicit kill-list of vanity features |
| Judge / Architect | Solid for stage; needs IA |

#### AI Strategy — **6/10**

| Question | Answer |
|----------|--------|
| Why written? | Prevent pure-RAG failure mode |
| Complete? | Principle good; justification thin |
| Too shallow? | “Why X / why not Y” underdeveloped |
| Assumptions | Hybrid is obviously correct |
| Missing | Decision rights of AI vs deterministic code; eval protocol depth |
| Judge critique | “Show me the AI, not just architecture diagrams” |
| Architect critique | No failure taxonomy for LLM steps |

#### Data Requirements — **5/10**

| Question | Answer |
|----------|--------|
| Why written? | List entities & sources |
| Complete? | Conceptual only |
| Too shallow? | No acquisition, licensing workflow, versioning, QA |
| Assumptions | Hackathon data will be usable |
| Missing | Pipeline, chunking, human verification, lineage |
| Judge critique | “What data did you actually use?” |
| Architect critique | Data is the product — this section was underweighted |

#### System Architecture — **6/10**

| Question | Answer |
|----------|--------|
| Why written? | High-level boxes |
| Complete? | Logical only |
| Too shallow? | No sequence flows, failure modes, trust boundaries |
| Assumptions | Postgres + optional vectors suffice |
| Missing | Knowledge model depth, agent decision, TDRs |
| Judge critique | Looks like every other stack slide |
| Architect critique | No component contracts or data flow invariants |

#### Technologies — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Actionable stack guidance |
| Complete? | Reasonable for hackathon |
| Too shallow? | Alternatives listed; ADRs missing |
| Assumptions | Python preferred for NLP |
| Missing | Decision records, replacement strategy |
| Critiques | Fine for MVP; not production-spec grade |

#### Risks / Assumptions / Trade-offs — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Honesty & scope control |
| Complete? | Good start |
| Too shallow? | Missing regulatory, ops, go-to-market risks |
| Assumptions | Assistive framing is enough legally |
| Missing | Residual risk acceptance criteria |
| Critiques | Solid; needs severity × likelihood |

#### Roadmap / Milestones — **7/10**

| Question | Answer |
|----------|--------|
| Why written? | Execution plan |
| Complete? | Hackathon-centric |
| Too shallow? | No post-hackathon product phases with business gates |
| Missing | Dependency graph, staffing assumptions |
| Critiques | Good for build; weak for venture narrative |

#### Competitive Positioning — **4/10**

| Question | Answer |
|----------|--------|
| Why written? | Differentiation |
| Complete? | Four-row table only |
| Too shallow? | **Yes — major V1 weakness** |
| Missing | Named competitors, research, workflows, gaps |
| Judge critique | “Have you looked at existing AYUSH tools?” |
| Architect critique | Positioning without market map is fragile |

#### Demo Strategy — **6/10**

| Question | Answer |
|----------|--------|
| Why written? | Win the room |
| Complete? | Script present |
| Too shallow? | No objections Q&A, wow moments, judge psychology |
| Missing | Fallback fidelity, timing, prop design |
| Critiques | Usable; not battle-tested |

#### Future Scope — **5/10**

| Question | Answer |
|----------|--------|
| Why written? | Show ambition |
| Complete? | Feature laundry list |
| Too shallow? | No business model, GTM, ecosystem |
| Missing | Monetization, hospital/gov paths, API platform |
| Critiques | Reads as backlog, not vision |

#### Overall V1 score — **6.1 / 10**

**Verdict:** Strong product *thesis*, weak *company-grade* planning. Discrimination insight must be preserved. Market, knowledge ontology, data ops, AI decision rights, UX, TDRs, demo psychology, and startup path must be upgraded.

### Cross-perspective gaps found in V1

| Perspective | What was missing |
|-------------|------------------|
| Product Manager | JTBD, user stories, success criteria, kill criteria |
| Startup Founder | Why now, wedge, monetization, defensibility |
| AI Researcher | Eval design, baselines, ablation story |
| Domain Expert | Ontology fidelity, classical epistemology limits |
| UX Designer | Journey, IA, screen hierarchy, clinical workflow |
| Engineering Manager | Staffing, critical path, quality gates, ownership |
| Hackathon Judge | Wow moments, objection handling, memorability |
| Investor | Market size proxies, moat, expansion narrative |

### What V2 preserves from V1

- Core thesis: **discrimination > search**
- Principle: **Structure decides → Rules protect → Retrieval grounds → LLM explains**
- Punarnavadi vs Vyaghryadi as north-star demo
- Hybrid architecture rejection of pure RAG / pure LLM diagnosis
- Vertical MVP over 150-text vanity
- Safety as deterministic gates
- Citation firewall

### What V2 changes or adds

- Full problem discovery & market map
- Product vision/mission/goals/stories/journeys
- Deep AI “why / why not” + decision rights
- Knowledge ontology & data lifecycle
- Explicit **anti-agent-swarm** decision (pipeline with modules)
- UX information architecture
- TDRs for every major choice
- Startup + monetization path
- Formal final architecture audit

---

## 2. Executive Summary

**VedyaAI** is a classical-grounded **Ayurvedic Formulation Decision Support & Learning Platform**.

It is **not** “ChatGPT over Ayurvedic PDFs.” Pure RAG demos fail clinically and look identical to every other hackathon submission.

### The insight

The problem statement’s own example — *Punarnavadi Kashaya* vs *Vyaghryadi Kashaya* — reveals the true job:

> Many formulations share a primary indication. The hard problem is choosing the **right** one under secondary conditions, comorbidities, medicine medium, and ingredient suitability — then proving the choice with classical references.

That is **differential formulation selection**, not document search.

### What we build

A system that:

1. Interprets a clinical vignette (symptoms + patient constraints).
2. Resolves synonyms and contextual homonyms.
3. Retrieves candidates from a structured classical knowledge base.
4. Applies deterministic safety gates.
5. Ranks and **discriminates** among overlapping formulations.
6. Explains *why A over B* with citable references.
7. Turns every recommendation into a teaching moment.

### Winning thesis (hackathon + product)

> “We don’t return ten decoctions for fever. We show why *Vyaghryadi* fits Pinasa-associated URTI better than *Punarnavadi*, and why *Punarnavadi* fits systemic inflammatory presentations — with classical citations and safety gates.”

### Non-goals (explicit)

- Autonomous diagnosis or prescription
- Claiming medical-device clinical efficacy in MVP
- Ingesting “all 150 texts” without structure
- Chatbot-as-product identity
- Inventing missing Rasa–Guna–Virya–Vipaka values

### One-line value

Reduce time-to-correct-formulation from hours of textual hunting to minutes of explainable, cited decision support — without replacing the vaidya.

---

## 3. Problem Discovery

### 3.1 Why this problem exists

Ayurveda encodes clinical wisdom across centuries of texts: Brihatrayi, Laghutrayi, Nighantus, later yogagranthas, regional commentaries. Knowledge was designed for **guru–shishya transmission**, not computational retrieval.

Digitization solved **access** (PDFs, scans, portals) but not **decision support**. Having 150 searchable texts increases cognitive load: more candidates, more synonyms, more conflicting senses, more ways to miss a contraindication.

### 3.2 Who suffers

| Stakeholder | Pain | Frequency | Cost of error |
|-------------|------|-----------|---------------|
| BAMS / MD (Ayu) student | Cannot cross-walk literature for viva/clinical postings | Daily during training | Learning gaps, exam failure |
| Junior vaidya | OPD time pressure; overlapping yogas | Multiple patients/day | Suboptimal formulation choice |
| Faculty | Hard to create reproducible teaching cases | Weekly | Weak pedagogical consistency |
| Senior vaidya | Distrusts black-box tools; still wants faster lookup | Occasional | Will reject uncited AI |
| Institutions / AYUSH colleges | No standard digital reasoning aid | Continuous | Uneven clinical training quality |

**Primary beachhead user:** BAMS final-year + junior practitioner (learning + speed).  
**Authority user to win trust:** Faculty / senior vaidya (citations + safety).

### 3.3 How they solve it today

1. **Memory & guru guidance** — fastest, non-scalable, uneven quality.
2. **Manual book lookup** — Charaka, Sharangadhara, Bhaishajya Ratnavali, etc.
3. **PDF / digital library keyword search** — returns undifferentiated hits.
4. **Static encyclopedias / formulary browsers** — good catalogs, weak patient context.
5. **Peer discussion / WhatsApp groups** — informal, unverifiable.
6. **Generic LLMs (ChatGPT etc.)** — fluent, often uncited or wrongly cited.

### 3.4 Why current solutions fail

| Approach | Failure mode |
|----------|--------------|
| Memory | Incomplete; bias toward commonly taught yogas |
| Manual texts | Slow; impractical under OPD load |
| Keyword search | No discrimination among overlapping indications |
| Encyclopedias | No comorbidities / medium / ingredient gates |
| Generic LLMs | Hallucinated shlokas; unsafe confidence |
| Research KGs | Browser UX; not clinical workflow |

### 3.5 Why AI is actually needed

AI is needed for **language and explanation**, not for inventing classical knowledge:

- Free-text symptoms → structured clinical frame
- Synonym / vernacular mapping at scale
- Natural-language comparative teaching explanations
- Semantic recall of relevant excerpts when structured fields are incomplete

AI is **not** needed (and must not be trusted) to:

- Invent formulations
- Override contraindication rules
- Fabricate references
- Autonomously diagnose disease

### 3.6 Why hasn’t this already been solved?

1. **Knowledge engineering cost** — structuring classical yoga–indication–ingredient graphs is expensive and expert-bound.
2. **Ambiguity** — synonymy and homonymy are first-class linguistic problems.
3. **Safety liability** — healthcare AI teams avoid domains without clear labels.
4. **Wrong product metaphor** — most attempts built search or chat, not discrimination.
5. **Evaluation vacuum** — no large public gold set of vignette → preferred yoga.
6. **Digitization illusion** — PDFs look “done”; computation-ready ontology is not.

### 3.7 What makes it technically difficult

1. Dense many-to-many indication overlap (discrimination required).
2. Synonym expansion vs contextual sense disambiguation (opposite NLP pressures).
3. Incomplete pharmacological property coverage (must not hallucinate).
4. Safety constraints are logical, not semantic-similarity problems.
5. Citation fidelity under generative models.
6. Inter-expert disagreement on “best” yoga for borderline cases.
7. Multilingual / multi-script legacy (MVP scopes this down).

### 3.8 Hidden challenges

- **Negative knowledge** (“not suitable because…”) is as valuable as recommendations and rarely modeled.
- Same yoga, different indications across texts/editions → provenance conflicts.
- *Kalpana* (Kwatha vs Asava vs Ghrita) changes suitability independent of herbs.
- Prakriti is clinically important but psychometrically noisy — false precision risk.
- Students may treat AI output as exam truth → educational responsibility.
- Regulatory ambiguity (CDSS vs medical device) if overclaimed.

### 3.9 Problem decomposition (solvable subproblems)

| ID | Subproblem | Solvable in MVP? |
|----|------------|------------------|
| P1 | Term normalization (synonyms) | Yes |
| P2 | Contextual homonym senses | Yes (rule-backed demos) |
| P3 | Candidate generation from structured links | Yes |
| P4 | Safety gating (ingredient/medium × condition) | Yes |
| P5 | Pairwise/listwise discrimination ranking | Yes (core) |
| P6 | Citation-bound explanation | Yes |
| P7 | Full Prakriti automation | No (defer) |
| P8 | Corpus-scale OCR of 150 texts | No (defer) |
| P9 | Clinical outcome validation RCT | No (post-venture) |

---

## 4. Market & Competitor Analysis

### 4.1 Current clinical/academic workflow

```
Patient presents
  → History + examination (vaidya)
  → Provisional roga / lakshana framing
  → Mental shortlist of yogas from memory/texts
  → Check ingredients, kalpana, comorbidities (often informal)
  → Select yoga + anupana + pathya advice
  → Teach student (if teaching hospital)
```

**Friction points:** shortlist construction, discrimination, contraindication recall, citation for teaching.

### 4.2 Competitive landscape

#### A. Manual / traditional approaches

| | Detail |
|--|--------|
| **Examples** | Guru guidance, classical book study, college notes |
| **Strengths** | High trust, contextual wisdom, pedagogical depth |
| **Weaknesses** | Not scalable, slow, uneven across practitioners |
| **Gaps** | No computational discrimination, no audit trail |
| **Opportunity** | Encode *teachable discrimination patterns* without replacing guru |

#### B. Digital repositories & formularies

| | Detail |
|--|--------|
| **Examples** | Ayurvedic Formulary of India (AFI), Pharmacopoeia portals, digital libraries, static yoga encyclopedias, Bhaishajya Kalpana Kosha-like catalogs |
| **Strengths** | Authoritative listings, dosage/anupana fields, standardization |
| **Weaknesses** | Catalog mentality; weak patient-context ranking |
| **Gaps** | No “why A over B”; limited contraindication automation |
| **Opportunity** | Become the **decision layer** on top of repositories |

#### C. Graph / research databases

| | Detail |
|--|--------|
| **Examples** | GRAYU, AyurKOSH-like KGs, academic extractions |
| **Strengths** | Rich associations (plant–disease–phytochemical) |
| **Weaknesses** | Research UX; not OPD workflow; may lack classical citation UX |
| **Gaps** | Explanation + safety + learning journey |
| **Opportunity** | Reuse structured links; wrap with clinical discrimination UX |

#### D. Named / similar software attempts

| | Detail |
|--|--------|
| **Examples** | AYURSOFTAPP-class formulary suggestors; various college projects; questionnaire dosha apps |
| **Strengths** | Domain intent aligned; some synonym/contraindication awareness |
| **Weaknesses** | Often search-first; weak eval; limited explainability; thin AI |
| **Gaps** | Comparative discrimination as hero; citation firewall; golden vignette science |
| **Opportunity** | Out-execute on **ranking + explain + safety + demo science** |

#### E. Textbook-grounded CDSS research

| | Detail |
|--|--------|
| **Examples** | Academic pipelines extracting disease–dosha–treatment graphs; ML dosha classifiers |
| **Strengths** | Text fidelity focus; methodological seriousness |
| **Weaknesses** | Not productized; may optimize diagnosis more than formulation discrimination |
| **Gaps** | Practitioner UX, safety productization, hackathon-ready narrative |
| **Opportunity** | Borrow grounding ethos; specialize on formulation choice |

#### F. Generic AI chatbots

| | Detail |
|--|--------|
| **Examples** | ChatGPT / Gemini / Claude used ad hoc by students |
| **Strengths** | Fluent NL, zero onboarding, always available |
| **Weaknesses** | Hallucinated references, inconsistent classical fidelity, no deterministic safety |
| **Gaps** | Trust, auditability, curriculum alignment |
| **Opportunity** | Be the **trusted alternative**: grounded, constrained, citeable |

#### G. Wellness / consumer Ayurveda apps

| | Detail |
|--|--------|
| **Examples** | Dosha quizzes, lifestyle tip apps |
| **Strengths** | Consumer distribution |
| **Weaknesses** | Not classical CDSS; low academic credibility |
| **Gaps** | Serious clinical/educational use |
| **Opportunity** | Explicitly **not** compete here; stay clinical-education grade |

### 4.3 Competitive advantage (moat thesis)

| Moat layer | Why it defends |
|------------|----------------|
| **Discrimination engine** | Harder to copy than a chat UI |
| **Ontology + synonym/homonym graph** | Expert-expensive to rebuild |
| **Safety rulebase** | Trust differentiator; testable |
| **Golden vignette eval harness** | Scientific credibility |
| **Citation-bound generation policy** | Brand of trust |
| **Teaching UX (A vs B)** | Habit formation in colleges |

**Positioning statement:**  
VedyaAI is the decision and learning layer that turns Ayurvedic repositories into a **context-aware, citeable formulation discriminator**.

### 4.4 Why users adopt (adoption thesis)

- **Students:** faster viva prep + clearer reasoning than PDFs/chatbots  
- **Juniors:** 30–60s shortlist with safety flags  
- **Faculty:** assignable, reproducible cases with citations  
- **Institutions:** standardized teaching aid aligned to classical sources  

### 4.5 Why judges remember it

One sentence they can repeat:  
*“They showed two fever decoctions and made the AI explain which one fits — with shastra citations and diabetes safety gates.”*

---

## 5. Product Definition

### 5.1 Vision

Make classical Ayurvedic formulation wisdom **computable, comparable, and teachable** — so every learner and practitioner can reach a citeable drug-of-choice insight in minutes.

### 5.2 Mission

Build the most trustworthy AI-assisted formulation decision support system for Ayurveda by combining structured classical knowledge, deterministic safety, and citation-bound explanation.

### 5.3 Product goals

| Goal | Description |
|------|-------------|
| G1 Clinical utility | Shortlist appropriate yogas under patient constraints |
| G2 Safety | Never silently recommend known contraindicated ingredient/medium matches |
| G3 Trust | Every recommendation carries provenance |
| G4 Pedagogy | Every session teaches discrimination reasoning |
| G5 Extensibility | New texts/formulations enrich the graph without rewriting the brain |
| G6 Responsibility | Remain decision support; clinician/learner retains authority |

### 5.4 Core value proposition

**For** Ayurvedic students and practitioners  
**who** struggle to choose among overlapping classical formulations  
**VedyaAI** is a formulation discrimination workbench  
**that** ranks suitable yogas with comparative explanations, classical citations, and safety alerts  
**unlike** PDF search and generic chatbots  
**which** either dump undifferentiated results or sound confident without grounding.

### 5.5 Success criteria

**Hackathon success**

- Live demo wins the Punarnavadi vs Vyaghryadi narrative
- Judges can restate the differentiator
- Zero fabricated citations in demo path
- Safety case visibly fires

**Product success (near-term)**

- Pairwise ranking accuracy ≥ 80% on golden set
- Time-to-shortlist < 60s for trained users on covered clusters
- Faculty willingness to assign ≥ 1 case in teaching

**Kill criteria (pivot or stop feature)**

- If ranker cannot beat keyword baseline on golden pairwise tasks → fix data/ranker before UI polish
- If explanations hallucinate refs in eval → ship structured templates only

### 5.6 What should actually be built (product shape)

**VedyaAI — Classical Formulation Discriminator & Learning Companion**

**Inputs**

- Free-text + structured symptoms/lakshanas
- Optional provisional roga
- Patient profile: age band, comorbidities, pregnancy, allergies; optional soft Prakriti
- Optional kalpana constraints

**Outputs**

1. Ranked formulations & single drugs with fit scores  
2. Why this / why not that comparative explanations  
3. Classical reference cards  
4. Safety panel (ingredient + medium)  
5. Pharmacological property cards when available  
6. Learning panel (synonyms, discrimination teaching point)

---

## 6. User Personas, Journeys & Stories

### 6.1 Personas

#### Primary — Ananya (Final-year BAMS)

- **Job:** Prepare clinically sound reasoning for postings/viva  
- **Environment:** Hostel/college Wi-Fi, mobile + laptop  
- **Success:** Explains why Vyaghryadi > Punarnavadi in Pinasa vignette  
- **Fear:** Memorizing lists without understanding  

#### Primary — Dr. Rohan (Junior practitioner)

- **Job:** Reach a defensible shortlist quickly in OPD  
- **Environment:** Time-poor clinic; intermittent connectivity  
- **Success:** 30–60s cited shortlist + safety flags  
- **Fear:** Missing an obvious contraindication  

#### Authority — Prof. Meera (Faculty)

- **Job:** Teach reproducible classical reasoning  
- **Success:** Assigns VedyaAI cases; trusts citations  
- **Fear:** Students learning from hallucinated AI  

#### Secondary — Hackathon judges / technical evaluators

- Need: clear AI story, measurable demo, responsible stance  

### 6.2 User journeys

#### Journey A — Student learning session

1. Opens **Demo/Learn** preset or enters vignette  
2. Sees resolved terms + synonyms (*Jvara* ↔ *Santapa*)  
3. Reviews ranked yogas  
4. Opens **Compare** for top-2  
5. Reads citation cards  
6. Toggles Learning mode → teaching point saved mentally / notes  

#### Journey B — Junior clinical assist

1. Enters chief complaints + diabetes comorbidity  
2. System resolves entities  
3. Safety panel flags unsuitable media/ingredients  
4. Reviews remaining ranked options  
5. Verifies references before clinical judgment  
6. Does **not** auto-prescribe  

#### Journey C — Faculty classroom

1. Launches preset vignette on projector  
2. Asks class to predict ranking  
3. Reveals VedyaAI discrimination + citations  
4. Discusses disagreement / classical nuance  

### 6.3 Key user stories

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a student, I enter fever+cough+cold so I get a ranked shortlist with reasons | P0 |
| US-02 | As a practitioner, I add diabetes so unsafe jaggery/fermented options are flagged | P0 |
| US-03 | As a user, I see why A ranked above B in one screen | P0 |
| US-04 | As a user, I see classical references for each recommendation | P0 |
| US-05 | As a student, I see synonym tags so I learn multiple names of one disease | P0 |
| US-06 | As a user, I search by pharmacological property (e.g., Tikta rasa) | P1 |
| US-07 | As a user, I see correct sense of *Abhaya* in *Jatyadi* context | P1 |
| US-08 | As a faculty member, I run preset cases without typing | P0 (demo) |
| US-09 | As a user, I understand when data is missing (no invented Virya) | P0 |
| US-10 | As a practitioner, I get counterfactual (“without diabetes, ranking changes”) | P1 |

---

## 7. Functional Requirements

Acceptance-oriented requirements for MVP.

### FR-1 Clinical intake

- Accept free-text symptoms and structured tags  
- Capture age band, comorbidities, pregnancy, allergies  
- Optional Prakriti as soft signal only  
- **Acceptance:** Preset Pinasa vignette can be loaded in one click  

### FR-2 Entity resolution

- Map terms → canonical roga/lakshana/dravya IDs  
- Expand synonyms  
- Apply contextual sense rules when present  
- **Acceptance:** “Santapa” retrieves Jvara-linked yogas  

### FR-3 Candidate generation

- Retrieve yogas/single drugs linked to resolved entities  
- Support property-based entry path (P1)  
- **Acceptance:** Both Punarnavadi and Vyaghryadi appear as candidates for Jvara+Kasa  

### FR-4 Safety filtering

- Hard-flag/exclude unsuitable ingredients and media  
- Show warnings explicitly  
- **Acceptance:** Diabetic + Guda / Asava-Arishta rules fire in tests and UI  

### FR-5 Ranking & discrimination

- Score with primary/secondary indication, profile fit, penalties  
- Expose feature contributions  
- **Acceptance:** Pinasa vignette ranks Vyaghryadi above Punarnavadi without LLM  

### FR-6 Explanation & citation

- Generate explanations only from evidence pack  
- Show reference metadata on every recommendation  
- **Acceptance:** Spot-check shows 0 fabricated refs on golden explanations  

### FR-7 Learning layer

- Synonym tags, A-vs-B teaching card  
- Optional counterfactuals (P1)  

### FR-8 Transparency & responsibility

- Confidence/coverage indicators  
- Persistent decision-support disclaimer  
- Ephemeral vignettes by default (no PII store)  

---

## 8. Non-Functional Requirements

| ID | Requirement | MVP target |
|----|-------------|------------|
| NFR-1 Latency | End-to-end recommend | < 3–5s p95 |
| NFR-2 Citation integrity | Fabricated refs | 0 on eval sample |
| NFR-3 Safety determinism | Coded rules | 100% unit pass |
| NFR-4 Availability | Demo | Single-region OK |
| NFR-5 Privacy | PII | Session-only vignettes |
| NFR-6 Explainability | Rank features | Inspectable in UI/API |
| NFR-7 Extensibility | Add yoga rows | No ranker rewrite |
| NFR-8 Eval repeatability | Golden suite | Runnable in CI |
| NFR-9 Responsible AI | Framing | Non-diagnostic UI copy |
| NFR-10 Cost | LLM usage | Only extract+explain |
| NFR-11 Audit | Recommendation trace | Store feature vector + rule hits (anonymous) |
| NFR-12 Accessibility | Basic a11y | Keyboard navigable core flow |
| NFR-13 Security | Secrets/API | Env-based keys; rate limits |
| NFR-14 Graceful degradation | LLM down | Rank+safety still work; template explanations |

---

## 9. Product Features

### P0 — Must ship

1. Vignette intake + demo presets  
2. Synonym-aware retrieval  
3. Ranked results with scores  
4. Safety/contraindication panel  
5. Citation cards  
6. Comparative “Why A over B”  
7. Property cards when present  
8. Disclaimer + coverage honesty  

### P1 — Strong differentiators

1. Learning mode narrative  
2. Homonym disambiguation demo (*Abhaya*)  
3. Counterfactual ranking  
4. Pharmacological reverse search  

### P2 — Later

1. Multi-turn conversational intake  
2. Full Prakriti assessment  
3. Multilingual UI  
4. Accounts / saved cases  
5. NAMASTE export  

### Explicit kill list (do not build in hackathon)

- Agent swarm orchestration theater  
- Fine-tuned custom LLM from scratch  
- Full OCR pipeline  
- Dose titration engine  
- Consumer wellness quiz product  
- Blockchain provenance  

---

## 10. Knowledge Modeling

Knowledge is the product. The UI is a lens.

### 10.1 Design principles

1. **Canonical IDs over strings** everywhere in computation  
2. **Names are labels**; meanings are senses  
3. **Provenance on edges**, not only nodes  
4. **Null ≠ unknown invented value**  
5. **Primary vs secondary indications are first-class** (enables discrimination)

### 10.2 Core entities

| Entity | Meaning | Key attributes |
|--------|---------|----------------|
| `Concept` | Abstract controlled term | `concept_id`, type, status |
| `Term` | Surface string | language, script, normalized form |
| `Roga` | Disease / clinical condition | concept link, hierarchy parent |
| `Lakshana` | Symptom/sign | concept link |
| `Dravya` | Single drug/herb/mineral | botanical refs optional, properties |
| `Yoga` | Compound formulation | kalpana type, ingredients |
| `Kalpana` | Pharmaceutical form/medium | Kwatha, Asava, Ghrita, … |
| `PropertySet` | Rasa/Guna/Virya/Vipaka/Prabhava | nullable fields |
| `Reference` | Classical citation | text, section, verse/page, excerpt_id |
| `ConstraintRule` | Safety policy | condition × forbidden target × severity |
| `SenseRule` | Contextual meaning | term + context_yoga → dravya_sense |

### 10.3 Relationships

| Relationship | Semantics |
|--------------|-----------|
| `Term` —denotes→ `Concept` | Lexical mapping |
| `Term` —synonym_of→ `Term` | Via shared concept |
| `Yoga` —treats→ `Roga`/`Lakshana` | `weight`: primary/secondary; `source_ref` |
| `Yoga` —contains→ `Dravya` | quantity/part optional |
| `Yoga` —has_form→ `Kalpana` | medium |
| `Yoga`/`Dravya` —has_properties→ `PropertySet` | sparse |
| `Yoga` —cited_in→ `Reference` | mandatory for MVP rows |
| `ConstraintRule` —applies_to→ patient condition × Dravya/Kalpana | safety |
| `SenseRule` —overrides→ default denotation | homonyms |

### 10.4 Hierarchies

**Disease hierarchy (illustrative)**  
`Roga` trees for demo clusters, e.g. *Jvara* family, *Pratishyaya/Pinasa* under respiratory, *Prameha* metabolic — used for inheritance of synonym tags and candidate expansion (controlled, not unbounded).

**Ingredient hierarchy**  
`Dravya` → family/category (e.g., Madhura dravya, fermented substrates) to fire class-level contraindications (jaggery-like sweeteners; Asava–Arishta class).

**Formulation hierarchy**  
`Yoga` instance → `Kalpana` class → route/medium policy.

**Reference hierarchy**  
Work (Charaka Samhita) → Sthana/Chapter → Verse/section → Excerpt span.

### 10.5 Terminology, synonyms, contextual meanings

**Synonym path:** user string → normalize → Term → Concept → expand all Terms for retrieval recall.

**Homonym path:** if SenseRule matches (term + yoga context), bind to contextual Dravya; else default Concept.

**Encoded exemplar:**  
- Default: *Abhaya* → *Terminalia chebula*  
- Context: in *Jatyadi ghrita* → *Vetiveria zizanioides* (per corpus rule)

### 10.6 Knowledge flow at runtime

```
User text
  → extracted candidate strings
  → Term/Concept resolution (+ synonym expansion)
  → Sense disambiguation if context available
  → Graph query: yogas treating concepts (primary/secondary)
  → Join ingredients + kalpana + properties + references
  → Apply ConstraintRules
  → Rank by discrimination features
  → Build Evidence Pack (structured + optional excerpt spans)
  → Explain (templates or LLM bound to pack)
```

### 10.7 Ontology governance

- Every concept change requires `version` bump  
- Human verification flag on clinically sensitive edges  
- Conflicting text indications stored as multiple sourced edges, not overwritten  

---

## 11. Data Strategy

Treat data as the foundation, not an afterthought.

### 11.1 Data sources

| Source | Role | Priority |
|--------|------|----------|
| Hackathon “data section” (formulations, synonyms, refs) | Primary bootstrap | P0 |
| AFI / API (official) | Standardization / cross-check | P0/P1 |
| NAMASTE terminologies | Synonym/morbidity alignment | P1 |
| Open curated sets (CC-licensed formulation JSON, research KGs) | Fill gaps | P1 |
| Permitted classical excerpts | RAG evidence spans | P1 |
| Expert-authored golden vignettes | Eval + demo | P0 |

### 11.2 Acquisition principles

1. Prefer **structured** over scraped prose.  
2. Prefer **licensed/open/official** over gray PDFs.  
3. Store **reference metadata** even when full text cannot be redistributed.  
4. Keep raw → cleaned → canonical layers separate.

### 11.3 Licensing & compliance

- Maintain a `DATA_LICENSE_REGISTER` (source, license, allowed use, redistribution).  
- Do not ship copyrighted full books in a public repo without rights.  
- For demo, prefer short excerpts under fair use / permitted sources + citations.  
- If uncertain: reference pointers only (book + section), no verbatim copyrighted body.

### 11.4 Cleaning & standardization

- Unicode normalize; transliteration standard (IAST preferred for MVP).  
- Deduplicate yogas by canonical Sanskrit name + kalpana.  
- Map aliases into Term table rather than duplicating Yoga rows.  
- Normalize comorbidity dictionary (diabetes → Prameha/Madhumeha tags as configured).  

### 11.5 Validation & human verification

| Gate | Rule |
|------|------|
| Schema validation | Required fields present |
| Citation gate | MVP yoga must have ≥1 reference |
| Indication gate | ≥1 treats-edge |
| Safety authoring | Demo comorbidity rules peer-reviewed |
| Spot-check | Domain reviewer samples 10% of new edges |
| Golden vignettes | Pairwise labels dual-reviewed if possible |

### 11.6 Metadata & lineage

Each record stores: `source`, `source_version`, `extracted_at`, `verified_by`, `verified_at`, `confidence`.

### 11.7 Chunking & embeddings (for textual evidence)

- Chunk classical excerpts by **shloka/section**, not arbitrary 512-token windows when structure exists.  
- Chunk metadata must include `reference_id`, work, locus.  
- Embeddings used for **evidence recall**, not for safety or final ranking authority.  
- Re-embed on corpus version bump; store `embedding_model` + `corpus_version`.

### 11.8 Missing values policy

- Null properties displayed as “Not available in corpus.”  
- Never impute Virya/Vipaka via LLM into the database.  
- Ranker must tolerate sparsity.

### 11.9 Versioning

- `corpus_version` semver for knowledge releases  
- Eval suite pinned to corpus version  
- Ability to diff yoga indication edges between versions  

### 11.10 Data quality bar (MVP)

- 150–400 yogas in vertical clusters with citations  
- Synonym coverage for demo diseases  
- ≥1 homonym SenseRule demo  
- Safety rules for diabetes × sweetener/fermented class  
- Golden vignette pack 25–40 cases  

### 11.11 Data pipeline (logical)

```
Acquire → License check → Raw store → Clean/standardize
  → Entity resolve → Graph load → Validate gates
  → Optional embed excerpts → Publish corpus_version
  → Run golden eval → Accept/reject release
```

---

## 12. AI Strategy

### 12.1 Core principle

> **Structure decides. Rules protect. Retrieval grounds. LLM explains.**

Never invert this order.

### 12.2 Why AI at all?

Without AI/NLP:

- Free-text intake collapses to brittle forms  
- Explanations become rigid templates only  
- Synonym recall across vernacular suffers  

With constrained AI:

- Flexible intake  
- High-quality teaching narratives  
- Semantic evidence packing  

### 12.3 Why RAG?

RAG connects explanations to **retrievable classical evidence** rather than parametric memory. It reduces (not eliminates) hallucination when paired with citation checks.

### 12.4 Why not only RAG?

Because formulation choice under constraints is **not** a nearest-neighbor document problem:

- Overlapping indications need **ranking features**, not chunk similarity  
- Contraindications need **logic**, not cosine distance  
- Homonyms need **sense rules**, not “most similar paragraph”

**Pure RAG failure mode:** fluent paragraph recommending a yoga that violates diabetes medium policy, with a plausible-looking fake verse.

### 12.5 Why Knowledge Graph / structured relational model?

- Explicit yoga–indication–ingredient topology  
- Primary/secondary weights for discrimination  
- Queryability, auditability, incremental curation  
- Deterministic candidate generation  

### 12.6 Why Rule Engine?

Safety and medium unsuitability are **policy**. Policies must be:

- Testable  
- Deterministic  
- Reviewable by domain experts  
- Independent of LLM temperature  

### 12.7 Why Embeddings & Vector Database?

- Soft recall of relevant excerpts/notes for explanation  
- Bridge vernacular paraphrases to tagged concepts (assistive)  
- Not authoritative for final ordering  

**MVP recommendation:** pgvector beside Postgres to minimize ops.

### 12.8 Why Hybrid Search?

Combine:

- **Structured query** (exact concept links) — precision  
- **Lexical** (term variants) — synonym robustness  
- **Vector** (semantic paraphrase) — recall of evidence  

Final candidate set is **intersected/prioritized with structured links first**.

### 12.9 Why Prompt Engineering & Structured Outputs?

- Force vignette → JSON clinical frame  
- Force explanation → JSON with `claims[]` each bearing `ref_ids[]`  
- Enable automatic refusal when `ref_ids` empty  

### 12.10 Why Citation Grounding?

Trust is the product. In classical medicine education, an uncited claim is noise; a fabricated citation is harm.

**Mechanism:** Evidence Pack only → generator → validate ref IDs exist → render.

### 12.11 Why LLM?

Best available tool for:

1. Unstructured clinical language understanding  
2. Comparative pedagogical explanation  

### 12.12 Why not fine-tuning (for now)?

| Fine-tuning promise | Reality for this MVP |
|---------------------|----------------------|
| Domain style | Achievable via prompts + glossary |
| Memorize shastras | Dangerous; encourages parametric citation |
| Rank yogas | Worse than explicit features; hard to audit |
| Cost/time | Poor hackathon ROI |

**Future:** consider fine-tuning only for entity extraction quality on labeled Ayurvedic notes — never as sole recommender.

### 12.13 Decision rights: what AI may / may not decide

| Decision | Owner |
|----------|-------|
| Final ranked order | Deterministic ranker |
| Safety exclude/flag | Rule engine |
| Synonym expansion | Ontology |
| Homonym sense | Sense rules (+ ontology) |
| Invent new yoga | **Never** |
| Invent reference | **Never** |
| Fill missing Virya into DB | **Never** |
| Draft explanation text | LLM/templates allowed |
| Diagnose disease as medical authority | **Never** (may suggest candidate concepts as assistance only) |

### 12.14 What remains deterministic

- ConstraintRule application  
- Score computation  
- Citation ID validation  
- Corpus version selection  
- Eval harness metrics  

### 12.15 Pipeline (logical)

```
User vignette (NL + structured)
        │
        ▼
 NL understanding → entities (schema-constrained)
        │
        ▼
 Entity linker + sense disambiguator
        │
        ▼
 Candidate retrieval (structured first; hybrid assist)
        │
        ▼
 Safety rule engine
        │
        ▼
 Ranker / discriminator (explainable features)
        │
        ▼
 Evidence pack builder
        │
        ▼
 Explanation (LLM or template) citation-bound
```

### 12.16 Evaluation strategy

**Golden Vignette Pack (25–40):**

- Pairwise A ≻ B labels  
- Safety must-fire cases  
- Synonym retrieval cases  
- Homonym sense cases  

**Metrics**

- Pairwise ranking accuracy (primary)  
- Recall@k of acceptable yogas  
- Contraindication precision/recall  
- Citation validity rate  
- Reference hallucination rate (~0)  

**Baselines to beat**

1. Keyword overlap ranker  
2. Embedding-only similarity ranker  
3. LLM-only recommendation (ablation; expect safety failures)

**Ablation story for judges:** removing secondary-indication weights collapses Punarnavadi/Vyaghryadi discrimination.

### 12.17 Prompting policy (summary)

- Low temperature for clinical explanation  
- Evidence-only context  
- Explicit “insufficient evidence” path  
- No browsing of parametric classical memory as authority  

---

## 13. Agent Architecture Decision

### 13.1 Candidate idea

Multiple specialized agents: Intake, Clinical Understanding, Terminology, Retrieval, Safety, Recommendation, Explanation, Learning.

### 13.2 Evaluation

| Claim for agents | Counter |
|------------------|---------|
| Clear separation of concerns | Achievable with **modules/services** without agent runtime |
| Parallelism | Our pipeline is mostly sequential by trust needs (safety before explain) |
| Tool-using autonomy | Autonomy increases nondeterminism in healthcare |
| Judge wow | Swarms often look like complexity theater |

### 13.3 Decision

**Reject multi-agent orchestration as the core architecture for MVP.**

Adopt a **deterministic modular pipeline** with optional LLM calls at two sealed stages (understand, explain). Internally we may *name* stages like agents for communication, but they are **functions with contracts**, not autonomous agents that negotiate.

### 13.4 Why this is better here

1. Safety must be deterministic — not emergent from agent debate.  
2. Ranking must be reproducible for eval and teaching.  
3. Debugging citation failures needs a linear trace.  
4. Hackathon reliability > agent choreography.  
5. Production path maps cleanly to service boundaries later.

### 13.5 When to reconsider agents (Phase 2+)

- Literature curation copilots for data ops (human-in-the-loop)  
- Faculty content-authoring assistants  
- Multi-corpus conflict resolution workflows with mandatory human approval  

Not for runtime prescription-like ranking.

### 13.6 Module map (agent-named, pipeline-real)

| Module | Responsibility | Autonomy |
|--------|----------------|----------|
| Intake | Validate/normalize input | None |
| Understand | NL → schema | LLM optional |
| Terminology | Link + synonym + sense | Deterministic |
| Retrieve | Candidates + evidence spans | Deterministic (+ vector assist) |
| Safety | ConstraintRules | Deterministic |
| Recommend | Ranker | Deterministic |
| Explain | Narrative from evidence | LLM optional |
| Learn | Teaching card assembly | Deterministic + optional LLM polish |

---

## 14. System Architecture

### 14.1 Logical architecture

```
┌──────────────────────────────────────────────────────────┐
│ Presentation                                             │
│  Workbench: Intake | Results | Compare | Learn | Demo   │
└─────────────────────────────┬────────────────────────────┘
                              │ API
┌─────────────────────────────▼────────────────────────────┐
│ Application pipeline services                            │
│  Intake · Understand · Resolve · Retrieve · Safety      │
│  · Rank · Evidence · Explain                             │
└───────┬───────────────┬───────────────┬──────────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ Postgres     │ │ pgvector     │ │ LLM gateway          │
│ (system of   │ │ (evidence    │ │ (extract + explain)  │
│  record KG)  │ │  recall)     │ │                      │
└───────┬──────┘ └──────────────┘ └──────────────────────┘
        │
        ▼
┌──────────────┐
│ Rule engine  │  YAML/DB ConstraintRules
└──────────────┘
```

### 14.2 Trust boundaries

1. **Browser** untrusted input  
2. **API** validates schema  
3. **Rank/Safety** no LLM authority  
4. **LLM gateway** cannot write to corpus tables  
5. **Explain** read-only evidence pack  

### 14.3 Ranking feature sketch

```
score(yoga) =
  w1 * primary_indication_match
+ w2 * secondary_indication_match
+ w3 * property_fit
+ w4 * prakriti_soft_fit          # low weight / optional
- w5 * contraindication_penalty  # or hard gate
- w6 * medium_unsuitability_penalty
+ w7 * citation_completeness_bonus
```

Punarnavadi vs Vyaghryadi must fall out of **secondary indication weights**, not prompt cleverness.

### 14.4 Failure modes & degradations

| Failure | Behavior |
|---------|----------|
| LLM timeout | Return rank+safety+template explanation |
| Unresolved entities | Ask clarifying chips; show partial matches |
| Empty candidates | Honest empty state + suggest broadening |
| Conflicting sources | Show both refs; lower confidence |
| Rule vs rank conflict | Safety wins always |

### 14.5 Sequence (happy path)

1. Client POST `/recommend` with vignette  
2. Understand → ClinicalFrame JSON  
3. Resolve concepts  
4. Retrieve candidates + refs  
5. Apply safety  
6. Rank  
7. Build evidence pack  
8. Explain (optional)  
9. Return `RecommendationResponse` with trace_id  

---

## 15. Technical Decision Records

### TDR-001: Product metaphor = Discrimination Workbench (not Chat)

- **Decision:** Clinical workbench with Compare as hero  
- **Alternatives:** Chat-first assistant; encyclopedia browser  
- **Advantages:** Judge clarity; forces discrimination UX  
- **Disadvantages:** Less “magical” than chat  
- **Why:** Problem is ranking under context  
- **Replace later:** Add conversational intake as a skin, not the core  

### TDR-002: Hybrid structured+rules+RAG-explain (not pure RAG)

- **Decision:** Hybrid pipeline  
- **Alternatives:** Pure RAG; pure LLM; pure KG browser  
- **Advantages:** Safety + discrimination + explanations  
- **Disadvantages:** More engineering than a single LangChain demo  
- **Why:** Matches clinical risk profile  
- **Replace later:** Improve ranker ML; keep rules  

### TDR-003: Postgres as system of record (graph later if needed)

- **Decision:** PostgreSQL + relational ontology  
- **Alternatives:** Neo4j-first; Mongo-only  
- **Advantages:** Joins, transactions, pgvector adjacency, simple ops  
- **Disadvantages:** Multi-hop graph queries more verbose  
- **Why:** Speed + reliability for MVP  
- **Replace later:** Add graph DB if traversal complexity explodes  

### TDR-004: Deterministic safety rules in DB/YAML

- **Decision:** Explicit ConstraintRules  
- **Alternatives:** LLM safety prompts; ML classifiers  
- **Advantages:** Testable, reviewable  
- **Disadvantages:** Manual authoring  
- **Why:** Non-negotiable in healthcare-adjacent demos  
- **Replace later:** Assisted rule mining with human approval  

### TDR-005: LLM for extract + explain only

- **Decision:** Sealed LLM roles  
- **Alternatives:** LLM recommender; multi-agent debate  
- **Advantages:** Controllable trust story  
- **Disadvantages:** Explanations depend on evidence quality  
- **Why:** Prevent authoritative hallucination  
- **Replace later:** Better extractors; still no LLM final rank  

### TDR-006: No fine-tuning in hackathon

- **Decision:** Prompted frontier LLM (+ templates fallback)  
- **Alternatives:** LoRA fine-tune on classical text  
- **Advantages:** Time, auditability  
- **Disadvantages:** May miss domain nuance in extraction  
- **Why:** ROI + safety  
- **Replace later:** Fine-tune extractor only with labeled data  

### TDR-007: No autonomous multi-agent runtime

- **Decision:** Modular pipeline  
- **Alternatives:** Agent swarm  
- **Advantages:** Determinism, debuggability  
- **Disadvantages:** Less trendy  
- **Why:** Healthcare + eval reproducibility  
- **Replace later:** Agents for offline curation tools  

### TDR-008: Vertical corpus over 150-text ingest

- **Decision:** Cluster excellence (Jvara–Kasa–Pinasa + safety cluster + optional Jatyadi)  
- **Alternatives:** Breadth-first scrape  
- **Advantages:** Finish quality; demo punch  
- **Disadvantages:** “But what about all texts?” objection  
- **Why:** Depth proves thesis  
- **Replace later:** Text-by-text expansion factory  

### TDR-009: Soft Prakriti only / optional

- **Decision:** Defer hard Prakriti engine  
- **Alternatives:** Full questionnaire diagnosis  
- **Advantages:** Avoid false precision  
- **Disadvantages:** Less “personalized” marketing  
- **Why:** Reliability  
- **Replace later:** Validated instrument integration  

### TDR-010: Python API + modern web UI preferred

- **Decision:** FastAPI (or equiv) + React/Next UI; finalize by team skills  
- **Alternatives:** Next full-stack only; Django monolith  
- **Advantages:** Best NLP ecosystem on backend  
- **Disadvantages:** Two languages possible  
- **Why:** AI velocity  
- **Replace later:** Consolidate if team standardizes  

### TDR-011: Ephemeral vignettes; minimal auth for demo

- **Decision:** No PII persistence in MVP  
- **Alternatives:** Full accounts/EHR  
- **Advantages:** Privacy, speed  
- **Disadvantages:** No longitudinal cases  
- **Why:** Responsible MVP  
- **Replace later:** Secured casebooks for colleges  

---

## 16. Recommended Technologies

> Roles are fixed by TDRs; concrete vendors can change.

| Layer | Recommendation | Mandatory? |
|-------|----------------|------------|
| UI | React or Next.js | One web UI mandatory |
| API | FastAPI (Python) preferred | Backend mandatory |
| DB | PostgreSQL + JSONB | Mandatory |
| Vectors | pgvector | Recommended |
| Rules | DB/YAML rules evaluated in code | Mandatory |
| LLM | Hosted frontier model via API | Recommended (with template fallback) |
| Embeddings | Multilingual model (e.g., bge-m3 class) or provider embeddings | Recommended |
| Deploy | Docker + single cloud target; cached demo path | Recommended |
| Eval | Pytest/CI golden suite | Recommended |
| Observability | Structured logs + trace_id + prompt traces | Recommended |

**Explicitly not needed for MVP:** Kubernetes, streaming agent meshes, custom trained foundation models, OCR farms, blockchain.

### Security & responsible use

- Env-based secrets; rate-limit LLM routes  
- Redact prompts in shared logs if they contain sensitive text  
- Prominent medical disclaimer  
- Refuse “diagnose me / prescribe autonomously” framing  

---

## 17. User Experience Design

### 17.1 Design principles

1. **Workbench not chat theater**  
2. **Compare is the hero**  
3. **Safety visible before persuasion**  
4. **Citations adjacent to claims**  
5. **Honesty about missing data**  
6. **Teaching moments without clutter**  

### 17.2 Information architecture

```
App Shell
├── Demo Presets (judge/faculty)
├── New Case (Intake)
├── Results
│   ├── Ranked list
│   ├── Safety panel
│   └── Coverage/confidence
├── Compare (A vs B)
├── Formulation Detail
│   ├── Properties
│   ├── Ingredients
│   ├── Indications (primary/secondary)
│   └── References
└── Learn
    ├── Synonym map
    └── Teaching point
```

### 17.3 Screen hierarchy (MVP)

1. **Home/Demo** — presets + short value prop + disclaimer  
2. **Intake** — symptoms, profile constraints  
3. **Results** — ranked yogas + safety summary  
4. **Compare** — side-by-side discrimination  
5. **Detail** — properties, ingredients, refs  
6. **Learn** — synonyms + teaching card  

### 17.4 Decision flow (user-perceived)

```
Enter vignette → See interpreted terms
  → Review safety gates
  → Inspect ranked options
  → Compare top contenders
  → Read citations
  → (Optional) Learn why ranking flips with context
  → Human makes final clinical/educational judgment
```

### 17.5 Clinical workflow alignment

VedyaAI assists **after** provisional framing, not instead of examination. Copy and UX should imply: “support selection among classical options,” not “diagnose disease.”

### 17.6 Navigation

- Persistent case summary chip (symptoms + comorbidities)  
- Always-on disclaimer footer  
- One-click reset to presets for demos  

### 17.7 Content hierarchy on Results

1. Safety alerts (if any)  
2. Top recommendation + score  
3. Why this over #2 (teaser linking to Compare)  
4. Full ranked list  
5. Learning/synonym drawer  

---

## 18. Innovation Analysis

### 18.1 Technical innovation

Explainable **constraint-aware ranking** over a classical yoga graph, with citation-validated generation — not embedding search alone.

### 18.2 AI innovation

**Sealed-role LLM usage** inside a healthcare-adjacent loop: AI may parse and teach, never author unsafe clinical authority.

### 18.3 Healthcare innovation

Operationalizes a real Ayurvedic clinical skill: **yoga vivechana** (discriminative selection among overlapping formulations), including medium/ingredient unsuitability.

### 18.4 UX innovation

**Compare-first clinical learning workbench** that makes “why A over B” the primary interface, not a chat transcript.

### 18.5 Educational innovation

Every recommendation emits a **teaching artifact** (synonym map + discrimination point), turning CDSS output into curriculum.

### 18.6 Fundamentally different from generic AI products

| Generic AI product | VedyaAI |
|--------------------|---------|
| Answers from model memory | Answers from versioned corpus + rules |
| Confidence theater | Coverage honesty + citation gate |
| Chat as product | Discrimination workbench |
| One-shot advice | Comparative reasoning object |

---

## 19. Risks, Assumptions & Trade-offs

### 19.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hallucinated citations | Medium | Critical | Evidence pack + ID validation |
| Unsafe recommendation | Medium | Critical | Hard rules before rank presentation |
| Thin corpus looks weak | Medium | High | Vertical excellence + killer demo |
| Licensing conflict | Medium | High | License register; refs without full text |
| Overclaim medical device | Medium | High | Educational/CDSS framing |
| Scope creep to 150 texts | High | High | TDR-008 enforcement |
| Prakriti false precision | Medium | Medium | Soft/optional only |
| Stage network/LLM failure | Medium | High | Cached golden demo path |
| Expert disagreement on labels | Medium | Medium | Pairwise labels + confidence notes |
| Students over-trust AI | Medium | High | Pedagogy + disclaimer + show uncertainty |

### 19.2 Assumptions

1. Usable structured data exists (hackathon or open substitutes).  
2. English + transliterated Sanskrit sufficient for MVP demo.  
3. Judges reward grounded discrimination over breadth claims.  
4. Vertical subset is acceptable if quality is high.  
5. At least one domain reviewer can validate vignettes.  
6. “Suggest” = decision support, not autonomous prescription.  
7. Template explanations are acceptable fallback if LLM blocked.

### 19.3 Trade-offs

| We choose | We reject (for now) | Why |
|-----------|---------------------|-----|
| Hybrid pipeline | Pure RAG chatbot | Safety + discrimination |
| Vertical clusters | 150-text ingest | Finish quality |
| Soft Prakriti | Hard Prakriti engine | Reliability |
| LLM extract/explain | LLM prescribe | Trust |
| Relational ontology first | Neo4j-first | Speed |
| Workbench + Compare | Chat-only | Memorability |
| Modular pipeline | Agent swarm | Determinism |
| Comorbidity depth | Full lifestyle OS | Focus |

---

## 20. Demo & Hackathon Strategy

Winning is product **and** presentation.

### 20.1 Storytelling arc (3 acts)

1. **Conflict:** Two decoctions, same fever+cough labels — which one?  
2. **Insight:** Discrimination under secondary context + safety  
3. **Proof:** Live system + architecture principle one-liner  

### 20.2 Live demo flow (6–7 minutes)

| Time | Beat | Action |
|------|------|--------|
| 0:00–0:40 | Hook | Ask judges to vote Vyaghryadi vs Punarnavadi for Pinasa-URTI |
| 0:40–1:40 | Problem | Show failure of undifferentiated “top 10 for Jvara” |
| 1:40–3:10 | WOW #1 | Run Pinasa vignette → Vyaghryadi wins with secondary tags + Compare |
| 3:10–4:00 | WOW #2 | Flip to inflammatory vignette → Punarnavadi rises |
| 4:00–4:50 | WOW #3 | Diabetic case → jaggery/fermented medium hard flags |
| 4:50–5:30 | Trust | Citation cards + “LLM didn’t pick; ranker did” |
| 5:30–6:10 | Ambiguity (if time) | *Abhaya* sense in Jatyadi |
| 6:10–7:00 | Close | Principle slide + production path |

### 20.3 WOW moments (must land)

1. Ranking flip between two clinically plausible yogas  
2. Safety gate visibly blocking unsuitable medium/ingredient  
3. Side-by-side Compare explanation with classical refs  
4. Ablation one-liner: “Without secondary weights, they tie”  

### 20.4 Judge experience design

- Large fonts; minimal clutter  
- Preset buttons labeled in plain language  
- Never type long text live unless necessary  
- Show score features briefly (trust)  
- End with memorable sentence judges can repeat  

### 20.5 Fallback demo

- Precomputed JSON outputs for all golden cases  
- Local template explanations if LLM key fails  
- Screen recording backup  
- Printed one-pager architecture + vignette results  

### 20.6 Demo success metrics

- ≥1 audible “oh” / note-taking at ranking flip  
- Judge restates discrimination thesis  
- No live citation miss  
- Safety case fires  

### 20.7 Expected questions & prepared answers

| Question | Answer |
|----------|--------|
| “Isn’t this just RAG?” | RAG explains; structured ranker + rules decide |
| “Why so few texts?” | Vertical proof > shallow breadth; factory next |
| “Can it diagnose?” | No — decision support for formulation selection |
| “What if experts disagree?” | We eval pairwise preferences; show confidence/coverage |
| “Why trust citations?” | Generator may only use retrieved ref IDs; validated |
| “Where is Prakriti?” | Soft optional; hard Prakriti deferred to avoid false precision |
| “How is this better than ChatGPT?” | Deterministic safety + discrimination features + citation firewall |
| “Regulatory?” | Educational/CDSS framing; clinician-in-the-loop |

### 20.8 Expected objections & responses

| Objection | Response |
|-----------|----------|
| “UI is simple” | Intentional clinical workbench; complexity is in rank/safety |
| “Dataset small” | Quality-labeled graph beats uncited PDF dump |
| “Not enough agents/LLM” | Determinism is the feature in healthcare AI |
| “Ayurveda is holistic; you oversimplify” | We encode discrimination & constraints first; expand carefully |

---

## 21. Development Roadmap & Milestones

### 21.1 Hackathon build phases

**Phase 0 — Align (0.5–1 day)**  
Dataset inventory, license register, freeze vignettes, approve plan.

**Phase 1 — Data foundation (1–2 days)**  
Schema, synonyms, safety rules, secondary weights, references.

**Phase 2 — Core intelligence (2–3 days)**  
Resolve → retrieve → safety → rank + golden eval harness.  
**Gate:** Punarnavadi/Vyaghryadi correct **without LLM**.

**Phase 3 — Explanation layer (1–2 days)**  
Evidence pack, citation-bound explain, Compare narratives.

**Phase 4 — UX (parallel, 1–2 days)**  
Intake, results, compare, learn, presets, disclaimer.

**Phase 5 — Harden & demo (1 day)**  
Latency, fallbacks, demo script rehearsal, objection drill.

### 21.2 Milestones

| Milestone | Exit criteria |
|-----------|---------------|
| M1 Plan approved | V2 dual-architect sign-off; scope frozen |
| M2 Data ready | Demo clusters loaded; licenses logged |
| M3 Ranker works | Pinasa vignette correct without LLM |
| M4 Safe by default | Safety golden cases 100% |
| M5 Explainable | 0 fabricated refs on sample |
| M6 Demo-ready | UI + presets + fallback |
| M7 Review gate | Domain + architect spot-check |

### 21.3 Engineering critical path

`Data model → Safety rules → Ranker eval → Explain → UI polish → Demo fallback`

UI must not block ranker. LLM must not block ranker.

---

## 22. Startup Vision Beyond the Hackathon

### 22.1 Wedge → expand

1. **Wedge:** College teaching + junior clinical assist for respiratory/fever discrimination clusters  
2. **Expand corpus:** Text-by-text with human verification workflows  
3. **Expand users:** Faculty CMS, institutional licenses  
4. **Expand interoperability:** NAMASTE / terminology services  
5. **Expand care settings:** Teaching hospitals OPDs as CDSS assist  

### 22.2 Business opportunities

| Motion | Description |
|--------|-------------|
| Education SaaS | College seats + faculty case library |
| Clinician Pro | Advanced safety packs + saved cases |
| API platform | Formulation discrimination API for health-tech |
| Research license | Anonymized reasoning traces for academia |
| Gov / AYUSH programs | Training standardization tooling (long-cycle) |

### 22.3 Educational use

- Viva simulation  
- Classroom compare sessions  
- Curriculum-aligned synonym mastery  

### 22.4 Hospital adoption path

- Start in teaching hospitals as **assistive reference**  
- Require clinician acknowledgment UX  
- Integrate later with local EMR only after validation studies  

### 22.5 Research platform

- Versioned corpus diffs  
- Inter-rater disagreement datasets  
- Ablation benchmarks for classical NLP  

### 22.6 Government / public-good angle

- Support standardized terminology literacy  
- Complement NAMASTE adoption with practical decision tooling  
- Avoid claiming replacement of classical education  

### 22.7 Open API & developer ecosystem

- Public `recommend` / `compare` / `terminology` endpoints (rate-limited)  
- Partner apps embed discrimination widget  
- Plugin for college LMS  

### 22.8 Scalability

- Corpus versioning + horizontal read replicas  
- Cache evidence packs for popular vignettes  
- Separate data curation workers from runtime API  

### 22.9 Monetization possibilities (ethical)

- Institutional subscriptions (primary)  
- Pro tier for clinics  
- API usage for B2B  
- Not: advertising inside clinical recommendations  

### 22.10 Long-term roadmap (post-hackathon)

| Phase | Outcome |
|-------|---------|
| 0–3 mo | Harden MVP clusters; 100+ golden vignettes; pilot with 1 college |
| 3–9 mo | Faculty CMS; NAMASTE mapping pilot; multilingual intake experiment |
| 9–18 mo | Multi-hospital teaching pilot; external clinical advisory board |
| 18+ mo | Validated CDSS positioning (jurisdiction-dependent); API ecosystem |

---

## 23. Team Operating Model

| Role | Owns | Critical deliverable |
|------|------|----------------------|
| Domain / data lead | Ontology, synonyms, safety, vignettes | Golden set quality |
| Backend / AI lead | Pipeline, ranker, eval harness | M3/M4 gates |
| Frontend lead | Workbench UX, presets, Compare | Demo clarity |
| Architect (rotating) | Scope, TDRs, citation policy | Prevent RAG-only drift |
| Pitch lead | Story, objections, timing | Judge memorability |

**Operating rule:** No P0 feature unless it improves **discrimination, safety, citation, or learning**.

---

## 24. Success Metrics

### Product

- Time-to-shortlist < 60s on covered clusters  
- Users can state A-vs-B reason after one Compare view  

### Technical

- Pairwise accuracy ≥ 80% (stretch ≥ 90% on demo cluster)  
- Contraindication catch rate = 100% on coded rules  
- Citation hallucination = 0 on sampled explanations  
- Ranker works with LLM disabled  

### Hackathon

- Judges restate differentiator  
- All three WOW moments land  
- Fallback never needed — or works invisibly  

### Venture signals (later)

- Organic faculty adoption  
- Repeat weekly usage in a pilot cohort  
- Willingness to pay institutional pilot fee  

---

## 25. Open Questions

1. Exact hackathon dataset fields, formats, licenses?  
2. Team stack strength: Python-first vs TS-first?  
3. LLM provider / offline constraints / budget?  
4. Citation granularity available (verse vs chapter)?  
5. Who is the clinical reviewer for golden vignettes?  
6. Claim language: “CDSS” vs “educational assistant”?  
7. Formulations-first vs equal single-drug priority?  
8. Include soft Prakriti field in MVP UI or hide?  
9. Presentation-day network guarantees?  
10. Public open-source repo implications for data shipping?  
11. Will organizers score domain fidelity via Ayurveda experts?  
12. Is branded demo dataset permitted if hackathon data is thin?

---

## 26. Final Architecture Audit

### Simulated critique — Principal Engineer (FAANG / frontier AI lab)

| Critique | V2 response / fix |
|----------|-------------------|
| “Where are contracts and invariants?” | Added trust boundaries, module contracts, safety-wins invariant |
| “Agents are trendy — why avoid?” | Explicit TDR-007 with rationale |
| “Eval is hand-wavy” | Baselines + ablations + pairwise primary metric |
| “Data story was weak” | Full data lifecycle + license register requirement |
| “LLM still spooky in healthcare” | Decision rights table; LLM cannot write corpus or final rank |

### Simulated critique — Healthcare AI startup founder

| Critique | V2 response / fix |
|----------|-------------------|
| “Who pays?” | Education SaaS wedge + institutional motion |
| “What’s the wedge?” | Teaching hospitals/colleges + junior assist |
| “Regulatory naïveté” | Non-goals + claim-language open question + clinician-in-loop |
| “Moat?” | Ontology + rules + golden eval + Compare UX habit |

### Simulated critique — Hackathon judge

| Critique | V2 response / fix |
|----------|-------------------|
| “Show me wow” | Ranking flip + safety + Compare scripted |
| “Looks like ChatGPT wrapper” | Ranker-without-LLM gate M3 |
| “Too much architecture cosplay” | Kill list; vertical scope |

### Simulated critique — Domain expert

| Critique | V2 response / fix |
|----------|-------------------|
| “Oversimplifies Ayurveda” | Explicit limits; negative knowledge; provenance conflicts |
| “Prakriti missing” | Soft/optional with false-precision rationale |
| “Citations must be real” | Citation firewall + license-aware excerpts |

### Residual weaknesses (accepted for now)

1. No large publicly validated outcome dataset — accepted; pairwise vignette eval is interim science.  
2. Multilingual depth deferred — accepted for MVP.  
3. Full classical epistemology (nidana panchaka end-to-end) not automated — accepted; formulation discrimination is the wedge.  
4. Exact market sizing TAM/SAM/SOM not quantified — accepted until pilot interviews; directional GTM present.

### Audit conclusion

V2 is materially stronger than V1: market map, ontology, data ops, AI decision rights, anti-swarm rationale, UX IA, TDRs, demo psychology, and venture path are now present. The core thesis is unchanged and sharper.

**Go / No-Go for implementation:** Conditional **Go** after open questions 1–5 and 9 are answered by the team.

---

## 27. Immediate Next Steps (after V2 approval)

1. Answer Open Questions (dataset, stack, LLM, reviewer, network).  
2. Create `DATA_LICENSE_REGISTER` and inventory sources.  
3. Freeze golden vignettes (must include Punarnavadi vs Vyaghryadi).  
4. Implement schema + safety + ranker **before** LLM explanation.  
5. Hit M3 gate (ranker correct without LLM).  
6. Only then explain + UI polish + demo fallback.  
7. Mid-build re-audit against §26 critiques.

---

## 28. Document Control

| Field | Value |
|-------|-------|
| Product | VedyaAI |
| Artifact | `plan.md` |
| Version | **2.0** |
| Supersedes | 1.0 |
| Phase | Planning / pre-implementation |
| Implementation status | **Blocked until plan approval** |
| Reviewers | Team + secondary AI architect (ChatGPT) + domain spot-check |

### Revision history

| Version | Date | Summary |
|---------|------|---------|
| 1.0 | 2026-07-18 | Initial architecture & product plan |
| 2.0 | 2026-07-18 | Formal self-review; market, ontology, data lifecycle, AI decision rights, agent decision, UX IA, TDRs, demo psychology, startup vision, final audit |

---

*End of plan V2. No implementation should begin until this document is reviewed and explicitly approved.*
