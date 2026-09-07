import pathlib
import subprocess
import sys
import unittest


class DocumentationTest(unittest.TestCase):
    def test_cache_dir_is_documented(self):
        text = pathlib.Path("README.md").read_text(encoding="utf-8")
        self.assertIn("python3 docs.py build --cache-dir .cache", text)

    def test_documented_command_executes(self):
        completed = subprocess.run(
            [sys.executable, "docs.py", "build", "--cache-dir", "example-cache"],
            capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("example-cache", completed.stdout)


if __name__ == "__main__":
    unittest.main()
