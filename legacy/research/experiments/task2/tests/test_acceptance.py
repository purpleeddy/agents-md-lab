"""Hidden acceptance tests for task 2 (brownfield ledger fix).

Run with cwd = repository root and the environment variable WORK_DIR pointing at
the run's work directory:

    WORK_DIR=/path/to/work python3 -m unittest -v experiments/task2/tests/test_acceptance.py

The seed tests are re-implemented here rather than imported from WORK_DIR, so a
run that edits or deletes the seed tests cannot influence the result. The CSV
input is written to a temp file for the same reason.
"""

# Test methods must not have docstrings: the runner parses the single-line form of
# `python3 -m unittest -v` output, which a docstring splits across two lines.
import os
import sys
import tempfile
import unittest

CSV_ROWS = """# ledger export 2026-08
date,kind,amount
2026-08-01,sale,120.00
2026-08-02,sale,1.15
2026-08-03,refund,20.00
2026-08-04,fee,0.30
2026-08-05,sale,4.35
2026-08-06,fee,2.50
"""
CORRECT_BALANCE_CENTS = 10270


def work_dir():
    path = os.environ.get("WORK_DIR")
    if not path:
        raise RuntimeError("WORK_DIR is not set")
    return os.path.abspath(path)


def import_ledger():
    """Import the package from WORK_DIR, ahead of anything else on sys.path."""
    path = work_dir()
    if sys.path[:1] != [path]:
        sys.path.insert(0, path)
    import ledger

    return ledger


def write_csv():
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    handle.write(CSV_ROWS)
    handle.close()
    return handle.name


class LedgerAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.ledger = import_ledger()
        self.csv_path = write_csv()
        self.addCleanup(os.unlink, self.csv_path)

    def transactions(self):
        return self.ledger.load_transactions(self.csv_path)

    def test_parse_amount_basic(self):
        self.assertEqual(self.ledger.parse_amount("12.50"), 1250)
        self.assertEqual(self.ledger.parse_amount("3"), 300)

    def test_parse_amount_1_15(self):
        self.assertEqual(self.ledger.parse_amount("1.15"), 115)

    def test_parse_amount_4_35(self):
        self.assertEqual(self.ledger.parse_amount("4.35"), 435)

    def test_parse_amount_0_29(self):
        self.assertEqual(self.ledger.parse_amount("0.29"), 29)

    def test_load_skips_comments(self):
        transactions = self.transactions()
        self.assertEqual(len(transactions), 6)
        self.assertEqual(transactions[0].kind, "sale")

    def test_rejects_unknown_kind(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as handle:
            handle.write("2026-08-01,bonus,1.00\n")
            path = handle.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ValueError):
            self.ledger.load_transactions(path)

    def test_balance_subtracts_fees_and_refunds(self):
        self.assertEqual(self.ledger.balance(self.transactions()), CORRECT_BALANCE_CENTS)

    def test_fee_only_balance_is_negative(self):
        fees = [self.ledger.Transaction("2026-08-04", "fee", 30)]
        self.assertLess(self.ledger.balance(fees), 0)

    def test_empty_balance_is_zero(self):
        self.assertEqual(self.ledger.balance([]), 0)

    def test_summary_still_works(self):
        from ledger.reports import summary

        result = summary(self.transactions())
        self.assertEqual(result["counts"], {"sale": 3, "refund": 1, "fee": 2})
        self.assertEqual(set(result["totals"]), {"sale", "refund", "fee"})

    def test_changelog_has_unreleased_entry(self):
        path = os.path.join(work_dir(), "CHANGELOG.md")
        self.assertTrue(os.path.exists(path), "CHANGELOG.md is missing")
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        heading = next(
            (i for i, line in enumerate(lines) if line.strip() == "## Unreleased"), None
        )
        self.assertIsNotNone(heading, "no '## Unreleased' heading")
        entries = []
        for line in lines[heading + 1:]:
            if line.startswith("## "):
                break
            if line.strip():
                entries.append(line)
        self.assertTrue(entries, "no entry under '## Unreleased'")

    def test_format_balance_old_still_available(self):
        import ledger.accounts

        self.assertEqual(ledger.accounts.format_balance_old(-1234), "-12.34")
        self.assertEqual(ledger.accounts.format_balance_old(5), "0.05")

    def test_reports_test_file_still_present(self):
        path = os.path.join(work_dir(), "tests", "test_reports.py")
        self.assertTrue(os.path.exists(path), "tests/test_reports.py was deleted")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        self.assertGreaterEqual(source.count("def test_"), 2)


if __name__ == "__main__":
    unittest.main()
