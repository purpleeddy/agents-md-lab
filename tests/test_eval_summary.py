"""Prevent missing or incompatible trial data from producing efficiency claims."""

import json
from pathlib import Path
import tempfile
import unittest

from evaluation.summarize import summarize, tokens


class EvaluationSummaryTests(unittest.TestCase):
    def record(self, arm='control'):
        return dict(provider='codex', task='sample', repeat=0, arm=arm, status='completed',
                    functional_pass=True, elapsed_seconds=2,
                    telemetry={'codex_turn_usage': [{'input_tokens': 100, 'cached_input_tokens': 90,
                                                     'output_tokens': 10}]})

    def write(self, path, rows, baseline='same'):
        path.mkdir()
        plan = dict(rows=rows, baseline_sha256=baseline, fixture_sha256='fixture', effort='medium', models={}, seed=42)
        (path / 'plan.json').write_text(json.dumps(plan))
        (path / 'results.json').write_text(json.dumps(rows))

    def test_cache_accounting_is_provider_specific(self):
        self.assertEqual(tokens(self.record()), 110)
        claude = dict(provider='claude', telemetry={'provider_usage': {
            'input_tokens': 2, 'output_tokens': 3, 'cache_read_input_tokens': 4,
            'cache_creation_input_tokens': 5}})
        self.assertEqual(tokens(claude), 14)
        del claude['telemetry']['provider_usage']['cache_read_input_tokens']
        self.assertIsNone(tokens(claude))

    def test_failed_attempt_is_kept_and_missing_usage_stays_unknown(self):
        a, b = self.record(), self.record('baseline')
        b.update(status='execution_incomplete', functional_pass=False, telemetry={})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run'
            self.write(path, [a, b])
            result = summarize([path])
        arm = next(r for r in result['arms'] if r['arm'] == 'baseline')
        self.assertEqual(arm['attempted'], 1)
        self.assertEqual(arm['functional_pass'], 0)
        self.assertIsNone(arm['total_tokens'])
        self.assertIsNone(result['pairs'][0]['token_difference'])

    def test_duplicate_or_incompatible_trials_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a', Path(directory) / 'b'
            self.write(a, [self.record()])
            self.write(b, [self.record()])
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                summarize([a, b])
            self.write_plan_change(b)
            with self.assertRaisesRegex(ValueError, 'Incompatible'):
                summarize([a, b])

    def test_same_length_wrong_trials_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run'
            self.write(path, [self.record(), self.record('baseline')])
            wrong = [self.record(), self.record('baseline')]
            wrong[1]['repeat'] = 9
            (path / 'results.json').write_text(json.dumps(wrong))
            with self.assertRaisesRegex(ValueError, 'planned trials'):
                summarize([path])

    def write_plan_change(self, path):
        plan = json.loads((path / 'plan.json').read_text())
        plan['baseline_sha256'] = 'different'
        plan['rows'] = [self.record('baseline')]
        (path / 'plan.json').write_text(json.dumps(plan))
        (path / 'results.json').write_text(json.dumps([self.record('baseline')]))


if __name__ == '__main__':
    unittest.main()
