# VedyaAI — Feature Suggestions & ElevenLabs Voice Plan

> Product backlog + voice strategy. Prioritize features that deepen **discrimination, trust, teaching, and accessibility** — not chat theater.

---

## A. Four features to implement next (recommended)

### 1. Locale-aware clinical explanations (EN / HI / GU)
**Why:** UI chrome is translated; ranking explanations and safety messages are still mostly English.  
**What:** Pass `locale` into `explainer.py` + safety message catalog; return `explanation.summary` in the active language. Keep classical Sanskrit names as-is.  
**Effort:** M · **Impact:** High for Hindi/Gujarati learners.

### 2. Voice vignette intake + spoken “why A over B” (ElevenLabs)
**Why:** Students and OPD juniors often think aloud; voice reduces typing friction and improves classroom demos.  
**What:** Mic → STT → existing `/recommend`; then TTS of top pick + compare teaser.  
**Effort:** M–L · **Impact:** High demo + accessibility.  
**Detail:** See section C below.

### 3. Counterfactual ranking panel
**Why:** Pedagogy — “what if this patient were diabetic?”  
**What:** One-click toggle comorbidities and re-run ranker; show score delta and safety flips.  
**Effort:** S–M · **Impact:** Strong teaching differentiator (already P1 in plan).

### 4. Faculty case library + export
**Why:** Beachhead = colleges. Faculty need assignable, reproducible cases.  
**What:** Save golden vignettes, share link, export citation pack PDF/Markdown.  
**Effort:** M · **Impact:** Adoption / monetization wedge.

---

## B. Additional strong candidates (backlog)

| Idea | Why it matters |
|------|----------------|
| Rate-limit auth + login lockout | Security basics |
| httpOnly cookie JWT | Safer than localStorage |
| Gujarati/Hindi surface forms in `terms` | Better retrieval for vernacular input |
| Homonym chip UX everywhere Abhaya-like cases appear | Trust + learning |
| Offline template-only mode badge | Honest when LLM is down |
| NAMASTE terminology mapping | Interop with AYUSH standards |
| Eval dashboard in UI (M3/M4/M5 pass/fail) | Credibility for judges |

---

## C. ElevenLabs — basic use cases vs VedyaAI fit

Research snapshot (ElevenLabs product surface): TTS API, STT (Scribe), Conversational Agents, multilingual voices, healthcare-oriented voice agent patterns (intake, education narration, documentation assist). Always treat clinical voice as **assistive / educational**, with disclaimer — not autonomous prescribing.

### Basic / foundational ElevenLabs use cases (any product)

1. **Text-to-Speech (TTS)** — read UI text, explanations, lessons aloud  
2. **Speech-to-Text (STT / Scribe)** — turn spoken input into text for forms or search  
3. **Multilingual narration** — same script in EN/HI/GU (and more)  
4. **Accessibility** — support low-vision / low-literacy users via audio  
5. **Conversational voice agent** — real-time turn-taking over mic/phone  
6. **Course / training narration** — scale educational audio without studio recording  
7. **Keyterm-boosted medical transcription** — better accuracy on drug/disease names  

### Best fits for VedyaAI (prioritized)

| Priority | Use case | How it plugs into current stack |
|----------|----------|----------------------------------|
| **P0** | Speak ranking explanation | TTS on `explanation.summary` + compare winner reason |
| **P0** | Voice symptom intake | STT → `free_text` → existing `/recommend` pipeline |
| **P1** | Multilingual voice | Locale toggle drives TTS language / voice ID |
| **P1** | Classroom “read this case” | Preset vignette narrated for faculty projector mode |
| **P2** | Conversational follow-up agent | Voice loop around existing conversation_id follow-ups |
| **P2** | Ayurvedic keyterm STT | Scribe keyterms: Jvara, Kashaya, Punarnavadi, … |
| **Later** | Phone / WhatsApp agent | Only after HIPAA/privacy review; educational framing |

### Explicitly weaker / avoid early

- Autonomous “prescribe over voice” agents  
- Replacing the deterministic ranker with a voice LLM  
- Storing raw clinical audio without consent + retention policy  

### Suggested MVP voice architecture

```
Mic → ElevenLabs STT (Scribe realtime or batch)
    → POST /recommend (unchanged discrimination engine)
    → Evidence + explanation JSON
    → ElevenLabs TTS (Flash/Turbo for low latency)
    → Play audio + show same Results UI
```

**Models (practical):**  
- Interactive TTS: Flash v2.5 / Turbo v2.5 (low latency)  
- Long teaching narration: Multilingual v2 / expressive v3  
- STT: Scribe v2 (+ keyterm prompting for Ayurvedic terms)

**Safety rule:** Voice never bypasses `SafetyEngine` or citation firewall.

---

## D. Suggested 2-sprint sequence

**Sprint 1**  
- Finish i18n for remaining clinical strings (explanations)  
- ElevenLabs TTS “Listen” on top recommendation  
- Counterfactual diabetes toggle  

**Sprint 2**  
- Voice intake (STT)  
- Faculty shareable case links  
- Auth hardening (rate limit + cookies)

---

## E. Success metrics for new features

- Voice intake → successful recommend in &lt; 8s p95  
- TTS used on ≥ 30% of demo sessions  
- HI/GU users can complete login → rank → follow-up without English-only blockers  
- Counterfactual demo produces audible “oh” in pitch (safety flip visible)
