import unittest
from calculator import total


class CalculatorTest(unittest.TestCase):
    def test_existing_total_behavior(self):
        self.assertEqual(total(10), 10)

    def test_discount_is_applied(self):
        self.assertEqual(total(10, discount=3), 7)
