---
title: How we compared and measured
---

# How we compared and measured

Two measurements sit behind this project; neither asks which file is better. The comparison
asks what published instruction files contain: ten public files, pinned by commit, read against ten
criteria. The experiment asks what one changes: three tasks by three conditions, ten runs a cell,
locked before any run.

## Sources the criteria rest on

Each criterion traces to a source below, with its citation, date read and archived copy in
[references.md](references.md). Sources behind the file's own rules are in
[rationale.md](rationale.md).

| Source | Kind | What it is used for |
|---|---|---|
| [anthropic-bp](references.md#ref-anthropic-bp) | vendor guidance | giving the agent a way to verify its work; what to include in an instruction file; the warning that emphasising many lines makes none of them stand out |
| [anthropic-memory](references.md#ref-anthropic-memory) | vendor documentation | the under-200-lines target, `@path` imports, and the fact that Claude Code reads `CLAUDE.md` |
| [anthropic-security](references.md#ref-anthropic-security) | vendor documentation | prompt injection: text found in files and tool output is not an instruction |
| [openai-agents-md](references.md#ref-openai-agents-md) | vendor documentation | nested precedence and the 32 KiB cap on loaded instruction files |
| [agents-md-spec](references.md#ref-agents-md-spec) | format | the tool-neutral file name and the sample file's setup and test sections |
| [humanlayer](references.md#ref-humanlayer) | practitioner | the length consensus, progressive disclosure, pointers instead of copies |
| [karpathy-multica](references.md#ref-karpathy-multica) | practitioner | the surgical-change rule |
| [agent-readmes](references.md#ref-agent-readmes) | study | what 2,303 real context files contain, and how rarely security instructions appear |
| [eth-agents-md](references.md#ref-eth-agents-md) | study | no general improvement in task success from context files; inference cost up 20–23% |
| [khatri-context-files](references.md#ref-khatri-context-files) | study | no detectable pass-rate difference, bounded to at most 10–15 percentage points |

Where they agree and differ:

| Point | Agreement |
|---|---|
| Give the agent a command that verifies its work | [anthropic-bp](references.md#ref-anthropic-bp) and [agents-md-spec](references.md#ref-agents-md-spec) agree; it is the one point every source states |
| Keep the file short | [anthropic-memory](references.md#ref-anthropic-memory) says under 200 lines, [humanlayer](references.md#ref-humanlayer) says under 300, [openai-agents-md](references.md#ref-openai-agents-md) sets a byte cap instead of a line count |
| Does an instruction file improve task success? | [eth-agents-md](references.md#ref-eth-agents-md) and [khatri-context-files](references.md#ref-khatri-context-files) both report no general improvement; the vendor guidance assumes it helps. This project treats the question as open, which is why the experiment measures both advantages and disadvantages |
| Repository overviews | [eth-agents-md](references.md#ref-eth-agents-md) reports they did not help, while five of the ten surveyed files carry one |
| Security instructions | [anthropic-security](references.md#ref-anthropic-security) and [agent-readmes](references.md#ref-agent-readmes) both treat them as necessary and rare; no file in the corpus below states a secrets rule or a rule about instructions found in files, and one of the ten raises a security consideration at all |

## The corpus

Inclusion rules, fixed when the survey was planned and before it ran.

1. A public `AGENTS.md` or `CLAUDE.md` at a repository root, reachable without an account.
2. At most 200 lines, the length criterion's own limit. Longer files go under "Files left out for
   length" rather than being dropped silently.
3. Pinned by commit in [`corpus.toml`](https://github.com/purpleeddy/agents-md-lab/blob/main/corpus.toml),
   so every verdict describes an immutable text.
4. Both file names represented, no two entries by one author, spanning vendor-adjacent, product
   and practitioner repositories; `why` in `corpus.toml` records what each shows.
5. A repository with no license file is recorded by line number only, its text never reproduced.

Columns are the criteria below, in order.

<!-- corpus:start -->

| File | Type | Stars | Lines | License | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [openai/agents.md](https://github.com/openai/agents.md/blob/ba9474a69e9a2c0c4176713843b78e8f54377941/AGENTS.md) | AGENTS.md | 24,174 | 43 | MIT | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | 4/10 |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/blob/7057f3318b938a2dd095fd89f786c11772b08197/CLAUDE.md) | CLAUDE.md | 8,805 | 44 | MIT | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | 3/10 |
| [getsentry/sentry](https://github.com/getsentry/sentry/blob/7395d32708261ef723e33be460da1641c36a9e0e/AGENTS.md) | AGENTS.md | 44,738 | 137 | FSL-1.1-ALv2 | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | 6/10 |
| [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty/blob/9897d6caba05c0cbf256f86bec2e2935f164a9c7/AGENTS.md) | AGENTS.md | 60,787 | 39 | MIT | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | 4/10 |
| [temporalio/temporal](https://github.com/temporalio/temporal/blob/109a38e8ca4827ae8c624fc1a9382290dcae0f69/AGENTS.md) | AGENTS.md | 22,865 | 105 | MIT | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | 6/10 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/8462496b34419f20b32778610571ac723e91f94c/CLAUDE.md) | CLAUDE.md | 210,637 | 65 | NONE | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | 5/10 |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer/blob/6014ccf95edf71b2d0ba31bcd65a9297a3decb65/CLAUDE.md) | CLAUDE.md | 11,467 | 88 | Apache-2.0 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | 4/10 |
| [omacom/omarchy](https://github.com/omacom/omarchy/blob/1c8f728b25cb8a42f1d02e4d2441230132cedb6c/AGENTS.md) | AGENTS.md | 38,642 | 133 | MIT | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | 5/10 |
| [obra/superpowers](https://github.com/obra/superpowers/blob/1d4c8d2aafb8fa0de3e5d7df80ff44899fa7e402/CLAUDE.md) | CLAUDE.md | 282,444 | 115 | MIT | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | 4/10 |
| [getzep/graphiti](https://github.com/getzep/graphiti/blob/375023b9e8db9957a48b2b6f3cb30d505a5ab39b/CLAUDE.md) | CLAUDE.md | 30,645 | 181 | Apache-2.0 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | 4/10 |
| Met by |  |  |  |  | 10 | 8 | 3 | 0 | 0 | 0 | 3 | 5 | 10 | 6 | of 10 files |

<!-- corpus:end -->

## The ten criteria

One question each with a fixed answer procedure, defined and version-stamped in
[`docs/criteria.json`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/criteria.json),
which also carries a worked example of each criterion and its known false positives and negatives.
The front page shows the same definitions in tooltips.

<!-- criteria:start -->

| # | Criterion | Question | Why | Sources |
|---|---|---|---|---|
| 1 | **Length** (`length`) | Is the file at most 200 total lines, counted the way wc -l counts them (newline-terminated lines)? | Anthropic's memory documentation targets under 200 lines per file because longer files consume more context and reduce adherence, and Codex stops loading instruction files at a 32 KiB cap. | [anthropic-memory](references.md#ref-anthropic-memory), [openai-agents-md](references.md#ref-openai-agents-md) |
| 2 | **Runnable commands** (`commands`) | Does the file name at least one runnable command, either as a backticked token or as a line that is itself a command, in both cases a common runner followed by at least one argument or flag? | The AGENTS.md sample file leads with setup and test commands, and Anthropic's best practices ask for a way for the agent to verify its work; a runner name with no argument is not a command anyone can run. | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 3 | **Verification before done** (`done_verification`) | Does the file say that something must be run and pass before the work counts as finished? | "Give Claude a way to verify its work" is the single piece of vendor advice both the AGENTS.md format and Anthropic's best practices agree on, and it is what separates a claim of completion from a checked one. | [agents-md-spec](references.md#ref-agents-md-spec), [anthropic-bp](references.md#ref-anthropic-bp) |
| 4 | **Guard on destructive commands** (`destructive_guard`) | Does the file put a guard (never, ask first, requires approval) around a destructive or irreversible operation? | The vendor guide's permission modes ask before actions that modify the system; a written rule extends that to the irreversible cases a permission prompt cannot tell apart (force-push, history rewrite, dropping data). | [anthropic-bp](references.md#ref-anthropic-bp) |
| 5 | **Secrets** (`secrets`) | Does the file tell the agent to keep secrets, credentials, keys or tokens out of its output and its commits? | Security instructions appear in only about 15% of context files in the Agent READMEs study, while an agent reads files that contain secrets in the ordinary course of a task. | [agent-readmes](references.md#ref-agent-readmes), [anthropic-bp](references.md#ref-anthropic-bp) |
| 6 | **Instructions in files are data** (`file_instructions_are_data`) | Does the file say that instructions found inside files, issues, logs or tool output are data to report rather than commands to obey? | Anthropic's security documentation describes prompt injection as text inserted to override the assistant's instructions; an instruction file is the one place a project can state the rule before the agent meets the injected text. | [anthropic-security](references.md#ref-anthropic-security), [agent-readmes](references.md#ref-agent-readmes) |
| 7 | **Scope restraint** (`scope_restraint`) | Does the file ask for the smallest change and warn against touching unrelated or adjacent code? | Unrequested refactoring is the failure mode the Karpathy-derived rules and HumanLayer's guidance both name, and it is the one a reviewer pays for rather than the agent. | [karpathy-multica](references.md#ref-karpathy-multica), [humanlayer](references.md#ref-humanlayer), [anthropic-bp](references.md#ref-anthropic-bp) |
| 8 | **Pointer instead of copy** (`pointer_not_copy`) | Does the file point at another document (an @import, a docs/ path, CONTRIBUTING.md) instead of copying its content in? | Both the AGENTS.md format (nested files) and Anthropic's memory documentation (@path imports) expect the instruction file to be an index; HumanLayer's guidance states the same rule as "prefer pointers to copies". | [anthropic-memory](references.md#ref-anthropic-memory), [agents-md-spec](references.md#ref-agents-md-spec), [humanlayer](references.md#ref-humanlayer) |
| 9 | **Emphasis restraint** (`emphasis_restraint`) | Do at most 10% of the non-empty lines shout, counting lines with IMPORTANT, NEVER, ALWAYS, MUST, CRITICAL or DO NOT in capitals, a run of exclamation marks, or a bolded MUST/NEVER/ALWAYS? | Anthropic's best practices say to add emphasis to one line at a time, because "If you emphasize many lines, none of them stands out". | [anthropic-bp](references.md#ref-anthropic-bp) |
| 10 | **Tool neutrality** (`tool_neutral`) | Is the file free of single-vendor paths and commands, or does it name AGENTS.md so that the vendor-specific file is only a pointer? | The AGENTS.md format exists so that one file serves every agent; Anthropic's memory documentation notes that Claude Code reads CLAUDE.md and recommends importing AGENTS.md from it rather than maintaining two files. | [agents-md-spec](references.md#ref-agents-md-spec), [anthropic-memory](references.md#ref-anthropic-memory) |

<!-- criteria:end -->

## The content criteria

A second set of eight, the `content` set in the same file. The rule criteria ask how a file is
written; these ask what it tells an agent about the project. They come from the two vendor lists of
what an instruction file should carry: the Include column of
[anthropic-bp](references.md#ref-anthropic-bp), and the sample file's sections and "Cover what
matters" in [agents-md-spec](references.md#ref-agents-md-spec). Both sets run on the same engine
over the same text and are never added together: one coverage number per set.

<!-- criteria-content:start -->

| # | Criterion | Question | Why | Sources |
|---|---|---|---|---|
| 1 | **Project overview** (`overview`) | Does the file say what the project is or how it is laid out — an overview, an architecture note, or a directory structure? | "Project overview" is the first of the sections the AGENTS.md site lists under "Cover what matters", and Anthropic's best practices include "Architectural decisions specific to your project" while excluding "File-by-file descriptions of the codebase". | [agents-md-spec](references.md#ref-agents-md-spec), [anthropic-bp](references.md#ref-anthropic-bp) |
| 2 | **Named files** (`key_files`) | Does the file name at least one source file or module path with a directory component? | Anthropic's memory documentation asks for instructions concrete enough to verify and gives "API handlers live in `src/api/handlers/`" as the shape to imitate, in place of "Keep files organized". | [anthropic-memory](references.md#ref-anthropic-memory) |
| 3 | **Environment setup** (`setup`) | Does the file say how to set the development environment up — installation, prerequisites, or a named environment step? | "Developer environment quirks (required env vars)" is a row of Anthropic's include table for CLAUDE.md, and the AGENTS.md sample file opens with "Dev environment tips". | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 4 | **Code style** (`code_style`) | Does the file state a code style, a naming convention, or the formatter the project uses? | "Code style rules that differ from defaults" is the second row of Anthropic's include table, against "Standard language conventions Claude already knows" in the exclude column, and "Code style guidelines" is one of the sections the AGENTS.md site names. | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 5 | **Testing instructions** (`testing_instructions`) | Does the file say how to run the tests — a runner command, a test-command section, or an instruction to run them? | "Testing instructions and preferred test runners" is a row of Anthropic's include table, and "Testing instructions" is a section of the AGENTS.md sample file and one of the five the site names. | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 6 | **Repository etiquette** (`pr_etiquette`) | Does the file state a convention for pull requests, commits, branches or review? | "Repository etiquette (branch naming, PR conventions)" is a row of Anthropic's include table, the AGENTS.md sample file ends with "PR instructions", and the site's third step names "Commit messages or pull request guidelines". | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 7 | **Warnings and gotchas** (`warnings`) | Does the file warn about a project-specific gotcha on a line that also names a file or a path the warning applies to? | "Common gotchas or non-obvious behaviors" is the last row of Anthropic's include table, against "Self-evident practices like 'write clean code'" in the exclude column, and the AGENTS.md site names "security gotchas" among the extra instructions a file should carry. | [anthropic-bp](references.md#ref-anthropic-bp), [agents-md-spec](references.md#ref-agents-md-spec) |
| 8 | **Security considerations** (`security`) | Does the file raise a security consideration — a threat, untrusted input, sanitising, authorisation, least privilege or input validation? | "Security considerations" is one of the five sections the AGENTS.md site names under "Cover what matters", and the Agent READMEs study finds security instructions in about 15% of the context files it collected. | [agents-md-spec](references.md#ref-agents-md-spec), [agent-readmes](references.md#ref-agent-readmes) |

<!-- criteria-content:end -->

The same ten files, columns in the order above.

<!-- corpus-content:start -->

| File | Type | Stars | Lines | License | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [openai/agents.md](https://github.com/openai/agents.md/blob/ba9474a69e9a2c0c4176713843b78e8f54377941/AGENTS.md) | AGENTS.md | 24,174 | 43 | MIT | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 2/8 |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/blob/7057f3318b938a2dd095fd89f786c11772b08197/CLAUDE.md) | CLAUDE.md | 8,805 | 44 | MIT | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 3/8 |
| [getsentry/sentry](https://github.com/getsentry/sentry/blob/7395d32708261ef723e33be460da1641c36a9e0e/AGENTS.md) | AGENTS.md | 44,738 | 137 | FSL-1.1-ALv2 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 5/8 |
| [ghostty-org/ghostty](https://github.com/ghostty-org/ghostty/blob/9897d6caba05c0cbf256f86bec2e2935f164a9c7/AGENTS.md) | AGENTS.md | 60,787 | 39 | MIT | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 4/8 |
| [temporalio/temporal](https://github.com/temporalio/temporal/blob/109a38e8ca4827ae8c624fc1a9382290dcae0f69/AGENTS.md) | AGENTS.md | 22,865 | 105 | MIT | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | 3/8 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/8462496b34419f20b32778610571ac723e91f94c/CLAUDE.md) | CLAUDE.md | 210,637 | 65 | NONE | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 0/8 |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer/blob/6014ccf95edf71b2d0ba31bcd65a9297a3decb65/CLAUDE.md) | CLAUDE.md | 11,467 | 88 | Apache-2.0 | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | 3/8 |
| [omacom/omarchy](https://github.com/omacom/omarchy/blob/1c8f728b25cb8a42f1d02e4d2441230132cedb6c/AGENTS.md) | AGENTS.md | 38,642 | 133 | MIT | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | 4/8 |
| [obra/superpowers](https://github.com/obra/superpowers/blob/1d4c8d2aafb8fa0de3e5d7df80ff44899fa7e402/CLAUDE.md) | CLAUDE.md | 282,444 | 115 | MIT | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | 1/8 |
| [getzep/graphiti](https://github.com/getzep/graphiti/blob/375023b9e8db9957a48b2b6f3cb30d505a5ab39b/CLAUDE.md) | CLAUDE.md | 30,645 | 181 | Apache-2.0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | 5/8 |
| Met by |  |  |  |  | 5 | 4 | 4 | 5 | 7 | 4 | 0 | 1 | of 10 files |

<!-- corpus-content:end -->

Two about these patterns, one about the site.

- **Three patterns were tightened before the corpus was read**, because a negated, incidental or
  placeholder use is a false positive on any file: `code_style` dropped the bare words for
  formatting and indentation, `testing_instructions` dropped "test suite", `warnings` now needs a
  path or filename on the gotcha line, and `security` dropped a bare match on "permission" during
  calibration. Each is in that criterion's `notes` with the lines that motivated it.
- **The author knew this repository's file while writing these patterns**, the bias named below.
  They are published, every verdict carries its evidence line, and the file is evaluated on both
  sets in public.
- **The site loads no external resource except the star count** and stores nothing about a
  visitor. That read-only request to GitHub's API sends an IP address and user agent, nothing
  else.

## Why the recommended file meets the rule criteria

The recommended file meets 9 of the 10 rule criteria, and that number is not evidence of anything:
the criteria and the file were written by one author, in the same weeks, from the same sources,
[anthropic-bp](references.md#ref-anthropic-bp),
[anthropic-memory](references.md#ref-anthropic-memory),
[anthropic-security](references.md#ref-anthropic-security),
[openai-agents-md](references.md#ref-openai-agents-md),
[agents-md-spec](references.md#ref-agents-md-spec), [humanlayer](references.md#ref-humanlayer)
and [karpathy-multica](references.md#ref-karpathy-multica). A file written from a set of sources
meets criteria drawn from them, so the number is expected by construction. One is
unmet. **Runnable commands**: the `## Project` section ships as the empty template, so the file
names no command until it lands in a repository. Two more were unmet until the criteria were
revised, which measured every file again in the same pass; no wording changed, and each reason in
full is on the [rationale page](rationale.md#what-the-check-says-about-this-file).

The checks are narrower still: each asks whether a statement is present, none whether it is good
or followed. A file can meet every rule criterion in seven lines:

<!-- stuffed:start -->

`docs/examples/stuffed.md` — 7 lines, sha256 `a6956183898a21883c0dc557c37062db5d4c5f56b451ee29b6f832413469a97e`. Rule criteria 10/10, content criteria 1/8.

<!-- stuffed:end -->

That file is [`docs/examples/stuffed.md`](https://github.com/purpleeddy/agents-md-lab/blob/main/docs/examples/stuffed.md),
an example of what presence-checking cannot see, not a file to adopt: it names a test
command no adopting repository necessarily has, and says nothing about the project it sits in.
The honest way to state a check's limit is a file that passes it and is useless. What the criteria
cannot answer, whether a file changes what an agent does, is what the experiment is for.


## How a verdict is decided

The engine is small, its limits are part of the result, and coverage counts what it finds and not
what a file is worth.

- **One line at a time.** CRLF and CR are normalised to LF and every pattern applies to a single
  line, so no criterion matches across a line break or into a fenced code block. That explains no
  verdict here: no file in this corpus fails a criterion because its evidence sat inside a fence.
- **Evidence.** A criterion passing on a match records up to three matching lines with their
  numbers; one passing on an absence records the offending lines. Every ✓ expands to its line.
- **Two engines, one answer.** `scripts/compare.py` and `docs/compare.js` run the same procedure,
  so the page can check a pasted file without a server; the patterns use the regex subset both
  compile identically, and `tests/test_compare.py` fails if one verdict differs.
- **Calibration is recorded, not hidden.** Several patterns were adjusted after reading the
  corpus, for example so a command table is not read as a completion condition. Each change is in
  that criterion's `notes` with the files that motivated it and the false positives and negatives
  remaining.
- **Reproduce it.** `scripts/compare.py` takes `--refresh`, `--check` and `--file`, as
  [CONTRIBUTING.md](https://github.com/purpleeddy/agents-md-lab/blob/main/CONTRIBUTING.md) sets out.


## Files left out for length

<!-- excluded:start -->

| File | Lines | Measured | Reason |
| --- | --- | --- | --- |
| [vercel/next.js/AGENTS.md](https://github.com/vercel/next.js/blob/HEAD/AGENTS.md) | 560 | 2026-09-07 | over 200 lines |
| [openai/codex/AGENTS.md](https://github.com/openai/codex/blob/HEAD/AGENTS.md) | 322 | 2026-09-07 | over 200 lines |
| [oven-sh/bun/CLAUDE.md](https://github.com/oven-sh/bun/blob/HEAD/CLAUDE.md) | 240 | 2026-09-07 | over 200 lines |
| [Kilo-Org/kilocode/AGENTS.md](https://github.com/Kilo-Org/kilocode/blob/HEAD/AGENTS.md) | 214 | 2026-09-07 | over 200 lines |
| [FerroxLabs/agents-md/AGENTS.md](https://github.com/FerroxLabs/agents-md/blob/HEAD/AGENTS.md) | 206 | 2026-09-07 | over 200 lines |
| [rails/rails/AGENTS.md](https://github.com/rails/rails/blob/HEAD/AGENTS.md) | 201 | 2026-09-07 | over 200 lines |
| [github/awesome-copilot/AGENTS.md](https://github.com/github/awesome-copilot/blob/HEAD/AGENTS.md) | 353 | 2026-09-07 | over 200 lines |

<!-- excluded:end -->

## The experiment

The design was locked before any run and is not restated here. The
[pre-registration](https://github.com/purpleeddy/agents-md-lab/blob/45b765a5a7424e855ee8fc0e28333e0d90d0f923/experiments/README.md)
is the authority on the three tasks, the three conditions, the ten runs a cell, the direction fixed
for every metric before the runs, and the Wilson and Newcombe intervals used instead of a
significance test. What the runs showed is on the [findings page](findings.md), from
`docs/data/experiment.json` over the 90 in `docs/data/experiment-runs.json`.

## What the experiment tested and what is shipped

The experiment ran one exact text, the root file with its `## Project` section replaced by the
empty template, sha256 `b8be420f0597e483469dbfb47dec94487103758016f2b03964d4c888f68fd832`, and not
the text shipped now; `git show 2a82474:AGENTS.md` through `generic_agents_md` from
`git show a556abe:scripts/experiment.py` reproduces it. Every version is a row below, measured on
its own text.

<!-- versions:start -->

| Version | Date | Lines | Bytes | Token estimate (bytes/4) | Criteria version | Rule criteria | Content criteria | What changed | Measured by | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1.0.0 | 2026-09-03 | 50 | 4,420 | 1,105 | 1.0.0 | 9/10 | 0/8 | the text the ninety runs wrote as `ours` | main run | measured, then revised |
| v1.0.1 | 2026-09-03 | 52 | 5,456 | 1,364 | 1.0.0 | 10/10 | 3/8 | four rule lines fixed after [an independent review](rationale.md#known-issues-the-review-found-in-the-file) of v1.0.0's text | not measured | shipped, then replaced |
| v1.1.0, as first written | 2026-09-03 | 35 | 3,840 | 960 | 1.0.0 | 8/10 | 0/8 | the rest of that review, then [a line audit](rationale.md#the-line-audit-what-each-rule-had-to-earn) that cut or merged every line with neither a measured effect nor a safety role | not measured | shipped, then amended |
| v1.1.0, amended | 2026-09-04 | 32 | 4,069 | 1,017 | 1.0.0 | 8/10 | 1/8 | [four rule clauses added from external feedback](rationale.md#amendments-after-external-feedback) and the Project template cut from five lines to two | not measured | shipped, then replaced |
| v1.2.0 | 2026-09-04 | 33 | 4,514 | 1,128 | 1.0.0 | 7/10 | 1/8 | [a second independent review](rationale.md#the-independent-design-review), of v1.1.0's text against the design goals, adopted whole | rounds 2 and 4 | adopted, then replaced |
| v1.3.0 | 2026-09-05 | 33 | 4,754 | 1,188 | 1.0.0 | 7/10 | 2/8 | [one boundary line moved](rationale.md#the-delivery-boundary) so an agent could deliver its own branch, and a Delivery slot added to the template | round 3 | not adopted; the pre-registered revert set was applied |
| v1.4.0 | 2026-09-07 | 32 | 4,438 | 1,109 | 1.1.0 | 9/10 | 0/8 | [six edits to v1.2.0](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#v140-the-text-adopted-on-review): five wordings compacted and one Boundaries sentence added, with the five lines that carry a measured effect byte-identical to v1.2.0's | not measured | adopted on review, and the file shipped now |

<!-- versions:end -->

Three things the table cannot hold. **Who the reviewers were.** Every review it names was a model
session, not a person and not an outside audit; no human reviewer outside this project has read the
file, and who read which text is on the
[rationale page](rationale.md#known-issues-the-review-found-in-the-file). **Why the coverage
columns are not one series.** Only the shipped row is measured at the current criteria version,
which the table names; within one version, lines were cut or reworded on their own merits and the
patterns then stopped matching, never the other way round: no line was written, kept or dropped to
change a verdict.
**Why one version has four hashes.** Before the shipped text, the root file carried this
repository's own `## Project` section and the page offered a copy with it emptied, so the table
below, of every text this project has offered, lists one early draft four times.

<!-- shipped:start -->

| Text | sha256 | Criteria version | Rule criteria | Content criteria |
| --- | --- | --- | --- | --- |
| Generic file the experiment ran (v1.0.0), recorded constant | `b8be420f0597e483469dbfb47dec94487103758016f2b03964d4c888f68fd832` | 1.0.0 | 9/10 | 0/8 |
| Root `AGENTS.md` with this repository's Project section filled in (v1.0.1), recorded constant | `ed7b9ce076e2b5bbd85a8a7dd2054a8984ae94f38b2ec3b874d5af9e8192f012` | 1.0.0 | 10/10 | 3/8 |
| Generic text, that Project section emptied (v1.0.1), recorded constant | `f8c7061ee44bb621a18c5539ac29b77854940723c5ca2d8b69c000dec5dacf36` | 1.0.0 | 9/10 | 0/8 |
| `docs/generated/agents-generic.md`, the file the button offered (v1.0.1), recorded constant | `2257466bb456d7b5200928597b700ff7ab211f9e08ecf694eb22860e3db972f4` | 1.0.0 | 8/10 | 0/8 |
| Root `AGENTS.md`, the first shipped as one file (v1.0.1 rules, empty template), recorded constant | `cc6035b0b7af5f63dd824cff31e13c77a790688424245e9785bc3c2e9cdaf87a` | 1.0.0 | 9/10 | 0/8 |
| Root `AGENTS.md` v1.1.0 as first written, before the 2026-09-04 amendment, recorded constant | `e9919a84e8e1d5278adfb0ddebeb46dd203d74bd17bc390ceabdb05c31f4c334` | 1.0.0 | 8/10 | 0/8 |
| Root `AGENTS.md` v1.1.0 as amended, the text v1.2.0 replaces, recorded constant | `f5eaf556b6ace2c6067eb9e3f61decb49e12bf610abe17fddbf0da67239cd84d` | 1.0.0 | 8/10 | 1/8 |
| Root `AGENTS.md` v1.2.0, the text rounds 2 and 4 measured, recorded constant | `e1677f04d7abe4a61031fd7e3a66be4df8e9e072b1a0313f22f4512254b2b8dc` | 1.0.0 | 7/10 | 1/8 |
| Root `AGENTS.md` v1.3.0, the text round 3 measured and did not adopt, recorded constant | `5714cfaa9540bb4039c7b358087d508fa3126dc4c315afcbd54138f0dc0560bd` | 1.0.0 | 7/10 | 2/8 |
| Root `AGENTS.md`, the file shipped now (v1.4.0) | `2811faf02714c8426746c6d7a7df0d4931e44718f568a8f1df739df2e8a77aa5` | 1.1.0 | 9/10 | 0/8 |

<!-- shipped:end -->

Four lines changed after the runs and nothing else did; all four are quoted, was and now, in
the [record](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#the-four-v101-lines).
The findings describe the measured text and are unaffected by them: the rules behind every metric
that moved are the Done test requirements, the Reporting section and "Read the files you will
change and their callers", identical in both texts. The four lines are themselves untested, written
in response to a review whose other findings are on the
[rationale page](rationale.md#known-issues-the-review-found-in-the-file).

## How the file evolves

Four grounds, each with a limit. **Measured effect** on the locked test set is the only ground for
adopting a rule; its limit is that test set, ten runs a cell, three tasks, one model, so a rule
aimed at behaviour the tasks never exercise needs a new task and a version bump first.
**Independent review**, here always a model session given the file text and nothing else, is the
ground for a safety boundary: every harm metric sits at the floor in all three conditions, so the
runs cannot separate a boundary that works from one nobody tested. Reasoning is not measurement, so
it still passes the acceptance rule. **Sources and corpus prevalence** give a rule
standing, not warrant. **Size** is a cost on every version.

Then subtraction. Each version re-reads the `none` cells for the current model, since
[anthropic-harness-design](references.md#ref-anthropic-harness-design) is right that assumptions
grow stale as the model gets more capable while the UX, cost and security boundaries stay. A rule
whose behaviour `none` already shows at the ceiling is a deletion candidate unless it is a safety
boundary: [anthropic-bp](references.md#ref-anthropic-bp) asks "would removing this cause Claude to
make mistakes?", and
[anthropic-context-engineering](references.md#ref-anthropic-context-engineering) argues for the
smallest set of high-signal tokens. [eth-agents-md](references.md#ref-eth-agents-md) supports both:
instructions are followed, overviews are not, cost rises by over 20%.
[mini-swe-agent](references.md#ref-mini-swe-agent) is the limit case, a hundred lines above 74% on
SWE-bench Verified; [weng-harness](references.md#ref-weng-harness) the counterpoint that the
interface with context and tools remains. A version that raises cost without moving a metric has
failed.

The loop: propose from review or a cited source, pre-register the acceptance rule and the revert
set, run, adopt or revert, record every text by hash, at most two rounds.

The delivery revision is the worked example and round 4 the control: with the text reverted, the
metric that decided round 3 read the round-3 value again, so the drop was not the text. One rule
follows: a round compares against cells collected the day it runs. Both are on the
[findings page](findings.md#round-3-a-version-the-rule-did-not-adopt) and in the pre-registration's
[round-3](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-05-opus-5)
and
[round-4](https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md#results-2026-09-05-opus-5-the-control)
Results sections.

**Karpathy phrase check.** The one corpus file with no license is never quoted here, and the check
stores no phrases: from the cached pinned file, take every fifth line over 40 characters, keep the
first six and grep each against every published file. It returns nothing; the cache is not
committed, so it skips in a fresh checkout.

**Permission settings.** The destructive list the file recommends is applied to this repository
itself, through the deny entries and the `PreToolUse` guard in
[CONTRIBUTING.md](https://github.com/purpleeddy/agents-md-lab/blob/main/CONTRIBUTING.md), which is
looser than the shipped file: a deny list is a floor, never the whole rule. It is not part of the
text under test and is not measured.

## Author bias and limitations

- The `ours` file is written by the author of this project, who knew all three tasks when
  writing it, because the test set was locked first. The `karpathy` file had no such advantage.
  The pre-registration records this as a limitation of the main run and traces every rule of the
  file to a source or a corpus observation rather than to a task.
- Ten runs per cell make wide intervals. A difference of one or two runs is inside them.
- The published comparison rests on `none` and `karpathy` cells collected on one date and reused
  by rounds 2, 3 and 4. Round 4 re-ran one text on a later date and moved a gated metric by five
  runs, so a stale baseline cell is a threat to validity and not a constant.
- One model, one CLI version, one flag set. Nothing here generalises to another agent without
  re-running it.
- The criteria are regexes over lines. A file can state a rule in wording no pattern anticipated,
  and this project's own `AGENTS.md` is a recorded example: see the note in
  [rationale.md](rationale.md#what-the-check-says-about-this-file).
- The corpus is ten files chosen by hand. It is a sample of what popular repositories publish,
  not a random sample of anything.

## What this is not

- **Not a ranking.** No file is ordered above another, and the table cannot be sorted by
  coverage. The count of criteria met is a description of a text, not a verdict on a project.
- **Not a quality measure.** A short file that names one command may serve its repository better
  than a long file that meets nine criteria.
- **Not a claim that instruction files work.** Two of the three studies cited here report no
  general improvement in task success. This project measures what changes, in both directions,
  on three tasks — which is a much smaller claim.
- **Not affiliated** with the AGENTS.md format, the Agentic AI Foundation, or any vendor whose
  documentation is cited.

What the project does license, said in one place beside the limits above and the ones the
experiment carries, is the [closing section](index.html#what-this-shows) of the front page; the
experiment's own list is [what was not shown](findings.md#what-was-not-shown).
