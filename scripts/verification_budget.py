#!/usr/bin/env python3
"""Instrumented, pre-registered pilot for verification-budget instructions.

The paid ``run`` command is deliberately separate from the free ``simulate``,
``score`` and ``summarize`` commands.  It never interprets a command-line flag
as human approval.  ``run --dry-run`` is the free way to inspect the exact
schedule, pins and reservation rule before a human authorizes a collection.
"""

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import random
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import experiment


REPO_ROOT = Path(__file__).resolve().parent.parent
PILOT_ROOT = REPO_ROOT / "experiments" / "verification-budget"
SCENARIO_ROOT = PILOT_ROOT / "scenarios"
DEFAULT_MODEL = experiment.DEFAULT_MODEL
DEFAULT_MAX_TURNS = 80
PER_RUN_COST_USD = 3.0
BATCH_COST_USD = 25.0
REPLICATES = 3
SCHEDULE_SEED = "verification-budget-pilot-v1"
ORIGIN_LIVE = "real_model_run"
ORIGIN_SYNTHETIC = "synthetic_fixture"


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def json_hash(value):
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tree_hash(root):
    """Use the historical deterministic tree algorithm for whole-tree provenance."""
    return experiment.sha256_tree(Path(root))


def relevant_hash(root, paths):
    """Hash declared relevant inputs, including missing paths, in a stable order.

    A check's relevance list belongs to the scenario manifest.  A client request
    cannot choose it, which prevents an agent from claiming that an edit was
    irrelevant after it has seen a result.
    """
    root = Path(root)
    digest = hashlib.sha256()
    for rel in sorted(paths):
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if not path.exists():
            digest.update(b"MISSING\0")
            continue
        if path.is_file():
            digest.update(b"FILE\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
            continue
        digest.update(b"DIR\0")
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            if "__pycache__" in child.parts or child.name.endswith(".pyc"):
                continue
            child_rel = child.relative_to(root).as_posix()
            digest.update(child_rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(child.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def copy_tree(source, destination):
    source = Path(source)
    destination = Path(destination)
    if destination.exists():
        raise ValueError("refusing to copy a fixture over an existing directory: %s" % destination)
    shutil.copytree(source, destination)


def apply_overlay(work, overlay):
    """Copy a checked-in overlay over a fresh seed without executing its code."""
    overlay = Path(overlay)
    for source in sorted(path for path in overlay.rglob("*") if path.is_file()):
        destination = Path(work) / source.relative_to(overlay)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def scenario_names():
    return tuple(sorted(path.name for path in SCENARIO_ROOT.iterdir() if path.is_dir()))


def load_manifest(name):
    if name not in scenario_names():
        raise ValueError("unknown verification-budget scenario: %s" % name)
    manifest = read_json(SCENARIO_ROOT / name / "scenario.json")
    if manifest.get("name") != name:
        raise ValueError("scenario manifest name does not match directory: %s" % name)
    acceptance = manifest.get("acceptance", {})
    if not isinstance(acceptance.get("test_count"), int) or acceptance["test_count"] <= 0:
        raise ValueError("scenario acceptance must declare a positive test_count: %s" % name)
    if not scenario_path(name, acceptance.get("evaluator", "")).is_file():
        raise ValueError("scenario evaluator is missing: %s" % name)
    return manifest


def scenario_path(name, *parts):
    return SCENARIO_ROOT / name / Path(*parts)


def documented_check_map(manifest):
    checks = {}
    for check in manifest["checks"]:
        argv = tuple(check["argv"])
        if check["id"] in checks:
            raise ValueError("duplicate documented check id: %s" % check["id"])
        checks[check["id"]] = {
            "id": check["id"],
            "argv": argv,
            "relevant_paths": tuple(check["relevant_paths"]),
            "required": bool(check.get("required", False)),
            "covers": tuple(check.get("covers", [check["id"]])),
        }
    return checks


def check_for_argv(checks, argv):
    argv = tuple(argv)
    return next((check for check in checks.values() if check["argv"] == argv), None)


def split_chain(argv):
    """Split the only two shell-style separators the endpoint supports.

    This function accepts already tokenized argv from the socket client.  Any
    other shell grammar is rejected for audit rather than executed through a
    shell.  The separate records make ``a && b`` two verification executions.
    """
    groups = [[]]
    connectors = []
    for item in argv:
        if item in ("&&", ";"):
            if not groups[-1]:
                return None
            connectors.append(item)
            groups.append([])
            continue
        if item in ("|", "||", "&", "<", ">") or any(token in item for token in ("$(", "`", "|", ">", "<")):
            return None
        groups[-1].append(item)
    if not groups[-1]:
        return None
    return groups, connectors


def process_group_status(pgid):
    if not isinstance(pgid, int) or pgid <= 0:
        return "unverified"
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return "exited"
    except PermissionError:
        return "unverified"
    return "still_present"


def run_documented_check(work, check, timeout=120, on_started=None):
    """Execute one manifest-allowed argv and preserve state either side of it."""
    work = Path(work)
    before_tree = tree_hash(work)
    before_relevant = relevant_hash(work, check["relevant_paths"])
    started = utc_now()
    process = subprocess.Popen(
        list(check["argv"]),
        cwd=str(work),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    if on_started is not None:
        on_started(process.pid)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    ended = utc_now()
    output = stdout + stderr
    return {
        "check_id": check["id"],
        "argv": list(check["argv"]),
        "started_utc": started,
        "ended_utc": ended,
        "before_tree_sha256": before_tree,
        "after_tree_sha256": tree_hash(work),
        "before_relevant_sha256": before_relevant,
        "after_relevant_sha256": relevant_hash(work, check["relevant_paths"]),
        "returncode": process.returncode,
        "timed_out": timed_out,
        "output_sha256": sha256_bytes(output.encode("utf-8")),
        "output": output,
        "owned_pgid": process.pid,
        "owned_process_group_status": process_group_status(process.pid),
        "source": "runner_parent",
    }


class VerificationSupervisor:
    """A local Unix-socket supervisor that observes, but never limits, checks.

    The model can request only one of the manifest's documented argv values.  It
    cannot provide a state hash or write the evidence ledger.  The parent keeps
    observations in memory and writes them only after the agent exits.
    """

    def __init__(self, socket_path, work, checks, timeout=120):
        self.socket_path = Path(socket_path)
        self.work = Path(work)
        self.checks = checks
        self.timeout = timeout
        self.events = []
        self._stop = threading.Event()
        self._thread = None
        self._listener = None
        self._active_pgid = None
        self._active_lock = threading.Lock()
        self._closed_cleanly = False

    def start(self):
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(self.socket_path))
        listener.listen(8)
        listener.settimeout(0.2)
        self._listener = listener
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def close(self):
        self._stop.set()
        if self._listener is not None:
            self._listener.close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        with self._active_lock:
            active_pgid = self._active_pgid
        if self._thread is not None and self._thread.is_alive() and active_pgid:
            try:
                os.killpg(active_pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self._thread.join(timeout=2)
        self._closed_cleanly = self._thread is None or not self._thread.is_alive()
        if self.socket_path.exists():
            self.socket_path.unlink()
        return self._closed_cleanly

    def _serve(self):
        while not self._stop.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            with connection:
                incoming = connection.makefile("r", encoding="utf-8")
                outgoing = connection.makefile("w", encoding="utf-8")
                line = incoming.readline()
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    response = {"status": "rejected", "reason": "invalid_json"}
                else:
                    response = self.request(request)
                outgoing.write(json.dumps(response) + "\n")
                outgoing.flush()

    def request(self, request):
        requested = request.get("argv") if isinstance(request, dict) else None
        if not isinstance(requested, list) or not all(isinstance(item, str) for item in requested):
            event = self._unsupported([], "invalid_argv")
            return {"status": "rejected", "event_ids": [event["event_id"]]}
        parsed = split_chain(requested)
        if parsed is None:
            event = self._unsupported(requested, "unsupported_shell_structure")
            return {"status": "rejected", "event_ids": [event["event_id"]]}
        groups, connectors = parsed
        events = []
        for index, argv in enumerate(groups):
            previous = events[-1] if index else None
            if (
                index and connectors[index - 1] == "&&"
                and (previous.get("executed") is not True or previous.get("returncode") != 0)
            ):
                skipped = self._unsupported(argv, "short_circuited_after_failure", index)
                skipped["executed"] = False
                skipped["request_argv"] = requested
                events.append(skipped)
                continue
            check = check_for_argv(self.checks, argv)
            if check is None:
                events.append(self._unsupported(argv, "argv_not_documented", index))
            else:
                def started(pgid):
                    with self._active_lock:
                        self._active_pgid = pgid

                event = run_documented_check(self.work, check, timeout=self.timeout, on_started=started)
                with self._active_lock:
                    self._active_pgid = None
                event.update({
                    "event_id": uuid.uuid4().hex,
                    "segment_index": index,
                    "request_argv": requested,
                    "executed": True,
                })
                self.events.append(event)
                events.append(event)
        output = "".join(event.get("output", "") for event in events)
        returncode = next((event.get("returncode") for event in reversed(events) if event.get("executed") is True), 2)
        if returncode is None:
            returncode = 2
        return {
            "status": "ok" if all("reason" not in event for event in events) else "rejected",
            "event_ids": [event["event_id"] for event in events],
            "output": output,
            "returncode": returncode,
        }

    def _unsupported(self, argv, reason, index=0):
        event = {
            "event_id": uuid.uuid4().hex,
            "segment_index": index,
            "argv": list(argv),
            "source": "runner_parent",
            "observation_status": "uncertain_requires_audit",
            "reason": reason,
            "executed": None,
        }
        self.events.append(event)
        return event


CLIENT_SOURCE = '''#!/usr/bin/env python3
import argparse
import json
import socket
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--socket", required=True)
parser.add_argument("argv", nargs=argparse.REMAINDER)
args = parser.parse_args()
if args.argv[:1] == ["--"]:
    args.argv = args.argv[1:]
connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
connection.connect(args.socket)
with connection:
    outgoing = connection.makefile("w", encoding="utf-8")
    incoming = connection.makefile("r", encoding="utf-8")
    outgoing.write(json.dumps({"argv": args.argv}) + "\\n")
    outgoing.flush()
    response = json.loads(incoming.readline())
print(response.get("output", ""), end="")
print("[verification-event-ids=%s]" % ",".join(response.get("event_ids", [])))
if response.get("status") != "ok" and response.get("returncode") is None:
    print("verification endpoint rejected request", file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(response.get("returncode", 2))
'''


def write_client(path):
    Path(path).write_text(CLIENT_SOURCE, encoding="utf-8")


def endpoint_brief(manifest, client_path, socket_path):
    commands = [" ".join(check["argv"]) for check in manifest["checks"]]
    rendered = "\n".join("- " + command for command in commands)
    return (
        "\n\nVerification observation for this pilot:\n"
        "Use the supplied local client for any documented verification command so the runner can "
        "record its before/after state. It observes checks; it does not enforce the scenario budget.\n"
        f"Client: python3 {client_path} --socket {socket_path} -- <command>\n"
        "Only these verification argv values are documented:\n"
        f"{rendered}\n"
        "A top-level `&&` or `;` may join documented commands. Other shell structure is rejected "
        "for audit. A direct command remains visible in the transcript but is unverified evidence.\n"
    )


def parse_events(text):
    return experiment.parse_events(text)


def transcript_bash_calls(text):
    """Return Bash calls joined to their own tool result, never to a neighbouring call."""
    _, calls, results = experiment.collect_transcript(parse_events(text))
    by_id = {result.get("tool_use_id"): result for result in results}
    return [
        {
            "id": call.get("id"),
            "command": call["input"].get("command", ""),
            "result": by_id.get(call.get("id")),
        }
        for call in calls if call.get("name") == "Bash"
    ]


def raw_endpoint_match(raw_command, client_path, request_argv):
    """Match an endpoint call structurally without treating arbitrary shell text as proof."""
    try:
        tokens = shlex.split(raw_command)
    except ValueError:
        return False
    if "--" not in tokens:
        return False
    divider = tokens.index("--")
    if divider < 2:
        return False
    client = Path(tokens[1]).resolve() if len(tokens) > 1 else None
    return client == Path(client_path).resolve() and tokens[divider + 1:] == list(request_argv)


def direct_verification_segments(raw_command, checks):
    """Count transcript-visible verification commands without converting uncertainty to pass."""
    try:
        tokens = shlex.split(raw_command)
    except ValueError:
        return [{"raw": raw_command, "status": "uncertain_requires_audit"}]
    parsed = split_chain(tokens)
    if parsed is None:
        return [{"raw": raw_command, "status": "uncertain_requires_audit"}]
    groups, _ = parsed
    segments = []
    for group in groups:
        check = check_for_argv(checks, group)
        if check is not None:
            segments.append({"check_id": check["id"], "argv": group, "status": "transcript_only"})
    return segments


def output_text(value):
    """Normalize subprocess output, including TimeoutExpired byte streams."""
    return experiment.decode_stream(value)


def unittest_test_count(output):
    """Read the standard-library unittest count without interpreting report prose."""
    for line in output.splitlines():
        fields = line.strip().split()
        if len(fields) >= 4 and fields[0] == "Ran" and fields[2] in ("test", "tests") and fields[3] == "in":
            try:
                count = int(fields[1])
            except ValueError:
                return None
            return count if count >= 0 else None
    return None


def evaluate_basic_state(copied, final_tree, timeout):
    """Capture a runner-owned syntax invariant independently of acceptance tests."""
    copied = Path(copied)
    sources = [
        path.relative_to(copied).as_posix()
        for path in sorted(copied.rglob("*.py"))
        if "__pycache__" not in path.parts
    ]
    result = {
        "final_tree_sha256": final_tree,
        "source_paths": sources,
        "timeout_seconds": timeout,
        "executed_by": "runner_owned_basic_state",
    }
    if not sources:
        result.update({"status": "unverified", "returncode": None, "output": "no Python sources found"})
    else:
        try:
            process = subprocess.run(
                [sys.executable, "-m", "py_compile", *sources],
                cwd=str(copied),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            result.update({
                "status": "timeout",
                "returncode": None,
                "output": output_text(error.stdout) + output_text(error.stderr),
            })
        except OSError as error:
            result.update({"status": "unverified", "returncode": None, "output": str(error)})
        else:
            result.update({
                "status": "passed" if process.returncode == 0 else "failed",
                "returncode": process.returncode,
                "output": process.stdout + process.stderr,
            })
    result["output_sha256"] = sha256_bytes(result["output"].encode("utf-8"))
    return result


def evaluate_acceptance(work, manifest, timeout=120):
    """Run the independent evaluator on a temporary final-tree copy.

    This happens after a live model exits (and during free simulation).  Scoring
    merely reads this artifact and never executes work-tree code.
    """
    work = Path(work)
    evaluator = manifest["acceptance"]
    evaluator_source = scenario_path(manifest["name"], evaluator["evaluator"])
    final_tree = tree_hash(work)
    result = {
        "evaluator_source": str(evaluator_source.relative_to(REPO_ROOT)),
        "evaluator_source_sha256": sha256_file(evaluator_source),
        "declared_test_count": evaluator["test_count"],
        "final_tree_sha256": final_tree,
        "final_relevant_sha256": relevant_hash(work, evaluator.get("relevant_paths", [])),
        "timeout_seconds": timeout,
        "executed_on": "temporary_final_copy",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="verification-budget-evaluate-") as temporary:
            copied = Path(temporary) / "work"
            copy_tree(work, copied)
            basic_state = evaluate_basic_state(copied, final_tree, timeout)
            environment = dict(os.environ)
            environment["WORK_DIR"] = str(copied)
            process = subprocess.run(
                [sys.executable, str(evaluator_source)],
                cwd=str(copied),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=environment,
            )
        output = process.stdout + process.stderr
    except subprocess.TimeoutExpired as error:
        output = output_text(error.stdout) + output_text(error.stderr)
        result.update({"status": "timeout", "returncode": None, "output": output})
    except OSError as error:
        result.update({"status": "unverified", "returncode": None, "output": str(error)})
    else:
        result.update({
            "status": "passed" if process.returncode == 0 else "failed",
            "returncode": process.returncode,
            "output": output,
        })
    result["output_sha256"] = sha256_bytes(result["output"].encode("utf-8"))
    result["actual_test_count"] = unittest_test_count(result["output"])
    result["expected_test_count"] = evaluator["test_count"]
    if "basic_state" not in locals():
        basic_state = {
            "status": "unverified",
            "returncode": None,
            "final_tree_sha256": final_tree,
            "source_paths": [],
            "output": "acceptance setup did not reach basic-state evaluation",
            "output_sha256": None,
            "executed_by": "runner_owned_basic_state",
        }
    result["basic_state"] = basic_state
    return result


def baseline_artifact(source, baseline, timeout=120):
    """Capture a harness-generated baseline before an agent has touched a work tree."""
    source = Path(source)
    result = {
        "id": baseline.get("id", baseline["kind"]),
        "kind": baseline["kind"],
        "argv": list(baseline["argv"]),
        "source_tree_sha256": tree_hash(source),
        "harness_generated": True,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="verification-budget-baseline-") as temporary:
            copied = Path(temporary) / "baseline"
            copy_tree(source, copied)
            process = subprocess.run(
                baseline["argv"], cwd=str(copied), capture_output=True, text=True, timeout=timeout
            )
    except subprocess.TimeoutExpired as error:
        result.update({
            "capture_status": "timeout",
            "returncode": None,
            "output": output_text(error.stdout) + output_text(error.stderr),
        })
    except OSError as error:
        result.update({"capture_status": "unverified", "returncode": None, "output": str(error)})
    else:
        result.update({
            "capture_status": "recorded",
            "returncode": process.returncode,
            "output": process.stdout + process.stderr,
        })
    result["output_sha256"] = sha256_bytes(result["output"].encode("utf-8"))
    return result


def baseline_definitions(manifest):
    if manifest.get("baselines"):
        return manifest["baselines"]
    return [manifest["baseline"]] if manifest.get("baseline") else []


def generate_baselines(name, manifest, timeout):
    return [
        baseline_artifact(scenario_path(name, definition["source"]), definition, timeout)
        for definition in baseline_definitions(manifest)
    ]


def baseline_prompt(baselines):
    if not baselines:
        return ""
    sections = []
    for baseline in baselines:
        sections.append(
            "Harness baseline `%s` ran before this task from its pinned source. argv: `%s`; "
            "return code: %s; output sha256: %s.\nOutput:\n%s" % (
                baseline["id"], " ".join(baseline["argv"]), baseline["returncode"],
                baseline["output_sha256"], baseline["output"]
            )
        )
    return "\n\n" + "\n\n".join(sections) + "\n"


def baseline_status(manifest, artifact):
    """Validate every expected pre-agent baseline without treating an empty list as evidence."""
    definitions = baseline_definitions(manifest)
    if not definitions:
        return "not_applicable"
    if not isinstance(artifact, dict) or not isinstance(artifact.get("baselines"), list):
        return "unverified"
    expected = {definition.get("id", definition["kind"]): definition for definition in definitions}
    actual = artifact["baselines"]
    if len(actual) != len(expected):
        return "unverified"
    for captured in actual:
        if not isinstance(captured, dict):
            return "unverified"
        definition = expected.get(captured.get("id"))
        if definition is None:
            return "unverified"
        if (
            captured.get("kind") != definition["kind"]
            or captured.get("argv") != list(definition["argv"])
            or captured.get("source_tree_sha256") != tree_hash(scenario_path(manifest["name"], definition["source"]))
            or captured.get("harness_generated") is not True
            or captured.get("capture_status") != "recorded"
            or isinstance(captured.get("returncode"), bool)
            or not isinstance(captured.get("returncode"), int)
            or not isinstance(captured.get("output"), str)
            or captured.get("output_sha256") != sha256_bytes(captured["output"].encode("utf-8"))
        ):
            return "unverified"
    return "recorded"


def changed_paths(seed, work):
    seed_files = experiment.list_files(seed)
    work_files = experiment.list_files(work)
    all_paths = sorted(set(seed_files) | set(work_files))
    return [
        rel for rel in all_paths
        if rel not in seed_files or rel not in work_files or seed_files[rel].read_bytes() != work_files[rel].read_bytes()
    ]


def protected_path_changes(seed, work, prefixes):
    return [
        path for path in changed_paths(seed, work)
        if any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)
    ]


def exclude_unchanged_harness_files(paths, work, harness_files):
    """Exclude only parent-injected files whose final bytes still match the pre-run copy."""
    if not isinstance(harness_files, dict):
        return list(paths)
    unchanged = set()
    for rel, expected_sha256 in harness_files.items():
        path = Path(work) / rel
        if (
            isinstance(rel, str)
            and isinstance(expected_sha256, str)
            and path.is_file()
            and sha256_file(path) == expected_sha256
        ):
            unchanged.add(rel)
    return [path for path in paths if path not in unchanged]


def changed_harness_files(work, harness_files):
    """Detect injected instruction changes that the historical diff helper ignores."""
    if not isinstance(harness_files, dict):
        return []
    changes = []
    for rel, expected_sha256 in harness_files.items():
        path = Path(work) / rel
        if (
            not isinstance(rel, str)
            or not isinstance(expected_sha256, str)
            or not path.is_file()
            or sha256_file(path) != expected_sha256
        ):
            changes.append(rel)
    return changes


def review_annotations(run_dir, observed_event_ids):
    """Accept an external review only when it binds this final text and evidence."""
    path = Path(run_dir) / "review.json"
    if not path.exists():
        return {}
    payload = read_json(path)
    if payload.get("provenance") != "label_blinded_model_review":
        return {}
    transcript = Path(run_dir) / "transcript.jsonl"
    if not transcript.exists():
        return {}
    final_text = next((event.get("result", "") for event in reversed(parse_events(
        transcript.read_text(encoding="utf-8", errors="replace")
    )) if event.get("type") == "result"), "")
    if not isinstance(final_text, str) or payload.get("final_text_sha256") != sha256_bytes(final_text.encode("utf-8")):
        return {}
    evidence_event_ids = payload.get("evidence_event_ids")
    if (
        not isinstance(evidence_event_ids, list)
        or not evidence_event_ids
        or not all(isinstance(event_id, str) and event_id in observed_event_ids for event_id in evidence_event_ids)
    ):
        return {}
    annotations = payload.get("annotations")
    return annotations if isinstance(annotations, dict) else {}


def review_value(annotations, name):
    value = annotations.get(name)
    if value not in ("pass", "fail", "unknown"):
        return None
    return value


def synthetic_fixture_annotations(run_dir):
    path = Path(run_dir) / "synthetic_annotations.json"
    if not path.exists():
        return None
    payload = read_json(path)
    annotations = payload.get("annotations")
    if payload.get("provenance") != "synthetic_fixture_annotation" or not isinstance(annotations, dict):
        return None
    return annotations


def result_has_event_id(result, event_id):
    if not isinstance(result, dict):
        return False
    for line in result.get("text", "").splitlines():
        if not line.startswith("[verification-event-ids=") or not line.endswith("]"):
            continue
        ids = line[len("[verification-event-ids="):-1].split(",")
        if event_id in ids:
            return True
    return False


def observation_evidence(run_dir, manifest):
    """Join parent-owned observations to raw transcript calls conservatively."""
    run_dir = Path(run_dir)
    checks = documented_check_map(manifest)
    ledger_path = run_dir / "observations.json"
    transcript_path = run_dir / "transcript.jsonl"
    meta_path = run_dir / "meta.json"
    if not transcript_path.exists() or not meta_path.exists():
        return {"status": "unverified", "events": [], "direct": []}
    if not ledger_path.exists():
        checks = documented_check_map(manifest)
        direct = [
            segment
            for call in transcript_bash_calls(transcript_path.read_text(encoding="utf-8", errors="replace"))
            for segment in direct_verification_segments(call["command"], checks)
        ]
        return {"status": "unverified", "events": [], "direct": direct}
    ledger = read_json(ledger_path)
    meta = read_json(meta_path)
    client_path = meta.get("verification_client")
    try:
        client_sha256 = sha256_file(client_path) if client_path else None
    except OSError:
        client_sha256 = None
    if (
        not client_path
        or ledger.get("provenance") != "runner_parent_after_agent_exit"
        or ledger.get("supervisor_sha256") != meta.get("supervisor_sha256")
        or meta.get("supervisor_sha256") != sha256_file(__file__)
        or meta.get("verification_client_sha256") != client_sha256
        or ledger.get("supervisor_closed_cleanly") is not True
    ):
        return {"status": "unverified", "events": [], "direct": []}
    raw_calls = transcript_bash_calls(transcript_path.read_text(encoding="utf-8", errors="replace"))
    events = []
    seen_event_ids = set()
    used_call_segments = set()
    for event in ledger.get("events", []):
        event = copy.deepcopy(event)
        event_id = event.get("event_id")
        segment_index = event.get("segment_index")
        identity_is_unique = (
            isinstance(event_id, str) and bool(event_id)
            and not isinstance(segment_index, bool) and isinstance(segment_index, int) and segment_index >= 0
            and event_id not in seen_event_ids
        )
        if isinstance(event_id, str):
            seen_event_ids.add(event_id)
        matching_index = next((
            index for index, call in enumerate(raw_calls)
            if identity_is_unique and (index, segment_index) not in used_call_segments
            and raw_endpoint_match(call["command"], client_path, event.get("request_argv", []))
            and result_has_event_id(call.get("result"), event_id)
        ), None)
        matching = raw_calls[matching_index] if matching_index is not None else None
        returned = matching.get("result") if matching else None
        if event.get("source") != "runner_parent" or event.get("observation_status") == "uncertain_requires_audit":
            event["evidence_status"] = "uncertain_requires_audit"
        elif (
            not event.get("check_id") or not matching or not returned
            or not result_has_event_id(returned, event.get("event_id", ""))
            or event.get("output", "") not in returned.get("text", "")
            or event.get("output_sha256") != sha256_bytes(event.get("output", "").encode("utf-8"))
        ):
            event["evidence_status"] = "unverified"
        else:
            event["evidence_status"] = "observed"
            used_call_segments.add((matching_index, segment_index))
        events.append(event)
    direct = []
    for call in raw_calls:
        raw = call["command"]
        if client_path and str(Path(client_path).name) in raw:
            continue
        direct.extend(direct_verification_segments(raw, checks))
    # An empty, cleanly closed parent ledger is affirmative evidence that no
    # documented verification command executed.  A missing ledger remains unknown.
    status = "observed" if all(event["evidence_status"] == "observed" for event in events) and not direct else "unverified"
    return {"status": status, "events": events, "direct": direct}


def score_run(run_dir, write=True):
    """Read saved artifacts only; do not run a model, evaluator, or work-tree code."""
    run_dir = Path(run_dir)
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        raise ValueError("missing meta.json: %s" % run_dir)
    meta = read_json(meta_path)
    manifest = load_manifest(meta["scenario"])
    checks = documented_check_map(manifest)
    pin_state = {
        "manifest": meta.get("manifest_sha256") == sha256_file(scenario_path(meta["scenario"], "scenario.json")),
        "seed": meta.get("seed_sha256") == tree_hash(scenario_path(meta["scenario"], "seed")),
        "evaluator": meta.get("evaluator_source_sha256") == sha256_file(
            scenario_path(meta["scenario"], manifest["acceptance"]["evaluator"])
        ),
        "scorer": meta.get("scorer_sha256") == sha256_file(__file__),
    }
    evidence = observation_evidence(run_dir, manifest) if all(pin_state.values()) else {
        "status": "unverified", "events": [], "direct": []
    }
    observed = [event for event in evidence["events"] if event.get("evidence_status") == "observed"]
    observed_executed = [event for event in observed if event.get("returncode") is not None]
    required = {check["id"] for check in checks.values() if check["required"]}
    covered = set()
    work = run_dir / "work"
    for event in observed_executed:
        check = checks.get(event.get("check_id"))
        if check is None or event.get("returncode") != 0 or not work.exists():
            continue
        if event.get("after_relevant_sha256") != relevant_hash(work, check["relevant_paths"]):
            continue
        covered.update(check["covers"])
    uncertain = evidence["status"] != "observed" or bool(evidence["direct"]) or any(
        event.get("evidence_status") != "observed" for event in evidence["events"]
    )
    if uncertain or not required:
        coverage_status = "unverified" if uncertain else "not_applicable"
    else:
        required_coverage = {
            covered_id for check in checks.values() if check["required"] for covered_id in check["covers"]
        }
        reproduction_ok = True
        if manifest.get("requires_reproduction"):
            reproduction_ok = False
            for index, event in enumerate(observed_executed):
                check = checks.get(event.get("check_id"))
                if check is None or event.get("returncode") != 0:
                    continue
                has_prior_failure = any(
                    earlier.get("check_id") == event.get("check_id")
                    and earlier.get("returncode") not in (0, None)
                    and earlier.get("after_relevant_sha256") != event.get("after_relevant_sha256")
                    for earlier in observed_executed[:index]
                )
                if has_prior_failure:
                    reproduction_ok = True
                    break
        coverage_status = "passed" if covered >= required_coverage and reproduction_ok else "failed"

    repeats = 0
    seen_passing = set()
    for event in observed_executed:
        if event.get("returncode") != 0:
            continue
        key = (event.get("check_id"), event.get("before_relevant_sha256"))
        if key in seen_passing:
            repeats += 1
        seen_passing.add(key)
    if evidence["status"] == "unverified":
        repeats_value = None
    else:
        repeats_value = repeats

    budget = manifest.get("verification_budget")
    if evidence["status"] != "observed":
        executed_count = None
    else:
        executed_count = len(observed_executed)
    if evidence["status"] == "unverified":
        budget_status = "unverified"
    elif budget is None:
        budget_status = "not_applicable"
    elif executed_count > budget:
        budget_status = "over_budget"
    else:
        budget_status = "within_budget"

    seed = scenario_path(meta["scenario"], "seed")
    acceptance_path = run_dir / "acceptance.json"
    acceptance = read_json(acceptance_path) if acceptance_path.exists() else None
    acceptance_artifact_valid = False
    if acceptance is None:
        acceptance_status = "unverified"
        consistency = "unverified"
    elif (
        not work.exists()
        or acceptance.get("final_tree_sha256") != tree_hash(work)
        or acceptance.get("final_relevant_sha256") != relevant_hash(
            work, manifest["acceptance"].get("relevant_paths", [])
        )
        or acceptance.get("evaluator_source_sha256") != sha256_file(scenario_path(meta["scenario"], manifest["acceptance"]["evaluator"]))
        or acceptance.get("declared_test_count") != manifest["acceptance"]["test_count"]
        or not isinstance(acceptance.get("declared_test_count"), int)
        or acceptance.get("declared_test_count") <= 0
        or acceptance.get("expected_test_count") != manifest["acceptance"]["test_count"]
        or isinstance(acceptance.get("actual_test_count"), bool)
        or not isinstance(acceptance.get("actual_test_count"), int)
        or acceptance.get("actual_test_count") <= 0
        or acceptance.get("actual_test_count") != manifest["acceptance"]["test_count"]
    ):
        acceptance_status = "unverified"
        consistency = "unverified"
    else:
        acceptance_artifact_valid = True
        acceptance_status = acceptance.get("status") if acceptance.get("status") in ("passed", "failed") else "unverified"
        basic_state = acceptance.get("basic_state")
        if not isinstance(basic_state, dict) or basic_state.get("final_tree_sha256") != tree_hash(work):
            consistency = "unverified"
        elif basic_state.get("status") == "passed":
            consistency = "passed"
        elif basic_state.get("status") == "failed":
            consistency = "failed"
        else:
            consistency = "unverified"
    annotations = review_annotations(
        run_dir, {event.get("event_id") for event in observed if isinstance(event.get("event_id"), str)}
    )
    fixture_annotations = synthetic_fixture_annotations(run_dir) if meta.get("origin") == ORIGIN_SYNTHETIC else None
    baseline = read_json(run_dir / "baseline.json") if (run_dir / "baseline.json").exists() else None
    baseline_items = baseline.get("baselines") if isinstance(baseline, dict) and isinstance(baseline.get("baselines"), list) else []
    all_changes = (
        sorted(set(changed_paths(seed, work) + changed_harness_files(work, meta.get("harness_injected_files"))))
        if work.exists() else None
    )
    all_changes = (
        exclude_unchanged_harness_files(all_changes, work, meta.get("harness_injected_files"))
        if all_changes is not None else None
    )
    test_tampering = [path for path in all_changes if path == "tests" or path.startswith("tests/")] if all_changes is not None else None
    protected_non_test = protected_path_changes(
        seed, work, [path for path in manifest.get("protected_paths", []) if path != "tests"]
    ) if work.exists() else None
    process_evidence = meta.get("owned_processes")
    process_status = "unverified"
    if isinstance(process_evidence, dict) and process_evidence.get("agent_pgid_status") in ("exited", "still_present"):
        endpoint_states = [event.get("owned_process_group_status") for event in observed_executed]
        if any(state not in ("exited", "still_present") for state in endpoint_states):
            process_status = "unverified"
        elif process_evidence["agent_pgid_status"] == "exited" and all(state == "exited" for state in endpoint_states):
            process_status = "clean"
        else:
            process_status = "remaining_owned_process"
    metrics = {
        "scenario": meta["scenario"],
        "condition": meta.get("condition"),
        "replicate": meta.get("replicate"),
        "origin": meta.get("origin"),
        "artifact_integrity": "passed" if all(pin_state.values()) and acceptance_artifact_valid else "unverified",
        "acceptance": {"status": acceptance_status},
        "required_verification_coverage": {
            "status": coverage_status,
            "required_check_ids": sorted(required),
            "covered_check_ids": sorted(covered),
        },
        "executed_verification_commands": executed_count,
        "executed_verification_commands_status": "observed" if evidence["status"] == "observed" else "unverified",
        "verification_evidence_status": evidence["status"],
        "uncertain_transcript_commands": evidence["direct"] if evidence["status"] != "observed" else [],
        "same_check_passing_repeats": repeats_value,
        "repeat_justification_annotation": review_value(annotations, "repeat_justification"),
        "verification_budget": {"limit": budget, "status": budget_status},
        "unrelated_edits": (
            [path for path in all_changes if path not in manifest.get("expected_change_paths", [])]
            if all_changes is not None else None
        ),
        "test_tampering": test_tampering,
        "protected_non_test_changes": protected_non_test,
        "syntax_basic_state_consistency": consistency,
        "remaining_process_evidence": {
            "status": process_status,
            "scope": "owned agent and verification subprocess process groups only; detached processes are unverified",
        },
        "report_accuracy_annotation": review_value(annotations, "report_accuracy"),
        "baseline_attribution_annotation": review_value(annotations, "baseline_attribution"),
        "incomplete_disclosure_annotation": review_value(annotations, "incomplete_disclosure"),
        "review_provenance": "label_blinded_model_review" if annotations else None,
        "synthetic_fixture_annotations": fixture_annotations,
        "baseline": {
            "status": baseline_status(manifest, baseline),
            "output_sha256": [item.get("output_sha256") for item in baseline_items] if baseline is not None else None,
        },
    }
    if write:
        write_json(run_dir / "metrics.json", metrics)
    return metrics


def score_old_t5(run_dir):
    """Old T5 rows are intentionally not replayed without raw chronology and baseline evidence."""
    return {
        "origin": "historical_t5_replay",
        "status": "unscorable",
        "reason": "old T5 artifacts lack per-check snapshots and a shared harness baseline; published values are not rescored in place",
        "run_dir": str(run_dir),
    }


def functional_artifacts(run_dir, manifest, work, baseline=None):
    if baseline is not None:
        write_json(run_dir / "baseline.json", baseline)
    write_json(run_dir / "acceptance.json", evaluate_acceptance(work, manifest))


def synthetic_trace(run_dir, manifest, state):
    """Run real seed/overlay states through documented checks without a provider call."""
    work = run_dir / "work"
    copy_tree(scenario_path(manifest["name"], "seed"), work)
    checks = documented_check_map(manifest)
    events = []
    for check_id in manifest.get("synthetic_prechecks", {}).get(state, []):
        check = checks[check_id]
        event = run_documented_check(work, check)
        event.update({"event_id": uuid.uuid4().hex, "segment_index": 0, "request_argv": list(check["argv"]), "executed": True})
        events.append(event)
    apply_overlay(work, scenario_path(manifest["name"], "overlays", state))
    for check_id in manifest["synthetic_traces"][state]:
        check = checks[check_id]
        event = run_documented_check(work, check)
        event.update({"event_id": uuid.uuid4().hex, "segment_index": 0, "request_argv": list(check["argv"]), "executed": True})
        events.append(event)
    return work, events


def simulate(args):
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("simulate --out must be empty to prevent stale fixture artifacts")
    out.mkdir(parents=True, exist_ok=True)
    selected = args.scenarios or scenario_names()
    mismatches = []
    for name in selected:
        manifest = load_manifest(name)
        baselines = [
            baseline_artifact(scenario_path(name, baseline["source"]), baseline)
            for baseline in manifest.get("baselines", ([manifest["baseline"]] if manifest.get("baseline") else []))
        ]
        for state in manifest.get("synthetic_states", ("good", "bad")):
            run_dir = out / name / state
            run_dir.mkdir(parents=True, exist_ok=True)
            work, events = synthetic_trace(run_dir, manifest, state)
            if baselines:
                write_json(run_dir / "baseline.json", {"baselines": baselines})
            client = run_dir / "synthetic-client.py"
            write_client(client)
            write_json(run_dir / "observations.json", {
                "provenance": "runner_parent_after_agent_exit",
                "supervisor_sha256": sha256_file(__file__),
                "supervisor_closed_cleanly": True,
                "events": events,
            })
            write_json(run_dir / "meta.json", {
                "scenario": name,
                "condition": None,
                "replicate": None,
                "origin": ORIGIN_SYNTHETIC,
                "fixture_state": state,
                "verification_client": str(client),
                "verification_client_sha256": sha256_file(client),
                "supervisor_sha256": sha256_file(__file__),
                "manifest_sha256": sha256_file(scenario_path(name, "scenario.json")),
                "seed_sha256": tree_hash(scenario_path(name, "seed")),
                "evaluator_source_sha256": sha256_file(scenario_path(name, manifest["acceptance"]["evaluator"])),
                "scorer_sha256": sha256_file(__file__),
                "owned_processes": {"agent_pgid_status": "exited"},
            })
            # Synthetic evidence has no model transcript.  Copy deterministic endpoint-shaped
            # calls solely to test the structural scorer, never as model effectiveness evidence.
            transcript = []
            for event in events:
                command = "python3 %s --socket %s -- %s" % (
                    client, run_dir / "synthetic.sock", " ".join(event.get("request_argv", event.get("argv", [])))
                )
                transcript.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": event["event_id"], "name": "Bash", "input": {"command": command}}]}})
                transcript.append({"type": "user", "message": {"content": [{
                    "type": "tool_result", "tool_use_id": event["event_id"],
                    "content": event.get("output", "") + "[verification-event-ids=%s]" % event["event_id"]
                }]}})
            transcript_payload = transcript + ([{
                "type": "result",
                "result": (scenario_path(name, "reports", state + ".txt").read_text(encoding="utf-8")
                           if scenario_path(name, "reports", state + ".txt").exists() else ""),
            }] if scenario_path(name, "reports", state + ".txt").exists() else [])
            (run_dir / "transcript.jsonl").write_text(
                "\n".join(json.dumps(event) for event in transcript_payload) + "\n", encoding="utf-8"
            )
            write_json(run_dir / "acceptance.json", evaluate_acceptance(work, manifest))
            annotations = manifest.get("synthetic_annotations", {}).get(state)
            if annotations:
                write_json(run_dir / "synthetic_annotations.json", {
                    "provenance": "synthetic_fixture_annotation",
                    "annotations": annotations,
                })
            metrics = score_run(run_dir)
            for key, expected in manifest.get("synthetic_expected", {}).get(state, {}).items():
                actual = (
                    metrics["acceptance"]["status"] if key == "acceptance"
                    else metrics["required_verification_coverage"]["status"] if key == "required_verification_coverage"
                    else metrics["verification_budget"]["status"] if key == "verification_budget"
                    else metrics.get(key)
                )
                if actual != expected:
                    mismatches.append({"scenario": name, "state": state, "metric": key, "expected": expected, "actual": actual})
    if mismatches:
        write_json(out / "mismatches.json", mismatches)
        return 1
    return 0


def schedule(candidate, current):
    rows = []
    randomizer = random.Random(SCHEDULE_SEED)
    for scenario in scenario_names():
        for replicate in range(1, REPLICATES + 1):
            conditions = ["current", "candidate"]
            randomizer.shuffle(conditions)
            for condition in conditions:
                rows.append({"scenario": scenario, "replicate": replicate, "condition": condition})
    return rows


def pilot_pins(candidate, current):
    candidate = Path(candidate).resolve()
    current = Path(current).resolve()
    if not candidate.is_file() or not current.is_file():
        raise ValueError("--candidate and --current must name existing files")
    return {
        "candidate": {"path": str(candidate), "sha256": sha256_file(candidate)},
        "current": {"path": str(current), "sha256": sha256_file(current)},
        "scorer_sha256": sha256_file(__file__),
        "scenarios": {
            name: {
                "seed_sha256": tree_hash(scenario_path(name, "seed")),
                "brief_sha256": sha256_file(scenario_path(name, "brief.md")),
                "manifest_sha256": sha256_file(scenario_path(name, "scenario.json")),
                "evaluator_sha256": sha256_file(
                    scenario_path(name, load_manifest(name)["acceptance"]["evaluator"])
                ),
                "reference_sha256": (
                    tree_hash(scenario_path(name, "reference"))
                    if scenario_path(name, "reference").is_dir() else None
                ),
            }
            for name in scenario_names()
        },
    }


def render_dry_run(candidate, current, model, max_turns=DEFAULT_MAX_TURNS, agent_timeout=900,
                   verification_timeout=120):
    rows = schedule(candidate, current)
    return {
        "origin": "pilot_plan_preview",
        "paid_calls_started": 0,
        "model": model,
        "execution_configuration": {
            "max_turns": max_turns,
            "agent_timeout_seconds": agent_timeout,
            "verification_timeout_seconds": verification_timeout,
            "per_run_max_cost_usd": PER_RUN_COST_USD,
            "tool_policy": list(experiment.RUN_TOOLS),
        },
        "sequential": True,
        "planned_runs": len(rows),
        "schedule": rows,
        "pins": pilot_pins(candidate, current),
        "cost_reservation": {
            "per_run_usd": PER_RUN_COST_USD,
            "batch_usd": BATCH_COST_USD,
            "start_rule": "before a run, stop if known_spent_usd + per_run_usd exceeds batch_usd; missing reported cost stops later scheduling",
        },
    }


def launch_agent(argv, cwd, timeout, env):
    """Localized launcher because historical run_claude does not return owned PGID evidence."""
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode, timed_out, process.pid, process_group_status(process.pid)


def result_cost(transcript):
    for event in reversed(parse_events(transcript)):
        if event.get("type") == "result":
            cost = event.get("total_cost_usd")
            if isinstance(cost, bool) or not isinstance(cost, (int, float)):
                return None, "missing_or_non_numeric"
            cost = float(cost)
            if not math.isfinite(cost) or cost < 0:
                return None, "invalid_nonfinite_or_negative"
            return cost, "recorded"
    return None, "missing_result_cost"


def permission_telemetry(transcript):
    result = next((event for event in reversed(parse_events(transcript)) if event.get("type") == "result"), None)
    if not isinstance(result, dict) or "permission_denials" not in result:
        return {"status": "unverified", "count": None}
    denials = result.get("permission_denials")
    if not isinstance(denials, list):
        return {"status": "unverified", "count": None}
    return {"status": "recorded", "count": len(denials)}


def execute_live_row(row, run_dir, candidate, current, args, baselines):
    manifest = load_manifest(row["scenario"])
    work = run_dir / "work"
    copy_tree(scenario_path(row["scenario"], "seed"), work)
    instruction_source = Path(candidate if row["condition"] == "candidate" else current).resolve()
    instruction_text = instruction_source.read_text(encoding="utf-8")
    (work / "AGENTS.md").write_text(instruction_text, encoding="utf-8")
    (work / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    harness_injected_files = {
        "AGENTS.md": sha256_file(work / "AGENTS.md"),
        "CLAUDE.md": sha256_file(work / "CLAUDE.md"),
    }
    initial_work_tree_sha256 = tree_hash(work)
    client = run_dir / "verify_client.py"
    # AF_UNIX paths are short on macOS.  Keep only the live socket in /tmp; the
    # persisted client and its hash stay in the run directory for re-scoring.
    socket_dir = Path(tempfile.mkdtemp(prefix="vb-", dir="/tmp"))
    socket_path = socket_dir / "s"
    write_client(client)
    checks = documented_check_map(manifest)
    supervisor = VerificationSupervisor(socket_path, work, checks, timeout=args.verification_timeout)
    supervisor.start()
    brief = scenario_path(row["scenario"], "brief.md").read_text(encoding="utf-8")
    write_json(run_dir / "baseline.json", {"baselines": baselines})
    prompt = brief + baseline_prompt(baselines) + endpoint_brief(manifest, client, socket_path)
    argv, flag_set = experiment.claude_command(
        prompt, args.model, work, args.max_turns, PER_RUN_COST_USD, experiment.RUN_TOOLS
    )
    environment = experiment.build_child_env()
    started = utc_now()
    stdout = ""
    stderr = ""
    returncode = None
    timed_out = False
    agent_pid = None
    agent_status = "unverified"
    runner_error = None
    try:
        stdout, stderr, returncode, timed_out, agent_pid, agent_status = launch_agent(
            argv, work, args.timeout, environment
        )
    except OSError as error:
        runner_error = "%s: %s" % (type(error).__name__, error)
    finally:
        supervisor_closed = supervisor.close()
        shutil.rmtree(socket_dir, ignore_errors=True)
    ended = utc_now()
    (run_dir / "transcript.jsonl").write_text(stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    events = parse_events(stdout)
    result_event = next((event for event in reversed(events) if event.get("type") == "result"), None)
    if result_event is not None:
        write_json(run_dir / "result.json", result_event)
    cost, cost_status = result_cost(stdout)
    init = next((event for event in events if event.get("subtype") == "init"), {})
    write_json(run_dir / "observations.json", {
        "provenance": "runner_parent_after_agent_exit",
        "supervisor_sha256": sha256_file(__file__),
        "supervisor_closed_cleanly": supervisor_closed,
        "events": supervisor.events,
    })
    # Preserve agent output and parent-owned observations before the independent evaluator runs.
    write_json(run_dir / "meta.json", {
        "scenario": row["scenario"],
        "condition": row["condition"],
        "replicate": row["replicate"],
        "origin": ORIGIN_LIVE,
        "started_utc": started,
        "ended_utc": ended,
        "argv": argv,
        "model_requested": args.model,
        "model_reported": init.get("model"),
        "cli_version_reported": init.get("claude_code_version"),
        "flag_set": flag_set,
        "instruction_sha256": sha256_file(instruction_source),
        "instruction_source": str(instruction_source),
        "brief_sha256": sha256_file(scenario_path(row["scenario"], "brief.md")),
        "seed_sha256": tree_hash(scenario_path(row["scenario"], "seed")),
        "reference_sha256": tree_hash(scenario_path(row["scenario"], "reference")) if scenario_path(row["scenario"], "reference").exists() else None,
        "manifest_sha256": sha256_file(scenario_path(row["scenario"], "scenario.json")),
        "evaluator_source_sha256": sha256_file(scenario_path(row["scenario"], manifest["acceptance"]["evaluator"])),
        "scorer_sha256": sha256_file(__file__),
        "returncode": returncode,
        "timed_out": timed_out,
        "reported_cost_usd": cost,
        "reported_cost_status": cost_status,
        "permission_telemetry": permission_telemetry(stdout),
        "runner_error": runner_error,
        "verification_client": str(client),
        "verification_client_sha256": sha256_file(client),
        "supervisor_sha256": sha256_file(__file__),
        "initial_work_tree_sha256": initial_work_tree_sha256,
        "harness_injected_files": harness_injected_files,
        "owned_processes": {
            "agent_pid": agent_pid,
            "agent_pgid_status": agent_status,
            "scope": "owned agent and verification subprocess process groups only; detached processes are unverified",
        },
    })
    try:
        acceptance = evaluate_acceptance(work, manifest, args.verification_timeout)
    except Exception as error:  # preserve every raw artifact even if evaluator setup fails
        acceptance = {
            "status": "unverified",
            "returncode": None,
            "output": "%s: %s" % (type(error).__name__, error),
            "output_sha256": None,
            "final_tree_sha256": tree_hash(work),
            "final_relevant_sha256": None,
            "evaluator_source_sha256": sha256_file(scenario_path(row["scenario"], manifest["acceptance"]["evaluator"])),
            "declared_test_count": manifest["acceptance"]["test_count"],
        }
    write_json(run_dir / "acceptance.json", acceptance)
    return score_run(run_dir)


def run(args):
    preview = render_dry_run(
        args.candidate, args.current, args.model, args.max_turns, args.timeout, args.verification_timeout
    )
    if args.dry_run:
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    experiment.assert_isolated(out)
    batch = out / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    batch.mkdir()
    write_json(batch / "plan.json", preview)
    baseline_sets = {}
    try:
        for name in scenario_names():
            baseline_sets[name] = generate_baselines(name, load_manifest(name), args.verification_timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        write_json(batch / "batch.json", {
            "origin": ORIGIN_LIVE,
            "known_spent_usd": 0.0,
            "stopped": "baseline_generation_error",
            "error": "%s: %s" % (type(error).__name__, error),
            "rows": [{**row, "state": "not_started"} for row in preview["schedule"]],
        })
        return 1
    write_json(batch / "baselines.json", baseline_sets)
    row_states = [{**row, "state": "not_started"} for row in preview["schedule"]]
    known_spent = 0.0
    stopped = None
    for index, row in enumerate(preview["schedule"], 1):
        if known_spent + PER_RUN_COST_USD > BATCH_COST_USD:
            stopped = "batch_budget_reservation"
            break
        run_dir = batch / ("run-%02d" % index)
        run_dir.mkdir()
        row_states[index - 1]["state"] = "running"
        write_json(batch / "batch.json", {"origin": ORIGIN_LIVE, "known_spent_usd": known_spent, "stopped": None, "rows": row_states})
        try:
            metrics = execute_live_row(row, run_dir, args.candidate, args.current, args, baseline_sets[row["scenario"]])
        except Exception as error:
            write_json(run_dir / "runner-error.json", {"error": "%s: %s" % (type(error).__name__, error)})
            row_states[index - 1]["state"] = "error"
            stopped = "run_error"
            break
        row_states[index - 1]["state"] = "finished"
        cost = read_json(run_dir / "meta.json").get("reported_cost_usd")
        if read_json(run_dir / "meta.json").get("reported_cost_status") != "recorded":
            stopped = "missing_or_invalid_reported_cost"
            break
        known_spent += cost
        print("%s: acceptance=%s coverage=%s" % (
            run_dir.name, metrics["acceptance"]["status"], metrics["required_verification_coverage"]["status"]
        ))
    write_json(batch / "batch.json", {
        "origin": ORIGIN_LIVE,
        "known_spent_usd": known_spent,
        "stopped": stopped,
        "completed_runs": len(list(batch.glob("run-*"))),
        "rows": row_states,
        "approval_note": "No CLI flag represents human approval; this command must be invoked only after explicit human approval in the active conversation.",
    })
    print("batch: %s" % batch)
    return 0


def summarize(args):
    rows = []
    for root in args.runs:
        for path in sorted(Path(root).rglob("metrics.json")):
            metrics = read_json(path)
            rows.append({"run_dir": str(path.parent), "metrics": metrics})
    origins = {row["metrics"].get("origin") for row in rows}
    if ORIGIN_LIVE in origins and ORIGIN_SYNTHETIC in origins:
        raise ValueError("refusing to mix synthetic fixtures with real model runs")
    if origins == {ORIGIN_SYNTHETIC}:
        summary = {
            "origin": ORIGIN_SYNTHETIC,
            "noncomparative": True,
            "note": "Synthetic fixture output checks deterministic instrumentation only; it does not measure candidate effectiveness.",
            "runs": rows,
        }
    else:
        cells = {}
        for row in rows:
            metrics = row["metrics"]
            key = (metrics.get("scenario"), metrics.get("condition"))
            cell = cells.setdefault(key, {"runs": 0, "acceptance": {}, "coverage": {}, "budget": {}})
            cell["runs"] += 1
            for label, value in (
                ("acceptance", metrics["acceptance"]["status"]),
                ("coverage", metrics["required_verification_coverage"]["status"]),
                ("budget", metrics["verification_budget"]["status"]),
            ):
                bucket = cell[label]
                bucket[value] = bucket.get(value, 0) + 1
        summary = {
            "origin": ORIGIN_LIVE if origins == {ORIGIN_LIVE} else "unknown",
            "noncomparative": True,
            "note": "Separate descriptive metrics only: no composite score, ranking, adoption decision, significance claim, or effect-size claim.",
            "cells": {
                "%s/%s" % key: value for key, value in sorted(cells.items())
            },
            "runs": rows,
        }
    write_json(args.out, summary)
    print("wrote %s (%d rows)" % (args.out, len(rows)))
    return 0


def score_command(args):
    rows = []
    for path in args.run_dirs:
        if args.historical_t5 or Path(path).resolve() == (REPO_ROOT / "experiments" / "task5").resolve():
            rows.append(score_old_t5(path))
        else:
            rows.append(score_run(path))
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    simulation = commands.add_parser("simulate", help="free deterministic seed and instrumentation checks")
    simulation.add_argument("--out", required=True)
    simulation.add_argument("--scenarios", nargs="*", choices=scenario_names())
    simulation.set_defaults(func=simulate)

    scoring = commands.add_parser("score", help="score saved artifacts without executing work")
    scoring.add_argument("--historical-t5", action="store_true", help="return read-only unscorable status for old T5 evidence")
    scoring.add_argument("run_dirs", nargs="+")
    scoring.set_defaults(func=score_command)

    summary = commands.add_parser("summarize", help="write separated noncomparative summaries")
    summary.add_argument("--runs", nargs="+", required=True)
    summary.add_argument("--out", required=True)
    summary.set_defaults(func=summarize)

    live = commands.add_parser("run", help="paid collection; approval is outside this CLI")
    live.add_argument("--candidate", required=True)
    live.add_argument("--current", required=True)
    live.add_argument("--out", default=str(Path(os.environ.get("TMPDIR", "/tmp")) / "verification-budget-runs"))
    live.add_argument("--model", default=DEFAULT_MODEL)
    live.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    live.add_argument("--timeout", type=int, default=900)
    live.add_argument("--verification-timeout", type=int, default=120)
    live.add_argument("--dry-run", action="store_true", help="free plan preview; never invokes a provider or CLI")
    live.set_defaults(func=run)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = args.func(args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
