# Contributing

## Commands

```
python3 -m unittest                            # test all
python3 -m unittest tests.test_experiment      # test one
python3 scripts/compare.py --check             # every generated block matches the data
python3 scripts/experiment.py --dry-run        # the fixture check
```

`python3 scripts/experiment.py summarize --runs <dir>… --out <file>` writes the summary and a
sibling `<file>-runs.json`; add `--markdown` to print the per-run, comparison and headline
tables to stdout as well.

Python 3.11 or newer, standard library only; there is nothing to install. There is no build,
lint, typecheck or format command; do not invent one.

## Permission settings

These are the tiers this project recommends, in four levels. Deny what nothing takes back:
`rm -rf`, `git clean`, `git reset --hard`, the three force-push forms, `git commit --no-verify`
and `-n`, and `gh pr merge`. Guard what has to be read rather than matched by name: a push that
targets `main` or `master`, one carrying a force flag or a `+` refspec, and a write to
`.claude/`, `.github/workflows/` or the guard itself. Allow everything else, including a push of
the branch a task created and `gh pr create`, so an agent session delivers its own work and a
person merges it. Behind all three, the branch protection below.

[`scripts/hook_guard.py`](scripts/hook_guard.py) implements the guard tier: it reads a
`PreToolUse` payload on stdin and exits 2 with a reason on stderr for exactly those pushes and
writes. `tests/test_hook_guard.py` proves its behaviour by running it, case by case.

The guard is wired here. `.claude/settings.json` is byte for byte the file checked in at
[`docs/examples/settings.json`](docs/examples/settings.json), so the four tiers above are the
permissions a session in this repository runs under: the nine deny entries, both `PreToolUse`
matchers pointed at the guard, and delivery left allowed, so a session can push the branch it
created for its task and open a pull request. One line installs the same file in an adopting
repository:

```
cp docs/examples/settings.json .claude/settings.json
```

A person runs that line, here as well as there: the settings reserve `.claude/` for a human ask,
so an agent session cannot install the permissions it works under, and one that could would be
the reason not to trust them. Both hook entries run the same wrapper:

```
sh -c 'g="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/hook_guard.py"; [ -f "$g" ] || exit 0; exec python3 "$g"'
```

which falls back to the working directory when the variable is unset and exits 0 when the script
is missing, so a checkout without it works rather than refusing every tool call. The hook is a
convenience even now that it runs: a command written in a form it cannot parse goes through,
which is why the guarantee is the branch protection below.

## Branch protection

A ruleset on `main` requires a pull request and blocks force-push and deletion. It asks for zero
approvals, because this repository has one maintainer and a rule nobody can satisfy is a rule
that gets bypassed; an adopter with a second maintainer should raise the count.

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
