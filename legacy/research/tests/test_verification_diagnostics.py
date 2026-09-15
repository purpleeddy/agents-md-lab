"""Offline contract tests for the read-only verification observation diagnostic."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verification_budget as budget  # noqa: E402
import verification_diagnostics as diagnostics  # noqa: E402


class DiagnosticFixture:
    def make(
        self, temporary, mode="normal", run_id="run-01", client_path="/retired/run/verify_client.py",
        direct_command="python3 -m unittest tests.test_counter | tee log",
    ):
        root = Path(temporary)
        collection = root / "collection"
        collection.mkdir()
        run = collection / run_id
        run.mkdir()
        scenario = "b-one"
        manifest = budget.load_manifest(scenario)
        check = budget.documented_check_map(manifest)["counter"]
        client = run / "verify_client.py"
        budget.write_client(client)
        source_hash = budget.sha256_file(budget.__file__)
        meta = {
            "scenario": scenario,
            "condition": "candidate",
            "replicate": 1,
            "verification_client": client_path,
            "verification_client_sha256": budget.sha256_file(client),
            "supervisor_sha256": source_hash,
            "scorer_sha256": source_hash,
            "manifest_sha256": budget.sha256_file(budget.scenario_path(scenario, "scenario.json")),
        }
        output = "fixture verification output\n"
        event = {
            "event_id": "event-1",
            "segment_index": 0,
            "request_argv": list(check["argv"]),
            "check_id": check["id"],
            "source": "runner_parent",
            "output": output,
            "output_sha256": budget.sha256_bytes(output.encode("utf-8")),
        }
        command = "python3 %s --socket /retired/socket -- %s" % (client_path, " ".join(check["argv"]))
        transcript = [
            {"type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": "call-1", "name": "Bash", "input": {"command": command},
            }]}},
            {"type": "user", "message": {"content": [{
                "type": "tool_result", "tool_use_id": "call-1", "content": output + "[verification-event-ids=event-1]",
            }]}},
        ]
        coverage = "failed"
        evidence = "observed"
        if mode in ("direct", "both"):
            transcript.append({"type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": "direct", "name": "Bash",
                "input": {"command": direct_command},
            }]}})
            coverage = evidence = "unverified"
        if mode in ("linkage", "both"):
            transcript[0]["message"]["content"][0]["input"]["command"] += " 2>&1"
            coverage = evidence = "unverified"
        if mode == "missing-marker":
            transcript[1]["message"]["content"][0]["content"] = output
            coverage = evidence = "unverified"
        if mode == "missing-output-binding":
            transcript[1]["message"]["content"][0]["content"] = "[verification-event-ids=event-1]"
            coverage = evidence = "unverified"
        if mode == "missing-result":
            transcript = transcript[:1]
            coverage = evidence = "unverified"
        if mode == "malformed-transcript":
            transcript = None
        metrics = {
            "verification_evidence_status": evidence,
            "required_verification_coverage": {"status": coverage},
        }
        ledger = {
            "provenance": "runner_parent_after_agent_exit",
            "supervisor_sha256": source_hash,
            "supervisor_closed_cleanly": True,
            "events": [event],
        }
        budget.write_json(run / "meta.json", meta)
        budget.write_json(run / "metrics.json", metrics)
        budget.write_json(run / "observations.json", ledger)
        if transcript is None:
            (run / "transcript.jsonl").write_text("{not-json}\n", encoding="utf-8")
        else:
            (run / "transcript.jsonl").write_text(
                "\n".join(json.dumps(item) for item in transcript) + "\n", encoding="utf-8"
            )
        publication = {
            "schema": diagnostics.PUBLIC_SCHEMA,
            "runs": [{
                "run_id": run_id,
                "scenario": scenario,
                "condition": "candidate",
                "replicate": 1,
                "metrics": metrics,
                "source_pins": {
                    "manifest_sha256": meta["manifest_sha256"],
                    "runner_sha256": source_hash,
                    "scorer_sha256": source_hash,
                },
                "raw_artifact_sha256": {
                    name: budget.sha256_file(run / name) for name in diagnostics.RAW_FILENAMES
                },
            }],
        }
        publication_path = root / "publication.json"
        budget.write_json(publication_path, publication)
        return collection, publication_path, run, publication

    def report(self, collection, publication):
        return diagnostics.diagnose(collection, publication)


class DiagnosticTest(unittest.TestCase, DiagnosticFixture):
    def test_normal_row_keeps_observed_status_without_dereferencing_retired_client_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(temporary)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        self.assertEqual(report["runs"][0]["category"], "normal")
        self.assertEqual(report["runs"][0]["stored_statuses"]["verification_evidence_status"], "observed")
        self.assertNotIn("/retired", json.dumps(report))
        self.assertNotIn("event-1", json.dumps(report))
        self.assertNotIn("fixture verification output", json.dumps(report))
        self.assertNotIn("call-1", json.dumps(report))

    def test_direct_parser_rejected_pipe_is_explanatory_not_execution_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(temporary, "direct")
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        self.assertEqual(report["runs"][0]["category"], "unsupported_shell_structure")
        self.assertEqual(
            report["runs"][0]["direct_observations"][0]["forms"],
            ["parser_rejected_pipe_token_or_character"],
        )
        self.assertEqual(report["runs"][0]["interpretation"], "explanatory_only_preserves_stored_outcome")

    def test_direct_redirection_is_a_parser_character_category(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(
                temporary, "direct", direct_command="python3 -m unittest tests.test_counter > log"
            )
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        self.assertEqual(
            report["runs"][0]["direct_observations"][0]["forms"],
            ["parser_rejected_redirection_token_or_character"],
        )

    def test_endpoint_transport_tail_explains_raw_argv_mismatch_without_upgrade(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(temporary, "linkage")
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        event = report["runs"][0]["events"][0]
        self.assertEqual(report["runs"][0]["category"], "endpoint_linkage")
        self.assertEqual(event["failure_reasons"], ["raw_argv_mismatch"])
        self.assertEqual(event["syntactic_suffix_explains_strict_mismatch"], ["parser_rejected_redirection_token_or_character"])

    def test_mixed_direct_and_linkage_causes_are_kept_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(temporary, "both")
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        self.assertEqual(report["runs"][0]["category"], "unsupported_shell_and_endpoint_linkage")

    def test_missing_marker_and_tool_result_stay_linkage_uncertainty(self):
        for mode, reason in (
            ("missing-marker", "missing_event_marker"),
            ("missing-result", "missing_event_marker"),
            ("missing-output-binding", "output_binding_missing"),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                collection, publication, _run, _ = self.make(temporary, mode)
                report, status = self.report(collection, publication)
            self.assertEqual(status, 0)
            self.assertEqual(report["runs"][0]["events"][0]["failure_reasons"], [reason])

    def test_malformed_transcript_is_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, _run, _ = self.make(temporary, "malformed-transcript")
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertEqual(report["diagnostic_status"], "unavailable")
        self.assertEqual(report["errors"][0]["code"], "malformed_required_archive_artifact")

    def test_missing_ledger_is_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            (run / "observations.json").unlink()
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertIn("unsafe_or_missing_raw_artifact", [item["code"] for item in report["errors"]])

    def test_semantically_malformed_transcript_is_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            events = [json.loads(line) for line in (run / "transcript.jsonl").read_text(encoding="utf-8").splitlines()]
            events[0]["message"]["content"][0]["input"] = "not-an-input-object"
            (run / "transcript.jsonl").write_text(
                "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8"
            )
            publication_data = budget.read_json(publication)
            publication_data["runs"][0]["raw_artifact_sha256"]["transcript.jsonl"] = budget.sha256_file(run / "transcript.jsonl")
            budget.write_json(publication, publication_data)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertIn("malformed_bash_call", [item["code"] for item in report["errors"]])

    def test_arbitrary_matching_status_strings_are_not_emitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            metrics = budget.read_json(run / "metrics.json")
            metrics["verification_evidence_status"] = "private-status-token"
            metrics["required_verification_coverage"]["status"] = "private-status-token"
            budget.write_json(run / "metrics.json", metrics)
            publication_data = budget.read_json(publication)
            publication_data["runs"][0]["metrics"] = metrics
            publication_data["runs"][0]["raw_artifact_sha256"]["metrics.json"] = budget.sha256_file(run / "metrics.json")
            budget.write_json(publication, publication_data)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertNotIn("private-status-token", json.dumps(report))

    def test_tampered_hash_or_frozen_source_is_unavailable(self):
        for target in ("publication-hash", "source-hash", "client-hash"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                collection, publication_path, run, publication = self.make(temporary)
                if target == "publication-hash":
                    publication["runs"][0]["raw_artifact_sha256"]["metrics.json"] = "0" * 64
                    budget.write_json(publication_path, publication)
                elif target == "source-hash":
                    meta = budget.read_json(run / "meta.json")
                    meta["supervisor_sha256"] = "0" * 64
                    budget.write_json(run / "meta.json", meta)
                    publication["runs"][0]["raw_artifact_sha256"]["meta.json"] = budget.sha256_file(run / "meta.json")
                    budget.write_json(publication_path, publication)
                else:
                    client = run / "verify_client.py"
                    client.write_text("tampered\n", encoding="utf-8")
                    publication["runs"][0]["raw_artifact_sha256"]["verify_client.py"] = budget.sha256_file(client)
                    budget.write_json(publication_path, publication)
                report, status = self.report(collection, publication_path)
            self.assertEqual(status, 1)
            self.assertEqual(report["diagnostic_status"], "unavailable")

    def test_duplicate_and_traversal_public_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication_path, _run, publication = self.make(temporary)
            duplicate = dict(publication["runs"][0])
            publication["runs"].append(duplicate)
            budget.write_json(publication_path, publication)
            report, status = self.report(collection, publication_path)
            self.assertEqual(status, 1)
            self.assertIn("duplicate_publication_run_id", [item["code"] for item in report["errors"]])
            publication["runs"] = [dict(duplicate, run_id="../escape")]
            budget.write_json(publication_path, publication)
            report, status = self.report(collection, publication_path)
        self.assertEqual(status, 1)
        self.assertIn("unsafe_publication_run_id", [item["code"] for item in report["errors"]])

    def test_duplicate_ledger_event_id_is_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            ledger = budget.read_json(run / "observations.json")
            ledger["events"].append(dict(ledger["events"][0], segment_index=1))
            budget.write_json(run / "observations.json", ledger)
            publication_data = budget.read_json(publication)
            publication_data["runs"][0]["raw_artifact_sha256"]["observations.json"] = budget.sha256_file(run / "observations.json")
            budget.write_json(publication, publication_data)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertIn("duplicate_or_invalid_event_id", [item["code"] for item in report["errors"]])

    def test_symlink_escape_is_rejected_without_opening_external_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            external = Path(temporary) / "external.json"
            external.write_text("{}\n", encoding="utf-8")
            (run / "metrics.json").unlink()
            (run / "metrics.json").symlink_to(external)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertIn("unsafe_or_missing_raw_artifact", [item["code"] for item in report["errors"]])

    def test_symlinked_run_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            external = Path(temporary) / "external-run"
            run.rename(external)
            run.symlink_to(external, target_is_directory=True)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 1)
        self.assertIn("unsafe_archive_run_entry", [item["code"] for item in report["errors"]])

    def test_quoted_literal_metacharacter_is_described_as_parser_rejected_character_only(self):
        self.assertEqual(
            diagnostics.parser_rejected_forms("printf '%s' 'a|b'"),
            ["parser_rejected_pipe_token_or_character"],
        )

    def test_compound_endpoint_events_use_distinct_segment_slots(self):
        request = ["python3", "-m", "unittest", "tests.test_counter", "&&", "python3", "-m", "unittest", "tests.test_counter"]
        client = "/retired/run/verify_client.py"
        calls = [{
            "command": "python3 %s --socket /retired/socket -- %s" % (client, " ".join(request)),
            "result": {"text": "output\n[verification-event-ids=one,two]"},
        }]
        events = [
            {"event_id": "one", "segment_index": 0, "request_argv": request, "output": "output", "output_sha256": "a" * 64},
            {"event_id": "two", "segment_index": 1, "request_argv": request, "output": "output", "output_sha256": "b" * 64},
        ]
        records = diagnostics.event_records(calls, events, client)
        self.assertEqual([record["strict_match"] for record in records], ["matched", "matched"])

    def test_compound_endpoint_events_cannot_reuse_the_same_segment_slot(self):
        request = ["python3", "-m", "unittest", "tests.test_counter", "&&", "python3", "-m", "unittest", "tests.test_counter"]
        client = "/retired/run/verify_client.py"
        calls = [{
            "command": "python3 %s --socket /retired/socket -- %s" % (client, " ".join(request)),
            "result": {"text": "output\n[verification-event-ids=one,two]"},
        }]
        events = [
            {"event_id": "one", "segment_index": 0, "request_argv": request, "output": "output", "output_sha256": "a" * 64},
            {"event_id": "two", "segment_index": 0, "request_argv": request, "output": "output", "output_sha256": "b" * 64},
        ]
        records = diagnostics.event_records(calls, events, client)
        self.assertEqual(records[1]["failure_reasons"], ["strict_endpoint_shape_mismatch"])

    def test_unrelated_wrong_request_has_no_suffix_explanation(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary, "linkage")
            transcript = (run / "transcript.jsonl").read_text(encoding="utf-8").replace("2>&1", "different")
            (run / "transcript.jsonl").write_text(transcript, encoding="utf-8")
            publication_data = budget.read_json(publication)
            publication_data["runs"][0]["raw_artifact_sha256"]["transcript.jsonl"] = budget.sha256_file(run / "transcript.jsonl")
            budget.write_json(publication, publication_data)
            report, status = self.report(collection, publication)
        self.assertEqual(status, 0)
        event = report["runs"][0]["events"][0]
        self.assertEqual(event["failure_reasons"], ["raw_argv_mismatch"])
        self.assertEqual(event["syntactic_suffix_explains_strict_mismatch"], [])

    def test_cli_writes_only_stdout_and_never_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection, publication, run, _ = self.make(temporary)
            before = {name: (run / name).read_bytes() for name in diagnostics.RAW_FILENAMES}
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = diagnostics.main(["--collection", str(collection), "--publication", str(publication)])
            after = {name: (run / name).read_bytes() for name in diagnostics.RAW_FILENAMES}
        self.assertEqual(status, 0)
        self.assertEqual(before, after)
        self.assertTrue(json.loads(stdout.getvalue())["read_only"])


if __name__ == "__main__":
    unittest.main()
