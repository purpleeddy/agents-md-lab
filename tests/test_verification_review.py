"""Offline contract checks for condition-blinded verification review transport."""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verification_budget as budget  # noqa: E402
import verification_review as review  # noqa: E402


class ReviewFixture:
    def batch(self, temporary, observed=True):
        root = Path(temporary) / "batch"
        root.mkdir()
        run = root / "run-01"
        run.mkdir()
        client = run / "verify_client.py"
        budget.write_client(client)
        scenario = "b-one"
        budget.copy_tree(budget.scenario_path(scenario, "seed"), run / "work")
        counter = run / "work" / "counter.py"
        counter.write_text(counter.read_text(encoding="utf-8") + "\n# fixture change\n", encoding="utf-8")
        meta = {
            "scenario": scenario,
            "condition": "candidate",
            "replicate": 1,
            "origin": budget.ORIGIN_LIVE,
            "verification_client": str(client),
            "verification_client_sha256": budget.sha256_file(client),
            "supervisor_sha256": budget.sha256_file(budget.__file__),
            "runner_sha256": budget.sha256_file(budget.__file__),
            "scorer_sha256": budget.sha256_file(budget.__file__),
            "manifest_sha256": budget.sha256_file(budget.scenario_path(scenario, "scenario.json")),
            "seed_sha256": budget.tree_hash(budget.scenario_path(scenario, "seed")),
            "evaluator_source_sha256": budget.sha256_file(budget.scenario_path(scenario, "acceptance.py")),
            "reported_cost_usd": 0.2,
            "reported_cost_status": "recorded",
            "returncode": 0,
            "timed_out": False,
            "owned_processes": {"agent_pgid_status": "exited"},
        }
        budget.write_json(run / "meta.json", meta)
        transcript = [{"type": "result", "result": "candidate report: changed /Users/alice/work/counter.py"}]
        events = []
        if observed:
            check = budget.documented_check_map(budget.load_manifest(scenario))["counter"]
            event = {
                "event_id": "event-1",
                "segment_index": 0,
                "request_argv": list(check["argv"]),
                "check_id": check["id"],
                "argv": list(check["argv"]),
                "source": "runner_parent",
                "executed": True,
                "returncode": 0,
                "timed_out": False,
                "output": "Ran 1 test\nOK\n",
                "output_sha256": budget.sha256_bytes(b"Ran 1 test\nOK\n"),
                "before_relevant_sha256": "a" * 64,
                "after_relevant_sha256": "b" * 64,
            }
            events.append(event)
            command = "python3 %s --socket %s -- %s" % (
                client, run / "verify.sock", " ".join(check["argv"])
            )
            transcript = [
                {"type": "assistant", "message": {"content": [{
                    "type": "tool_use", "id": "call-1", "name": "Bash", "input": {"command": command},
                }]}},
                {"type": "user", "message": {"content": [{
                    "type": "tool_result", "tool_use_id": "call-1",
                    "content": event["output"] + "[verification-event-ids=event-1]",
                }]}},
                transcript[0],
            ]
        (run / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in transcript) + "\n", encoding="utf-8")
        budget.write_json(run / "observations.json", {
            "provenance": "runner_parent_after_agent_exit",
            "supervisor_sha256": budget.sha256_file(budget.__file__),
            "supervisor_closed_cleanly": True,
            "events": events,
        })
        budget.write_json(run / "acceptance.json", {
            "status": "passed", "returncode": 0, "declared_test_count": 1, "expected_test_count": 1,
            "actual_test_count": 1, "final_tree_sha256": "c" * 64, "final_relevant_sha256": "d" * 64,
            "output": "acceptance output from /Users/alice/work", "output_sha256": "e" * 64,
        })
        budget.write_json(run / "baseline.json", {"baselines": [{
            "id": "baseline", "kind": "seed", "argv": ["python3", "-m", "unittest"],
            "capture_status": "recorded", "returncode": 1, "source_tree_sha256": "f" * 64,
            "output": "baseline at /Users/alice/work", "output_sha256": "0" * 64,
        }]})
        budget.write_json(root / "batch.json", {
            "origin": budget.ORIGIN_LIVE, "known_spent_usd": 0.2, "collection_cost_status": "recorded",
            "stopped": "cli_error", "rows": [],
        })
        budget.write_json(root / "plan.json", {"model": budget.DEFAULT_MODEL})
        budget.write_json(root / "collection-pins.json", {
            "precollection": {"cli_version": {"status": "recorded", "normalized": "2.1.263"}},
        })
        return root, run

    def response(self, packet, event_ids):
        reviews = []
        for row in packet["rows"]:
            reviews.append({
                "opaque_id": row["opaque_id"],
                "final_text_sha256": row["final_text_sha256"],
                "evidence_event_ids": event_ids,
                "annotations": {
                    name: {"value": "unknown", "rationale": "offline fixture"}
                    for name in review.ANNOTATIONS
                },
            })
        return {"reviews": reviews}

    def successful_invocation_record(self, packet, response):
        return {
            "origin": "label_blinded_model_review",
            "paid_calls_started": 1,
            "packet_sha256": hashlib.sha256(review.json_bytes(packet)).hexdigest(),
            "returncode": 0,
            "timed_out": False,
            "reported_cost_status": "recorded",
            "model_reported_status": "matched",
            "cli_version_reported_status": "matched",
            "cli_result_error": False,
            "response_status": "valid_unimported",
            "response_sha256": hashlib.sha256(review.json_bytes(response)).hexdigest(),
        }


class ReviewPacketTest(unittest.TestCase, ReviewFixture):
    def test_prepare_blinds_labels_and_redacts_known_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            batch, _run = self.batch(temporary)
            packet_dir = Path(temporary) / "packet"
            self.assertEqual(review.main(["prepare", str(batch), "--out", str(packet_dir)]), 0)
            packet = review.read_json(packet_dir / review.PACKET_NAME)
            mapping = review.read_json(packet_dir / review.MAPPING_NAME)
        encoded = json.dumps(packet)
        row = packet["rows"][0]
        self.assertNotIn('"condition"', encoded)
        self.assertNotIn("/Users/alice", encoded)
        self.assertIn("candidate report", row["final_text"])
        self.assertNotEqual(row["final_text_sha256"], row["final_text_display_sha256"])
        self.assertEqual(row["changed_paths"], ["counter.py"])
        self.assertEqual(mapping["rows"][0]["opaque_id"], row["opaque_id"])

    def test_import_requires_exact_membership_and_writes_only_valid_joinable_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            batch, run = self.batch(temporary)
            packet_dir = Path(temporary) / "packet"
            review.main(["prepare", str(batch), "--out", str(packet_dir)])
            packet = review.read_json(packet_dir / review.PACKET_NAME)
            response = self.response(packet, ["event-1"])
            invocation_dir = Path(temporary) / "invocation"
            invocation_dir.mkdir()
            response_path = invocation_dir / "review-response.private.json"
            review.write_json(response_path, response)
            review.write_json(
                invocation_dir / "review-run.private.json", self.successful_invocation_record(packet, response)
            )
            self.assertEqual(review.main(["import", "--packet", str(packet_dir), "--response", str(response_path)]), 0)
            stored = review.read_json(run / "review.json")
            response["reviews"].append(dict(response["reviews"][0]))
            review.write_json(response_path, response)
            with self.assertRaises(ValueError):
                review.main(["import", "--packet", str(packet_dir), "--response", str(response_path)])
        self.assertEqual(stored["provenance"], "label_blinded_model_review")
        self.assertEqual(stored["evidence_event_ids"], ["event-1"])

    def test_zero_event_unknown_review_is_retained_as_null_not_joined(self):
        with tempfile.TemporaryDirectory() as temporary:
            batch, run = self.batch(temporary, observed=False)
            packet_dir = Path(temporary) / "packet"
            review.main(["prepare", str(batch), "--out", str(packet_dir)])
            packet = review.read_json(packet_dir / review.PACKET_NAME)
            invocation_dir = Path(temporary) / "invocation"
            invocation_dir.mkdir()
            response_path = invocation_dir / "review-response.private.json"
            response = self.response(packet, [])
            review.write_json(response_path, response)
            review.write_json(
                invocation_dir / "review-run.private.json", self.successful_invocation_record(packet, response)
            )
            self.assertEqual(review.main(["import", "--packet", str(packet_dir), "--response", str(response_path)]), 0)
            report = review.read_json(packet_dir / "review-import.private.json")
        self.assertFalse((run / "review.json").exists())
        self.assertIsNone(report["rows"][0]["review"])

    def test_invoke_dry_run_starts_no_reviewer_or_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            batch, _run = self.batch(temporary)
            packet_dir = Path(temporary) / "packet"
            review.main(["prepare", str(batch), "--out", str(packet_dir)])
            stream = io.StringIO()
            with unittest.mock.patch.object(review.budget, "launch_agent") as launch, \
                 unittest.mock.patch.object(review.budget, "capture_cli_version") as version, \
                 contextlib.redirect_stdout(stream):
                self.assertEqual(review.main([
                    "invoke", str(batch), "--packet", str(packet_dir), "--dry-run",
                ]), 0)
        self.assertEqual(json.loads(stream.getvalue())["paid_calls_started"], 0)
        launch.assert_not_called()
        version.assert_not_called()

    def test_second_paid_attempt_is_refused_after_one_captured_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            batch, _run = self.batch(temporary)
            packet_dir = Path(temporary) / "packet"
            review.main(["prepare", str(batch), "--out", str(packet_dir)])
            packet = review.read_json(packet_dir / review.PACKET_NAME)
            response = self.response(packet, ["event-1"])
            stdout = "\n".join(json.dumps(event) for event in [
                {"type": "system", "subtype": "init", "model": budget.DEFAULT_MODEL, "claude_code_version": "2.1.263"},
                {
                    "type": "result", "subtype": "success", "is_error": False,
                    "terminal_reason": "completed", "result": json.dumps(response), "total_cost_usd": 0.1,
                },
            ]) + "\n"
            version = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            with unittest.mock.patch.object(review.budget, "capture_cli_version", return_value=version), \
                 unittest.mock.patch.object(
                     review.budget, "launch_agent", return_value=(stdout, "", 0, False, 99, "exited")
                 ) as launch:
                self.assertEqual(review.main([
                    "invoke", str(batch), "--packet", str(packet_dir), "--out", str(Path(temporary) / "first"),
                ]), 0)
                self.assertEqual(review.main([
                    "invoke", str(batch), "--packet", str(packet_dir), "--out", str(Path(temporary) / "second"),
                ]), 1)
        self.assertEqual(launch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
