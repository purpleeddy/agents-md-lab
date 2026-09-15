# Version 1.0.0 validation

Date: 2026-09-15. Checkpoint prepared for Git publication; further experiments are deferred at the user's request.

## Checks

- `python3 scripts/build_site.py`: passed; 51 static files generated.
- `python3 -m unittest discover -s tests -v`: passed; 70 tests.
- `python3 scripts/build_site.py --check`: passed; 51 generated files verified.
- `python3 scripts/check_all.py`: passed; active tests, snapshot integrity, historical generated output, and 12 historical fixtures passed. Historical suite: 471 tests, with two original optional-cache skips. Those two checks remain unverified.
- `git diff --check` and working-tree review: passed before commit.
- Browser rendering and accessibility: unverified in this checkpoint; no new visual inspection was performed.
- General model effectiveness, code quality, and human effort: unverified. See [the partial pilot](evaluation/RESULTS.md); additional model runs are deferred.

## Included changes and preservation

The public baseline and bilingual single-page website are released as version 1.0.0. The English artifact has 24 bullets across six sections and SHA-256 `259d0ce9dd68eded547b2582df18ae8626762be459541bf17e38067e4991abbe`.

The earlier project reset moved research into the frozen `legacy/research/` snapshot. Retired paths are listed in [the migration inventory](legacy/retired-paths.json). Snapshot integrity passed; Git history is retained. Earlier public version 2.0.0 and 3.0.0 entries and downloads were removed at the user's request. No additional source files were deleted for this checkpoint.

Raw experiment traces, private data, and recovery backups are excluded through `.gitignore`. The existing settings, permission guard, and guard tests are retained. No dependencies or permission settings were changed for this checkpoint. The user authorized committing and pushing the current work to the repository's existing remote; no separate deployment command is included.
