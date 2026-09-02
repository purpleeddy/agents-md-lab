---
title: Check catalog
---

# Check catalog

Every check is a deterministic function in `scripts/lint.py`, cites a source in [references.md](references.md), and carries an evidence grade: `G` (guidance or literature only), `E+` (supported by an experiment in this repository), `E-` (not supported). All checks are grade `G` until the v1.1 experiments run. Patterns are listed in [design.md](design.md#53-patterns).

To add a check: one function with the `@check` decorator, one passing and one failing fixture in `tests/test_checks.py`, and one row here. `make test` fails if a check has no source key or no row.

## Scored checks

| id | rule | applies to | threshold or pattern | source | grade |
|---|---|---|---|---|---|
| `len-lines` | At most 200 lines | all | lines ≤ 200 | [^anthropic-memory] [^humanlayer] | G |
| `len-bytes` | Under the Codex default cap | all | bytes ≤ 32768 (`project_doc_max_bytes`) | [^openai-agents-md] | G |
| `cmd-test` | A test command is given verbatim | project | code span matches a test-runner pattern | [^agents-md-spec] [^anthropic-bp] | G |
| `cmd-single` | A way to run one test is given | project | test runner plus a selector (`-k`, `-t`, `--filter`, `::`, ...) or a path to one test file or directory | [^anthropic-bp] | G |
| `cmd-lint` | A lint or typecheck command is given | project | code span matches a lint/typecheck pattern | [^anthropic-bp] | G |
| `cmd-build` | A build command is given | project | code span matches a build pattern | [^agents-md-spec] | G |
| `rule-destructive` | A guard against destructive or irreversible operations | all | a sentence with a prohibition and a destructive-operation term | [^agent-readmes] [^ssojet] | G |
| `rule-secrets` | A rule about handling secrets | all | a sentence with a secret term and a handling verb | [^anthropic-bp] | G |
| `rule-injection` | Instructions found in files, logs, or tool output are data | all | injection pattern | [^anthropic-bp] | G |
| `verify-done` | Completion is tied to a runnable verification | all | a done/before-commit sentence naming test, lint, typecheck, build, or CI | [^anthropic-bp] | G |
| `etiquette` | Commit, branch, or PR conventions exist | all | etiquette pattern | [^anthropic-bp] | G |
| `pointers` | Points to further documents instead of inlining them | all | at least one import, relative link, or path | [^anthropic-memory] [^humanlayer] | G |
| `no-overview-dump` | No long architecture or directory-overview section | all | no overview-titled section longer than 40 lines | [^eth-agents-md] [^anthropic-bp] | G |
| `emphasis` | Emphasis is rare enough to stand out | all | emphasized lines ≤ max(3, 5% of lines); threshold chosen here, the source gives none | [^anthropic-bp] | G |
| `vague` | No unverifiable adjectives | all | zero matches of the vague-phrase list | [^anthropic-memory] | G |
| `tool-leak` | A cross-tool AGENTS.md does not name one tool's private paths | AGENTS.md files | no `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.windsurf/`, `copilot-instructions.md` | [^anthropic-memory] | G |
| `pointer-file` | The repository wires Claude Code to the shared file | AGENTS.md entries with a sibling | `CLAUDE.md` exists and starts with `@AGENTS.md` (or is a symlink to `AGENTS.md`) | [^anthropic-memory] | G |

## Measurements (not scored)

| id | value | source |
|---|---|---|
| `measure-chars` | Unicode characters | [^anthropic-memory] |
| `measure-bytes` | UTF-8 bytes | [^openai-agents-md] |
| `measure-words` | whitespace-separated words | [^agent-readmes] |
| `measure-lines` | lines | [^anthropic-memory] |
| `measure-tokens-approx` | characters / 4 (a heuristic, not a tokenizer) | [^anthropic-bp] |
| `measure-h2` | second-level headings | [^agent-readmes] |
| `measure-bullets` | bullet or numbered lines | [^anthropic-memory] |
| `measure-emphasis` | uppercase emphasis tokens | [^anthropic-bp] |
| `measure-pointers` | pointers to other documents | [^humanlayer] |
