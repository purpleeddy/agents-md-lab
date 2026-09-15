# Verification-observation diagnostic (2026-09-08)

## Purpose and status

This is a separate, read-only explanation of the saved verification-observation
states in the 2026-09-07 pilot. It does not alter the frozen runner, scorer,
review transport, raw archive, public projection, protocol, or stored metrics.
It does not re-score a row, execute a documented check, recover verification
evidence, import a review, or make a model-behavior, condition-effect, ranking,
or adoption claim.

The diagnostic reads every published run rather than selecting only unknown
rows. Its generated JSON is a derivative explanation: every stored
`unverified` outcome remains `unverified`.

## Invocation and deterministic output

```sh
python3 scripts/verification_diagnostics.py \
  --collection data/verification-budget/20260907-090636/collection \
  --publication experiments/verification-budget/results-2026-09-07.json \
  > /tmp/verification-observation-diagnostic.json
```

The program writes deterministic, privacy-safe JSON to standard output only.
The redirect is a caller-owned new derived artifact; the program itself creates,
modifies, and deletes no file. The generated JSON is copied byte-for-byte from
validated standard output into the dated historical artifact and is not
hand-edited. Future runs use a fresh output path and do not overwrite that
historical artifact.

## Validation boundary

Before it diagnoses any row, the tool requires every published run ID to be a
unique `run-<digits>` name and to match the direct archive run-directory set. It
opens only five fixed, regular files in each archive run directory:
`meta.json`, `metrics.json`, `observations.json`, `transcript.jsonl`, and
`verify_client.py`. It compares each to the matching public raw-artifact hash
before parsing the row. Missing files, malformed artifacts, hash drift,
duplicate or unsafe IDs, and run or file symlinks make the diagnostic explicitly
unavailable; it does not silently omit, relabel, or repair a row.

It also requires the frozen supervisor/scorer source hash, the checked-in
scenario manifest hash, the archived verification-client hash, and their public
pin counterparts to match. The saved client path is treated only as a lexical
string: it is never resolved, opened, localized, or otherwise dereferenced.
This means the diagnostic preserves ambiguity for relative or symlink-sensitive
forms instead of claiming general filesystem-equivalence to the frozen matcher.

The transcript is rejected when any nonblank JSONL line or the required
assistant/tool shape is malformed. For a well-formed row, the diagnostic reuses
the frozen transcript parser, documented-check map, shell-structure parser, and
event-marker helper. Its strict lexical endpoint comparison reports whether an
event marker is present, whether the raw argv differs, and whether the returned
tool text binds the recorded output. It reports only safe run IDs, fixed status
values, hashes, event ordinals, and fixed cause labels. It never serializes raw
commands, absolute paths, account or session identifiers, tool IDs, reports, or
output text.

A parser-rejected pipe or redirection token or character is an explanation of
why the frozen parser remained conservative. It does not prove that a shell
pipeline or redirection occurred, that an endpoint executed, or that a test
passed. Likewise, a matching request prefix plus a trailing syntactic suffix
only explains a strict raw-argv mismatch; it is never upgraded into execution or
coverage evidence.

## Instrumentation fixture history

The initial focused
`python3 -m unittest tests.test_verification_diagnostics` command ran 20 tests
and reported two failures. Both were synthetic compound-endpoint fixtures whose
event marker was adjacent to the output rather than on its own line, which does
not satisfy the frozen marker helper. The fixtures were corrected to add that
newline while keeping the positive distinct-segment and negative reused-slot
assertions. This was instrumentation-fixture work only: it made no provider
call, changed no retained row, and establishes no statement about model
behavior.

## Generated result

The generated [all-row JSON](observation-diagnostics-2026-09-08.json) is the
byte-identical standard output from the validated original-archive command. It
is 56,873 bytes with sha256
`f56eca7ad825a4b6be9f74036c8903574e2e0805763bde60f84f7c92b0d33900`.
The public-projection input hash is
`eed65dcf792f280ddf96eba4714afcce31fbbbed09cbd446c20f20899f26a4ab`;
the frozen supervisor/scorer hash is
`df3383769ab4c2451e9228d7ddd573097f48360455412a65a3d21cd4641276f8`;
and the diagnostic source hash is
`3400c2fc747f25fcf970771025f25a4fcf98bf2cbc55c411597003eab7834ab1`.
The retained private archive tree hash remains
`b4e9c53e1c625adb12b8aa805520f58018fffe510614276941072e75fb6567da`.

All 36 public rows matched their stored evidence and coverage statuses. The
diagnostic reports 24 observed and 12 unverified verification-evidence rows;
coverage remains 16 passed, 8 failed, and 12 unverified. Its safe explanatory
categories are 24 normal rows, 9 parser-rejected-shell rows, 2 endpoint-linkage
rows, and 1 row with both. It records 8 unmatched events across 3 rows and 12
parser-rejected direct observations across 10 rows. The direct-observation form
counts are 10 pipe-token-or-character and 5 redirection-token-or-character
records; a single observation can have more than one form.

An earlier preliminary manual tally of 13 direct observations was incorrect.
The deterministic all-row diagnostic count is 12. This is a counting correction
in a separate explanatory derivative, not a changed stored metric, a recovered
verification result, or a model-behavior finding.

After the fixture correction, `python3 -m unittest tests.test_verification_diagnostics` passed 20 tests.
The full `python3 -m unittest` suite passed 360 tests, `python3 scripts/compare.py --check` passed,
and `python3 scripts/experiment.py --dry-run` passed its 12 fixtures. The diagnostic command passed
against both the original and a relocated retained archive with exit code 0, no standard error,
byte-identical output, and no absolute-path leakage. These are instrumentation and
archive-portability checks, not tests of model behavior or candidate effectiveness.
