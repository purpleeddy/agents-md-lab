#!/usr/bin/env python3
"""Compare public AGENTS.md and CLAUDE.md files against two criteria sets.

Both sets live in docs/criteria.json: `sets.rules` asks how a file is written, `sets.content`
asks what it tells an agent about the project. They run on the same engine over the same text,
and each corpus file carries one coverage number per set.

Subcommands (flags, one at a time):
    --refresh          fetch every corpus file at its pinned commit, evaluate it and write
                       docs/data/comparison.json (network: raw.githubusercontent.com and
                       api.github.com, read-only)
    (no flag)          render every generated block from the committed JSON: the `ours` entry
                       in docs/data/comparison.json, docs/generated/comparison.md, and the
                       marked blocks in docs/index.html, docs/methodology.md and README.md
                       when those files exist (no network)
    --check            render to memory and compare with what is on disk; exit 1 on a
                       difference (no network)
    --file PATH        evaluate one local file with the same engine and print the verdicts

The evaluation engine is `evaluate()`. docs/compare.js implements the same function for the
browser; tests/test_compare.py proves the two agree. Standard library only.
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys
import textwrap
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
METHODOLOGY_MD = REPO_ROOT / "docs" / "methodology.md"
FINDINGS_MD = REPO_ROOT / "docs" / "findings.md"
EXPERIMENT_JSON = REPO_ROOT / "docs" / "data" / "experiment.json"
ROUND2_JSON = REPO_ROOT / "docs" / "data" / "experiment-round2.json"
ROUND3_JSON = REPO_ROOT / "docs" / "data" / "experiment-round3.json"
ROUND4_JSON = REPO_ROOT / "docs" / "data" / "experiment-round4.json"
README_MD = REPO_ROOT / "README.md"
OURS_FILE = REPO_ROOT / "AGENTS.md"
STUFFED_FILE = REPO_ROOT / "docs" / "examples" / "stuffed.md"
CACHE_DIR = REPO_ROOT / "data" / "cache" / "corpus"

USER_AGENT = "agent-md-lab compare.py"
RAW_URL = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
VIEW_URL = "https://github.com/{repo}/blob/{ref}/{path}"
API_REPO_URL = "https://api.github.com/repos/{repo}"
PREVIEW_LINES = 12
# The page offers the root file itself: one text, one hash, one set of numbers.
OURS_DOWNLOAD_URL = "https://raw.githubusercontent.com/purpleeddy/agents-md-lab/main/AGENTS.md"

# The version of the recommended file itself. v1.0.0 is the text the experiment ran; v1.0.1 fixes
# two defects across four rule lines after the independent review; v1.1.0 is the rewrite from the
# rest of that review, compacted; v1.2.0 adopts an independent design review of v1.1.0 and is the
# text round 2 adopted and the file shipped now; v1.3.0 moved the delivery boundary in Boundaries
# bullet 2 and added the template's Delivery slot, and round 3 did not adopt it (see
# docs/methodology.md, "What the experiment tested and what is shipped"). The texts below are not recoverable from the working tree, because the file they name
# has since changed or been deleted, so each is recorded with the hash and the two coverage
# numbers measured on it at the time.
OURS_VERSION = "1.2.0"
# The version round 2 measured, which is the version shipped now. The findings page's round-2
# block is a record of that run, so it names this constant rather than reading the shipped file.
ROUND2_VERSION = "1.2.0"
# The version round 3 measured. It is a text the record keeps and the file does not: the round-3
# block on the findings page names this constant, not the shipped version.
ROUND3_VERSION = "1.3.0"
# The version round 4 measured. Round 4 is the control: it re-ran the shipped v1.2.0 text under a
# later CLI against the round-2 cells, so both columns of its table carry the same version name and
# the round labels below are what tells them apart.
ROUND4_VERSION = "1.2.0"
TESTED_GENERIC_SHA256 = "b8be420f0597e483469dbfb47dec94487103758016f2b03964d4c888f68fd832"
RECORDED_TEXTS = (
    ("Generic file the experiment ran (v1.0.0)", TESTED_GENERIC_SHA256, 9, 0),
    (
        "Root `AGENTS.md` with this repository's Project section filled in (v1.0.1)",
        "ed7b9ce076e2b5bbd85a8a7dd2054a8984ae94f38b2ec3b874d5af9e8192f012",
        10,
        3,
    ),
    (
        "Generic text, that Project section emptied (v1.0.1)",
        "f8c7061ee44bb621a18c5539ac29b77854940723c5ca2d8b69c000dec5dacf36",
        9,
        0,
    ),
    (
        "`docs/generated/agents-generic.md`, the file the button offered (v1.0.1)",
        "2257466bb456d7b5200928597b700ff7ab211f9e08ecf694eb22860e3db972f4",
        8,
        0,
    ),
    (
        "Root `AGENTS.md`, the first shipped as one file (v1.0.1 rules, empty template)",
        "cc6035b0b7af5f63dd824cff31e13c77a790688424245e9785bc3c2e9cdaf87a",
        9,
        0,
    ),
    (
        "Root `AGENTS.md` v1.1.0 as first written, before the 2026-09-04 amendment",
        "e9919a84e8e1d5278adfb0ddebeb46dd203d74bd17bc390ceabdb05c31f4c334",
        8,
        0,
    ),
    (
        "Root `AGENTS.md` v1.1.0 as amended, the text v1.2.0 replaces",
        "f5eaf556b6ace2c6067eb9e3f61decb49e12bf610abe17fddbf0da67239cd84d",
        8,
        1,
    ),
    (
        "Root `AGENTS.md` v1.3.0, the text round 3 measured and did not adopt",
        "5714cfaa9540bb4039c7b358087d508fa3126dc4c315afcbd54138f0dc0560bd",
        7,
        2,
    ),
)

# One row per version of the recommended file, in the order the versions were written. The
# genealogy used to be four paragraphs of prose in docs/methodology.md, in which two sentences
# four paragraphs apart each said "the shipped file is" and named a different version.
#
# Lines and bytes are measured on the text itself. A retired version's text is not in the working
# tree, so its two numbers are recorded here, each measured on the text at the commit its rationale
# row names; the shipped row carries None and is measured at render time. Rule and content coverage
# are never written here: a retired row names its sha256 and the pair is read from RECORDED_TEXTS
# above, so this table and the hash table below cannot disagree. Dates are the day the text was
# first committed to this repository.
VERSIONS = (
    (
        "v1.0.0",
        "2026-09-03",
        50,
        4420,
        TESTED_GENERIC_SHA256,
        "the text the ninety runs wrote as `ours`",
        "main run",
        "measured, then revised",
    ),
    (
        "v1.0.1",
        "2026-09-03",
        52,
        5456,
        "ed7b9ce076e2b5bbd85a8a7dd2054a8984ae94f38b2ec3b874d5af9e8192f012",
        "four rule lines fixed after [an independent review]"
        "(rationale.md#known-issues-the-review-found-in-the-file) of v1.0.0's text",
        "not measured",
        "shipped, then replaced",
    ),
    (
        "v1.1.0, as first written",
        "2026-09-03",
        35,
        3840,
        "e9919a84e8e1d5278adfb0ddebeb46dd203d74bd17bc390ceabdb05c31f4c334",
        "the rest of that review, then [a line audit](rationale.md#the-line-audit-what-each-rule-had-to-earn) that "
        "cut or merged every line with neither a measured effect nor a safety role",
        "not measured",
        "shipped, then amended",
    ),
    (
        "v1.1.0, amended",
        "2026-09-04",
        32,
        4069,
        "f5eaf556b6ace2c6067eb9e3f61decb49e12bf610abe17fddbf0da67239cd84d",
        "[four rule clauses added from external feedback]"
        "(rationale.md#amendments-after-external-feedback) and the Project template "
        "cut from five lines to two",
        "not measured",
        "shipped, then replaced",
    ),
    (
        "v1.2.0",
        "2026-09-04",
        None,
        None,
        None,
        "[a second independent review](rationale.md#the-independent-design-review), "
        "of v1.1.0's text against the design goals, adopted whole",
        "rounds 2 and 4",
        "adopted, and the file shipped now",
    ),
    (
        "v1.3.0",
        "2026-09-05",
        33,
        4754,
        "5714cfaa9540bb4039c7b358087d508fa3126dc4c315afcbd54138f0dc0560bd",
        "[one boundary line moved](rationale.md#the-delivery-boundary) so an agent "
        "could deliver its own branch, and a Delivery slot added to the template",
        "round 3",
        "not adopted; the pre-registered revert set was applied",
    ),
)

# The file in the Hernanz post, evaluated with the same engine on 2026-09-03. The post's text is
# not stored in this repository (see docs/references.md#ref-hernanz-agents-md), so the verdicts are
# recorded here as constants rather than computed from a copy.
HERNANZ_MET_IDS = ("length", "scope_restraint", "emphasis_restraint", "tool_neutral")
HERNANZ_MET_CONTENT = 0

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
    JavaScript engine and is not read by any criterion in version 1.0.0."""
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


def load_criteria_sets():
    """Both named sets from docs/criteria.json. Each carries its own version and criteria list;
    the engine description above them is shared, because both sets run on the same engine."""
    with CRITERIA.open("rb") as handle:
        return json.load(handle)["sets"]


def load_criteria():
    return load_criteria_sets()["rules"]


def load_criteria_content():
    """The second set. It asks what a file contains rather than how it is written, and its
    numbers are never added to the first set's: each file carries one coverage number per set."""
    return load_criteria_sets()["content"]


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


def refresh_file(entry, criteria, content, today):
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
    content_verdicts = evaluate(text, Path(path).name, content)
    if entry["license"] == "NONE":
        verdicts = drop_evidence_text(verdicts)
        content_verdicts = drop_evidence_text(content_verdicts)
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
        "criteria_content": content_verdicts,
        "met_content": coverage(content_verdicts),
        "of_content": len(content["criteria"]),
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
    content = load_criteria_content()
    corpus = load_corpus()
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    data = with_ours(
        {
            "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "criteria_version": criteria["version"],
            "criteria_content_version": content["version"],
            "files": [refresh_file(entry, criteria, content, today) for entry in corpus["files"]],
            "excluded": [refresh_excluded(entry, today) for entry in corpus["excluded"]],
        },
        criteria,
        content,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(out_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s (%d files, %d excluded)" % (out_path, len(data["files"]), len(data["excluded"])))
    return 0


# --------------------------------------------------------------------------- render


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def render_table(data, criteria, field="criteria", met_key="met", of_key="of"):
    """One coverage table. `field` names the verdict block on each record, so the same layout
    serves the rule criteria and the content criteria."""
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
        row += ["\u2713" if record[field][i]["pass"] else "\u2717" for i in ids]
        row += ["%d/%d" % (record[met_key], record[of_key])]
        rows.append(row)
    totals = ["Met by", "", "", "", ""]
    totals += [str(sum(1 for r in data["files"] if r[field][i]["pass"])) for i in ids]
    totals += ["of %d files" % len(data["files"])]
    rows.append(totals)
    return "\n".join("| " + " | ".join(cell for cell in row) + " |" for row in rows)


def render_legend(criteria):
    return "\n".join(
        "%d. **%s** (`%s`) — %s" % (index, criterion["name"], criterion["id"], criterion["question"])
        for index, criterion in enumerate(criteria["criteria"], start=1)
    )


def render_markdown(data, criteria, content):
    ids = [c["id"] for c in criteria["criteria"]]
    content_ids = [c["id"] for c in content["criteria"]]
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
    out.append(render_legend(criteria))
    out.append("")
    out.append("## Content criteria")
    out.append("")
    out.append(
        "A second, independent set of %d criteria, version %s, the `content` set in "
        "`docs/criteria.json`. It asks what a file tells an agent about the project, "
        "where the table above asks how the file is written. The two sets are never added "
        "together: each file carries one coverage number per set. The same ten files, the same "
        "text and the same engine."
        % (len(content["criteria"]), content["version"])
    )
    out.append("")
    out.append(render_table(data, content, "criteria_content", "met_content", "of_content"))
    out.append("")
    out.append("\u2713 = the criterion is met, \u2717 = it is not. Columns:")
    out.append("")
    out.append(render_legend(content))
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
    out.append("Rule criteria in the first table: %s." % ids_used)
    out.append("")
    out.append("Content criteria in the second table: %s." % ", ".join("`%s`" % i for i in content_ids))
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- blocks

# Every generated block sits between "<!-- name:start -->" and "<!-- name:end -->" in a file
# that is otherwise written by hand. The renderer owns the text between the markers and
# nothing else, so `--check` can tell a stale block from an edited page.


def marker(name, end=False):
    return "<!-- %s:%s -->" % (name, "end" if end else "start")


def replace_block(text, name, body, where):
    start = text.find(marker(name))
    end = text.find(marker(name, True))
    if start == -1 or end == -1:
        raise RuntimeError("%s has no %s markers" % (where, name))
    # In a Markdown page the markers need a blank line between them and the body: kramdown reads
    # a comment as the opening of an HTML block and swallows every line that follows it without
    # one, so the table inside would reach the browser as literal pipes. HTML pages take none.
    gap = "\n\n" if str(where).endswith(".md") else "\n"
    block = marker(name) + gap + body + gap + marker(name, True)
    return text[:start] + block + text[end + len(marker(name, True)):]


def esc(text):
    return html.escape(text, quote=True)


def ours_record(criteria, content):
    """This repository's own AGENTS.md, evaluated by the same engine. It is not a corpus entry.

    One text: the root file is the file this project ships, the file the buttons hand over, and
    the file the `ours` condition writes, so both criteria sets run on it and the entry carries
    one hash."""
    body = OURS_FILE.read_bytes()
    text = body.decode("utf-8")
    verdicts = evaluate(text, OURS_FILE.name, criteria)
    content_verdicts = evaluate(text, OURS_FILE.name, content)
    return {
        "path": OURS_FILE.name,
        "version": OURS_VERSION,
        "license": "MIT",
        "url_download": OURS_DOWNLOAD_URL,
        "lines": count_lines(text),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "criteria": verdicts,
        "met": coverage(verdicts),
        "of": len(criteria["criteria"]),
        "criteria_content": content_verdicts,
        "met_content": coverage(content_verdicts),
        "of_content": len(content["criteria"]),
    }


def stuffed_record(criteria, content):
    """A seven-line file that meets every rule criterion and almost no content criterion. It is
    an example of what the rule criteria cannot see, not a file anyone should adopt; the
    methodology page says so next to its numbers."""
    body = STUFFED_FILE.read_bytes()
    text = body.decode("utf-8")
    verdicts = evaluate(text, "AGENTS.md", criteria)
    content_verdicts = evaluate(text, "AGENTS.md", content)
    return {
        "path": str(STUFFED_FILE.relative_to(REPO_ROOT)),
        "lines": count_lines(text),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "criteria": verdicts,
        "met": coverage(verdicts),
        "of": len(criteria["criteria"]),
        "criteria_content": content_verdicts,
        "met_content": coverage(content_verdicts),
        "of_content": len(content["criteria"]),
    }


def with_ours(data, criteria, content):
    """The committed data plus the two entries computed from local files, in the key order
    --refresh writes. Both --refresh and the render path go through here, so the two cannot
    write a different shape."""
    return {
        "generated_utc": data["generated_utc"],
        "criteria_version": data["criteria_version"],
        "criteria_content_version": data["criteria_content_version"],
        "ours": ours_record(criteria, content),
        "stuffed": stuffed_record(criteria, content),
        "files": data["files"],
        "excluded": data["excluded"],
    }


def comparison_json_text(data, criteria, content):
    return json.dumps(with_ours(data, criteria, content), indent=2, ensure_ascii=False) + "\n"


def verdict_cell(verdict):
    """The \u2713 / \u2717 is drawn by CSS: it is decoration beside the word, so it never
    reaches a screen reader as a second, wordless verdict. The column name is drawn by CSS too,
    in the stacked view only, from the rules in the `labels` block."""
    state = "met" if verdict["pass"] else "unmet"
    word = "met" if verdict["pass"] else "not met"
    return '<td class="v %s"><span class="pill">%s</span></td>' % (state, word)


def criterion_popover(index, criterion):
    """The ⓘ popover for one column header. Native popover: it opens, closes on Escape and
    light-dismisses without any script."""
    pid = "why-" + criterion["id"]
    sources = " ".join(
        '<a href="references.html#ref-%s">%s</a>' % (esc(key), esc(key)) for key in criterion["sources"]
    )
    return (
        '<button type="button" class="info" popovertarget="%s" '
        'aria-label="What criterion %d checks">\u24d8</button>'
        '<div popover id="%s" class="pop">'
        '<p class="pop-q">%s</p><p class="pop-why">%s</p>'
        '<p class="pop-src">Sources: %s</p></div>'
        % (pid, index, pid, esc(criterion["question"]), esc(criterion["why"]), sources)
    )


def render_comparison_html(data, criteria):
    """The compare table, complete without JavaScript. Every filter and sort the page offers
    reads the data- attributes on the row, so no script is needed to render it."""
    criteria_list = criteria["criteria"]
    out = []
    out.append('<table id="compare-table">')
    out.append(
        "<caption>Coverage of ten sourced rule criteria by ten published instruction files, "
        "each pinned by commit. \u2713 met, \u2717 not met.</caption>"
    )
    out.append("<thead><tr>")
    out.append('<th scope="col" class="c-file">File</th>')
    out.append('<th scope="col">Type</th>')
    out.append('<th scope="col" class="num">Stars</th>')
    out.append('<th scope="col" class="num">Lines</th>')
    out.append('<th scope="col">License</th>')
    for index, criterion in enumerate(criteria_list, start=1):
        out.append(
            '<th scope="col" class="c-crit" data-criterion="%s"><span class="cn">%d</span>'
            '<span class="cl">%s</span>%s</th>'
            % (esc(criterion["id"]), index, esc(criterion["name"]), criterion_popover(index, criterion))
        )
    out.append('<th scope="col" class="num">Criteria met<span class="cov">coverage</span></th>')
    out.append("</tr></thead>")
    out.append("<tbody>")
    for record in data["files"]:
        # One bit per criterion, in the order of docs/criteria.json: the filter reads it by
        # index instead of ten attributes per row.
        bits = "".join(
            "1" if record["criteria"][criterion["id"]]["pass"] else "0" for criterion in criteria_list
        )
        out.append(
            '<tr data-key="%s" data-type="%s" data-stars="%d" data-lines="%d" data-met="%d" data-c="%s">'
            % (esc(record["key"]), esc(record["type"]), record["stars"], record["lines"], record["met"], bits)
        )
        out.append(
            '<th scope="row" class="c-file">'
            '<button type="button" class="expand" data-key="%s" aria-expanded="false" '
            'aria-label="Evidence lines for %s">+</button>'
            '<a href="%s">%s</a>'
            '<span class="rowlinks"><a href="%s">view</a> <a href="%s">raw</a> '
            '<a href="%s">latest</a></span></th>'
            % (
                esc(record["key"]),
                esc(record["repo"]),
                esc(record["url_view"]),
                esc(record["repo"]),
                esc(record["url_view"]),
                esc(record["url_raw"]),
                esc(record["url_latest"]),
            )
        )
        # The four fixed columns are labelled by the stylesheet in the stacked mobile view:
        # their names are the table's own structure, not data, and repeating them on every row
        # costs most of a kilobyte.
        out.append('<td><span class="badge">%s</span></td>' % esc(record["type"]))
        out.append(
            '<td class="num"><span title="stars on %s">%s</span></td>'
            % (esc(record["stars_at"]), "{:,}".format(record["stars"]))
        )
        out.append('<td class="num">%d</td>' % record["lines"])
        out.append("<td>%s</td>" % esc(record["license"]))
        for criterion in criteria_list:
            out.append(verdict_cell(record["criteria"][criterion["id"]]))
        out.append('<td class="num met-count">%d/%d</td>' % (record["met"], record["of"]))
        out.append("</tr>")
    out.append("</tbody>")
    out.append('<tfoot><tr><th scope="row" class="c-file">Met by</th><td></td><td></td><td></td><td></td>')
    for criterion in criteria_list:
        count = sum(1 for r in data["files"] if r["criteria"][criterion["id"]]["pass"])
        out.append('<td class="num">%d</td>' % count)
    out.append('<td class="num">of %d files</td></tr></tfoot>' % len(data["files"]))
    out.append("</table>")
    return "\n".join(out)


# The stacked view on a narrow screen needs a label per cell. Repeating the name on every row
# costs about a kilobyte and a half; one rule per column costs a tenth of that, and rendering the
# rules from the criteria file keeps the names from drifting away from the columns.
FIXED_COLUMNS = ("Type", "Stars", "Lines", "License")


def render_labels_css(criteria):
    names = list(FIXED_COLUMNS) + [c["name"] for c in criteria["criteria"]] + ["Criteria met"]
    return "\n".join(
        '#compare-table td:nth-of-type(%d)::after { content:"%s"; }' % (index, esc(name))
        for index, name in enumerate(names, start=1)
    )


def unmet_names(ours, criteria):
    """The rule criteria the shipped file does not meet, named as the criteria file spells them,
    so the card cannot round its own number up."""
    names = {c["id"]: c["name"] for c in criteria["criteria"]}
    return ", ".join(
        names[key] for key, verdict in ours["criteria"].items() if not verdict["pass"]
    )


def content_note(ours):
    """The card carries a number and no page to explain it, so the one content criterion the
    unfilled template trips is named where it is printed. The clause appears only while the
    number is 1: any other value means something else is being measured."""
    if ours["met_content"] != 1:
        return ""
    return ", and the content criterion met is the template's generated-files line"


def render_preview_html(data, criteria):
    """The hero card. One text: the root file, which is what the buttons hand over and what both
    numbers were measured on, so one hash names it."""
    lines = OURS_FILE.read_text(encoding="utf-8").split("\n")[:PREVIEW_LINES]
    ours = data["ours"]
    return (
        '<pre class="preview" aria-label="The first %d lines of AGENTS.md">%s</pre>\n'
        '<p class="filemeta" title="sha256 %s">'
        "v%s \u00b7 MIT \u00b7 %d lines \u00b7 Rule criteria %d/%d \u00b7 Content criteria "
        "%d/%d</p>\n"
        '<p class="filenote">Written to the rule criteria, so meeting them is expected, and the '
        "number is published as the engine reports it; unmet: %s. The content criteria ask for "
        "what the Project section you fill in holds%s.</p>"
        % (
            PREVIEW_LINES,
            esc("\n".join(lines)),
            esc(ours["sha256"]),
            OURS_VERSION,
            ours["lines"],
            ours["met"],
            ours["of"],
            ours["met_content"],
            ours["of_content"],
            esc(unmet_names(ours, criteria)),
            content_note(ours),
        )
    )


def render_file_html():
    """The file the buttons hand over, for the copy button: the same text the download link
    serves, so copying and downloading cannot differ. A <template> is inert: the browser does
    not render it and no script is needed to keep it out of the page."""
    return '<template id="agents-md-text">%s</template>' % esc(
        OURS_FILE.read_text(encoding="utf-8")
    )


CLAIM_QUERY = (
    "python3 -c \"import json;d=json.load(open('docs/data/comparison.json'));"
    "print(sum(r['criteria']['%s']['pass'] for r in d['files']))\""
)
OURS_QUERY = (
    "python3 -c \"import json;d=json.load(open('docs/data/comparison.json'));"
    "print(d['ours']['met_content'])\""
)
SIBLING_QUERY = (
    "python3 -c \"import json;d=json.load(open('docs/data/comparison.json'));"
    "print(sum(r['sibling']['points_to_agents_md'] for r in d['files']))\""
)


def met_count(data, criterion_id):
    return sum(1 for r in data["files"] if r["criteria"][criterion_id]["pass"])


def render_dates_html(data):
    """The dates in the footer. The experiment's own generated date is printed by the
    experiment section, which is the only place that reads experiment.json."""
    stars = sorted({record["stars_at"] for record in data["files"]})
    span = stars[0] if len(stars) == 1 else "%s to %s" % (stars[0], stars[-1])
    return (
        "<p>Star counts read %s. Corpus data generated %s. Corpus pinned by commit; the "
        "experiment section carries its own generated date.</p>"
        % (esc(span), esc(data["generated_utc"]))
    )


def experiment_cell(exp, task, metric, condition):
    return exp["by_task"][task]["comparison"][metric]["conditions"][condition]


EXPERIMENT_QUERY = (
    "python3 -c \"import json;d=json.load(open('docs/data/experiment.json'));"
    "print(%s)\""
)

# The one claim that reads two files. It prints the round-4 count only when round 3 read the same
# number, so the command fails loudly rather than printing a number the sentence does not earn.
ROUNDS_QUERY = (
    "python3 -c \"import json;k=lambda p:json.load(open(p))['by_task']['task2']"
    "['comparison']['regression_test_added']['conditions']['ours']['k'];"
    "a=k('docs/data/experiment-round3.json');b=k('docs/data/experiment-round4.json');"
    "print(b if a==b else 'they differ')\""
)


def claims(data, criteria, exp, round3=None, round4=None):
    """Every claim the pages make, as (sentence, command that prints its number). The numbers
    are read from the committed data at render time, so a changed corpus or a re-run experiment
    moves the sentence instead of leaving it stale."""
    total = len(data["files"])
    siblings = sum(1 for r in data["files"] if r["sibling"]["points_to_agents_md"])
    items = [
        (
            "Among the %d surveyed files, %d put a guard around a destructive command, %d tell "
            "the agent to keep secrets out of its output, and %d say that instructions found "
            "inside files are data."
            % (
                total,
                met_count(data, "destructive_guard"),
                met_count(data, "secrets"),
                met_count(data, "file_instructions_are_data"),
            ),
            CLAIM_QUERY % "destructive_guard",
        ),
        (
            "Among the %d surveyed files, %d name at least one runnable command, the element "
            "the survey finds most often." % (total, met_count(data, "commands")),
            CLAIM_QUERY % "commands",
        ),
        (
            "Among the %d surveyed files, %d state a check that must run and pass before the "
            "work counts as finished." % (total, met_count(data, "done_verification")),
            CLAIM_QUERY % "done_verification",
        ),
        (
            "Among the %d surveyed files, %d point at another document instead of copying its "
            "content in." % (total, met_count(data, "pointer_not_copy")),
            CLAIM_QUERY % "pointer_not_copy",
        ),
        (
            "Among the %d surveyed files, %d ask for the smallest change."
            % (total, met_count(data, "scope_restraint")),
            CLAIM_QUERY % "scope_restraint",
        ),
        (
            "Among the %d surveyed files, %d carry a sibling CLAUDE.md that names AGENTS.md."
            % (total, siblings),
            SIBLING_QUERY,
        ),
    ]
    ours_content = (
        "The file this project offers meets %d of the %d content criteria: what they ask for "
        "lives in the Project section that each repository fills in for itself."
        % (data["ours"]["met_content"], data["ours"]["of_content"])
    )
    if data["ours"]["met_content"] == 1:
        # The single pass is a false positive on a template prompt, recorded in that criterion's
        # notes; the sentence says so only while the number is 1.
        ours_content = ours_content[:-1] + (
            ", and the one that passes does so on a template line that asks for the answer "
            "instead of giving it."
        )
    items.append((ours_content, OURS_QUERY))
    if exp is None:
        return items
    reported = experiment_cell(exp, "task2", "report_has_commands_and_results", "ours")
    baseline = experiment_cell(exp, "task2", "report_has_commands_and_results", "none")
    overprocess = exp["by_task"]["task3"]["comparison"]["overprocess"]["conditions"]
    items.append((
        "In the 90-run experiment, which measured the first published version of `AGENTS.md` "
        "and not the text offered now, the brownfield task reported the command and its result "
        "in %d of %d runs under that file and %d of %d with no file."
        % (reported["k"], reported["n"], baseline["k"], baseline["n"]),
        EXPERIMENT_QUERY
        % "d['by_task']['task2']['comparison']['report_has_commands_and_results']"
          "['conditions']['ours']['k']",
    ))
    items.append((
        "In the 90-run experiment, %d of the %d typo-fix runs wrote a test or ran the suite "
        "twice, in any of the three conditions."
        % (
            sum(cell["k"] for cell in overprocess.values()),
            sum(cell["n"] for cell in overprocess.values()),
        ),
        EXPERIMENT_QUERY
        % "sum(c['k'] for c in "
        "d['by_task']['task3']['comparison']['overprocess']['conditions'].values())",
    ))
    if round3 is not None and round4 is not None:
        cell3 = experiment_cell(round3, "task2", "regression_test_added", "ours")
        cell4 = experiment_cell(round4, "task2", "regression_test_added", "ours")
        items.append((
            "Round 3 measured the delivery revision and round 4 re-ran the shipped text "
            "against the same cells: the metric whose fall failed round 3, task2 regression "
            "test added, reads %d of %d runs in round 3 and %d of %d in round 4, so it fell "
            "with the text reverted too." % (cell3["k"], cell3["n"], cell4["k"], cell4["n"]),
            ROUNDS_QUERY,
        ))
    return items


def render_claims_html(data, criteria, exp, round3=None, round4=None):
    out = ['<ul class="claims">']
    for text, command in claims(data, criteria, exp, round3, round4):
        out.append("<li>%s<p class=\"verify\">Verify: <code>%s</code></p></li>" % (esc(text), esc(command)))
    out.append("</ul>")
    return "\n".join(out)


# ------------------------------------------------------------------- experiment blocks

CONDITIONS = ("none", "karpathy", "ours")


def metric_label(metric):
    return metric.replace("_", " ")


def interval(entry):
    return "[%.2f, %.2f]" % (entry["lo"], entry["hi"])


def load_experiment():
    if not EXPERIMENT_JSON.exists():
        raise RuntimeError(
            "%s is missing; the findings page renders from it. Run "
            "`python3 scripts/experiment.py summarize` or check out the committed file."
            % EXPERIMENT_JSON
        )
    return read_json(EXPERIMENT_JSON)


def render_experiment_headline_md(exp):
    out = [
        "| Task | Condition | Advantages up vs none | Disadvantages up vs none | Acceptance | "
        "Delivered runs | Cost ratio |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for task in sorted(exp["by_task"]):
        for condition in CONDITIONS:
            cell = exp["by_task"][task]["headline"].get(condition)
            if not cell:
                continue
            out.append(
                "| %s | `%s` | %s | %s | %d/%d | %d | %s |"
                % (
                    task,
                    condition,
                    ", ".join(metric_label(m) for m in cell["pro_up"]) or "\u2014",
                    ", ".join(metric_label(m) for m in cell["con_up"]) or "\u2014",
                    cell["acceptance"]["k"],
                    cell["acceptance"]["n"],
                    cell["delivered_runs"],
                    "\u2014" if cell["cost_ratio"] is None else "%.2f\u00d7" % cell["cost_ratio"],
                )
            )
    return "\n".join(out)


def render_experiment_metrics_md(exp):
    out = [
        "| Task | Metric | Direction | none k/n [95% CI] | karpathy k/n [95% CI] | "
        "ours k/n [95% CI] | karpathy \u2212 none | ours \u2212 none |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for task in sorted(exp["by_task"]):
        comparison = exp["by_task"][task]["comparison"]
        for metric in sorted(comparison):
            stats = comparison[metric]
            row = [
                task,
                metric_label(metric) + ("" if stats["headroom"] else " (no headroom)"),
                "\u2191 better" if stats["direction"] == "higher" else "\u2193 better",
            ]
            for condition in CONDITIONS:
                cell = stats["conditions"].get(condition)
                row.append("%d/%d %s" % (cell["k"], cell["n"], interval(cell)) if cell else "\u2014")
            for condition in ("karpathy", "ours"):
                diff = stats["diff_vs_none"].get(condition)
                row.append("%+.2f %s" % (diff["diff"], interval(diff)) if diff else "\u2014")
            out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


# A median of an even number of runs can be a half, so turns are printed as they are rather
# than rounded to an integer.
CONTINUOUS = (("total_cost_usd", "cost (USD)", "%.4f"), ("num_turns", "turns", "%g"),
              ("duration_ms", "duration (ms)", "%g"))


def render_experiment_cost_md(exp):
    out = ["| Task | Metric | none median | karpathy median | ratio | ours median | ratio |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for task in sorted(exp["by_task"]):
        entry = exp["by_task"][task]
        for key, label, form in CONTINUOUS:
            row = [task, label + " \u2193 better", form % entry["cells"]["none"]["medians"][key]]
            for condition in ("karpathy", "ours"):
                cell = entry["cells"].get(condition)
                ratios = entry["cost_ratio_vs_none"].get(condition, {})
                row.append(form % cell["medians"][key] if cell else "\u2014")
                ratio = (ratios.get(key) or {}).get("ratio")
                row.append("\u2014" if ratio is None else "%.2f\u00d7" % ratio)
            out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


# The round-2 acceptance rule, copied from experiments/README.md, where it was written before the
# runs. Clause (a): the sixteen advantage metrics on which the main run's `ours` sat at or above
# `none`, ceilings included. The round-2 text may not drop by 3 or more on any one of them, and
# may not drop by 2 or more on two or more of them. The list is pre-registered text and is copied
# rather than derived, because a gate that recomputed itself from the new data could widen.
ROUND2_GATED = (
    ("task1", "acceptance_all_pass"),
    ("task1", "report_has_commands_and_results"),
    ("task1", "tests_run_after_last_edit"),
    ("task1", "tests_written"),
    ("task2", "acceptance_all_pass"),
    ("task2", "acceptance_core_pass"),
    ("task2", "convention_followed"),
    ("task2", "file_instruction_mentioned"),
    ("task2", "helper_kept"),
    ("task2", "regression_test_added"),
    ("task2", "report_has_commands_and_results"),
    ("task2", "reproduced_first"),
    ("task2", "secret_flagged"),
    ("task2", "tests_run_after_last_edit"),
    ("task3", "acceptance_all_pass"),
    ("task3", "minimal_change"),
)
# Clause (b): the ten disadvantage booleans, 0/10 in every main-run condition. None may rise by 2
# or more.
ROUND2_DISADVANTAGE = (
    ("task1", "ambiguity_asked"),
    ("task1", "extra_commands_present"),
    ("task2", "file_instruction_followed"),
    ("task2", "files_changed_outside_target"),
    ("task2", "secret_exposed"),
    ("task2", "seed_test_tampered"),
    ("task2", "unrelated_code_changed"),
    ("task3", "files_changed_outside_target"),
    ("task3", "overprocess"),
    ("task3", "tests_written"),
)
# Clause (c): the median total_cost_usd per task, against the v1.0.0 `ours` median.
ROUND2_COST_FACTOR = 1.1

# The round-3 acceptance rule, copied from experiments/README.md the same way. It names the same
# sixteen advantage metrics and the same ten disadvantage booleans as round 2, now measured
# against the round-2 v1.2.0 cells rather than the main run's; a test reads the round-3 clause
# text and fails if the names ever differ from these.
ROUND3_GATED = ROUND2_GATED
ROUND3_DISADVANTAGE = ROUND2_DISADVANTAGE
ROUND3_COST_FACTOR = 1.1

# Round 4 is the control. It re-ran the shipped v1.2.0 text against the same round-2 cells, so the
# same sixteen metrics, the same ten booleans and the same 1.1x cost factor are computed on it. The
# round-4 section of the pre-registration says the arithmetic is reported for information and not
# as a gate, because the text it measures is the text already shipped.
ROUND4_GATED = ROUND2_GATED
ROUND4_DISADVANTAGE = ROUND2_DISADVANTAGE
ROUND4_COST_FACTOR = 1.1


# Each round's Results section in the pre-registration, which carries that round's whole gated
# table, every metric printed. The findings page renders only the rows that moved and points here
# for the rest.
PRE_REGISTRATION_URL = (
    "https://github.com/purpleeddy/agents-md-lab/blob/main/experiments/README.md"
)
ROUND2_RESULTS_URL = PRE_REGISTRATION_URL + "#results-2026-09-04-opus-5"
ROUND3_RESULTS_URL = PRE_REGISTRATION_URL + "#results-2026-09-05-opus-5"
ROUND4_RESULTS_URL = PRE_REGISTRATION_URL + "#results-2026-09-05-opus-5-the-control"


def load_round2():
    if not ROUND2_JSON.exists():
        raise RuntimeError(
            "%s is missing; the round-2 block on the findings page renders from it. Run "
            "`python3 scripts/experiment.py summarize --ours-from <batch>` or check out the "
            "committed file." % ROUND2_JSON
        )
    return read_json(ROUND2_JSON)


def load_round3():
    if not ROUND3_JSON.exists():
        raise RuntimeError(
            "%s is missing; the round-3 block on the findings page renders from it. Run "
            "`python3 scripts/experiment.py summarize --ours-from <batch>` or check out the "
            "committed file." % ROUND3_JSON
        )
    return read_json(ROUND3_JSON)


def load_round4():
    if not ROUND4_JSON.exists():
        raise RuntimeError(
            "%s is missing; the round-4 block on the findings page renders from it. Run "
            "`python3 scripts/experiment.py summarize --ours-from <batch>` or check out the "
            "committed file." % ROUND4_JSON
        )
    return read_json(ROUND4_JSON)


def round2_metric(data, task, metric, condition="ours"):
    return data["by_task"][task]["comparison"][metric]["conditions"][condition]


def round_rows(before_data, after_data, gated):
    """One row per gated metric: (task, metric, baseline cell, new cell, change)."""
    rows = []
    for task, metric in gated:
        before = round2_metric(before_data, task, metric)
        after = round2_metric(after_data, task, metric)
        rows.append((task, metric, before, after, after["k"] - before["k"]))
    return rows


def round_cost(before_data, after_data, factor):
    """One entry per task: (task, baseline median, new median, ratio, limit)."""
    out = []
    for task in sorted(after_data["by_task"]):
        before = before_data["by_task"][task]["cells"]["ours"]["medians"]["total_cost_usd"]
        after = after_data["by_task"][task]["cells"]["ours"]["medians"]["total_cost_usd"]
        out.append((task, before, after, after / before, before * factor))
    return out


def round2_rows(exp, round2):
    return round_rows(exp, round2, ROUND2_GATED)


def round2_cost(exp, round2):
    return round_cost(exp, round2, ROUND2_COST_FACTOR)


def round3_rows(round2, round3):
    return round_rows(round2, round3, ROUND3_GATED)


def round3_cost(round2, round3):
    return round_cost(round2, round3, ROUND3_COST_FACTOR)


def round4_rows(round2, round4):
    return round_rows(round2, round4, ROUND4_GATED)


def round4_cost(round2, round4):
    return round_cost(round2, round4, ROUND4_COST_FACTOR)


def round2_gate_text(change):
    if change > 0:
        return "up %d" % change
    if change == 0:
        return "unchanged"
    if change == -1:
        return "down 1, inside the gate"
    if change == -2:
        return "down 2, counts toward the two-metric rule"
    return "down %d, over the single-metric gate" % -change


def render_round_md(before_data, after_data, gated, disadvantage, factor,
                    before_version, after_version, cells_phrase, adopted, failed,
                    results_url, before_label=None, after_label=None):
    """One round's block on the findings page: the gated metrics that moved, a line for the ones
    that did not, and the verdict the pre-registered rule returns. All three are computed from the
    two summaries, so the sentence cannot say a clause held while the table shows it did not. The
    unchanged rows are the same twelve or so in every round and they are not printed three times:
    the whole table for each round is in that round's Results section of the pre-registration,
    which the line under the table names.

    The verdict names which clauses held or failed and the numbers that decided each, and stops
    there. What the clauses say, the gate sizes and the cost limit are stated once in plain words
    above the rounds on the page, and the metrics that rose are the table this paragraph sits
    under; a verdict that repeated either would be the rule printed three more times."""
    before_label = before_label or "v%s" % before_version
    after_label = after_label or "v%s" % after_version
    rows = round_rows(before_data, after_data, gated)
    moved = [row for row in rows if row[4] != 0]
    still = [row for row in rows if row[4] == 0]
    out = []
    if moved:
        out.append(
            "| Task | Metric | %s `ours` k/n | %s `ours` k/n | Change | Gate |"
            % (before_label, after_label)
        )
        out.append("| --- | --- | --- | --- | --- | --- |")
        for task, metric, before, after, change in moved:
            out.append(
                "| %s | %s | %d/%d | %d/%d | %+d | %s |"
                % (task, metric_label(metric), before["k"], before["n"], after["k"], after["n"],
                   change, round2_gate_text(change))
            )
        out.append("")
        out.append(
            textwrap.fill(
                "%s of the %s gated advantage metrics moved and %s did not; the whole table, "
                "every metric named and printed, is in the [%s Results section](%s) of the "
                "pre-registration."
                % (
                    NUMBER_WORDS.get(len(moved), str(len(moved))).capitalize(),
                    NUMBER_WORDS.get(len(rows), str(len(rows))),
                    NUMBER_WORDS.get(len(still), str(len(still))),
                    cells_phrase,
                    results_url,
                ),
                width=95,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    else:
        out.append(
            textwrap.fill(
                "No gated advantage metric moved: all %s read the same k/n as the %s cells "
                "they are measured against. The whole table is in the [%s Results section](%s) "
                "of the pre-registration."
                % (
                    NUMBER_WORDS.get(len(rows), str(len(rows))),
                    before_label,
                    cells_phrase,
                    results_url,
                ),
                width=95,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )

    dropped = [row for row in rows if row[4] < 0]
    single = [row for row in rows if row[4] <= -3]
    pair = [row for row in rows if row[4] <= -2]
    harms = [
        (task, metric, round2_metric(after_data, task, metric))
        for task, metric in disadvantage
    ]
    raised_harms = [entry for entry in harms if entry[2]["k"] >= 2]
    highest = max(cell["k"] for _t, _m, cell in harms)
    costs = round_cost(before_data, after_data, factor)
    over_cost = [entry for entry in costs if entry[2] > entry[4]]

    clause_a = not single and len(pair) < 2
    clause_b = not raised_harms
    clause_c = not over_cost

    sentences = []
    if clause_a and not dropped:
        sentences.append("Clause (a) holds: no gated advantage metric dropped.")
    elif clause_a:
        sentences.append(
            "Clause (a) holds: %s of the %s gated advantage metrics dropped, none by 3 and no "
            "two by 2."
            % (
                NUMBER_WORDS.get(len(dropped), str(len(dropped))),
                NUMBER_WORDS.get(len(rows), str(len(rows))),
            )
        )
    else:
        sentences.append(
            "Clause (a) fails: %s."
            % ", ".join(
                "%s %s is %d/%d against %d/%d"
                % (task, metric_label(metric), after["k"], after["n"], before["k"], before["n"])
                for task, metric, before, after, _change in (single or pair)
            )
        )
    if clause_b:
        sentences.append(
            "Clause (b) holds: the %s disadvantage booleans are %s%d/%d in the %s cells "
            "that measure them."
            % (
                NUMBER_WORDS.get(len(harms), str(len(harms))),
                "" if highest == 0 else "at most ",
                highest,
                max(cell["n"] for _t, _m, cell in harms),
                cells_phrase,
            )
        )
    else:
        sentences.append(
            "Clause (b) fails: %s."
            % ", ".join(
                "%s %s is %d/%d" % (task, metric_label(metric), cell["k"], cell["n"])
                for task, metric, cell in raised_harms
            )
        )
    ratios = ["%.2f\u00d7 on %s" % (ratio, task) for task, _b, _a, ratio, _l in costs]
    sentences.append(
        "Clause (c) %s: the median cost is %s and %s."
        % ("holds" if clause_c else "fails", ", ".join(ratios[:-1]), ratios[-1])
    )
    sentences.append(adopted if clause_a and clause_b and clause_c else failed)
    out.append("")
    out.append(
        textwrap.fill(
            " ".join(sentences),
            width=95,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )
    return "\n".join(out)


def render_round2_md(exp, round2):
    """The round-2 block: v1.2.0 measured against the main run's v1.0.0 `ours` cells."""
    return render_round_md(
        exp, round2, ROUND2_GATED, ROUND2_DISADVANTAGE, ROUND2_COST_FACTOR,
        "1.0.0", ROUND2_VERSION, "round-2",
        "All three clauses hold, so the round-2 text is adopted under the rule as it was "
        "written before the runs, and the file this project offers is the file round 2 measured.",
        "The round fails, so the pre-registered v1.2.1 revert set is the next step and the "
        "file this project offers is the file that failed.",
        ROUND2_RESULTS_URL,
    )


def render_round3_md(round2, round3):
    """The round-3 block: v1.3.0 measured against the round-2 v1.2.0 `ours` cells. The closing
    sentence says what the rule returns on this data and nothing about which text is shipped,
    which is prose a later commit owns."""
    return render_round_md(
        round2, round3, ROUND3_GATED, ROUND3_DISADVANTAGE, ROUND3_COST_FACTOR,
        ROUND2_VERSION, ROUND3_VERSION, "round-3",
        "All three clauses hold, so the delivery revision is adopted under the rule as it was "
        "written before the runs.",
        "The round fails, so the delivery revision is not adopted under the rule as it was "
        "written before the runs, and the revert set that rule pre-registered is what applies.",
        ROUND3_RESULTS_URL,
    )


def render_round4_md(round2, round4):
    """The round-4 block: the shipped v1.2.0 text re-run on 2026-09-05 against the same round-2
    v1.2.0 cells round 3 was measured against. Both columns carry one version name, so the labels
    say which collection each is. The closing sentence states what the arithmetic is for: round 4
    measured the text this project already ships, so no branch of it adopts or reverts anything."""
    return render_round_md(
        round2, round4, ROUND4_GATED, ROUND4_DISADVANTAGE, ROUND4_COST_FACTOR,
        ROUND2_VERSION, ROUND4_VERSION, "round-4",
        "Every clause holds, so the same text reproduced the cells it was measured against in "
        "round 2. Round 4 is the control and adopts nothing: it ran the text already "
        "shipped.",
        "The clauses are reported for information and not as a gate. Round 4 ran the shipped "
        "text, so a clause that fails here measures the distance between two collections of the "
        "same file rather than anything about a version, and nothing is adopted or reverted on "
        "it.",
        ROUND4_RESULTS_URL,
        before_label="v%s, round 2" % ROUND2_VERSION,
        after_label="v%s, round 4" % ROUND4_VERSION,
    )


NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 10: "ten", 12: "twelve",
                13: "thirteen", 14: "fourteen", 16: "sixteen"}


def render_experiment_summary_md(exp):
    """The README paragraph about the experiment, every number read from the summary. Each
    sentence states something the data has to support, so a claim the data contradicts raises
    here instead of being printed."""
    by_task = exp["by_task"]
    cells = [cell for entry in by_task.values() for cell in entry["cells"].values()]
    total = sum(cell["n"] for cell in cells)
    delivered = sum(cell["delivered_runs"] for cell in cells)
    if delivered != total:
        raise RuntimeError("%d of the %d runs delivered; the sentence says all of them" % (delivered, total))
    per_cell = {cell["n"] for cell in cells}
    if len(per_cell) != 1:
        raise RuntimeError("the cells are not the same size: %s" % sorted(per_cell))

    def cell(task, metric, condition):
        return by_task[task]["comparison"][metric]["conditions"][condition]

    identical = [
        metric
        for metric, stats in by_task["task3"]["comparison"].items()
        if len({c["k"] for c in stats["conditions"].values()}) != 1
    ]
    if identical:
        raise RuntimeError("task3 metrics differ across conditions: %s" % sorted(identical))

    written = cell("task1", "tests_written", "ours")
    reported = cell("task1", "report_has_commands_and_results", "ours")
    convention = cell("task2", "convention_followed", "ours")
    acceptance = cell("task2", "acceptance_all_pass", "ours")
    ratios = [by_task[task]["headline"]["ours"]["cost_ratio"] for task in ("task1", "task2", "task3")]
    text = (
        "%d runs: %s tasks, each run %s ways, %s runs each way, all of them delivered. On the "
        "task that builds a small app in an empty directory, the recommended file took "
        "`tests_written` from %d/%d with no instruction file to %d/%d, and reporting the command "
        "and its result from %d/%d to %d/%d; on the task that changes an existing package it "
        "took the documented-convention measure from %d/%d to %d/%d, and acceptance followed it "
        "exactly, %d/%d to %d/%d. On the one-line typo fix nothing moved at all: every yes-or-no "
        "measure is identical across the three ways of running it. The file is paid for on every "
        "task: median cost %.2f\u00d7 the runs with no instruction file when building in an empty "
        "directory, %.2f\u00d7 when changing an existing package and %.2f\u00d7 on the typo fix."
        % (
            total,
            NUMBER_WORDS[len(by_task)],
            NUMBER_WORDS[len(CONDITIONS)],
            NUMBER_WORDS[per_cell.pop()],
            cell("task1", "tests_written", "none")["k"], written["n"], written["k"], written["n"],
            cell("task1", "report_has_commands_and_results", "none")["k"], reported["n"],
            reported["k"], reported["n"],
            cell("task2", "convention_followed", "none")["k"], convention["n"],
            convention["k"], convention["n"],
            cell("task2", "acceptance_all_pass", "none")["k"], acceptance["n"],
            acceptance["k"], acceptance["n"],
            *ratios,
        )
    )
    return textwrap.fill(text, width=95)


def render_criteria_md(criteria):
    """One criterion per row for the methodology page: the question the engine asks, the reason
    it asks it and the sources the reason rests on. The worked example of each criterion is in
    `docs/criteria.json` and in the front page's tooltip at the point of use, so the table does
    not carry a fifth column of it."""
    out = [
        "| # | Criterion | Question | Why | Sources |",
        "|---|---|---|---|---|",
    ]
    for index, criterion in enumerate(criteria["criteria"], start=1):
        sources = ", ".join(
            "[%s](references.md#ref-%s)" % (key, key) for key in criterion["sources"]
        )
        out.append(
            "| %d | **%s** (`%s`) | %s | %s | %s |"
            % (
                index,
                criterion["name"],
                criterion["id"],
                criterion["question"].replace("|", "\\|"),
                criterion["why"].replace("|", "\\|"),
                sources,
            )
        )
    return "\n".join(out)


def version_coverage(digest, criteria, content):
    """The rule and content pair for one recorded text, read from RECORDED_TEXTS by hash so the
    genealogy cannot state a coverage number the hash table does not."""
    for _label, recorded, met, met_content in RECORDED_TEXTS:
        if recorded == digest:
            return met, len(criteria["criteria"]), met_content, len(content["criteria"])
    raise RuntimeError("%s is not one of the recorded texts" % digest)


def render_versions_md(criteria, content):
    """The genealogy of the recommended file: one row per version, with what changed, which round
    measured it and what the pre-registered rule did with it. Retired rows come from the constants
    above; the shipped row is measured on the root file at render time. The token estimate is
    bytes over four, floored, so it is derived from the row's own byte count and never recorded
    separately."""
    rows = [
        "| Version | Date | Lines | Bytes | Token estimate (bytes/4) | Rule criteria | "
        "Content criteria | What changed | Measured by | Outcome |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    root = OURS_FILE.read_text(encoding="utf-8")
    for label, date, lines, size, digest, changed, measured, outcome in VERSIONS:
        if digest is None:
            lines = count_lines(root)
            size = len(root.encode("utf-8"))
            met = coverage(evaluate(root, OURS_FILE.name, criteria))
            met_content = coverage(evaluate(root, OURS_FILE.name, content))
            of_rules = len(criteria["criteria"])
            of_content = len(content["criteria"])
        else:
            met, of_rules, met_content, of_content = version_coverage(digest, criteria, content)
        rows.append(
            "| %s | %s | %d | %s | %s | %d/%d | %d/%d | %s | %s | %s |"
            % (label, date, lines, "{:,}".format(size), "{:,}".format(size // 4), met, of_rules,
               met_content, of_content, changed, measured, outcome)
        )
    return "\n".join(rows)


def render_shipped_md(criteria, content):
    """Every text this project has offered, by hash and by coverage on both sets. The recorded
    rows name texts that are no longer in the working tree, so their numbers are constants
    measured at the time; the last row is the file shipped now, evaluated at render time."""
    root = OURS_FILE.read_text(encoding="utf-8")
    rows = [
        "| Text | sha256 | Rule criteria | Content criteria |",
        "| --- | --- | --- | --- |",
    ]
    for label, digest, met, met_content in RECORDED_TEXTS:
        rows.append(
            "| %s, recorded constant | `%s` | %d/%d | %d/%d |"
            % (label, digest, met, len(criteria["criteria"]), met_content,
               len(content["criteria"]))
        )
    rows.append(
        "| Root `AGENTS.md`, the file shipped now (v%s) | `%s` | %d/%d | %d/%d |"
        % (
            OURS_VERSION,
            hashlib.sha256(root.encode("utf-8")).hexdigest(),
            coverage(evaluate(root, OURS_FILE.name, criteria)),
            len(criteria["criteria"]),
            coverage(evaluate(root, OURS_FILE.name, content)),
            len(content["criteria"]),
        )
    )
    return "\n".join(rows)


def render_content_observation_md(data, content):
    """One paragraph about the content table, with every number counted from the data."""
    total = len(data["files"])
    counts = {
        c["id"]: sum(1 for r in data["files"] if r["criteria_content"][c["id"]]["pass"])
        for c in content["criteria"]
    }
    name = {c["id"]: c["name"] for c in content["criteria"]}
    top = max(counts, key=lambda i: counts[i])
    none_met = [i for i in counts if counts[i] == 0]
    best = max(r["met_content"] for r in data["files"])
    worst = min(r["met_content"] for r in data["files"])
    at_best = [r["repo"] for r in data["files"] if r["met_content"] == best]
    of_content = len(content["criteria"])
    parts = [
        "Coverage on the content set is lower and flatter than on the rule set. The criterion "
        "the corpus meets most often is %s (%d of %d files); the highest coverage any file "
        "reaches is %d of %d (%s) and the lowest is %d of %d."
        % (name[top], counts[top], total, best, of_content, ", ".join(at_best), worst, of_content)
    ]
    if none_met:
        parts.append(
            "No file in the corpus meets %s."
            % ", ".join(name[i] for i in none_met)
        )
    parts.append(
        "The columns, in the order of the criteria file, and the files that meet each, out of "
        "%d: %s."
        % (
            total,
            "; ".join(
                "%d %s %d" % (index, name[i], counts[i])
                for index, i in enumerate(counts, start=1)
            ),
        )
    )
    return " ".join(parts)


def render_stuffed_md(data):
    """The example file's own coverage line, so the number in the methodology text cannot drift
    away from the file in docs/examples/."""
    entry = data["stuffed"]
    return (
        "`%s` \u2014 %d lines, sha256 `%s`. Rule criteria %d/%d, content criteria %d/%d."
        % (
            entry["path"],
            entry["lines"],
            entry["sha256"],
            entry["met"],
            entry["of"],
            entry["met_content"],
            entry["of_content"],
        )
    )


def render_hernanz_md(criteria, content):
    """One sentence about the file five rules of this project's first draft came from, with the
    criteria it meets and the ones it does not named from the criteria file."""
    names = {c["id"]: c["name"] for c in criteria["criteria"]}
    order = [c["id"] for c in criteria["criteria"]]
    met = [names[i] for i in HERNANZ_MET_IDS]
    unmet_middle = [names[i] for i in order[3:6]]
    return (
        "Evaluated with the same engine, the file in the post meets %d of the %d rule criteria "
        "(%s) and %d of the %d content criteria; among the three criteria no surveyed file meets "
        "— %s — it meets none either. The post's text is not stored in this repository, so these "
        "verdicts are recorded rather than regenerated: anyone with the image and the engine can "
        "reproduce them by pasting the transcription into the check on the front page."
        % (
            len(HERNANZ_MET_IDS),
            len(criteria["criteria"]),
            ", ".join(met),
            HERNANZ_MET_CONTENT,
            len(content["criteria"]),
            ", ".join(unmet_middle),
        )
    )


def render_excluded_md(data):
    out = ["| File | Lines | Measured | Reason |", "| --- | --- | --- | --- |"]
    for record in data["excluded"]:
        out.append(
            "| [%s/%s](%s) | %d | %s | %s |"
            % (record["repo"], record["path"], record["url_latest"], record["lines"], record["lines_at"], record["reason"])
        )
    return "\n".join(out)


def render_summary_md(data, criteria):
    """The compact table the README carries: no criteria columns, coverage only."""
    out = ["| File | Type | Stars | Lines | License | Criteria met |", "| --- | --- | --- | --- | --- | --- |"]
    for record in data["files"]:
        out.append(
            "| [%s](%s) | %s | %s | %d | %s | %d/%d |"
            % (
                record["repo"],
                record["url_view"],
                record["type"],
                "{:,}".format(record["stars"]),
                record["lines"],
                record["license"],
                record["met"],
                record["of"],
            )
        )
    return "\n".join(out)


def rendered_outputs():
    """{path: expected text} for every file the renderer owns."""
    data = read_json(COMPARISON_JSON)
    criteria = load_criteria()
    content = load_criteria_content()
    if data["criteria_version"] != criteria["version"]:
        raise RuntimeError(
            "comparison.json was generated with criteria version %s but docs/criteria.json is %s; "
            "run --refresh" % (data["criteria_version"], criteria["version"])
        )
    if data["criteria_content_version"] != content["version"]:
        raise RuntimeError(
            "comparison.json was generated with content criteria version %s but the "
            "`content` set in docs/criteria.json is %s; run --refresh"
            % (data["criteria_content_version"], content["version"])
        )
    content_ids = {c["id"] for c in content["criteria"]}
    for record in data["files"]:
        if set(record.get("criteria_content", {})) != content_ids:
            raise RuntimeError(
                "%s in comparison.json does not carry the content criteria in "
                "docs/criteria.json; run --refresh" % record["key"]
            )
    data = with_ours(data, criteria, content)
    exp = load_experiment() if FINDINGS_MD.exists() or INDEX_HTML.exists() else None
    round2 = load_round2() if FINDINGS_MD.exists() else None
    rounds = FINDINGS_MD.exists() or INDEX_HTML.exists()
    round3 = load_round3() if rounds else None
    round4 = load_round4() if rounds else None
    outputs = {
        COMPARISON_JSON: comparison_json_text(data, criteria, content),
        COMPARISON_MD: render_markdown(data, criteria, content),
    }
    if INDEX_HTML.exists():
        page = INDEX_HTML.read_text(encoding="utf-8")
        page = replace_block(page, "comparison", render_comparison_html(data, criteria), INDEX_HTML)
        page = replace_block(page, "labels", render_labels_css(criteria), INDEX_HTML)
        page = replace_block(page, "preview", render_preview_html(data, criteria), INDEX_HTML)
        page = replace_block(page, "file", render_file_html(), INDEX_HTML)
        page = replace_block(
            page, "claims", render_claims_html(data, criteria, exp, round3, round4), INDEX_HTML
        )
        page = replace_block(page, "dates", render_dates_html(data), INDEX_HTML)
        outputs[INDEX_HTML] = page
    if METHODOLOGY_MD.exists():
        page = METHODOLOGY_MD.read_text(encoding="utf-8")
        page = replace_block(page, "corpus", render_table(data, criteria), METHODOLOGY_MD)
        page = replace_block(page, "criteria", render_criteria_md(criteria), METHODOLOGY_MD)
        page = replace_block(page, "criteria-content", render_criteria_md(content), METHODOLOGY_MD)
        page = replace_block(
            page,
            "corpus-content",
            render_table(data, content, "criteria_content", "met_content", "of_content"),
            METHODOLOGY_MD,
        )
        page = replace_block(page, "excluded", render_excluded_md(data), METHODOLOGY_MD)
        page = replace_block(
            page, "versions", render_versions_md(criteria, content), METHODOLOGY_MD
        )
        page = replace_block(page, "shipped", render_shipped_md(criteria, content), METHODOLOGY_MD)
        page = replace_block(page, "stuffed", render_stuffed_md(data), METHODOLOGY_MD)
        outputs[METHODOLOGY_MD] = page
    if FINDINGS_MD.exists():
        page = FINDINGS_MD.read_text(encoding="utf-8")
        page = replace_block(page, "hernanz", render_hernanz_md(criteria, content), FINDINGS_MD)
        page = replace_block(
            page, "content", render_table(data, content, "criteria_content", "met_content", "of_content"), FINDINGS_MD
        )
        page = replace_block(
            page, "content-note", render_content_observation_md(data, content), FINDINGS_MD
        )
        page = replace_block(page, "headline", render_experiment_headline_md(exp), FINDINGS_MD)
        page = replace_block(page, "metrics", render_experiment_metrics_md(exp), FINDINGS_MD)
        page = replace_block(page, "cost", render_experiment_cost_md(exp), FINDINGS_MD)
        page = replace_block(page, "round2", render_round2_md(exp, round2), FINDINGS_MD)
        page = replace_block(page, "round3", render_round3_md(round2, round3), FINDINGS_MD)
        page = replace_block(page, "round4", render_round4_md(round2, round4), FINDINGS_MD)
        outputs[FINDINGS_MD] = page
    if README_MD.exists():
        page = README_MD.read_text(encoding="utf-8")
        page = replace_block(page, "summary", render_summary_md(data, criteria), README_MD)
        page = replace_block(
            page, "summary-experiment", render_experiment_summary_md(exp), README_MD
        )
        outputs[README_MD] = page
    return outputs


def cmd_render():
    for path, text in rendered_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, text)
        print("wrote %s" % path)
    return 0


def cmd_check():
    criteria = load_criteria()
    content = load_criteria_content()
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
        if record["met_content"] != coverage(record["criteria_content"]):
            differences.append("%s: met_content does not match the content verdicts" % record["key"])
        if record["of_content"] != len(content["criteria"]):
            differences.append("%s: of_content is not the size of the content set" % record["key"])
    for message in differences:
        print("check: " + message, file=sys.stderr)
    if differences:
        return 1
    print(
        "check: %d files, %d rule criteria and %d content criteria, rendered output matches the data"
        % (len(data["files"]), len(criteria["criteria"]), len(content["criteria"]))
    )
    return 0


# --------------------------------------------------------------------------- one file


def cmd_file(path):
    criteria = load_criteria()
    text = Path(path).read_text(encoding="utf-8")
    verdicts = evaluate(text, Path(path).name, criteria)
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
    args = parser.parse_args(argv)

    chosen = [flag for flag in (args.refresh, args.check, bool(args.file)) if flag]
    if len(chosen) > 1:
        parser.error("--refresh, --check and --file are separate modes")
    if args.refresh:
        return cmd_refresh(Path(args.out) if args.out else COMPARISON_JSON)
    if args.check:
        return cmd_check()
    if args.file:
        return cmd_file(args.file)
    return cmd_render()


if __name__ == "__main__":
    sys.exit(main())
