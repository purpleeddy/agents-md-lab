# pricing

Line-item quotes for the parts catalogue, plus the rounding helpers the monthly
report uses.

## Install

Copy the `pricing/` directory next to your code. There is nothing to build.

## Usage

    from pricing import quote

    total = quote(items)
    discounted = quote(items, discount=0.10, currency="EUR")

`quote()` takes a list of `(name, cents)` pairs, an optional `discount` (a
fraction of the total to take off, from 0.0 up to but not including 1.0) and an
optional `currency` (`USD`, `EUR` or `GBP`, `USD` by default). It returns the
total as a formatted amount string, such as `$15.45`, not as an integer.

## Development

`CONTRIBUTING.md` has the commands.
