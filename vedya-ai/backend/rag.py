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

# Romanized Gujarati / colloquial health vocabulary → English retrieval terms.
# Lets "mane tav chhe" (Gujarati typed in Latin script) resolve to Jvara.
ROMAN_GU_LEXICON: dict[str, str] = {
    "tav": "fever", "taav": "fever", "tavv": "fever", "bukhar": "fever", "jvar": "fever",
    "khansi": "cough", "khasi": "cough", "udharas": "cough", "udhras": "cough", "ughras": "cough",
    "sardi": "common cold", "shardi": "common cold", "salekham": "common cold",
    "sojo": "swelling", "soja": "swelling", "sojo-chadvo": "swelling",
    "dukhavo": "pain", "dukhe": "pain", "dard": "pain", "pida": "pain",
    "pet": "stomach", "petma": "stomach", "petno": "stomach",
    "mathu": "head", "matha": "head", "mathano": "head", "mathama": "head",
    "ulti": "vomiting", "ubka": "nausea", "moda": "nausea",
    "jhada": "diarrhea", "zada": "diarrhea", "atisar": "diarrhea",
    "kabajiyat": "constipation", "kabjiyat": "constipation",
    "chakkar": "dizziness", "kamjori": "weakness", "nabalai": "weakness", "ashakti": "weakness",
    "bhukh": "appetite", "aruchi": "anorexia",
    "madhumeh": "diabetes", "diabetes": "diabetes", "diabites": "diabetes",
    "garbhavati": "pregnancy", "garbhvati": "pregnancy", "sagarbha": "pregnancy",
    "galama": "throat", "galu": "throat", "gala": "throat",
    "shwas": "breathlessness", "swas": "breathlessness", "haaf": "breathlessness",
    "kharaj": "itching", "khanjavad": "itching", "khaj": "itching",
    "anidra": "insomnia", "ungh": "sleep", "unghna": "sleep",
    "tavcha": "skin", "chamdi": "skin",
    "sandha": "joint", "sandhano": "joint", "ghutan": "knee",
    # intent words → booster
    "sarvar": "treatment", "ilaj": "treatment", "upay": "remedy", "upchar": "treatment",
    "dava": "medicine", "dawa": "medicine", "davo": "medicine", "aushadh": "medicine",
}

# Romanized Gujarati function words — drop them so they never pollute retrieval.
ROMAN_GU_STOPWORDS = {
    "mane", "mne", "che", "chhe", "cche", "6e", "ane", "ne", "ma", "mara", "maru",
    "thay", "thayo", "thai", "thaay", "hoy", "hoi", "joie", "joiye", "joi",
    "su", "shu", "kem", "kevi", "rite", "mate", "karvu", "karvo", "karo",
    "levu", "levi", "levo", "aave", "avey", "aavto", "gher", "ghare",
    "koi", "kai", "etle", "pan", "to", "tame", "ame", "hu", "chu", "chho",
}


def _tokenize(question: str) -> list[str]:
    words = re.findall(r"[A-Za-z\u0900-\u097F\u0A80-\u0AFF]+", question)
    return [w for w in words if len(w) > 1]


def _map_roman_gujarati(tokens: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Replace romanized Gujarati words with English retrieval terms.
    Returns (token dicts with {text, orig}, transliterations applied)."""
    mapped: list[dict[str, str]] = []
    transliterations: list[dict[str, str]] = []
    for tok in tokens:
        low = tok.lower()
        if low in ROMAN_GU_STOPWORDS:
            continue
        if low in ROMAN_GU_LEXICON:
            english = ROMAN_GU_LEXICON[low]
            mapped.append({"text": english, "orig": tok})
            transliterations.append({"from": tok, "to": english})
        else:
            mapped.append({"text": tok, "orig": tok})
    return mapped, transliterations


def extract_clinical_terms(text: str, max_terms: int = 12) -> list[str]:
    """No-LLM fallback for free-text intake: tokenize, map romanized Gujarati,
    drop function words, and emit bigrams first so 'common cold' resolves
    before 'cold'. The resolver decides what actually maps to a concept."""
    tokens = _tokenize(text)
    mapped, _ = _map_roman_gujarati(tokens)
    content = [
        t["text"] for t in mapped
        if t["text"].lower() not in STOPWORDS
    ]
    content = list(dict.fromkeys(content))
    bigrams = [f"{content[i]} {content[i+1]}" for i in range(len(content) - 1)]
    return (bigrams + content)[:max_terms]


def expand_query(db, question: str) -> dict[str, Any]:
    """Map question words to canonical concepts + synonyms via terms table."""
    raw_tokens = _tokenize(question)
    token_dicts, transliterations = _map_roman_gujarati(raw_tokens)
    content = [t for t in token_dicts if t["text"].lower() not in STOPWORDS]
    boosters = [t["text"] for t in token_dicts if t["text"].lower() in INTENT_BOOSTERS]

    matched_concepts: list[dict[str, Any]] = []
    expansion_terms: set[str] = set()
    seen_concepts: set[str] = set()

    cur = db.cursor()
    # Try single tokens and adjacent bigrams (e.g. "common cold")
    candidates: list[dict[str, str]] = list(content)
    for i in range(len(content) - 1):
        candidates.append({
            "text": f"{content[i]['text']} {content[i+1]['text']}",
            "orig": f"{content[i]['orig']} {content[i+1]['orig']}",
        })

    for cand in candidates:
        cur.execute(
            """
            SELECT c.concept_id::text, c.canonical_name, c.type
            FROM terms t JOIN concepts c ON t.concept_id = c.concept_id
            WHERE lower(t.surface_form) = lower(%s)
            LIMIT 1
            """,
            (cand["text"],),
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
             "surface_form": cand["orig"], "synonyms": synonyms}
        )
        expansion_terms.update(synonyms)
        expansion_terms.add(row[1])
    cur.close()

    return {
        "tokens": [t["text"] for t in content],
        "boosters": boosters,
        "concepts": matched_concepts,
        "expansion_terms": sorted(expansion_terms),
        "transliterations": transliterations,
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
) -> list[str]:
    """Deterministic, citation-bound summary as separate lines.
    Kept short and structured — full verse quotes live in the sources panel,
    and each line is translated independently so formatting survives."""
    if not passages and not formulations:
        return [
            "The current corpus does not contain a passage answering this question.",
            "Try classical terms (e.g. Jvara for fever, Kasa for cough), or ask about "
            "a specific formulation or disease.",
        ]

    lines: list[str] = []

    if expansion["concepts"]:
        names = ", ".join(
            f"{c['canonical_name']}" + (f" (asked as “{c['surface_form']}”)" if c["surface_form"].lower() != c["canonical_name"].lower() else "")
            for c in expansion["concepts"][:4]
        )
        lines.append(f"Your question maps to the classical concepts: {names}.")

    if formulations:
        top = formulations[:3]
        for f in top:
            kalpana = f" ({f['kalpana']})" if f.get("kalpana") else ""
            lines.append(
                f"• {f['name']}{kalpana} is indicated in the corpus for "
                f"{', '.join(f['matched_conditions'][:3])}."
            )

    if passages:
        works = sorted({p["work"] for p in passages[:4]})
        lines.append(
            f"{len(passages)} supporting passages were retrieved from {', '.join(works)} — "
            "see the classical sources below with exact chapter and verse."
        )

    return lines


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
    lang = {"en": "English", "gu": "Gujarati"}.get(locale, "English")
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
    answer_lines = (
        [line for line in llm_answer.split("\n") if line.strip()]
        if llm_answer
        else compose_answer(question, expansion, passages, formulations)
    )

    return {
        "question": question,
        "answer": "\n".join(answer_lines),
        "answer_lines": answer_lines,
        "transliterations": expansion.get("transliterations", []),
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
