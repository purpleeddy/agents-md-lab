# Local CLI efficiency pilot

This pilot asks whether adding the public baseline improves outcomes or reduces effort within each configured coding client. It does not rank Codex against Claude. Its six small Python fixtures validate the measurement procedure; they are not representative enough to prove general development efficiency.

## Design fixed before model runs

- Control: the client's normal configuration plus fixture project notes.
- Treatment: the same setup plus the exact public `templates/baseline.md`.
- Six tasks, three repetitions, two arms, separately for Codex and Claude: 72 planned task runs.
- Requested effort: medium for both clients. Effort labels are not comparable across providers.
- Default requested models: `gpt-6-astra` and `fable`. Claude's resolved model is recorded from its initialization event. Pin a full model ID with `--claude-model` when available; an alias can change.
- A fixed seed shuffles task/repetition pairs. The arm order alternates, and each pair runs consecutively. Each attempt starts with fresh files, a fresh Git repository, and no resumed conversation.
- Client configurations, permission controls, hooks, and global instructions remain enabled. These are installed-client comparisons, not isolated base-model experiments. Do not change settings between arms. Cached prompts, provider routing, and uncontrolled host configuration remain possible confounders.

The six fixtures cover interval boundaries, pagination, a compatible keyword-only interface extension, CSV parsing, narrowly scoped normalization, and default-value merging. All starting implementations pass their visible tests but fail independent requirements; reference solutions pass both. Only fixture input files are supplied to the candidate. Graders and reference answers stay outside that directory. This separation is not a hardened defense against a malicious candidate reading other host files.

Task prompts explicitly require regression tests in a new file and preserve the existing test file byte-for-byte, matching the protected-file grader. This controls the task contract but may reduce differences attributable to the baseline's verification rules. These fixtures do not test deployment approval, secret handling, long tasks, UI design, or an agent's response to genuine human clarification. Add held-out real tasks before making broader claims; do not tune wording against all evaluation tasks and then reuse them as independent evidence.

## Run

From the repository root, print the schedule without invoking any model:

```sh
python3 -m evaluation.run
```

On a host where both configured CLIs can initialize, connect, and edit a disposable repository, run the paid/subscription pilot:

```sh
python3 -m evaluation.run --run
```

Codex child sessions select the workspace-write sandbox needed for the authorized fixture edits. The runner does not alter persistent permission settings, disable hooks, bypass host restrictions, read credential files, install dependencies, or deploy anything. A successful text probe does not prove edit permission. An incomplete task execution stops that provider's remaining work and is recorded separately from a functional failure. Resolve infrastructure failures before interpreting the comparison. Do not bypass a denied action to obtain a score.

`--provider codex` or `--provider claude` runs one client in a dedicated terminal. `--max-runs 2` limits a calibration to the first pair; keep those calibration records separate from the complete run. `--repeats 1` selects a smaller 24-run trial. `--timeout` bounds each task invocation, default 600 seconds; `--preflight-timeout` defaults to 90 seconds. A timeout terminates the invocation's process group. A subsequent invocation creates a new attempt directory; it does not silently retry or overwrite earlier results.

## What is measured

The runner records the baseline and fixture hashes, requested model/effort, CLI versions, schedule, elapsed time, raw provider usage, reported model where available, and tool events. It preserves candidate files for review. Each run has independent functional checks plus visible tests and hashes of protected files. A zero exit code without completed model output is not a completed task. A zero grader exit without executed tests is not a pass.

Raw traces and candidates stay under ignored `.backups/eval-*`. They may contain host-specific metadata and must be inspected and sanitized before sharing. Do not commit raw logs automatically. Review traces to verify instruction loading and required-check execution; those facts are not established merely by writing an AGENTS.md file or passing the external grader.

Provider token fields are retained without inventing missing values. Codex cached input is a subset of its input usage, not additional input; per-turn usage records are retained if there is more than one turn. Claude's reported cost is a client estimate, not a verified invoice. Missing cost or usage is unknown, not zero. Tool-event definitions differ between clients, so compare arms within one client. [Codex JSON events](https://developers.openai.com/codex/noninteractive), [Claude programmatic output](https://code.claude.com/docs/en/headless).

## Interpretation

First review correctness, required-check execution, scope compliance, and code quality. Blind the arm labels for human code review. External tests cover only their assertions; they do not establish readability or complete authorization compliance. Human correction counts and review time require an actual standardized human review and are currently unmeasured.

Then compare paired task outcomes and token/time differences within each client. Include failed attempts and timeouts in the accounting; do not report only successful runs. Show completion rate alongside aggregate effort per accepted result, and retain the task-level differences so a cheap failure cannot look like an improvement. Do not average the two providers' results into one score. Do not claim superiority from a few favorable tasks or from the pilot's point estimates without uncertainty and a larger, held-out task sample.

Document an unchanged result as readily as an improvement. The public instructions stay at version 1.0.0 until evidence warrants a content change. See [the current execution status](RESULTS.md) and [the content review procedure](../REVIEW.md).

## Inspect a completed run

Combine the two full-run directories, excluding calibration directories:

```sh
python3 -m evaluation.summarize .backups/eval-CODEX-RUN .backups/eval-CLAUDE-RUN
```

Replace the illustrative directory names with those printed by the runners. The summary rejects duplicate trials and mismatched baseline/fixture/model configurations. It preserves failed attempts and unknown usage, and reports raw paired differences. A summary is not a significance test or approval to publish a superiority claim.
