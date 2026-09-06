# agents-md-lab

An instruction file for coding agents, and the measurements behind it: ten published files read
against ten sourced criteria, and a pre-registered experiment on what such a file changes, in
both directions.

Site: <https://purpleeddy.github.io/agents-md-lab/>

## Adopt the file

1. In your repository root:

   ```
   curl -fsSL https://raw.githubusercontent.com/purpleeddy/agents-md-lab/main/AGENTS.md -o AGENTS.md
   ```

2. Add a `CLAUDE.md` beside it whose only line is `@AGENTS.md`.
3. Fill the `## Project` section: stack, verifying commands, generated files, where the details
   live. No one else can write it for you, and while it is empty the file names no
   runnable command — one of three of the ten rule criteria the file as offered does not meet,
   all three in
   [the methodology](docs/methodology.md#why-the-recommended-file-meets-the-rule-criteria).
4. Mirror the destructive list in your agent's permission settings. Yours may be looser than the
   file, which holds every push behind an explicit ask, and the file is what the agent reads.
   [`CONTRIBUTING.md`](CONTRIBUTING.md) has the four tiers,
   [`docs/examples/settings.json`](docs/examples/settings.json) and
   [`scripts/hook_guard.py`](scripts/hook_guard.py) the files.

## What the survey found

How many of the ten rule criteria each file meets, each defined in
[the methodology](docs/methodology.md#the-ten-criteria). A count is what a file contains, not how
well it is written.

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

Evidence line by line: [the comparison](docs/generated/comparison.md); the eight content
criteria: [the findings](docs/findings.md#what-the-ten-files-tell-an-agent-about-the-project).

## What the experiment showed

Three tasks, ten runs each, in three conditions: no instruction file, a public file another
project ships, and the file above. Every run was one model on one tool, so nothing here carries
to another agent unless you re-run it, and a re-run of the same text has moved one measure by
five runs in ten.

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

Those runs measured an earlier text than the file above. Later rounds, and
[what the experiment does not show](docs/findings.md#what-was-not-shown), are on the findings
page.

## Documentation

- [Methodology](docs/methodology.md): sources, corpus rules, how a verdict is decided.
- [Findings](docs/findings.md): what the survey and the experiment showed.
- [Rationale](docs/rationale.md): one row per rule.
- [References](docs/references.md): every citation key and date read.
- [The pre-registration](experiments/README.md): tagged before run one.

## Reproduce it

```
python3 -m unittest                       # the whole suite
python3 scripts/compare.py --check        # every generated block matches the data
python3 scripts/compare.py --file AGENTS.md   # evaluate one local file
python3 scripts/experiment.py --dry-run   # the fixture check
python3 scripts/compare.py --refresh      # re-fetch the corpus (network)
python3 scripts/experiment.py run --task task1 --conditions none karpathy ours --runs 10
```

## Contributing

A file joins the survey through one `[[files]]` entry in `corpus.toml`, pinned by commit; a
counter-example is as welcome. Open either as an issue —
[`CONTRIBUTING.md`](CONTRIBUTING.md) has the rest.

## License

MIT, for the code, the data and the pages. Corpus files keep their own licenses and are never
redistributed here.

`agents.md` is stewarded by the Agentic AI Foundation; this project is not affiliated with it or
with any vendor whose documentation is cited.
