#!/usr/bin/env python3
"""Read-only explanation of saved verification-observation uncertainty.

This tool audits a public verification-budget projection against its retained
private archive without re-scoring a row, executing a check, dereferencing a
recorded client path, or printing transcript material.  Its classifications
explain why the frozen scorer retained an outcome; they never recover evidence
or change a stored status.
"""

import argparse
import json
import re
import shlex
import sys
from collections import Counter
from pathlib import Path, PurePath

import verification_budget as budget


RAW_FILENAMES = (
    "meta.json",
    "metrics.json",
    "observations.json",
    "transcript.jsonl",
    "verify_client.py",
)
PUBLIC_SCHEMA = "verification-budget-public-results-v1"
DIAGNOSTIC_SCHEMA = "verification-budget-observation-diagnostic-v1"
RUN_ID_RE = re.compile(r"^run-[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_STATUSES = {"observed", "unverified"}
COVERAGE_STATUSES = {"passed", "failed", "unverified", "not_applicable"}


def is_safe_run_id(value):
    """Accept only this collection's public run-ID contract, never a path."""
    return isinstance(value, str) and bool(RUN_ID_RE.fullmatch(value))


def is_sha256(value):
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def inside(root, path):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def add_error(errors, code, run_id=None):
    item = {"code": code}
    if is_safe_run_id(run_id):
        item["run_id"] = run_id
    if item not in errors:
        errors.append(item)


def unavailable(errors):
    return {
        "schema": DIAGNOSTIC_SCHEMA,
        "diagnostic_status": "unavailable",
        "errors": sorted(errors, key=lambda item: (item.get("run_id", ""), item["code"])),
    }


def supplied_regular_file(path):
    """Read one explicitly supplied input without following a leaf symlink."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def supplied_collection(path):
    """Resolve the explicitly supplied collection root once, before child checks."""
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        return None
    try:
        return path.resolve(strict=True)
    except OSError:
        return None


def archive_run_dir(collection, run_id):
    """Return a direct, non-symlink child of ``collection`` or ``None``."""
    path = collection / run_id
    if path.is_symlink() or not path.is_dir():
        return None
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return None
    return resolved if resolved.parent == collection else None


def archive_file(collection, run_dir, name):
    """Return a fixed-name regular archive file, rejecting escape links."""
    if name not in RAW_FILENAMES:
        return None
    path = run_dir / name
    if path.is_symlink() or not path.is_file():
        return None
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return None
    if not inside(collection, resolved) or resolved.parent != run_dir:
        return None
    return resolved


def parse_json_bytes(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def parse_complete_transcript(data):
    """Reject malformed lines rather than silently dropping a partial transcript."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict):
            return None
    return text


def required_statuses(metrics):
    if not isinstance(metrics, dict):
        return None
    coverage = metrics.get("required_verification_coverage")
    if not isinstance(coverage, dict):
        return None
    evidence = metrics.get("verification_evidence_status")
    if evidence not in EVIDENCE_STATUSES or coverage.get("status") not in COVERAGE_STATUSES:
        return None
    return {
        "verification_evidence_status": evidence,
        "required_verification_coverage_status": coverage["status"],
    }


def shell_forms(tokens):
    """Describe parser-rejected token characters; do not infer shell execution."""
    forms = []
    if any(token in ("|", "||") or "|" in token for token in tokens):
        forms.append("parser_rejected_pipe_token_or_character")
    if any(token in ("<", ">") or "<" in token or ">" in token for token in tokens):
        forms.append("parser_rejected_redirection_token_or_character")
    if any(token == "&" for token in tokens):
        forms.append("parser_rejected_background_token")
    if any("$(" in token for token in tokens):
        forms.append("parser_rejected_command_substitution_character")
    if any("`" in token for token in tokens):
        forms.append("parser_rejected_backtick_character")
    return forms or ["parser_rejected_other_shell_structure"]


def parser_rejected_forms(raw_command):
    try:
        tokens = shlex.split(raw_command)
    except (TypeError, ValueError):
        return ["parser_rejected_unparseable_shell_text"]
    return shell_forms(tokens)


def lexical_endpoint_shape(raw_command, recorded_client, request_argv):
    """Strictly compare transcript argv without resolving the logged client path.

    The frozen scorer resolves a historical absolute client path.  This audit
    deliberately uses lexical equality instead, because the archived path may
    no longer exist and must never be dereferenced.  A suffix is explanatory
    only when the lexical client and documented request prefix already match.
    """
    try:
        tokens = shlex.split(raw_command)
    except (TypeError, ValueError):
        return {"strict": False, "reason": "unparseable_endpoint_command", "tail_forms": []}
    if "--" not in tokens:
        return {"strict": False, "reason": "missing_endpoint_divider", "tail_forms": []}
    divider = tokens.index("--")
    if divider < 2 or len(tokens) < 2 or tokens[1] != recorded_client:
        return {"strict": False, "reason": "endpoint_client_shape_mismatch", "tail_forms": []}
    observed_argv = tokens[divider + 1:]
    if observed_argv == request_argv:
        return {"strict": True, "reason": None, "tail_forms": []}
    tail_forms = []
    if observed_argv[:len(request_argv)] == request_argv and len(observed_argv) > len(request_argv):
        tail_forms = shell_forms(observed_argv[len(request_argv):])
        if tail_forms == ["parser_rejected_other_shell_structure"]:
            tail_forms = []
    return {"strict": False, "reason": "raw_argv_mismatch", "tail_forms": tail_forms}


def transcript_calls(text):
    """Use the frozen transcript parser only after complete-line validation."""
    try:
        calls = budget.transcript_bash_calls(text)
    except (AttributeError, KeyError, TypeError):
        return None
    return calls if all(isinstance(call.get("command"), str) for call in calls) else None


def direct_records(calls, checks, client_name):
    records = []
    for call in calls:
        raw = call["command"]
        # Keep the frozen scorer's conservative name-based exclusion, without
        # exposing the command or using the recorded absolute client path.
        if client_name in raw:
            continue
        for segment in budget.direct_verification_segments(raw, checks):
            if segment.get("status") == "uncertain_requires_audit":
                records.append({
                    "kind": "parser_rejected_shell_structure",
                    "forms": parser_rejected_forms(raw),
                })
            else:
                records.append({"kind": "transcript_only_documented_check", "forms": []})
    return records


def validate_event(event, event_ids):
    if not isinstance(event, dict):
        return "malformed_observation_event"
    event_id = event.get("event_id")
    segment_index = event.get("segment_index")
    request_argv = event.get("request_argv")
    output = event.get("output")
    if not isinstance(event_id, str) or not event_id or event_id in event_ids:
        return "duplicate_or_invalid_event_id"
    event_ids.add(event_id)
    if isinstance(segment_index, bool) or not isinstance(segment_index, int) or segment_index < 0:
        return "invalid_event_ordinal"
    if not isinstance(request_argv, list) or not request_argv or not all(isinstance(item, str) for item in request_argv):
        return "invalid_event_request_argv"
    if event.get("source") != "runner_parent":
        return "forged_event_source"
    if not isinstance(output, str) or not is_sha256(event.get("output_sha256")):
        return "invalid_event_output_binding"
    if budget.sha256_bytes(output.encode("utf-8")) != event["output_sha256"]:
        return "forged_event_output_hash"
    return None


def event_records(calls, events, recorded_client):
    """Report strict matcher linkage without event IDs, calls, or output text."""
    used_call_segments = set()
    records = []
    for ordinal, event in enumerate(events):
        event_id = event["event_id"]
        marked = [
            (index, call)
            for index, call in enumerate(calls)
            if budget.result_has_event_id(call.get("result"), event_id)
        ]
        record = {
            "ordinal": ordinal,
            "ledger_output_sha256": event["output_sha256"],
            "marker_presence": "present" if marked else "missing",
            "strict_match": "unmatched",
            "failure_reasons": [],
            "syntactic_suffix_explains_strict_mismatch": [],
        }
        if not marked:
            record["failure_reasons"].append("missing_event_marker")
            records.append(record)
            continue
        shapes = [
            (index, call, lexical_endpoint_shape(call["command"], recorded_client, event["request_argv"]))
            for index, call in marked
        ]
        exact = next(
            (
                (index, call)
                for index, call, shape in shapes
                if shape["strict"] and (index, event["segment_index"]) not in used_call_segments
            ),
            None,
        )
        if exact is None:
            if any(shape["reason"] == "raw_argv_mismatch" for _, _, shape in shapes):
                record["failure_reasons"].append("raw_argv_mismatch")
                for _, _, shape in shapes:
                    for form in shape["tail_forms"]:
                        if form not in record["syntactic_suffix_explains_strict_mismatch"]:
                            record["syntactic_suffix_explains_strict_mismatch"].append(form)
            else:
                record["failure_reasons"].append("strict_endpoint_shape_mismatch")
            records.append(record)
            continue
        index, call = exact
        returned = call.get("result")
        if not isinstance(returned, dict) or event["output"] not in returned.get("text", ""):
            record["failure_reasons"].append("output_binding_missing")
            records.append(record)
            continue
        used_call_segments.add((index, event["segment_index"]))
        record["strict_match"] = "matched"
        records.append(record)
    return records


def classify_row(calls, checks, client_name, events, recorded_client):
    direct = direct_records(calls, checks, client_name)
    event_data = event_records(calls, events, recorded_client)
    direct_uncertain = bool(direct)
    direct_parser_rejected = any(item["kind"] == "parser_rejected_shell_structure" for item in direct)
    linkage_uncertain = any(item["strict_match"] != "matched" for item in event_data)
    if direct_uncertain and linkage_uncertain:
        category = (
            "unsupported_shell_and_endpoint_linkage"
            if direct_parser_rejected else "transcript_only_and_endpoint_linkage"
        )
    elif direct_uncertain:
        category = "unsupported_shell_structure" if direct_parser_rejected else "transcript_only_documented_check"
    elif linkage_uncertain:
        category = "endpoint_linkage"
    else:
        category = "normal"
    return category, direct, event_data


def validate_archive(collection, publication):
    """Validate all required files and hashes before opening diagnostic JSON."""
    errors = []
    if not isinstance(publication, dict) or publication.get("schema") != PUBLIC_SCHEMA:
        add_error(errors, "invalid_publication_schema")
        return None, errors
    public_runs = publication.get("runs")
    if not isinstance(public_runs, list) or not public_runs:
        add_error(errors, "invalid_publication_runs")
        return None, errors
    rows = {}
    for row in public_runs:
        if not isinstance(row, dict):
            add_error(errors, "malformed_publication_run")
            continue
        run_id = row.get("run_id")
        if not is_safe_run_id(run_id):
            add_error(errors, "unsafe_publication_run_id")
            continue
        if run_id in rows:
            add_error(errors, "duplicate_publication_run_id", run_id)
            continue
        rows[run_id] = row

    archive_ids = set()
    try:
        entries = list(collection.iterdir())
    except OSError:
        add_error(errors, "unreadable_collection")
        return None, errors
    for entry in entries:
        if not entry.name.startswith("run-"):
            continue
        if not is_safe_run_id(entry.name) or entry.is_symlink() or not entry.is_dir():
            add_error(errors, "unsafe_archive_run_entry")
            continue
        archive_ids.add(entry.name)
    if set(rows) != archive_ids:
        add_error(errors, "publication_archive_run_set_mismatch")

    validated = []
    for run_id, row in sorted(rows.items()):
        run_dir = archive_run_dir(collection, run_id)
        if run_dir is None:
            add_error(errors, "unsafe_or_missing_archive_run", run_id)
            continue
        public_hashes = row.get("raw_artifact_sha256")
        if not isinstance(public_hashes, dict):
            add_error(errors, "invalid_publication_raw_hashes", run_id)
            continue
        artifacts = {}
        for name in RAW_FILENAMES:
            expected = public_hashes.get(name)
            if not is_sha256(expected):
                add_error(errors, "invalid_publication_raw_hash", run_id)
                continue
            path = archive_file(collection, run_dir, name)
            if path is None:
                add_error(errors, "unsafe_or_missing_raw_artifact", run_id)
                continue
            try:
                actual = budget.sha256_file(path)
            except OSError:
                add_error(errors, "unreadable_raw_artifact", run_id)
                continue
            if actual != expected:
                add_error(errors, "raw_artifact_hash_mismatch", run_id)
                continue
            artifacts[name] = path
        if len(artifacts) == len(RAW_FILENAMES):
            validated.append((run_id, row, run_dir, artifacts))
    return validated, errors


def diagnose_row(run_id, public_row, artifacts, source_hash):
    """Classify one validated row without writing or executing archive content."""
    try:
        meta = parse_json_bytes(artifacts["meta.json"].read_bytes())
        metrics = parse_json_bytes(artifacts["metrics.json"].read_bytes())
        ledger = parse_json_bytes(artifacts["observations.json"].read_bytes())
        transcript = parse_complete_transcript(artifacts["transcript.jsonl"].read_bytes())
    except OSError:
        return None, "unreadable_required_archive_artifact"
    if not isinstance(meta, dict) or not isinstance(ledger, dict) or transcript is None:
        return None, "malformed_required_archive_artifact"
    stored = required_statuses(metrics)
    published = required_statuses(public_row.get("metrics"))
    if stored is None or published is None or stored != published:
        return None, "stored_status_mismatch"
    scenario = meta.get("scenario")
    if not isinstance(scenario, str) or scenario not in budget.scenario_names():
        return None, "invalid_scenario"
    condition = meta.get("condition")
    replicate = meta.get("replicate")
    if (
        condition not in ("current", "candidate")
        or isinstance(replicate, bool)
        or not isinstance(replicate, int)
        or replicate <= 0
        or public_row.get("scenario") != scenario
        or public_row.get("condition") != condition
        or public_row.get("replicate") != replicate
    ):
        return None, "public_run_identity_mismatch"
    try:
        manifest = budget.load_manifest(scenario)
    except (OSError, ValueError, json.JSONDecodeError):
        return None, "invalid_scenario"
    manifest_hash = budget.sha256_file(budget.scenario_path(scenario, "scenario.json"))
    public_pins = public_row.get("source_pins")
    if (
        meta.get("manifest_sha256") != manifest_hash
        or not isinstance(public_pins, dict)
        or public_pins.get("manifest_sha256") != manifest_hash
    ):
        return None, "manifest_source_hash_mismatch"
    if (
        meta.get("supervisor_sha256") != source_hash
        or meta.get("scorer_sha256") != source_hash
        or ledger.get("supervisor_sha256") != source_hash
        or public_pins.get("runner_sha256") != source_hash
        or public_pins.get("scorer_sha256") != source_hash
    ):
        return None, "frozen_supervisor_source_hash_mismatch"
    if ledger.get("provenance") != "runner_parent_after_agent_exit" or ledger.get("supervisor_closed_cleanly") is not True:
        return None, "forged_or_incomplete_observation_ledger"
    recorded_client = meta.get("verification_client")
    if not isinstance(recorded_client, str):
        return None, "invalid_recorded_client_path"
    lexical_client = PurePath(recorded_client)
    if not lexical_client.is_absolute() or ".." in lexical_client.parts or lexical_client.name != "verify_client.py":
        return None, "lexically_ambiguous_recorded_client_path"
    client_hash = budget.sha256_file(artifacts["verify_client.py"])
    if meta.get("verification_client_sha256") != client_hash:
        return None, "verification_client_hash_mismatch"
    calls = transcript_calls(transcript)
    if calls is None:
        return None, "malformed_bash_call"
    events = ledger.get("events")
    if not isinstance(events, list):
        return None, "malformed_observation_events"
    event_ids = set()
    for event in events:
        issue = validate_event(event, event_ids)
        if issue is not None:
            return None, issue
    checks = budget.documented_check_map(manifest)
    category, direct, event_data = classify_row(calls, checks, lexical_client.name, events, recorded_client)
    inferred_evidence = "unverified" if category != "normal" else "observed"
    if stored["verification_evidence_status"] != inferred_evidence:
        return None, "diagnostic_evidence_status_mismatch"
    return {
        "run_id": run_id,
        "scenario": scenario,
        "condition": condition,
        "replicate": replicate,
        "stored_statuses": stored,
        "raw_digests": {name: budget.sha256_file(artifacts[name]) for name in RAW_FILENAMES},
        "category": category,
        "direct_observations": direct,
        "events": event_data,
        "interpretation": "explanatory_only_preserves_stored_outcome",
    }, None


def diagnose(collection_path, publication_path):
    """Return ``(report, exit_code)`` for the read-only diagnostic command."""
    publication_bytes = supplied_regular_file(publication_path)
    collection = supplied_collection(collection_path)
    if publication_bytes is None or collection is None:
        return unavailable([{"code": "unreadable_supplied_input"}]), 1
    publication = parse_json_bytes(publication_bytes)
    if publication is None:
        return unavailable([{"code": "malformed_publication"}]), 1
    validated, errors = validate_archive(collection, publication)
    if errors:
        return unavailable(errors), 1
    source_hash = budget.sha256_file(budget.__file__)
    runs = []
    for run_id, row, _run_dir, artifacts in validated:
        record, error = diagnose_row(run_id, row, artifacts, source_hash)
        if error is not None:
            add_error(errors, error, run_id)
        else:
            runs.append(record)
    if errors:
        return unavailable(errors), 1
    category_counts = Counter(record["category"] for record in runs)
    direct_form_counts = Counter(
        form for record in runs for direct in record["direct_observations"] for form in direct["forms"]
    )
    stored_coverage_counts = Counter(
        record["stored_statuses"]["required_verification_coverage_status"] for record in runs
    )
    stored_evidence_counts = Counter(record["stored_statuses"]["verification_evidence_status"] for record in runs)
    return {
        "schema": DIAGNOSTIC_SCHEMA,
        "diagnostic_status": "complete",
        "read_only": True,
        "publication_sha256": budget.sha256_bytes(publication_bytes),
        "frozen_supervisor_source_sha256": source_hash,
        "diagnostic_source_sha256": budget.sha256_file(__file__),
        "status_agreement": {"status": "matched", "run_count": len(runs)},
        "summary": {
            "category_counts": dict(sorted(category_counts.items())),
            "direct_parser_rejected_form_counts": dict(sorted(direct_form_counts.items())),
            "stored_coverage_status_counts": dict(sorted(stored_coverage_counts.items())),
            "stored_evidence_status_counts": dict(sorted(stored_evidence_counts.items())),
        },
        "runs": sorted(runs, key=lambda record: record["run_id"]),
        "interpretation": (
            "Parser-rejected characters and syntactic suffixes explain strict matcher uncertainty only; "
            "they do not prove shell side effects, endpoint execution, or verification coverage."
        ),
    }, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True, help="retained archive collection directory")
    parser.add_argument("--publication", required=True, help="public results projection JSON")
    args = parser.parse_args(argv)
    report, status = diagnose(args.collection, args.publication)
    print(json.dumps(report, indent=2, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
