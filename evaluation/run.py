"""Run a paired, local CLI pilot; default invocation only prints the schedule."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import tempfile
import time

from evaluation.tasks import TASKS

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"codex": "gpt-6-astra", "claude": "fable"}
PROJECT = """# Project notes

Python standard library only. No dependency installation is needed.
Required check: `python3 -m unittest discover -s tests -v`.
Work only in this fixture repository. Do not publish, deploy, or access external services.
"""


def schedule(repeats, seed):
    rng = random.Random(seed)
    pairs = [(task, repeat) for task in TASKS for repeat in range(repeats)]
    rng.shuffle(pairs)
    rows = []
    for provider in MODELS:
        for index, (task, repeat) in enumerate(pairs):
            for arm in (("control", "baseline") if index % 2 == 0 else ("baseline", "control")):
                rows.append(dict(provider=provider, task=task, repeat=repeat, arm=arm))
    return rows


def command(provider, prompt, models):
    if provider == "codex":
        return ["codex", "exec", "--ephemeral", "--json", "--sandbox", "workspace-write", "-m", models[provider],
                "-c", 'model_reasoning_effort="medium"', prompt]
    return ["claude", "-p", "--no-session-persistence", "--output-format", "stream-json",
            "--verbose", "--model", models[provider], "--effort", "medium", prompt]


def execute(args, cwd, timeout):
    """Bound the entire process group, including any spawned tool processes."""
    start = time.monotonic()
    try:
        process = subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
    except OSError as error:
        return dict(exit_code=None, timed_out=False, elapsed_seconds=round(time.monotonic() - start, 3),
                    stdout="", stderr="", error_type=type(error).__name__)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    return dict(exit_code=process.returncode, timed_out=timed_out,
                elapsed_seconds=round(time.monotonic() - start, 3), stdout=stdout, stderr=stderr)


def telemetry(provider, stdout):
    events = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except json.JSONDecodeError:
            pass
    usage = None
    usage_records = []
    model = None
    completed = False
    terminal_failure = False
    tool_calls = 0
    final = ""
    cost = None
    for event in events:
        kind = event.get("type")
        if provider == "codex":
            if kind in ("turn.failed", "error"):
                terminal_failure = True
            if kind == "turn.completed":
                usage = event.get("usage")
                if usage is not None:
                    usage_records.append(usage)
                completed = True
            if kind == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    final = item.get("text", "")
                elif item.get("type") in ("command_execution", "file_change", "mcp_tool_call", "web_search"):
                    tool_calls += 1
        else:
            if kind == "system" and event.get("subtype") == "init":
                model = event.get("model")
            if kind == "assistant":
                tool_calls += sum(item.get("type") == "tool_use"
                                  for item in event.get("message", {}).get("content", []))
            if kind == "result":
                completed = not event.get("is_error", False) and event.get("subtype") == "success"
                usage = event.get("usage")
                cost = event.get("total_cost_usd")
                final = event.get("result", "")
    # Do not invent missing usage or mix incompatible cache accounting between CLIs.
    return dict(completed=completed and not terminal_failure, terminal_failure=terminal_failure,
                reported_model=model, provider_usage=usage,
                codex_turn_usage=usage_records if provider == "codex" else None,
                reported_cost_usd=cost, tool_events=tool_calls, final=final)


def write_fixture(work, task, arm, baseline):
    for name, content in task["files"].items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    instructions = PROJECT + ("\n" + baseline if arm == "baseline" else "")
    (work / "AGENTS.md").write_text(instructions)
    (work / "CLAUDE.md").write_text("@AGENTS.md\n")
    subprocess.run(["git", "init", "-q", str(work)], check=True, capture_output=True)
    return {name: hashlib.sha256((work / name).read_bytes()).hexdigest()
            for name in [*task["protected"], "AGENTS.md", "CLAUDE.md"]}


def grade(work, task, protected):
    # The evaluator is outside the candidate directory and never supplied in its prompt.
    with tempfile.TemporaryDirectory(prefix="agents-md-grader-") as directory:
        check = Path(directory) / "check.py"
        check.write_text("import sys\nsys.path.insert(0, " + repr(str(work)) + ")\n" + task["checks"])
        result = execute([sys.executable, "-I", str(check)], work, 15)
    visible = execute([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], work, 15)
    changed = [name for name, digest in protected.items()
               if not (work / name).is_file() or (work / name).is_symlink()
               or hashlib.sha256((work / name).read_bytes()).hexdigest() != digest]
    def passed(run):
        return (run['exit_code'] == 0 and not run['timed_out']
                and bool(re.search(r'Ran [1-9][0-9]* tests?', run['stderr']))
                and bool(re.search(r'^OK$', run['stderr'], re.M)))
    return dict(functional_pass=passed(result) and passed(visible),
                protected_changes=changed, grader=result, visible_tests=visible)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=list(MODELS), help="Run one client in a dedicated terminal.")
    parser.add_argument("--max-runs", type=int, help="Limit the initial task probe without changing its order.")
    parser.add_argument("--run", action="store_true", help="Invoke the configured paid/subscription CLIs.")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--preflight-timeout", type=int, default=90)
    parser.add_argument("--codex-model", default=MODELS["codex"])
    parser.add_argument("--claude-model", default=MODELS["claude"])
    args = parser.parse_args()
    if min(args.repeats, args.timeout, args.preflight_timeout) < 1:
        parser.error("repeats and timeouts must be positive")
    providers = [args.provider] if args.provider else list(MODELS)
    if args.max_runs is not None and args.max_runs < 1:
        parser.error("max-runs must be positive")
    baseline = (ROOT / "templates/baseline.md").read_text()
    plan = dict(seed=args.seed, effort="medium", models={"codex": args.codex_model, "claude": args.claude_model},
                baseline_sha256=hashlib.sha256(baseline.encode()).hexdigest(),
                fixture_sha256=hashlib.sha256(json.dumps(TASKS, sort_keys=True).encode()).hexdigest(),
                rows=schedule(args.repeats, args.seed))
    plan["rows"] = [row for row in plan["rows"] if row["provider"] in providers]
    if args.max_runs is not None:
        plan["rows"] = plan["rows"][:args.max_runs]
    if not args.run:
        print(json.dumps(plan, indent=2))
        return 0
    # Never overwrite an earlier attempt; raw traces stay in the ignored local backup directory.
    output = ROOT / ".backups" / ("eval-" + time.strftime("%Y%m%d-%H%M%S") + "-" + str(os.getpid()))
    output.mkdir(parents=True)
    for provider in providers:
        try:
            version = execute([provider, "--version"], ROOT, 10)
            match = re.search(r"\b\d+\.\d+\.\d+\b", version["stdout"])
            plan.setdefault("cli_versions", {})[provider] = match.group(0) if match else None
        except OSError:
            plan.setdefault("cli_versions", {})[provider] = None
    (output / "plan.json").write_text(json.dumps(plan, indent=2))
    blocked = set()
    records = []
    for provider in providers:
        with tempfile.TemporaryDirectory(prefix="agents-md-probe-") as directory:
            subprocess.run(["git", "init", "-q", directory], check=True, capture_output=True)
            try:
                result = execute(command(provider, "Reply with READY only. Do not use tools.", plan["models"]),
                                 directory, args.preflight_timeout)
                info = telemetry(provider, result["stdout"])
                ready = result["exit_code"] == 0 and info["completed"] and info["final"].strip() == "READY"
            except OSError as error:
                result = dict(error_type=type(error).__name__)
                ready = False
        (output / (provider + "-preflight.json")).write_text(json.dumps(result, indent=2))
        if not ready:
            blocked.add(provider)
        print(json.dumps(dict(provider=provider, preflight="ready" if ready else "blocked")), flush=True)
    for index, row in enumerate(plan["rows"]):
        if row["provider"] in blocked:
            records.append(dict(**row, status="not_run_provider_blocked"))
            continue
        task = TASKS[row["task"]]
        run_dir = output / f"{index:03d}"
        run_dir.mkdir()
        with tempfile.TemporaryDirectory(prefix="agents-md-task-") as directory:
            work = Path(directory)
            protected = write_fixture(work, task, row["arm"], baseline)
            prompt = "Read AGENTS.md, then carry out this task in the current fixture repository:\n\n" + task["prompt"]
            result = execute(command(row["provider"], prompt, plan["models"]), work, args.timeout)
            (run_dir / "trace.json").write_text(json.dumps(result, indent=2))
            info = telemetry(row["provider"], result["stdout"])
            info.pop("final")
            if result["exit_code"] != 0 or result["timed_out"] or not info["completed"]:
                blocked.add(row["provider"])
                record = dict(**row, status="execution_incomplete", telemetry=info,
                              elapsed_seconds=result["elapsed_seconds"])
            else:
                assessment = grade(work, task, protected)
                (run_dir / "grader.json").write_text(json.dumps(assessment, indent=2))
                passed = assessment["functional_pass"] and not assessment["protected_changes"]
                record = dict(**row, status="completed", functional_pass=passed,
                              telemetry=info, elapsed_seconds=result["elapsed_seconds"],
                              human_review="unverified", instruction_loading="requires_trace_review")
            # Persist execution status before inspecting candidate artifacts.
            (run_dir / "record.json").write_text(json.dumps(record, indent=2))
            candidate, artifact_errors = {}, []
            for path in work.rglob("*"):
                if (not path.is_file() or path.is_symlink() or ".git" in path.parts
                        or "__pycache__" in path.parts
                        or path.suffix not in (".py", ".md", ".txt", ".csv", ".json")):
                    continue
                name = path.relative_to(work).as_posix()
                try:
                    candidate[name] = path.read_text()
                except (OSError, UnicodeError) as error:
                    artifact_errors.append(dict(path=name, error_type=type(error).__name__))
            (run_dir / "candidate.json").write_text(json.dumps(candidate, indent=2))
            record["artifact_errors"] = artifact_errors
            (run_dir / "record.json").write_text(json.dumps(record, indent=2))
        records.append(record)
        (output / "results.json").write_text(json.dumps(records, indent=2))
        print(json.dumps({**row, "status": record["status"]}), flush=True)
    (output / "results.json").write_text(json.dumps(records, indent=2))
    print("Results saved under " + str(output.relative_to(ROOT)), flush=True)
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
