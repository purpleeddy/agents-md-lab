import importlib.util
import os
import pathlib
import unittest


def load_increment():
    path = pathlib.Path(os.environ["WORK_DIR"]) / "counter.py"
    spec = importlib.util.spec_from_file_location("candidate_counter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.increment


class Acceptance(unittest.TestCase):
    def test_increment_is_fixed(self):
        self.assertEqual(load_increment()(4), 5)


if __name__ == "__main__":
    unittest.main()
