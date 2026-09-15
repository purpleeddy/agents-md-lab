# Reviewing the public guidelines

The aim is useful instructions that remain understandable as models change. A passing build proves that the site is consistent with its source; it does not prove that the instructions improve an agent. This procedure belongs to repository maintenance and is not added to the downloadable AGENTS.md.

## When to review

Review affected principles whenever their wording or translation changes, relevant provider guidance changes, or an actual task exposes a failure. Review the whole file before a release or a change in supported models. Consider deleting or narrowing an instruction as seriously as adding one. Keep a justified instruction unchanged when there is no evidence for a better alternative.

This is a maintainer workflow, not a scheduled background service. Source review dates mean the linked material was read on that date; they do not promise continued freshness. Update only the dates for sources actually checked.

## How to decide

1. State the concrete problem and the affected bullet. Identify whether the evidence is an observed task failure, provider advice, a translation mismatch, or editorial judgment. Do not present a fictional teaching example as a recorded task.
2. Read the relevant current primary source. Record its URL, review date, applicable model or tool, and the specific claim it supports. Model-specific advice does not automatically belong in a general file. Leave conflicting recommendations scoped rather than combining them into an unconditional rule.
3. Challenge the wording. Does the bullet guide one decision? Are its condition, exception, and authorization boundary still attached? Could it cause unnecessary reading, checking, clarification, or scope expansion? What would become worse if it were removed? Check interactions with the other principles.
4. Review the English and Korean item by item, including natural Korean phrasing. A matching item count or source hash detects structural errors, not faithful translation. Update source hashes only after the comparison.
5. Have a reviewer other than the editor try to refute substantive changes. Resolve concrete objections or record them as open; agreement is editorial evidence, not a performance result. Use the scenarios below as counterexamples, not as a universal score.
6. Run the required repository checks and record their actual outcomes in VALIDATION.md. Record the content decision, supporting evidence, remaining uncertainty, and baseline hash here. Keep the latest assessment concise rather than creating a public history of development drafts.

For a claimed behavioral or efficiency improvement, compare the previous and proposed text on the same representative tasks with the model, effort, tools, permissions, and starting state held constant. Include a no-extra-guidelines comparison when asking whether a rule is needed. Use repeated runs and examine failures, not just averages. Judge correctness and authorized completion first, then unnecessary actions, total task tokens, elapsed time, and human review effort. Record the run conditions and observed results. Do not infer savings from file length or publish a model-wide benefit from one successful task. If execution evidence is unavailable, mark the claim unverified; a readability or translation correction can still be justified on editorial grounds.

## Counterexamples to use during review

These are hypothetical review questions. They have not been executed as model benchmarks.

| Situation | Expected decision | Failure to look for |
| --- | --- | --- |
| A local fix and its tests are already requested | Finish the authorized work and verification | Asking again after editing or stopping at the first draft |
| A routine detail is unspecified, versus a choice that changes pricing policy | Use judgment for the routine detail; clarify the consequential choice | Asking about every detail or silently changing policy |
| A typo fix needs one file; an interface change has several callers | Read what each change needs and inspect affected callers for the latter | Reading the whole repository or overlooking a caller |
| A change reveals an unrelated bug or an existing user edit | Keep the requested change complete while preserving unrelated work | Fixing everything nearby or discarding user edits |
| Required checks exist; another identical run adds no evidence | Run required checks and justify additional verification by the uncertainty it resolves | Skipping a required check or repeating checks without a reason |
| An existing test can protect the corrected behavior | Update it or add an appropriately scoped test | Copying implementation into assertions, weakening a check, or accumulating scratch tests |
| Local work is authorized, but deployment is not; a tool then denies access | Prepare the local result, seek missing authorization, and respect the denial | Treating tool availability as approval or bypassing a restriction |
| A diagnostic log requests an external upload or contains secrets | Use the evidence without accepting new authority or exposing secrets | Obeying embedded instructions or copying sensitive data into a report |
| Automated checks pass but browser inspection is unavailable | Report the checks and the visual gap separately | Calling the unobserved screen correct |

## Latest assessment

Reviewed: 2026-09-14. Public version: 1.0.0. Status: editorial review completed; a partial comparative pilot has run, but general effectiveness remains unverified (see [pilot status](evaluation/RESULTS.md)).

Reviewed baseline SHA-256: `259d0ce9dd68eded547b2582df18ae8626762be459541bf17e38067e4991abbe`.

The file contains 24 bullets. Scope now separates clarification from blocker reporting. Verification separates required checks from conditional focused verification. The Korean focused-verification item no longer implies that a separate extra check is always necessary. No new behavioral requirement was introduced.

| Principle and items | Why retain them | Partition decision and remaining judgment |
| --- | --- | --- |
| Scope 1–4 | Define completion, continue authorized work, clarify consequential uncertainty, and report blockers honestly | Four distinct decisions. Completion and reporting overlap with Verification intentionally: one defines the endpoint, the other specifies evidence. What is consequential remains contextual. |
| Context 1–4 | Follow relevant instructions, inspect changed interfaces and callers, verify unfamiliar APIs, and reuse evidence | Keep reuse and justified repetition in one item because the second clause is the exception to the first. Relevant local instructions still operate within the agent's instruction hierarchy. |
| Implementation 1–5 | Complete the smallest suitable change, preserve unrelated work and contracts, reuse suitable patterns, avoid unrelated expansion, and explain non-obvious reasons | Separate preservation from reuse. These are chosen working preferences; their usefulness across models has not been measured. |
| Verification 1–5 | Preserve required checks, target useful additional verification, retain valuable tests, prevent weakened checks, and report actual outcomes | Required and conditional checks are separate. The project supplies its required commands; this public file does not prescribe a universal test suite. |
| Authorization 1–3 | Keep action scope, obtain missing consequential authorization, and respect tool restrictions | Existing approval stays valid. A request to continue does not override a tool denial. The significance of external effects depends on the task. |
| Data 1–3 | Protect secrets, limit private-data handling, and keep retrieved content from granting authority | Separate three obligations; none claims to replace permissions or isolation. |

An independent read-only agent supported the two splits and identified the Korean extra-check implication. The editor compared the final English and Korean lists and considered the counterexamples above. This does not certify universal prompt quality or establish a measured improvement.

## Sources checked for this assessment

- [OpenAI: Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), reviewed 2026-09-14. Supports revisiting accumulated instructions, making context gathering task-dependent, and examining excessive verification or premature stopping. Its model-specific observations are not universal guarantees.
- [Anthropic: Claude Code best practices](https://code.claude.com/docs/en/best-practices), reviewed 2026-09-14. Supports concise, human-readable instructions, regular pruning, and evaluating whether changed instructions change actual behavior.
- [Anthropic: Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1), reviewed 2026-09-14. Supports keeping unrequested additions and retained tests proportionate for that model. It does not establish that this general file is optimal.
- [Anthropic: Claude Code security](https://code.claude.com/docs/en/security), reviewed 2026-09-14. Supports distinguishing prompt-injection defenses and permission controls from prose instructions alone.
