---
title: References
---

# References

Every citation key used in this repository is defined here as a Markdown footnote. `make test` fails on an undefined or unused key. Each web source records the date it was read and an archived copy; documentation pages change often, so the archive is what a claim was checked against. Corpus repositories are pinned by commit in `data/manifest.lock.json` and are not repeated here.

## Vendor documentation

[^anthropic-bp]: Anthropic. "Best practices for Claude Code." Claude Code documentation. https://code.claude.com/docs/en/best-practices — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085003/https://code.claude.com/docs/en/best-practices. Cited for: the include/exclude table for CLAUDE.md content, "give Claude a way to verify its work", emphasis guidance ("If you emphasize many lines, none of them stands out"), preferring single tests, and hostile-content-driven actions.

[^anthropic-memory]: Anthropic. "How Claude remembers your project." Claude Code documentation. https://code.claude.com/docs/en/memory — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085027/https://code.claude.com/docs/en/memory. Cited for: the 200-line target, specificity examples, `@path` imports, `.claude/rules/`, and the statement that Claude Code reads `CLAUDE.md` and not `AGENTS.md` (recommending `@AGENTS.md` or a symlink).

[^openai-agents-md]: OpenAI. "AGENTS.md" (Codex agent configuration). https://learn.chatgpt.com/docs/agent-configuration/agents-md — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085051/https://learn.chatgpt.com/docs/agent-configuration/agents-md. Cited for: global versus project files, nested precedence, and the 32 KiB default cap (`project_doc_max_bytes`).

[^agents-md-spec]: "AGENTS.md — A simple, open format for guiding coding agents." https://agents.md/ — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085117/https://agents.md/. Source repository `openai/agents.md` (MIT). Stewarded by the Agentic AI Foundation under the Linux Foundation; this project is not affiliated. Cited for: the recommended sections and the sample file.

## Practitioner guidance

[^humanlayer]: HumanLayer. "Writing a good CLAUDE.md." HumanLayer blog. https://www.humanlayer.dev/blog/writing-a-good-claude-md — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085144/https://www.humanlayer.dev/blog/writing-a-good-claude-md. Cited for: the under-300-lines consensus, progressive disclosure, "prefer pointers to copies", and "never send an LLM to do a linter's job".

[^ssojet]: SSOJet. "6 AGENTS.md Examples From Real Production Repos." https://ssojet.com/blog/agents-md-examples — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085216/https://ssojet.com/blog/agents-md-examples. Cited for: high-blast-radius rules first and the 40–80 line observation. A vendor blog; used only as a secondary source.

[^beams-commit]: Chris Beams. "How to Write a Git Commit Message." 2014. https://cbea.ms/git-commit/ — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085241/https://cbea.ms/git-commit/. Cited for: imperative subject lines and the 50/72 rule.

[^standard-readme]: Richard Littauer. "Standard Readme" specification. https://github.com/RichardLitt/standard-readme/blob/main/spec.md — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085346/https://github.com/RichardLitt/standard-readme/blob/main/spec.md. Cited for: README section order.

## Studies

[^agent-readmes]: Worawalan Chatlatanagulchai, Hao Li, Yutaro Kashiwa, Brittany Reid, Kundjanasith Thonglek, Pattara Leelaprute, Arnon Rungsawang, Bundit Manaskasemsak, Bram Adams, Ahmed E. Hassan, Hajimu Iida. "Agent READMEs: An Empirical Study of Context Files for Agentic Coding." arXiv:2511.12884, 2025-11-17. https://doi.org/10.48550/arXiv.2511.12884. Cited for: 2,303 context files from 1,925 repositories; 16 instruction types; testing instructions in about 75% of files and security instructions in about 15% (14.5% in the v1 HTML body, 14.8% in the abstract); median 485 words for Claude Code files; median update interval about 24 hours. The accompanying dataset (`hao-li/AgentREADMEs` on Hugging Face) declares no license and is not used here.

[^eth-agents-md]: Thibaud Gloaguen, Niels Mündler, Mark Müller, Veselin Raychev, Martin Vechev. "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" arXiv:2602.11988, 2026-02-12. https://doi.org/10.48550/arXiv.2602.11988. Cited for: no general improvement in task success from context files across 300 SWE-bench Lite tasks and 138 issues from repositories with developer-written files, four agents; inference cost up 20–23%; repository overviews not helpful; tool instructions followed (uv used 1.6 times per instance when mentioned versus fewer than 0.01 when not; repository-specific tools 2.5 times per instance when mentioned — absolute counts, not multipliers).

[^khatri-context-files]: Prakhar Khatri. "Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories." arXiv:2607.27250, 2026-07-28. https://doi.org/10.48550/arXiv.2607.27250. Single-author preprint. Cited only for: no detectable pass-rate difference between no context file, an always-on file, and selective retrieval across 288 evaluated runs (two agents, 17 tasks, three repositories), with the effect bounded to at most 10–15 percentage points by equivalence testing.

[^terminal-bench]: Mike A. Merrill, Alexander G. Shaw, Nicholas Carlini, Boxuan Li, Harsh Raj, Ivan Bercovich, Lin Shi, Jeong Yeon Shin, Thomas Walshe, E. Kelly Buchanan, Junhong Shen, Guanghao Ye, Haowei Lin, and others. "Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces." arXiv:2601.11868; also ICLR 2026 (https://openreview.net/forum?id=a7Qa4CcHak). https://doi.org/10.48550/arXiv.2601.11868. Cited for: the task format (instruction, Dockerfile, tests, oracle solution) and the harness that runs Claude Code, Codex CLI, OpenHands and Mini-SWE-Agent.

[^harbor-tasks]: Harbor framework. "Task Structure." https://www.harborframework.com/docs/tasks — accessed 2026-09-02. Archive: https://web.archive.org/web/20260902085305/https://www.harborframework.com/docs/tasks. Cited for: `instruction.md`, `task.toml`, `environment/Dockerfile`, `solution/solve.sh`, `tests/test.sh`, and the reward file at `/logs/verifier/reward.json`.

## Files and posts discussed but not in the corpus

[^hernanz-agents-md]: Marcos Hernanz. "After doing ~60B tokens, this is my full AGENTS.md." X, 2026. https://x.com/MarcosHernanz/status/2083954734487212511 — accessed 2026-09-02 (screenshot supplied by the maintainer; login may be required to view). Not fetchable from a licensed repository, so it is not a corpus entry; its rules are paraphrased in `src/AGENTS.md` with attribution (see [provenance](provenance.md)).

[^hernanz-follow-up]: Marcos Hernanz. Follow-up post: "Asking the models to not preserve backward compatibility can be dangerous. A few weeks ago one of my agents nuked an entire production table when doing a migration ..." X, 2026. https://x.com/MarcosHernanz/status/2084300817528672305 — accessed 2026-09-02. Cited for: the reason the compatibility rule in `src/AGENTS.md` is split and guarded.

[^karpathy-multica]: Forrest Chang (multica-ai). `CLAUDE.md` in `multica-ai/andrej-karpathy-skills`, "derived from Andrej Karpathy's observations on LLM coding pitfalls". https://github.com/multica-ai/andrej-karpathy-skills — pinned in the manifest at commit `8462496b34419f20b32778610571ac723e91f94c`. The repository has no license file (checked 2026-09-02). Not written by Karpathy. Cited for: the "surgical changes" and "goal-driven execution" rules paraphrased in `src/AGENTS.md`.

[^ferrox-agents-md]: Sean Donahoe (FerroxLabs). `agents-md`: a drop-in AGENTS.md synthesizing Karpathy's four principles. MIT. https://github.com/FerroxLabs/agents-md — pinned in the manifest. Listed as prior art: the nearest existing project to this one.
