# Research preservation and migration

The original tracked project is frozen unchanged in `research/`. `manifest.json` records its starting commit, SHA-256 hashes, POSIX modes, and symlink targets. `retired-paths.json` lists every original active path retired during the redesign; its contents remain in the frozen tree.

The preserved project measured earlier instruction files. Its results do not establish the effectiveness of the public 2.0.0 baseline.

## Verification

Run `python3 scripts/check_all.py` from the repository root. The runner verifies the manifest, restores the historical checkout from retained local Git history into a temporary directory, and executes the original unittest suite, comparison check, and experiment dry-run. The active suite is discovered separately.

A fresh full-history clone supplies the required public source and history. Missing required Git objects fail before testing. Original optional corpus caches remain optional, with their unavailable coverage explicitly reported as unverified. No private data is needed.

## Local recovery

The implementation session created a complete Git history bundle at `.backups/pre-redesign.bundle` and copied ignored research data to `.backups/local-data/`. These paths are local-only and are intentionally excluded from version control. Do not publish them. They are recovery material, not prerequisites for normal validation.

Before retiring any original paths, the bundle was verified and restored into a temporary directory; the hashes and modes of all 332 tracked files matched. Historical checks were also run in an isolated checkout: comparison generation and 12 dry-run fixtures passed, while five of 471 unittest cases errored because the environment denied Unix socket binding. Unavailable original corpus-cache checks were reported separately.

To recover, clone the local bundle into a new temporary directory and compare its files against the manifest before using it. Copy local supplemental data only into an appropriately private location. Never reset the active working tree to perform a recovery test.

## Interface retirement

The public text evaluator, rule-count comparison interface, live star count, and experiment-first homepage were retired. Their source and tests remain frozen here. Former research page URLs now point readers to a contextual archive notice. The active guard script and settings remain unchanged.
