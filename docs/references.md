---
title: References
---

# References

Every citation key used in this repository is defined here once. Each web source records the date
it was read and, where one exists, an archived copy; documentation pages change often, so the
archive is what a claim was checked against. Every URL below was fetched during the stage that
added it, except `hernanz-agents-md`, which is described in its own entry.

Each entry carries the anchor `ref-` plus its key, which is what every citation on this site links
to: `anthropic-bp` is [`references.md#ref-anthropic-bp`](#ref-anthropic-bp).

## Vendor documentation

The pages the vendors publish about their own instruction files.

- <a id="ref-anthropic-bp"></a>**anthropic-bp** — Anthropic. "Best practices for Claude Code." Claude Code documentation. https://code.claude.com/docs/en/best-practices — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085003/https://code.claude.com/docs/en/best-practices.

  Cited for: "Give Claude a way to verify its work", the include/exclude guidance for CLAUDE.md content, and the emphasis warning ("If you emphasize many lines, none of them stands out"). The content criteria take their list from the Include column of that table: "Bash commands Claude can't guess", "Code style rules that differ from defaults", "Testing instructions and preferred test runners", "Repository etiquette (branch naming, PR conventions)", "Architectural decisions specific to your project", "Developer environment quirks (required env vars)" and "Common gotchas or non-obvious behaviors", against the Exclude column's "File-by-file descriptions of the codebase", "Standard language conventions Claude already knows" and "Self-evident practices like 'write clean code'".

- <a id="ref-anthropic-memory"></a>**anthropic-memory** — Anthropic. "How Claude remembers your project." Claude Code documentation. https://code.claude.com/docs/en/memory — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085027/https://code.claude.com/docs/en/memory.

  Cited for: "Size: target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence.", "The more specific and concise your instructions, the more consistently Claude follows them.", `@path/to/import` imports, and the fact that Claude Code reads `CLAUDE.md` rather than `AGENTS.md`. Also for the specificity examples that ask for a named path rather than a general instruction: "API handlers live in `src/api/handlers/`" instead of "Keep files organized".

- <a id="ref-anthropic-security"></a>**anthropic-security** — Anthropic. "Security." Claude Code documentation. https://code.claude.com/docs/en/security — accessed 2026-09-03. Archive: https://web.archive.org/web/20260829183136/https://code.claude.com/docs/en/security.

  Cited for: the "Protect against prompt injection" section — "Prompt injection is a technique where an attacker attempts to override or manipulate an AI assistant's instructions by inserting malicious text" — and the best practices for working with untrusted content.

- <a id="ref-openai-agents-md"></a>**openai-agents-md** — OpenAI. "AGENTS.md" (Codex agent configuration). https://learn.chatgpt.com/docs/agent-configuration/agents-md — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085051/https://learn.chatgpt.com/docs/agent-configuration/agents-md.

  Cited for: nested precedence and the size cap — Codex "stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default)".

- <a id="ref-agents-md-spec"></a>**agents-md-spec** — "AGENTS.md — A simple, open format for guiding coding agents." https://agents.md/ — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085117/https://agents.md/. Source repository `openai/agents.md` (MIT). Stewarded by the Agentic AI Foundation under the Linux Foundation; this project is not affiliated.

  Cited for: the tool-neutral file name, the sample file's setup-commands and test-commands sections, and nested files for subprojects. Also for the sections the page names: the sample file's "Dev environment tips", "Testing instructions" and "PR instructions", the "Cover what matters" list (project overview, build and test commands, code style guidelines, testing instructions, security considerations) and the extra instructions it names next to it ("Commit messages or pull request guidelines, security gotchas").

## Practitioner guidance

Written by people who maintain instruction files rather than the tools that read them.

- <a id="ref-humanlayer"></a>**humanlayer** — HumanLayer. "Writing a good CLAUDE.md." HumanLayer blog. https://www.humanlayer.dev/blog/writing-a-good-claude-md — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085144/https://www.humanlayer.dev/blog/writing-a-good-claude-md.

  Cited for: the under-300-lines consensus, progressive disclosure, and "prefer pointers to copies".

- <a id="ref-karpathy-multica"></a>**karpathy-multica** — Forrest Chang (multica-ai). `CLAUDE.md` in `multica-ai/andrej-karpathy-skills`, "derived from Andrej Karpathy's observations on LLM coding pitfalls". https://github.com/multica-ai/andrej-karpathy-skills — accessed 2026-09-03; pinned in `corpus.toml` at commit `8462496b34419f20b32778610571ac723e91f94c`. The repository has no license file (checked 2026-09-02), so its contents are never reproduced here: only line numbers and derived facts. Not written by Karpathy.

  Cited for: the surgical-change rule.

- <a id="ref-hernanz-agents-md"></a>**hernanz-agents-md** — Marcos Hernanz. "After doing ~60B tokens, this is my full AGENTS.md." X, 2026. https://x.com/MarcosHernanz/status/2083954734487212511 — accessed 2026-09-03. The page serves its body only with JavaScript and viewing it may require an account, so no archived copy of the text is available here; the file text was transcribed from an image of the post supplied by the project author on 2026-09-03, and the seven bullets are summarised in [rationale.md](rationale.md), not reproduced.

  Cited for: the simplest-implementation rule, the reuse-first rule and the no-compatibility-shims rule, which v0 of this project's file took from the post. Not a corpus entry: the corpus is files fetchable at a pinned commit.

- <a id="ref-beams-commit"></a>**beams-commit** — Chris Beams. "How to Write a Git Commit Message." 2014. https://cbea.ms/git-commit/ — accessed 2026-09-03. Archive: https://web.archive.org/web/20260902085241/https://cbea.ms/git-commit/.

  Cited for: the imperative mood in the subject line ("Use the imperative mood in the subject line"), "Limit the subject line to 50 characters" and "Wrap the body at 72 characters" — the 72 in this repository's commit rule is the body-wrap figure used as a subject ceiling, not the source's 50-character subject target.

## Studies

Empirical work on what context files contain and whether they change an agent's results.

- <a id="ref-agent-readmes"></a>**agent-readmes** — Worawalan Chatlatanagulchai, Hao Li, Yutaro Kashiwa, Brittany Reid, Kundjanasith Thonglek, Pattara Leelaprute, Arnon Rungsawang, Bundit Manaskasemsak, Bram Adams, Ahmed E. Hassan, Hajimu Iida. "Agent READMEs: An Empirical Study of Context Files for Agentic Coding." arXiv:2511.12884, 2025-11-17. https://arxiv.org/abs/2511.12884 — accessed 2026-09-03. https://doi.org/10.48550/arXiv.2511.12884.

  Cited for: 2,303 context files from 1,925 repositories; 16 instruction types; testing instructions in about 75% of files and security instructions in about 15%; median 485 words for Claude Code files. The accompanying dataset declares no license and is not used here.

- <a id="ref-eth-agents-md"></a>**eth-agents-md** — Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, Martin Vechev. "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" arXiv:2602.11988, 2026-02-12. https://arxiv.org/abs/2602.11988 — accessed 2026-09-03. https://doi.org/10.48550/arXiv.2602.11988.

  Cited for: no general improvement in task success from context files across 300 SWE-bench Lite tasks and 138 issues from repositories with developer-written files, four agents; inference cost up 20–23%; repository overviews not helpful; tool instructions followed.

- <a id="ref-khatri-context-files"></a>**khatri-context-files** — Prakhar Khatri. "Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories." arXiv:2607.27250, 2026-07-28. https://arxiv.org/abs/2607.27250 — accessed 2026-09-03. https://doi.org/10.48550/arXiv.2607.27250. Single-author preprint. Cited only for: no detectable pass-rate difference between no context file, an always-on file, and selective retrieval across 288 evaluated runs, with the effect bounded to at most 10–15 percentage points by equivalence testing.

## Corpus files

The ten files in the comparison are not cited here. Each one is pinned by commit, license and
content hash in [`corpus.toml`](https://github.com/purpleeddy/agents-md-lab/blob/main/corpus.toml),
and its view, raw and latest URLs are in the table on the front page and in
[`docs/data/comparison.json`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/data/comparison.json).
One corpus file is also a cited source, because a rule of this repository's own `AGENTS.md` rests
on it: [`karpathy-multica`](#ref-karpathy-multica), listed under Practitioner guidance above. Its
repository carries no license, so only line numbers and derived facts are recorded and none of its
text appears anywhere in this project.
