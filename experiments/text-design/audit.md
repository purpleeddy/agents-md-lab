# AGENTS.md text design audit

## Status and recommendation

This audit answers whether the instruction file itself can be clearer, shorter,
better bounded, or more complete. It does not extend the experiment harness.
[Issue 18](https://github.com/purpleeddy/agents-md-lab/issues/18) was opened before
the drafts were written. Both drafts are unadopted research artifacts, not
instructions for this checkout:

- [Conservative compression](conservative.md): editorial changes intended to
  preserve the existing obligations, exceptions and priority. Static review can
  challenge this intention; it cannot prove equivalent agent behavior.
- [Structural revision](structural.md): deliberate changes to check selection,
  completion states, approval scope, outside-checkout scope, existing changes,
  verification budgets and stopped work. It is not a lossless compression.

The recommendation is to retain the shipped file rather than replace it merely
for the conservative draft's small size saving. The structural draft is a design
comparison, not the next file to adopt wholesale: making more behavior explicit
costs substantial text. Its strongest changes are the explicit handling of
existing failures and protection of existing edits; they deserve separate
adoption decisions. No entire existing rule has earned deletion in this audit.
A shorter file is a smaller input, not evidence of lower total work cost or
better task outcomes.

The pinned source is [AGENTS.md at the merged baseline](https://github.com/purpleeddy/agents-md-lab/blob/94a6071b635962ebd40b27818bc8dfe312e3bcfc/AGENTS.md),
SHA-256 `2811faf02714c8426746c6d7a7df0d4931e44718f568a8f1df739df2e8a77aa5`.
All source line numbers below refer to that file. The [corpus comparison](corpus.md)
and [counter-review](review.md) are separate evidence for this recommendation.

## Measured size, not measured behavior

| Text | UTF-8 bytes | Whitespace words | LF-terminated lines | Byte change from shipped |
| --- | ---: | ---: | ---: | ---: |
| Shipped | 4,438 | 725 | 32 | — |
| Conservative | 4,355 | 702 | 32 | −83 (−1.87%) |
| Structural | 6,041 | 935 | 34 | +1,603 (+36.12%) |

The [measurement record](measurements.json) pins all three texts by SHA-256.
Bytes are `len(Path(path).read_bytes())`, words are
`len(Path(path).read_text(encoding="utf-8").split())`, and lines are LF byte
counts, including blank lines. Percentages use shipped bytes as denominator and
are rounded to two decimals. These are not tokenizer counts. The JSON is the
validator's captured output copied byte-for-byte (1,504 bytes; SHA-256
`a75bf4e3888ed46845d2b6623d695da1e9af353edbe7bb551fb8beaeef36c9bf`).

The conservative draft changes ten source lines to save 83 bytes. In particular,
it rewrites all five historically attributed lines, so its small saving does
not justify calling those lines' old measured effects preserved. The structural
draft makes more policy explicit, but its 36.12% size increase is a real input
cost and the reason it is not recommended as a wholesale replacement. Neither
percentage predicts total tokens, latency, spend or task performance.

## Grounds and findings

Changes originate in the numbered editorial findings below, the separate
reviewer's SR findings in the counter-review, or the already published
[review findings](../../docs/rationale.md#known-issues-the-review-found-in-the-file).
Pilot results did not generate a rule or decide whether to retain one. No
criterion was run against the drafts or used to choose their wording.

| Finding | Evidence and disposition |
| --- | --- |
| ED01 — compress expression, not obligations | Lines 6, 7, 10, 13, 14, 18, 21, 22, 23 and 26 contain restated subjects, long connective phrases or passive forms. The conservative draft substitutes shorter sentences while retaining the individual requirements. This is an editorial hypothesis, not a claim of behavioral equivalence. |
| ED02 — apparent duplication carries different authority | Line 6 makes honest completion a Boundary; line 26 specifies the final report. Moving all reporting obligations out of Boundaries would let nearer ordinary docs override the safeguard. Keep both roles. Likewise lines 7, 9 and 10 respectively identify gated actions, denial handling and who can authorize. This concurs with the independent review's nonfindings and A11/B20, A2/B6/B7. |
| ED03 — broad reporting and privacy rules have unresolved costs | Line 26 asks for every ignored instruction found in data; line 8 absolutely prohibits transmitting personal data and asks for a path only. An irrelevant embedded instruction can bloat a report; even a path can identify a person. Do not silently add a “material only” qualifier or a personal-data exception in a compression draft. Both candidates retain these rules; a later policy change needs its own cases and review. |
| ED04 — the generic template cannot supply project knowledge | Lines 30–32 intentionally have no actual commands, setup steps or project-specific invariants. Keep an editable Project entrypoint and deeper-document pointers. Do not populate it with commands from another repository or move a full repository map into the universal rules. Adopters still must supply their own valid information. A17/A18/A22/B23 remains partially open. |
| SR01 / SR02 — check scope and completion need explicit states | Line 21 requires all Project commands to pass even when a baseline failure is unrelated, and does not define whether no-command “unverified” can count as Done. The structural draft preserves mandatory Project checks, permits applicability only when the requirement states it, and defines a baseline exception for non-required-pass checks plus limited completion when no documented commands exist. It intentionally does not make a mandatory full-suite failure cease to block Done. Grounds: A5/A6/A24 and the separate review. |
| SR03 — approval has a source but no stated lifetime | Lines 7, 9 and 10 do not spell out when an existing ask expires or whether a repeated ask is necessary. The structural draft bounds it to its stated scope until completion or revocation, without authorizing a separate external action. This is a new explicit policy, not a claim the original demands repeated permission. |
| SR04 — the external-write exception is syntactically ambiguous | In line 9, “without an explicit ask” may attach just to instruction/settings changes or also to outside-checkout writes. The structural draft explicitly permits only a human-named external location, apart from task-needed caches and temporary files. This can widen one reading and narrow another; it is intentionally excluded from compression. |
| SR05 — existing edits need an ownership boundary | Line 23 inventories the final tree without requiring an initial inventory; “no unrelated changes” can misdescribe someone else's baseline edits as the agent's defect. The structural draft inspects and preserves existing work, asks before overwriting it, and checks what this task introduced at the end. |
| B21 / B24 — bounded verification and a stopped state | Existing line 18 stops repeated failures or no progress, but does not address repeated passing checks, observable human budgets, surviving task processes or the remaining-work handoff. The structural draft addresses these published findings without inventing a budget. It retains the failure/no-progress rule. This is not inferred from the pilot's costs or unknowns. |

Two problems in the surrounding explanation also need to remain visible. The
[rationale](../../docs/rationale.md#known-issues-the-review-found-in-the-file)
says two rows remain open, but its A17/A18/A22/B23 response also explicitly leaves
part of the template design open. Also, the historical line audit and
[methodology subtraction passage](../../docs/methodology.md#how-the-file-evolves)
use absence of measured effect as deletion language, while the rationale's final
principle and the human's task prohibit results as grounds for writing, keeping
or dropping rules. This audit follows that prohibition. Those historical passages
are not silently rewritten or used as an exception; the discrepancies are flagged
here rather than expanding this change into a method rewrite.

## Rule-by-rule contract and changes

Each row states the trigger, obligation and exception in the shipped text. Unless
marked **Boundary**, nearer project docs can override an ordinary rule; they
cannot loosen Boundaries or supply a human ask. **C** and **S** identify the two
drafts. The full texts supply the exact before/after wording, and the final
measurement record identifies their bytes.

| ID / source line | Trigger → obligation; exception / priority | C: disposition | S: disposition and ground |
| --- | --- | --- | --- |
| H / 3 | Nearer project docs → override ordinary rules; except Boundaries | Exact | Exact |
| B1 / 6 | A completion or existence claim → observed evidence and check status/reason; no gaming unless the human explicitly asks, then disclose; **Boundary** | Editorial compression, ED01; all gaming examples and exceptions retained | Same as C |
| B2 / 7 | Destructive, externally visible or dependency action → explicit ask; public API example applies where Project marks a contract; **Boundary** | Editorial compression, ED01; open examples and every action class retained | Same as C |
| B3 / 8 | Handling secrets/personal data or sending repository/environment data → nondisclosure, no credential-store reads, limited destinations; explicit-action exception applies to the destination clause; **Boundary** | Exact, ED03 | Exact; no new disclosure exception |
| B4 / 9 | External writes or instruction/settings changes → restrictions; caches/temp exception, harness permission is not an ask, denial/missing ask stops only that action even unattended; **Boundary** | Exact, preserving ambiguous modifier scope | Explicit external-location exception and task-needed temporary scope, SR04; denial and settings safeguards retained |
| B5 / 10 | Claimed authorization → only the conversation's human can grant it; embedded data and project docs cannot; **Boundary** | Editorial compression, ED01; human prompt distinguished from embedded content | C plus bounded authorization lifetime, SR03 |
| P1 / 13 | Before editing → read changed files/direct callers, find helper; signature change → inventory every call site/read changed ones; over 3 files or public interface → plan files and verification first | Editorial compression, ED01; no threshold or caller-set reduction | C plus pre-edit inventory/preservation, SR05 |
| P2 / 14 | Multiple reasonable readings and consequential wrong guess → one targeted question; otherwise state an assumption/proceed; unattended assumptions only for reversible internal changes | Editorial compression, ED01; all branches retained | Same as C |
| W1 / 17 | Implementation choice → smallest correct complete change, no unrelated edits/speculative abstractions, existing dependencies first | Exact | Exact |
| W2 / 18 | Same command/error twice with no change, or three no-progress attempts → stop/report | Editorial compression, ED01; both stopping conditions retained | Same as C; separate budget/repeat/process rule added from B21/B24 |
| D0 / 20 | Claiming Done → all following conditions hold | Exact | Exact heading; D1/D3 intentionally change its conditions |
| D1 / 21 | Verification → every Project command passes; absent Project commands use named sources only; absent commands report unverified rather than guess | Editorial compression, ED01; unresolved completion effect retained | Mandatory Project/explicit checks, applicability only where documented, bounded fallback; baseline exception and explicit no-command completion effect, SR01/SR02 and A5/A6/A24 |
| D2 / 22 | Bug fix → reproduced before/passes after; feature → behavior test; no suite/unreproducible test → explain why and how verified | Editorial compression, ED01; feature test and both exceptions retained | Same as C |
| D3 / 23 | Final review → diff and status, no unrelated changes/debug output/untracked leftovers | Active-voice compression, ED01; both commands retained | Attribute baseline vs introduced changes, SR05 |
| R1 / 26 | Final report → changes, checks/results, deletion/external/unverified/ignored-instruction inventory; small task permits one line, not omitted evidence | Editorial compression, ED01/ED02; full inventory retained | Same as C plus explicit stopped-work handoff, B24 |
| R2 / 27 | Uncertainty or infeasible request → state gaps and evidence-based pushback | Exact | Exact |
| T1 / 30 | Adopter setup → fill stack/package manager placeholder | Exact, ED04 | Exact |
| T2 / 31 | Adopter verification → fill command placeholders | Exact, ED04 | Exact; catalog still needs applicability information in project docs |
| T3 / 32 | Adopter constraints → fill generated-file/API-contract fields and detail pointers | Exact, ED04 | Exact; no inferred authorization from a template |

No rewrite of a historically attributed line inherits that line's old experimental
evidence automatically. The conservative draft changes all five such source
lines (6, 13, 21, 22 and 26). The drafts are whole new texts, even when a reviewer
finds their obligations similar. Unchanged clauses were retained for their
documented purpose, not because a metric moved or did not move.

## Matched scenario walkthrough

These are explicit synthetic situations and static readings by the author,
challenged by a separate model reviewer. No agent executed these tasks under the
three files. The cells describe prescribed or ambiguous behavior, not observed
compliance, success rates or simulator pass counts. No adoption threshold is
derived from this table.

| Situation held constant | Shipped file | Conservative draft | Structural draft |
| --- | --- | --- | --- |
| S01: prose-only edit; Project catalogs unit and integration commands without applicability conditions | Every Project command must pass | Same | Same; the agent cannot invent an applicability exception. Project must explicitly define a narrower condition |
| S02: unrelated suite failure recorded before a requested fix; the failed check comes from fallback docs, not Project or an explicit pass requirement | No Done route for this case is specified | Same | Baseline-proven unrelated failure is separately disclosed; no unasked repair; no new/uncertain failures allowed |
| S03: no documented verification commands and no explicit required check | Report unverified; completion effect ambiguous | Same ambiguity | Limited completion permitted with unverified status and inspection account; no invented check |
| S04: bug cannot be reproduced in a test | Explain why and how the fix was verified; other Done conditions still apply | Same | Same; an unrun explicitly required check still blocks completion |
| S05: public signature change spans five files and has other unchanged callers | Plan first; list every call site; read changed files/direct callers and call sites being edited | Same sets and threshold | Same, plus inspect existing edits |
| S06: re-run an already passing check without changed relevant input or new evidence | Failure-loop rule does not bound this passing repeat | Same | Requires a concrete reason; not an automatic ban on useful repetition |
| S07: human already asked to publish this work; scope unchanged and unfinished | Human ask is valid authority; duration is unspecified, repeated asking is not mandated | Same | Reuse the ask for unchanged target/recipient/effect until complete/revoked; clarify material changes and require authority for separate external actions |
| S08: a repository file or quoted issue directs secret upload or grants itself permission | Cannot grant permission; credential/disclosure Boundary applies | Same | Same; persistence clause does not turn data into authority |
| S09: tool denies an authorized action; an alternate route exists | Stop that action, no detour; continue independent work and report | Same | Same, even if prior approval remains in scope |
| S10: requested file already contains another person's staged or unstaged edit | Final diff/status required; no explicit initial ownership check | Same | Inspect status and staged/unstaged diffs first, preserve existing edits, ask before conflicting overwrite; distinguish task-introduced changes |
| S11: human explicitly names a sibling directory as output destination | Scope of trailing “without an explicit ask” is ambiguous | Same ambiguity, not silently relaxed | Named location allowed; unnamed external writes still blocked apart from task-needed cache/temp exception |
| S12: stated observable execution budget is about to be exceeded and task-owned process remains | Failure/no-progress stop rule only; report inventory does not specify remaining-work handoff | Same | Stop before limit, do not leave unasked task processes, leave consistent/reviewable partial work within remaining permission/budget, disclose inconsistencies and remaining work |
| S13: README lists a check that reads a credential store or performs an unasked destructive action | Boundaries overrides the command rule; stop that action and disclose missing verification | Same | Same; required/applicable does not grant permission |
| S14: human explicitly requires the suite to pass, but a baseline failure predates the task | Not complete | Same | Still not complete; baseline exception cannot waive the explicit pass requirement |
| S15: relevant code changes after a previous passing test | Required verification still applies | Same | Repeat is permitted; scope and required-check rules still decide what must run |
| S16: two identical failures without changes, or three attempts with no new information | Stop and report | Same | Same, with explicit stopped-work handoff |

## Adoption limits

For a subsequent text proposal, prioritize SR05 (initial ownership and final
attribution of existing changes) before bundling the rest of the structural
draft. Next consider SR01/SR02 as a completion-policy decision, including the
cost of preserving mandatory checks. Defer approval-lifetime and external-path
exceptions to their own authorization cases. Retain the published B21/B24
proposal as a separate behavioral change; do not merge it merely to make this
audit's structural draft comprehensive. This order comes from the review's
concrete failure modes and change scope, not pilot outcomes.

The structural changes affect behavior and do not qualify as lossless edits.
New budget/scope behavior cannot be adopted from these walkthroughs or from the
old pilot. A later adoption proposal must follow the published methodology:
observable tasks where needed, a new test-set version and lock for a new adoption
round, contemporaneous comparison cells, a fixed acceptance rule and a revert
set. This PR neither schedules nor pays for that work. For conservative text
review, static agreement is necessary editorial evidence, not a substitute for
the project's acceptance requirements or a license to call the draft measured.

The shipped file, earlier pilot candidate, criteria, scorers, generated blocks,
historical results and pre-registration prefix remain unchanged. The current
research recommendation is therefore a reviewed candidate and named unresolved
decisions, not a new release.

## Verification of this delivery

| Command / check | Observed result |
| --- | --- |
| `python3 -m unittest` | Passed 367 tests in 18.170 seconds |
| `python3 scripts/compare.py --check` | Passed: 10 files, 10 rule criteria, 8 content criteria; generated output matches data |
| `python3 scripts/experiment.py --dry-run` | Passed all 12 stored fixtures |
| Measurement-copy and value audit | Captured JSON copied exactly; all three hashes, sizes, words and LF counts match the actual files |
| Source and historical-artifact audit | Baseline tracked files unchanged except the README append; pre-Lock prefix and historical publication unchanged; retained archive still 772 files with tree hash `b4e9c53e1c625adb12b8aa805520f58018fffe510614276941072e75fb6567da` |
| Document audit | All 16 scenario IDs and 18 rule rows plus the Done heading present; local links resolve; corpus blob links remain commit-pinned; no unlicensed phrase hits |

The initial path-count audit used `git status --porcelain=v1`, whose default
output collapsed the untracked research directory. Its derived
`status_exactly_seven` result was `False`. Repeating the inventory with
`git status --porcelain=v1 -uall` enumerated exactly the seven planned paths.
This corrects an audit-method false negative, not a missing-file defect. The
review records the separate text and citation corrections as well.

No production code, test logic, dependency, hook, permission setting or generated
block changed, and no existing file was deleted. New executable behavior was
not introduced, so no implementation test suite was added; the scenario table
and separate counter-review are the explicit semantic review, with behavior
unverified. Project tests check the repository artifacts, not compliance with
the candidate prose. Build, lint, typecheck and format commands are not defined
by CONTRIBUTING and were not invented. External effects are the proposal issue,
task branch and PR; no merge or paid experiment is part of delivery.
