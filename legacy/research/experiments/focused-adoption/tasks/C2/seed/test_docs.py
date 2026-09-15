import unittest
from pathlib import Path

class DocsTest(unittest.TestCase):
    def test_units_example(self):
        self.assertIn("`to_milliseconds(2)` returns `2000` milliseconds.", Path("units.md").read_text())
