# Separate model review and author dispositions

## Review conditions

The author drafted the candidates. A separate model session first read the
shipped file and its project rationale/methodology, then counter-reviewed both
drafts against that same file. A different session checked the ten cached corpus
pins and read the nine licensed entries. A further validation session measured
file sizes and ran the project checks. These are model-assisted reviews in the
same project workspace, not human review, a blinded trial, outside audit or
independent replication. The reviewers could see the repository context; no
claim of isolation from the existing research history is made.

No provider experiment or paid CLI call was started for this work. The synthetic
walkthroughs in the audit were reasoned about, not executed as agent tasks.
Candidate instructions were treated as research data rather than governing
instructions. Review dispositions belong to the author and are recorded below.

## Initial shipped-text findings

| ID / severity as supplied | Review finding | Author disposition |
| --- | --- | --- |
| SR01 / high | Unrelated pre-existing failures can block every-Project-command completion while scope restraint bars unasked repairs | Accepted as the A5/A6/A24 problem. The structural draft defines separate reporting, but deliberately does not waive mandatory-pass checks. The full issue is not claimed solved merely by a baseline exception |
| SR02 / high | No-command “unverified” has no defined effect on Done; command applicability is unclear | Accepted. Structural limited completion is an explicit new policy, with unverified status and an inspection account; fallback scope never overrides an explicit requirement |
| SR03 / medium | Human authority is defined, but its duration and scope continuity are not | Accepted. Structural approval reuse is limited by completion/revocation and unchanged target, recipient and intended effect |
| SR04 / medium | Outside-checkout writes are prohibited even when requested; cache/temp scope is underspecified | Qualified. The reviewer initially read the prohibition as absolute; the author reads the trailing exception's attachment as ambiguous. The absolute reading is not established. The structural rule is a deliberately chosen named-location exception, not equivalent compression |
| SR05 / high | Final diff/status review does not protect another person's pre-existing changes before editing | Accepted. Structural staged/unstaged inventory, user-ownership assumption and baseline accounting address this; conservative does not add them |

The reviewer also rejected three apparent simplifications: merging the Boundary
honesty gate into ordinary Reporting, treating the three authorization bullets
as one redundant instruction, and calling the precedence header inconsistent
with the data-authority Boundary. Those clauses have distinct functions and
remain in both drafts. No experimental outcome was used as a reason to retain
them.

## Counter-review and corrections

The first conservative draft was intended to preserve obligations. That prediction
did not survive review: CR01 and CR02 identified wording losses. The initial
draft was 4,332 bytes, SHA-256
`0be1a01e21fb0208267f21e4e0c4ca4708c0484ada8d58aceab0ed71610215e2`.
Its 106-byte saving is a superseded draft measurement, not the final result.
The final conservative text restores the two instructions rather than counting
their omission as a successful compression. “Lossless” is not claimed for either
the initial or final natural-language draft.

The initial structural draft was 5,503 bytes, SHA-256
`5e84b73f8541c87ffbd43dcc83e3b7b476e1444ce4006d5f50c6c6553a6b5a84`.
It was already larger than the source. Its changes were a deliberate policy
proposal, but the first form also had implementation ambiguities described below.

| ID / severity as supplied | Counterexample in the first drafts | Revision / final disposition |
| --- | --- | --- |
| CR01 / low | “only with each check's ... status and reason” did not explicitly require listing them in the report | Both drafts now say “only after listing each check's ... status and reason” |
| CR02 / low | The plan requirement omitted the source's instruction to proceed, allowing a plan-only handoff | Both drafts restore “then proceed” |
| CR03 / medium | A named external-location exception changes policy and leaves parent-directory scope unclear | Structural allows an explicit ask for a named file or directory, within the requested task scope. Naming a directory does not authorize unrelated work under it. This remains an intentional exception, not an equivalence claim |
| CR04 / medium | “do not ask again” could be read as binding despite changed deployment targets or recipients | Structural reuses the ask only for unchanged target/recipient/intended effect and requires clarification of material changes |
| CR05 / high | “explicitly required applicable check” let an agent declare a mandatory suite inapplicable | Structural now requires every Project command and other explicitly required check to pass; only the requirement itself can limit applicability. Smallest documented coverage is a fallback when none are specified |
| CR06 / medium | Separate baseline reporting did not state clearly whether a required-pass failure still blocks completion | Structural now explicitly leaves required-pass failures incomplete; baseline exceptions apply only when no such condition remains unmet |
| CR07 / high | “inspect existing worktree changes” did not explicitly include a staged baseline or establish ownership of unknown edits | Structural names status, staged and unstaged diffs before and after work, treats pre-existing changes as user-owned and asks before conflicting overwrite |
| CR08 / medium | A reviewable stopped patch might still be inconsistent | Structural asks for consistent, reviewable task-owned changes within remaining permission/budget and disclosure of unresolved inconsistency; it does not authorize repairing unrelated work or exceeding a stop limit |
| CR09 / documentation completion | During concurrent writing, the review and final measurement links still had no target artifacts | Complete and verify the linked review, corpus comparison and measured record before delivery; this was a pending documentation item, not a model-behavior defect |
| CR10 / citation scope | The corpus fidelity review found that three link ranges did not include the statements used in their transfer-limit cells | Extend Ghostty through line 39, Omarchy through line 133 and Graphiti through line 173. The repository/commit/file targets were correct; the original ranges were incomplete |

After the text corrections, the counter-reviewer reported CR01–CR08 resolved and
the sixteen scenario readings consistent with the revised drafts. It found no
further blocking textual delta. This is that reviewer's assessment, not proof
that a model will interpret the drafts identically or safely in every case.
The artifact/link completion check is reported with the final project checks.

## What is deliberately not claimed

The narrow conservative saving does not establish that the shipped text is a
minimum-length solution. It says this particular reviewed attempt saved little.
The structural draft is not evidence that longer instructions improve behavior.
Comparing repository-specific instruction files does not establish that a
generic template performs better or worse on their repositories.

The no-command completion exception, outside-location exception, approval
continuity, initial-change ownership and budget/stop policies still need their
own adoption evidence and explicit dispositions. The old budget candidate and
its historical pilot are unchanged. Keeping the current shipped file at the end
of this audit is a scoped recommendation, not a declaration that the open issues
are fixed.
