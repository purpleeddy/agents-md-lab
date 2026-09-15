# Contributing

## Source and generated output

The canonical public file is `templates/baseline.md`. The root `AGENTS.md` is an exact copy of the public baseline so this repository uses the same instructions it offers to others. Keep both files identical when updating the baseline. English content lives in `site/content/en.json`; Korean website translations live in `site/content/ko.json`. Keep code examples, comments, identifiers, and the downloadable artifact English.

Edit the shared layout and assets under `site/`. Generated files under `docs/` are never edited by hand. Build them with:

```sh
python3 scripts/build_site.py
```

The generator intentionally supports only the baseline's constrained headings and structured editorial data. Do not add a general Markdown parser or a new dependency for ordinary content changes.

## Required checks

```sh
python3 scripts/check_all.py
```

This command runs the active unittest suite, generated-output verification, snapshot integrity, and the three original checks inside a temporary full-history historical checkout. It preserves historical assertions and optional-cache skips. Missing historical Git objects fail with an actionable diagnostic. No private backup or private dataset is required.

Node must be available for the current JavaScript interaction tests; they use only Node's built-in modules. `docs/.nojekyll` makes the published output entirely static. The existing publishing folder is retained; Jekyll template processing is not required.

For focused iteration:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py --check
```

There are no separate lint, typecheck, or format commands. Report each check as passed, failed, or unverified; do not describe skipped coverage as passed. Sandbox-denied socket tests must remain failures until run in an environment that permits them; do not bypass permissions.

## Editorial review

For every baseline or translation edit, follow [the content review procedure](REVIEW.md). Recheck the affected principles when provider guidance changes or a real task exposes a failure. Keep the latest substantive review in that document; passing site tests does not establish instruction quality.

Each principle uses a flat Markdown bullet list, with one decision per item and its conditions intact. Korean translations must use the same item count and order. The website renders both as semantic lists and keeps the connected story explaining the purpose, decisions, and limits in prose. Use the shared fictional cart task throughout. Write for someone who has used a coding agent but may not know terms such as caller or regression; explain those terms where they first matter. Narrative belongs in paragraphs, not code blocks. The semantic IDs are scope, context, implementation, verification, authorization, and data, derived from the baseline headings. Use `preference` for a chosen working style, `guidance` for directly supported documentation, and `observed` only for a specifically identified experiment. A citation does not establish measured effectiveness.

Review both language versions in the same change and update their matching revision fields. Korean rules include a full translation and a sourceSha256 of the exact UTF-8 list body returned by the baseline extractor. Update this hash only after reviewing the translation against the new source; the generator checks it but never refreshes it. A matching hash does not establish translation accuracy. Add a changelog entry for a baseline change. Keep one reading page per language. Preserve stable rule IDs and matching section anchors across languages; earlier routes must link to the corresponding sections in the full document. Examples explain decisions without asserting results that were not measured.

Keep project settings and placeholders out of the public artifact. Local-context examples and tool installation guidance belong only on the website. Version 1.0.0 is the first public release. Keep route aliases linked to the current explanations. Model-specific suggestions must name their scope, and must not imply measured benefits on other models.

## Browser review

Check English and Korean at 320, 768, and 1440 CSS pixels, keyboard-only navigation, 200% zoom, reduced motion, JavaScript disabled, and clipboard denial. Check copy/download bytes and language switching at the same section. Check contrast and overflow, and inspect screenshots. Automated HTML tests cannot establish that a page is comfortable to read.

## Historical and security boundaries

Do not edit the frozen tree under `legacy/research/`; verify it against `legacy/manifest.json`. Its original tests run in isolation. Do not commit `.backups/`, ignored research data, credentials, or unlicensed corpus content.

Keep `.claude/settings.json`, `scripts/hook_guard.py`, and the guard tests active. The existing wrapper can succeed when its target script is absent, so removing the target silently changes protection. Permission settings and hooks require an explicit user request to change.

Publishing, pushing, deployment, dependency changes, and security-setting changes require task authorization. Existing settings are not that authorization.
