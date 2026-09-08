# Focused observation preparation

## Scope and evidence boundary

This is a free, offline parent-owned observation instrument for the existing
functional task seeds. It is not a live agent collector, a report interpreter,
a new lock or adoption evidence. The instruction texts and earlier artifacts
remain fixed. It supplies a checked local evidence format for the observation
prerequisite in the [draft protocol](protocol.md#what-must-exist-before-a-new-lock).

The historical [observation diagnostic](../verification-budget/observation-diagnostics-2026-09-08.md)
found twelve unverified evidence rows, including strict command-string linkage
and parser limitations. Those retained outcomes stay unverified. This new
instrument makes no attempt to recover or reinterpret them. Its fixed command
API records execution directly in an offline parent process; connecting an
actual agent's request to that process remains a separate unverified step.

## Collection contract

The collector materializes a pinned task and records the initial worktree and
logical Git index. Fixed manifest command IDs select the local Python checks.
Each check records its phase, actual execution evidence and before/after state;
explicit checkpoints record sampled changes. A seal binds the ordered record
count and final state. Source pins identify the instrument and fixture inputs.

A passing final-state check needs a successful observed process with a nonzero
test count and matching pre-check, post-check and sealed final state. A baseline
pass alone cannot prove final verification. An edit after a passing check makes
that observation stale unless a later final check supplies relevant evidence.
An unavailable script, zero tests or missing final observation cannot be
promoted into a pass. A baseline failure remains a failure, even if a separate
completion policy would allow an honestly disclosed result.

Hashes establish consistency, not authenticity. Someone able to rewrite an
entire bundle can compute new hashes. The format is not a security boundary
against same-account filesystem access, forged subprocess output or hostile
fixture code. It supports trusted checked-in mini-repositories only.

Checkpoints describe sampled chronology. Neither matching before/after hashes
nor a seal proves that an intermediate overwrite or direct, unobserved command
never occurred. An eventual agent adapter must retain request/result identity,
intermediate observations, complete process lifecycle and costs before claiming
agent coverage or behavior. This instrument does not fill those fields from
fixture expectations.

Full-tree relevance is deliberately conservative: even an unrelated change
can invalidate an earlier check. Any future narrower relevance contract must
be declared before collection, rather than inferred after a desired outcome.
Generated Python cache directories and internal Git files are excluded from
the worktree inventory; logical index state is represented separately.

## Relation to acceptance and reports

Functional acceptance, preservation, observed verification, completion policy
and report accuracy remain separate questions. This module observes checks; it
does not infer a correct final report from a successful task artifact.
The task-seed grammar for C1/C2 is bounded by the public example tests, including
the literal `returns` form. Equally correct prose outside that grammar requires
an explicit future disposition; regex rejection alone must not be presented
as proof that the prose is semantically wrong.

No provider or natural-language reviewer runs here. No condition is compared,
no cost advantage is predicted, and no candidate rule is changed in response
to an observation. Live reporting, task independence and the draft adoption
gate remain unverified.


## Free commands

```sh
python3 scripts/focused_observation.py simulate --out /tmp/focused-observation-readiness
python3 -m unittest tests.test_focused_observation
```

Use an absent or empty output directory. The CLI supports only local simulation
and writes `results.json`; the parent collector API is exercised by those local
fixtures. It does not start or control a model. Results include both expected
classifications and observed evidence, so a failed oracle cannot disappear into
a count of successful checks. Final verification results are independent of
completion eligibility and remain separate from baseline outcomes.


## Preparation and review record

The [new capture](observation-readiness.json) records fourteen matched expected
classifications: two passed, eight unknown, two failed, one unverified and one
unavailable. Four intentionally corrupted bundles are invalid/unknown; missing
final checks and stale state can also be unknown in an otherwise consistent
bundle. The 73 source pins cover the new module and the unchanged task sources.
The artifact is the unmodified output of:

```sh
python3 scripts/focused_observation.py simulate --out /tmp/focused-observation-final-20260908
```

It contains zero provider calls and explicitly unknown agent coverage, report
accuracy and agent cost. The runtime metadata describes the local Python/Git
instrument, not a model runtime. Source/runtime drift invalidates replay under
current pins rather than silently relabeling older records.

The authored focused suite initially passed eleven tests in 6.233 seconds;
that did not establish the final design's correctness. Root inspection and
independent off-golden probes found three issues before publication:

| Finding | Evidence before correction | Disposition |
| --- | --- | --- |
| FO01 | A C4 verifier added to the fixture and actually exiting zero still received unavailable solely from its command label | Require before-state absence plus observed nonzero missing-file diagnostic; contradictory availability is unknown |
| FO02 | A stdout integer of 27, with consistency hashes recomputed, was accepted as valid/passed | Require string stdout/stderr even in a consistently hashed bundle |
| FO03 | Static inspection found that only stale passes were made unknown; an earlier failure could be attributed to a later edited state | Make all stale final classifications unknown; retain the actual historical statuses separately |

FO01/FO02 were independent disposable-repository probes, not automated red
runs before the implementation changes. FO03 was a code-review finding; the
added test executes a failed C1 check, fixes the file and seals without a new
check, requiring historical failure and final unknown. The final regressions
also cover stale unavailable evidence, integer/boolean schema fields,
index-only changes, nested untracked files, execution-time mutation and
rehashed output tampering. Hashes still do not authenticate a producer.

The final author command `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
tests.test_focused_observation` passed fourteen tests in 7.055 seconds. No
focused suite run failed during this implementation. Independent re-review
reproduced FO01's present-verifier and stale-unavailable cases and FO02's
rehashed nonstring output case against the final module. Full project checks
and protected-file comparisons are reported with the delivery.

This preparation does not change completion policy, implement report scoring,
recover earlier unavailable observations, or establish live collection
readiness. All statements about final verification are limited to the locally
executed fixed commands represented by these bundles.
