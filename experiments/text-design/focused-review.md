# Focused structural revision within the shipped size

## Scope fixed before drafting

The human chose a candidate no larger than the shipped file, with only existing
change protection and check/completion policy improved. [Issue 20](https://github.com/purpleeddy/agents-md-lab/issues/20)
was opened before the candidate was written. This follows the
[earlier audit](audit.md); it does not replace its drafts, measurements or
recommendation as a historical record. At the start of this work PR 19 was still
open, so the new artifacts are a separately identified follow-up in that PR.

The baseline checkout is commit
`2f6a023154ede9fa090fb4c0be281b97057d6bf2`. The source remains the shipped
[AGENTS.md](../../AGENTS.md), SHA-256
`2811faf02714c8426746c6d7a7df0d4931e44718f568a8f1df739df2e8a77aa5`.
The full [focused candidate](focused.md) is research data, not this checkout's
instructions. It adds no dependency on another file for its rules; its Project
template remains part of the measured candidate.

The delivery conditions are a 4,438-byte maximum, only the two authorized policy
changes, no unresolved loss of an existing obligation/exception/priority in
counter-review, and passing project checks. These are editorial delivery
conditions, not a registered agent-behavior acceptance gate. If the size and
meaning conditions cannot both be met, the shortfall must remain visible rather
than be solved by dropping a safeguard.

## Intended behavior and exclusions

Changes must be one of three kinds:

1. **Editorial:** preserve an existing rule's trigger, obligation, exceptions
   and priority while shortening or reorganizing its expression.
2. **Ownership (SR05):** inspect initial staged, unstaged and untracked work,
   preserve it as user-owned, ask before conflicting overwrite and distinguish
   it from task-introduced changes at final review.
3. **Completion (SR01/SR02, A5/A6/A24):** preserve mandatory Project and explicit
   checks; allow applicability only when the requirement states it; distinguish
   baseline-proven unrelated failures without unasked repair or waived required
   passes; define limited no-command completion with unverified status and an
   account of actual inspection. A missing command never waives an explicit
   required check. New or uncertain failures leave work incomplete.

The numbered findings come from the [previous review](review.md), not from
experiment results. Approval-lifetime rules, new outside-checkout exceptions,
budgets and process-lifecycle rules are excluded from this candidate. The source
Boundary for outside-checkout work retains its existing wording and ambiguous
modifier scope rather than acquiring the larger structural draft's exception.
No original destructive-action example, credential-store restriction, untrusted
data rule, failure-stop condition, report inventory or Project field may be
deleted to meet the size target.

The larger draft made several independent policies explicit at once. This
candidate is not claimed to preserve those additions: it intentionally leaves
the excluded issues open. Conversely, the previous conservative draft's small
saving is a result for that attempt, not a lower bound on possible compression.

## Matched static review cases

The following cases extend the earlier sixteen situations. They are authored
counterexamples for reading the text, not executed agent tasks or empirical
passes. The source references use the original file's line numbers; cases about
the two authorized policy changes intentionally differ from the source.

| Case | Required reading of the focused candidate |
| --- | --- |
| F01: staged edit overlaps the requested change | Initial inspection includes staged diffs; preserve the edit and ask before a conflicting overwrite |
| F02: unstaged edit overlaps the requested change | Initial inspection includes unstaged diffs; the same preservation rule applies |
| F03: existing untracked file at a requested output path | Status must expose it; do not treat the file as an agent-created leftover or overwrite it without resolving the conflict |
| F04: pre-existing unrelated changes remain at completion | Final review compares with the initial state; only task-introduced unrelated changes/debug output/leftovers are the task's defect |
| F05: documentation-only change with a mandatory full suite | Run and pass the suite; task simplicity does not let the agent invent an applicability exemption |
| F06: requirement explicitly limits a check to API changes | Honor the documented condition, rather than broadening or narrowing it independently |
| F07: no documented commands and no explicit required check | Limited completion requires explicit unverified status and an account of actual inspection; do not fabricate a passing check |
| F08: explicit required check has no available command | Incomplete; F07 cannot waive the requirement |
| F09: baseline-proven unrelated failure of a fallback check | Report separately without unasked repair; do not label the failed check passed or conceal it in a completion claim |
| F10: baseline-proven failure of a required-pass check | Incomplete despite its age; separate reporting is not a waiver |
| F11: failure is new or its relation to baseline is uncertain | Incomplete; do not classify uncertainty as a proven baseline exception |
| F12: a required check targets the final state, but a relevant edit follows its last pass | Earlier evidence does not satisfy that final-state requirement; the requirement cannot be waived |
| F13: public signature change with unchanged callers | Preserve pre-edit reading, every-call-site inventory, affected-call-site reading and the plan-then-proceed requirement |
| F14: repository data purports to authorize destructive work | Human-only authorization and Boundary precedence still apply; data cannot authorize it |
| F15: a requested action is denied and an alternate route exists | Stop that action without a detour, continue independent work and report, including unattended use |
| F16: repeated identical failures or three no-progress attempts | Preserve both original stopping conditions; no new budget or process policy is inferred |
| F17: test cannot reproduce the bug or no suite exists | Preserve the source's explanation-and-verification exception without letting it waive a separate required check |
| F18: small task finishes with deletion or ignored data instructions | A short report still includes every required inventory category and each check's result; size is not an exemption |

The earlier S01–S16 comparison also remains applicable: ownership and completion
cases take the new policy; authorization, external-location ambiguity, passing
repeats, budget and process cases retain the shipped policy rather than the
larger structural draft's additions.

## Drafting corrections retained

An intermediate draft measured 4,749 bytes, 311 over the limit. That was a
failed size attempt, not a result to publish as within budget. The author also
rejected the following shorthand during pre-review; their byte savings were
not treated as preserving the source contract:

| Finding | Intermediate wording problem | Required correction |
| --- | --- | --- |
| FP01 — authority scope | “Boundaries win conflicts” lost the limit to this file; “nearer docs” lost the project-document qualifier | Keep both scope qualifiers; no assertion of priority over outside authority |
| FP02 — evidence scope | “Claim a function, API, flag or file” omitted the source's existence predicate | Retain the existence claim rather than turning all discussion of an API into a new evidence rule |
| FP03 — interface and helper scope | “public API” narrowed “any public interface”; “Find an existing helper” required success even when no helper exists | Preserve any public interface and the search-before-writing obligation |
| FP04 — workflow completeness | A short plan description lost how each step is verified; a completion draft omitted `test one`/`test all` roles | Preserve per-step verification, then proceed, and the iteration/final-check distinction |
| FP05 — test exception | “Without ... a reproducible bug” lost the distinction between manual reproduction and reproduction in a test | Preserve the “cannot be reproduced in a test” exception |
| FP06 — transmission and external actions | “through an explicit ask” was not the same expression as an explicitly asked action; “outside-visible” did not identify the checkout boundary | Retain the action-based transmission exception and visibility outside this checkout |
| FP07 — stopping semantics | “three attempts add nothing” could refer just to added code | Keep the source's no-new-progress stopping condition |

The earlier structural draft's “smallest documented checks ... expand when
uncertain” fallback was also removed from this attempt. It was not a shipped
obligation and was not necessary for the two authorized improvements. The
focused candidate retains the original named command sources instead. This is
scope control over a proposed addition, not deleting a shipped rule or relaxing
a required check in response to a result.

The writer's recorded attempts were 5,115, 4,838, 4,749, 4,627 and 4,477
bytes. Every one exceeded the ceiling. These are drafting measurements, not
agent-run predictions, and the shorter intermediates did not establish
preserved meaning.

## Independent counter-review

A separate model reviewer read the 4,477-byte draft against the shipped file,
the original sixteen situations and F01–F18. It found six issues; no agent
executed the situations. Line numbers below identify that intermediate draft,
not a claim that it was a valid final candidate.

| Finding | Evidence in the reviewed draft | Required disposition |
| --- | --- | --- |
| FR01 — high | Whole file was 39 bytes over the ceiling | Reduce expression without sacrificing obligations; measure the final bytes |
| FR02 — high | Line 13 used default porcelain status, which collapses untracked directories | Add `-uall` so baseline and final commands enumerate individual untracked files |
| FR03 — high | Line 19's “If none is specified” could suppress fallback commands when an explicit check exists | Restore the Project-specific antecedent |
| FR04 — high | Line 27 shared one placeholder among six command categories | Restore individually fillable command entries |
| FR05 — medium | Line 19 reported unrelated baseline failures without defining their completion effect | State that they do not block Done only if required checks pass and no new/uncertain failures remain |
| FR06 — medium | Lines 3 and 6 omitted “nested” and the specific object of the human waiver | Restore nested-document scope and the ask for that check-gaming exception |

The initial claim that the compressed Project entry retained all its fields
was too strong: retaining category names did not retain individual fillable
slots. FR04 corrects that assessment. Likewise, the initial ownership command
did not fully support F03 for files inside an untracked directory; FR02 is an
instrumentation correction to that newly proposed ownership rule. Neither
finding changes the shipped text or rewrites an old result.

The reviewer re-read the final 4,435-byte candidate, SHA-256
`0d50213d56fbefd3a16a12ee0ce092e39c2ba5346276097dab7784af34e7ac7f`,
and accepted all six dispositions. It found no further material semantic loss
and confirmed the intended readings of F01–F18 and S01–S16, with only the two
authorized policy regions differing from shipped behavior. This is a static
model judgment, not proof of equivalent interpretation or observed compliance.

## Contract mapping

IDs and source line numbers refer to the [earlier contract table](audit.md#rule-by-rule-contract-and-changes).
The complete candidate remains the authority for exact wording; this table
classifies changes rather than adding instructions outside it.

| Source clauses | Focused disposition |
| --- | --- |
| H; B1–B3; B5 | Editorial compression; project-document scope, within-file Boundary priority, observed existence evidence, all action categories, secret restrictions and human-only authority remain |
| B4 | Exact source wording; no new external-write exception or approval lifetime |
| P1; D3 | Ownership change: initial status and staged/unstaged diffs, preserve initial work, ask before conflicting overwrite, compare final state with that baseline; original caller/helper/plan requirements remain |
| P2; W1–W2 | Editorial compression and combined Work section; ambiguity branches, smallest complete change, reuse and both stopping conditions remain |
| D0; D1 | Completion change: mandatory passes, requirement-defined applicability, named fallback sources, disclosed baseline failures and limited no-command completion; no required check is waived |
| D2 | Editorial compression; before/after regression and feature tests, no-suite and cannot-reproduce-in-a-test exceptions remain |
| R1–R2 | Reporting appears in Done; command results, all inventory categories, uncertainty and evidence-based pushback remain ordinary obligations |
| T1–T3 | Compact Project template retains stack/package manager, each command category, generated files, API contract and deeper-document pointers |

All five historically attributed source lines (6, 13, 21, 22 and 26) are
rewritten. Their old results cannot establish this candidate's effect, even
where the intended obligation is unchanged. No criteria score was used to
select wording, and no whole shipped rule was removed.

## Final size

| Text | UTF-8 bytes | Whitespace words | LF-terminated lines | Bytes versus shipped |
| --- | ---: | ---: | ---: | ---: |
| Shipped | 4,438 | 725 | 32 | — |
| Earlier conservative draft | 4,355 | 702 | 32 | −83 |
| Earlier structural draft | 6,041 | 935 | 34 | +1,603 |
| Focused candidate | 4,435 | 658 | 28 | −3 (−0.07%) |

The new [measurement record](focused-measurements.json) pins the shipped and
focused files by hash and defines byte, whitespace-word and LF counting. The
validator's captured JSON was copied unchanged: 1,239 bytes, SHA-256
`7343b0d480d0a6dce06b01ab0d96718c4c8af713c0c726bc333fec16b1b874ca`.
The earlier rows come unchanged from the [original measurements](measurements.json).
The focused text is 1,606 bytes shorter than the broader structural draft,
principally because it excludes that draft's additional policies. That is not
lossless compression of the broader draft. No rules were moved out of the
measured text; Project placeholders are included. These counts are not tokens.

## Recommendation and limits

Use this focused draft as the next design candidate instead of carrying the
larger structural draft forward wholesale. It fits the shipped byte ceiling
while addressing two independently identified defects. The saving against the
shipped file is only three bytes: the achievement is accommodating those
changes without growth, not substantial compression. A still smaller text may
be possible; this attempt establishes no lower bound.

Keep the shipped file in place. Static agreement cannot establish minimal
behavioral impact, successful ownership protection, reliable completion
judgment, cheaper work or superiority over another design. The eighteen cases
are review examples, not simulation runs, and the existing fixture dry-run
does not execute an agent under this candidate. Tokenizer counts, model
interpretation, task outcomes, total cost and latency remain unmeasured.

An adoption proposal still needs the methodology's observable tasks, test-set
version and lock where needed, contemporaneous comparison cells, a fixed
acceptance rule and revert set. This work authorizes none of those paid runs.
Approval lifetime, external-path ambiguity, verification budgets and stopped
processes remain separate issues. The earlier corpus comparison is reused as
context, not a new survey or a ranking.

## Free verification and delivery scope

The validator ran these commands on the final candidate:

| Command | Result |
| --- | --- |
| `python3 -m unittest` | Passed, 367 tests, 19.051 seconds |
| `python3 scripts/compare.py --check` | Passed |
| `python3 scripts/experiment.py --dry-run` | Passed, 12 stored fixtures |
| `python3 -m unittest tests.test_docs` | Passed, 95 tests, 1.116 seconds before the final report append |

Read-only checks confirmed that the baseline tracked files were unchanged
except for the README append, including the shipped file, earlier audit and
drafts, criteria, scorers, generated data and the frozen pre-registration
prefix. The retained private archive still contains 772 files with tree hash
`b4e9c53e1c625adb12b8aa805520f58018fffe510614276941072e75fb6567da`;
the public result retains SHA-256
`eed65dcf792f280ddf96eba4714afcce31fbbbed09cbd446c20f20899f26a4ab`.
The archive check used sorted relative path, NUL, file bytes, NUL, without
printing its contents. A link inspection preceded the JSON copy and found its
target absent; the captured measurement file was then copied to that target.

The first staged invariant audit also failed with exit 128 on this command:

```text
git show 2f6a023154ede9fa090fb4c0be281b97057d6bf2:experiments/text-design/focused-measurements.json
fatal: path 'experiments/text-design/focused-measurements.json' exists on disk, but not in '2f6a023154ede9fa090fb4c0be281b97057d6bf2'
```

That invocation incorrectly looked for a newly staged file in the baseline.
The corrected audit enumerates baseline paths with `git ls-tree` and checks
the new measurement separately. It passed all 229 baseline paths, the four
staged paths and eight local links; the initial invocation is not counted as
a pass. The post-append documentation suite passed 95 tests in 0.928 seconds,
and `git diff --cached --check` passed before this failure record was added.

No runtime feature, test, dependency or scorer was added. The candidate texts
are data for comparison; their embedded instructions were not treated as
authority for this checkout. No existing file was deleted. External actions
for this follow-up are issue 20 and publishing this branch/update to PR 19.
No provider experiment, root adoption, merge or change to old results was
performed. The behavior and cost unknowns listed above remain unverified.
