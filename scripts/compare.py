#!/usr/bin/env python3
"""Compare public AGENTS.md and CLAUDE.md files against the criteria in docs/criteria.json.

Subcommands (flags, one at a time):
    --refresh          fetch every corpus file at its pinned commit, evaluate it and write
                       docs/data/comparison.json (network: raw.githubusercontent.com and
                       api.github.com, read-only)
    (no flag)          render docs/generated/comparison.md from the committed JSON, and the
                       block between the comparison markers in docs/index.html if that file
                       exists (no network)
    --check            render to memory and compare with what is on disk; exit 1 on a
                       difference (no network)
    --file PATH        evaluate one local file with the same engine and print the verdicts

The evaluation engine is `evaluate()`. docs/compare.js implements the same function for the
browser; tests/test_compare.py proves the two agree. Standard library only.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "corpus.toml"
CRITERIA = REPO_ROOT / "docs" / "criteria.json"
COMPARISON_JSON = REPO_ROOT / "docs" / "data" / "comparison.json"
COMPARISON_MD = REPO_ROOT / "docs" / "generated" / "comparison.md"
INDEX_HTML = REPO_ROOT / "docs" / "index.html"
CACHE_DIR = REPO_ROOT / "data" / "cache" / "corpus"

USER_AGENT = "agent-md-lab compare.py"
RAW_URL = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
VIEW_URL = "https://github.com/{repo}/blob/{ref}/{path}"
API_REPO_URL = "https://api.github.com/repos/{repo}"
MARKER_START = "<!-- comparison:start -->"
MARKER_END = "<!-- comparison:end -->"

MAX_EVIDENCE = 3
SIBLING_OF = {"AGENTS.md": "CLAUDE.md", "CLAUDE.md": "AGENTS.md"}
AGENTS_MD_POINTER = re.compile(r"@AGENTS\.md|\bAGENTS\.md\b", re.ASCII)


# --------------------------------------------------------------------------- engine


def normalize(text):
    """Line endings only. Both engines split on "\n" so that they see the same lines."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_lines(text):
    return normalize(text).split("\n")


def count_lines(text):
    """Newline-terminated lines, the same number `wc -l` prints."""
    return normalize(text).count("\n")


def compile_pattern(pattern, flags):
    options = re.ASCII
    if "i" in flags:
        options |= re.IGNORECASE
    if "m" in flags:
        options |= re.MULTILINE
    return re.compile(pattern, options)


def matching_lines(lines, regex):
    """(line number, text) for every line the regex matches, one-based."""
    return [(i + 1, line) for i, line in enumerate(lines) if regex.search(line)]


def evidence_from(hits):
    return [{"line": number, "text": text} for number, text in hits[:MAX_EVIDENCE]]


def evaluate_regex_rule(lines, pattern, flags, pass_if):
    hits = matching_lines(lines, compile_pattern(pattern, flags))
    if pass_if == "match":
        return {"pass": bool(hits), "evidence": evidence_from(hits)}
    if pass_if == "no_match":
        return {"pass": not hits, "evidence": evidence_from(hits)}
    raise ValueError("unknown pass_if for a regex rule: %r" % (pass_if,))


def evaluate_criterion(criterion, text, lines):
    kind = criterion["kind"]
    if kind == "lines":
        total = count_lines(text)
        limit = criterion["pass_if"]["max_lines"]
        return {"pass": total <= limit, "evidence": [], "lines": total}
    if kind == "regex":
        return evaluate_regex_rule(lines, criterion["pattern"], criterion["flags"], criterion["pass_if"])
    if kind == "emphasis":
        regex = compile_pattern(criterion["pattern"], criterion["flags"])
        nonempty = [(i + 1, line) for i, line in enumerate(lines) if line.strip()]
        hits = [(number, line) for number, line in nonempty if regex.search(line)]
        limit = int(round(criterion["pass_if"]["max_ratio"] * 1000))
        passed = len(hits) * 1000 <= limit * len(nonempty)
        return {
            "pass": passed,
            "evidence": evidence_from(hits),
            "emphatic_lines": len(hits),
            "nonempty_lines": len(nonempty),
        }
    if kind == "composite":
        results = [
            evaluate_regex_rule(lines, rule["pattern"], rule["flags"], rule["pass_if"])
            for rule in criterion["rules"]
        ]
        if criterion["combine"] != "any":
            raise ValueError("unknown combine: %r" % (criterion["combine"],))
        passed = any(result["pass"] for result in results)
        if passed:
            evidence = next(result["evidence"] for result in results if result["pass"])
        else:
            evidence = [item for result in results for item in result["evidence"]][:MAX_EVIDENCE]
        return {
            "pass": passed,
            "evidence": evidence,
            "rules": [result["pass"] for result in results],
        }
    raise ValueError("unknown criterion kind: %r" % (kind,))


def evaluate(text, filename, criteria):
    """{criterion id: verdict} for one file. `filename` is accepted for parity with the
    JavaScript engine and is not read by any criterion in version 1.0."""
    lines = split_lines(text)
    return {c["id"]: evaluate_criterion(c, text, lines) for c in criteria["criteria"]}


def coverage(verdicts):
    return sum(1 for verdict in verdicts.values() if verdict["pass"])


def drop_evidence_text(verdicts):
    """Line numbers only. Used for a source whose repository has no license, so that no part
    of its text is reproduced here."""
    stripped = {}
    for key, verdict in verdicts.items():
        copy = dict(verdict)
        copy["evidence"] = [{"line": item["line"]} for item in verdict["evidence"]]
        stripped[key] = copy
    return stripped


# --------------------------------------------------------------------------- input


def load_criteria():
    with CRITERIA.open("rb") as handle:
        return json.load(handle)


def load_corpus():
    with CORPUS.open("rb") as handle:
        return tomllib.load(handle)


def read_json(path):
    with path.open("rb") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------- network


def http_get(url):
    """Bytes, or None on 404. Any other error is raised."""
    headers = {"User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = "Bearer " + token
        headers["Accept"] = "application/vnd.github+json"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def fetch_text(url):
    body = http_get(url)
    if body is None:
        return None
    return body.decode("utf-8"), body


def fetch_stars(repo):
    body = http_get(API_REPO_URL.format(repo=repo))
    if body is None:
        raise RuntimeError("repository not found on the GitHub API: " + repo)
    return json.loads(body.decode("utf-8"))["stargazers_count"]


# --------------------------------------------------------------------------- refresh


def cache_write(key, digest, text):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / ("%s-%s.md" % (key, digest[:8]))
    path.write_text(text, encoding="utf-8")
    return path


def sibling_record(repo, commit, path, filename):
    """Only whether the sibling file exists and, for a CLAUDE.md sibling, whether it names
    AGENTS.md. The sibling's text is never stored."""
    sibling_name = SIBLING_OF.get(filename)
    if sibling_name is None:
        return {"path": None, "present": False, "points_to_agents_md": False}
    sibling_path = str(Path(path).parent / sibling_name) if "/" in path else sibling_name
    fetched = fetch_text(RAW_URL.format(repo=repo, ref=commit, path=sibling_path))
    if fetched is None:
        return {"path": sibling_path, "present": False, "points_to_agents_md": False}
    text, _ = fetched
    points = sibling_name == "CLAUDE.md" and bool(AGENTS_MD_POINTER.search(normalize(text)))
    return {"path": sibling_path, "present": True, "points_to_agents_md": points}


def refresh_file(entry, criteria, today):
    repo = entry["repo"]
    commit = entry["commit"]
    path = entry["path"]
    raw_url = RAW_URL.format(repo=repo, ref=commit, path=path)
    fetched = fetch_text(raw_url)
    if fetched is None:
        raise RuntimeError("file not found at its pinned commit: %s %s@%s" % (repo, path, commit))
    text, body = fetched
    digest = hashlib.sha256(body).hexdigest()
    cache_write(entry["key"], digest, text)
    verdicts = evaluate(text, Path(path).name, criteria)
    if entry["license"] == "NONE":
        verdicts = drop_evidence_text(verdicts)
    record = {
        "key": entry["key"],
        "repo": repo,
        "path": path,
        "type": entry["type"],
        "commit": commit,
        "license": entry["license"],
        "license_note": entry.get("license_note", ""),
        "formerly": entry.get("formerly", ""),
        "why": entry["why"],
        "url_view": VIEW_URL.format(repo=repo, ref=commit, path=path),
        "url_raw": raw_url,
        "url_latest": VIEW_URL.format(repo=repo, ref="HEAD", path=path),
        "stars": fetch_stars(repo),
        "stars_at": today,
        "lines": count_lines(text),
        "bytes": len(body),
        "sha256": digest,
        "sibling": sibling_record(repo, commit, path, Path(path).name),
        "criteria": verdicts,
        "met": coverage(verdicts),
        "of": len(criteria["criteria"]),
    }
    return record


def refresh_excluded(entry, today):
    raw_url = RAW_URL.format(repo=entry["repo"], ref="HEAD", path=entry["path"])
    fetched = fetch_text(raw_url)
    if fetched is None:
        raise RuntimeError("excluded file not found at HEAD: %s %s" % (entry["repo"], entry["path"]))
    text, _ = fetched
    return {
        "repo": entry["repo"],
        "path": entry["path"],
        "lines": count_lines(text),
        "lines_at": today,
        "reason": entry["reason"],
        "url_latest": VIEW_URL.format(repo=entry["repo"], ref="HEAD", path=entry["path"]),
    }


def cmd_refresh(out_path):
    criteria = load_criteria()
    corpus = load_corpus()
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    data = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "criteria_version": criteria["version"],
        "files": [refresh_file(entry, criteria, today) for entry in corpus["files"]],
        "excluded": [refresh_excluded(entry, today) for entry in corpus["excluded"]],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(out_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s (%d files, %d excluded)" % (out_path, len(data["files"]), len(data["excluded"])))
    return 0


# --------------------------------------------------------------------------- render


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def render_table(data, criteria):
    ids = [c["id"] for c in criteria["criteria"]]
    header = ["File", "Type", "Stars", "Lines", "License"]
    header += [str(i + 1) for i in range(len(ids))]
    header += ["Coverage"]
    rows = [header, ["---"] * len(header)]
    for record in data["files"]:
        row = [
            "[%s](%s)" % (record["repo"], record["url_view"]),
            record["type"],
            "{:,}".format(record["stars"]),
            str(record["lines"]),
            record["license"],
        ]
        row += ["\u2713" if record["criteria"][i]["pass"] else "\u2717" for i in ids]
        row += ["%d/%d" % (record["met"], record["of"])]
        rows.append(row)
    totals = ["Met by", "", "", "", ""]
    totals += [str(sum(1 for r in data["files"] if r["criteria"][i]["pass"])) for i in ids]
    totals += ["of %d files" % len(data["files"])]
    rows.append(totals)
    return "\n".join("| " + " | ".join(cell for cell in row) + " |" for row in rows)


def render_markdown(data, criteria):
    ids = [c["id"] for c in criteria["criteria"]]
    out = []
    out.append("# Comparison of published instruction files")
    out.append("")
    out.append(
        "Generated by `python3 scripts/compare.py` from `docs/data/comparison.json`. "
        "Do not edit this file by hand."
    )
    out.append("")
    out.append(
        "Criteria version %s, data generated %s. Every file is pinned by commit in "
        "`corpus.toml`. Coverage is the number of criteria a file meets; it is a description "
        "of what the file contains, not a judgement of the project."
        % (data["criteria_version"], data["generated_utc"])
    )
    out.append("")
    out.append(render_table(data, criteria))
    out.append("")
    out.append("\u2713 = the criterion is met, \u2717 = it is not. Columns:")
    out.append("")
    for index, criterion in enumerate(criteria["criteria"]):
        out.append("%d. **%s** (`%s`) — %s" % (index + 1, criterion["name"], criterion["id"], criterion["question"]))
    out.append("")
    out.append("## Files left out for length")
    out.append("")
    out.append(
        "Well-known instruction files that the survey does not cover, because the survey is "
        "about files of 200 lines or fewer. Line counts are `wc -l` counts at the "
        "default-branch HEAD on the date shown, so they move as the files are edited."
    )
    out.append("")
    out.append("| File | Lines | Measured | Reason |")
    out.append("| --- | --- | --- | --- |")
    for record in data["excluded"]:
        out.append(
            "| [%s/%s](%s) | %d | %s | %s |"
            % (record["repo"], record["path"], record["url_latest"], record["lines"], record["lines_at"], record["reason"])
        )
    out.append("")
    out.append("## Sibling files")
    out.append("")
    out.append(
        "Whether the same commit also carries the other file name, and whether a sibling "
        "`CLAUDE.md` names `AGENTS.md`. Only these two facts are recorded; the sibling's text "
        "is never read into the data."
    )
    out.append("")
    out.append("| File | Sibling | Present | Names AGENTS.md |")
    out.append("| --- | --- | --- | --- |")
    for record in data["files"]:
        sibling = record["sibling"]
        out.append(
            "| %s | %s | %s | %s |"
            % (
                record["repo"],
                sibling["path"] or "-",
                "yes" if sibling["present"] else "no",
                "yes" if sibling["points_to_agents_md"] else "no",
            )
        )
    out.append("")
    ids_used = ", ".join("`%s`" % i for i in ids)
    out.append("Criteria in this table: %s." % ids_used)
    out.append("")
    return "\n".join(out)


def render_index_block(data, criteria):
    return MARKER_START + "\n" + render_table(data, criteria) + "\n" + MARKER_END


def replace_marked_block(html, block):
    start = html.find(MARKER_START)
    end = html.find(MARKER_END)
    if start == -1 or end == -1:
        raise RuntimeError("docs/index.html has no comparison markers")
    return html[:start] + block + html[end + len(MARKER_END):]


def rendered_outputs():
    """{path: expected text} for every file the renderer owns."""
    data = read_json(COMPARISON_JSON)
    criteria = load_criteria()
    if data["criteria_version"] != criteria["version"]:
        raise RuntimeError(
            "comparison.json was generated with criteria version %s but docs/criteria.json is %s; "
            "run --refresh" % (data["criteria_version"], criteria["version"])
        )
    outputs = {COMPARISON_MD: render_markdown(data, criteria)}
    if INDEX_HTML.exists():
        html = INDEX_HTML.read_text(encoding="utf-8")
        outputs[INDEX_HTML] = replace_marked_block(html, render_index_block(data, criteria))
    return outputs


def cmd_render():
    for path, text in rendered_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, text)
        print("wrote %s" % path)
    return 0


def cmd_check():
    differences = []
    for path, text in rendered_outputs().items():
        if not path.exists():
            differences.append("%s is missing" % path)
        elif path.read_text(encoding="utf-8") != text:
            differences.append("%s differs from what the data renders" % path)
    data = read_json(COMPARISON_JSON)
    keys = {record["key"] for record in data["files"]}
    corpus_keys = {entry["key"] for entry in load_corpus()["files"]}
    if keys != corpus_keys:
        differences.append(
            "comparison.json covers %s but corpus.toml lists %s"
            % (sorted(keys), sorted(corpus_keys))
        )
    for record in data["files"]:
        if record["met"] != coverage(record["criteria"]):
            differences.append("%s: met does not match the verdicts" % record["key"])
    for message in differences:
        print("check: " + message, file=sys.stderr)
    if differences:
        return 1
    print("check: %d files, rendered output matches the data" % len(data["files"]))
    return 0


# --------------------------------------------------------------------------- one file


def cmd_file(path, name):
    criteria = load_criteria()
    text = Path(path).read_text(encoding="utf-8")
    verdicts = evaluate(text, name or Path(path).name, criteria)
    print("%s — %d lines" % (path, count_lines(text)))
    for criterion in criteria["criteria"]:
        verdict = verdicts[criterion["id"]]
        print("%s %-28s %s" % ("\u2713" if verdict["pass"] else "\u2717", criterion["id"], criterion["question"]))
        if criterion["kind"] == "emphasis":
            print("      %d of %d non-empty lines" % (verdict["emphatic_lines"], verdict["nonempty_lines"]))
        for item in verdict["evidence"]:
            print("      line %d: %s" % (item["line"], item.get("text", "").strip()))
    print("coverage: %d/%d" % (coverage(verdicts), len(criteria["criteria"])))
    return 0


# --------------------------------------------------------------------------- cli


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="fetch the corpus and rewrite the data")
    parser.add_argument("--out", help="where --refresh writes the JSON (default docs/data/comparison.json)")
    parser.add_argument("--check", action="store_true", help="compare the rendered output with the files on disk")
    parser.add_argument("--file", help="evaluate one local file and print the verdicts")
    parser.add_argument("--name", help="file name to report for --file (default the file's own name)")
    args = parser.parse_args(argv)

    chosen = [flag for flag in (args.refresh, args.check, bool(args.file)) if flag]
    if len(chosen) > 1:
        parser.error("--refresh, --check and --file are separate modes")
    if args.refresh:
        return cmd_refresh(Path(args.out) if args.out else COMPARISON_JSON)
    if args.check:
        return cmd_check()
    if args.file:
        return cmd_file(args.file, args.name)
    return cmd_render()


if __name__ == "__main__":
    sys.exit(main())
