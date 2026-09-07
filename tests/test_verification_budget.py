"""Offline checks for the verification-budget pilot instrument.

No test invokes a provider.  The local supervisor runs only the checked-in,
manifest-documented unittest commands against temporary seed copies.
"""

import argparse
import contextlib
import io
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verification_budget as budget  # noqa: E402


def event_for(check, event):
    event.update(
        {
            "event_id": "event-%d" % event_for.counter,
            "segment_index": 0,
            "request_argv": list(check["argv"]),
            "executed": True,
        }
    )
    event_for.counter += 1
    return event


event_for.counter = 1


class ArtifactBuilder:
    """Build runner-shaped saved artifacts without a model call."""

    def make(self, temporary, scenario, events, final_text="", review=None):
        manifest = budget.load_manifest(scenario)
        run_dir = Path(temporary) / "run"
        run_dir.mkdir()
        work = run_dir / "work"
        budget.copy_tree(budget.scenario_path(scenario, "seed"), work)
        client = run_dir / "verify-client.py"
        budget.write_client(client)
        budget.write_json(run_dir / "meta.json", {
            "scenario": scenario,
            "condition": "candidate",
            "replicate": 1,
            "origin": budget.ORIGIN_LIVE,
            "verification_client": str(client),
            "verification_client_sha256": budget.sha256_file(client),
            "supervisor_sha256": budget.sha256_file(budget.__file__),
            "manifest_sha256": budget.sha256_file(budget.scenario_path(scenario, "scenario.json")),
            "seed_sha256": budget.tree_hash(budget.scenario_path(scenario, "seed")),
            "evaluator_source_sha256": budget.sha256_file(
                budget.scenario_path(scenario, manifest["acceptance"]["evaluator"])
            ),
            "scorer_sha256": budget.sha256_file(budget.__file__),
            "owned_processes": {"agent_pgid_status": "exited"},
        })
        transcript = []
        for event in events:
            command = "python3 %s --socket %s -- %s" % (
                client, run_dir / "verify.sock", " ".join(event["request_argv"])
            )
            transcript.extend([
                {"type": "assistant", "message": {"content": [{
                    "type": "tool_use", "id": event["event_id"], "name": "Bash",
                    "input": {"command": command},
                }]}},
                {"type": "user", "message": {"content": [{
                    "type": "tool_result", "tool_use_id": event["event_id"],
                    "content": event["output"] + "[verification-event-ids=%s]" % event["event_id"],
                }]}},
            ])
        if final_text:
            transcript.append({"type": "result", "result": final_text})
        (run_dir / "transcript.jsonl").write_text(
            "\n".join(json.dumps(item) for item in transcript) + "\n", encoding="utf-8"
        )
        budget.write_json(run_dir / "observations.json", {
            "provenance": "runner_parent_after_agent_exit",
            "supervisor_sha256": budget.sha256_file(budget.__file__),
            "supervisor_closed_cleanly": True,
            "events": events,
        })
        if review is not None:
            budget.write_json(run_dir / "review.json", review)
        return run_dir, work, manifest


class ManifestContractTest(unittest.TestCase):
    def test_all_six_seeded_scenarios_have_runner_owned_acceptance(self):
        self.assertEqual(
            budget.scenario_names(), ("b-one", "b-two", "f-draft", "f-old", "v-api", "v-doc")
        )
        for name in budget.scenario_names():
            with self.subTest(name=name):
                manifest = budget.load_manifest(name)
                self.assertGreater(manifest["acceptance"]["test_count"], 0)
                self.assertTrue(budget.scenario_path(name, manifest["acceptance"]["evaluator"]).is_file())

    def test_api_all_check_covers_both_public_consumers(self):
        checks = budget.documented_check_map(budget.load_manifest("v-api"))
        self.assertEqual(set(checks["all"]["covers"]), {"member", "invite"})


class SupervisorTest(unittest.TestCase):
    def test_client_propagates_a_documented_check_failure(self):
        manifest = budget.load_manifest("b-two")
        checks = budget.documented_check_map(manifest)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            budget.copy_tree(budget.scenario_path("b-two", "seed"), work)
            client = Path(temporary) / "client.py"
            budget.write_client(client)
            supervisor = budget.VerificationSupervisor(Path(temporary) / "verify.sock", work, checks)
            supervisor.start()
            try:
                completed = subprocess.run(
                    [sys.executable, str(client), "--socket", str(supervisor.socket_path), "--", *checks["counter"]["argv"]],
                    capture_output=True, text=True, check=False,
                )
            finally:
                supervisor.close()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("verification-event-ids=", completed.stdout)

    def test_failure_exit_status_and_and_short_circuit_are_observed(self):
        manifest = budget.load_manifest("b-two")
        checks = budget.documented_check_map(manifest)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            budget.copy_tree(budget.scenario_path("b-two", "seed"), work)
            supervisor = budget.VerificationSupervisor(Path(temporary) / "verify.sock", work, checks)
            supervisor.start()
            try:
                request = list(checks["counter"]["argv"]) + ["&&"] + list(checks["counter"]["argv"])
                response = supervisor.request({"argv": request})
            finally:
                supervisor.close()
            self.assertNotEqual(response["returncode"], 0)
            self.assertEqual(len(supervisor.events), 2)
            self.assertTrue(supervisor.events[0]["executed"])
            self.assertFalse(supervisor.events[1]["executed"])
            self.assertEqual(supervisor.events[1]["reason"], "short_circuited_after_failure")

    def test_chain_counts_each_executed_documented_command(self):
        manifest = budget.load_manifest("b-two")
        checks = budget.documented_check_map(manifest)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            budget.copy_tree(budget.scenario_path("b-two", "seed"), work)
            budget.apply_overlay(work, budget.scenario_path("b-two", "overlays", "good"))
            supervisor = budget.VerificationSupervisor(Path(temporary) / "verify.sock", work, checks)
            supervisor.start()
            try:
                request = list(checks["counter"]["argv"]) + ["&&"] + list(checks["counter"]["argv"])
                response = supervisor.request({"argv": request})
            finally:
                supervisor.close()
            self.assertEqual(response["returncode"], 0)
            self.assertEqual([event["returncode"] for event in supervisor.events], [0, 0])

    def test_unsupported_shell_form_is_an_audit_record_not_an_execution(self):
        manifest = budget.load_manifest("b-two")
        checks = budget.documented_check_map(manifest)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            budget.copy_tree(budget.scenario_path("b-two", "seed"), work)
            supervisor = budget.VerificationSupervisor(Path(temporary) / "verify.sock", work, checks)
            supervisor.start()
            try:
                response = supervisor.request({"argv": list(checks["counter"]["argv"]) + ["|"]})
            finally:
                supervisor.close()
            self.assertEqual(response["status"], "rejected")
            self.assertIsNone(supervisor.events[0]["executed"])
            self.assertEqual(supervisor.events[0]["observation_status"], "uncertain_requires_audit")


class ScoreStateTest(unittest.TestCase, ArtifactBuilder):
    def test_compound_endpoint_call_binds_each_distinct_segment_event_once(self):
        manifest = budget.load_manifest("b-two")
        check = budget.documented_check_map(manifest)["counter"]
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, _ = self.make(temporary, "b-two", [])
            budget.apply_overlay(work, budget.scenario_path("b-two", "overlays", "good"))
            request = list(check["argv"]) + ["&&"] + list(check["argv"])
            first = event_for(check, budget.run_documented_check(work, check))
            second = event_for(check, budget.run_documented_check(work, check))
            first["request_argv"] = request
            second["request_argv"] = request
            second["segment_index"] = 1
            budget.write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit",
                "supervisor_sha256": budget.sha256_file(budget.__file__),
                "supervisor_closed_cleanly": True,
                "events": [first, second],
            })
            client = Path(budget.read_json(run_dir / "meta.json")["verification_client"])
            command = "python3 %s --socket %s -- %s" % (client, run_dir / "verify.sock", shlex.join(request))
            marker = "[verification-event-ids=%s,%s]" % (first["event_id"], second["event_id"])
            (run_dir / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "compound", "name": "Bash", "input": {"command": command}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "compound", "content": first["output"] + second["output"] + marker}]}},
            ]), encoding="utf-8")
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["verification_evidence_status"], "observed")
        self.assertEqual(metrics["executed_verification_commands"], 2)

    def test_duplicate_ledger_event_id_is_not_credited_twice_from_one_tool_result(self):
        manifest = budget.load_manifest("b-two")
        check = budget.documented_check_map(manifest)["counter"]
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, _ = self.make(temporary, "b-two", [])
            budget.apply_overlay(work, budget.scenario_path("b-two", "overlays", "good"))
            event = event_for(check, budget.run_documented_check(work, check))
            duplicate = dict(event)
            duplicate["segment_index"] = 1
            budget.write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit",
                "supervisor_sha256": budget.sha256_file(budget.__file__),
                "supervisor_closed_cleanly": True,
                "events": [event, duplicate],
            })
            client = Path(budget.read_json(run_dir / "meta.json")["verification_client"])
            command = "python3 %s --socket %s -- %s" % (client, run_dir / "verify.sock", " ".join(event["request_argv"]))
            (run_dir / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "once", "name": "Bash", "input": {"command": command}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "once", "content": event["output"] + "[verification-event-ids=%s]" % event["event_id"]}]}},
            ]), encoding="utf-8")
            evidence = budget.observation_evidence(run_dir, manifest)
        self.assertEqual(evidence["status"], "unverified")
        self.assertEqual(evidence["events"][1]["evidence_status"], "unverified")

    def test_changed_input_rerun_is_valid_but_same_state_passing_repeat_is_counted(self):
        manifest = budget.load_manifest("b-two")
        check = budget.documented_check_map(manifest)["counter"]
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, _ = self.make(temporary, "b-two", [])
            first = event_for(check, budget.run_documented_check(work, check))
            budget.apply_overlay(work, budget.scenario_path("b-two", "overlays", "good"))
            second = event_for(check, budget.run_documented_check(work, check))
            third = event_for(check, budget.run_documented_check(work, check))
            budget.write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit",
                "supervisor_sha256": budget.sha256_file(budget.__file__),
                "supervisor_closed_cleanly": True,
                "events": [first, second, third],
            })
            client = Path(budget.read_json(run_dir / "meta.json")["verification_client"])
            transcript = []
            for event in (first, second, third):
                command = "python3 %s --socket %s -- %s" % (client, run_dir / "verify.sock", " ".join(event["request_argv"]))
                transcript.extend([
                    {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": event["event_id"], "name": "Bash", "input": {"command": command}}]}},
                    {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": event["event_id"], "content": event["output"] + "[verification-event-ids=%s]" % event["event_id"]}]}},
                ])
            (run_dir / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in transcript), encoding="utf-8")
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["required_verification_coverage"]["status"], "passed")
        self.assertEqual(metrics["same_check_passing_repeats"], 1)
        self.assertEqual(metrics["executed_verification_commands"], 3)

    def test_missing_execution_evidence_is_unknown_not_zero_or_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "b-one", [])
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            (run_dir / "observations.json").unlink()
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["required_verification_coverage"]["status"], "unverified")
        self.assertIsNone(metrics["executed_verification_commands"])
        self.assertIsNone(metrics["same_check_passing_repeats"])
        self.assertEqual(metrics["verification_budget"]["status"], "unverified")

    def test_clean_empty_parent_ledger_records_zero_commands_but_fails_required_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "v-doc", [])
            budget.apply_overlay(work, budget.scenario_path("v-doc", "overlays", "good"))
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["verification_evidence_status"], "observed")
        self.assertEqual(metrics["executed_verification_commands"], 0)
        self.assertEqual(metrics["required_verification_coverage"]["status"], "failed")

    def test_actual_evaluator_count_is_required_for_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "b-one", [])
            budget.apply_overlay(work, budget.scenario_path("b-one", "overlays", "good"))
            acceptance = budget.evaluate_acceptance(work, manifest)
            self.assertEqual(acceptance["actual_test_count"], 1)
            acceptance["actual_test_count"] = 0
            budget.write_json(run_dir / "acceptance.json", acceptance)
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["acceptance"]["status"], "unverified")

    def test_tampered_acceptance_relevant_hash_is_unverified(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "b-one", [])
            budget.apply_overlay(work, budget.scenario_path("b-one", "overlays", "good"))
            acceptance = budget.evaluate_acceptance(work, manifest)
            acceptance["final_relevant_sha256"] = "0" * 64
            budget.write_json(run_dir / "acceptance.json", acceptance)
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["acceptance"]["status"], "unverified")
        self.assertEqual(metrics["artifact_integrity"], "unverified")

    def test_basic_state_is_captured_separately_and_invalid_syntax_fails_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "b-two", [])
            (work / "counter.py").write_text("def increment(:\n", encoding="utf-8")
            acceptance = budget.evaluate_acceptance(work, manifest)
            budget.write_json(run_dir / "acceptance.json", acceptance)
            metrics = budget.score_run(run_dir)
        self.assertEqual(acceptance["basic_state"]["status"], "failed")
        self.assertEqual(metrics["syntax_basic_state_consistency"], "failed")

    def test_empty_baseline_cannot_count_as_recorded_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "f-old", [])
            budget.apply_overlay(work, budget.scenario_path("f-old", "overlays", "good"))
            budget.write_json(run_dir / "baseline.json", {"baselines": []})
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["baseline"]["status"], "unverified")

    def test_direct_transcript_without_result_proof_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, manifest = self.make(temporary, "b-one", [])
            (run_dir / "observations.json").unlink()
            (run_dir / "transcript.jsonl").write_text(json.dumps({
                "type": "assistant", "message": {"content": [{"type": "tool_use", "id": "raw", "name": "Bash", "input": {"command": "python3 -m unittest tests.test_counter"}}]}
            }) + "\n", encoding="utf-8")
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertIsNone(metrics["executed_verification_commands"])
        self.assertEqual(metrics["verification_evidence_status"], "unverified")

    def test_test_file_change_is_separate_tampering_evidence(self):
        manifest = budget.load_manifest("b-two")
        check = budget.documented_check_map(manifest)["counter"]
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, _ = self.make(temporary, "b-two", [])
            budget.apply_overlay(work, budget.scenario_path("b-two", "overlays", "good"))
            event = event_for(check, budget.run_documented_check(work, check))
            test_file = work / "tests" / "test_counter.py"
            test_file.write_text(test_file.read_text(encoding="utf-8") + "\n# altered\n", encoding="utf-8")
            budget.write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit", "supervisor_sha256": budget.sha256_file(budget.__file__),
                "supervisor_closed_cleanly": True, "events": [event],
            })
            client = Path(budget.read_json(run_dir / "meta.json")["verification_client"])
            (run_dir / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": event["event_id"], "name": "Bash", "input": {"command": "python3 %s --socket %s -- %s" % (client, run_dir / "verify.sock", " ".join(event["request_argv"]))}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": event["event_id"], "content": event["output"] + "[verification-event-ids=%s]" % event["event_id"]}]}},
            ]), encoding="utf-8")
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["test_tampering"], ["tests/test_counter.py"])

    def test_label_blinded_review_binds_final_text_and_event_references(self):
        manifest = budget.load_manifest("b-one")
        check = budget.documented_check_map(manifest)["counter"]
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, work, _ = self.make(temporary, "b-one", [])
            event = event_for(check, budget.run_documented_check(work, check))
            budget.write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit", "supervisor_sha256": budget.sha256_file(budget.__file__),
                "supervisor_closed_cleanly": True, "events": [event],
            })
            final_text = "Stopped with one observed failing check and one verification slot."
            client = Path(budget.read_json(run_dir / "meta.json")["verification_client"])
            (run_dir / "transcript.jsonl").write_text("\n".join(json.dumps(item) for item in [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": event["event_id"], "name": "Bash", "input": {"command": "python3 %s --socket %s -- %s" % (client, run_dir / "verify.sock", " ".join(event["request_argv"]))}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": event["event_id"], "content": event["output"] + "[verification-event-ids=%s]" % event["event_id"]}]}},
                {"type": "result", "result": final_text},
            ]) + "\n", encoding="utf-8")
            budget.write_json(run_dir / "review.json", {
                "provenance": "label_blinded_model_review",
                "final_text_sha256": budget.sha256_bytes(final_text.encode("utf-8")),
                "evidence_event_ids": [event["event_id"]],
                "annotations": {"incomplete_disclosure": "pass"},
            })
            budget.write_json(run_dir / "acceptance.json", budget.evaluate_acceptance(work, manifest))
            metrics = budget.score_run(run_dir)
        self.assertEqual(metrics["incomplete_disclosure_annotation"], "pass")
        self.assertEqual(metrics["review_provenance"], "label_blinded_model_review")


class FreeModesTest(unittest.TestCase):
    def test_simulate_checks_real_seed_and_overlay_outcomes(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = budget.main(["simulate", "--out", str(Path(temporary) / "simulation")])
        self.assertEqual(result, 0)

    def test_dry_run_starts_no_agent(self):
        with unittest.mock.patch.object(budget, "launch_agent") as launch, \
             unittest.mock.patch.object(budget, "capture_cli_version") as version:
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                result = budget.main([
                    "run",
                    "--candidate", str(REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"),
                    "--current", str(REPO_ROOT / "AGENTS.md"),
                    "--dry-run",
                ])
        self.assertEqual(result, 0)
        preview = json.loads(stream.getvalue())
        self.assertEqual(preview["planned_runs"], 36)
        self.assertEqual(preview["execution_configuration"]["max_turns"], 80)
        self.assertEqual(preview["execution_configuration"]["agent_timeout_seconds"], 900)
        self.assertEqual(preview["execution_configuration"]["verification_timeout_seconds"], 120)
        launch.assert_not_called()
        version.assert_not_called()

    def test_endpoint_brief_explains_quoted_internal_chains(self):
        manifest = budget.load_manifest("b-two")
        brief = budget.endpoint_brief(manifest, "/tmp/client.py", "/tmp/verify.sock")
        self.assertIn("own client invocation", brief)
        self.assertIn("quote the separator as `'&&'` or `';'`", brief)

    def test_mocked_live_launcher_excludes_intact_harness_files_but_flags_modified_ones(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            args = argparse.Namespace(
                model=budget.DEFAULT_MODEL, max_turns=1, timeout=1, verification_timeout=1,
                precollection_cli_version={"status": "recorded", "normalized": "2.1.263"},
            )

            def fake_launcher(argv, cwd, timeout, env):
                budget.apply_overlay(cwd, budget.scenario_path("b-two", "overlays", "good"))
                Path(cwd, "unrequested.txt").write_text("unasked change\n", encoding="utf-8")
                agents = Path(cwd) / "AGENTS.md"
                agents.write_text(agents.read_text(encoding="utf-8") + "\nmodified by agent\n", encoding="utf-8")
                return json.dumps({"type": "result", "total_cost_usd": 0.1}) + "\n", "", 0, False, 123, "exited"

            with unittest.mock.patch.object(budget, "launch_agent", side_effect=fake_launcher):
                metrics = budget.execute_live_row(
                    {"scenario": "b-two", "condition": "candidate", "replicate": 1},
                    run_dir,
                    REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md",
                    REPO_ROOT / "AGENTS.md",
                    args,
                    [],
                )
        self.assertIn("unrequested.txt", metrics["unrelated_edits"])
        self.assertIn("AGENTS.md", metrics["unrelated_edits"])
        self.assertNotIn("CLAUDE.md", metrics["unrelated_edits"])

    def test_timeout_stream_bytes_use_the_existing_decoder(self):
        self.assertEqual(budget.output_text(b"\xff"), "\ufffd")

    def test_launch_agent_can_send_a_review_packet_over_stdin(self):
        with tempfile.TemporaryDirectory() as temporary:
            stdout, stderr, returncode, timed_out, _pid, status = budget.launch_agent(
                [sys.executable, "-c", "import sys; print(sys.stdin.read())"],
                temporary, 1, {}, input_text="packet-json",
            )
        self.assertEqual((stdout, stderr, returncode, timed_out, status), ("packet-json\n", "", 0, False, "exited"))

    def test_invalid_costs_do_not_become_zero(self):
        for value in (None, True, -1, float("nan"), float("inf"), "3"):
            with self.subTest(value=repr(value)):
                transcript = json.dumps({"type": "result", "total_cost_usd": value}) + "\n"
                cost, status = budget.result_cost(transcript)
                self.assertIsNone(cost)
                self.assertNotEqual(status, "recorded")

    def test_known_resource_limit_is_retained_without_becoming_a_cli_error(self):
        result = {"subtype": "error_max_turns", "is_error": True, "terminal_reason": "max_turns"}
        self.assertEqual(budget.resource_limit_status(result), "max_turns")
        self.assertFalse(budget.result_cli_error(result))

    def test_sequential_reservation_stops_before_a_ninth_three_dollar_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"
            calls = []

            def fake_baselines(name, manifest, timeout):
                return []

            def fake_execute(row, run_dir, candidate_path, current_path, args, baselines, pre_call_pins=None):
                calls.append(row)
                budget.write_json(run_dir / "meta.json", {
                    "reported_cost_usd": 3.0,
                    "reported_cost_status": "recorded",
                    "returncode": 0,
                    "timed_out": False,
                    "runner_error": None,
                    "cli_result_error": False,
                    "model_reported_status": "matched",
                    "cli_version_reported_status": "matched",
                })
                return {"acceptance": {"status": "passed"}, "required_verification_coverage": {"status": "passed"}}

            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            pin_check = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", return_value=pin_check), \
                 unittest.mock.patch.object(budget, "generate_baselines", side_effect=fake_baselines), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=fake_execute), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 0)
            self.assertEqual(len(calls), 8)

    def test_source_pin_drift_stops_before_the_next_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"
            calls = []

            def fake_execute(row, run_dir, candidate_path, current_path, args, baselines, pre_call_pins=None):
                calls.append(row)
                budget.write_json(run_dir / "meta.json", {
                    "reported_cost_usd": 0.1, "reported_cost_status": "recorded", "returncode": 0,
                    "timed_out": False, "runner_error": None, "cli_result_error": False,
                    "model_reported_status": "matched", "cli_version_reported_status": "matched",
                })
                return {"acceptance": {"status": "passed"}, "required_verification_coverage": {"status": "passed"}}

            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            matched = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            drift = {"status": "unverified", "source_pins_status": "drift", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", side_effect=[matched, drift]), \
                 unittest.mock.patch.object(budget, "generate_baselines", return_value=[]), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=fake_execute), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 1)
            batch = next((base / "runs").iterdir())
            state = budget.read_json(batch / "batch.json")
        self.assertEqual(len(calls), 1)
        self.assertEqual(state["stopped"], "source_pin_drift")
        self.assertEqual(state["rows"][1]["state"], "not_started")

    def test_missing_reported_model_stops_after_retaining_known_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"

            def fake_execute(row, run_dir, candidate_path, current_path, args, baselines, pre_call_pins=None):
                budget.write_json(run_dir / "meta.json", {
                    "reported_cost_usd": 0.1, "reported_cost_status": "recorded", "returncode": 0,
                    "timed_out": False, "runner_error": None, "cli_result_error": False,
                    "model_reported_status": "missing_or_mismatched", "cli_version_reported_status": "matched",
                })
                return {"acceptance": {"status": "failed"}, "required_verification_coverage": {"status": "failed"}}

            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            pin_check = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", return_value=pin_check), \
                 unittest.mock.patch.object(budget, "generate_baselines", return_value=[]), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=fake_execute), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 1)
            state = budget.read_json(next((base / "runs").iterdir()) / "batch.json")
        self.assertEqual(state["stopped"], "missing_or_mismatched_reported_model")
        self.assertEqual(state["known_spent_usd"], 0.1)

    def test_resource_limited_known_cost_row_does_not_stop_the_next_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"
            calls = []

            def fake_execute(row, run_dir, candidate_path, current_path, args, baselines, pre_call_pins=None):
                calls.append(row)
                budget.write_json(run_dir / "meta.json", {
                    "reported_cost_usd": 3.0, "reported_cost_status": "recorded", "returncode": 0,
                    "timed_out": False, "runner_error": None, "cli_result_error": False,
                    "resource_limit_status": "max_turns", "model_reported_status": "matched",
                    "cli_version_reported_status": "matched",
                })
                return {"acceptance": {"status": "failed"}, "required_verification_coverage": {"status": "failed"}}

            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            pin_check = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", return_value=pin_check), \
                 unittest.mock.patch.object(budget, "generate_baselines", return_value=[]), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=fake_execute), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 0)
            state = budget.read_json(next((base / "runs").iterdir()) / "batch.json")
        self.assertEqual(len(calls), 8)
        self.assertEqual(state["stopped"], "batch_budget_reservation")
        self.assertEqual(state["rows"][0]["resource_limit_status"], "max_turns")

    def test_cli_error_with_known_cost_stops_after_the_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"
            calls = []

            def fake_execute(row, run_dir, candidate_path, current_path, args, baselines, pre_call_pins=None):
                calls.append(row)
                budget.write_json(run_dir / "meta.json", {
                    "reported_cost_usd": 0.1, "reported_cost_status": "recorded", "returncode": 0,
                    "timed_out": False, "runner_error": None, "cli_result_error": True,
                    "resource_limit_status": "not_limited", "model_reported_status": "matched",
                    "cli_version_reported_status": "matched",
                })
                return {"acceptance": {"status": "unverified"}, "required_verification_coverage": {"status": "unverified"}}

            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            pin_check = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", return_value=pin_check), \
                 unittest.mock.patch.object(budget, "generate_baselines", return_value=[]), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=fake_execute), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 1)
            state = budget.read_json(next((base / "runs").iterdir()) / "batch.json")
        self.assertEqual(len(calls), 1)
        self.assertEqual(state["stopped"], "cli_error")

    def test_runner_exception_marks_collection_cost_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = REPO_ROOT / "experiments" / "verification-budget" / "candidate" / "AGENTS.md"
            current = REPO_ROOT / "AGENTS.md"
            args = argparse.Namespace(
                candidate=str(candidate), current=str(current), out=str(base / "runs"), model=budget.DEFAULT_MODEL,
                max_turns=80, timeout=1, verification_timeout=1, dry_run=False,
            )
            captured = {"status": "recorded", "raw": "2.1.263 (Claude Code)", "normalized": "2.1.263"}
            pin_check = {"status": "matched", "source_pins_status": "matched", "cli_version_status": "matched"}
            with unittest.mock.patch.object(budget, "capture_cli_version", return_value=captured), \
                 unittest.mock.patch.object(budget, "collection_pin_check", return_value=pin_check), \
                 unittest.mock.patch.object(budget, "generate_baselines", return_value=[]), \
                 unittest.mock.patch.object(budget, "execute_live_row", side_effect=RuntimeError("collector failed")), \
                 unittest.mock.patch.object(budget.experiment, "assert_isolated"):
                self.assertEqual(budget.run(args), 1)
            state = budget.read_json(next((base / "runs").iterdir()) / "batch.json")
        self.assertEqual(state["stopped"], "run_error")
        self.assertEqual(state["collection_cost_status"], "unknown")

    def test_old_t5_replay_is_read_only_unscorable(self):
        result = budget.score_old_t5(REPO_ROOT / "experiments" / "task5")
        self.assertEqual(result["status"], "unscorable")


if __name__ == "__main__":
    unittest.main()
