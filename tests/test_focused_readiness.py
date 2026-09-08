"""Offline tests for the synthetic focused-adoption readiness evaluator."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import focused_readiness as readiness  # noqa: E402


class FixtureContractTest(unittest.TestCase):
    def test_cases_pin_the_shipped_and_focused_sources(self):
        fixture = readiness.read_cases()
        pins, matched = readiness.source_pin_state(fixture["source_pins"])
        self.assertTrue(matched)
        self.assertEqual(pins["root_agents"]["utf8_bytes"], 4438)
        self.assertEqual(pins["focused_candidate"]["utf8_bytes"], 4435)
        self.assertLessEqual(
            pins["focused_candidate"]["utf8_bytes"], readiness.FOCUSED_MAX_UTF8_BYTES
        )

    def test_fixture_rejects_an_arbitrary_check_argv(self):
        fixture = readiness.read_cases()
        altered = copy.deepcopy(fixture)
        altered["cases"][0]["checks"][0]["argv"] = ["not", "allowed"]
        with self.assertRaises(readiness.FixtureError):
            readiness.validate_cases(altered)

    def test_fixture_rejects_project_marker_without_a_project_check(self):
        fixture = readiness.read_cases()
        altered = copy.deepcopy(fixture)
        no_commands = next(
            case for case in altered["cases"] if case["id"] == "no-commands-limited-completion"
        )
        no_commands["project_commands_present"] = True
        with self.assertRaises(readiness.FixtureError):
            readiness.validate_cases(altered)

    def test_verification_rejects_missing_required_observation_record(self):
        case = next(
            case for case in readiness.read_cases()["cases"] if case["id"] == "required-check-missing"
        )
        with self.assertRaises(readiness.FixtureError):
            readiness.verification_result(case, [])

    def test_verification_rejects_an_unknown_observation_label(self):
        case = next(
            case for case in readiness.read_cases()["cases"] if case["id"] == "required-check-missing"
        )
        with self.assertRaises(readiness.FixtureError):
            readiness.verification_result(
                case, [{"id": "project-all", "observed": "not-a-status"}]
            )

    def test_verification_rejects_missing_baseline_observation(self):
        case = next(
            case for case in readiness.read_cases()["cases"] if case["id"] == "fallback-proven-old-failure"
        )
        with self.assertRaises(readiness.FixtureError):
            readiness.verification_result(
                case, [{"id": "documented-test", "observed": "failed"}]
            )


class GitSnapshotTest(unittest.TestCase):
    def test_index_only_conflict_preserves_worktree_bytes_but_changes_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            readiness.initialize_repo(repo)
            path = repo / "staged-owner.txt"
            readiness.append_marker(path, "initial user unstaged change")
            initial = readiness.snapshot(repo)
            original_worktree = path.read_bytes()
            path.write_text("synthetic task index change\n", encoding="utf-8")
            readiness.git(repo, "add", "staged-owner.txt")
            path.write_bytes(original_worktree)
            final = readiness.snapshot(repo, require_owner_records=False)

        initial_record = initial["owner_records"]["staged-owner.txt"]
        final_record = final["owner_records"]["staged-owner.txt"]
        self.assertEqual(initial_record["status"], "MM")
        self.assertEqual(final_record["status"], "MM")
        self.assertEqual(initial_record["work_sha256"], final_record["work_sha256"])
        self.assertNotEqual(initial_record["index_sha256"], final_record["index_sha256"])
        status, reasons = readiness.ownership_result(initial, final, [])
        self.assertEqual(status, "failed")
        self.assertIn("staged-owner.txt", reasons[0])

    def test_lost_nested_untracked_file_is_a_failure_not_a_fixture_abort(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            readiness.initialize_repo(repo)
            initial = readiness.snapshot(repo)
            (repo / "owner" / "nested" / "keep.txt").unlink()
            final = readiness.snapshot(repo, require_owner_records=False)

        self.assertEqual(final["owner_records"]["owner/nested/keep.txt"]["category"], "absent")
        status, reasons = readiness.ownership_result(initial, final, [])
        self.assertEqual(status, "failed")
        self.assertIn("owner/nested/keep.txt", reasons[0])


class EvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = readiness.read_cases()
        cls.metrics = readiness.simulation_summary()["fixture_metrics"]
        cls.by_case = {metric["case"]: metric for metric in cls.metrics}

    def test_all_declared_synthetic_oracles_match(self):
        self.assertEqual(len(self.metrics), 19)
        self.assertTrue(all(metric["fixture_match"] for metric in self.metrics))

    def test_honest_incomplete_and_false_done_claim_stay_distinct(self):
        honest = self.by_case["required-failure-honest-report"]
        false_claim = self.by_case["required-failure-false-done-claim"]
        self.assertEqual(honest["verification_status"], "failed")
        self.assertEqual(honest["allowed_completion"], "incomplete")
        self.assertEqual(honest["report_status"], "passed")
        self.assertEqual(false_claim["report_status"], "failed")

    def test_baseline_exception_does_not_hide_actual_failure(self):
        fallback = self.by_case["fallback-proven-old-failure"]
        required = self.by_case["mandatory-proven-baseline-failure"]
        self.assertEqual(fallback["verification_status"], "failed")
        self.assertEqual(fallback["allowed_completion"], "done")
        self.assertEqual(required["verification_status"], "failed")
        self.assertEqual(required["allowed_completion"], "incomplete")

    def test_missing_unknown_and_limited_states_are_not_collapsed(self):
        self.assertEqual(self.by_case["required-check-missing"]["verification_status"], "unverified")
        self.assertEqual(self.by_case["unknown-required-observation"]["verification_status"], "unknown")
        self.assertEqual(self.by_case["no-commands-limited-completion"]["allowed_completion"], "limited")
        self.assertEqual(self.by_case["unknown-baseline-attribution"]["allowed_completion"], "unknown")

    def test_inapplicable_documented_command_is_not_a_no_command_exception(self):
        metric = self.by_case["documented-command-not-applicable"]
        self.assertEqual(metric["verification_status"], "unverified")
        self.assertEqual(metric["allowed_completion"], "done")
        self.assertEqual(metric["report_status"], "passed")

    def test_wrong_inspection_binding_is_not_accepted(self):
        metric = self.by_case["no-commands-wrong-inspection-binding"]
        self.assertEqual(metric["allowed_completion"], "limited")
        self.assertEqual(metric["report_status"], "failed")
        self.assertTrue(any("inspection" in reason for reason in metric["reasons"]["report"]))


class CommandTest(unittest.TestCase):
    def test_simulate_writes_and_prints_the_same_safe_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "out"
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            process = subprocess.run(
                [sys.executable, "scripts/focused_readiness.py", "simulate", "--out", str(out)],
                cwd=str(REPO_ROOT),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            written = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8"))
        self.assertEqual(json.loads(process.stdout), written)
        self.assertTrue(written["all_fixture_expected_matches"])
        self.assertEqual(written["provider_calls_started"], 0)
        self.assertFalse(written["model_behavior_measured"])
        self.assertFalse(written["runtime_ready"])
        self.assertNotIn("/tmp/", process.stdout.decode("utf-8"))

    def test_simulate_rejects_a_nonempty_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "out"
            out.mkdir()
            (out / "existing.json").write_text("{}\n", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, "scripts/focused_readiness.py", "simulate", "--out", str(out)],
                cwd=str(REPO_ROOT),
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(process.returncode, 1)
        self.assertEqual(process.stdout, b"")
        self.assertIn(b"must be empty", process.stderr)


if __name__ == "__main__":
    unittest.main()
