"""Hidden acceptance tests for task 3 (one-line typo fix in the ledger seed).

Run with cwd = repository root and the environment variable WORK_DIR pointing at
the run's work directory:

    WORK_DIR=/path/to/work python3 -m unittest -v experiments/task3/tests/test_acceptance.py
"""

# Test methods must not have docstrings: the runner parses the single-line form of
# `python3 -m unittest -v` output, which a docstring splits across two lines.
import difflib
import os
import unittest

SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "task2", "seed")
IGNORED_DIRS = (".claude", "__pycache__")
IGNORED_NAMES = ("CLAUDE.md", "AGENTS.md", ".DS_Store", ".gitkeep")
TYPO = "recieve"
FIXED = "receive"


def work_dir():
    path = os.environ.get("WORK_DIR")
    if not path:
        raise RuntimeError("WORK_DIR is not set")
    return os.path.abspath(path)


def relevant_files(root):
    found = {}
    for directory, subdirs, names in os.walk(root):
        subdirs[:] = [name for name in subdirs if name not in IGNORED_DIRS]
        for name in names:
            if name in IGNORED_NAMES or name.endswith(".pyc"):
                continue
            path = os.path.join(directory, name)
            found[os.path.relpath(path, root)] = path
    return found


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


class TypoFixAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.work = work_dir()
        self.seed = os.path.abspath(SEED_DIR)

    def test_typo_fixed(self):
        path = os.path.join(self.work, "README.md")
        self.assertTrue(os.path.exists(path), "README.md is missing")
        text = read_text(path)
        self.assertIn(FIXED, text)
        self.assertNotIn(TYPO, text)

    def test_no_other_file_changed(self):
        seed_files = relevant_files(self.seed)
        work_files = relevant_files(self.work)
        self.assertEqual(
            sorted(set(seed_files) - set(work_files)), [], "seed files are missing from the work dir"
        )
        self.assertEqual(
            sorted(set(work_files) - set(seed_files)), [], "the work dir has extra files"
        )
        changed = [
            name
            for name in sorted(seed_files)
            if name != "README.md" and read_bytes(seed_files[name]) != read_bytes(work_files[name])
        ]
        self.assertEqual(changed, [], "files other than README.md were changed")

    def test_readme_changed_on_one_line(self):
        seed_lines = read_text(os.path.join(self.seed, "README.md")).splitlines()
        work_lines = read_text(os.path.join(self.work, "README.md")).splitlines()
        opcodes = difflib.SequenceMatcher(None, seed_lines, work_lines).get_opcodes()
        edits = [code for code in opcodes if code[0] != "equal"]
        # At most one edit: an unchanged README is minimal too, and test_typo_fixed
        # is what reports a README that was never fixed.
        self.assertLessEqual(len(edits), 1, f"expected at most one edited line, got {edits}")
        for tag, i1, i2, j1, j2 in edits:
            self.assertEqual(tag, "replace", f"expected a replaced line, got {tag}")
            self.assertEqual((i2 - i1, j2 - j1), (1, 1), "expected exactly one line replaced")


if __name__ == "__main__":
    unittest.main()
