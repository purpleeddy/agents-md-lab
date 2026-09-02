# results/v1

Machine-generated outputs of `make check`. Do not edit by hand.

## `checks.csv`

| column | type | meaning |
|---|---|---|
| `file` | string | manifest `key`, or `author` for `src/AGENTS.md` |
| `check_id` | string | check id from the registry in `scripts/lint.py` |
| `applicable` | `true` / `false` | whether the check applies to this file's type and filename |
| `pass` | `true` / `false` / empty | empty when not applicable or when the check is a measurement (`measure-*`) |
| `value` | number or empty | the measured quantity (lines, count, density) when the check has one |
| `line` | integer or empty | 1-based line of the first matching evidence, when there is one |

Rows are in manifest order, then registry order. The author's file comes last.

## `run.json`

Written only when `checks.csv` changes: results version, creation time, Python version, sha256 of `scripts/lint.py` and of the lock file, file and check counts.

Licensing: these results are derived data and are published under CC-BY-4.0. They contain no text from the source files.
