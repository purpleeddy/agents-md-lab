"""Run the actual enhancement script against controlled browser capabilities."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SiteInteractionTest(unittest.TestCase):
    def test_clipboard_fallback_and_live_locale_navigation(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required for the shipped JavaScript interaction checks.")
        result = subprocess.run([node, str(ROOT / "tests/site_interactions.js")],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
