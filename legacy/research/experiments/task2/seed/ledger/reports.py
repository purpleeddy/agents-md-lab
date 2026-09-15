"""Aggregate reports over transactions."""

from .accounts import balance


def summary(transactions):
    """Count transactions per kind and report the totals in cents."""
    counts = {}
    totals = {}
    for transaction in transactions:
        counts[transaction.kind] = counts.get(transaction.kind, 0) + 1
        totals[transaction.kind] = totals.get(transaction.kind, 0) + transaction.amount_cents
    return {"counts": counts, "totals": totals, "balance": balance(transactions)}
