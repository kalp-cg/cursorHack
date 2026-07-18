"""
Phase 0a: Enrich formulations with symptom_tags, primary_indications, secondary_indications.

Strategy:
  1. Parse free-text `indications` field against a canonical DISEASE_DICT
     to derive primary indication tags.
  2. Cross-reference `main_ingredients` against herbs_amidha for each herb's
     `main_indications` to derive secondary indication tags.
  3. Preserve existing `symptom_tags` on the 3 hero demos; enrich the rest.

Output: data/enriched/formulations_enriched.json
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
ENRICHED = ROOT / "data" / "enriched"
ENRICHED.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Canonical disease/symptom dictionary
# Each entry: "surface string" -> "canonical tag"
# Covers both English terms in the indications text and Ayurvedic terms.
# ---------------------------------------------------------------------------
DISEASE_DICT: dict[str, str] = {
    # Fever / Jvara cluster
    "fever": "Jvara",
    "jvara": "Jvara",
    "jwara": "Jvara",
    "santapa": "Jvara",
    "pyrexia": "Jvara",
    "chronic fever": "Jvara",
    "all types of fever": "Jvara",
    "intermittent fever": "Jvara",

    # Cough / Kasa cluster
    "cough": "Kasa",
    "kasa": "Kasa",
    "dry cough": "Kasa",
    "kapha cough": "Kasa",

    # Cold / Pinasa cluster
    "common cold": "Pinasa",
    "cold": "Pinasa",
    "pinasa": "Pinasa",
    "pratishyaya": "Pinasa",
    "pratiśyāya": "Pinasa",
    "urti": "Pinasa",
    "upper respiratory tract infection": "Pinasa",
    "rhinitis": "Pinasa",
    "runny nose": "Pinasa",
    "nasal": "Pinasa",

    # Breathlessness / Shwasa cluster
    "breathlessness": "Shwasa",
    "dyspnea": "Shwasa",
    "asthma": "Shwasa",
    "shwasa": "Shwasa",
    "swasa": "Shwasa",
    "bronchial": "Shwasa",
    "tamaka": "Shwasa",

    # Hiccup
    "hiccup": "Hikka",
    "hikka": "Hikka",
    "hiccough": "Hikka",

    # Edema / Shotha cluster
    "edema": "Shotha",
    "oedema": "Shotha",
    "swelling": "Shotha",
    "inflammation": "Shotha",
    "shotha": "Shotha",
    "shopha": "Shotha",
    "inflammatory": "Shotha",
    "sotha": "Shotha",

    # Diabetes / Prameha cluster
    "diabetes": "Prameha",
    "prameha": "Prameha",
    "madhumeha": "Prameha",
    "diabetic": "Prameha",
    "urinary disorders": "Prameha",
    "glycosuria": "Prameha",

    # Digestive / Agnimandya cluster
    "indigestion": "Agnimandya",
    "agnimandya": "Agnimandya",
    "dyspepsia": "Agnimandya",
    "loss of appetite": "Agnimandya",
    "aruchi": "Agnimandya",
    "digestive": "Agnimandya",
    "anorexia": "Agnimandya",

    # IBS / Grahani
    "malabsorption": "Grahani",
    "grahani": "Grahani",
    "irritable bowel": "Grahani",
    "ibs": "Grahani",

    # Constipation / Vibandha
    "constipation": "Vibandha",
    "vibandha": "Vibandha",
    "laxative": "Vibandha",

    # Diarrhoea / Atisara
    "diarrhea": "Atisara",
    "diarrhoea": "Atisara",
    "atisara": "Atisara",
    "loose stools": "Atisara",

    # Dysentery / Pravahika
    "dysentery": "Pravahika",
    "pravahika": "Pravahika",

    # Piles / Arsha
    "piles": "Arsha",
    "hemorrhoids": "Arsha",
    "arsha": "Arsha",

    # Jaundice / Kamala
    "jaundice": "Kamala",
    "kamala": "Kamala",
    "icterus": "Kamala",

    # Liver disorders
    "liver": "Yakrit Vikara",
    "hepatitis": "Yakrit Vikara",
    "hepatomegaly": "Yakrit Vikara",
    "yakrit": "Yakrit Vikara",

    # Skin / Kushtha cluster
    "skin disease": "Kushtha",
    "kushtha": "Kushtha",
    "eczema": "Kushtha",
    "psoriasis": "Kushtha",
    "dermatitis": "Kushtha",
    "skin": "Kushtha",
    "leprosy": "Kushtha",

    # Wounds / Vrana
    "wound": "Vrana",
    "vrana": "Vrana",
    "ulcer": "Vrana",
    "non-healing": "Vrana",
    "burn": "Vrana",

    # Eye / Netra Roga
    "eye disease": "Netra Roga",
    "eye": "Netra Roga",
    "netra": "Netra Roga",
    "vision": "Netra Roga",
    "chakshushya": "Netra Roga",
    "ophthalmia": "Netra Roga",
    "conjunctivitis": "Netra Roga",

    # Hair / Kesha
    "hair fall": "Khalitya",
    "hair": "Khalitya",
    "keshya": "Khalitya",
    "khalitya": "Khalitya",
    "alopecia": "Khalitya",

    # Hyperacidity / Amlapitta
    "hyperacidity": "Amlapitta",
    "amlapitta": "Amlapitta",
    "acid peptic": "Amlapitta",

    # Bleeding / Raktapitta
    "raktapitta": "Raktapitta",
    "bleeding disorder": "Raktapitta",
    "hemoptysis": "Raktapitta",

    # Calcium / Bone
    "calcium": "Asthi Kshaya",
    "bone": "Asthi Kshaya",

    # Pitta pacifier
    "pitta pacifier": "Pitta Shamana",

    # Anemia / Pandu
    "anemia": "Pandu",
    "anaemia": "Pandu",
    "pandu": "Pandu",
    "iron deficiency": "Pandu",

    # Heart / Hridaya
    "heart": "Hrid Roga",
    "hridya": "Hrid Roga",
    "cardiac": "Hrid Roga",
    "palpitation": "Hrid Roga",

    # Joints / Amavata-Vatarakta
    "arthritis": "Amavata",
    "amavata": "Amavata",
    "rheumatoid": "Amavata",
    "gout": "Vatarakta",
    "vatarakta": "Vatarakta",
    "joint pain": "Amavata",
    "joints": "Amavata",

    # Back pain / Katigraha
    "back pain": "Katigraha",
    "lumbar": "Katigraha",
    "katigraha": "Katigraha",

    # Nervous / Vata Vyadhi
    "paralysis": "Vata Vyadhi",
    "neurological": "Vata Vyadhi",
    "vata vyadhi": "Vata Vyadhi",
    "epilepsy": "Vata Vyadhi",
    "tremor": "Vata Vyadhi",

    # Memory / Medhya
    "memory": "Medhya",
    "medhya": "Medhya",
    "brain": "Medhya",
    "cognition": "Medhya",
    "concentration": "Medhya",

    # Menstrual / Artava
    "menstrual": "Artava Vikara",
    "menorrhagia": "Artava Vikara",
    "dysmenorrhea": "Artava Vikara",
    "leucorrhea": "Artava Vikara",
    "amenorrhea": "Artava Vikara",
    "asrigdara": "Artava Vikara",

    # Reproductive / Shukra
    "infertility": "Shukra Kshaya",
    "aphrodisiac": "Vajikarana",
    "vajikarana": "Vajikarana",
    "libido": "Vajikarana",

    # Postnatal / Sutika
    "post-natal": "Sutika",
    "post natal": "Sutika",
    "sutika": "Sutika",
    "postnatal": "Sutika",
    "postpartum": "Sutika",

    # Urinary / Mutravaha
    "urinary": "Mutra Vikara",
    "diuretic": "Mutra Vikara",
    "mutra": "Mutra Vikara",
    "dysuria": "Mutra Vikara",
    "kidney": "Mutra Vikara",

    # Ascites / Jalodara
    "ascites": "Jalodara",
    "jalodara": "Jalodara",
    "abdominal fluid": "Jalodara",

    # Spleen / Pliha
    "spleen": "Pliha Roga",
    "plihayakrid": "Pliha Roga",

    # General debility / Daurbalya
    "debility": "Daurbalya",
    "weakness": "Daurbalya",
    "fatigue": "Daurbalya",
    "daurbalya": "Daurbalya",
    "emaciation": "Daurbalya",
    "general tonic": "Daurbalya",
    "tonic": "Daurbalya",
    "rejuvenative": "Rasayana",
    "rasayana": "Rasayana",
    "health promoter": "Rasayana",
    "immunomodulator": "Rasayana",
    "immunity": "Rasayana",
    "adaptogen": "Rasayana",

    # Intestinal worms / Krimi
    "worm": "Krimi",
    "parasite": "Krimi",
    "krimi": "Krimi",

    # Obesity / Sthoulya
    "obesity": "Sthoulya",
    "overweight": "Sthoulya",
    "sthoulya": "Sthoulya",
    "weight loss": "Sthoulya",
}


def normalize(text: str) -> str:
    """Lower-case + unicode-normalize a string for matching."""
    return unicodedata.normalize("NFKD", text.lower()).strip()


def extract_primary_from_indications(indication_text: str) -> list[str]:
    """
    Scan the free-text `indications` field for known disease/symptom terms.
    Returns deduplicated list of canonical tags, ordered by first occurrence.
    """
    text_norm = normalize(indication_text)
    found: dict[str, int] = {}  # canonical -> first match position

    # Sort by length descending so longer phrases match before substrings
    for surface, canonical in sorted(DISEASE_DICT.items(), key=lambda x: -len(x[0])):
        pos = text_norm.find(normalize(surface))
        if pos != -1 and canonical not in found:
            found[canonical] = pos

    return [k for k, _ in sorted(found.items(), key=lambda x: x[1])]


def build_herb_lookup(herbs: list[dict]) -> dict[str, dict]:
    """Build a lookup from normalized herb name -> herb record."""
    lookup: dict[str, dict] = {}
    for h in herbs:
        name_norm = normalize(h["name"])
        lookup[name_norm] = h
        for syn in h.get("sanskrit_synonyms") or []:
            lookup[normalize(syn)] = h
    return lookup


def get_secondary_from_ingredients(
    main_ingredients: list[str],
    herb_lookup: dict[str, dict],
    primary_set: set[str],
) -> list[str]:
    """
    Collect main_indications from constituent herbs that are NOT already primary.
    De-duplicate, preserve order of first encounter.
    """
    seen: set[str] = set(primary_set)
    secondary: list[str] = []
    for ing_name in main_ingredients:
        herb = herb_lookup.get(normalize(ing_name))
        if not herb:
            # Try partial match (first word)
            first_word = normalize(ing_name).split()[0] if ing_name else ""
            herb = herb_lookup.get(first_word)
        if herb:
            for indication in herb.get("main_indications") or []:
                canonical = DISEASE_DICT.get(normalize(indication), indication)
                if canonical not in seen:
                    seen.add(canonical)
                    secondary.append(canonical)
    return secondary


def enrich_formulations(
    formulations: list[dict],
    herbs: list[dict],
) -> list[dict]:
    herb_lookup = build_herb_lookup(herbs)
    enriched = []

    for f in formulations:
        f_out = dict(f)  # shallow copy

        # If already fully tagged (hero demos), preserve existing tags
        existing_tags = f.get("symptom_tags") or []
        if existing_tags:
            # Derive primary/secondary split from existing tags vs indications
            indications_text = f.get("indications", "")
            primary = extract_primary_from_indications(indications_text)
            primary_set = set(primary)
            secondary = [t for t in existing_tags if t not in primary_set]
            f_out["primary_indications"] = primary if primary else existing_tags[:3]
            f_out["secondary_indications"] = secondary
            enriched.append(f_out)
            continue

        # Derive from indications text
        indications_text = f.get("indications", "")
        primary = extract_primary_from_indications(indications_text)
        primary_set = set(primary)

        # Derive secondary from ingredient herbs
        main_ingredients = f.get("main_ingredients") or []
        secondary = get_secondary_from_ingredients(main_ingredients, herb_lookup, primary_set)

        # Build unified symptom_tags (primary first, then secondary)
        all_tags = list(dict.fromkeys(primary + secondary))

        f_out["symptom_tags"] = all_tags
        f_out["primary_indications"] = primary
        f_out["secondary_indications"] = secondary

        enriched.append(f_out)

    return enriched


def main():
    forms_path = RAW / "formulations_bhaishajya.json"
    herbs_path = RAW / "herbs_amidha.json"

    print(f"Loading formulations from {forms_path}")
    formulations = json.loads(forms_path.read_text(encoding="utf-8"))

    print(f"Loading herbs from {herbs_path}")
    herbs = json.loads(herbs_path.read_text(encoding="utf-8"))

    print(f"Enriching {len(formulations)} formulations...")
    enriched = enrich_formulations(formulations, herbs)

    out_path = ENRICHED / "formulations_enriched.json"
    out_path.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Written {len(enriched)} records to {out_path}")

    # Stats
    with_tags = sum(1 for f in enriched if f.get("symptom_tags"))
    zero_tags = sum(1 for f in enriched if not f.get("symptom_tags"))
    avg_primary = sum(len(f.get("primary_indications", [])) for f in enriched) / len(enriched)
    avg_secondary = sum(len(f.get("secondary_indications", [])) for f in enriched) / len(enriched)

    print(f"\n=== Enrichment stats ===")
    print(f"  With symptom_tags: {with_tags}/{len(enriched)}")
    print(f"  Zero tags (check DISEASE_DICT coverage): {zero_tags}")
    print(f"  Avg primary indications: {avg_primary:.1f}")
    print(f"  Avg secondary indications: {avg_secondary:.1f}")

    # Spot-check hero demos
    print("\n=== Hero demo verification ===")
    for name in ("Punarnavadi Kashayam", "Vyaghryadi Kashayam", "Jatyadi Ghrita"):
        match = next((f for f in enriched if f["name"] == name), None)
        if match:
            print(f"\n{name}:")
            print(f"  primary: {match.get('primary_indications')}")
            print(f"  secondary: {match.get('secondary_indications')}")
            print(f"  symptom_tags: {match.get('symptom_tags')}")


if __name__ == "__main__":
    main()
