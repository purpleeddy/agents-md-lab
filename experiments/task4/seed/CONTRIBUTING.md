# Contributing

Keep changes under `warehouse/` small, and add a case to `tests/` when behaviour changes.

The unit tests are plain `unittest`: `python3 -m unittest` from the repository root runs
them. `make test` is the wrapper CI uses, on a fresh container.
