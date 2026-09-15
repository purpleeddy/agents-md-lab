"""Fixed functional assertions; never copied into a task's editable seed."""
import importlib.util
from pathlib import Path
import sys
import re
import shutil
import subprocess
import tempfile
import unittest

TASK, ROOT = sys.argv[1], Path(sys.argv[2]).resolve()
sys.argv = [sys.argv[0]]


def module(name):
    spec = importlib.util.spec_from_file_location('accepted_' + name, ROOT / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class FunctionalAcceptance(unittest.TestCase):
    def test_requested_behavior(self):
        if TASK == 'O4':
            parser = module('parser')
            for source, delimiter, expected in [('a,b', ',', ['a', 'b']), ('a;b', ';', ['a', 'b']), ('a|b|', '|', ['a', 'b', '']), ('a::b', '::', ['a', 'b'])]:
                with self.subTest(source=source):
                    self.assertEqual(parser.parse_row(source, delimiter), expected)
            # Run the submitted regression dynamically, independently of its syntax.
            original = Path(__file__).parent / 'O4/seed/parser.py'
            with tempfile.TemporaryDirectory(prefix='focused-regression-') as temporary:
                copied = Path(temporary) / 'repo'
                shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns('.git', '__pycache__'))
                for label, source in [('final', ROOT / 'parser.py'), ('original', original)]:
                    shutil.copyfile(source, copied / 'parser.py')
                    observed = subprocess.run([sys.executable, '-m', 'unittest'], cwd=copied,
                                              capture_output=True, text=True, timeout=30)
                    match = re.search(r'Ran (\d+) tests?\b', observed.stderr)
                    self.assertIsNotNone(match, label + ': no observed test count')
                    self.assertGreater(int(match.group(1)), 0, label)
                    print('Regression ' + label + ':\n' + observed.stderr)
                    if label == 'final':
                        self.assertEqual(observed.returncode, 0, observed.stderr)
                    else:
                        self.assertNotEqual(observed.returncode, 0, 'tests did not reproduce the original bug')
                        self.assertIn('FAIL:', observed.stderr, 'original parser must cause an assertion failure')
        elif TASK == 'C1':
            self.assertEqual(module('maths').add(2, 3), 5)
            text = (ROOT / 'examples.md').read_text().replace('`', '')
            self.assertRegex(text, r'add\(2,\s*3\)\s+returns\s+5\b')
            self.assertNotRegex(text, r'add\(2,\s*3\)\s+returns\s+(?!5\b)\d+')
        elif TASK == 'C2':
            self.assertEqual(module('units').to_milliseconds(2), 2000)
            text = (ROOT / 'units.md').read_text().replace('`', '')
            self.assertRegex(text, r'to_milliseconds\(2\)\s+returns\s+2000\s+milliseconds\b')
            self.assertRegex(text, r'2\s+seconds\b')
            self.assertNotRegex(text, r'to_milliseconds\(2\)\s+returns\s+(?!2000\b)\d+')
        elif TASK == 'C3':
            links = re.findall(r'\[[^]\n]+\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)', (ROOT / 'CHANGELOG.md').read_text())
            expected = (ROOT / 'releases/v1.md').resolve()
            self.assertTrue(any((ROOT / link).resolve() == expected for link in links))
            self.assertTrue(expected.is_file())
        elif TASK == 'C4':
            self.assertEqual((ROOT / 'instructions.txt').read_text(), 'To receive an export, open the downloads folder.\n')
        else:
            self.fail('blocked tasks have ownership endpoints, not functional fixes')


if __name__ == '__main__':
    unittest.main()
