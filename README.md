# agents-md-lab

What belongs in an instruction file for a coding agent, measured twice. Ten published
`AGENTS.md` and `CLAUDE.md` files are pinned by commit and evaluated line by line against ten
criteria drawn from vendor documentation, practitioner guides and three studies; then a
pre-registered experiment runs three tasks under three conditions — no instruction file, a
pinned public file, and the file in this repository — to see what an instruction file changes,
in both directions. Coverage of criteria describes what a file contains. It is not a quality
measure, and no file here is put above another.

Site: <https://purpleeddy.github.io/agents-md-lab/>

## Adopt the file

The file is `AGENTS.md` v1.0.1: the text the experiment ran, with two rules amended after an
independent review. What changed and what it means for the results is in
[methodology](docs/methodology.md#what-the-experiment-tested-and-what-is-shipped).

1. Download [`AGENTS.md`](AGENTS.md) into your repository root.
2. Add a `CLAUDE.md` next to it whose only line is `@AGENTS.md`, so Claude Code loads the same
   rules the other agents read.
3. Fill the `## Project` section: stack, the commands that verify a change, what is generated,
   and where the details live. That section is the part no one else can write for you.

## What the survey found

<!-- summary:start -->
| File | Type | Stars | Lines | License | Criteria met |
| --- | --- | --- | --- | --- | --- |
| [openai/agents.md](https://github.com/openai/agents.md/blob/ba9474a69e9a2c0c4176713843b78e8f54377941/AGENTS.md) | AGENTS.md | 24,088 | 43 | MIT | 4/10 |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/blob/7057f3318b938a2dd095fd89f786c11772b08197/CLAUDE.md) | CLAUDE.md | 8,782 | 44 | MIT | 3/10 |
| [getsentry/sentry](https://github.com/getsentry/sentry/blob/7395d32708261ef723e33be460da1641c36a9e0e/AGENTS.md) | AGENTS.md | 44,714 | 137 | FSL-1.1-ALv2 | 5/10 |
| [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty/blob/9897d6caba05c0cbf256f86bec2e2935f164a9c7/AGENTS.md) | AGENTS.md | 60,629 | 39 | MIT | 4/10 |
| [temporalio/temporal](https://github.com/temporalio/temporal/blob/109a38e8ca4827ae8c624fc1a9382290dcae0f69/AGENTS.md) | AGENTS.md | 22,796 | 105 | MIT | 6/10 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/8462496b34419f20b32778610571ac723e91f94c/CLAUDE.md) | CLAUDE.md | 209,759 | 65 | NONE | 5/10 |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer/blob/6014ccf95edf71b2d0ba31bcd65a9297a3decb65/CLAUDE.md) | CLAUDE.md | 11,369 | 88 | Apache-2.0 | 4/10 |
| [omacom/omarchy](https://github.com/omacom/omarchy/blob/1c8f728b25cb8a42f1d02e4d2441230132cedb6c/AGENTS.md) | AGENTS.md | 37,461 | 133 | MIT | 5/10 |
| [obra/superpowers](https://github.com/obra/superpowers/blob/1d4c8d2aafb8fa0de3e5d7df80ff44899fa7e402/CLAUDE.md) | CLAUDE.md | 280,984 | 115 | MIT | 4/10 |
| [getzep/graphiti](https://github.com/getzep/graphiti/blob/375023b9e8db9957a48b2b6f3cb30d505a5ab39b/CLAUDE.md) | CLAUDE.md | 30,542 | 181 | Apache-2.0 | 4/10 |
| **AGENTS.md** | AGENTS.md | — | 52 | MIT | 10/10 |
<!-- summary:end -->

Full table with the evidence line behind every ✓: the [comparison](docs/generated/comparison.md)
or the [front page](https://purpleeddy.github.io/agents-md-lab/#compare).

## What the experiment showed

Ninety runs, three tasks by three conditions by ten, all of them delivered. On the greenfield
task the recommended file took `tests_written` from 0/10 with no instruction file to 6/10, and
reporting the command and its result from 0/10 to 9/10; on the brownfield task it took the
documented-convention metric from 5/10 to 10/10, and acceptance followed it exactly, 5/10 to
10/10. On the one-line typo fix nothing moved at all: every boolean metric is identical across
the three conditions. The file is paid for on every task — median cost 1.95× the no-file
condition on the greenfield task, 1.45× on the brownfield one and 1.29× on the typo fix.

The numbers, the intervals, the null results and what the experiment does not show are on
[the findings page](docs/findings.md); the design was locked before any run at tag
`testset-v1.0`.

## Documentation

- [Methodology](docs/methodology.md) — sources, corpus rules, how a verdict is decided, and what
  this is not.
- [Findings](docs/findings.md) — what the comparison and the experiment showed.
- [Rationale](docs/rationale.md) — one row per rule of `AGENTS.md`: sources, reason, what changed.
- [References](docs/references.md) — every citation key, with the date read and an archive link.
- [Pre-registration](experiments/README.md) — the experiment as it was locked at `testset-v1.0`.

## Reproduce it

```
python3 -m unittest                       # the whole suite
python3 scripts/compare.py --check        # every generated block matches the data
python3 scripts/compare.py --file AGENTS.md   # evaluate one local file
python3 scripts/experiment.py --dry-run   # the scoring fixtures
python3 scripts/compare.py --refresh      # re-fetch the corpus (network)
python3 scripts/experiment.py run --task task1 --conditions none karpathy ours --runs 10
```

Python 3.11 or newer, standard library only. There is nothing to install.

## Contributing

A file joins the survey through one `[[files]]` entry in `corpus.toml`, pinned by commit, with
one sentence saying what it shows that the others do not. Counter-examples are as welcome as
additions: a file that meets a criterion the check calls unmet is a bug in the pattern, and the
criteria carry their known false positives and false negatives in their `notes`. Open either as
an issue. Discussions open after the first release.

## License

MIT, for the code, the data and the pages. The corpus files stay under their own licenses and
are never redistributed here; the one repository with no license is recorded by line number
only.

`agents.md` is stewarded by the Agentic AI Foundation; this project is not affiliated with it or
with any vendor whose documentation is cited.
