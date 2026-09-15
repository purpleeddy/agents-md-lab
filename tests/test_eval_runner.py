"""Check measurement plumbing without contacting model providers."""

import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

from evaluation import run
from evaluation.tasks import TASKS, SOLUTIONS


class EvaluationRunnerTests(unittest.TestCase):
    def test_schedule_pairs_each_task_and_repeat_for_both_clients(self):
        rows = run.schedule(3, 42)
        self.assertEqual(rows, run.schedule(3, 42))
        self.assertEqual(len(rows), 72)
        for provider in run.MODELS:
            for task in TASKS:
                for repeat in range(3):
                    pair = [r for r in rows if (r['provider'], r['task'], r['repeat'])
                            == (provider, task, repeat)]
                    self.assertEqual({r['arm'] for r in pair}, {'control', 'baseline'})

    def test_dedicated_client_calibration_plan_does_not_invoke_models(self):
        result = subprocess.run([sys.executable, '-m', 'evaluation.run', '--provider', 'claude',
                                 '--max-runs', '2'], cwd=run.ROOT, capture_output=True, text=True, check=True)
        plan = json.loads(result.stdout)
        self.assertEqual(len(plan['rows']), 2)
        self.assertEqual({r['provider'] for r in plan['rows']}, {'claude'})
        self.assertEqual({r['arm'] for r in plan['rows']}, {'control', 'baseline'})

    def test_only_instructions_differ_between_arms(self):
        task = TASKS['interval_overlap']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arm in ['control', 'baseline']:
                work = root / arm
                work.mkdir()
                run.write_fixture(work, task, arm, 'TEST BASELINE\n')
            for name in [*task['files'], 'CLAUDE.md']:
                self.assertEqual((root / 'control' / name).read_bytes(),
                                 (root / 'baseline' / name).read_bytes())
            self.assertEqual((root / 'baseline/AGENTS.md').read_text(),
                             (root / 'control/AGENTS.md').read_text() + '\nTEST BASELINE\n')
            self.assertFalse((root / 'baseline/check.py').exists())

    def test_grader_checks_behavior_and_preserved_files(self):
        task = TASKS['interval_overlap']
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            protected = run.write_fixture(work, task, 'control', '')
            self.assertFalse(run.grade(work, task, protected)['functional_pass'])
            for name, source in SOLUTIONS['interval_overlap'].items():
                (work / name).write_text(source)
            self.assertTrue(run.grade(work, task, protected)['functional_pass'])
            (work / 'tests/test_app.py').write_text('# Tests removed\n')
            result = run.grade(work, task, protected)
            self.assertFalse(result['functional_pass'])
            self.assertEqual(result['protected_changes'], ['tests/test_app.py'])

    def test_codex_usage_is_preserved_without_double_counting_cached_tokens(self):
        usage = {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 20}
        events = [{'type': 'item.completed', 'item': {'type': 'command_execution'}},
                  {'type': 'turn.completed', 'usage': usage}]
        parsed = run.telemetry('codex', '\n'.join(map(json.dumps, events)))
        self.assertTrue(parsed['completed'])
        self.assertEqual(parsed['provider_usage'], usage)
        self.assertEqual(parsed['codex_turn_usage'], [usage])
        self.assertIsNone(parsed['reported_cost_usd'])
        self.assertEqual(parsed['tool_events'], 1)

    def test_codex_terminal_failure_cannot_be_hidden_by_completion(self):
        completed = {'type': 'turn.completed', 'usage': {'input_tokens': 10}}
        for failure in [{'type': 'turn.failed'}, {'type': 'error'}]:
            for events in [[completed, failure], [failure, completed]]:
                parsed = run.telemetry('codex', '\n'.join(map(json.dumps, events)))
                self.assertFalse(parsed['completed'])
                self.assertTrue(parsed['terminal_failure'])
                self.assertEqual(parsed['codex_turn_usage'], [completed['usage']])

    def test_missing_executable_is_recorded_as_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run.execute([str(Path(directory) / 'missing-cli')], directory, 1)
        self.assertIsNone(result['exit_code'])
        self.assertEqual(result['error_type'], 'FileNotFoundError')
        self.assertFalse(result['timed_out'])

    def test_claude_initialization_is_not_a_completed_run(self):
        initial = {'type': 'system', 'subtype': 'init', 'model': 'fixture-model'}
        parsed = run.telemetry('claude', json.dumps(initial))
        self.assertFalse(parsed['completed'])
        self.assertIsNone(parsed['provider_usage'])
        self.assertEqual(parsed['reported_model'], 'fixture-model')
        failed = {'type': 'result', 'subtype': 'error_max_budget_usd', 'is_error': True}
        self.assertFalse(run.telemetry('claude', json.dumps(failed))['completed'])
        success = {'type': 'result', 'subtype': 'success', 'is_error': False,
                   'usage': {'input_tokens': 12}, 'total_cost_usd': 0.01, 'result': 'READY'}
        parsed = run.telemetry('claude', json.dumps(initial) + '\n' + json.dumps(success))
        self.assertTrue(parsed['completed'])
        self.assertEqual(parsed['reported_cost_usd'], 0.01)

    def test_timeout_does_not_look_like_success(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run.execute([sys.executable, '-c', 'import time; time.sleep(10)'], directory, 0.05)
        self.assertTrue(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)


if __name__ == '__main__':
    unittest.main()
