# Contributing

## Commands

```
python3 -m unittest                            # test all
python3 -m unittest tests.test_experiment      # test one
python3 scripts/compare.py --check             # every generated block matches the data
python3 scripts/experiment.py --dry-run        # the scoring fixtures
```

Python 3.11 or newer, standard library only; there is nothing to install. There is no build,
lint, typecheck or format command; do not invent one.

## Generated files, never edited by hand

`docs/data/`, `docs/generated/`, and anything above the "Lock" heading in
`experiments/README.md`. The first two are written by `scripts/compare.py`; the third is a
pre-registration, and editing it after the tag invalidates the experiment.

## Where the details live

- [`docs/methodology.md`](docs/methodology.md): sources, corpus rules, how a verdict is decided.
- [`docs/rationale.md`](docs/rationale.md): why each rule of the root `AGENTS.md` exists.
- [`docs/references.md`](docs/references.md): every citation key, with its date read.
- [`experiments/README.md`](experiments/README.md): the experiment as it was pre-registered.

## Proposing a corpus file

Open an issue with one `[[files]]` entry for `corpus.toml`, pinned by commit, and one sentence
saying what the file shows that the others do not. Counter-examples are as welcome: a file that
meets a criterion the check calls unmet, or misses one it calls met, is a defect in the pattern.
Quote the line and name the criterion; each criterion carries its known false positives and
negatives in `notes` in `docs/criteria.json`.

## License

MIT, for the code, the data and the pages. Corpus files stay under their own licenses and are
never redistributed here. `agents.md` is stewarded by the Agentic AI Foundation; this project is
not affiliated with it or with any vendor whose documentation is cited.
