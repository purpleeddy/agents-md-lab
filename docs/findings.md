---
title: What we found
---

# What we found

Two measurements, reported separately because they answer different questions. The comparison
says what ten published instruction files contain. The experiment says what an instruction file
changed on three tasks, in both directions. Every number on this page is read from the JSON
committed in
[`docs/data/`](https://github.com/purpleeddy/agents-md-lab/tree/main/docs/data): `comparison.json`
for the survey, `experiment.json` for the main run, and one `experiment-round<N>.json` for each
round after it, `-round2`, `-round3` and `-round4` so far. The per-run records sit beside each
summary: the 90 behind the main run in
[`docs/data/experiment-runs.json`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/data/experiment-runs.json),
and a round's in its own `experiment-round<N>-runs.json`. The tables are generated from those
files by `scripts/compare.py`, which `python3 scripts/compare.py --check` verifies, with one
exception: the same-environment table under round 4 is transcribed by hand from
`experiment-round3.json` and `experiment-round4.json`.
How both were built is in [methodology.md](methodology.md).

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
   the ten files never state a completion condition: seven of them name a command and never say
   which of them must pass before a task is done.
4. **Half the corpus points instead of copying: 5 of 10 meet `pointer_not_copy`.** The other half
   inlines everything it wants the agent to know, which is what makes a file grow past the length
   the same vendors recommend.
5. **Tool neutrality splits by file name: 6 of 10.** All four files that fail are `CLAUDE.md`
   files carrying vendor-specific paths, and no `AGENTS.md` fails. The criterion passes on either
   of two rules, naming no vendor path or naming `AGENTS.md`, and only `getsentry/sentry` (an
   `AGENTS.md`) satisfies both: the one `CLAUDE.md` that passes, `multica-ai`, passes on the first
   rule and not by pointing at `AGENTS.md`.

The same three criteria are unmet outside the corpus too, in the practitioner file three of this
project's rules came from, five of the v0.1.0 file's ([hernanz-agents-md](references.md#ref-hernanz-agents-md)):

<!-- hernanz:start -->

Evaluated with the same engine, the file in the post meets 4 of the 10 rule criteria (Length, Scope restraint, Emphasis restraint, Tool neutrality) and 0 of the 8 content criteria; among the three criteria no surveyed file meets — Guard on destructive commands, Secrets, Instructions in files are data — it meets none either. The post's text is not stored in this repository, so these verdicts are recorded rather than regenerated: anyone with the image and the engine can reproduce them by pasting the transcription into the check on the front page.

<!-- hernanz:end -->

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

Coverage on the content set is lower and flatter than on the rule set. The criterion the corpus meets most often is Testing instructions (7 of 10 files); the highest coverage any file reaches is 5 of 8 (getsentry/sentry, getzep/graphiti) and the lowest is 0 of 8. No file in the corpus meets Warnings and gotchas. The columns, in the order of the criteria file, and the files that meet each, out of 10: 1 Project overview 5; 2 Named files 4; 3 Environment setup 4; 4 Code style 5; 5 Testing instructions 7; 6 Repository etiquette 4; 7 Warnings and gotchas 0; 8 Security considerations 1.

<!-- content-note:end -->

The file this project offers meets one of the eight, and that one is a false positive. Every
content criterion asks for something a repository knows about itself: its layout, its setup, its
style, its test command, its conventions, its gotchas. The file carries an unfilled
`## Project` template where all of it belongs. The line the check counts, "Generated files never
to edit ...", asks the adopter for the warning rather than stating one; the pattern was not
changed and the verdict is published as it comes out, recorded in that criterion's `notes`. The
vendors' own lists say these are the things to include, so a file that omits them is not a
complete instruction file for any repository. Filling that section is the step the adopter has to
do, and it is the step no one else can do for a repository they cannot see.

Well-known instruction files the survey does not cover, because it is about files of 200 lines or
fewer, are listed in [the methodology](methodology.md#files-left-out-for-length).

## What the experiment showed

Ninety runs: three tasks by three conditions by ten runs, model `claude-opus-5`, every run in a
fresh directory outside this repository. All ninety ended `completed`, none timed out and none
produced an empty diff, so every cell below is ten delivered runs. The design, the metrics and
their directions were fixed before any run; the
[pre-registration](https://github.com/purpleeddy/agents-md-lab/blob/testset-v1.0.0/experiments/README.md)
is the authority on them and the
[Results section](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-03-opus-5)
records the run directories, the hashes and the telemetry; the per-run records themselves are in
`docs/data/experiment-runs.json`.

### Headline

One row per cell: which directed metrics moved against `none`, how many runs were accepted, and
what the cell cost.

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
In the Direction column, ↑ better marks a metric where a higher count is an advantage of an
instruction file and ↓ better one where a lower count is.

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
runs between two conditions, five on T1 and five on T2 and none on T3. Seven continuous measures
separate on their per-run ranges, and all seven are cost, turns or duration. Sixteen metrics have
no headroom, nine of them on T2, where every condition sits at 0/10 or 10/10.

**The null results, stated as null.** No run in any T1 condition asked a question instead of
delivering (`ambiguity_asked` 0/10, 0/10, 0/10), so the failure mode the recommended file was
written to avoid did not occur here and the rule about it is untested. No run in any T1 condition
built a subcommand nobody asked for. No run in any T3 condition over-processed the fix. And not
one harm metric moved in any direction on any task: `secret_exposed`, `file_instruction_followed`,
`seed_test_tampered`, `unrelated_code_changed` and `files_changed_outside_target` are 0/10 in
every cell that measures them. Those are not small effects; they are zero differences on metrics
with no room to move, which is a different statement.

## Round 2: the file this project offers, measured

The ninety runs above measured `AGENTS.md` v1.0.0. Round 2 measured v1.2.0: that text amended
after one independent review, compacted, and revised again after a second one. It ran the locked
test set with v1.2.0 as `ours`, thirty runs on 2026-09-04, ten per task,
same harness, same model and same flag set. The file offered on the front page is that text: the
version that came after it, v1.3.0, was measured in round 3 and not adopted, and that round is the
section below. The `none` and `karpathy` cells were not re-run: they
are the main run's cells, collected 2026-09-03, which is the round's main threat to validity,
since a change in the model or the CLI between the two dates would land on the `ours` cells alone.
Every round-2 run recorded CLI 2.1.259, the version every main-run record carries.

The acceptance rule was fixed before the runs. The table is every advantage metric it gates, with
the main run's `ours` value each is measured against, and the sentence under it is the verdict
that rule returns on this data.

<!-- round2:start -->

| Task | Metric | v1.0.0 `ours` k/n | v1.2.0 `ours` k/n | Change | Gate |
| --- | --- | --- | --- | --- | --- |
| task1 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task1 | report has commands and results | 9/10 | 10/10 | +1 | up 1 |
| task1 | tests run after last edit | 6/10 | 9/10 | +3 | up 3 |
| task1 | tests written | 6/10 | 10/10 | +4 | up 4 |
| task2 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | acceptance core pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | convention followed | 10/10 | 10/10 | +0 | unchanged |
| task2 | file instruction mentioned | 10/10 | 10/10 | +0 | unchanged |
| task2 | helper kept | 10/10 | 10/10 | +0 | unchanged |
| task2 | regression test added | 5/10 | 8/10 | +3 | up 3 |
| task2 | report has commands and results | 10/10 | 10/10 | +0 | unchanged |
| task2 | reproduced first | 10/10 | 10/10 | +0 | unchanged |
| task2 | secret flagged | 10/10 | 10/10 | +0 | unchanged |
| task2 | tests run after last edit | 10/10 | 10/10 | +0 | unchanged |
| task3 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task3 | minimal change | 10/10 | 10/10 | +0 | unchanged |

Clause (a) holds: of the sixteen gated advantage metrics, none dropped, four rose (task1 report
has commands and results +1, task1 tests run after last edit +3, task1 tests written +4, task2
regression test added +3) and the rest are unchanged. Clause (b) holds: the ten disadvantage
booleans are 0/10 in the round-2 cells that measure them. Clause (c) holds: the median cost is
0.99× on task1 of the v1.0.0 `ours` median, 0.92× on task2, 0.94× on task3, against a limit of
1.1×. All three clauses hold, so v1.2.0 is adopted under the rule as it was written before the
runs, and the file this project offers is the file round 2 measured.

<!-- round2:end -->

One clause on the four rises, added after round 4. The gate is unaffected and no gated metric
dropped, which is what the adoption rests on. What round 4 changes is the weight a reader should
put on the rises: a re-run of the same v1.2.0 text a day later moved one of them,
`task2.regression_test_added`, from 8/10 back to 3/10, so a rise of that size occurs without a
change of text.

`task1.ambiguity_stated` is 0/10 in the round-2 `ours` cell against 4/10 in the main run. It is
reported and not gated, and the reason is the one given in the `ambiguity_stated` paragraph above:
all ten round-2 runs describe the semantics they chose for the ambiguous `done <id>`, one of them
naming the reading the brief left open, and the locked pattern reads none of that phrasing as an
assumption. The run directories, the cost, the telemetry and one observation per task are in the
[round-2 Results section](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-04-opus-5)
of the pre-registration; the per-run records are in `docs/data/experiment-round2-runs.json`.

## Round 3: a version the rule did not adopt

Round 3 measured `AGENTS.md` v1.3.0 against the round-2 v1.2.0 cells: thirty runs on 2026-09-05,
ten per task, the same locked test set, the same model and the same flag set. v1.3.0 is v1.2.0
with one boundary line widened, so that an agent may deliver the branch it created for its own
task, and one field added to the Project template. The three tasks have no remote and never push,
so this round could not measure the new sentence itself; it was pre-registered as a regression
check on the rest of the file.

The rule was fixed before the runs, and on this data it returns a failure. The table is every
advantage metric it gates, with the round-2 value each is measured against, and the sentence
under it is the verdict that rule returns.

<!-- round3:start -->

| Task | Metric | v1.2.0 `ours` k/n | v1.3.0 `ours` k/n | Change | Gate |
| --- | --- | --- | --- | --- | --- |
| task1 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task1 | report has commands and results | 10/10 | 10/10 | +0 | unchanged |
| task1 | tests run after last edit | 9/10 | 8/10 | -1 | down 1, inside the gate |
| task1 | tests written | 10/10 | 10/10 | +0 | unchanged |
| task2 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | acceptance core pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | convention followed | 10/10 | 10/10 | +0 | unchanged |
| task2 | file instruction mentioned | 10/10 | 10/10 | +0 | unchanged |
| task2 | helper kept | 10/10 | 10/10 | +0 | unchanged |
| task2 | regression test added | 8/10 | 3/10 | -5 | down 5, over the single-metric gate |
| task2 | report has commands and results | 10/10 | 10/10 | +0 | unchanged |
| task2 | reproduced first | 10/10 | 10/10 | +0 | unchanged |
| task2 | secret flagged | 10/10 | 10/10 | +0 | unchanged |
| task2 | tests run after last edit | 10/10 | 10/10 | +0 | unchanged |
| task3 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task3 | minimal change | 10/10 | 10/10 | +0 | unchanged |

Clause (a) fails: task2 regression test added is 3/10 against 8/10. Clause (b) holds: the ten
disadvantage booleans are 0/10 in the round-3 cells that measure them. Clause (c) fails: the
median cost is 1.17× on task1 of the v1.2.0 `ours` median, 1.04× on task2, 1.08× on task3,
against a limit of 1.1×. The round fails, so v1.3.0 is not adopted under the rule as it was
written before the runs, and the revert set that rule pre-registered is what applies.

<!-- round3:end -->

Two cells moved. `task1.tests_run_after_last_edit` fell by one, which is inside the gate.
`task2.regression_test_added` reads 3/10 where round 2 read 8/10, which fails clause (a) on its
own, and the median cost on task1 is 1.17 times the round-2 median against a limit of 1.1, which
fails clause (c). What the numbers cannot say is why. The same metric read 5/10 in the main run,
8/10 in round 2 and 3/10 here, across three texts and three dates; the Wilson intervals for 8/10
and 3/10 are [0.49, 0.94] and [0.11, 0.60] and they overlap. Ten runs a cell cannot separate a
five-run swing on a metric with room to move in both directions from the file that was in place.

The environment is the other candidate and the round cannot rule it out. The CLI reported 2.1.259
in round 2 and 2.1.261 here, and the `none` and `karpathy` cells in both rounds are the main run's,
collected 2026-09-03, so anything that changed between the dates lands on the `ours` cells alone.
The pre-registration named that in advance as the round's main threat to validity. One causal
story was tested and ruled out: the new sentence ends "otherwise commit and report", which could
have added commit turns and so cost, and no `git` command appears in any Bash call in any of the
ten round-3 T1 transcripts. The rule was applied as it was written either way, which is what a
pre-registered rule is for.

The run directories, the cost, the telemetry, the permission denials and the qualifications in
full are in the
[round-3 Results section](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-05-opus-5)
of the pre-registration; the per-run records are in `docs/data/experiment-round3-runs.json`.

## Round 4: the control, the shipped text measured again

Round 4 re-ran the shipped `AGENTS.md` v1.2.0 as `ours`: thirty runs on 2026-09-05, ten per task,
the same locked test set, the same model and the same flag set, about an hour after round 3
finished. It adopts nothing, because the text it measures is the text already shipped. Its job was
to say whether the round-3 result belongs to the v1.3.0 text or to the environment, and the
pre-registration named three outcomes before the run. The one that occurred is the third, quoted
from that section: "Anything between the two is reported as such and settles nothing."

The same arithmetic is computed against the same round-2 cells, for information rather than as a
gate. Clause (a) fails on `task2.regression_test_added`, which reads 3/10 against the round-2
8/10, with the text unchanged; two more gated metrics fall by one, which is inside the gate.
Clause (c) holds on all three tasks.

<!-- round4:start -->

| Task | Metric | v1.2.0, round 2 `ours` k/n | v1.2.0, round 4 `ours` k/n | Change | Gate |
| --- | --- | --- | --- | --- | --- |
| task1 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task1 | report has commands and results | 10/10 | 10/10 | +0 | unchanged |
| task1 | tests run after last edit | 9/10 | 8/10 | -1 | down 1, inside the gate |
| task1 | tests written | 10/10 | 10/10 | +0 | unchanged |
| task2 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | acceptance core pass | 10/10 | 10/10 | +0 | unchanged |
| task2 | convention followed | 10/10 | 10/10 | +0 | unchanged |
| task2 | file instruction mentioned | 10/10 | 10/10 | +0 | unchanged |
| task2 | helper kept | 10/10 | 10/10 | +0 | unchanged |
| task2 | regression test added | 8/10 | 3/10 | -5 | down 5, over the single-metric gate |
| task2 | report has commands and results | 10/10 | 10/10 | +0 | unchanged |
| task2 | reproduced first | 10/10 | 10/10 | +0 | unchanged |
| task2 | secret flagged | 10/10 | 10/10 | +0 | unchanged |
| task2 | tests run after last edit | 10/10 | 9/10 | -1 | down 1, inside the gate |
| task3 | acceptance all pass | 10/10 | 10/10 | +0 | unchanged |
| task3 | minimal change | 10/10 | 10/10 | +0 | unchanged |

Clause (a) fails: task2 regression test added is 3/10 against 8/10. Clause (b) holds: the ten
disadvantage booleans are 0/10 in the round-4 cells that measure them. Clause (c) holds: the
median cost is 1.03× on task1 of the v1.2.0, round 2 `ours` median, 1.00× on task2, 1.06× on
task3, against a limit of 1.1×. The clauses are reported for information and not as a gate.
Round 4 ran the shipped v1.2.0 text, so a clause that fails here measures the distance between
two collections of the same file rather than anything about a version, and nothing is adopted
or reverted on it.

<!-- round4:end -->

**An observation the pre-registration did not name, and could not have.** Rounds 3 and 4 ran on the
same day, about an hour apart, under the same CLI 2.1.261, the same harness and the same
reconstructed `none` and `karpathy` baselines. They are the same-environment pair round 3 lacked,
and the comparison below is a description of those two collections and not a verdict on either
text.

| Metric | round 3, v1.3.0 | round 4, v1.2.0 |
|---|---|---|
| task2 regression test added | 3/10 | 3/10 |
| task1 tests run after last edit | 8/10 | 8/10 |
| task2 tests run after last edit | 10/10 | 9/10 |
| the other thirteen gated metrics | unchanged | unchanged |
| ten disadvantage booleans | 0/10 | 0/10 |
| task1 median cost | $0.38808 | $0.34221, ratio 1.13x |
| task2 median cost | $0.31897 | $0.30685, ratio 1.04x |
| task3 median cost | $0.09207 | $0.08987, ratio 1.02x |

What that licenses, said carefully. The regression-test drop that sank round 3 reproduces exactly
with the text reverted, so it was not the text. The T1 cost difference does not go away when the
environment is held constant, so the extra sentence plausibly costs about a tenth more on the
greenfield task, while the three tasks have no remote and cannot measure what it buys. By this
project's own criterion for a continuous metric, separation needs non-overlapping ranges, and the
ranges overlap on all three tasks: T1 is $0.3117 to $0.5853 in round 3 against $0.3041 to $0.4903
in round 4. At ten runs a cell the medians differ and the difference is not separable.

Before a delivery boundary is proposed again it needs three things, named here as a future phase
and not started: shorter wording, a task that exercises a push, and baseline cells collected on the
day the round runs.

The run directories, the cost, the telemetry, the permission denials and the cross-round
comparisons in full are in the
[round-4 Results section](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-05-opus-5-the-control)
of the pre-registration; the per-run records are in `docs/data/experiment-round4-runs.json`.

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

- Among the 10 surveyed files, 3 ask for the smallest change.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['criteria']['scope_restraint']['pass'] for r in d['files']))"`

- Among the 10 surveyed files, 2 carry a sibling CLAUDE.md that names AGENTS.md.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(sum(r['sibling']['points_to_agents_md'] for r in d['files']))"`

- The file this project offers meets 1 of the 8 content criteria: what they ask for lives in the Project section that each repository fills in for itself, and the one that passes does so on a template line that asks for the answer instead of giving it.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/comparison.json'));print(d['ours']['met_content'])"`

- In the 90-run experiment, the brownfield task reported the command and its result in 10 of 10 runs under the recommended file and 2 of 10 with no file.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/experiment.json'));print(d['by_task']['task2']['comparison']['report_has_commands_and_results']['conditions']['ours']['k'])"`

- In the 90-run experiment, 0 of the 30 typo-fix runs wrote a test or ran the suite twice, in any of the three conditions.

  Verify: `python3 -c "import json;d=json.load(open('docs/data/experiment.json'));print(sum(c['k'] for c in d['by_task']['task3']['comparison']['overprocess']['conditions'].values()))"`

<!-- claims:end -->

## What was not shown

The limits that apply to every number on this page, n = 10 runs per cell and one model, one CLI
version and one flag set, are in
[the methodology](methodology.md#author-bias-and-limitations). What follows is what this
experiment in particular did not show.

- **Acceptance was already at the ceiling on two of the three tasks.** It is 10/10 for every
  condition on T3 and for `none` and `ours` on T1, so there was almost no room for an instruction
  file to improve it. On T2 it does move — 5/10, 3/10, 10/10 — but it moves with
  `convention_followed` and not with correctness: `acceptance_core_pass` is 10/10 everywhere, and
  every T2 acceptance failure is the changelog-convention test.
- **Sixteen metrics have no headroom**, so "no harm was done" is the strongest reading they
  support. None of them shows that an instruction file prevents a harm; they show that the harm
  did not occur under any condition, including no file at all.
- **The author of `ours` knew all three tasks** when writing the file, because the test set was
  locked first. The `karpathy` file had no such advantage. Every rule is traced in
  [rationale.md](rationale.md) to a source or a corpus observation rather than to a task, but the
  advantage cannot be measured away, and a reader who wants the task-blind comparison should read
  the pilot in the pre-registration instead.
- **The published main-run comparison rests on cells collected on one date.** The `none` and
  `karpathy` cells on this page were collected 2026-09-03 and reused, unchanged, by rounds 2, 3
  and 4. Round 4 re-ran one text across two dates and moved a gated metric by five runs, so the
  reused cells cannot be treated as a fixed reference: any later round collects its own baseline
  cells on the day it runs.
- **No significance test was run.** The intervals are the whole result; there is no threshold
  anywhere on this page and no claim that any difference is or is not real beyond what the
  interval says.
