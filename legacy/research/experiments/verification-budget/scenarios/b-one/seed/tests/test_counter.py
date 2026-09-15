import unittest
from counter import increment


class CounterTest(unittest.TestCase):
    def test_increment(self):
        self.assertEqual(increment(4), 5)
