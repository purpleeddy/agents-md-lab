# Pilot execution status

Date: 2026-09-15. Status: partial pilot; no general efficiency claim established.

The main experiment planned six synthetic Python tasks × two arms × three repetitions × two clients: 72 task runs. Separate Orca terminals ran the configured clients against disposable fixtures. Four calibration runs are excluded. Raw traces and backups remain local and are not published.

| Client | Control completed / planned | Baseline completed / planned | Functional checks |
| --- | --- | --- | --- |
| Codex, requested gpt-6-astra, medium | 5 / 18 | 4 / 18 | All 9 completed runs passed |
| Claude, requested fable, medium | 18 / 18 | 18 / 18 | All 36 completed runs passed |

Codex attempted a tenth run but did not complete it; the runner left the remaining 26 runs unattempted after that interruption. The interruption's cause has not been established in this review. Incomplete runs are not successful coding outcomes. Earlier initialization failures were followed by successful runs through Orca after the runtime environment changed; this does not isolate a single cause for those earlier failures.

The machine-readable [aggregate](summary.json) records both completed and incomplete pairs. Claude's control arm reported 2,095,511 total tokens and the baseline arm 2,016,394, a descriptive reduction of approximately 3.8%. Median elapsed times were 64.224 and 58.111 seconds respectively. These observations are not a causal or statistically established efficiency improvement. Codex's incomplete schedule does not support a full-arm comparison.

Token totals include reported cache usage according to each client's schema; token totals are not billed cost. Existing global configurations, cache state, execution order, concurrent host activity, and the small task sample limit interpretation. Six tasks with repeated runs are not 18 independent task types. Cross-client token comparisons are not meaningful here.

Functional checks cover visible tests, independent requirements, and protected-file integrity. They do not establish equal code quality or reduced human review effort. Comprehensive trace review and human review remain unverified. No efficiency claim has been added to the website, and the baseline is unchanged.

Baseline SHA-256: `259d0ce9dd68eded547b2582df18ae8626762be459541bf17e38067e4991abbe`.

See the [pilot protocol](README.md) for fixtures, arm isolation, scheduling, grading, and usage accounting. Future work should resolve the Codex interruption, collect a complete comparable schedule, and review behavior before drawing conclusions.
