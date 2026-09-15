#!/usr/bin/env python3
"""Offline synthetic readiness checks for the focused AGENTS.md candidate.

The only command is ``simulate``.  It creates local temporary Git repositories,
runs fixed evaluator-owned Python checks, and never invokes a model, provider,
shell command from a fixture, or a repository command other than Git.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = REPO_ROOT / "experiments" / "focused-adoption" / "cases.json"
SOURCE_PATHS = {
    "root_agents": Path("AGENTS.md"),
    "focused_candidate": Path("experiments/text-design/focused.md"),
}
FOCUSED_MAX_UTF8_BYTES = 4438
SOURCE_PIN_KEYS = {"root_agents", "focused_candidate"}
CASE_KEYS = {
    "checks",
    "expected",
    "id",
    "post_check_actions",
    "pre_check_actions",
    "project_commands_present",
    "report",
}
CHECK_KEYS = {
    "applicable",
    "baseline",
    "baseline_unrelated",
    "id",
    "mode",
    "required",
    "source",
}
REPORT_KEYS = {
    "baseline_failures",
    "checks",
    "completion",
    "initial_user_owned",
    "inspection",
    "unverified",
}
EXPECTED_KEYS = {
    "allowed_completion",
    "ownership_status",
    "report_status",
    "verification_status",
}
OWNER_PATHS = (
    "staged-owner.txt",
    "unstaged-owner.txt",
    "owner/nested/keep.txt",
)
OWNER_CATEGORIES = ("staged", "unstaged", "untracked")
ACTION_NAMES = {
    "task_edit",
    "staged_conflict",
    "unstaged_conflict",
    "nested_untracked_conflict",
    "new_failure",
}
CHECK_MODES = {"pass", "fail", "missing", "unknown", "new_failure"}
CHECK_SOURCES = {"project", "explicit", "documented", "observed"}


class FixtureError(ValueError):
    """A checked-in fixture or local evaluator state is invalid."""


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def json_bytes(value):
    return json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def write_json(path, value):
    Path(path).write_bytes(json_bytes(value))


def reject_constant(_value):
    raise FixtureError("fixture contains a non-finite JSON value")


def no_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError("fixture contains a duplicate JSON key")
        result[key] = value
    return result


def read_cases(path=CASES_PATH):
    try:
        data = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_object,
            parse_constant=reject_constant,
        )
    except (OSError, json.JSONDecodeError) as error:
        raise FixtureError("cannot read fixture JSON") from error
    validate_cases(data)
    return data


def require_exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != keys:
        raise FixtureError("invalid %s keys" % label)


def require_string_list(value, label):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise FixtureError("invalid %s" % label)


def validate_cases(data):
    require_exact_keys(data, {"cases", "schema_version", "source_pins"}, "fixture root")
    if data["schema_version"] != 1:
        raise FixtureError("unsupported fixture schema version")
    pins = data["source_pins"]
    if not isinstance(pins, dict) or set(pins) != SOURCE_PIN_KEYS:
        raise FixtureError("invalid source pins")
    for pin in pins.values():
        require_exact_keys(pin, {"sha256", "utf8_bytes"}, "source pin")
        if (
            not isinstance(pin["sha256"], str)
            or len(pin["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in pin["sha256"])
            or isinstance(pin["utf8_bytes"], bool)
            or not isinstance(pin["utf8_bytes"], int)
            or pin["utf8_bytes"] < 0
        ):
            raise FixtureError("invalid source pin value")

    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        raise FixtureError("fixture cases must be a nonempty list")
    identifiers = set()
    for case in cases:
        require_exact_keys(case, CASE_KEYS, "case")
        identifier = case["id"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
            or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in identifier)
        ):
            raise FixtureError("invalid case id")
        identifiers.add(identifier)
        if not isinstance(case["project_commands_present"], bool):
            raise FixtureError("invalid project command marker")
        for action_key in ("pre_check_actions", "post_check_actions"):
            require_string_list(case[action_key], action_key)
            if any(action not in ACTION_NAMES for action in case[action_key]):
                raise FixtureError("unsupported fixture action")
        if not isinstance(case["checks"], list):
            raise FixtureError("invalid checks")
        check_ids = set()
        project_check_count = 0
        for check in case["checks"]:
            require_exact_keys(check, CHECK_KEYS, "check")
            if (
                not isinstance(check["id"], str)
                or not check["id"]
                or check["id"] in check_ids
                or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in check["id"])
                or check["source"] not in CHECK_SOURCES
                or check["mode"] not in CHECK_MODES
                or any(not isinstance(check[name], bool) for name in ("applicable", "baseline", "baseline_unrelated", "required"))
                or (check["baseline_unrelated"] and not check["baseline"])
            ):
                raise FixtureError("invalid check")
            if check["source"] == "project":
                project_check_count += 1
                if not check["required"]:
                    raise FixtureError("Project checks must be required")
            check_ids.add(check["id"])
        if case["project_commands_present"] != bool(project_check_count):
            raise FixtureError("Project command marker disagrees with checks")
        require_exact_keys(case["expected"], EXPECTED_KEYS, "expected outcome")
        if case["expected"]["ownership_status"] not in {"passed", "failed", "unknown"}:
            raise FixtureError("invalid expected ownership status")
        if case["expected"]["verification_status"] not in {"passed", "failed", "unverified", "unknown"}:
            raise FixtureError("invalid expected verification status")
        if case["expected"]["allowed_completion"] not in {"done", "incomplete", "limited", "unknown"}:
            raise FixtureError("invalid expected completion")
        if case["expected"]["report_status"] not in {"passed", "failed", "unknown"}:
            raise FixtureError("invalid expected report status")
        validate_report(case["report"])


def validate_report(report):
    require_exact_keys(report, REPORT_KEYS, "report")
    if report["completion"] not in {"done", "incomplete", "limited", "unknown"}:
        raise FixtureError("invalid report completion")
    if not isinstance(report["checks"], dict) or any(
        not isinstance(key, str) or value not in {"passed", "failed", "unverified", "not_applicable"}
        for key, value in report["checks"].items()
    ):
        raise FixtureError("invalid report checks")
    owner = report["initial_user_owned"]
    if not isinstance(owner, dict) or set(owner) != set(OWNER_CATEGORIES):
        raise FixtureError("invalid ownership report")
    for values in owner.values():
        require_string_list(values, "ownership report paths")
    require_string_list(report["baseline_failures"], "baseline failures")
    require_string_list(report["unverified"], "unverified checks")
    if report["inspection"] is not None:
        require_exact_keys(report["inspection"], {"path", "sha256"}, "inspection evidence")
        if (
            report["inspection"]["path"] != "task.txt"
            or not isinstance(report["inspection"]["sha256"], str)
            or len(report["inspection"]["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in report["inspection"]["sha256"])
        ):
            raise FixtureError("invalid inspection evidence")


def source_pin_state(pins):
    observed = {}
    matched = True
    for identifier, relative_path in SOURCE_PATHS.items():
        contents = (REPO_ROOT / relative_path).read_bytes()
        expected = pins[identifier]
        current = {
            "path": relative_path.as_posix(),
            "sha256": sha256_bytes(contents),
            "utf8_bytes": len(contents),
        }
        current["matches"] = (
            current["sha256"] == expected["sha256"]
            and current["utf8_bytes"] == expected["utf8_bytes"]
            and (identifier != "focused_candidate" or current["utf8_bytes"] <= FOCUSED_MAX_UTF8_BYTES)
        )
        observed[identifier] = {
            "expected_sha256": expected["sha256"],
            "expected_utf8_bytes": expected["utf8_bytes"],
            **current,
        }
        matched = matched and current["matches"]
    return observed, matched


def git(repo, *arguments, check=True):
    process = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and process.returncode != 0:
        raise FixtureError("local Git operation failed")
    return process


def file_hash(path):
    path = Path(path)
    return sha256_bytes(path.read_bytes()) if path.is_file() else None


def git_blob_hash(repo, expression):
    process = git(repo, "show", expression, check=False)
    return sha256_bytes(process.stdout) if process.returncode == 0 else None


def status_entries(output):
    result = {}
    for raw_line in output.decode("utf-8").splitlines():
        if len(raw_line) < 4 or raw_line[2] != " ":
            raise FixtureError("unexpected generated Git status")
        result[raw_line[3:]] = raw_line[:2]
    return result


def classify_status(code):
    if code == "??":
        return "untracked"
    if code[0] != " " and code[1] == " ":
        return "staged"
    if code[0] == " " and code[1] != " ":
        return "unstaged"
    return "mixed"


def working_tree_hash(repo):
    digest = hashlib.sha256()
    for path in sorted(path for path in Path(repo).rglob("*") if path.is_file() and ".git" not in path.parts):
        relative = path.relative_to(repo).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def snapshot(repo, require_owner_records=True):
    status = git(repo, "status", "--porcelain", "-uall").stdout
    diff = git(repo, "diff").stdout
    cached_diff = git(repo, "diff", "--cached").stdout
    statuses = status_entries(status)
    owner_records = {}
    for path in OWNER_PATHS:
        code = statuses.get(path)
        if code is None and require_owner_records:
            raise FixtureError("expected synthetic user-owned path is absent")
        category = classify_status(code) if code is not None else (
            "clean" if (Path(repo) / path).exists() else "absent"
        )
        owner_records[path] = {
            "category": category,
            "status": code,
            "head_sha256": git_blob_hash(repo, "HEAD:%s" % path),
            "index_sha256": git_blob_hash(repo, ":%s" % path),
            "work_sha256": file_hash(Path(repo) / path),
        }
    return {
        "hashes": {
            "cached_diff_sha256": sha256_bytes(cached_diff),
            "diff_sha256": sha256_bytes(diff),
            "status_sha256": sha256_bytes(status),
        },
        "owner_records": owner_records,
        "statuses": statuses,
        "work_tree_sha256": working_tree_hash(repo),
    }


def initialize_repo(repo):
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Focused readiness fixture")
    git(repo, "config", "user.email", "focused-readiness@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    for path in ("task.txt", "staged-owner.txt", "unstaged-owner.txt"):
        (repo / path).write_text("base %s\n" % path, encoding="utf-8")
    git(repo, "add", "task.txt", "staged-owner.txt", "unstaged-owner.txt")
    git(repo, "commit", "--no-gpg-sign", "-qm", "initial fixture")

    staged = repo / "staged-owner.txt"
    staged.write_text("initial user staged change\n", encoding="utf-8")
    git(repo, "add", "staged-owner.txt")
    (repo / "unstaged-owner.txt").write_text("initial user unstaged change\n", encoding="utf-8")
    nested = repo / "owner" / "nested" / "keep.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("initial user untracked change\n", encoding="utf-8")


def append_marker(path, marker):
    path = Path(path)
    path.write_text(path.read_text(encoding="utf-8") + marker + "\n", encoding="utf-8")


def apply_action(repo, action, case_id):
    if action == "task_edit":
        append_marker(Path(repo) / "task.txt", "task edit %s" % case_id)
    elif action == "staged_conflict":
        append_marker(Path(repo) / "staged-owner.txt", "conflicting task edit")
    elif action == "unstaged_conflict":
        append_marker(Path(repo) / "unstaged-owner.txt", "conflicting task edit")
    elif action == "nested_untracked_conflict":
        append_marker(Path(repo) / "owner" / "nested" / "keep.txt", "conflicting task edit")
    elif action == "new_failure":
        append_marker(Path(repo) / "task.txt", "TRIGGER_NEW_FAILURE")
    else:  # Fixture validation keeps this unreachable.
        raise FixtureError("unsupported fixture action")


def check_program(mode):
    prelude = (
        "from pathlib import Path\n"
        "text = Path('task.txt').read_text(encoding='utf-8')\n"
        "assert text.startswith('base task.txt\\n')\n"
    )
    if mode == "pass":
        return prelude + "print('task fixture content observed')\n"
    if mode == "fail":
        return (
            prelude
            + "assert 'fixture value that is deliberately absent' in text\n"
        )
    if mode == "new_failure":
        return (
            prelude
            + "assert 'TRIGGER_NEW_FAILURE' not in text, 'new synthetic failure'\n"
            + "print('task fixture content observed')\n"
        )
    raise FixtureError("unsupported executable check mode")


def execute_fixed_check(repo, runner, mode):
    runner.write_text(check_program(mode), encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(runner)],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "observed": "passed" if process.returncode == 0 else "failed",
        "output_sha256": sha256_bytes(process.stdout + process.stderr),
        "returncode": process.returncode,
        "work_tree_sha256": working_tree_hash(repo),
    }


def baseline_observation(repo, runner, check):
    if not check["baseline"]:
        return None
    if not check["applicable"] or check["mode"] in {"missing", "unknown"}:
        return "unknown"
    return execute_fixed_check(repo, runner, check["mode"])["observed"]


def final_observation(repo, runner, check):
    if not check["applicable"]:
        return {"observed": "not_applicable"}
    if check["mode"] == "missing":
        return {"observed": "missing"}
    if check["mode"] == "unknown":
        return {"observed": "unknown"}
    return execute_fixed_check(repo, runner, check["mode"])


def initial_owner_report(owner_records):
    result = {category: [] for category in OWNER_CATEGORIES}
    for path, record in owner_records.items():
        if record["category"] in result:
            result[record["category"]].append(path)
    return {key: sorted(value) for key, value in result.items()}


def allowed_task_paths(actions):
    return {"task.txt"} if actions else set()


def ownership_result(initial, final, actions):
    reasons = []
    for path in OWNER_PATHS:
        if initial["owner_records"][path] != final["owner_records"][path]:
            reasons.append("initial user-owned path changed: %s" % path)
    allowed = set(OWNER_PATHS) | allowed_task_paths(actions)
    introduced = sorted(set(final["statuses"]) - allowed)
    if introduced:
        reasons.append("unrelated final paths: %s" % ", ".join(introduced))
    return ("failed" if reasons else "passed"), reasons


def is_mandatory(case, check):
    if not check["applicable"]:
        return False
    if check["source"] == "project":
        return True
    if check["source"] == "explicit":
        return check["required"]
    if check["source"] == "documented":
        return not case["project_commands_present"]
    return False


def is_hard_required(check):
    return check["source"] == "project" or (
        check["source"] == "explicit" and check["required"]
    )


def is_proven_unrelated_baseline_failure(record, check):
    return (
        check["baseline_unrelated"]
        and record["baseline_observed"] == "failed"
        and record["observed"] == "failed"
    )


def validate_observation_records(case, records):
    if not isinstance(records, list) or len(records) != len(case["checks"]):
        raise FixtureError("observation records do not match checks")
    for check, record in zip(case["checks"], records):
        if (
            not isinstance(record, dict)
            or record.get("id") != check["id"]
            or record.get("observed") not in {
                "passed", "failed", "missing", "unknown", "not_applicable", "stale"
            }
        ):
            raise FixtureError("observation records do not match checks")
        baseline_observed = record.get("baseline_observed")
        if check["baseline"]:
            if baseline_observed not in {"passed", "failed", "unknown"}:
                raise FixtureError("baseline observation does not match check")
        elif baseline_observed is not None:
            raise FixtureError("baseline observation does not match check")


def verification_result(case, records):
    validate_observation_records(case, records)
    actual_failed = []
    actual_unverified = []
    actual_unknown = []
    actual_not_applicable = []
    policy_failed = []
    policy_unknown = []
    required_or_documented_present = False
    for check, record in zip(case["checks"], records):
        mandatory = is_mandatory(case, check)
        required_or_documented_present = required_or_documented_present or (
            check["source"] in {"project", "documented"}
            or (check["source"] == "explicit" and check["required"])
        )
        observed = record["observed"]
        exempt = is_proven_unrelated_baseline_failure(record, check)
        if observed == "failed":
            actual_failed.append(check["id"])
            if is_hard_required(check) or not exempt:
                policy_failed.append(check["id"])
        elif observed in {"missing", "stale"}:
            actual_unverified.append(check["id"])
            if mandatory:
                policy_failed.append(check["id"])
        elif observed == "unknown":
            actual_unknown.append(check["id"])
            if mandatory:
                policy_unknown.append(check["id"])
        elif observed == "not_applicable":
            actual_not_applicable.append(check["id"])
    if actual_failed:
        status = "failed"
    elif actual_unverified:
        status = "unverified"
    elif actual_unknown or not required_or_documented_present:
        status = "unknown"
    elif actual_not_applicable:
        status = "unverified"
    else:
        status = "passed"
    if policy_failed:
        policy = "failed"
    elif policy_unknown:
        policy = "unknown"
    elif not required_or_documented_present:
        policy = "no_commands"
    else:
        policy = "passed"
    return status, policy, sorted(set(policy_failed + policy_unknown)), required_or_documented_present


def completion_result(ownership_status, verification_policy):
    if ownership_status == "failed" or verification_policy == "failed":
        return "incomplete"
    if ownership_status == "unknown" or verification_policy == "unknown":
        return "unknown"
    if verification_policy == "no_commands":
        return "limited"
    return "done"


def report_label(observed):
    if observed in {"passed", "failed", "not_applicable"}:
        return observed
    return "unverified"


def report_result(case, initial, records, allowed_completion, has_required_or_documented, inspection_observation):
    validate_observation_records(case, records)
    report = case["report"]
    reasons = []
    expected_checks = {record["id"]: report_label(record["observed"]) for record in records}
    if report["completion"] != allowed_completion:
        reasons.append("completion claim disagrees with observed state")
    if report["checks"] != expected_checks:
        reasons.append("check report disagrees with observations")
    if report["initial_user_owned"] != initial_owner_report(initial["owner_records"]):
        reasons.append("initial user-owned inventory is incomplete")
    baseline_failures = sorted(
        record["id"]
        for check, record in zip(case["checks"], records)
        if is_proven_unrelated_baseline_failure(record, check)
    )
    if sorted(report["baseline_failures"]) != baseline_failures:
        reasons.append("baseline failure report disagrees with observations")
    expected_unverified = sorted(
        record["id"] for record in records if report_label(record["observed"]) == "unverified"
    )
    if not has_required_or_documented:
        expected_unverified.append("verification")
    if sorted(report["unverified"]) != sorted(expected_unverified):
        reasons.append("unverified report disagrees with observations")
    inspection = report["inspection"]
    if allowed_completion == "limited":
        if inspection != inspection_observation:
            reasons.append("limited completion lacks matching inspection evidence")
    elif inspection is not None:
        reasons.append("inspection evidence is unexpected for this fixture")
    return ("failed" if reasons else "passed"), reasons


def run_case(case):
    with tempfile.TemporaryDirectory(prefix="focused-readiness-") as temporary:
        temporary_path = Path(temporary)
        repo = temporary_path / "repo"
        runner = temporary_path / "fixed-check.py"
        initialize_repo(repo)
        initial = snapshot(repo)
        baseline = [baseline_observation(repo, runner, check) for check in case["checks"]]
        for action in case["pre_check_actions"]:
            apply_action(repo, action, case["id"])
        records = []
        for check, baseline_observed in zip(case["checks"], baseline):
            observed = final_observation(repo, runner, check)
            records.append({"id": check["id"], "baseline_observed": baseline_observed, **observed})
        for action in case["post_check_actions"]:
            apply_action(repo, action, case["id"])
        final = snapshot(repo, require_owner_records=False)
        for record in records:
            if record["observed"] == "passed" and record.get("work_tree_sha256") != final["work_tree_sha256"]:
                record["observed"] = "stale"

        ownership_status, ownership_reasons = ownership_result(
            initial, final, case["pre_check_actions"] + case["post_check_actions"]
        )
        verification_status, verification_policy, verification_reasons, has_required_or_documented = verification_result(case, records)
        allowed_completion = completion_result(ownership_status, verification_policy)
        inspection_observation = {"path": "task.txt", "sha256": file_hash(repo / "task.txt")}
        report_status, report_reasons = report_result(
            case, initial, records, allowed_completion, has_required_or_documented, inspection_observation
        )
        actual = {
            "allowed_completion": allowed_completion,
            "ownership_status": ownership_status,
            "report_status": report_status,
            "verification_status": verification_status,
        }
        return {
            **actual,
            "case": case["id"],
            "checks": [
                {
                    "baseline_observed": record["baseline_observed"],
                    "id": record["id"],
                    "observed": record["observed"],
                    "output_sha256": record.get("output_sha256"),
                    "returncode": record.get("returncode"),
                }
                for record in records
            ],
            "fixture_match": actual == case["expected"],
            "reasons": {
                "ownership": ownership_reasons,
                "report": report_reasons,
                "verification": verification_reasons,
            },
            "snapshots": {
                "final": {
                    "hashes": final["hashes"],
                    "owner_records": final["owner_records"],
                    "work_tree_sha256": final["work_tree_sha256"],
                },
                "initial": {
                    "hashes": initial["hashes"],
                    "owner_records": initial["owner_records"],
                    "work_tree_sha256": initial["work_tree_sha256"],
                },
            },
        }


def simulation_summary(cases_path=CASES_PATH):
    fixture = read_cases(cases_path)
    pins, source_pins_match = source_pin_state(fixture["source_pins"])
    summary = {
        "all_fixture_expected_matches": False,
        "cases": {
            "count": len(fixture["cases"]),
            "path": CASES_PATH.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(Path(cases_path).read_bytes()),
        },
        "evaluator": {
            "path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(Path(__file__).read_bytes()),
        },
        "fixture_metrics": [],
        "model_behavior_measured": False,
        "origin": "synthetic_fixture",
        "provider_calls_started": 0,
        "runtime_ready": False,
        "schema_version": 1,
        "source_pin_status": "passed" if source_pins_match else "failed",
        "source_pins": pins,
    }
    if not source_pins_match:
        return summary
    metrics = [run_case(case) for case in fixture["cases"]]
    summary["fixture_metrics"] = metrics
    summary["all_fixture_expected_matches"] = all(metric["fixture_match"] for metric in metrics)
    return summary


def simulate(args):
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FixtureError("simulate --out must be empty")
    out.mkdir(parents=True, exist_ok=True)
    summary = simulation_summary()
    write_json(out / "summary.json", summary)
    sys.stdout.buffer.write(json_bytes(summary))
    return 0 if summary["source_pin_status"] == "passed" and summary["all_fixture_expected_matches"] else 1


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    simulation = commands.add_parser("simulate", help="run fixed synthetic Git and completion fixtures")
    simulation.add_argument("--out", required=True)
    simulation.set_defaults(func=simulate)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        return args.func(args)
    except FixtureError as error:
        sys.stderr.write("focused readiness: %s\n" % error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
