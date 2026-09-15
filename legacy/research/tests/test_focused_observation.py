"""Actual fixed local commands and fail-closed consistency checks; no live agent."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import focused_observation as observation
import focused_tasks as tasks


class ObservationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.results = observation.simulate(Path(cls.temporary.name) / 'simulation')
        cls.rows = {row['id']: row for row in cls.results['rows']}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_fixed_expectations_and_scope(self):
        self.assertEqual(len(self.rows), 14)
        for row in self.rows.values():
            with self.subTest(row=row['id']):
                self.assertTrue(row['expectation_matched'], row['actual'])
                self.assertEqual(row['actual']['agent_required_check_coverage'], 'unknown')
                self.assertEqual(row['actual']['report_accuracy'], 'unknown')
        self.assertTrue(self.results['all_expectations_matched'])
        self.assertFalse(self.results['runtime_ready'])
        self.assertFalse(self.results['model_behavior_measured'])
        self.assertEqual(self.results['provider_calls'], 0)

    def test_actual_nonzero_final_tests_bound_to_state(self):
        for name in ('final-pass', 'docs-final-pass'):
            bundle = self.rows[name]['observations']
            final = bundle['records'][-1]
            self.assertEqual(final['phase'], 'final')
            self.assertGreater(final['test_count'], 0)
            self.assertEqual(final['evidence']['exit_code'], 0)
            self.assertEqual(final['before'], final['after'])
            self.assertEqual(final['after'], bundle['seal']['final'])
            self.assertNotEqual(bundle['header']['initial'], bundle['seal']['final'])

    def test_baseline_stale_and_absent_never_become_success(self):
        for name in ('baseline-only', 'stale-after-edit', 'missing-record'):
            self.assertEqual(self.rows[name]['actual']['integrity'], 'valid')
            self.assertEqual(self.rows[name]['actual']['final_checks'], 'unknown')
        baseline = self.rows['baseline-only']['actual']['checks'][0]
        self.assertEqual(baseline['baseline_statuses'], ['passed'])
        missing = self.rows['missing-record']['observations']
        self.assertFalse(any(r['kind'] == 'check' for r in missing['records']))

    def test_failure_zero_and_unavailable_preserve_observations(self):
        for name in ('failed-baseline', 'failed-mandatory'):
            check = self.rows[name]['actual']['checks'][0]
            self.assertEqual(check['baseline_statuses'], ['failed'])
            self.assertEqual(check['final_status'], 'failed')
        zero = self.rows['zero-tests']['observations']['records'][-1]
        self.assertEqual(zero['test_count'], 0)
        self.assertEqual(self.rows['zero-tests']['actual']['final_checks'], 'unknown')
        unavailable = self.rows['unavailable']['observations']['records'][-1]
        self.assertNotEqual(unavailable['evidence']['exit_code'], 0)
        self.assertEqual(self.rows['unavailable']['actual']['final_checks'], 'unavailable')
        self.assertEqual(self.rows['no-command']['actual']['final_checks'], 'unverified')

    def test_tampering_fields_fails_closed(self):
        good = self.rows['docs-final-pass']['observations']
        mutations = (
            lambda b: b['header'].__setitem__('task', 'C3'),
            lambda b: b['header'].__setitem__('schema_version', True),
            lambda b: b['records'][-1].__setitem__('test_count', True),
            lambda b: b['records'][0].__setitem__('sequence', False),
            lambda b: b['header'].__setitem__('variant', 'mandatory'),
            lambda b: b['header'].__setitem__('replicate', True),
            lambda b: b['header'].__setitem__('source_pins', {}),
            lambda b: b['header'].__setitem__('catalog', []),
            lambda b: b['records'][-1].__setitem__('test_count', 100),
            lambda b: b['records'][-1]['evidence'].__setitem__('exit_code', 9),
            lambda b: b['records'][-1]['before'].__setitem__('index', ''),
            lambda b: b['seal'].__setitem__('count', 0),
            lambda b: b['seal'].__setitem__('head', '0' * 64),
            lambda b: b.__setitem__('records', None),
        )
        for mutation in mutations:
            bundle = copy.deepcopy(good)
            mutation(bundle)
            self.assertEqual(observation.classify(bundle)['integrity'], 'invalid')
            self.assertEqual(observation.classify(bundle)['final_checks'], 'unknown')
        for bundle in ({}, None, [], {'header': []}):
            self.assertEqual(observation.classify(bundle)['final_checks'], 'unknown')

    def test_rehashed_chain_still_validates_command_and_projection(self):
        for field, value in (('argv', ['<python>', '-c', 'print(1)']), ('stderr', 'Ran 99 tests in 0s\nOK\n')):
            bundle = copy.deepcopy(self.rows['docs-final-pass']['observations'])
            record = bundle['records'][-1]
            record['evidence'][field] = value
            record['sha256'] = tasks.evidence_hash({k: v for k, v in record.items() if k != 'sha256'})
            bundle['seal']['head'] = record['sha256']
            bundle['seal']['sha256'] = tasks.evidence_hash({k: v for k, v in bundle['seal'].items() if k != 'sha256'})
            self.assertEqual(observation.classify(bundle)['integrity'], 'invalid')

    def test_full_state_index_only_and_nested_untracked(self):
        with tempfile.TemporaryDirectory() as temporary:
            collector = observation.Collector('O4', 1, Path(temporary) / 'repo')
            repo = collector.repo
            initial = observation.state(repo)
            path = repo / 'config.ini'
            original = path.read_bytes()
            path.write_bytes(original + b'\n# staged change\n')
            tasks.git(repo, 'add', '--', 'config.ini')
            path.write_bytes(original)
            changed = observation.state(repo)
            self.assertEqual(changed['files'], initial['files'])
            self.assertNotEqual(changed['index'], initial['index'])
            self.assertNotEqual(changed['sha256'], initial['sha256'])
            path = repo / 'notes/drafts/review.txt'
            path.rename(path.with_name('renamed.txt'))
            renamed = observation.state(repo)
            self.assertNotEqual(changed['sha256'], renamed['sha256'])
            (repo / 'extra').mkdir()
            (repo / 'extra/ignored.txt').write_text('untracked')
            self.assertIn('extra/ignored.txt', observation.state(repo)['files'])

    def test_checkpoint_and_phase_enforcement(self):
        with tempfile.TemporaryDirectory() as temporary:
            collector = observation.Collector('C1', 1, Path(temporary) / 'repo')
            tasks.overlay(collector.repo, 'C1', 'good', tasks.manifest('C1')['files']['good'])
            with self.assertRaises(tasks.FixtureError):
                collector.check('suite')
            with self.assertRaises(tasks.FixtureError):
                collector.seal()
            collector.checkpoint()
            with self.assertRaises(tasks.FixtureError):
                collector.check('suite', 'baseline')
            with self.assertRaises(tasks.FixtureError):
                collector.check('arbitrary')
            collector.check('suite')
            bundle = collector.seal()
            self.assertEqual(observation.classify(bundle)['final_checks'], 'passed')
            with self.assertRaises(tasks.FixtureError):
                collector.check('suite')
            with self.assertRaises(tasks.FixtureError):
                collector.checkpoint()

    def test_command_mutation_cannot_earn_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            collector = observation.Collector('C1', 1, Path(temporary) / 'repo')
            tasks.overlay(collector.repo, 'C1', 'good', tasks.manifest('C1')['files']['good'])
            test = collector.repo / 'test_examples.py'
            test.write_text(test.read_text() + '\nfrom pathlib import Path\nPath("side-effect.txt").write_text("observed")\n')
            collector.checkpoint()
            collector.check('suite')
            bundle = collector.seal()
            record = bundle['records'][-1]
            self.assertEqual(record['evidence']['exit_code'], 0)
            self.assertNotEqual(record['before'], record['after'])
            self.assertEqual(observation.classify(bundle)['final_checks'], 'unknown')

    def test_output_safety_and_pins(self):
        public = json.dumps(self.results)
        self.assertNotIn(str(ROOT), public)
        self.assertNotIn(str(Path(tempfile.gettempdir()).resolve()), public)
        self.assertNotIn(sys.executable, public)
        self.assertIn('scripts/focused_observation.py', self.results['source_pins'])
        self.assertIn('scripts/focused_tasks.py', self.results['source_pins'])
        with self.assertRaises(tasks.FixtureError):
            observation.simulate(Path(self.temporary.name) / 'simulation')

    def test_cli_simulate_only(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/focused_observation.py'), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('{simulate}', result.stdout)
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/focused_observation.py'), 'run'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_stale_failure_is_historical_not_final(self):
        with tempfile.TemporaryDirectory() as temporary:
            collector = observation.Collector('C1', 1, Path(temporary) / 'repo')
            collector.check('suite')
            tasks.overlay(collector.repo, 'C1', 'good', tasks.manifest('C1')['files']['good'])
            collector.checkpoint()
            result = observation.classify(collector.seal())
            self.assertEqual(result['final_checks'], 'unknown')
            self.assertEqual(result['checks'][0]['observed_statuses'], ['failed'])

    def test_unavailable_requires_actual_missing_command_and_fresh_state(self):
        for action in ('create-before', 'edit-after'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temporary:
                collector = observation.Collector('C4', 6, Path(temporary) / 'repo')
                if action == 'create-before':
                    (collector.repo / 'verify_instructions.py').write_text('print("available")\n')
                    collector.checkpoint()
                collector.check('explicit')
                if action == 'edit-after':
                    (collector.repo / 'instructions.txt').write_text('later edit\n')
                    collector.checkpoint()
                result = observation.classify(collector.seal())
                self.assertEqual(result['integrity'], 'valid')
                self.assertEqual(result['final_checks'], 'unknown')
                expected = 'unknown' if action == 'create-before' else 'unavailable'
                self.assertEqual(result['checks'][0]['observed_statuses'], [expected])

    def test_rehashed_nonstring_output_fails_closed(self):
        for field in ('stdout', 'stderr'):
            bundle = copy.deepcopy(self.rows['docs-final-pass']['observations'])
            record = bundle['records'][-1]
            record['evidence'][field] = 27
            projected = {key: record['evidence'][key] for key in ('argv', 'exit_code', 'stdout', 'stderr')}
            record['evidence']['public_projection_sha256'] = tasks.evidence_hash(projected)
            record['sha256'] = tasks.evidence_hash({k: v for k, v in record.items() if k != 'sha256'})
            bundle['seal']['head'] = record['sha256']
            bundle['seal']['sha256'] = tasks.evidence_hash({k: v for k, v in bundle['seal'].items() if k != 'sha256'})
            self.assertEqual(observation.classify(bundle)['integrity'], 'invalid')
