import unittest

from pricing import average_unit_price, round_half_even


class RoundingTest(unittest.TestCase):
    def test_round_half_even_rounds_to_two_places(self):
        self.assertEqual(round_half_even(1.234), 1.23)
        self.assertEqual(round_half_even(1.236), 1.24)

    def test_round_half_even_rounds_a_tie_up_to_even(self):
        # 2.675 sits exactly between 2.67 and 2.68, so the even digit wins.
        self.assertEqual(round_half_even(2.675), 2.68)

    def test_average_unit_price_of_an_empty_basket_is_zero(self):
        self.assertEqual(average_unit_price([]), 0.0)


if __name__ == "__main__":
    unittest.main()
