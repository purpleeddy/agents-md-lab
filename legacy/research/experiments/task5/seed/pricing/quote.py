"""Totals for a basket of line items."""

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£"}


def quote(items, discount=0.0, currency="USD"):
    """Total `items` and return it as a formatted amount.

    `items` is a sequence of (name, cents) pairs. `discount` is a fraction of the
    total to take off, from 0.0 up to but not including 1.0. `currency` picks the
    symbol the amount is written with.
    """
    if not 0.0 <= discount < 1.0:
        raise ValueError("discount must be at least 0.0 and below 1.0")
    if currency not in CURRENCY_SYMBOLS:
        raise ValueError(f"unknown currency: {currency}")
    cents = sum(int(price) for _name, price in items)
    return format_amount(int(cents * (1.0 - discount)), currency)


def format_amount(cents, currency="USD"):
    """`cents` written with the symbol for `currency`."""
    symbol = CURRENCY_SYMBOLS[currency]
    sign = "-" if cents < 0 else ""
    return f"{sign}{symbol}{abs(cents) // 100}.{abs(cents) % 100:02d}"
