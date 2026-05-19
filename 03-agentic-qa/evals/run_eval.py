"""Eval harness for The Auditor.

Usage:
    # Step A — gap detection only (no LLM required):
    python evals/run_eval.py

    # Step B — full end-to-end including test generation (requires Ollama):
    python evals/run_eval.py --full

Exits non-zero if any fixture's gap F1 falls below PASS_THRESHOLD.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.auditor import TreeSitterAuditor
from evals.scorers import gap_prf, test_file_executes, coverage_delta

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
PASS_THRESHOLD = 0.8  # minimum F1 for gap detection per fixture


def load_fixtures() -> list[dict]:
    fixtures = []
    for name in sorted(os.listdir(FIXTURES_DIR)):
        path = os.path.join(FIXTURES_DIR, name)
        expected_path = os.path.join(path, "expected.json")
        if os.path.isdir(path) and os.path.exists(expected_path):
            with open(expected_path) as f:
                expected = json.load(f)
            fixtures.append({"name": name, "path": path, "expected": expected})
    return fixtures


def run_gap_eval(fixtures: list[dict]) -> list[dict]:
    auditor = TreeSitterAuditor()
    results = []
    for fx in fixtures:
        t0 = time.time()
        gaps = auditor.find_gaps(fx["path"])
        elapsed = time.time() - t0
        score = gap_prf(gaps, fx["expected"]["gaps"])
        results.append({
            "fixture": fx["name"],
            "score": score,
            "elapsed_s": round(elapsed, 3),
            "predicted_gaps": [(g["file"], g["name"]) for g in gaps],
            "expected_gaps": fx["expected"]["gaps"],
        })
    return results


def run_full_eval(fixtures: list[dict]) -> list[dict]:
    from agent.graph import initialize_state, run_agent
    results = []
    for fx in fixtures:
        print(f"  Running agent on {fx['name']}...", flush=True)
        t0 = time.time()
        state = initialize_state(fx["path"])
        try:
            state = run_agent(state)
        except Exception as e:
            results.append({"fixture": fx["name"], "error": str(e)})
            continue
        elapsed = time.time() - t0

        test_file = state.get("test_file", "")
        exec_result = test_file_executes(test_file, fx["path"]) if test_file else {}

        gaps = state.get("functions", [])
        cov_result = {}
        if test_file and gaps:
            first_gap = gaps[0]
            cov_result = coverage_delta(
                first_gap["file"], first_gap["name"], fx["path"], test_file
            )

        results.append({
            "fixture": fx["name"],
            "elapsed_s": round(elapsed, 1),
            "test_file": test_file,
            "executability": exec_result,
            "coverage": cov_result,
        })
    return results


def print_gap_table(results: list[dict]) -> bool:
    print("\n=== Gap Detection (Tree-sitter, no LLM) ===")
    header = f"{'Fixture':<35} {'P':>6} {'R':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'ms':>6}"
    print(header)
    print("-" * len(header))
    all_pass = True
    for r in results:
        s = r["score"]
        passed = s["f1"] >= PASS_THRESHOLD
        flag = "  OK" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(
            f"{r['fixture']:<35} {s['precision']:>6.3f} {s['recall']:>6.3f} "
            f"{s['f1']:>6.3f} {s['tp']:>4} {s['fp']:>4} {s['fn']:>4} "
            f"{int(r['elapsed_s']*1000):>5}ms  [{flag}]"
        )
    return all_pass


def print_full_table(results: list[dict]) -> None:
    print("\n=== End-to-End (LLM + test generation) ===")
    for r in results:
        if "error" in r:
            print(f"{r['fixture']}: ERROR — {r['error']}")
            continue
        ex = r.get("executability", {})
        cov = r.get("coverage", {})
        collects = ex.get("collects", "n/a")
        passes = ex.get("passes", "n/a")
        delta = cov.get("delta", "n/a")
        improved = cov.get("improved", "n/a")
        print(
            f"{r['fixture']:<35}  collects={collects}  passes={passes}  "
            f"cov_delta={delta}%  improved={improved}  ({r['elapsed_s']}s)"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run The Auditor eval harness")
    parser.add_argument("--full", action="store_true", help="Run end-to-end eval (requires Ollama)")
    args = parser.parse_args()

    fixtures = load_fixtures()
    if not fixtures:
        print(f"No fixtures found in {FIXTURES_DIR}")
        sys.exit(1)

    print(f"Found {len(fixtures)} fixture(s): {[f['name'] for f in fixtures]}")

    gap_results = run_gap_eval(fixtures)
    all_pass = print_gap_table(gap_results)

    if args.full:
        # Note: coverage_delta only evaluates the first detected gap per fixture,
        # not all gaps. Full-eval failures (exceptions, non-executing tests) are
        # printed but do NOT affect the exit code — Ollama may not be running in CI.
        full_results = run_full_eval(fixtures)
        print_full_table(full_results)

    if not all_pass:
        print(f"\nFAIL: one or more fixtures have gap F1 < {PASS_THRESHOLD}")
        sys.exit(1)
    print("\nPASS")


if __name__ == "__main__":
    main()
