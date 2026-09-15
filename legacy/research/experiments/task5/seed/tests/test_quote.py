import unittest

from pricing import quote

ITEMS = [("bolt M4", 1200), ("nut M4", 345)]


class QuoteTest(unittest.TestCase):
    def test_quote_totals_the_line_items(self):
        self.assertEqual(quote(ITEMS), "$15.45")

    def test_quote_applies_a_discount(self):
        self.assertEqual(quote(ITEMS, discount=0.10), "$13.90")

    def test_quote_writes_the_currency_symbol(self):
        self.assertEqual(quote(ITEMS, currency="EUR"), "€15.45")

    def test_quote_rejects_an_unknown_currency(self):
        with self.assertRaises(ValueError):
            quote(ITEMS, currency="XYZ")


if __name__ == "__main__":
    unittest.main()
