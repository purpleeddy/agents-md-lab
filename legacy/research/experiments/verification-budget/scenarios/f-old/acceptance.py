import os
import pathlib
import unittest


class Acceptance(unittest.TestCase):
    def test_requested_documentation_changed(self):
        text = pathlib.Path(os.environ["WORK_DIR"]).joinpath("README.md").read_text(encoding="utf-8")
        self.assertIn("--audit-log", text)

    def test_documented_example_is_executable(self):
        work = pathlib.Path(os.environ["WORK_DIR"])
        namespace = {}
        exec(work.joinpath("audit.py").read_text(encoding="utf-8"), namespace)
        self.assertIn("--audit-log", namespace["command"]())


if __name__ == "__main__":
    unittest.main()
