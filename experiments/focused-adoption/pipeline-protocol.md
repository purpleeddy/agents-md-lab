# Focused local evidence pipeline

## Purpose and boundary

This free integration connects the existing task, observation and provisional
report tools. It generates review input from actual local fixture execution;
it does not connect an agent, interpret a model report or open an adoption
gate. Instruction texts, earlier instruments and captures remain fixed.
The [draft experiment](protocol.md) still requires live request attribution,
report review, legacy metric integration, real packet-size preflight and a new
lock before a separately authorized collection.

The integration addresses a gap between the earlier independent checks:
matching each instrument's own fixture expectations does not establish that
its evidence belongs to the same task, variant and final tree as another
instrument's evidence. A valid report contract also does not establish that
its required roles were derived from the task rather than chosen by an author.

## Evidence production

For each fixed local scenario, the pipeline materializes an actual task,
retains its initial protected-path snapshot, executes parent-owned checks and
seals the sampled worktree/index chronology. It then runs the existing
independent functional/ownership acceptance and requires the full observed
state to equal the seal both before and after that evaluation. Source pins
must remain unchanged through collection, acceptance and packet production.

The independent evaluator also runs local checks of its own. Those are not
promoted into collector evidence or attributed to an agent; the producer uses
the sealed collector's final-check classification. Acceptance evidence is
separate from verification and from the final report. A failed functional
check can be evidence for an honest incomplete report; it is never converted
into a successful edit.

A context item carries the task brief, expected endpoint and declared check
catalog. Ownership and acceptance items carry actual observations bound to
the same task/variant and sealed state. A check item is emitted only when all
applicable final checks have known, current observations. Missing or stale
observations remain retained telemetry in context, with no qualifying check
item. This prevents a baseline pass alone from satisfying a final-check role.

Required roles come from the pinned task manifest. Completion requires
ownership, acceptance and context, plus checks when applicable and dialogue
for a blocked endpoint. Report accuracy uses the same conservative coverage
requirement; ownership attribution and clarification retain their respective
minimums. This can withhold a known annotation even when a narrower claim is
assessable. It does not loosen the draft gate or claim complete semantics.

No dialogue is fabricated from a brief, expected endpoint or report string.
The blocked ownership tasks therefore retain unknown clarification eligibility
in this free integration. Their preserved files alone do not prove that an
agent asked a question or reported the conflict correctly.

## Retained result and limits

The result retains observation bundles for independent classification replay,
actual command evidence, acceptance/state bindings, report inputs and source
pins. Hashes prove consistency only, as described by the
[observation protocol](observation-protocol.md). Replaying a classification is
not re-executing an agent or authenticating an event producer.

Reports and all-unknown response annotations are explicitly authored fixtures.
The [report transport](report-protocol.md) checks only their structure and
citations. Known evidence availability, a valid response and artifact success
are distinct from a correct model report or successful adoption outcome.
No reviewer runs and no provisional response is imported.

All ten good task variants are joined, with additional missing-final-check,
stale-after-edit, bad-functional-fix and protected-work-loss cases. These are
fourteen instrument scenarios, not fourteen independent tasks or condition
comparisons. The existing bounded prose grammar and sampled-chronology limits
remain in force. Output projection is exercised on these trusted fixtures;
semantic blinding and privacy for arbitrary live reports remain unverified.


## Free command and result

```sh
python3 scripts/focused_pipeline.py simulate --out /tmp/focused-pipeline-final-20260908
python3 -m unittest tests.test_focused_pipeline
```

Use an absent or empty output directory. The CLI supports simulation only.
The [captured result](pipeline-readiness.json) is the unmodified local command
output: 582,960 bytes with 77 source pins and fourteen matched expectations.
Artifact acceptance is eleven passed and three failed. Eleven rows have known
current check evidence; the no-command, skipped-final and stale rows do not.
All three blocked cases lack required dialogue evidence. These counts describe
different dimensions and must not be pooled into an agent success rate.

The report packet has fourteen fixture reports and 56 authored unknown
annotations. It passes the provisional transport contract, not semantic review.
The observed collector bundles are retained in full for replay, while report
evidence also has a compact projection bound to those bundles and the shared
sealed state. Raw evidence hashes and public projection hashes keep their
previous meanings; no private absolute path is intentionally published.

Independent design review identified the joins requiring inspection: shared
task/variant/seal identity, unchanged source pins across phases, and retained
rather than discarded observation bundles. Implementation review found no
material defect within the fixed simulation scope. The author's focused
command passed eleven tests in 10.686 seconds; independent re-review passed
eleven in 10.573 seconds. Tests include acceptance-induced state mutation and
source drift rejection, preserved failure outcomes, missing/stale check-role
withholding, blocked dialogue absence and replay of the retained bundles.
No focused suite failed in this implementation. Full project checks and
protected-file comparisons are reported with the delivery.

This is a task-derived **local fixture** evidence producer. It does not accept
arbitrary live transcripts or establish a provider adapter's authenticity,
complete process lifecycle, report extraction, semantic blinding or costs.
Those missing components cannot be inferred from the joined local artifacts.
