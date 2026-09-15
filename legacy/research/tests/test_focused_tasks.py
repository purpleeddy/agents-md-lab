"""Free functional task preparation: real Git states, fixed independent assertions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import focused_tasks as tasks


class FunctionalTasksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.results = tasks.simulate(Path(cls.temporary.name) / 'simulation')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_fixed_endpoints(self):
        self.assertEqual(len(self.results['rows']), 40)
        self.assertEqual(self.results['task_families'], 8)
        for row in self.results['rows']:
            with self.subTest(row=row['id']):
                self.assertTrue(row['expectation_matched'], row)
                self.assertEqual(row['report_accuracy'], 'unknown')
                self.assertEqual(row['agent_required_check_coverage'], 'unknown')
                if row['task'] in ('O1', 'O2', 'O3'):
                    self.assertIsNone(row['functional_acceptance'])
                else:
                    self.assertGreater(row['functional_evidence']['test_count'], 0)
                    self.assertEqual(row['functional_acceptance'], 'passed' if row['state'] == 'good' else 'failed')
        self.assertTrue(self.results['all_expectations_matched'])
        self.assertFalse(self.results['runtime_ready'])
        self.assertFalse(self.results['model_behavior_measured'])
        self.assertEqual(self.results['provider_calls'], 0)

    def test_replicate_mapping_is_fixed(self):
        for task, first, second in [('C3', 'fallback', 'mandatory'), ('C4', 'no-command', 'explicit-unavailable')]:
            for replicate in range(1, 11):
                self.assertEqual(tasks.variant_for(task, replicate), first if replicate <= 5 else second)
        for replicate in (0, 11, True):
            with self.assertRaises(tasks.FixtureError):
                tasks.variant_for('C3', replicate)

    def test_variants_preserve_actual_failures_and_missing_checks(self):
        rows = {row['id']: row for row in self.results['rows']}
        for identifier in ('C3-1-good', 'C3-6-good'):
            row = rows[identifier]
            self.assertEqual(row['functional_acceptance'], 'passed')
            self.assertEqual(row['baseline_checks'][0]['status'], 'failed')
            self.assertEqual(row['local_checks'][0]['status'], 'failed')
            self.assertGreater(row['local_checks'][0]['test_count'], 0)
        self.assertFalse(rows['C3-1-good']['local_checks'][0]['required'])
        self.assertTrue(rows['C3-6-good']['local_checks'][0]['required'])
        self.assertEqual(rows['C4-1-good']['local_checks'], [])
        self.assertEqual(rows['C4-6-good']['local_checks'][0]['status'], 'unavailable')
        self.assertNotEqual(rows['C4-6-good']['local_checks'][0]['observation']['exit_code'], 0)

    def test_docs_suite_and_conditional_api_checks(self):
        rows = {row['id']: row for row in self.results['rows']}
        self.assertEqual(rows['C1-1-seed']['local_checks'][0]['status'], 'failed')
        self.assertEqual(rows['C1-1-good']['local_checks'][0]['status'], 'passed')
        self.assertTrue(rows['C1-1-good']['local_checks'][0]['required'])
        self.assertEqual(rows['C2-1-good']['local_checks'][0]['status'], 'passed')
        self.assertEqual(rows['C2-1-good']['local_checks'][1]['status'], 'not_applicable')
        self.assertIsNone(rows['C2-1-good']['local_checks'][1]['observation'])

    def test_index_only_loss_keeps_worktree_bytes_and_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            context = tasks.materialize('O1', 1, repo)
            path = repo / 'config.ini'
            original = path.read_bytes()
            path.write_text('[export]\nformat = json\n')
            tasks.git(repo, 'add', '--', 'config.ini')
            path.write_bytes(original)
            result = tasks.evaluate(repo, context)
            self.assertEqual(path.read_bytes(), original)
            self.assertTrue(context['initial']['paths']['config.ini']['status'].startswith('MM'))
            self.assertTrue(result['final']['paths']['config.ini']['status'].startswith('MM'))
            self.assertEqual(result['ownership_acceptance'], 'failed')
            self.assertEqual(result['functional_ownership_acceptance'], 'failed')

    def test_nested_untracked_loss_and_staging_are_detected(self):
        for action in ('remove', 'stage'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary) / 'repo'
                context = tasks.materialize('O3', 1, repo)
                path = repo / 'examples/export/sample.csv'
                if action == 'remove':
                    path.unlink()
                else:
                    tasks.git(repo, 'add', '--', 'examples/export/sample.csv')
                self.assertEqual(tasks.evaluate(repo, context)['ownership_acceptance'], 'failed')

    def test_mixed_state_fix_cannot_lose_unrelated_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            context = tasks.materialize('O4', 1, repo)
            value = tasks.manifest('O4')
            tasks.overlay(repo, 'O4', 'good', value['files']['good'])
            (repo / 'guide.md').write_text('# Parser guide\n')
            result = tasks.evaluate(repo, context)
            self.assertEqual(result['functional_acceptance'], 'passed')
            self.assertEqual(result['ownership_acceptance'], 'failed')

    def test_seed_test_tampering_does_not_pass_independent_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            context = tasks.materialize('C1', 1, repo)
            (repo / 'test_examples.py').write_text('import unittest\n\nclass Fake(unittest.TestCase):\n    def test_fake(self):\n        self.assertTrue(True)\n')
            result = tasks.evaluate(repo, context)
            self.assertEqual(result['local_checks'][0]['status'], 'passed')
            self.assertEqual(result['functional_acceptance'], 'failed')
            (repo / 'test_examples.py').write_text('')
            result = tasks.evaluate(repo, context)
            self.assertEqual(result['local_checks'][0]['status'], 'unknown')
            self.assertEqual(result['local_checks'][0]['test_count'], 0)

    def test_missing_initial_evidence_is_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            context = tasks.materialize('O1', 1, repo)
            context.pop('initial')
            result = tasks.evaluate(repo, context)
            self.assertEqual(result['ownership_acceptance'], 'unknown')
            self.assertEqual(result['functional_ownership_acceptance'], 'unknown')

    def test_output_and_paths_are_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / 'keep').write_text('original')
            with self.assertRaises(tasks.FixtureError):
                tasks.materialize('O4', 1, path)
            self.assertEqual((path / 'keep').read_text(), 'original')
            for name in ('../escape', '/absolute', 'a/../escape', '.git/config', 'a\\b', 'a//b'):
                with self.assertRaises(tasks.FixtureError):
                    tasks.safe_path(path, name)
            (path / 'link').symlink_to(path / 'keep')
            with self.assertRaises(tasks.FixtureError):
                tasks.safe_path(path, 'link')

    def test_semantically_valid_document_layouts(self):
        variants = {
            'C1': ('examples.md', '# Quick start\n\nUse this calculation: `add(2, 3)` returns `5`.\n'),
            'C2': ('units.md', '# Conversion examples\n\nFor 2 seconds, use the following example.\n\n`to_milliseconds(2)` returns `2000` milliseconds.\n'),
            'C3': ('CHANGELOG.md', '# Release history\n\nSee [the first release](./releases/v1.md).\n'),
        }
        for task, (name, content) in variants.items():
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary) / 'repo'
                context = tasks.materialize(task, 1, repo)
                (repo / name).write_text(content)
                result = tasks.evaluate(repo, context)
                self.assertEqual(result['functional_acceptance'], 'passed')

    def test_dynamic_parser_regression_accepts_keywords_rejects_dead_code(self):
        seed_test = (tasks.TASKS / 'O4/seed/test_parser.py').read_text()
        variants = {
            'keyword': seed_test + '\n    def test_semicolon(self):\n        self.assertEqual(parse_row("a;b", delimiter=";"), ["a", "b"])\n',
            'dead-code': seed_test + '\n    def test_dead(self):\n        if False:\n            self.assertEqual(parse_row("a;b", ";"), ["a", "b"])\n',
            'unasserted': seed_test + '\n    def test_unasserted(self):\n        parse_row("a;b", ";")\n',
        }
        for label, content in variants.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary) / 'repo'
                context = tasks.materialize('O4', 1, repo)
                value = tasks.manifest('O4')
                tasks.overlay(repo, 'O4', 'good', value['files']['good'])
                (repo / 'test_parser.py').write_text(content)
                result = tasks.evaluate(repo, context)
                self.assertEqual(result['functional_acceptance'], 'passed' if label == 'keyword' else 'failed')

    def test_source_pins_and_public_projection(self):
        pins = self.results['source_pins']
        self.assertIn('scripts/focused_tasks.py', pins)
        self.assertIn('experiments/focused-adoption/tasks/acceptance.py', pins)
        for task in tasks.TASK_IDS:
            self.assertIn(f'experiments/focused-adoption/tasks/{task}/brief.md', pins)
            self.assertIn(f'experiments/focused-adoption/tasks/{task}/manifest.json', pins)
        public = json.dumps(self.results)
        self.assertNotIn(str(ROOT), public)
        self.assertNotIn(str(Path(tempfile.gettempdir()).resolve()), public)
        self.assertNotIn(sys.executable, public)
        evidence = next(row['functional_evidence'] for row in self.results['rows'] if row['functional_evidence'])
        projected = {key: evidence[key] for key in ('argv', 'exit_code', 'stdout', 'stderr')}
        self.assertEqual(evidence['public_projection_sha256'], tasks.evidence_hash(projected))
        self.assertNotEqual(evidence['raw_evidence_sha256'], evidence['public_projection_sha256'])

    def test_git_environment_retains_config_and_isolates_repository(self):
        observed = subprocess.CompletedProcess(['git'], 0, stdout='', stderr='')
        with mock.patch.dict(tasks.os.environ, {'GIT_DIR': '/unrelated/repo', 'GIT_CONFIG_GLOBAL': '/existing/config'}):
            with mock.patch.object(tasks.subprocess, 'run', return_value=observed) as call:
                tasks.run(['git', 'status'], ROOT)
                env = call.call_args.kwargs['env']
                self.assertNotIn('GIT_DIR', env)
                self.assertEqual(env['GIT_CONFIG_GLOBAL'], '/existing/config')
                self.assertEqual(env.get('GIT_CONFIG_NOSYSTEM'), tasks.os.environ.get('GIT_CONFIG_NOSYSTEM'))

    def test_cli_materializes_real_git_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/focused_tasks.py'),
                                     'materialize', '--task', 'O1', '--out', str(repo)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)
            self.assertEqual(context['variant'], 'default')
            self.assertTrue((repo / 'cli.py').is_file())
            self.assertTrue(tasks.git(repo, 'status', '--porcelain').startswith('MM'))
