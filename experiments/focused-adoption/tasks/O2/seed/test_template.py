import unittest
from pathlib import Path

class TemplateTest(unittest.TestCase):
    def test_heading(self):
        self.assertTrue(Path("report-template.md").read_text().startswith("# "))
