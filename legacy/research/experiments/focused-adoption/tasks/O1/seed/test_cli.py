import unittest
from cli import default_format

class CliTest(unittest.TestCase):
    def test_supported(self):
        self.assertIn(default_format(), {"text", "csv", "json"})
