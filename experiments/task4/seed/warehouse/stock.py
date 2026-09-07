"""Reading the stock export and reporting what has to be reordered."""

import csv
from collections import namedtuple

Item = namedtuple("Item", "sku name quantity status")

STATUSES = ("active", "discontinued")


def load_items(path):
    """Every row of the stock export, in file order."""
    items = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            status = (row.get("status") or "active").strip()
            if status not in STATUSES:
                raise ValueError("unknown status: %s" % status)
            items.append(
                Item(row["sku"].strip(), row["name"].strip(), int(row["quantity"]), status)
            )
    return items


def low_stock(items, threshold):
    """Items under the reorder threshold, lowest quantity first."""
    below = [item for item in items if item.quantity < threshold]
    return sorted(below, key=lambda item: (item.quantity, item.sku))


def total_quantity(items):
    return sum(item.quantity for item in items)
