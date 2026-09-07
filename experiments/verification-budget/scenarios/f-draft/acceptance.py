import importlib.util
import os
import pathlib
import unittest


def load_total():
    path = pathlib.Path(os.environ["WORK_DIR"]) / "calculator.py"
    spec = importlib.util.spec_from_file_location("candidate_calculator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.total


class Acceptance(unittest.TestCase):
    def test_existing_total_behavior_is_restored(self):
        self.assertEqual(load_total()(10), 10)

    def test_draft_discount_feature_is_preserved(self):
        self.assertEqual(load_total()(10, discount=3), 7)


if __name__ == "__main__":
    unittest.main()
