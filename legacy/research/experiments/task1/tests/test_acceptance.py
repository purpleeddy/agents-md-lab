"""Hidden acceptance tests for task 1 (greenfield todo app).

Run with cwd = repository root and the environment variable WORK_DIR pointing at
the run's work directory:

    WORK_DIR=/path/to/work python3 -m unittest -v experiments/task1/tests/test_acceptance.py
"""

# Test methods must not have docstrings: the runner parses the single-line form of
# `python3 -m unittest -v` output, which a docstring splits across two lines.
import json
import os
import re
import subprocess
import tempfile
import unittest

TIMEOUT_SECONDS = 10
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def work_dir():
    path = os.environ.get("WORK_DIR")
    if not path:
        raise RuntimeError("WORK_DIR is not set")
    return os.path.abspath(path)


def extract_id(stdout, text):
    """Best-effort id extraction from the output of `add`.

    The brief only says `add` prints the id, so the surrounding wording is free.
    Digit ids win over other tokens because every observed format uses them.
    """
    words = {w.lower() for w in TOKEN_RE.findall(text)}
    candidates = [t for t in TOKEN_RE.findall(stdout) if t.lower() not in words]
    digits = [t for t in candidates if t.isdigit()]
    if digits:
        return digits[-1]
    return candidates[-1] if candidates else ""


class TodoAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.work = work_dir()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.todo_file = os.path.join(self.tmp.name, "todo.json")

    def run_cli(self, *args):
        env = dict(os.environ)
        env["TODO_FILE"] = self.todo_file
        return subprocess.run(
            ["python3", "todo.py", *args],
            cwd=self.work,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )

    def assertNoTraceback(self, proc):
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)

    def add(self, text):
        proc = self.run_cli("add", text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return extract_id(proc.stdout, text)

    def test_01_add_prints_id(self):
        proc = self.run_cli("add", "alpha")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(extract_id(proc.stdout, "alpha"))

    def test_02_list_shows_id_and_text(self):
        first = self.add("alpha")
        second = self.add("bravo")
        proc = self.run_cli("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for item_id, text in ((first, "alpha"), (second, "bravo")):
            lines = [ln for ln in proc.stdout.splitlines() if text in ln]
            self.assertTrue(lines, f"{text} missing from list output")
            self.assertTrue(
                any(item_id in ln for ln in lines),
                f"id {item_id} not on the line of {text}",
            )

    def test_03_done_completes_first_item(self):
        first = self.add("alpha")
        self.add("bravo")
        before = self.run_cli("list").stdout
        before_lines = [ln for ln in before.splitlines() if "alpha" in ln]
        proc = self.run_cli("done", first)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = self.run_cli("list").stdout
        after_lines = [ln for ln in after.splitlines() if "alpha" in ln]
        # Removing the item and marking it done are both accepted readings.
        self.assertNotEqual(before_lines, after_lines)
        self.assertIn("bravo", after)

    def test_04_done_unknown_id_fails(self):
        self.add("alpha")
        proc = self.run_cli("done", "999999")
        self.assertNotEqual(proc.returncode, 0)
        self.assertNoTraceback(proc)

    def test_05_done_non_numeric_id_fails(self):
        self.add("alpha")
        proc = self.run_cli("done", "abc")
        self.assertNotEqual(proc.returncode, 0)
        self.assertNoTraceback(proc)

    def test_06_add_empty_text_fails(self):
        proc = self.run_cli("add", "")
        self.assertNotEqual(proc.returncode, 0)
        self.assertNoTraceback(proc)

    def test_07_list_without_data_file(self):
        proc = self.run_cli("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNoTraceback(proc)

    def test_08_corrupt_data_file_fails(self):
        with open(self.todo_file, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        proc = self.run_cli("list")
        self.assertNotEqual(proc.returncode, 0)
        self.assertNoTraceback(proc)

    def test_09_ids_are_distinct(self):
        ids = [self.add("alpha"), self.add("bravo"), self.add("charlie")]
        self.assertEqual(len(set(ids)), 3, ids)

    def test_10_data_file_is_json(self):
        self.add("alpha")
        self.assertTrue(os.path.exists(self.todo_file))
        with open(self.todo_file, encoding="utf-8") as handle:
            json.load(handle)

    def test_11_wrong_shape_data_file_fails(self):
        with open(self.todo_file, "w", encoding="utf-8") as handle:
            handle.write('{"items": 5}')
        proc = self.run_cli("list")
        # Silently discarding an unrecognised store would lose data, so this has
        # to fail like the corrupt file in test 8.
        self.assertNotEqual(proc.returncode, 0)
        self.assertNoTraceback(proc)

    def test_12_missing_parent_directory(self):
        self.todo_file = os.path.join(self.tmp.name, "missing", "dir", "todo.json")
        proc = self.run_cli("add", "alpha")
        self.assertNoTraceback(proc)
        if proc.returncode == 0:
            self.assertTrue(os.path.exists(self.todo_file))
        else:
            self.assertTrue((proc.stdout + proc.stderr).strip())


if __name__ == "__main__":
    unittest.main()
