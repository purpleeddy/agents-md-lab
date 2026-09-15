# Installed runtime preflight audit

## Decision

Do not lock or launch the proposed comparison from the offline readiness
captures. The local evidence pipeline is validated, but installed CLI help
and synthetic schema sizing do not prove option behavior, provider schema
support or actual agent integration. This audit narrows those remaining
claims without changing an instruction text or historical instrument.

## Observed local facts

The [captured audit](runtime-preflight.json) records command exit codes, byte
counts and output hashes rather than redistributing the full CLI help text.

| Item | Observed value |
| --- | --- |
| Installed CLI version output | `2.1.263 (Claude Code)` |
| Plain version/help calls | exit 0, no stderr |
| Existing runner's turn-limit option in help | `--max-turns` not listed |
| Listed integration options | `--max-budget-usd`, `--output-format`, `--json-schema`, `--mcp-config`, `--strict-mcp-config`, `--setting-sources`, `--no-session-persistence` |
| Largest pretty serialized synthetic response schema | 167,411 bytes |
| Largest compact serialization of the same schema objects | 64,893 bytes |
| Historical review helper's conservative argv budget | 100,000 bytes |

Compact schema bytes alone fit below that historical threshold. The threshold
is not a provider context limit or a measured operating-system argument limit;
it also does not account for all other arguments. No reviewed file or stored
schema was compacted or overwritten by this arithmetic check. Real reports,
provider schema features and input/output token limits remain unverified.

## Help is not an option-behavior test

These free probes all exited 0 without stderr:

```sh
claude --version
claude --help
claude --max-turns 1 --help
claude --definitely-invalid-focused-preflight --help
```

The last option name was deliberately invented as a negative control. Its
successful help invocation demonstrates why help exit status cannot establish
that the turn-limit option is recognized or effective. Conversely, absence
from help does not establish that an option was removed. Both runtime claims
remain unverified; there is no inferred pass, inferred removal or flag change.

The existing `claude_command` helper in `scripts/experiment.py` still emits
`--max-turns` and writes an isolated task settings file. It was inspected, not
invoked by this audit. No settings, permission mode or instruction-discovery
behavior was changed. Listed MCP options provide a possible integration route,
not evidence that a new connector has been implemented or works with a model.

## Reproducing schema sizing

After adding `scripts` to Python's import path, use the unchanged
`focused_reports.synthetic_packet()` and split its rows into forty-row batches.
For each `focused_reports.response_schema(batch)`, count UTF-8 bytes for
`verification_review_v2.json_bytes(schema) + b"\n"` and for
`json.dumps(schema, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.
The capture records every batch size and the three report/helper source pins.
This measures serialization of identical schema objects, not model tokens.

## Remaining execution contract

Before a new lock, the real connection must establish actual request/result
identity and complete owned-process lifecycle, preserve initial/final state,
retain reports and costs, and expose the same interface to all four arms.
The legacy metric adapter and condition-neutral report projection are still
missing. A real packet preflight must check both schema compatibility and
complete input/output size. An operational turn/timeout/budget limit needs
behavioral evidence rather than a help-only green check.

No paid connection probe or review is authorized by this audit. The historical
collection analogies in the [draft protocol](protocol.md#historical-cost-estimate-and-stop-conditions)
remain the cost basis: $71.88–$257.53 for 440 work rows under different recorded
mean/maximum assumptions, not a forecast or ceiling. Review cost is separate
and unestimated. Any eventual proposal must name its concrete invocation,
allowance, locked artifacts and stop/revert rule before requesting a paid run.

This is a read-only runtime audit plus arithmetic record, not a code feature.
No test failure or failed behavioral prediction was hidden: the negative
control is retained specifically because an exit-0 help check is insufficient.
