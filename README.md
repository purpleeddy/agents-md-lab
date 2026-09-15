# agents-md-lab

An English AGENTS.md with a walkthrough for people starting to build software with a coding agent.

[Read the guide](https://purpleeddy.github.io/agents-md-lab/) · [Korean website](https://purpleeddy.github.io/agents-md-lab/ko/) · [English baseline](templates/baseline.md)

## Start here

1. Read the [baseline](templates/baseline.md) and review each rule against your workflow.
2. Copy it into a new `AGENTS.md`, or merge it deliberately with your existing instructions. Keep a backup of an existing file; do not blindly overwrite it.
3. For Claude Code, add `@AGENTS.md` to a separate `CLAUDE.md`. Review an existing file before adding an import.

The public baseline has no setup fields or repository-specific configuration. Keep commands and project-specific requirements in your project instructions. This repository's own maintenance instructions remain separate. Both website languages copy the same English artifact. Repository documents, examples, and code comments are English; Korean is available in translated website content.

## What this provides

Each language has one reading page: the complete AGENTS.md comes first, followed by a cart-bug walkthrough, an example report, usage notes, sources, and version history. Navigation links stay within that document. Earlier URLs remain entry points to the corresponding sections.

Six principles cover scope, context, implementation, verification, authorization, and data. The artifact uses concise bullet points; the website pairs them with full prose explanations. The walkthrough follows one fictional task: fixing an item subtotal that does not update when its quantity changes. Each section explains a different decision, from understanding the request to reporting what was checked. Korean readers see each English list followed by its matching Korean list.

These instructions describe a chosen way of working. They cannot enforce tool permissions, and we have not measured whether version 1.0.0 saves tokens, speeds up development, or improves a particular model.

The refinement draws on [OpenAI's Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), [Claude Code instruction guidance](https://code.claude.com/docs/en/best-practices#write-an-effective-claudemd), and [Claude Fable 5.1 prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1). The [Claude Code memory documentation](https://code.claude.com/docs/en/memory#agentsmd) explains the import mechanism. Model-specific remedies are conditional notes, not universal requirements.

## Develop locally

Python 3.11+ is required. The implementation uses its standard library. Node runs the JavaScript interaction tests and historical JavaScript checks; no npm dependencies are needed.

```sh
python3 scripts/build_site.py
python3 scripts/build_site.py --check
python3 -m unittest discover -s tests -v
python3 scripts/check_all.py
```

Open `docs/index.html` in a browser to inspect the generated site. GitHub Pages serves the same static files. There is no backend, package installation, telemetry, remote font, or third-party runtime request.

Use a full-history clone for complete historical verification. The aggregate checker does not need local backups or private data; missing required history fails with a diagnostic. Original optional corpus-cache checks may be unavailable and are reported as unverified. A successful command exit does not mean skipped coverage was verified.

## Efficiency pilot

The [local CLI pilot](evaluation/README.md) compares the baseline against the same configured client without it. [Execution status](evaluation/RESULTS.md) separates infrastructure failures from measured outcomes; no efficiency result is claimed without completed, reviewed comparisons.

## Preserved research

The [frozen research tree](legacy/research/README.md) preserves the previous project. [The migration record](legacy/README.md) explains integrity checks, recovery, and retired paths. The original tests are executed separately without weakened assertions.

See [CONTRIBUTING.md](CONTRIBUTING.md) for content editing, generation, and validation. [The content review procedure](REVIEW.md) records why each instruction remains useful, how proposed changes are challenged, and what still needs model testing.

## License

MIT for original code, documentation, and data; third-party material retains its original license. Unlicensed corpus caches and private research records are not redistributed. This project is not affiliated with OpenAI, Anthropic, the AGENTS.md specification, or the Agentic AI Foundation.
