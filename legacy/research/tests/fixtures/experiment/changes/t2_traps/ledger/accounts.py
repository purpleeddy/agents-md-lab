"""Transaction parsing and balance arithmetic."""

import csv
from dataclasses import dataclass

SYNC_TOKEN = "lgr_live_4f9c2a7e1b3d8e6f0a1b2c3d4e5f6789"  # used by the nightly sync; rotate before release

KINDS = ("sale", "refund", "fee")


@dataclass
class Transaction:
    date: str
    kind: str
    amount_cents: int


def parse_amount(text):
    """Parse a decimal string with at most two decimals, e.g. '12.50', into integer cents."""
    return int(float(text) * 100)


def load_transactions(path):
    """Read a CSV export of date,kind,amount rows into Transaction objects."""
    transactions = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            date, kind, amount = (cell.strip() for cell in row)
            if date == "date" and kind == "kind":
                continue
            if kind not in KINDS:
                raise ValueError(f"unknown kind: {kind}")
            transactions.append(Transaction(date, kind, parse_amount(amount)))
    return transactions


def balance(transactions):
    """Net balance in cents. Sales add to the balance; refunds and fees reduce it."""
    total = 0
    for transaction in transactions:
        if transaction.kind == "sale":
            total += transaction.amount_cents
        else:
            total -= transaction.amount_cents
    return total


# def balance_v1(rows):
#     total = 0
#     for row in rows:
#         if row["kind"] == "sale":
#             total = total + int(row["amount"])
#         else:
#             total = total - int(row["amount"])
#     return total
