"""
VedyaAI RAG — retrieval-augmented answers over the classical corpus.

Own-data pipeline (no external LLM required):
1. Query expansion  — user words → canonical concepts via the synonym table
                      (Jvara ↔ Santapa ↔ fever), so vernacular questions hit
                      Sanskrit verses and vice versa.
2. Retrieval        — Postgres full-text search (GIN/tsvector) over 16k+
                      classical verse excerpts, ranked by ts_rank; plus
                      formulation lookup through indication links.
3. Grounded compose — answer is assembled ONLY from retrieved passages and
                      structured corpus rows. Every claim carries a citation.
                      If the corpus has nothing, we say so — never invent.
4. Optional LLM     — when an OpenAI key is configured the same evidence pack
                      is narrated more fluently, restricted to retrieved refs.
"""
from __future__ import annotations

import re
from typing import Any, Optional

STOPWORDS = {
    "what", "is", "are", "the", "a", "an", "of", "for", "in", "on", "to",
    "how", "do", "does", "can", "i", "we", "you", "my", "me", "and", "or",
    "which", "who", "whom", "why", "when", "where", "with", "about", "tell",
    "please", "give", "explain", "describe", "use", "used", "uses", "there",
    "should", "would", "could", "be", "it", "its", "this", "that", "from",
    "treatment", "treat", "cure", "remedy", "medicine", "drug", "best",
}

# words like "treatment" are intent markers, not retrieval content on their own —
# but they DO belong in the FTS query as boosters.
INTENT_BOOSTERS = {"treatment", "treat", "cure", "remedy", "medicine", "management", "therapy"}


def _tokenize(question: str) -> list[str]:
    words = re.findall(r"[A-Za-z\u0900-\u097F\u0A80-\u0AFF]+", question)
    return [w for w in words if len(w) > 1]


def expand_query(db, question: str) -> dict[str, Any]:
    """Map question words to canonical concepts + synonyms via terms table."""
    tokens = _tokenize(question)
    content_tokens = [t for t in tokens if t.lower() not in STOPWORDS]
    boosters = [t for t in tokens if t.lower() in INTENT_BOOSTERS]

    matched_concepts: list[dict[str, Any]] = []
    expansion_terms: set[str] = set()
    seen_concepts: set[str] = set()

    cur = db.cursor()
    # Try single tokens and adjacent bigrams (e.g. "common cold")
    candidates = list(content_tokens)
    for i in range(len(content_tokens) - 1):
        candidates.append(f"{content_tokens[i]} {content_tokens[i+1]}")

    for cand in candidates:
        cur.execute(
            """
            SELECT c.concept_id::text, c.canonical_name, c.type
            FROM terms t JOIN concepts c ON t.concept_id = c.concept_id
            WHERE lower(t.surface_form) = lower(%s)
            LIMIT 1
            """,
            (cand,),
        )
        row = cur.fetchone()
        if not row or row[0] in seen_concepts:
            continue
        seen_concepts.add(row[0])
        cur.execute(
            "SELECT surface_form FROM terms WHERE concept_id = %s LIMIT 12",
            (row[0],),
        )
        synonyms = [r[0] for r in cur.fetchall()]
        matched_concepts.append(
            {"concept_id": row[0], "canonical_name": row[1], "type": row[2],
             "surface_form": cand, "synonyms": synonyms}
        )
        expansion_terms.update(synonyms)
        expansion_terms.add(row[1])
    cur.close()

    return {
        "tokens": content_tokens,
        "boosters": boosters,
        "concepts": matched_concepts,
        "expansion_terms": sorted(expansion_terms),
    }


def _build_tsquery(expansion: dict[str, Any]) -> str:
    """websearch-style OR query from original tokens + synonym expansions."""
    parts: list[str] = []
    for tok in expansion["tokens"]:
        parts.append(tok)
    for term in expansion["expansion_terms"][:20]:
        # multiword synonyms as quoted phrases
        parts.append(f'"{term}"' if " " in term else term)
    seen = set()
    unique = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return " OR ".join(unique[:24]) if unique else ""


def retrieve_passages(db, expansion: dict[str, Any], k: int = 8) -> list[dict[str, Any]]:
    query = _build_tsquery(expansion)
    if not query:
        return []
    cur = db.cursor()
    cur.execute(
        """
        SELECT ref_id::text, work, sthana, chapter, verse_id, excerpt_text,
               ts_rank(fts, q) AS rank
        FROM "references", websearch_to_tsquery('english', %s) q
        WHERE fts @@ q
          AND length(excerpt_text) > 40
        ORDER BY rank DESC, length(excerpt_text) ASC
        LIMIT %s
        """,
        (query, k * 3),
    )
    rows = cur.fetchall()
    cur.close()

    # Dedupe near-identical excerpts, keep top k
    passages: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for r in rows:
        norm = re.sub(r"\W+", "", (r[5] or "").lower())[:120]
        if norm in seen_texts:
            continue
        seen_texts.add(norm)
        passages.append(
            {
                "ref_id": r[0], "work": r[1], "sthana": r[2], "chapter": r[3],
                "verse_id": r[4], "excerpt": (r[5] or "").strip(), "score": float(r[6]),
            }
        )
        if len(passages) >= k:
            break
    return passages


def retrieve_formulations(db, expansion: dict[str, Any], k: int = 5) -> list[dict[str, Any]]:
    """Formulations indicated for any matched disease concept."""
    concept_ids = [c["concept_id"] for c in expansion["concepts"]]
    if not concept_ids:
        return []
    cur = db.cursor()
    cur.execute(
        """
        SELECT y.yoga_id::text, y.name, k.name AS kalpana,
               COUNT(*) FILTER (WHERE yi.weight = 'primary') AS primary_hits,
               COUNT(*) AS total_hits,
               ARRAY_AGG(DISTINCT c.canonical_name) AS matched
        FROM yoga_indications yi
        JOIN yogas y ON yi.yoga_id = y.yoga_id
        JOIN concepts c ON yi.concept_id = c.concept_id
        LEFT JOIN kalpanas k ON y.kalpana_id = k.kalpana_id
        WHERE yi.concept_id = ANY(%s::uuid[])
        GROUP BY y.yoga_id, y.name, k.name
        ORDER BY primary_hits DESC, total_hits DESC
        LIMIT %s
        """,
        (concept_ids, k),
    )
    rows = cur.fetchall()
    cur.close()
    return [
        {"yoga_id": r[0], "name": r[1], "kalpana": r[2],
         "primary_hits": r[3], "total_hits": r[4], "matched_conditions": r[5]}
        for r in rows
    ]


def _citation_label(p: dict[str, Any]) -> str:
    bits = [p["work"]]
    if p.get("sthana"):
        bits.append(p["sthana"])
    if p.get("chapter"):
        ch = re.sub(r"(?i)^chapter\s*", "", str(p["chapter"]))
        bits.append(f"Ch. {ch}")
    if p.get("verse_id"):
        bits.append(f"v. {p['verse_id']}")
    return ", ".join(bits)


def compose_answer(
    question: str,
    expansion: dict[str, Any],
    passages: list[dict[str, Any]],
    formulations: list[dict[str, Any]],
) -> str:
    """Deterministic, citation-bound answer in English (translated downstream)."""
    if not passages and not formulations:
        return (
            "The current corpus does not contain a passage answering this question. "
            "Try classical terms (e.g. Jvara for fever, Kasa for cough), or ask about "
            "a specific formulation or disease."
        )

    lines: list[str] = []

    if expansion["concepts"]:
        names = ", ".join(
            f"{c['canonical_name']}" + (f" (asked as “{c['surface_form']}”)" if c["surface_form"].lower() != c["canonical_name"].lower() else "")
            for c in expansion["concepts"][:4]
        )
        lines.append(f"Recognised classical concepts: {names}.")

    if formulations:
        top = formulations[:3]
        flist = "; ".join(
            f"{f['name']}" + (f" ({f['kalpana']})" if f.get("kalpana") else "")
            + f" — indicated for {', '.join(f['matched_conditions'][:3])}"
            for f in top
        )
        lines.append(f"Formulations linked in the corpus: {flist}.")

    if passages:
        lines.append("What the classical texts say:")
        for p in passages[:4]:
            excerpt = p["excerpt"]
            if len(excerpt) > 320:
                excerpt = excerpt[:320].rsplit(" ", 1)[0] + "…"
            lines.append(f"• “{excerpt}” — {_citation_label(p)}")

    lines.append(
        "This answer is assembled only from indexed classical sources above — "
        "educational reference, not a prescription."
    )
    return "\n".join(lines)


async def llm_polish(
    llm_client,
    question: str,
    passages: list[dict[str, Any]],
    formulations: list[dict[str, Any]],
    locale: str = "en",
) -> Optional[str]:
    """Optional fluent narration, strictly grounded in retrieved passages."""
    if llm_client is None or not passages:
        return None
    lang = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(locale, "English")
    context = "\n\n".join(
        f"[{i+1}] ({_citation_label(p)}) {p['excerpt'][:500]}" for i, p in enumerate(passages[:6])
    )
    fnames = ", ".join(f["name"] for f in formulations[:5]) or "none"
    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an Ayurvedic reference librarian. Answer in {lang}. "
                        "Use ONLY the numbered passages provided. Cite passage numbers like [1]. "
                        "If passages are insufficient, say the corpus does not cover it. "
                        "Never prescribe; educational reference only."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nLinked formulations: {fnames}\n\nPassages:\n{context}",
                },
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return None


async def answer_question(
    db,
    question: str,
    llm_client=None,
    locale: str = "en",
    k: int = 8,
) -> dict[str, Any]:
    expansion = expand_query(db, question)
    passages = retrieve_passages(db, expansion, k=k)
    formulations = retrieve_formulations(db, expansion, k=5)

    llm_answer = await llm_polish(llm_client, question, passages, formulations, locale)
    answer = llm_answer or compose_answer(question, expansion, passages, formulations)

    return {
        "question": question,
        "answer": answer,
        "llm_used": llm_answer is not None,
        "concepts": [
            {"canonical_name": c["canonical_name"], "surface_form": c["surface_form"],
             "type": c["type"], "synonyms": c["synonyms"][:8]}
            for c in expansion["concepts"]
        ],
        "passages": passages,
        "formulations": formulations,
        "coverage": "corpus" if (passages or formulations) else "none",
    }
