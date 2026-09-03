# Contributing

## Commands

```
python3 -m unittest                            # test all
python3 -m unittest tests.test_experiment      # test one
python3 scripts/compare.py --check             # every generated block matches the data
python3 scripts/experiment.py --dry-run        # the scoring fixtures
```

`python3 scripts/experiment.py summarize --runs <dir>… --out <file>` writes the summary and a
sibling `<file>-runs.json`; add `--markdown` to print the per-run, comparison and headline
tables to stdout as well.

Python 3.11 or newer, standard library only; there is nothing to install. There is no build,
lint, typecheck or format command; do not invent one.

## Changing AGENTS.md

The root `AGENTS.md` is the file this project publishes and the file the `ours` condition of the
experiment writes, so a change to it is a change to the thing under test. Every rule line carries
a row in [`docs/rationale.md`](docs/rationale.md) naming its source, and the text under test is
pinned by sha256 in [`experiments/README.md`](experiments/README.md). A proposed change should say
which row it adds or edits and what it does to that sha; open it as an issue first.

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
