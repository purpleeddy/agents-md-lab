"""Actual offline task-to-observation-to-report joins, never model measurements."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import focused_pipeline as pipeline


class FocusedPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.result = pipeline.simulate(Path(cls.temporary.name) / 'simulation')
        cls.rows = {row['id']: row for row in cls.result['rows']}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_fourteen_fixed_expectations(self):
        self.assertEqual(len(self.rows), 14)
        self.assertEqual({r['task'] for r in self.rows.values()}, set(pipeline.tasks.TASK_IDS))
        for row in self.rows.values():
            with self.subTest(row=row['id']):
                self.assertTrue(row['expectation_matched'], row['actual'])
        self.assertTrue(self.result['all_expectations_matched'])
        self.assertEqual(self.result['report_validation']['status'], 'contract_valid')
        self.assertEqual(self.result['report_validation']['rows'], 14)
        self.assertFalse(self.result['adoption_eligible'])
        self.assertFalse(self.result['model_behavior_measured'])
        self.assertFalse(self.result['runtime_ready'])
        self.assertEqual(self.result['provider_calls'], 0)

    def test_retained_bundles_replay_and_acceptance_binds_same_final_state(self):
        for row in self.rows.values():
            bundle = row['observations']
            classification = pipeline.observation.classify(bundle)
            self.assertEqual(classification['integrity'], 'valid')
            self.assertEqual(classification['final_checks'], row['actual']['final_checks'])
            for event in row['packet_row']['evidence']:
                binding = event['payload']['source_binding']
                self.assertEqual(binding['task'], bundle['header']['task'])
                self.assertEqual(binding['variant'], bundle['header']['variant'])
                self.assertEqual(binding['sealed_state_sha256'], bundle['seal']['final']['sha256'])
                if event['kind'] == 'acceptance':
                    state = event['payload']['state_binding']
                    self.assertTrue(state['unchanged'])
                    self.assertEqual(state['before_sha256'], state['after_sha256'])
                    self.assertEqual(state['after_sha256'], state['sealed_sha256'])

    def test_missing_stale_and_no_command_never_invent_check_kind(self):
        for name in ('C1-skip-final', 'C1-stale', 'C4-no-command-good'):
            row = self.rows[name]
            kinds = {event['kind'] for event in row['packet_row']['evidence']}
            self.assertNotIn('check', kinds)
            context = next(event['payload'] for event in row['packet_row']['evidence'] if event['kind'] == 'context')
            self.assertIn('noneligible_check_telemetry', context)
        for name in ('C1-skip-final', 'C1-stale'):
            self.assertEqual(self.rows[name]['actual']['final_checks'], 'unknown')
            self.assertIn('check', self.rows[name]['packet_row']['required_evidence_kinds']['completion_policy'])
        self.assertNotIn('check', self.rows['C4-no-command-good']['packet_row']['required_evidence_kinds']['completion_policy'])

    def test_blocked_rows_need_missing_dialogue_not_authored_endpoint(self):
        for name in ('O1-good', 'O2-good', 'O3-good'):
            row = self.rows[name]['packet_row']
            self.assertNotIn('dialogue', {e['kind'] for e in row['evidence']})
            self.assertIn('dialogue', row['required_evidence_kinds']['completion_policy'])
            self.assertFalse(pipeline.reports.eligible(row, 'clarification'))
            self.assertFalse(pipeline.reports.eligible(row, 'completion_policy'))
            self.assertFalse(pipeline.reports.eligible(row, 'report_accuracy'))

    def test_independent_bad_functional_and_protected_loss_evidence(self):
        for name, functional, ownership in (('O4-bad-functional', 'failed', 'passed'),
                                            ('O4-protected-loss', 'passed', 'failed')):
            evidence = {e['kind']: e['payload'] for e in self.rows[name]['packet_row']['evidence']}
            self.assertEqual(evidence['acceptance']['functional_acceptance'], functional)
            self.assertEqual(evidence['ownership']['status'], ownership)
            self.assertGreater(evidence['acceptance']['functional_evidence']['test_count'], 0)
            self.assertEqual(evidence['acceptance']['functional_ownership_acceptance'], 'failed')

    def test_actual_failed_and_unavailable_checks_are_eligible_evidence(self):
        for name, status in (('C3-fallback-good', 'failed'), ('C3-mandatory-good', 'failed'),
                             ('C4-unavailable-good', 'unavailable')):
            row = self.rows[name]
            self.assertTrue(row['actual']['known_check_evidence'])
            self.assertEqual(row['actual']['final_checks'], status)
            check = next(e['payload'] for e in row['packet_row']['evidence'] if e['kind'] == 'check')
            self.assertTrue(any(r.get('evidence', {}).get('exit_code', 0) != 0 for r in check['records']))

    def test_acceptance_cannot_change_sealed_tree(self):
        original = pipeline.tasks.evaluate
        def changing(repo, context):
            result = original(repo, context)
            (repo / 'after-acceptance.txt').write_text('changed')
            return result
        with mock.patch.object(pipeline.tasks, 'evaluate', side_effect=changing):
            with self.assertRaisesRegex(pipeline.tasks.FixtureError, 'acceptance changed sealed state'):
                pipeline.run_case(pipeline.SCENARIOS[8])

    def test_source_drift_stops_collection(self):
        original = pipeline.source_pins()
        with mock.patch.object(pipeline, 'source_pins', side_effect=[original, {}]):
            with self.assertRaisesRegex(pipeline.tasks.FixtureError, 'source pins changed'):
                pipeline.run_case(pipeline.SCENARIOS[8])

    def test_invalid_observation_never_provides_check_evidence(self):
        bundle = copy.deepcopy(self.rows['C1-good']['observations'])
        bundle['records'].pop()
        classification = pipeline.observation.classify(bundle)
        self.assertEqual(classification['integrity'], 'invalid')
        self.assertFalse(pipeline.check_evidence_known(bundle, classification))

    def test_safe_capture_pins_and_report_packet_hash(self):
        public = json.dumps(self.result)
        self.assertNotIn(str(ROOT), public)
        self.assertNotIn(str(Path(tempfile.gettempdir()).resolve()), public)
        self.assertNotIn(sys.executable, public)
        packet = {'schema': pipeline.reports.SCHEMA, 'rows': [r['packet_row'] for r in self.result['rows']]}
        self.assertEqual(pipeline.reports.transport.canonical_sha256(packet), self.result['report_packet_sha256'])
        pipeline.reports.source_rows(packet)
        for name in ('focused_pipeline.py', 'focused_tasks.py', 'focused_observation.py', 'focused_reports.py',
                     'verification_review.py', 'verification_review_v2.py'):
            self.assertIn('scripts/' + name, self.result['source_pins'])

    def test_cli_simulate_only_and_nonempty_output_refused(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/focused_pipeline.py'), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('{simulate}', result.stdout)
        with self.assertRaises(ValueError):
            pipeline.simulate(Path(self.temporary.name) / 'simulation')
