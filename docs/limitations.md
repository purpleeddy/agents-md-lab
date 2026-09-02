---
title: Limitations
---

# Limitations

Read this before quoting any number from the report.

1. **The score measures guideline conformance, not effect.** Every check in v1 is grade `G`: it encodes what vendor documentation or a published study recommends. Passing a check says a file follows that advice, not that the advice works. The two controlled studies we know of could not detect a task-success difference from context files at all (`eth-agents-md`: 438 tasks, 4 agents, cost up 20–23%; `khatri-context-files`: 288 runs). Until the experiments in v1.1 run, no check here is evidence of effect.

2. **The corpus is a curated sample, not a population.** About fifteen well-known files were chosen by the maintainer because they are widely cited. Nothing about them generalizes to the tens of thousands of context files on GitHub. The one large-scale descriptive study (`agent-readmes`, 2,303 files) is cited for population statistics; its dataset is not used because it carries no license.

3. **Types are not comparable to each other.** A monorepo onboarding file and a personal rules file are different documents with different jobs. The report keeps them in the same table for convenience but never ranks across types, and the four command checks apply only to project files. Do not compare a project file's score with a generic file's score.

4. **Checks are regular expressions.** They detect wording, not intent. A file can satisfy `rule-destructive` with a sentence that no agent will ever act on, and a well-written guard phrased unusually can fail it. Every pattern is public in `scripts/lint.py`; when a pattern misses a legitimate phrasing, the fix is a pull request with a fixture.

5. **The scoring can be gamed, visibly.** Because the checks are deterministic, a file written to the patterns will pass them. The length, emphasis, and vagueness checks catch the crudest padding; they do not catch a file that says the right words without meaning them. This is a reason to keep the score labeled as conformance.

6. **The author's file is in the same tables, and it was written against the checks.** `src/AGENTS.md` is linted by the same code as every other file and shown in its own table, outside the corpus. The maintainer wrote the checks, chose the corpus, and revised the file after the checks existed; it passes all of them. Everything is deterministic and reproducible, but it is not independent, and on the checks with low corpus pass rates (`rule-destructive`, `rule-injection`, `verify-done`) its pass shows that the patterns match the maintainer's phrasing, not that the patterns have good recall.

7. **Token counts are a heuristic.** "Approximate tokens" is characters divided by four. Real tokenizers differ by model and by language.

8. **Experiments (v1.1) will be narrow.** When they run, they will cover one agent, one model, one CLI version, and a handful of rules, with pre-registered outcomes and confidence intervals. Task success will be recorded only as a harm signal, never as the primary outcome, because prior work shows it is insensitive at any affordable sample size.

9. **Prior work is cited for what it found, not for more.** "Did not detect a difference" is not "no effect". The tool-use numbers in `eth-agents-md` are absolute uses per instance, not multipliers.

Citation keys resolve in [references.md](references.md).
