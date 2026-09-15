# Comparison with the pinned instruction-file designs

This is a static design comparison against the ten entries already selected in
[corpus.toml](../../corpus.toml), not a fresh survey of current repository heads.
The sample excludes files over 200 lines; it cannot establish superiority over
longer or differently organized designs outside that selection.
A separate model session inspected the licensed cached files. Before reading,
it verified that each cache had exactly one matching filename and that all ten
matched the SHA-256, byte count and newline count published in
[comparison.json](../../docs/data/comparison.json). No refresh or re-scoring ran.
The unlicensed entry received only a derived-fact check, not a qualitative text
review. This limits any claim about the full corpus's design coverage.

Each source link below is pinned to the manifest commit. Line intervals identify
where the observation was made; none is a claim about a repository's current
instructions. The role labels are this review's interpretations, not measured
categories or the published regex verdicts.

| Entry / pinned evidence | Design contribution | Transfer limit for a generic AGENTS.md |
| --- | --- | --- |
| [Format sample, lines 8–22](https://github.com/openai/agents.md/blob/ba9474a69e9a2c0c4176713843b78e8f54377941/AGENTS.md#L8-L22) | Repository operations: explains the development/production command distinction and lockfile maintenance with dependency changes | Useful operational specificity depends on its Next.js workflow; do not invent equivalent commands for every adopter |
| [Claude Code Action, lines 3–20 and 30–37](https://github.com/anthropics/claude-code-action/blob/7057f3318b938a2dd095fd89f786c11772b08197/CLAUDE.md#L3-L37) | Repository operations: combines check commands with architecture, public-API and lifecycle landmarks | Bun, authentication and action cleanup are local concerns; commands and invariants belong in the adopter's Project docs |
| [Sentry, lines 42–58, 94–103 and 127–129](https://github.com/getsentry/sentry/blob/7395d32708261ef723e33be460da1641c36a9e0e/AGENTS.md#L42-L129) | Repository operations: completion checks and targeted verification, with path-based routing to nearer instructions and skills | Environment setup, permission modes and customer-data policy are not universal defaults |
| [Ghostty, lines 7–39](https://github.com/ghostty-org/ghostty/blob/9897d6caba05c0cbf256f86bec2e2935f164a9c7/AGENTS.md#L7-L39) | Repository operations: focused-test alternatives and subsystem-specific commands/invariants | A short file can be useful because it knows this codebase; its contribution policy at lines 34–39 is not a general agent behavior rule |
| [Temporal, lines 5–13, 49–66 and 83–92](https://github.com/temporalio/temporal/blob/109a38e8ca4827ae8c624fc1a9382290dcae0f69/AGENTS.md#L5-L92) | Mixed workflow and operations: check conventions/dependencies first, then implement, regenerate and verify | Go tags and prescribed planning/response detail depend on the task and repository; copying them would increase universal overhead |
| [HumanLayer, lines 39–60 and 74–88](https://github.com/humanlayer/humanlayer/blob/6014ccf95edf71b2d0ba31bcd65a9297a3decb65/CLAUDE.md#L39-L88) | Repository operations: an authoritative verification entrypoint plus package-local manifests and shared conventions | Monorepo component descriptions and workflow triggers belong in local guidance |
| [Omarchy, lines 3–20, 34–59 and 105–133](https://github.com/omacom/omarchy/blob/1c8f728b25cb8a42f1d02e4d2441230132cedb6c/AGENTS.md#L3-L133) | Mixed workflow and operations: route task types to deeper guides and use an authoritative command registry | Platform paths, shell style, privileged commands and configuration-copy behavior are not safe universal assumptions |
| [Superpowers, lines 11–20, 48–70 and 93–115](https://github.com/obra/superpowers/blob/1d4c8d2aafb8fa0de3e5d7df80ff44899fa7e402/CLAUDE.md#L11-L115) | Contribution/workflow emphasis: concrete problem statements, full-diff human review, and before/after evidence for behavior-shaping changes | Its review thresholds, disclosure requirements and contribution governance remain that project's policy |
| [Graphiti, lines 17–36, 65–93 and 112–173](https://github.com/getzep/graphiti/blob/375023b9e8db9957a48b2b6f3cb30d505a5ab39b/CLAUDE.md#L17-L173) | Repository operations: commands by subproject, unit/integration distinctions and architecture landmarks | Provider configuration, database setup and a model catalogue cannot be copied into a stable generic core |
| [Unlicensed entry](https://github.com/multica-ai/andrej-karpathy-skills/blob/8462496b34419f20b32778610571ac723e91f94c/CLAUDE.md) | Derived facts only: 65 newline-terminated lines; 2,357 bytes; SHA-256 `694a2d721e41c385f3db492838c23299826df5ba9809e3b0721aac70021e196a`; existing rule/content verdict counts 5/10 and 0/8; published evidence line numbers 19, 34, 35 and 52 | No quotations, paraphrases, qualitative role classification or content-derived design advice in this review |

## What this comparison supports

The shipped file is a portable behavior and authorization core. Most licensed
comparators above are filled-in operational documents. The shipped file is less
ready to operate a particular repository until its Project fields or linked docs
are filled; that is a real limitation, not evidence that it should embed another
repository's setup or directory map. Conversely, copying a short repository file
would not automatically preserve this file's explicit authorization and
completion-reporting contract. The different purposes prevent an overall
better-than claim from this comparison.

Useful design transfers are conditional verification guidance and one maintained
entrypoint for commands and deeper context. These support revisiting the known
applicability/template issues, alongside A5/A6/A24 and A17/A18/A22/B23. They do not
authorize waiving explicit required checks. The final structural draft therefore
retains mandatory Project commands; an adopter has to document their conditions,
rather than letting the agent invent them.

Keep project-specific setup, style, subsystem maps, contribution workflow and
network destinations in the adopter's documents. Keep the small generic Project
template as their entrypoint. Do not add a universal style guide, model catalogue,
multi-agent topology, approval-free delivery rule or fixed execution budget just
because a comparator includes specialized guidance. Those would introduce new
policy and maintenance costs without answering this audit's identified defects.

The existing regex tallies describe what the patterns found. They neither show
that a missing pattern means a missing concept nor measure whether a rule helps
an agent. No candidate wording, deletion or recommendation in this audit was
selected to increase those tallies.
