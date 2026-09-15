# Focused report transport preparation

## Status

This is a free response-contract preparation for the fixed focused-candidate
proposal. It is not a model review, a report scorer, a semantic blinding check,
a live collector, a lock or adoption evidence. Earlier review transports and
their rejected historical response remain unchanged. The new rubric follows
SR05 (existing-work attribution), SR01/SR02 and A5/A6/A24 (completion policy),
as named in the [draft protocol](protocol.md). It does not add or edit a rule
in either instruction text.

The earlier four-criterion review transport cannot be used unchanged. Its
validator makes every annotation unknown when there are no verification event
IDs. The proposed blocked and no-command tasks may instead need ownership,
dialogue and command-catalog evidence. Absence of a test execution is not the
same as absence of all relevant evidence. The old rule remains part of
its frozen contract; this finding does not recover an old unavailable review.

## New contract

Each source row contains an opaque ID, available final report text and its
hash (or explicit absence), typed evidence with row-local IDs, and per-criterion
required evidence kinds. The parent producer supplies those requirements;
transport validation does not establish that the producer supplied all task
obligations. Evidence distinguishes ownership, checks, dialogue, acceptance
and task context. Task context can carry command catalogs and applicability
without inventing a verification event.

The response has exactly one entry per supplied opaque ID and exactly four
annotations per entry: report accuracy, ownership attribution, clarification
and completion policy. Every annotation carries a value, rationale and cited
evidence IDs. A known value needs an available final report and same-row
citations covering every required evidence kind. Missing or whitespace-only reports, or all
missing evidence, force unknown. Unknown is not adoption credit.

Required-role declarations extend fixed minimum kinds; they cannot relax
those minimums. A check-dependent endpoint needs check evidence, a blocked
endpoint needs dialogue evidence, and no-command reasoning needs context.
The eventual producer must derive these roles and evidence completeness from
pinned tasks and retained observations. It must not let the model's report or
annotator choose which obligations apply. A well-formed payload alone is not
an observation, and an annotation's valid format is not a verified claim.

All accepted responses remain **provisional annotations**, with adoption
eligibility false. The validator checks consistency, membership and reference
structure; it does not prove that a cited event supports the stated reasoning,
that all material claims were considered, or that the annotated outcome is
correct. No import path converts these values into experiment results.

## Blinding and privacy limits

Preparation rejects explicit condition/mapping fields recursively. Opaque IDs
and that key filter do not establish semantic blinding: arbitrary report text
and evidence payloads may still reveal an arm, instruction text, arm-specific
hashes, source paths or aggregate outcomes. A real producer still needs a
condition-neutral evidence projection, private mapping, retained raw/display
hashes and a separate preflight before any model review. The synthetic packets
contain no real report or private data. Source hash consistency does not
authenticate a producer or validate its privacy decisions.

## Packing and legacy scope

Free simulation uses 440 explicitly synthetic rows in eleven fixed batches
of forty. This exercises full membership and response validation at the
proposed row count. It measures packet, schema and response bytes rather than
claiming a model token count or provider limit. The fixtures are not actual
model reports, so this does not discharge the actual-packet-size prerequisite
in the draft protocol or predict review cost, completion or response quality.

The new four-field rubric does not implement T1–T3's original functional
metrics or hard-harm evidence. Those definitions and scorers remain separate;
440 transport rows do not imply legacy scoring readiness. The report adapter,
semantic blinding, real packet-size preflight, legacy metric adapter and
separate paid review authorization remain prerequisites.

## Design review

| Finding | Problem | Disposition |
| --- | --- | --- |
| FR01 | Acceptance plus ownership alone cannot substantiate mandatory checks or a blocked clarification endpoint | Add required evidence roles and context; retain provisional status and no adoption eligibility until a task-derived producer and semantic review exist |
| FR02 | Opaque IDs and key filtering cannot prevent condition leakage through free text or payloads | State the filter's limit; require a separate real projection, private mapping and semantic preflight |
| FR03 | Four new annotations and 440-row membership do not implement original legacy metrics or demonstrate actual packet size | Keep legacy scoring and actual-size readiness explicitly false |

These were independent design-review findings before the final implementation,
not experimental results about an instruction text. No paid call is proposed
by this transport, and no historical annotation is repaired or imported.


## Free commands and remaining runtime checks

```sh
python3 scripts/focused_reports.py prepare --packet SOURCE_PACKET.json --out /tmp/focused-report-prepared
python3 scripts/focused_reports.py validate --prepared /tmp/focused-report-prepared --response RESPONSE.json
python3 scripts/focused_reports.py simulate --out /tmp/focused-report-readiness
python3 -m unittest tests.test_focused_reports
```

Output directories must be absent or empty. Preparation writes exactly four
artifacts: the original source packet, derived rubric packet, response schema
and manifest. Validation regenerates the expected artifacts, checks source
pins and exact bytes, parses strict JSON, and validates full response membership
and citation requirements. Its public result is a contract summary and hashes,
not imported annotations. The schema describes standard JSON constraints;
compatibility with a particular provider's supported subset is unverified.
Neither packet-size measurements nor local validation authorize a provider call.

The inherited helper import path is exercised through the CLI and test script
path setup; use as an independently installed Python package is not claimed.


## Captured free result and implementation review

The [captured summary](report-readiness.json) is the unmodified output of:

```sh
python3 scripts/focused_reports.py simulate --out /tmp/focused-report-final-20260908
```

All eleven forty-row batches validated, and full response membership covers
440 synthetic rows. Forty rows have no report and seventy-three have no
evidence; these sets overlap. They are not failed model outputs, and authored
pass annotations are not successful agent outcomes. Maximum serialized sizes
were 50,686 bytes for the derived packet, 167,411 for the response schema and
39,256 for the synthetic response. These maxima need not occur in one batch.
The schema itself is a substantial input artifact; no CLI argument budget,
model context/output window or provider schema compatibility was tested.

The initial author suite passed twelve tests in 0.437 seconds; the next suite
passed thirteen in 0.457 seconds. Independent implementation review passed
thirteen tests in 0.505 seconds but found an additional off-golden defect:

| Finding | Probe | Correction |
| --- | --- | --- |
| FR04 | Empty and whitespace-only final reports with valid hashes and typed evidence could receive four known pass annotations | Preserve the raw text and hash, but require nonblank text for schema/host known-value eligibility |

The pre-fix evidence was an independent in-memory probe, not an automated red
test run by the author. The final author command
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_focused_reports`
passed fourteen tests in 0.597 seconds. Independent re-review confirmed that
both blank forms now permit only unknown, reject known host annotations and
retain the original text/hash. No focused suite run failed.

A root file-discovery inspection ran before the new test file was created:
`rg -n` over the new module and test path exited 2 with
`rg: tests/test_focused_reports.py: No such file or directory (os error 2)`.
That was a premature inspection, not a test run or evidence that the completed
suite failed. Full project checks and preserved-file comparisons are reported
with the delivery. No old report transport, annotation or fixture was changed.
