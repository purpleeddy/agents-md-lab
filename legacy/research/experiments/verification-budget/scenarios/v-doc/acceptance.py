import os
import pathlib
import subprocess
import sys
import unittest


class Acceptance(unittest.TestCase):
    def test_readme_has_executable_example(self):
        text = pathlib.Path(os.environ["WORK_DIR"]).joinpath("README.md").read_text(encoding="utf-8")
        self.assertIn("python3 docs.py build --cache-dir .cache", text)

    def test_example_command_runs(self):
        work = os.environ["WORK_DIR"]
        completed = subprocess.run(
            [sys.executable, "docs.py", "build", "--cache-dir", "acceptance-cache"],
            cwd=work, capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("acceptance-cache", completed.stdout)


if __name__ == "__main__":
    unittest.main()
