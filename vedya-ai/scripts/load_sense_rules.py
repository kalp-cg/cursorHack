"""Load contextual sense/homonym disambiguation rules from data/sense_rules.yaml."""
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_connection

ROOT = Path(__file__).parent.parent
SENSE_FILE = ROOT / "data" / "sense_rules.yaml"


def main():
    rules = yaml.safe_load(SENSE_FILE.read_text(encoding="utf-8"))
    conn = get_connection()
    cur = conn.cursor()

    loaded = 0
    for rule in rules:
        term = rule["term"]
        context_yoga_name = rule.get("context_yoga")
        context_dravya = rule.get("context_botanical") or rule.get("context_dravya_name") or ""
        explanation = (rule.get("explanation") or "").strip()
        source = rule.get("source")
        default_dravya = rule.get("default_botanical") or rule.get("default_dravya_name") or ""

        # Resolve context_yoga_id if yoga name is not 'any'
        context_yoga_id = None
        if context_yoga_name and context_yoga_name != "any":
            cur.execute(
                "SELECT yoga_id FROM yogas WHERE lower(name) = lower(%s)", (context_yoga_name,)
            )
            row = cur.fetchone()
            if row:
                context_yoga_id = str(row[0])

        cur.execute(
            """
            INSERT INTO sense_rules
                (term, default_dravya_name, context_yoga_id, context_yoga_name, context_dravya_name, explanation, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (term, default_dravya, context_yoga_id, context_yoga_name, context_dravya, explanation, source),
        )
        loaded += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {loaded} sense rules")


if __name__ == "__main__":
    main()
