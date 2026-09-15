import os
import unittest

from ledger import load_transactions
from ledger.reports import summary

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "transactions.csv")


class SummaryTest(unittest.TestCase):
    def test_counts_per_kind(self):
        result = summary(load_transactions(FIXTURE))
        self.assertEqual(result["counts"], {"sale": 3, "refund": 1, "fee": 2})

    def test_totals_include_every_kind(self):
        result = summary(load_transactions(FIXTURE))
        self.assertEqual(set(result["totals"]), {"sale", "refund", "fee"})
        self.assertGreater(result["totals"]["sale"], 0)


if __name__ == "__main__":
    unittest.main()
