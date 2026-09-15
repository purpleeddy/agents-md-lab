# warehouse

Stock levels for one warehouse instance. It reads the stock export and reports which
SKUs have fallen below their reorder threshold.

The working records live in `var/store/`. They belong to the instance this checkout
runs and are written by the nightly count, not by the test suite.

## Development

Run the test suite with `make test`.
