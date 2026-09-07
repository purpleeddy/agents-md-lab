import os
import tempfile
import unittest

from warehouse import load_items, low_stock, total_quantity

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "items.csv")


class StockTest(unittest.TestCase):
    def setUp(self):
        self.items = load_items(FIXTURE)

    def test_load_items_reads_every_row(self):
        self.assertEqual(len(self.items), 5)
        self.assertEqual(self.items[0].sku, "A-100")
        self.assertEqual(self.items[0].quantity, 4)

    def test_load_items_rejects_an_unknown_status(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as handle:
            handle.write("sku,name,quantity,status\nZ-1,Mystery,1,retired\n")
            path = handle.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            load_items(path)

    def test_low_stock_lists_an_active_item_under_the_threshold(self):
        skus = [item.sku for item in low_stock(self.items, 5)]
        self.assertIn("A-100", skus)
        self.assertNotIn("A-101", skus)

    def test_low_stock_is_sorted_by_quantity(self):
        quantities = [item.quantity for item in low_stock(self.items, 5)]
        self.assertEqual(quantities, sorted(quantities))

    def test_total_quantity_sums_every_item(self):
        self.assertEqual(total_quantity(self.items), 25)


if __name__ == "__main__":
    unittest.main()
