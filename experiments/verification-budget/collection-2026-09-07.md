# Verification-budget paid pilot collection record (2026-09-07)

## Status

**Authorized, pending collection.** A human gave explicit approval in the active conversation on
2026-09-07 for this paid pilot, its single blinded review call when affordable, and publication of
the completed record and pull request. No provider call, collection row, or reviewer call has yet
started. This is an operational addendum and result placeholder, not a model-behavior result.

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

## Result placeholder

| Field | Status before collection |
| --- | --- |
| CLI preflight | Captured: raw `2.1.263 (Claude Code)`; normalized `2.1.263` |
| Frozen source hashes and exact argv | Pending saved `plan.json` and row metadata |
| Collection rows and outcomes | Pending; no rows started |
| Blinded review | Pending shared-budget decision; no call started |
| Actual collection and review cost | Pending reported provider cost artifacts |
| Comparisons, limitations, and publication record | Pending retained artifacts; no result or adoption claim |

When artifacts are available, complete this record with the batch location and timestamp, all
frozen hashes and settings, every row's retained status, actual costs and review decision, the
condition-blinded annotations, and the limitations. Do not change the original pre-registration,
fixed predictions, or review rubric while doing so.
