"""Load safety constraint rules from data/constraint_rules.yaml."""
import json
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_connection

ROOT = Path(__file__).parent.parent
RULES_FILE = ROOT / "data" / "constraint_rules.yaml"


def main():
    rules = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    conn = get_connection()
    cur = conn.cursor()

    loaded = 0
    for rule in rules:
        target_value = rule["target_value"]
        if not isinstance(target_value, list):
            target_value = [target_value]

        cur.execute(
            """
            INSERT INTO constraint_rules
                (rule_id, condition_concept, condition_aliases, target_type, target_value,
                 severity, message, classical_basis, applies_to_yoga_names)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rule_id) DO UPDATE
              SET condition_concept=EXCLUDED.condition_concept,
                  condition_aliases=EXCLUDED.condition_aliases,
                  target_type=EXCLUDED.target_type,
                  target_value=EXCLUDED.target_value,
                  severity=EXCLUDED.severity,
                  message=EXCLUDED.message,
                  classical_basis=EXCLUDED.classical_basis,
                  applies_to_yoga_names=EXCLUDED.applies_to_yoga_names
            """,
            (
                rule["rule_id"],
                rule["condition"],
                rule.get("condition_aliases") or [],
                rule["target_type"],
                json.dumps(target_value),
                rule["severity"],
                rule["message"].strip(),
                rule.get("classical_basis"),
                rule.get("applies_to_yoga_names") or [],
            ),
        )
        loaded += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {loaded} constraint rules")


if __name__ == "__main__":
    main()
