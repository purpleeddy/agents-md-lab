# agents-md-lab

What belongs in an instruction file for a coding agent, measured two ways: ten published
`AGENTS.md` and `CLAUDE.md` files, each pinned to one commit and read against ten sourced
criteria, and an experiment on what an instruction file changes, in both directions, whose rules
were written down before any run. You get the file this project recommends, the numbers behind
it, and the data and scripts to reproduce both.

Site: <https://purpleeddy.github.io/agents-md-lab/>

## Adopt the file

1. Put the file in your repository root:

   ```
   curl -fsSL https://raw.githubusercontent.com/purpleeddy/agents-md-lab/main/AGENTS.md -o AGENTS.md
   ```

   That is the instruction file this project recommends: short enough to read in full before you
   adopt it, with its `## Project` section left empty for you to fill in. It has been measured on
   this project's own test set, revised after independent review and measured again, more than
   once; one revision failed the rule written for it beforehand and was undone. Which text each
   round of runs measured is in
   [the methodology](docs/methodology.md#what-the-experiment-tested-and-what-is-shipped), and the
   reason for every line, with what changed and why, is in [the rationale](docs/rationale.md).

2. Add a `CLAUDE.md` next to it whose only line is `@AGENTS.md`, so Claude Code loads the same
   rules the other agents read.
3. Fill the `## Project` section: stack, the commands that verify a change, what is generated,
   and where the details live. That section is the part no one else can write for you, and it is
   the reason the file as offered here does not meet the runnable-command criterion.
4. Mirror the destructive list in your agent's permission settings: deny what nothing takes
   back, and leave delivery allowed, so the agent can still push its own task branch and open a
   pull request. [`CONTRIBUTING.md`](CONTRIBUTING.md) sets the four tiers out,
   [`docs/examples/settings.json`](docs/examples/settings.json) is a settings file to copy, and
   [`scripts/hook_guard.py`](scripts/hook_guard.py) is the guard it calls, which reads the pushes
   a deny rule can only match by name. A written rule cannot stop a command: the file states
   the boundary, the settings refuse the command, and branch protection on the server is what
   holds when a session gets past both.

## What the survey found

How many of the ten rule criteria each file meets. The criteria ask how a file is written, and
each one is defined in [the methodology](docs/methodology.md#the-ten-criteria). The count describes what a file
contains. It is not a measure of quality, and no file here is put
above another.

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

<!-- summary:end -->

The root `AGENTS.md` of this repository is not in the table: it was written to these criteria, so
meeting them is expected by construction, and it is checked on the
[front page](https://purpleeddy.github.io/agents-md-lab/)
and in [methodology](docs/methodology.md#why-the-recommended-file-meets-the-rule-criteria) instead.

Full table with the evidence line behind every check mark: the
[comparison](docs/generated/comparison.md) or the
[front page](https://purpleeddy.github.io/agents-md-lab/#compare). The same ten files against the
eight content criteria, which ask what a file says about its own project, are in the
[findings](docs/findings.md#what-the-ten-files-tell-an-agent-about-the-project).

## What the experiment showed

Each of three tasks was run ten times in each of three ways: with no instruction file, with a
public instruction file another project ships, and with the file this project recommends. The
three tasks are building a small command-line app in an empty directory, a change inside an
existing package that documents a convention, and a one-line typo fix. The summary below is
written from the run data.

<!-- summary-experiment:start -->

90 runs: three tasks, each run three ways, ten runs each way, all of them delivered. On the
task that builds a small app in an empty directory, the recommended file took `tests_written`
from 0/10 with no instruction file to 6/10, and reporting the command and its result from 0/10
to 9/10; on the task that changes an existing package it took the documented-convention measure
from 5/10 to 10/10, and acceptance followed it exactly, 5/10 to 10/10. On the one-line typo fix
nothing moved at all: every yes-or-no measure is identical across the three ways of running it.
The file is paid for on every task: median cost 1.95× the runs with no instruction file when
building in an empty directory, 1.45× when changing an existing package and 1.29× on the typo
fix.

<!-- summary-experiment:end -->

Those runs measured an earlier text than the file offered above. Every round of runs since then
was written down before it ran: which measures had to hold, what the file was allowed to cost,
and, where a change was on trial, which lines to undo if it did not. One round adopted the
shorter text now offered here. A later one changed one boundary line, failed on two of the three
parts of its own rule, and the lines it named beforehand were undone as written. The tables for
every round are on [the findings page](docs/findings.md), together with the uncertainty on each
number, the measures that did not move, and
[what the experiment does not show](docs/findings.md#what-was-not-shown). The tasks and the
measures were fixed under a git tag before any run, and each later round's rule went into the same file before that round ran. Read
any single rise or fall against this: a re-run of the same text, on the same tasks, has moved one
measure by five runs in ten, so a change of that size on its own says nothing about the text.

## Documentation

- [Methodology](docs/methodology.md): sources, corpus rules, how a verdict is decided, and what
  this is not.
- [Findings](docs/findings.md): what the comparison and the experiment showed.
- [Rationale](docs/rationale.md): one row per rule of `AGENTS.md`, with its sources, its reason
  and what changed.
- [References](docs/references.md): every citation key, with the date read and an archive link.
- [The experiment as written down beforehand](experiments/README.md): the tasks and the measures,
  fixed under a git tag before the first run, and each round's rule written down before it ran.

## Reproduce it

```
python3 -m unittest                       # the whole suite
python3 scripts/compare.py --check        # every generated block matches the data
python3 scripts/compare.py --file AGENTS.md   # evaluate one local file
python3 scripts/experiment.py --dry-run   # the fixture check
python3 scripts/compare.py --refresh      # re-fetch the corpus (network)
python3 scripts/experiment.py run --task task1 --conditions none karpathy ours --runs 10
```

Python 3.11 or newer, standard library only. There is nothing to install.

## Contributing

A file joins the survey through one `[[files]]` entry in `corpus.toml`, pinned by commit, with
one sentence saying what it shows that the others do not. Counter-examples are as welcome as
additions: a file that meets a criterion the check calls unmet is a defect in the pattern, and the
criteria carry their known false positives and false negatives in their `notes`. Open either as
an issue.

## License

MIT, for the code, the data and the pages. The corpus files stay under their own licenses and
are never redistributed here; the one repository with no license is recorded by line number
only.

`agents.md` is stewarded by the Agentic AI Foundation; this project is not affiliated with it or
with any vendor whose documentation is cited.
