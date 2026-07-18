"""
Build the unified RAG corpus: data/corpus.json

Walks every raw source and emits one clean, deduplicated, training-ready
record list. This file IS the data model for retrieval — anything indexed
into Postgres FTS comes from here, so corpus quality can be reviewed by
opening a single JSON file.

Record shape:
{
  "doc_id":      stable sha1 of (source_type, work, sthana, chapter, verse_id, name),
  "source_type": "verse" | "formulation" | "herb",
  "work":        source text name,
  "sthana":      section (verses only),
  "chapter":     chapter (verses only),
  "verse_id":    verse number (verses only),
  "name":        formulation/herb name (structured records only),
  "text":        retrievable English text,
  "metadata":    everything else worth keeping (type, category, dosage, ...)
}

Usage:
    python scripts/build_corpus.py            # writes data/corpus.json
    python scripts/build_corpus.py --load     # also upserts verse records into Postgres
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "corpus.json"

STHANA_MAP = {
    "1.Sutrasthana": "Sutrasthana",
    "2.Nidanasthana": "Nidanasthana",
    "3.Vimanasthana": "Vimanasthana",
    "4.Sharirasthana": "Sharirasthana",
    "5.Indriyasthana": "Indriyasthana",
    "6.Cikitsasthana": "Cikitsasthana",
    "7.Kalpasthana": "Kalpasthana",
    "8.Siddhisthana": "Siddhisthana",
}


def doc_id(*parts: str) -> str:
    return hashlib.sha1("||".join(p or "" for p in parts).encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    # Strip bracketed editorial artifacts like [???]
    text = re.sub(r"\[\?+\]", "", text)
    return text.strip()


def build_verses() -> list[dict]:
    records: list[dict] = []
    seen: set[str] = set()
    charaka = RAW / "Ayurveda" / "charak-samhita"
    for sthana_dir in sorted(charaka.iterdir()):
        if not sthana_dir.is_dir():
            continue
        sthana = next(
            (v for k, v in STHANA_MAP.items() if sthana_dir.name.startswith(k)),
            sthana_dir.name,
        )
        for chapter_file in sorted(sthana_dir.glob("*.json")):
            chapter = chapter_file.stem.replace("chapter", "")
            try:
                verses = json.loads(chapter_file.read_text())
            except Exception as e:
                print(f"  ! skip {chapter_file}: {e}", file=sys.stderr)
                continue
            for v in verses:
                text = clean_text(v.get("text", ""))
                if len(text) < 15:  # headers / empty artifacts
                    continue
                did = doc_id("verse", "Charaka Samhita", sthana, chapter, str(v.get("verse_id", "")), "")
                if did in seen:
                    continue
                seen.add(did)
                records.append({
                    "doc_id": did,
                    "source_type": "verse",
                    "work": "Charaka Samhita",
                    "sthana": sthana,
                    "chapter": chapter,
                    "verse_id": str(v.get("verse_id", "")),
                    "name": None,
                    "text": text,
                    "metadata": {},
                })
    return records


def build_formulations() -> list[dict]:
    records: list[dict] = []
    path = RAW / "formulations_bhaishajya.json"
    if not path.exists():
        return records
    for f in json.loads(path.read_text()):
        name = clean_text(f.get("name", ""))
        if not name:
            continue
        text_bits = [name]
        if f.get("type"):
            text_bits.append(f"({f['type']})")
        if f.get("indications"):
            text_bits.append(f"Indications: {clean_text(f['indications'])}")
        if f.get("ingredients"):
            text_bits.append(f"Ingredients: {clean_text(f['ingredients'])}")
        records.append({
            "doc_id": doc_id("formulation", f.get("reference", ""), "", "", "", name),
            "source_type": "formulation",
            "work": clean_text(f.get("reference", "")) or "Bhaishajya compendium",
            "sthana": None,
            "chapter": None,
            "verse_id": None,
            "name": name,
            "text": " ".join(text_bits),
            "metadata": {
                "type": f.get("type"),
                "category": f.get("category"),
                "main_ingredients": f.get("main_ingredients"),
                "dosage": f.get("dosage"),
                "anupana": f.get("anupana"),
            },
        })
    return records


def build_herbs() -> list[dict]:
    records: list[dict] = []
    path = RAW / "herbs_amidha.json"
    if not path.exists():
        return records
    herbs = json.loads(path.read_text())
    items = herbs if isinstance(herbs, list) else herbs.get("herbs", [])
    for h in items:
        if not isinstance(h, dict):
            continue
        name = clean_text(h.get("name") or h.get("sanskrit_name") or "")
        if not name:
            continue
        text_bits = [name]
        for key in ("botanical_name", "english_name", "actions", "indications", "rasa", "virya", "vipaka"):
            val = h.get(key)
            if val:
                if isinstance(val, list):
                    val = ", ".join(str(x) for x in val)
                text_bits.append(f"{key.replace('_', ' ').title()}: {clean_text(str(val))}")
        records.append({
            "doc_id": doc_id("herb", "", "", "", "", name),
            "source_type": "herb",
            "work": "Herb monographs (Amidha)",
            "sthana": None,
            "chapter": None,
            "verse_id": None,
            "name": name,
            "text": " ".join(text_bits),
            "metadata": {k: h.get(k) for k in ("botanical_name", "english_name", "rasa", "guna", "virya", "vipaka") if h.get(k)},
        })
    return records


def load_verses_to_db(verses: list[dict]) -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    from db_utils import get_connection
    from psycopg2.extras import execute_values

    conn = get_connection()
    cur = conn.cursor()
    rows = [
        (v["work"], v["sthana"], v["chapter"], v["verse_id"], v["text"], "corpus.json")
        for v in verses
    ]
    # Partial unique index uq_refs_charaka_verse makes this idempotent
    execute_values(
        cur,
        """
        INSERT INTO "references" (work, sthana, chapter, verse_id, excerpt_text, source_file)
        VALUES %s
        ON CONFLICT (sthana, chapter, verse_id) WHERE work = 'Charaka Samhita'
        DO UPDATE SET excerpt_text = EXCLUDED.excerpt_text
        """,
        rows,
        page_size=500,
    )
    conn.commit()
    cur.execute("SELECT count(*) FROM \"references\"")
    print(f"  references table now: {cur.fetchone()[0]} rows")
    cur.close()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", action="store_true", help="upsert verses into Postgres")
    args = parser.parse_args()

    verses = build_verses()
    formulations = build_formulations()
    herbs = build_herbs()
    corpus = verses + formulations + herbs

    OUT.write_text(json.dumps(corpus, ensure_ascii=False, indent=1))
    print(f"✓ corpus.json written: {len(corpus)} records "
          f"({len(verses)} verses, {len(formulations)} formulations, {len(herbs)} herbs)")

    if args.load:
        load_verses_to_db(verses)


if __name__ == "__main__":
    main()
