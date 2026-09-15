"""Rounding helpers for the monthly catalogue report.

Nothing here is on the path of `quote()`; the report imports these directly.
"""


def round_half_even(value, places=2):
    """Round `value` to `places` decimals, ties going to the even digit."""
    return round(value, places)


def average_unit_price(prices_in_cents):
    """The mean of `prices_in_cents`, in whole currency units."""
    if not prices_in_cents:
        return 0.0
    return round_half_even(sum(prices_in_cents) / len(prices_in_cents) / 100.0)
