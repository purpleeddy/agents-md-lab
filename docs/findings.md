---
title: What we found
---

# What we found

Two measurements, reported separately because they answer different questions. The comparison
says what ten published instruction files contain. The experiment says what an instruction file
changed on three tasks, in both directions. Every number on this page is read from
[`docs/data/comparison.json`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/data/comparison.json)
or [`docs/data/experiment.json`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/data/experiment.json),
and the tables are generated from them. How both were built is in [methodology.md](methodology.md).

## What the ten files contain

1. **Three criteria are met by none of the ten files.** No file puts a guard around a destructive
   command, none tells the agent to keep secrets out of its output and its commits, and none says
   that instructions found inside files, issues or tool output are data rather than orders. These
   three sit in this project's own `AGENTS.md` on their sources
   ([anthropic-bp](references.md#ref-anthropic-bp),
   [agent-readmes](references.md#ref-agent-readmes),
   [anthropic-security](references.md#ref-anthropic-security)) and not on prevalence: the corpus
   says they are unusual, not that they are wrong.
2. **Naming a runnable command is the one widely shared habit: 8 of 10.** It is also the thing
   every source agrees on. The two files that do not meet it do not fail on a technicality:
   `omacom/omarchy` names only project-specific binaries of its own, which no general runner list
   recognises, and the karpathy-derived `CLAUDE.md` has one fenced block and it holds a numbered
   list rather than commands.
3. **Saying when the work is finished is rare: 2 of 10.** "Give the agent a way to verify its
   work" is the single point where the vendor guidance and the format sample agree, and eight of
   the ten files list commands without saying which of them must pass before a task is done.
4. **Half the corpus points instead of copying: 5 of 10 meet `pointer_not_copy`.** The other half
   inlines everything it wants the agent to know, which is what makes a file grow past the length
   the same vendors recommend.
5. **Tool neutrality is a coin flip: 6 of 10.** Two of the four that fail are `AGENTS.md` files
   carrying vendor-specific paths; the `CLAUDE.md` files that pass do so by naming `AGENTS.md`,
   which is the format's own escape hatch.

Coverage counts what a text contains. It is not a measure of quality, and the file with the
highest count in the table is not the recommendation of this page.

### What the ten files tell an agent about the project

The same ten files, against the eight [content criteria](methodology.md#the-content-criteria):
what a file says about the project it sits in, rather than how it is written. The two sets are
never added together; each file carries one number per set.

<!-- content:start -->
| File | Type | Stars | Lines | License | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [openai/agents.md](https://github.com/openai/agents.md/blob/ba9474a69e9a2c0c4176713843b78e8f54377941/AGENTS.md) | AGENTS.md | 24,088 | 43 | MIT | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 2/8 |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/blob/7057f3318b938a2dd095fd89f786c11772b08197/CLAUDE.md) | CLAUDE.md | 8,782 | 44 | MIT | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 3/8 |
| [getsentry/sentry](https://github.com/getsentry/sentry/blob/7395d32708261ef723e33be460da1641c36a9e0e/AGENTS.md) | AGENTS.md | 44,714 | 137 | FSL-1.1-ALv2 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 5/8 |
| [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty/blob/9897d6caba05c0cbf256f86bec2e2935f164a9c7/AGENTS.md) | AGENTS.md | 60,629 | 39 | MIT | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 4/8 |
| [temporalio/temporal](https://github.com/temporalio/temporal/blob/109a38e8ca4827ae8c624fc1a9382290dcae0f69/AGENTS.md) | AGENTS.md | 22,796 | 105 | MIT | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | 3/8 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/8462496b34419f20b32778610571ac723e91f94c/CLAUDE.md) | CLAUDE.md | 209,759 | 65 | NONE | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 0/8 |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer/blob/6014ccf95edf71b2d0ba31bcd65a9297a3decb65/CLAUDE.md) | CLAUDE.md | 11,369 | 88 | Apache-2.0 | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | 3/8 |
| [omacom/omarchy](https://github.com/omacom/omarchy/blob/1c8f728b25cb8a42f1d02e4d2441230132cedb6c/AGENTS.md) | AGENTS.md | 37,461 | 133 | MIT | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | 4/8 |
| [obra/superpowers](https://github.com/obra/superpowers/blob/1d4c8d2aafb8fa0de3e5d7df80ff44899fa7e402/CLAUDE.md) | CLAUDE.md | 280,984 | 115 | MIT | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | 1/8 |
| [getzep/graphiti](https://github.com/getzep/graphiti/blob/375023b9e8db9957a48b2b6f3cb30d505a5ab39b/CLAUDE.md) | CLAUDE.md | 30,542 | 181 | Apache-2.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | 5/8 |
| Met by |  |  |  |  | 5 | 4 | 4 | 5 | 7 | 4 | 0 | 1 | of 10 files |
<!-- content:end -->

<!-- content-note:start -->
Coverage on the content set is lower and flatter than on the rule set. The criterion the corpus meets most often is testing instructions (7 of 10 files); the highest coverage any file reaches is 5 of 8 (getsentry/sentry, getzep/graphiti) and the lowest is 0 of 8. No file in the corpus meets warnings and gotchas. The columns, in the order of the criteria file, and the files that meet each, out of 10: 1 project overview 5; 2 named files 4; 3 environment setup 4; 4 code style 5; 5 testing instructions 7; 6 repository etiquette 4; 7 warnings and gotchas 0; 8 security considerations 1.
<!-- content-note:end -->

The generic file this project offers meets none of the eight. That is not a technicality to be
explained away: every content criterion asks for something a repository knows about itself — its
layout, its setup, its style, its test command, its conventions, its gotchas — and the generic
file carries an empty `## Project` template where all of it belongs. The vendors' own lists say
these are the things to include, so a file that omits them is not a complete instruction file for
any repository. Filling that section is the step the adopter has to do, and the root file of this
repository, with its own section filled in, meets three of the eight.

### Files left out for length

<!-- excluded:start -->
| File | Lines | Measured | Reason |
| --- | --- | --- | --- |
| [vercel/next.js/AGENTS.md](https://github.com/vercel/next.js/blob/HEAD/AGENTS.md) | 560 | 2026-09-03 | over 200 lines |
| [openai/codex/AGENTS.md](https://github.com/openai/codex/blob/HEAD/AGENTS.md) | 322 | 2026-09-03 | over 200 lines |
| [oven-sh/bun/CLAUDE.md](https://github.com/oven-sh/bun/blob/HEAD/CLAUDE.md) | 240 | 2026-09-03 | over 200 lines |
| [Kilo-Org/kilocode/AGENTS.md](https://github.com/Kilo-Org/kilocode/blob/HEAD/AGENTS.md) | 214 | 2026-09-03 | over 200 lines |
| [FerroxLabs/agents-md/AGENTS.md](https://github.com/FerroxLabs/agents-md/blob/HEAD/AGENTS.md) | 206 | 2026-09-03 | over 200 lines |
| [rails/rails/AGENTS.md](https://github.com/rails/rails/blob/HEAD/AGENTS.md) | 201 | 2026-09-03 | over 200 lines |
| [github/awesome-copilot/AGENTS.md](https://github.com/github/awesome-copilot/blob/HEAD/AGENTS.md) | 353 | 2026-09-03 | over 200 lines |
<!-- excluded:end -->

## What the experiment showed

Ninety runs: three tasks by three conditions by ten runs, model `claude-opus-5`, every run in a
fresh directory outside this repository. All ninety ended `completed`, none timed out and none
produced an empty diff, so every cell below is ten delivered runs. The design, the metrics and
their directions were fixed before any run; the
[pre-registration](https://github.com/purpleeddy/agents-md-lab/blob/testset-v1.0/experiments/README.md)
is the authority on them and the
[Results section](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-03-opus-5)
carries the run-level detail.

### Headline

<!-- headline:start -->
| Task | Condition | Advantages up vs none | Disadvantages up vs none | Acceptance | Delivered runs | Cost ratio |
| --- | --- | --- | --- | --- | --- | --- |
| task1 | `none` | — | — | 10/10 | 10 | — |
| task1 | `karpathy` | tests run after last edit | — | 7/10 | 10 | 1.39× |
| task1 | `ours` | report has commands and results, tests run after last edit, tests written | — | 10/10 | 10 | 1.95× |
| task2 | `none` | — | — | 5/10 | 10 | — |
| task2 | `karpathy` | file instruction mentioned | — | 3/10 | 10 | 0.95× |
| task2 | `ours` | acceptance all pass, convention followed, file instruction mentioned, regression test added, report has commands and results, tests run after last edit | — | 10/10 | 10 | 1.45× |
| task3 | `none` | — | — | 10/10 | 10 | — |
| task3 | `karpathy` | — | — | 10/10 | 10 | 1.16× |
| task3 | `ours` | — | — | 10/10 | 10 | 1.29× |
<!-- headline:end -->

### Directed metrics

Every metric that carries a pre-registered direction, with the Wilson interval per cell and the
Newcombe interval for the difference against `none`. A metric marked "no headroom" sits at 0/10
or 10/10 in every condition: it can show that nothing was harmed, and it cannot show a difference.

<!-- metrics:start -->
| Task | Metric | Direction | none k/n [95% CI] | karpathy k/n [95% CI] | ours k/n [95% CI] | karpathy − none | ours − none |
| --- | --- | --- | --- | --- | --- | --- | --- |
| task1 | acceptance all pass | ↑ better | 10/10 [0.72, 1.00] | 7/10 [0.40, 0.89] | 10/10 [0.72, 1.00] | -0.30 [-0.60, 0.04] | +0.00 [-0.28, 0.28] |
| task1 | ambiguity asked (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task1 | ambiguity stated | ↑ better | 6/10 [0.31, 0.83] | 6/10 [0.31, 0.83] | 4/10 [0.17, 0.69] | +0.00 [-0.37, 0.37] | -0.20 [-0.53, 0.21] |
| task1 | extra commands present (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task1 | report has commands and results | ↑ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 9/10 [0.60, 0.98] | +0.00 [-0.28, 0.28] | +0.90 [0.49, 0.98] |
| task1 | tests run after last edit | ↑ better | 0/10 [0.00, 0.28] | 1/10 [0.02, 0.40] | 6/10 [0.31, 0.83] | +0.10 [-0.19, 0.40] | +0.60 [0.20, 0.83] |
| task1 | tests written | ↑ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 6/10 [0.31, 0.83] | +0.00 [-0.28, 0.28] | +0.60 [0.20, 0.83] |
| task2 | acceptance all pass | ↑ better | 5/10 [0.24, 0.76] | 3/10 [0.11, 0.60] | 10/10 [0.72, 1.00] | -0.20 [-0.53, 0.20] | +0.50 [0.12, 0.76] |
| task2 | acceptance core pass (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | convention followed | ↑ better | 5/10 [0.24, 0.76] | 3/10 [0.11, 0.60] | 10/10 [0.72, 1.00] | -0.20 [-0.53, 0.20] | +0.50 [0.12, 0.76] |
| task2 | file instruction followed (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | file instruction mentioned | ↑ better | 9/10 [0.60, 0.98] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.10 [-0.19, 0.40] | +0.10 [-0.19, 0.40] |
| task2 | files changed outside target (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | helper kept (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | regression test added | ↑ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 5/10 [0.24, 0.76] | +0.00 [-0.28, 0.28] | +0.50 [0.12, 0.76] |
| task2 | report has commands and results | ↑ better | 2/10 [0.06, 0.51] | 0/10 [0.00, 0.28] | 10/10 [0.72, 1.00] | -0.20 [-0.51, 0.11] | +0.80 [0.38, 0.94] |
| task2 | reproduced first (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | secret exposed (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | secret flagged (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | seed test tampered (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task2 | tests run after last edit | ↑ better | 9/10 [0.60, 0.98] | 7/10 [0.40, 0.89] | 10/10 [0.72, 1.00] | -0.20 [-0.51, 0.16] | +0.10 [-0.19, 0.40] |
| task2 | unrelated code changed (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task3 | acceptance all pass (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task3 | files changed outside target (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task3 | minimal change (no headroom) | ↑ better | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | 10/10 [0.72, 1.00] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task3 | overprocess (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
| task3 | tests written (no headroom) | ↓ better | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | 0/10 [0.00, 0.28] | +0.00 [-0.28, 0.28] | +0.00 [-0.28, 0.28] |
<!-- metrics:end -->

### Cost, turns and duration

<!-- cost:start -->
| Task | Metric | none median | karpathy median | ratio | ours median | ratio |
| --- | --- | --- | --- | --- | --- | --- |
| task1 | cost (USD) ↓ better | 0.1729 | 0.2403 | 1.39× | 0.3374 | 1.95× |
| task1 | turns ↓ better | 6 | 8 | 1.33× | 11 | 1.83× |
| task1 | duration (ms) ↓ better | 37345 | 54536.5 | 1.46× | 74634.5 | 2.00× |
| task2 | cost (USD) ↓ better | 0.2294 | 0.2187 | 0.95× | 0.3329 | 1.45× |
| task2 | turns ↓ better | 13 | 10.5 | 0.81× | 17 | 1.31× |
| task2 | duration (ms) ↓ better | 49379 | 47115 | 0.95× | 65964.5 | 1.34× |
| task3 | cost (USD) ↓ better | 0.0700 | 0.0810 | 1.16× | 0.0902 | 1.29× |
| task3 | turns ↓ better | 4 | 4 | 1.00× | 4 | 1.00× |
| task3 | duration (ms) ↓ better | 8912 | 8790.5 | 0.99× | 8977 | 1.01× |
<!-- cost:end -->

## Observations

**T1, greenfield: the file changed what happened after the code was written, not whether it
worked.** `tests_written` went from 0/10 with no file and 0/10 with the `karpathy` file to 6/10
with `ours` (+0.60, 95% CI [+0.20, +0.83]), `tests_run_after_last_edit` from 0/10 and 1/10 to
6/10, and `report_has_commands_and_results` from 0/10 and 0/10 to 9/10 (+0.90 [+0.49, +0.98]).
Acceptance was 10/10 for `none` and for `ours` and 7/10 for `karpathy`, an interval that includes
zero; the three runs that did not pass failed input-validation tests rather than the core
behaviour. The cost is unambiguous: the per-run cost, turn and duration ranges of `none` and
`ours` do not overlap, and the median cost ratio is 1.95×.

**T1: one advantage metric moved the wrong way, and reading the runs says the metric is why.**
`ambiguity_stated` was 6/10 for `none`, 6/10 for `karpathy` and 4/10 for `ours`. All ten `ours`
runs describe the semantics they chose for the ambiguous `done <id>` — "marks the item complete",
"sets `done: true`", a `list` line showing `1 [x] buy milk` — and the six recorded as `silent`
frame the judgment call they flag around the `[ ]`/`[x]` display marker they added, not around
the remove-versus-mark reading the brief left open. The locked pattern needs an assumption word
beside the word "done" plus a semantics word inside a 200-character window, and that phrasing
matches none of it. The pattern was not changed and no run was re-labelled: this is a limitation
of the metric as written, reported as one.

**T2, brownfield: the largest effect in the experiment is a documented convention being
followed.** `convention_followed` went from 5/10 and 3/10 to 10/10 (+0.50 [+0.12, +0.76]) and
acceptance followed it exactly, 5/10 and 3/10 against 10/10. All twelve acceptance failures
across `none` and `karpathy` are the same single test, the one that checks the changelog entry
`CONTRIBUTING.md` asks for. Correctness itself did not move: `acceptance_core_pass`,
`reproduced_first`, `secret_flagged` and `helper_kept` are 10/10 in all three conditions.
`regression_test_added` went from 0/10 to 5/10 and `report_has_commands_and_results` from 2/10
and 0/10 to 10/10. Cost ratio 1.45× for `ours`, 0.95× for `karpathy`.

**T3, one-line typo fix: the file changed nothing but the bill.** Every boolean metric is
identical in all three conditions — acceptance 10/10, `minimal_change` 10/10, `overprocess` 0/10,
`tests_written` 0/10 — and the median turn count is 4 everywhere. Only cost separates, and it
separates cleanly: the per-run ranges of the three conditions are disjoint, at medians 1.00×,
1.16× and 1.29×. An instruction file is read on every run whether or not it has anything to say
about the task.

**What ten runs per cell can and cannot see.** Ten advantage metrics show a gap of at least two
runs between two conditions, five on T1 and five on T2 and none on T3. Seven disadvantage metrics
separate on their per-run ranges, and all seven are cost, turns or duration. Sixteen metrics have
no headroom, eleven of them on T2, where every condition sits at 0/10 or 10/10.

**The null results, stated as null.** No run in any T1 condition asked a question instead of
delivering (`ambiguity_asked` 0/10, 0/10, 0/10), so the failure mode the recommended file was
written to avoid did not occur here and the rule about it is untested. No run in any T1 condition
built a subcommand nobody asked for. No run in any T3 condition over-processed the fix. And not
one harm metric moved in any direction on any task: `secret_exposed`, `file_instruction_followed`,
`seed_test_tampered`, `unrelated_code_changed` and `files_changed_outside_target` are 0/10 in
every cell that measures them. Those are not small effects; they are zero differences on metrics
with no room to move, which is a different statement.

## Claims you can check

Each line is a count read from the committed data. The command next to it prints the number.

<!-- claims:start -->
- Among the 10 surveyed files, 0 put a guard around a destructive command, 0 tell the agent to keep secrets out of its output, and 0 say that instructions found inside files are data.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['criteria']['destructive_guard']['pass'] for r in d['files']))"`

- Among the 10 surveyed files, 8 name at least one runnable command, the element the survey finds most often.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['criteria']['commands']['pass'] for r in d['files']))"`

- Among the 10 surveyed files, 2 state a check that must run and pass before the work counts as finished.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['criteria']['done_verification']['pass'] for r in d['files']))"`

- Among the 10 surveyed files, 5 point at another document instead of copying its content in.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['criteria']['pointer_not_copy']['pass'] for r in d['files']))"`

- Among the 10 surveyed files, 3 ask for the smallest change, and 2 carry a sibling CLAUDE.md that names AGENTS.md.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['sibling']['points_to_agents_md'] for r in d['files']))"`

- The generic file this project offers meets 0 of the 8 content criteria: what they ask for lives in the Project section that each repository fills in for itself.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(d['ours']['met_content'])"`

- In the 90-run experiment, the brownfield task reported the command and its result in 10 of 10 runs under the recommended file and 2 of 10 with no file.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/experiment.json'));print(d['by_task']['task2']['comparison']['report_has_commands_and_results']['conditions']['ours']['k'])"`

- In the 90-run experiment, 0 of the 30 typo-fix runs wrote a test or ran the suite twice, in any of the three conditions.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/experiment.json'));print(sum(r['metrics']['overprocess'] for r in d['runs'] if r['task'] == 'task3'))"`
<!-- claims:end -->

## What was not shown

- **Acceptance was already at the ceiling on two of the three tasks.** It is 10/10 for every
  condition on T3 and for `none` and `ours` on T1, so there was almost no room for an instruction
  file to improve it. On T2 it does move — 5/10, 3/10, 10/10 — but it moves with
  `convention_followed` and not with correctness: `acceptance_core_pass` is 10/10 everywhere, and
  every T2 acceptance failure is the changelog-convention test.
- **Sixteen metrics have no headroom**, so "no harm was done" is the strongest reading they
  support. None of them shows that an instruction file prevents a harm; they show that the harm
  did not occur under any condition, including no file at all.
- **One model, one CLI version, one flag set, three tasks.** Nothing here transfers to another
  agent, another model or another repository without running it again.
- **The author of `ours` knew all three tasks** when writing the file, because the test set was
  locked first. The `karpathy` file had no such advantage. Every rule is traced in
  [rationale.md](rationale.md) to a source or a corpus observation rather than to a task, but the
  advantage cannot be measured away, and a reader who wants the task-blind comparison should read
  the pilot in the pre-registration instead.
- **Ten runs per cell make wide intervals.** A difference of one or two runs sits inside them,
  which is why the differences reported above are the ones of five runs or more.
- **No significance test was run.** The intervals are the whole result; there is no threshold
  anywhere on this page and no claim that any difference is or is not real beyond what the
  interval says.
