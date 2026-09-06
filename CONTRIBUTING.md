# Contributing

## Commands

```
python3 -m unittest                            # test all
python3 -m unittest tests.test_experiment      # test one
python3 scripts/compare.py --check             # every generated block matches the data
python3 scripts/experiment.py --dry-run        # the fixture check
```

`python3 scripts/experiment.py summarize --runs <dir>… --out <file>` writes the summary and a
sibling `<file>-runs.json`; `--markdown` also prints the tables.

Python 3.11 or newer, standard library only. There is no build, lint, typecheck or format
command; do not invent one.

## Permission settings

The tiers this project recommends, in four levels. Deny the nine things nothing takes back:
`rm -rf`, `git clean`, `git reset --hard`, the three force-push forms, `git commit --no-verify`
and `-n`, and `gh pr merge`. Guard what must be read, not matched by name: a push that
targets `main` or `master`, one carrying a force flag or a `+` refspec, and a write to
`.claude/`, `.github/workflows/` or the guard itself. Allow everything else, including a push of
the branch a task created and `gh pr create`, so a session delivers its own work and a person
merges it. Behind all three, the branch protection below.

[`scripts/hook_guard.py`](scripts/hook_guard.py) implements the guard tier: it reads a
`PreToolUse` payload on stdin and exits 2 with a reason on stderr for exactly those pushes and
writes. `tests/test_hook_guard.py` proves that case by case.

The guard is wired here: `.claude/settings.json` is byte for byte
[`docs/examples/settings.json`](docs/examples/settings.json), so those tiers are what a session
in this repository runs under. That is looser than the shipped `AGENTS.md`, whose Boundaries
override this file and hold every push behind an explicit ask: the deny list is a floor and not
a licence. One line installs the same file in an adopting repository:

```
cp docs/examples/settings.json .claude/settings.json
```

A person runs that line: the settings reserve `.claude/` for a human ask, so an agent session
cannot install the permissions it works under. Both hook entries run the same wrapper:

```
sh -c 'g="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/hook_guard.py"; [ -f "$g" ] || exit 0; exec python3 "$g"'
```

which falls back to the working directory when the variable is unset and exits 0 when the script
is missing, so a checkout without it works rather than refusing every tool call. A command
written in a form the guard cannot parse goes through: the guarantee is the branch protection
below.

## Branch protection

A ruleset on `main` requires a pull request and blocks force-push and deletion. It asks for zero
approvals, because this repository has one maintainer and a rule nobody can satisfy is a rule
that gets bypassed; an adopter with a second maintainer should raise the count.

## Changing AGENTS.md

The root `AGENTS.md` is what the `ours` condition of the experiment writes, so changing it
changes the thing under test. Every rule line has a row in
[`docs/rationale.md`](docs/rationale.md), and the text under test is pinned by sha256 in
[`experiments/README.md`](experiments/README.md). Open a change as an issue first, saying which
row it edits and what it does to that sha.

## Generated files, never edited by hand

`docs/data/` and `docs/generated/`, written by `scripts/compare.py`, and anything above the
"Lock" heading in `experiments/README.md`, where an edit after the tag invalidates the
experiment.

## Where the details live

- [`docs/methodology.md`](docs/methodology.md): sources, corpus rules, how a verdict is decided.
- [`docs/rationale.md`](docs/rationale.md): why each rule exists.
- [`docs/references.md`](docs/references.md): every citation key and date read.
- [`experiments/README.md`](experiments/README.md): the pre-registration.

## Proposing a corpus file

Open an issue with one `[[files]]` entry for `corpus.toml`, pinned by commit, and one sentence
saying what the file shows that the others do not. Counter-examples are as welcome: a file that
meets a criterion the check calls unmet, or misses one it calls met, is a defect in the pattern.
Each criterion's known false positives and negatives are in its `notes` in
`docs/criteria.json`.

## License

MIT, for the code, the data and the pages. Corpus files stay under their own licenses and are
never redistributed here. The README carries the non-affiliation notice.
