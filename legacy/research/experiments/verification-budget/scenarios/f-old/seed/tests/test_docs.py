import pathlib
import unittest


class DocumentationTest(unittest.TestCase):
    def test_audit_log_is_documented(self):
        self.assertIn("--audit-log", pathlib.Path("README.md").read_text(encoding="utf-8"))
