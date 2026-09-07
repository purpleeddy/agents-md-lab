# pricing

Line-item quotes for the parts catalogue, plus the rounding helpers the monthly
report uses.

## Install

Copy the `pricing/` directory next to your code. There is nothing to build.

## Usage

    from pricing import quote

    total = quote(items)

`quote()` takes a list of `(name, cents)` pairs and returns the total in cents.

## Development

`CONTRIBUTING.md` has the commands.
