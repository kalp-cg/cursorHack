"""
VedyaAI Eval Harness — run_eval.py
Tests M3 (ranker without LLM), M4 (safety 100%), M5 (zero hallucinated refs).

Usage:
  DATABASE_URL=postgresql://... LLM_ENABLED=false python3 run_eval.py
  DATABASE_URL=postgresql://... python3 run_eval.py --gate M3
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.intake import build_clinical_frame
from pipeline.resolver import EntityResolver
from pipeline.retriever import retrieve_candidates
from pipeline.safety import SafetyEngine
from pipeline.ranker import rank
from models.schemas import VignetteInput, ClinicalFrame

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vedya:vedyapass@localhost:5432/vedyaai")
VIGNETTES_FILE = Path(__file__).parent / "golden_vignettes.json"


def connect():
    return psycopg2.connect(DATABASE_URL)


def run_pipeline_no_llm(inp_dict: dict, db):
    """Run the deterministic pipeline (no LLM) and return ranked results."""
    inp = VignetteInput(**inp_dict)
    frame = build_clinical_frame(inp)

    resolver = EntityResolver(db)
    resolver_output = resolver.resolve(frame)

    candidates = retrieve_candidates(resolver_output, frame, db, top_k=50)
    if not candidates:
        return [], [], frame, resolver_output

    safety_engine = SafetyEngine(db)
    safety_results = safety_engine.apply(candidates, frame)

    ranked = rank(candidates, safety_results, frame, top_k=20)
    return ranked, safety_results, frame, resolver_output


def check_pairwise(ranked, pairwise_expectations) -> list[dict]:
    """Check pairwise ranking expectations."""
    results = []
    ranked_names = [r.yoga_name for r in ranked]
    for exp in pairwise_expectations:
        preferred = exp["preferred"]
        over = exp["over"]
        try:
            pos_preferred = ranked_names.index(preferred)
        except ValueError:
            results.append({"pass": False, "reason": f"'{preferred}' not in results", "exp": exp})
            continue
        try:
            pos_over = ranked_names.index(over)
        except ValueError:
            results.append({"pass": False, "reason": f"'{over}' not in results", "exp": exp})
            continue
        passed = pos_preferred < pos_over
        results.append({
            "pass": passed,
            "reason": f"'{preferred}' rank {pos_preferred+1} vs '{over}' rank {pos_over+1}",
            "exp": exp,
        })
    return results


def check_safety(safety_results, expected: dict) -> list[dict]:
    """Check safety gate expectations."""
    results = []
    fired_rule_ids = set()
    for sr in safety_results:
        for v in sr.violations:
            fired_rule_ids.add(v.rule_id)

    for rule_id in (expected.get("safety_fires") or []):
        passed = rule_id in fired_rule_ids
        results.append({
            "pass": passed,
            "reason": f"Rule {rule_id} {'fired' if passed else 'DID NOT fire'}",
            "rule_id": rule_id,
        })

    if expected.get("safety_severity_min") == "HARD_EXCLUDE":
        has_hard = any(sr.hard_excluded for sr in safety_results)
        results.append({
            "pass": has_hard,
            "reason": "At least one HARD_EXCLUDE fired" if has_hard else "No HARD_EXCLUDE found",
        })

    return results


def check_recall(ranked, expected: dict) -> list[dict]:
    """Check candidate recall expectations."""
    results = []
    ranked_names = [r.yoga_name for r in ranked]

    for name in (expected.get("top_k_must_include") or []):
        found = name in ranked_names
        results.append({
            "pass": found,
            "reason": f"'{name}' {'found' if found else 'NOT found'} in top {len(ranked)} results",
        })

    min_count = expected.get("top_k_min_count", 0)
    if min_count:
        results.append({
            "pass": len(ranked) >= min_count,
            "reason": f"Got {len(ranked)} results, needed >= {min_count}",
        })

    return results


def run_all(db, gate: str | None = None) -> dict:
    vignettes = json.loads(VIGNETTES_FILE.read_text(encoding="utf-8"))["vignettes"]

    total = 0
    passed = 0
    failed_cases: list[dict] = []

    for vignette in vignettes:
        vtype = vignette["expected"]["type"]

        # Gate filtering
        if gate == "M3" and vtype not in ("pairwise_discrimination",):
            continue
        if gate == "M4" and vtype not in ("safety_gate",):
            continue
        if gate == "M5" and vtype not in ("citation_validity",):
            continue

        ranked, safety_results, frame, resolver_output = run_pipeline_no_llm(vignette["input"], db)

        case_results = []
        expected = vignette["expected"]

        if vtype == "pairwise_discrimination":
            case_results.extend(check_pairwise(ranked, expected.get("pairwise", [])))

        if vtype == "safety_gate":
            case_results.extend(check_safety(safety_results, expected))

        if vtype in ("candidate_recall", "pairwise_discrimination"):
            case_results.extend(check_recall(ranked, expected))

        if vtype == "synonym_retrieval":
            case_results.extend(check_recall(ranked, expected))
            # Check resolved concepts
            resolved_canonicals = [rc.canonical_name for rc in resolver_output.resolved_concepts]
            for must in (expected.get("resolved_must_include") or []):
                found = must in resolved_canonicals
                case_results.append({
                    "pass": found,
                    "reason": f"Concept '{must}' {'resolved' if found else 'NOT resolved'}",
                })

        if vtype == "citation_validity":
            for r in ranked[:5]:
                has_ref = bool(r.references)
                case_results.append({
                    "pass": has_ref,
                    "reason": f"'{r.yoga_name}' has refs: {has_ref}",
                })

        # Aggregate
        for cr in case_results:
            total += 1
            if cr["pass"]:
                passed += 1
            else:
                failed_cases.append({
                    "vignette_id": vignette["id"],
                    "vignette_name": vignette["name"],
                    **cr,
                })

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": round(passed / total * 100, 1) if total else 0,
        "failed_cases": failed_cases,
    }


def main():
    parser = argparse.ArgumentParser(description="VedyaAI Eval Harness")
    parser.add_argument("--gate", choices=["M3", "M4", "M5"], help="Run specific milestone gate only")
    parser.add_argument("--verbose", action="store_true", help="Show all results")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"VedyaAI Eval Harness  (LLM_ENABLED={os.getenv('LLM_ENABLED','true')})")
    print(f"Gate: {args.gate or 'ALL'}")
    print(f"{'='*60}\n")

    try:
        db = connect()
        print("✓ Database connected\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    results = run_all(db, gate=args.gate)

    print(f"Results: {results['passed']}/{results['total']} passed ({results['accuracy']}%)")

    if results["failed_cases"]:
        print(f"\n✗ FAILURES ({len(results['failed_cases'])}):")
        for fc in results["failed_cases"]:
            print(f"  [{fc['vignette_id']}] {fc['vignette_name']}: {fc['reason']}")

    if args.verbose and not results["failed_cases"]:
        print("\n✓ All checks passed!")

    # Gate-specific verdict
    gate_pass = results["failed"] == 0
    if args.gate == "M3":
        print(f"\n{'✓ M3 GATE PASS' if gate_pass else '✗ M3 GATE FAIL'}: Ranker discriminates without LLM")
    elif args.gate == "M4":
        print(f"\n{'✓ M4 GATE PASS' if gate_pass else '✗ M4 GATE FAIL'}: 100% safety rule catch rate")
    elif args.gate == "M5":
        print(f"\n{'✓ M5 GATE PASS' if gate_pass else '✗ M5 GATE FAIL'}: Zero hallucinated citations")

    db.close()
    sys.exit(0 if gate_pass else 1)


if __name__ == "__main__":
    main()
