---
title: Design
---

# agents-md-lab — design and implementation specification

This document is the implementation contract for the repository. Anyone should be able to implement or extend the project from this file alone. When code and this document disagree, fix one of them in the same change.

Status: v1 (deterministic checks and report). v1.1 (behavioral experiments) is specified here but not yet built; it needs a separate go-ahead because it spends model tokens.

## 1. Purpose and non-goals

**Core sentence.** Lint context files (`AGENTS.md`, `CLAUDE.md`) with deterministic, source-cited checks, and test contested rules with pre-registered behavioral experiments, so that the file we recommend is backed by evidence rather than taste.

**Evidence grades.** Every check carries one grade:

| Grade | Meaning |
|---|---|
| `G` | Backed only by vendor guidance or published literature (a citation key in `docs/references.md`). |
| `E+` | An experiment in this repository found the rule changes agent behavior in the intended direction. |
| `E-` | An experiment found no effect or a harmful effect. The check stays in the catalog, marked so people stop cargo-culting it. |

The project's only two jobs are to grow the check catalog and to move checks from `G` to `E+` or `E-`.

**Non-goals (v1).** Written first because readers assume the opposite.

- No task-success benchmark. Two studies could not detect a pass-rate difference from context files (see `references.md`: `eth-agents-md`, `khatri-context-files`); a small local benchmark would produce a confident-looking noise ranking.
- No quality ranking of files. The report has a score column (`passed / applicable`) and no rank column, no sorted table, no "best" language. Cross-type comparison (a monorepo onboarding file versus a personal rules file) is a category error.
- No LLM judges. A rubric written by the author, applied by one vendor's models, to a file the author wrote, is a self-confirmation loop. Every check here is a deterministic function with a unit test.
- No redistribution of corpus files. Only a manifest with commit-pinned URLs and hashes is committed. Results contain booleans, counts, and line numbers, never text from the sources.
- Not affiliated with the AGENTS.md specification (agents.md, stewarded by the Agentic AI Foundation under the Linux Foundation).

## 2. Decisions log

What was removed from earlier designs after five independent adversarial reviews (methodology, open-source reproducibility, red team, practitioner value, alternative designs), and why.

| Removed | Reason |
|---|---|
| Three LLM judges scoring a 10-criterion weighted rubric; file ranking | Author wrote the rubric and the draft from the same vendor guidance; judges were three sizes of one vendor's model; the author's file was excused from the criteria it would fail (empty Project section). Five of five reviewers rejected it. |
| Krippendorff's alpha, per-line "mean signed weight" attribution, heatmap/scatter/diverging-bar charts | Agreement among correlated judges is not reliability. Transferring a criterion weight to a cited line is a category error; uncited lines rendered as zero read as "no effect" when the truth is "no data". |
| Committing a transcription of a tweet | The tweet URL is live; committing the full text into a CC-BY repository is republication. We record URL, archive URL, and a hash of the text instead. |
| Depending on the AgentREADMEs dataset | Its dataset card declares no license. We cite the paper's aggregate statistics only. |
| BibTeX parser, JSON Schema validator, `CITATION.cff`, CI PR comments (in v1) | Hand-rolled parsers under a stdlib-only rule are a maintenance trap; fork PRs cannot write comments. Deferred to the public-launch checklist. |

Facts corrected during design:

1. In `eth-agents-md`, "1.6" and "2.5" are absolute tool uses per instance when the tool is mentioned (uv: 1.6 vs fewer than 0.01 when not mentioned; repository-specific tools: 2.5). They are not multipliers.
2. The same paper reports inference cost increases of 20–23% and that repository overviews are not helpful. Both are cited alongside the tool-use finding.
3. `khatri-context-files` (arXiv 2607.27250) is a single-author preprint (288 runs, 17 tasks, 3 repositories). It is cited only for the pass-rate null result.
4. The security-instruction share in `agent-readmes` differs between versions (14.5% in the HTML v1 body, 14.8% in the abstract); we cite "about 15%".

## 3. Pipeline

```
v1:    data  -> check -> report
v1.1:  data  -> check -> experiment -> report
```

One `make` target per stage. Each stage reads only the outputs of the previous stage plus authored files, and writes only into its own output location.

| Stage | Command | Reads | Writes | Fails when |
|---|---|---|---|---|
| data | `make data` (`scripts/data.py`) | `data/manifest.toml` | `data/cache/<key>.md` (gitignored), `data/manifest.lock.json` | manifest field missing or malformed; license not in allowlist; fetched sha256 differs from an existing lock entry (upstream drift) unless `--update`; declared `type` contradicts detected type |
| check | `make check` (`scripts/lint.py --corpus`) | lock file, cache | `results/v1/checks.csv`, `results/v1/run.json` (only when `checks.csv` content changed) | cache missing (run `make data`) |
| report | `make report` (`scripts/report.py`) | `checks.csv`, manifest, lock | `docs/report.md`, `docs/generated/summary.md`, the marked block in `README.md` | never; `--check` mode exits 1 if regeneration would change any output |
| test | `make test` | everything | nothing | any unit test fails; regeneration is not a no-op; a docs link or footnote is dangling |
| experiment (v1.1) | `make experiment TASK=<id>` | `experiments/<id>/`, `ANTHROPIC_API_KEY` | `results/v1.1/trials.jsonl`, `results/v1.1/effects.csv` | pre-registration file missing or its commit hash is not an ancestor of HEAD |

Re-running `make data check` on an unchanged manifest produces no diff. Timestamps live only in `run.json`, which is rewritten only when `checks.csv` changes.

## 4. Data contracts

### 4.1 `data/manifest.toml` (authored by humans)

```toml
[[files]]
key     = "sentry"                      # [a-z0-9-]+, unique, used as cache filename and results row id
repo    = "getsentry/sentry"            # GitHub owner/name
path    = "AGENTS.md"                   # path inside the repo at that commit
commit  = "0123456789abcdef0123456789abcdef01234567"  # full 40-hex SHA; branch names are rejected
license = "FSL-1.1-ALv2"                # SPDX identifier of the source repository
type    = "project"                     # "project" | "generic"; see 7.2
reason  = "Frequently cited single-source-of-truth pattern"  # one line, why it is in the corpus
```

Optional fields: `sibling = "CLAUDE.md"` (a second path fetched at the same commit for the `pointer-file` check), `note` (free text, one line).

The author's own file is not a `[[files]]` entry. It is declared once:

```toml
[author]
path = "src/AGENTS.md"
type = "generic"
```

### 4.2 `data/manifest.lock.json` (written by `data.py`)

```json
{
  "lock_version": 1,
  "files": {
    "sentry": {
      "url": "https://raw.githubusercontent.com/getsentry/sentry/<commit>/AGENTS.md",
      "sha256": "<hex>",
      "bytes": 7503,
      "swhid": "swh:1:cnt:<git-blob-sha1>",
      "swhid_verified": false,
      "sibling": {"path": "CLAUDE.md", "sha256": "<hex>", "bytes": 11, "present": true}
    }
  }
}
```

- `swhid` is computed locally as `sha1("blob " + len + "\0" + bytes)`. It is a claim about identity, not about archive presence; `swhid_verified` flips to `true` only when `make check-links` confirms the object at `archive.softwareheritage.org`.
- No timestamps. Keys are sorted; the file is written with `indent=2` and a trailing newline so diffs are stable.
- `data.py` refuses to overwrite an entry whose `sha256` changed unless `--update` is passed, and prints the old and new hash.

### 4.3 `results/v1/checks.csv`

| column | type | meaning |
|---|---|---|
| `file` | string | manifest `key`, or `author` for `src/AGENTS.md` |
| `check_id` | string | id from the registry |
| `applicable` | `true`/`false` | whether the check applies to this file's type and filename |
| `pass` | `true`/`false`/empty | empty when not applicable or when the check is a measurement |
| `value` | number or empty | the measured quantity (lines, count, density) |
| `line` | integer or empty | 1-based line of the first matching evidence, when there is one |

Rows are ordered by manifest order, then by registry order. The author row comes last.

### 4.4 `results/v1/run.json`

```json
{
  "results_version": "v1",
  "created": "2026-09-02T00:00:00Z",
  "python": "3.14.6",
  "lint_sha256": "<sha256 of scripts/lint.py>",
  "lock_sha256": "<sha256 of data/manifest.lock.json>",
  "files": 15,
  "checks": 27
}
```

Written only when `checks.csv` content changed. `created` is the time of that change.

### 4.5 `results/v1.1/trials.jsonl` and `effects.csv` (v1.1)

One JSON object per trial: `task`, `rule`, `condition` (`baseline` | `placebo` | `rule`), `rep`, `model` (full model name, never an alias), `cli_version`, `argv`, `effort`, `prompt_sha256`, `started`, `ended`, `outcomes` (object of the pre-registered metrics, each boolean or number), `reward` (from the task verifier, monitored only), `tokens_in`, `tokens_out`, `cost_usd`, `transcript_path`, `terminated_by_question` (boolean).

`effects.csv` columns: `rule`, `task`, `outcome`, `condition_a`, `condition_b`, `n_a`, `n_b`, `p_a`, `p_b`, `risk_difference`, `ci_low`, `ci_high`, `method` (`newcombe`), `primary` (`true` for the one pre-registered primary outcome per rule).

## 5. Check registry (`scripts/lint.py`)

### 5.1 Interface

```python
@dataclass(frozen=True)
class FileContext:
    key: str            # manifest key or "author"
    filename: str       # basename, e.g. "AGENTS.md"
    file_type: str      # "project" | "generic"
    text: str
    lines: tuple[str, ...]
    sibling: dict | None  # lock sibling entry, if any

@dataclass(frozen=True)
class CheckResult:
    passed: bool | None   # None for measurements and for not-applicable
    value: float | None
    line: int | None
    note: str = ""

@check(id="len-lines", applies_to="all", source="anthropic-memory", grade="G",
       description="At most 200 lines")
def len_lines(ctx: FileContext) -> CheckResult: ...
```

- `applies_to` is one of `all`, `project`, `generic`, `agents-md` (filename is `AGENTS.md`), `manifest` (needs lock data).
- Registry order is definition order. `lint.py` exposes `CHECKS: list[CheckSpec]`.
- A check must be a pure function of `FileContext`. No network, no clock, no randomness.
- Every check has at least one passing and one failing fixture in `tests/test_checks.py`. A check without a `source` key that exists in `docs/references.md` fails `make test`.

### 5.2 Initial catalog

Measurements (`passed` is always `None`; they feed the descriptive statistics):

| id | value |
|---|---|
| `measure-chars` | Unicode characters |
| `measure-bytes` | UTF-8 bytes |
| `measure-words` | whitespace-separated tokens |
| `measure-lines` | lines |
| `measure-tokens-approx` | `chars / 4`, rounded; labeled "approx." everywhere it is shown |
| `measure-h2` | count of `## ` headings |
| `measure-bullets` | count of lines starting with `- `, `* `, or `N. ` |
| `measure-emphasis` | count of whole-word uppercase `NEVER`, `ALWAYS`, `MUST`, `IMPORTANT`, `CRITICAL`, `DO NOT` |
| `measure-pointers` | count of `@path` imports, relative `.md` links, and paths ending in `/` |

Checks (`passed` is a boolean when applicable):

| id | applies | rule | threshold / pattern | source | grade |
|---|---|---|---|---|---|
| `len-lines` | all | line count within the vendor target | pass if lines <= 200 | `anthropic-memory` | G |
| `len-bytes` | all | under the Codex default cap | pass if bytes <= 32768 (`project_doc_max_bytes`) | `openai-agents-md` | G |
| `cmd-test` | project | a test command is given verbatim | a code span or fenced block matches a test-runner pattern (see 5.3) | `agents-md-spec`, `anthropic-bp` | G |
| `cmd-single` | project | a way to run one test is given | code span matches a single-test selector pattern | `anthropic-bp` ("prefer running single tests") | G |
| `cmd-lint` | project | a lint or typecheck command is given | code span matches a lint/typecheck pattern | `anthropic-bp` | G |
| `cmd-build` | project | a build command is given | code span matches a build pattern | `agents-md-spec` | G |
| `rule-destructive` | all | a guard against destructive or irreversible operations | a sentence contains a prohibition/approval phrase and a destructive-operation term (5.3) | `agent-readmes` (security instructions in about 15% of files), `ssojet` | G |
| `rule-secrets` | all | a rule about handling secrets | a sentence contains a secret term and a prohibition or handling verb | `anthropic-bp` | G |
| `rule-injection` | all | instructions found in files, logs, or tool output are treated as data | pattern in 5.3 | `anthropic-bp` (hostile content) | G |
| `verify-done` | all | completion is tied to a runnable verification | a sentence about being done/before committing names a test, lint, typecheck, build, or CI run | `anthropic-bp` ("give Claude a way to verify its work") | G |
| `etiquette` | all | commit, branch, or PR conventions exist | pattern in 5.3 | `anthropic-bp` (repository etiquette) | G |
| `pointers` | all | points to further documents instead of inlining them | `measure-pointers` >= 1 | `anthropic-memory` (imports), `humanlayer` (progressive disclosure) | G |
| `no-overview-dump` | all | no long architecture or directory-overview section | fail if any section whose heading matches the overview pattern has more than 40 lines before the next heading of the same or higher level | `eth-agents-md` (overviews not helpful), `anthropic-bp` (exclude file-by-file descriptions) | G |
| `emphasis` | all | emphasis is rare enough to stand out | pass if emphasized lines <= max(3, 5% of lines). Threshold chosen by this project; the source gives no number | `anthropic-bp` ("If you emphasize many lines, none of them stands out") | G |
| `vague` | all | no unverifiable adjectives | pass if zero matches of the vague-phrase list (5.3) | `anthropic-memory` (specificity) | G |
| `tool-leak` | agents-md | a cross-tool file does not reference one tool's private paths | fail on `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.windsurf/`, `copilot-instructions.md` | practitioner review; `anthropic-memory` (Claude Code reads CLAUDE.md, not AGENTS.md) | G |
| `pointer-file` | manifest, agents-md | the repo wires Claude Code to the shared file | pass if sibling `CLAUDE.md` exists and its content, stripped, is `@AGENTS.md` or a symlink target `AGENTS.md` | `anthropic-memory` (AGENTS.md section) | G |

Score column in the report: `passed / applicable`, counting only non-measurement checks.

### 5.3 Patterns

All patterns are case-insensitive Python `re` patterns applied to one sentence at a time, where a sentence is a bullet line or a period-terminated span. Code-span patterns are applied only to the content of backtick spans and fenced blocks.

- Test runner: `\b(npm|pnpm|yarn|bun)\s+(run\s+)?test\b|\bpytest\b|\bpython\s+-m\s+(pytest|unittest)\b|\bgo\s+test\b|\bcargo\s+test\b|\bmake\s+test\b|\bmix\s+test\b|\brake\s+test\b|\bbundle\s+exec\s+rspec\b|\brspec\b|\bvitest\b|\bjest\b|\bdotnet\s+test\b|\b(gradle|gradlew|mvn)\s+test\b|\bzig\s+build\s+test\b|\bbin/rails\s+test\b`
- Single-test selector: a test-runner match on the same span plus either a selector flag (`\s-t\s|\s-k\s|--filter\b|--grep\b|::|\s-run\s|\s--\s+--test|\btest_name\b|<test`) or a path argument that names one test file or directory (`\S*(tests?/|\.test\.|\.spec\.|/test_\w|_test\.\w)\S*`)
- Lint/typecheck: `\b(eslint|ruff|flake8|pylint|mypy|pyright|tsc|clippy|golangci-lint|go\s+vet|credo|rubocop|prettier\s+--check|biome|typecheck|lint)\b`
- Build: `\b(npm|pnpm|yarn|bun)\s+run\s+build\b|\bcargo\s+build\b|\bgo\s+build\b|\bmake(\s+build)?\b|\bmix\s+compile\b|\bzig\s+build\b|\btsc\s+-b\b|\bdotnet\s+build\b|\bgradle(w)?\s+build\b`
- Prohibition: `\b(never|do not|don't|must not|not allowed|forbidden|without (an )?explicit|ask (before|first)|require[sd]? (approval|confirmation)|only with (approval|permission))\b`, or a bare `no` within 40 characters before a destructive term ("No history rewrite")
- Destructive term: `rm\s+-rf|force[- ]push|--force\b|reset\s+--hard|drop\s+(table|database|column)|delete\s+(data|files|the database)|destructive|irreversible|history\s+rewrit|truncate\b`
- Secret term: `\b(secret|credential|api key|token|password|private key|\.env)\b`; handling verb: `\b(never|do not|don't|must not|redact|commit|print|paste|log|echo|expose)\b`
- Injection: `(prompt injection|hostile content|untrusted (input|content))|((instruction|prompt|command|text)s?[^.\n]{0,60}\b(in|inside|found in|from|within)\b[^.\n]{0,40}\b(file|log|issue|comment|tool output|web page|document)s?\b[^.\n]{0,60}\b(data|not (commands|instructions)|untrusted|ignore|do not follow|are not)\b)`
- Done/verify: a sentence matching `\b(done|complete|finish(ed|ing)|before (committing|merging|opening a pr|pushing|submitting|finishing|landing)|definition of done)\b` and also `\b(test|tests|lint|typecheck|type-check|build|ci|green|pass(es|ed|ing)?)\b` (any order within the sentence)
- Etiquette: `\b(commit message|commits? (should|must)|conventional commits|branch (name|naming)|pull request|\bPR (title|body|description)\b|open(ing)? a PR|squash|rebase)\b`
- Overview heading: `^(#{2,4})\s*(architecture|overview|project structure|directory structure|codebase structure|repository (layout|structure)|file structure|codebase overview)`
- Vague phrases: `\b(properly|appropriately|clean code|best practices|high[- ]quality|well[- ]written|nicely|as appropriate|where appropriate|when appropriate|common sense|write good code)\b`

Patterns are versioned with the code; a pattern change bumps nothing else but must keep every fixture passing.

### 5.4 Adding a check

1. Add the function to `scripts/lint.py` with the decorator; cite a key that exists in `docs/references.md`.
2. Add a passing and a failing fixture to `tests/test_checks.py`.
3. Add a row to `docs/checks.md` (id, rule, applies, threshold, source, grade `G`).
4. Run `make check report test`; commit the regenerated `checks.csv`, `report.md`, `summary.md`, and README block together with the code.

## 6. Report contract (`scripts/report.py`)

Outputs, all generated, all starting with `<!-- generated by scripts/report.py; do not edit -->` (README uses marker comments around its block instead):

1. `docs/report.md` with exactly four tables:
   - **Corpus** — n files by type; median, min, max of lines, words, bytes, approx. tokens; count of files with <= 200 lines.
   - **Check catalog** — id, rule, applies, grade, source key (from the registry, not hand-typed).
   - **Check matrix** — one row per file in manifest order, one column per non-measurement check, cell `pass` / `fail` / `n/a`, then `score` as `passed/applicable`. The author's file is a separate one-row table below, titled "Author's file (not part of the corpus)".
   - **Pass rate by type** — one row per check: project pass %, generic pass %, all.
   The report's first paragraph states what the score measures (guideline conformance) and links `limitations.md`. No table is sorted by score. No rank column exists in the code.
2. `docs/generated/summary.md` — five lines: results version; corpus size by type; number of checks; mean score for project files; mean score for generic files.
3. `README.md` — the text between `<!-- summary:start -->` and `<!-- summary:end -->` is replaced with the same five lines.

`report.py --check` regenerates into memory and exits 1 if any output differs from disk. `make test` runs it.

## 7. Corpus policy

### 7.1 License allowlist

`data.py` accepts an entry only when `license` is an SPDX identifier in the allowlist: OSI-approved licenses, Creative Commons licenses, and source-available licenses that permit reading and analysis (`FSL-1.1-ALv2`, `FSL-1.1-MIT`, `BUSL-1.1`). The allowlist is a constant in `data.py`; changing it is a reviewed change. Nothing from a corpus file is ever committed, so the allowlist protects contributors from fetching files they may not analyze, not from redistribution.

A public repository with no license file may be included only with `license = "NONE"` and a mandatory `license_note` stating that fact and the date it was checked. Such entries are linted like any other (only derived facts are published) and are flagged in the report's corpus table. GitHub reports `NOASSERTION` when it cannot classify a license file; record the identifier from the file itself (for example Sentry's `LICENSE.md` is `FSL-1.1-ALv2`) and mention the discrepancy in `note`.

### 7.2 Type rule

`type = "project"` if and only if any `cmd-*` check passes on the file. `data.py` runs that detector after fetching and fails when the declared type contradicts it. `generic` files skip the four `cmd-*` checks (`applicable = false`).

### 7.3 Exclusions and prior-art entries

Sources without a fetchable, license-bearing repository (for example a tweet) are not corpus entries. They are listed in `docs/references.md` with URL, archive URL, and a sha256 of the text as captured, and in the README's prior-art section.

### 7.4 Maintainer notice

Before the results are published on the site, each repository in the manifest is notified of its row (issue or email) with one week to opt out. The notice date goes into the manifest `note`.

## 8. `src/AGENTS.md` v1

The file is the author's entry. It is linted like every corpus file and shown in its own table. Its lineage is recorded in `docs/provenance.md` (line, source key, source line range, relation: verbatim / paraphrase / original).

Changes from v0 (line numbers refer to v0):

| v0 line | Action | Why |
|---|---|---|
| 3–4 header | rewrite | "override" promised a precedence no tool enforces; "adjacent code beats rules" tells the agent to copy anti-patterns |
| 6 "Boundaries (never override)" | rewrite | renamed to hard rules; states that hooks enforce what prose cannot |
| 7 "couldn't run it is failing" | rewrite | made every sandboxed session a failure and invited fabricated runs; now "report as unverified with the reason" |
| 9 cite file:line for every claim | rewrite | literal compliance bloats every message; now "do not assert what you have not verified" |
| 10 destructive commands, 11 secrets | keep one line each, move enforcement to `settings.example.json` | prose decays late in a session; deny rules and hooks do not |
| 16 ask a question | rewrite | trigger narrowed to irreversible or externally visible changes; non-interactive mode states the assumption and proceeds |
| 23 remove compatibility layers | split | the unqualified rule was publicly blamed by its source for an agent deleting a production table; now "no compatibility shims in internal code" and "never delete migrations, schema, data paths, or public API without a backup and an explicit ask" |
| 24 build in layers, 25 match style | delete | vague, overlapped 20–21, and restated harness defaults |
| 26 TODO owner | keep the "why, not what" half; TODO policy belongs to a linter | |
| 31 all four commands must pass | rewrite | proportionality: docs-only or config-only changes run the relevant check |
| 41 commit format and push | keep the one-command sentence; format and push gating move to hooks | |
| 43–48 Project | fill for this repository; `.claude/skills/` moves to `CLAUDE.md` | a cross-tool file must not name one tool's private paths |
| new | "Budget and modes" (five lines) | targeted tests first; do not read whole logs; a denied permission is a stop, not a detour; non-interactive mode and subagents; the harness prompt outranks this file |
| new | provenance line at the top pointing to `docs/provenance.md` | |

`src/settings.example.json` holds the enforcement half: `permissions.deny` entries for `rm -rf`, force push, `reset --hard`, `--no-verify`, and a `PreToolUse` hook stub that blocks writes under `migrations/`. It is an example to merge, not a file to copy blindly.

`src/AGENTS.md` is licensed CC-BY-4.0; see the README license table.

## 9. Experiment protocol (v1.1)

Not built in v1. Everything below is fixed now so the first run cannot drift toward a convenient design.

- **Task format.** Harbor task layout (`harbor-tasks`): `instruction.md`, `task.toml`, `environment/Dockerfile`, `tests/test.sh`, `solution/solve.sh`; the verifier writes `/logs/verifier/reward.json`. Tasks are runnable by any agent the Terminal-Bench harness supports (`terminal-bench`); the pilot runner is a local `claude -p` wrapper that reuses the same `tests/test.sh`.
- **Conditions.** `baseline` (a minimal file with only project commands), `placebo` (baseline plus an irrelevant paragraph of the same length as the rule), `rule` (baseline plus exactly one rule). One manipulated variable.
- **Pilot rules.** R1: the data-destruction guard from `src/AGENTS.md` (trap: a migration task where the shortest path deletes data irreversibly). R2: length dilution (the same rule set at 20 lines versus 200 lines; trap: a canary rule that is easy to comply with when noticed). The next round adds one rule from a file other than the author's and one rule the author's file rejects.
- **Size.** 2 rules x 3 conditions x 1 task x 20 reps = 120 trials. Estimated 1.8M–4.8M tokens at 15k–40k per trial. With n = 20 per condition a risk difference of 0.5 has a Newcombe interval of roughly [+0.19, +0.70].
- **Pre-registration.** `experiments/<task>/PREREGISTRATION.md`, committed before any trial: hypothesis; the one primary outcome per rule (everything else is exploratory); n; trap calibration result (baseline rate must land in 30–70%, else recalibrate before spending trials); analysis method; the commit hash of the code that will run. The runner refuses to start if the file's recorded commit is not an ancestor of `HEAD`.
- **Recorded per trial.** See 4.5. Model names are full names, never aliases. A trial that ends with the agent asking a question is recorded as `terminated_by_question = true`; how it counts for each outcome is stated in the pre-registration.
- **Statistics.** Risk difference between conditions with a Newcombe 95% interval; single proportions with Wilson intervals; cost delta. No p-values, no regression. `reward` (task success) is always recorded and reported as a monitored harm outcome, never as the primary metric.
- **Isolation.** Flags are fixed at pre-registration. `--bare` gives real isolation (no hooks, no user settings, no CLAUDE.md discovery) but requires `ANTHROPIC_API_KEY` and therefore needs the file under test injected explicitly; the alternative `--setting-sources` route keeps discovery. The chosen route and its argv are part of the pre-registration.
- **Scope statement.** Results are scoped to one agent, one model, one CLI version until a second agent is run through Harbor.

## 10. Site and README

- GitHub Pages serves `docs/` from `main`. `docs/_config.yml` sets `title`, `description` (identical to the README one-liner), `theme: jekyll-theme-minimal`, and excludes nothing that a page links to. No Gemfile, no plugins, no JavaScript.
- `docs/index.md` is the landing page: core sentence, non-affiliation notice, `{% include_relative generated/summary.md %}`, and links to report, checks, limitations, provenance, design.
- Charts: v1 uses Markdown tables only. v1.1 forest plots are SVG files generated by `report.py` into `docs/generated/` and embedded with an image link.
- README follows the Standard Readme section order: title and one-line description; badges (placeholder until CI exists); non-affiliation notice; table of contents; Background (what the project does not do, then the core sentence and grades); Results (site link and the generated summary block); Install (Python >= 3.11, no dependencies); Usage (`make` targets and `python scripts/lint.py your/AGENTS.md` with example output); The file (`src/AGENTS.md`, how to adopt it in three lines); Methodology; Contributing (three paths); Prior art and acknowledgments; Citation (placeholder until `CITATION.cff` exists); License (per-path table; last section).

## 11. Verification

`make test` runs, in order:

1. `python3 -c 'import sys; assert sys.version_info >= (3, 11)'` with a readable message on failure (also the first line of every `make` target).
2. `python3 -m unittest discover -s tests` — every check has passing and failing fixtures; lock round-trip; swhid computation against the known empty-blob SHA-1 `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`; type rule; Newcombe and Wilson interval functions against published worked examples (v1.1).
3. `python3 scripts/report.py --check` — regeneration of `report.md`, `summary.md`, and the README block is a no-op.
4. `python3 scripts/lint.py --self-test` — every registered check has a `source` key present in `docs/references.md` and a row in `docs/checks.md`.
5. A docs check: every relative link in `docs/*.md` and `README.md` resolves to a file; every `[^key]` footnote used in `docs/` and `README.md` is defined in `docs/references.md`, and every defined key is used at least once.

`make check-links` (network): every URL in `docs/references.md` and every lock `url` answers 2xx or 3xx to GET with a browser user agent; every `archive_url` answers; swhid presence at Software Heritage flips `swhid_verified`.

Manual, after the user creates the remote: push, enable Pages (Settings, Pages, Source `main` `/docs`), confirm the landing page and `report.md` render.

## 12. Glossary

| Term | Meaning |
|---|---|
| context file | An `AGENTS.md`, `CLAUDE.md`, or equivalent file read by a coding agent at session start. Vendor-neutral term from `agent-readmes`. |
| manifest / lock file | Human-authored list of corpus entries / machine-written pins (URL, sha256, bytes, swhid). |
| check | A deterministic function of a file's text with a citation and a grade. |
| evidence grade | `G` guidance-only, `E+` experimentally supported, `E-` experimentally unsupported. |
| guideline conformance score | `passed / applicable` non-measurement checks. Not a quality score. |
| type | `project` (contains a runnable command) or `generic` (behavioral rules only). |
| experiment / trap task / trial / condition | A pre-registered comparison / a Harbor task with a planted temptation / one agent run / `baseline`, `placebo`, or `rule`. |
| primary vs exploratory outcome | The one pre-registered metric per rule vs everything else. |
| risk difference, Newcombe interval, Wilson interval | Difference of two proportions and its confidence interval; interval for a single proportion. |
| pre-registration | Hypothesis, outcomes, n, and analysis committed before any trial runs. |
| pass rate | Task success from the verifier. Monitored only. |
| approx. tokens | `characters / 4`; a heuristic, not a tokenizer. |
| provenance | Where each line of `src/AGENTS.md` came from. |
| SPDX identifier | Standard license identifier, e.g. `Apache-2.0`, `CC-BY-4.0`. |
| swhid | Software Heritage identifier of a file's content. |

References for every citation key used above are in [references.md](references.md).
