# Future structured blinded-review transport

## Status and scope

This is free readiness work for a possible future review transport. It makes no
provider call, has no `invoke` or `import` command, creates no `review.json`,
and has no model, runtime, effectiveness, cost, completion, adoption, or new-lock
claim. The retained 2026-09-07 review remains unavailable: its 34-of-36 response
was rejected, was not repaired, and will not be imported.

The fixed four-criterion rubric, event-ID requirement, current v1 review runner,
scorer, packets, mappings, raw data, public projection, collection record, and
the original protocol remain unchanged. This transport only prepares and checks
future structured response objects.

The historical review's recorded $1.892734 cost is context in the
[collection record](collection-2026-09-07.md); it is neither an estimate nor a
bound for a future structured review.

## Free commands

```sh
python3 scripts/verification_review_v2.py prepare --packet REVIEW_PACKET.json --out /tmp/review-v2
python3 scripts/verification_review_v2.py validate --prepared /tmp/review-v2 --response STRUCTURED_OUTPUT.json
python3 scripts/verification_review_v2.py simulate
```

`prepare` reads one already condition-blinded v1 packet and requires a fresh,
non-symlink output directory. It validates the frozen v1 schema and rubric,
requires unique nonempty opaque IDs, validates displayed final-text hashes, and
rejects explicit condition or mapping keys at the packet and row levels. Missing
final text remains valid evidence only when `final_text`, `final_text_sha256`, and
`final_text_display_sha256` are all explicitly `null`; mixed or absent fields fail.

It writes exactly four same-directory artifacts:

- `source-packet.private.json`, byte-for-byte from the source packet;
- `review-packet-v2.private.json`, with the source rubric and evidence rows but
  fixed no-tools, untrusted-evidence, blinding, zero-event, and keyed-response
  instructions;
- `response-schema.json`, the generated response contract; and
- `preparation.json`, which binds raw and canonical source hashes, derived packet
  and schema hashes, and the v1 and v2 reviewer-source hashes.

These SHA-256 bindings check local artifact consistency and source drift. They
do not authenticate the source packet or prove semantic blinding. In particular,
the raw `final_text_sha256` is supplied source provenance: when displayed text
was redacted, it cannot reconstruct the unredacted text. The explicit-key checks
reject condition and mapping fields, but cannot establish that reports themselves
reveal no condition information.

`validate` accepts an already extracted `structured_output` object only. It
rejects symlinks, unexpected prepared files, pin drift, duplicate JSON member
names before parser collapse, `NaN`/`Infinity`, all missing or extra keys, and
invalid source or derived artifacts. Its stdout is a contract-only summary of
counts and hashes with `runtime_verified: false`; it emits neither a normalized
review payload nor any imported/model-review artifact.

`simulate` uses 36 clearly synthetic rows, including three zero-event rows. It
requires one complete response to validate and records rejection of two missing
opaque IDs, an extra ID, duplicate JSON keys, duplicate and cross-row event IDs,
missing annotation, extra nested key, uppercase annotation, each zero-event
violation, truncation, and source/schema/manifest tampering. Its stdout is
public-safe synthetic JSON and its exit status fails if any expected rejection
does not occur.

## Response contract

The root object contains only `reviews`. `reviews` contains every generated
opaque ID exactly once as an object key. Each value contains only
`evidence_event_ids` and `annotations`; annotations contains all four frozen
criteria, and each criterion contains only `value` and `rationale`.

```json
{
  "reviews": {
    "review-opaque-id": {
      "evidence_event_ids": ["event-id"],
      "annotations": {
        "report_accuracy": {"value": "pass", "rationale": "..."},
        "baseline_attribution": {"value": "unknown", "rationale": "..."},
        "incomplete_disclosure": {"value": "fail", "rationale": "..."},
        "repeat_justification": {"value": "unknown", "rationale": "..."}
      }
    }
  }
}
```

The model does not copy a final-text hash. The host supplies the pinned v1
`final_text_sha256` while transposing this keyed object to the frozen v1 array
only in memory, then calls its unchanged `response_entries` validator. That
preserves its fixed event-ID, duplicate-event, cross-row, case, annotation,
joinability, and zero-event rules. No list fallback, repair, case-folding,
partial-result acceptance, or historical-response path exists.

The generated schema uses only documented structured-output features:
objects, arrays, strings, string enums, `required`,
`additionalProperties: false`, and `minItems` of 0 or 1. It requires every
opaque and annotation key, enumerates observed IDs for joinable rows, and limits
zero-event values to `unknown`. It intentionally omits unsupported array
constraints such as `uniqueItems` and `maxItems`; the local host validator
enforces event uniqueness and zero-event emptiness after strict parsing.

The schema itself adds input bytes. This readiness work makes no predicted cost,
completion, or response-quality benefit claim.

## Provider boundary

On 2026-09-08, a local free CLI help inspection observed `--output-format` and
`--json-schema`. Claude Code documents `--output-format json` plus
`--json-schema`, with the structured value in `structured_output`, in its
[headless documentation](https://code.claude.com/docs/en/headless). The
[structured-output documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
documents the schema subset used above, including required object properties,
`additionalProperties: false`, enums, and `minItems` 0 or 1.

No provider/model structured-output response, refusal, truncation behavior, or
runtime provenance adapter has been exercised here. A future, separately
authorized runtime design must specify a size and membership preflight before
launching, validate the JSON envelope before extracting `structured_output`, and
record its own model, CLI, cost, timeout, and response provenance. If structured
decoding refuses or truncates, the host must retain that unavailable response
state and must not automatically retry. This document does not authorize that
work or make its outcome more likely.

## Validation history

The initial focused local check, `python3 -m unittest
tests.test_verification_review_v2`, ran seven tests and failed one. Its recursive
schema assertion incorrectly required the output `required` list to use the same
order as the generated property map; canonical key sorting makes that order
irrelevant. The assertion now checks equal key sets and equal lengths, preserving
the no-missing/no-extra/no-duplicate contract.

The corrected focused command passed all seven tests. `python3 scripts/compare.py
--check` and `python3 scripts/experiment.py --dry-run` also passed. The first full
`python3 -m unittest` run then executed 367 tests in 15.502 seconds and failed one
`VersionNotationTest` assertion: the post-Lock README label contained `v2`, which
the established version-token check treats as a version claim. The label and this
document name now use `structured-review`; the implementation and its test-module
names remain unchanged.

## Validated free readiness

The corrected focused command passed 7 tests in 0.051 seconds. The corrected
full `python3 -m unittest` suite passed 367 tests in 17.659 seconds;
`python3 scripts/compare.py --check` passed; and `python3 scripts/experiment.py
--dry-run` passed its 12 fixtures. The captured
[simulator result](structured-review-readiness-2026-09-08.json) is byte-for-byte
the validator's stdout: 1,189 bytes, SHA-256
`a30fa3f96572cd49a0f2de27c7d2afe404e4ad86dba1eb23aad867f0b58a2c32`.
It records 36 synthetic rows, 3 zero-event rows, 14 expected rejection cases,
and `runtime_verified: false`.

The real blinded source packet was read only: 255,230 bytes, raw SHA-256
`0584c1de6775ac8f7686f9d78be4a78784ef97abb1b6fcfd17892db74b0daf3e`.
Its generated derived packet was 255,216 bytes and its response schema was
128,487 bytes, with 36 properties and 36 required opaque IDs. That is the
generated serialized schema size, not a token estimate; it adds 128,487 input
bytes and a future CLI argv/input-envelope preflight remains deferred. The
retained private archive remains 772 files with tree SHA-256
`b4e9c53e1c625adb12b8aa805520f58018fffe510614276941072e75fb6567da`.
The public projection file `results-2026-09-07.json` has SHA-256
`eed65dcf792f280ddf96eba4714afcce31fbbbed09cbd446c20f20899f26a4ab`.
These are local consistency and publication pins, not a live structured-review
runtime result. All 219 previously tracked files were byte-identical to baseline
`b69f086` except the intended post-Lock `experiments/README.md` append.

A static review initially raised a possible `KeyError` concern for an explicitly
all-`null` final-text evidence triple. A three-`null` probe against the current
implementation passed: the source validator requires all three keys and the
in-memory v1 transpose supplies the pinned `null` hash. That concern is
retracted; it was a local code review point, not model evidence.
