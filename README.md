# agents-md-lab

Evidence-graded linter and experiment harness for AGENTS.md / CLAUDE.md context files.

<!-- badges: CI and license badges are added at public launch -->

> Not affiliated with the AGENTS.md specification or the Agentic AI Foundation.

## Table of contents

- [Background](#background)
- [Results](#results)
- [Install](#install)
- [Usage](#usage)
- [The file](#the-file)
- [Methodology](#methodology)
- [Contributing](#contributing)
- [Prior art and acknowledgments](#prior-art-and-acknowledgments)
- [Citation](#citation)
- [License](#license)

## Background

Context files (`AGENTS.md`, `CLAUDE.md`, `copilot-instructions.md`) are in tens of thousands of repositories, and almost all advice about them is taste. The two controlled studies we know of could not detect a task-success difference from these files at all, while they raised inference cost by about 20%, and found that repository overviews do not help but explicit tool instructions are followed[^eth-agents-md][^khatri-context-files].

So this project does not do the things people expect a benchmark to do:

- **No task-success benchmark.** It is insensitive at any affordable sample size.
- **No quality ranking of files.** There is a score column and no rank column anywhere.
- **No LLM judges.** Every check is a deterministic function with a unit test and a citation.

What it does: **lint context files with deterministic, source-cited checks, and test contested rules with pre-registered behavioral experiments, so that the file we recommend is backed by evidence rather than taste.**

Every check carries an evidence grade:

| Grade | Meaning |
|---|---|
| `G` | Backed only by vendor guidance or published literature |
| `E+` | An experiment in this repository found the rule changes agent behavior as intended |
| `E-` | An experiment found no effect or a harmful one; the check stays, marked, so people stop cargo-culting it |

All checks are `G` today. The project's only two jobs are to grow the catalog and to move checks from `G` to `E+` or `E-`.

## Results

Full tables live on the site: **https://qwerfunch.github.io/agents-md-lab/** (report, check catalog, limitations, provenance, design).

<!-- summary:start -->
- Results version: `v1` · corpus snapshot lock `6dad6355876e`
- Corpus: 16 files (13 project, 3 generic); the author's file is reported separately
- Checks: 17 deterministic checks, all grade `G` (guidance-only) until experiments run
- Mean guideline-conformance score, project files: 60%
- Mean guideline-conformance score, generic files: 56%
<!-- summary:end -->

The score is guideline conformance (checks passed / checks applicable). It is not a quality score, and files of different types are not comparable. Read [docs/limitations.md](docs/limitations.md) before quoting a number.

## Install

Python 3.11 or newer and GNU make. No dependencies.

```sh
git clone https://github.com/qwerfunch/agents-md-lab.git
cd agents-md-lab
make test
```

Experiments (v1.1, not yet released) additionally need `ANTHROPIC_API_KEY`.

## Usage

Lint your own file:

```sh
python3 scripts/lint.py path/to/AGENTS.md
```

```
path/to/AGENTS.md  (type: project)
  pass  len-lines          value=52
  pass  len-bytes          value=5057
  pass  cmd-test           line=49
  FAIL  cmd-single
  pass  rule-destructive   line=10
  pass  rule-secrets       line=11
  FAIL  rule-injection
  pass  verify-done        line=7
  ...
  score 15/17  (guideline conformance, grade G checks only; see docs/limitations.md)
```

`line=` points at the first sentence that satisfied a check; a `FAIL` with no line means nothing matched. Add `--type generic` to skip the command checks for a rules-only file, or `--format json|csv` for machine output.

Reproduce the corpus results:

| Command | What it does |
|---|---|
| `make data` | Fetches every manifest entry at its pinned commit into `data/cache/` (gitignored) and pins hashes in `data/manifest.lock.json` |
| `make check` | Runs every check over the corpus and the author's file into `results/v1/checks.csv` |
| `make report` | Regenerates `docs/report.md`, `docs/generated/summary.md`, and the summary block above |
| `make test` | Unit tests for every check, lock and manifest rules, docs links and citation keys, and a no-op regeneration check |
| `make check-links` | Network check of every URL in the references and lock, plus Software Heritage presence |

Re-running `make data check` on an unchanged manifest produces no diff.

## The file

[`src/AGENTS.md`](src/AGENTS.md) is the file this project recommends. It is linted with the same code as every corpus file and reported in its own table, outside the corpus. Every line's origin is in [docs/provenance.md](docs/provenance.md); the rules borrowed from other files are attributed there.

To adopt it:

1. Copy `src/AGENTS.md` to your repository root and fill in the `Project` section.
2. Add a `CLAUDE.md` containing `@AGENTS.md` so Claude Code reads the same file[^anthropic-memory].
3. Merge [`src/settings.example.json`](src/settings.example.json) into `.claude/settings.json`: it enforces the destructive-operation and `--no-verify` rules with permission denials and a hook, because prose decays late in a session and hooks do not.

## Methodology

- **Checks** are deterministic regular-expression functions over a file's text. Each cites a source and is listed in [docs/checks.md](docs/checks.md). Thresholds without a published number (emphasis density) are marked as chosen by this project.
- **Corpus** entries are pinned by commit SHA and content hash in `data/manifest.toml` and `data/manifest.lock.json`. Files are never redistributed; results contain booleans, counts, and line numbers only.
- **Experiments** (v1.1) will compare `baseline`, `baseline + placebo`, and `baseline + one rule` on Harbor-format trap tasks, with one pre-registered primary outcome per rule, n = 20 per condition, and risk differences with Newcombe intervals. Task success is recorded only as a harm signal.
- **Threats to validity**, in short: checks measure wording, not intent; the corpus is a curated sample; the maintainer wrote both the checks and the recommended file. The long version is [docs/limitations.md](docs/limitations.md). The implementation contract is [docs/design.md](docs/design.md).

## Contributing

Three ways in, smallest first:

1. **Add a file to the corpus.** Append an entry to `data/manifest.toml` (repo, path, full commit SHA, SPDX license, type, one-line reason), run `make data check report test`, and commit the regenerated results with it.
2. **Add a check.** One decorated function in `scripts/lint.py`, one passing and one failing fixture in `tests/test_checks.py`, one row in `docs/checks.md` with a citation key from `docs/references.md`.
3. **Add an experiment task** (v1.1): a Harbor-format task plus its pre-registration.

`make test` must pass. Repositories in the corpus are notified of their row before results are published and can opt out.

## Prior art and acknowledgments

Vendor guidance from Anthropic[^anthropic-bp][^anthropic-memory] and OpenAI[^openai-agents-md], the AGENTS.md specification[^agents-md-spec], HumanLayer's guide[^humanlayer], and the three studies cited above[^agent-readmes][^eth-agents-md][^khatri-context-files] shaped the check catalog. The recommended file paraphrases rules from the Karpathy-derived `CLAUDE.md` by Forrest Chang[^karpathy-multica] and from Marcos Hernanz's published `AGENTS.md`[^hernanz-agents-md]. `FerroxLabs/agents-md`[^ferrox-agents-md] is the nearest existing project. The README follows Standard Readme[^standard-readme].

## Citation

A `CITATION.cff` will be added at public launch. Until then, cite the repository URL and the commit you used.

## License

| Path | License |
|---|---|
| `scripts/`, `tests/`, `Makefile` | Apache-2.0 ([LICENSE](LICENSE)) |
| `src/AGENTS.md`, `src/CLAUDE.md`, `src/settings.example.json` | CC-BY-4.0 |
| `docs/`, `results/` | CC-BY-4.0 |
| `data/cache/` (never committed) | each source's own license, recorded in `data/manifest.toml` |

Full citation entries: [docs/references.md](docs/references.md).

[^anthropic-bp]: See docs/references.md.
[^anthropic-memory]: See docs/references.md.
[^openai-agents-md]: See docs/references.md.
[^agents-md-spec]: See docs/references.md.
[^humanlayer]: See docs/references.md.
[^agent-readmes]: See docs/references.md.
[^eth-agents-md]: See docs/references.md.
[^khatri-context-files]: See docs/references.md.
[^karpathy-multica]: See docs/references.md.
[^hernanz-agents-md]: See docs/references.md.
[^ferrox-agents-md]: See docs/references.md.
[^standard-readme]: See docs/references.md.
