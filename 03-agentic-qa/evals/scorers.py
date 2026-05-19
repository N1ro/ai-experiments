"""Scoring functions for The Auditor eval harness."""

from __future__ import annotations
import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def gap_prf(predicted: list[dict], expected: list[list]) -> dict:
    """Compute precision, recall, F1 for gap detection.

    predicted: list of dicts with keys 'file' and 'name' (from find_testing_gaps)
    expected: list of [relative_file, function_name] pairs from expected.json
    """
    pred_set = {(os.path.normpath(g["file"]), g["name"]) for g in predicted}
    # expected paths are relative; normalise for comparison
    exp_set = {(os.path.normpath(e[0]), e[1]) for e in expected}

    # Align by function name + filename stem so absolute-path differences don't matter
    pred_keys = {(Path(f).name, n) for f, n in pred_set}
    exp_keys = {(Path(f).name, n) for f, n in exp_set}

    tp = len(pred_keys & exp_keys)
    fp = len(pred_keys - exp_keys)
    fn = len(exp_keys - pred_keys)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "tp": tp, "fp": fp, "fn": fn}


def test_file_executes(test_file_path: str, fixture_dir: str) -> dict:
    """Return whether the generated test file can be collected and run by pytest.

    Copies the entire fixture dir to a temp location so writes don't pollute fixtures.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_fixture = os.path.join(tmp, "fixture")
        shutil.copytree(fixture_dir, tmp_fixture)

        rel = os.path.relpath(test_file_path, fixture_dir)
        tmp_test = os.path.join(tmp_fixture, rel)

        if not os.path.exists(tmp_test):
            return {"collects": False, "passes": False, "error": "test file not found"}

        collect = subprocess.run(
            ["python", "-m", "pytest", tmp_test, "--collect-only", "-q"],
            cwd=tmp_fixture,
            capture_output=True,
            text=True,
        )
        if collect.returncode != 0:
            return {"collects": False, "passes": False, "error": collect.stdout + collect.stderr}

        run = subprocess.run(
            ["python", "-m", "pytest", tmp_test, "-x", "-q"],
            cwd=tmp_fixture,
            capture_output=True,
            text=True,
        )
        return {
            "collects": True,
            "passes": run.returncode == 0,
            "output": run.stdout + run.stderr,
        }


def coverage_delta(source_file: str, target_function: str, fixture_dir: str,
                   generated_test_path: str) -> dict:
    """Measure whether coverage of target_function increases after adding the generated test.

    Runs coverage before (existing tests only) and after (existing + generated).
    Returns covered_before and covered_after booleans.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_fixture = os.path.join(tmp, "fixture")
        shutil.copytree(fixture_dir, tmp_fixture)

        rel_src = os.path.relpath(source_file, fixture_dir)
        tmp_src = os.path.join(tmp_fixture, rel_src)

        def run_coverage(extra_args: list[str]) -> str:
            result = subprocess.run(
                ["python", "-m", "coverage", "run", "--include", tmp_src,
                 "-m", "pytest", "-q"] + extra_args,
                cwd=tmp_fixture,
                capture_output=True,
                text=True,
            )
            report = subprocess.run(
                ["python", "-m", "coverage", "report", "--include", tmp_src],
                cwd=tmp_fixture,
                capture_output=True,
                text=True,
            )
            return report.stdout

        before = run_coverage([os.path.join(tmp_fixture, "tests")])

        rel_gen = os.path.relpath(generated_test_path, fixture_dir)
        tmp_gen = os.path.join(tmp_fixture, rel_gen)
        after = run_coverage([os.path.join(tmp_fixture, "tests"), tmp_gen]
                             if os.path.exists(tmp_gen) else [os.path.join(tmp_fixture, "tests")])

        def pct(report: str) -> int:
            for line in report.splitlines():
                if "TOTAL" in line:
                    parts = line.split()
                    try:
                        return int(parts[-1].rstrip("%"))
                    except ValueError:
                        pass
            return 0

        before_pct = pct(before)
        after_pct = pct(after)
        return {
            "coverage_before": before_pct,
            "coverage_after": after_pct,
            "delta": after_pct - before_pct,
            "improved": after_pct > before_pct,
        }
