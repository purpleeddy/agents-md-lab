"""Verify fixture validity without invoking model CLIs or external services."""

import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import unittest

from evaluation.tasks import SOLUTIONS, TASKS


class EvaluationFixtureTests(unittest.TestCase):
    def run_fixture(self, task, solution=None, visible=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / 'candidate'
            candidate.mkdir()
            for name, content in {**task['files'], **(solution or {})}.items():
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
            grader = root / 'grade.py'
            grader.write_text(task['checks'], encoding='utf-8')
            environment = dict(os.environ, PYTHONPATH=str(candidate),
                               PYTHONDONTWRITEBYTECODE='1')
            command = ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
                       if visible else [sys.executable, str(grader)])
            return subprocess.run(command, cwd=candidate if visible else root,
                                  env=environment, capture_output=True, text=True,
                                  timeout=10, check=False)

    def test_fixture_contract(self):
        self.assertEqual(len(TASKS), 6)
        self.assertEqual(set(TASKS), set(SOLUTIONS))
        for name, task in TASKS.items():
            with self.subTest(task=name):
                self.assertEqual(set(task), {'prompt', 'files', 'checks', 'protected'})
                self.assertIn('python3 -m unittest discover -s tests -v', task['prompt'])
                self.assertIn('tests/test_app.py', task['protected'])
                for path in task['files']:
                    parsed = PurePosixPath(path)
                    self.assertFalse(parsed.is_absolute())
                    self.assertNotIn('..', parsed.parts)
                    self.assertNotIn('\\', path)
                self.assertTrue(set(task['protected']) <= task['files'].keys())
                self.assertTrue(SOLUTIONS[name].keys() <= task['files'].keys())
                self.assertFalse(set(task['protected']) & SOLUTIONS[name].keys())
                compile(task['checks'], f'{name}/grader.py', 'exec')

    def test_initial_fixtures_fail_independent_checks(self):
        for name, task in TASKS.items():
            with self.subTest(task=name):
                result = self.run_fixture(task)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('FAILED (', result.stderr)

    def test_initial_visible_tests_pass(self):
        for name, task in TASKS.items():
            with self.subTest(task=name):
                result = self.run_fixture(task, visible=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reference_solutions_pass_all_fixture_tests(self):
        for name, task in TASKS.items():
            for visible in [False, True]:
                with self.subTest(task=name, visible=visible):
                    result = self.run_fixture(task, SOLUTIONS[name], visible)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
