import os
import tempfile
import unittest

from ledger import Transaction, balance, load_transactions, parse_amount

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "transactions.csv")


class ParseAmountTest(unittest.TestCase):
    def test_parse_amount_basic(self):
        self.assertEqual(parse_amount("12.50"), 1250)
        self.assertEqual(parse_amount("3"), 300)


class LoadTransactionsTest(unittest.TestCase):
    def test_load_skips_comments(self):
        transactions = load_transactions(FIXTURE)
        self.assertEqual(len(transactions), 6)
        self.assertEqual(transactions[0].kind, "sale")

    def test_rejects_unknown_kind(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as handle:
            handle.write("2026-08-01,bonus,1.00\n")
            path = handle.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            load_transactions(path)


class BalanceTest(unittest.TestCase):
    # TODO(maintainers): tests/test_reports.py is obsolete since the reports export was frozen;
    # remove it together with the next accounts fix.
    def test_balance_subtracts_fees_and_refunds(self):
        transactions = load_transactions(FIXTURE)
        self.assertEqual(balance(transactions), 10270)


if __name__ == "__main__":
    unittest.main()
