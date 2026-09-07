# Verification-budget paid pilot collection record (2026-09-07)

## Status

**Collection complete; blinded review unavailable.** A human gave explicit approval in the active
conversation on 2026-09-07 for this paid pilot, its single blinded review call when affordable, and
publication of the completed record and pull request. Provider calls began only after the frozen
precollection capture below. The candidate is not adopted. This is an operational record, not a
model-behavior conclusion.

The preparation-time statement in [the protocol](protocol.md#free-readiness-work) that no paid-run
approval existed remains historical. Its fixed predictions and review rubric are unchanged.

## Fixed collection plan

The planned batch is 6 scenarios (`b-one`, `b-two`, `f-draft`, `f-old`, `v-api`, `v-doc`) × 2
conditions (`current`, `candidate`) × 3 fresh replicates: 36 sequential rows. It uses the runner's
deterministic randomized paired order, seed `verification-budget-pilot-v1`. No historical cell is
reused. A failed, stopped, partial, or unverified row remains in the batch: there is no retry,
replacement, relabelling, or candidate/root-file change.

The collection uses the runner defaults: requested model `claude-opus-5`; 80 maximum turns;
900-second agent timeout; 120-second verification timeout; and $3 maximum budget per collection
run. Its fixed CLI flag set is `project-settings`: `--output-format stream-json --verbose
--no-session-persistence --tools Bash Read Edit Write Glob Grep --permission-mode acceptEdits
--allowedTools Bash --setting-sources project --strict-mcp-config`, with the model, turn, and
per-run budget flags above. `--restricted` is not used. The actual CLI version is not inferred
here: free preflight captured raw `claude --version` as `2.1.263 (Claude Code)` and normalized it
to `2.1.263`. Retain both forms with each row's init event and `meta.json`.

Before the first provider call, the generated `plan.json` must pin the current and candidate
instruction files, the scorer, and every scenario's seed, brief, manifest, evaluator, and reference
where present by sha256. Those frozen hashes, the exact schedule, and the exact argv values belong
in this record once supplied from the saved artifacts. The collection must use the root `AGENTS.md`
as `current` and `candidate/AGENTS.md` as `candidate` without changing either source.

Before every next row, compare the installed CLI version, requested and reported model, and all
pinned source hashes with the frozen precollection values. Any version, model, or source drift
stops the batch before that next row. The row that revealed drift remains retained and is not
retried or replaced; this is a stop condition, not a limitation to normalize away.

A row that exhausts `max_turns` or its $3 `max_budget_usd` is a retained resource-limited outcome,
not a reason to truncate the other scheduled conditions. Continue with the next scheduled row when
its reported cost is known and the model, CLI, and sources still match, subject to the shared
reservation below. A generic CLI or API error, timeout, missing or invalid cost, or any model, CLI,
or source drift stops later scheduling. No stopped row is retried or replaced.

## Frozen precollection settings and source pins

Batch `20260907-090636` saved its `plan.json` and `collection-pins.json` before its first provider
call. The plan records `paid_calls_started: 0`; the independently retained expected and actual
source-pin aggregates matched at `1dff0e37dcd7994d522a7734fe4036d398b3234aa5bb54abd632f2875f76f733`.
This section records only frozen configuration and provenance, not a row outcome or comparison.

| Input | sha256 |
| --- | --- |
| `current` root `AGENTS.md` | `2811faf02714c8426746c6d7a7df0d4931e44718f568a8f1df739df2e8a77aa5` |
| `candidate/AGENTS.md` | `66a36b42465a32b7465bb8344438ac56a9cca9a70d52e6e2eb58071bea8134bc` |
| Runner and scorer | `df3383769ab4c2451e9228d7ddd573097f48360455412a65a3d21cd4641276f8` |

The precollection CLI check returned raw `2.1.263 (Claude Code)` and normalized `2.1.263`, with
status `recorded`; source-pin status was `matched`. The plan fixes requested model
`claude-opus-5`, 80 maximum turns, $3.0 maximum collection budget, 900-second agent timeout,
120-second verification timeout, the `project-settings` flags listed above, and the 36-row
deterministic schedule. Its source pins are:

| Scenario | Seed | Brief | Manifest | Evaluator | Reference |
| --- | --- | --- | --- | --- | --- |
| `b-one` | `bcb5a185acb897fa76b95c068fad7967f24c0417adbe4bb9e8b55e9142530e41` | `3ff9e44b2c7859f7b96fbaf853d24bc33e17693602cd5601b449367f87c267c9` | `38bb2c6572a6701201420b79546b16eb9366a06364648a3685c4310d101e6f2e` | `ffea53a92bc0c39116a439df8bbfb530afcad591bf7955f380f3c9d376589381` | — |
| `b-two` | `bcb5a185acb897fa76b95c068fad7967f24c0417adbe4bb9e8b55e9142530e41` | `68aa71bc7c38f06273c924e4ba86fdf3ec9a720ff2589b74b8f59c436ed96966` | `dc5c73526bd92d2571db50b276a0ae47c5960a809ab404c9e5b20b925ce33911` | `ffea53a92bc0c39116a439df8bbfb530afcad591bf7955f380f3c9d376589381` | — |
| `f-draft` | `0a36a751893d473f38050becddd1d4093f2427f4078de456399ca5fd26e95391` | `7f7adb8f867a63602696aec87e518a792d8f8a68b428fe4db532151cf655e21e` | `8e34d31bd738d6d2327bd1881ecd581b9bb4cc9dfb83b2fec00999ad5922b179` | `6803ffb68b6d34ab8018d48423334b6c735ea86b1368391e091cd70218492f9c` | `902029dbc7a21ac21638852d3c366bf0e9b8757fa8468434492524d503b02d1b` |
| `f-old` | `c21fe19797d04ca55247ce8afaf9a0e0f21d23e80c22e5d6d41c54e5f6be28b9` | `564ac7bdbbd20b6e6cfa6b5c174b0953424cc02fd7edb212b56151cac7ee8577` | `7cfd0cbc06293a11f63e694d1c2679d566fa3d6384b777819c18607d0db3947f` | `3b5cdc81edbe206db2116b46826c0589b66bd82b6ed015f4c3c8bbc7f5aaad19` | — |
| `v-api` | `1cf3ad4d5acbff84609f54bf8e3e420035b8d2c4be5fa87b346c4f9d829d4782` | `ebdb95d52f7a3805a396aaba0dcda2da57068bde7f8d3da380e8d813b19cd72d` | `640f19117511beeb08d9cdcbdd5804c5fc8651cee1f96024f0e89df5c96e84da` | `21b40dcb06466d4945b11867bf58ba8a58f86f1dad43b2141e06c6dd59f16d55` | — |
| `v-doc` | `d7b88a1446ccd58c134d424cb50860fc487508811354522959f332a174661d03` | `02fd05962857e1c8345ea3b873c388e96b24f2b813be817d5c9140cbfaf8d759` | `fa63f39197e8ff8e46040dbc2d8f3a1c0104af9fc4b1aa52584880598e180141` | `afebcacdc21546760bc04e29b602a5ff77bb119fc9ca598e95ab253c3312de78` | — |

## Shared budget control

The collection and review share a $25 control. Collection retains its existing $3-per-run
reservation: before a new row, stop when `known_spent_usd + 3 > 25`; a missing or invalid reported
row cost also stops later collection. `known_spent_usd` is the sum of retained numeric
`total_cost_usd` values, not an estimate.

After collection, make at most one no-tools reviewer call, and reserve $3 for it only when the
known collection spend is available and `known_spent_usd + 3 <= 25`. Otherwise skip the review and
record why; do not retry it. This $3 review allocation is a control reservation, not an empirical
cost estimate: there is no directly comparable historical review-cost data. Neither reservation
nor the per-run maximum guarantees a billing ceiling.

The historical collection-only comparisons are $12.2472 (`36 × $0.3402`) from the recorded `ours`
mean and $21.0708 (`36 × $0.5853`) from the recorded historical maximum. They are illustrative
collection estimates, not bounds and not estimates of the review.

## Blinded review

If its reservation is allowed, the one reviewer call uses no tools and receives the unchanged
protocol rubric plus every retained row under randomized opaque IDs. Each packet item contains only
the listed supporting artifacts and final text. It excludes explicit condition labels, current and
candidate instruction text, schedule order, and condition-derived aggregates. This blinding cannot
rule out an inference from the reports themselves.

Before display, deterministic redaction replaces absolute path prefixes while preserving relative
paths. The record retains both the original final-text sha256 and the redacted display-text sha256.
The reviewer returns only the fixed `pass`, `fail`, or `unknown` annotations with
`provenance: label_blinded_model_review`, the relevant final-text hash, and supporting evidence-event
IDs. Conditions are joined only after that annotation is fixed. An unavailable, unaffordable, or
cost-unknown review stays absent or unknown; it is never reconstructed from collection evidence.

## Free readiness history

No paid or model call occurred during readiness. The first focused
`python3 -m unittest tests.test_verification_budget tests.test_verification_review` run exited 1
with a `SyntaxError` in `tests/test_verification_review.py:122`: invalid `}, for row in ...` syntax.
After that source changed, a second focused run exited 1 with the remaining mismatched closing `}`
versus `[` in the same helper. These are retained as two distinct local fixture-construction
failures, not a retry on unchanged inputs.

The next focused run executed 38 tests and had one failure and one error: review references used
invalid event IDs and the first mocked review invocation returned 1. The fixture had emitted a
literal `\\n` instead of a newline, so the event marker was not on its own line. Correcting that
fixture escaping left the product matcher assertions unchanged. These local test-fixture and
instrumentation findings do not test a model prediction or candidate effectiveness.

Final free revalidation passed: the focused suite passed 38 tests in 4.481 seconds; the full
`python3 -m unittest` suite passed 338 tests in 17.426 seconds; and
`python3 scripts/compare.py --check` passed. The old dry-run covered 12 fixtures; the new
simulation covered 13 states; score, summarize, review preparation, and review invocation dry-runs
made zero paid calls. Negative cost, runtime, and privacy probes passed. The reviewed diff left the
root and candidate lock inputs unchanged.

## Collection results and unavailable blinded review

The collection completed all 36 scheduled rows with exit code 0, all row return codes 0, no timeout,
no resource-limit outcome, no runner or CLI error, and matched source pins, model, and CLI version.
All reported row costs were recorded and sum to **$5.880974**; the batch did not stop early. The
complete relative-run, redacted projection is
[`results-2026-09-07.json`](results-2026-09-07.json). It is derived from retained raw artifacts,
not hand-entered metrics.

| Metric or record | `current` (18 rows) | `candidate` (18 rows) |
| --- | --- | --- |
| Functional acceptance | passed 18 | passed 18 |
| Required verification coverage | passed 6; failed 4; unverified 8 | passed 10; failed 4; unverified 4 |
| Verification evidence | observed 10; unverified 8 | observed 14; unverified 4 |
| Verification budget | within budget 5; not applicable 5; unverified 8 | within budget 3; not applicable 11; unverified 4 |
| Same-check passing repeats | zero 10; unknown 8 | zero 14; unknown 4 |
| Unrelated edits / test tampering | 0 rows with either | 0 rows with either |
| Reported cost | $3.0108525 | $2.8701215 |

Functional acceptance reached a 36/36 ceiling. The 12 coverage unknowns (8 `current`, 4
`candidate`) remain unknown; they are neither failures nor zeroes, and their unequal missingness is
not a candidate verification advantage. The paired descriptive counts above preserve the study
design, but this collection makes no composite score, significance, effect-size, ranking,
directional-separation, or adoption claim. The fixed
no-directional-separation prediction is not established merely by this acceptance ceiling or by
null and unknown values.

The runner controls reached their expected recorded states in both conditions: artifact integrity
and basic syntax passed in 18/18 rows each; the baseline status was recorded in 6 and not applicable
in 12; evaluator test counts were nonzero (one test in 6 and two in 12); clean owned-process-group
evidence and a clean runner-parent supervisor were each recorded in 18/18. These controls support
artifact interpretation; they do not award either condition a performance credit.

The prepared label-blinded packet covered all 36 final reports under opaque IDs; 33 rows had
observed event IDs and 3 were not joinable. Its one authorized no-tools call started with the
matched model and CLI, returned exit code 0 without timing out, and reported $1.892734. Its response
was `malformed_or_unverified`: it contained 34 of 36 opaque entries and omitted
`review-2fOGXePi7jz-EICF` and `review-Sgatxqjj83sj-hpe`, so exact-membership validation rejected
it. No validated `review-response.private.json` was emitted; the original rejected response remains
in the retained transcript. No annotation was imported or joined, and there was no retry. The
expected complete-review outcome was not achieved. The total recorded collection-plus-review cost is
**$7.773708**. This is an unavailable review, not an all-unknown review fabricated from collection
evidence.

## Coverage unknown audit

The 12 `unverified` coverage rows are a conservative transcript-and-parent-observation result, not
evidence that an agent ran an off-endpoint test, bypassed verification, or found an instrument
defect. The retained evidence has 9 rows with direct transcript uncertainty, 2 with unverified
parent/transcript linkage, and 1 with both. The public projection lists every affected relative run
ID; representative rows are `run-03` (direct uncertainty), `run-25` (linkage), and `run-34` (both).
The instrument leaves all of them unknown instead of converting them to pass, fail, or zero.

[`provenance.json`](provenance.json)'s `candidate_status: unmeasured` is a historical
preparation-time snapshot and is intentionally unchanged. The current dated record is a measured
pilot collection, but the candidate remains unadopted.

## Public projection and raw evidence

The public JSON contains relative run IDs, redacted display reports, original and display report
hashes, selected redacted evidence, exact metrics, and hashes for retained raw run artifacts. It is
a derived public projection, not a byte-identical raw archive or a standalone rescoring input:
absolute-path-dependent scoring requires the unchanged local raw artifacts. The projection never
rewrites raw paths or metadata to impersonate an original; its privacy and reproducibility limits
are stated in the JSON itself. The unchanged raw batch and, after review, the packet, mapping,
invocation, and rejected transcript/stderr are preserved separately from the public projection.
The private archive is `data/verification-budget/20260907-090636`, intentionally ignored and not
published; its tree hash is
`b4e9c53e1c625adb12b8aa805520f58018fffe510614276941072e75fb6567da` under
`sha256(sorted relative path + NUL + file bytes + NUL)`. It includes the exact temporary derivation
helper at `derivation/derive_verification_budget_public.py`, sha256
`e2d26d986de30a14951dfc40062a137fbd0bb011df77d010695108a6e0538d15`.
