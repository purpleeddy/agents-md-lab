import copy
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import focused_schedule as schedule


class FocusedScheduleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = schedule.generate()

    def test_full_balanced_assignment(self):
        rows = self.value['rows']
        self.assertEqual(len(rows), 440)
        self.assertEqual(len({r['run_id'] for r in rows}), 440)
        self.assertEqual(Counter(r['task'] for r in rows),
                         {t: 40 for t in ('T1', 'T2', 'T3', 'O1', 'O2', 'O3', 'O4', 'C1', 'C2', 'C3', 'C4')})
        self.assertEqual(Counter(r['condition'] for r in rows),
                         {'none': 110, 'karpathy': 110, 'current': 110, 'focused': 110})
        for start in range(0, 440, 4):
            block = rows[start:start + 4]
            self.assertEqual(len({(r['task'], r['replicate'], r['variant']) for r in block}), 1)
            self.assertEqual({r['condition'] for r in block}, {'none', 'karpathy', 'current', 'focused'})
        schedule.validate(self.value)

    def test_variant_mapping_and_no_readiness_claim(self):
        for row in self.value['rows']:
            if row['task'] == 'C3':
                self.assertEqual(row['variant'], 'fallback' if row['replicate'] <= 5 else 'mandatory')
            if row['task'] == 'C4':
                self.assertEqual(row['variant'], 'no-command' if row['replicate'] <= 5 else 'explicit-unavailable')
        self.assertEqual(self.value['status'], 'draft_unlocked')
        self.assertFalse(self.value['runtime_ready'])
        self.assertFalse(self.value['condition_and_runtime_pins_complete'])
        self.assertEqual(self.value['provider_calls'], 0)

    def test_bad_membership_and_types_rejected_even_with_recomputed_row_hash(self):
        mutations = [lambda r: r.pop(),
                     lambda r: r[1].update(condition=r[0]['condition']),
                     lambda r: r[1].update(run_id=r[0]['run_id']),
                     lambda r: r[0].update(replicate=True),
                     lambda r: r[0].update(ordinal=True),
                     lambda r: r[0].update(task='O1'),
                     lambda r: r[0].update(variant='default'),
                     lambda r: r[0].update(extra='unexpected')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = copy.deepcopy(self.value)
                mutate(value['rows'])
                value['rows_sha256'] = schedule.rows_digest(value['rows'])
                with self.assertRaises(ValueError):
                    schedule.validate(value)

    def test_changed_pins_or_claims_rejected(self):
        for key, value in [('source_pins', {}), ('schema_version', True),
                           ('runtime_ready', True), ('provider_calls', False),
                           ('status', 'locked')]:
            with self.subTest(key=key):
                data = copy.deepcopy(self.value)
                data[key] = value
                with self.assertRaises(ValueError):
                    schedule.validate(data)

    def test_check_uses_saved_order_and_external_hash_not_new_draw(self):
        value = copy.deepcopy(self.value)
        rows = value['rows']
        rows[0]['condition'], rows[1]['condition'] = rows[1]['condition'], rows[0]['condition']
        value['rows_sha256'] = schedule.rows_digest(rows)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'schedule.json'
            original = json.dumps(self.value).encode()
            changed = json.dumps(value).encode()
            path.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, 'externally supplied'):
                schedule.check(path, schedule.digest(original))
            with patch.object(schedule.random, 'Random', side_effect=AssertionError('must not redraw')):
                self.assertEqual(schedule.check(path, schedule.digest(changed))['rows'], 440)

    def test_duplicate_json_members_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'schedule.json'
            raw = json.dumps(self.value).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1').encode()
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                schedule.check(path, schedule.digest(raw))

    def test_cli_generate_and_check_and_refuse_nonempty_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / 'generated'
            argv = [sys.executable, str(ROOT / 'scripts/focused_schedule.py')]
            result = subprocess.run([*argv, 'generate', '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            info = json.loads(result.stdout)
            checked = subprocess.run([*argv, 'check', '--schedule', str(out / 'schedule.json'),
                                      '--sha256', info['sha256']], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            old = (out / 'schedule.json').read_bytes()
            repeated = subprocess.run([*argv, 'generate', '--out', str(out)], capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual((out / 'schedule.json').read_bytes(), old)
