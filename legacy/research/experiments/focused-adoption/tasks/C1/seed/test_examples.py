import unittest
from pathlib import Path
from maths import add

class ExamplesTest(unittest.TestCase):
    def test_example(self):
        self.assertIn(f"`add(2, 3)` returns `{add(2, 3)}`.", Path("examples.md").read_text())
