import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class ReadmeTest(unittest.TestCase):
    def test_no_typo(self):
        with open(os.path.join(HERE, "..", "README.md"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("recieve", text)
        self.assertIn("receive", text)


if __name__ == "__main__":
    unittest.main()
