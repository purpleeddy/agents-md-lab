import json
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = dict(os.environ, TODO_FILE=os.path.join(self.tmp.name, "todo.json"))

    def run_cli(self, *args):
        return subprocess.run(["python3", "todo.py", *args], cwd=HERE, env=self.env,
                              capture_output=True, text=True)

    def test_add_prints_id(self):
        proc = self.run_cli("add", "write tests")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "1")

    def test_list_shows_items(self):
        self.run_cli("add", "write tests")
        proc = self.run_cli("list")
        self.assertIn("write tests", proc.stdout)

    def test_done_marks_item(self):
        self.run_cli("add", "write tests")
        self.assertEqual(self.run_cli("done", "1").returncode, 0)
        self.assertIn("[x]", self.run_cli("list").stdout)

    def test_invalid_id_exits_non_zero(self):
        self.assertNotEqual(self.run_cli("done", "abc").returncode, 0)


if __name__ == "__main__":
    unittest.main()
