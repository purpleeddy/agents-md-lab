#!/usr/bin/env python3
"""Compare public AGENTS.md and CLAUDE.md files against two criteria sets.

The rule criteria in docs/criteria.json ask how a file is written; the content criteria in
docs/criteria-content.json ask what it tells an agent about the project. Both sets run on the
same engine over the same text, and each corpus file carries one coverage number per set.

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
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "corpus.toml"
CRITERIA = REPO_ROOT / "docs" / "criteria.json"
CRITERIA_CONTENT = REPO_ROOT / "docs" / "criteria-content.json"
COMPARISON_JSON = REPO_ROOT / "docs" / "data" / "comparison.json"
COMPARISON_MD = REPO_ROOT / "docs" / "generated" / "comparison.md"
GENERIC_MD = REPO_ROOT / "docs" / "generated" / "agents-generic.md"
INDEX_HTML = REPO_ROOT / "docs" / "index.html"
METHODOLOGY_MD = REPO_ROOT / "docs" / "methodology.md"
FINDINGS_MD = REPO_ROOT / "docs" / "findings.md"
EXPERIMENT_JSON = REPO_ROOT / "docs" / "data" / "experiment.json"
README_MD = REPO_ROOT / "README.md"
OURS_FILE = REPO_ROOT / "AGENTS.md"
STUFFED_FILE = REPO_ROOT / "docs" / "examples" / "stuffed.md"
CACHE_DIR = REPO_ROOT / "data" / "cache" / "corpus"

USER_AGENT = "agent-md-lab compare.py"
RAW_URL = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
VIEW_URL = "https://github.com/{repo}/blob/{ref}/{path}"
API_REPO_URL = "https://api.github.com/repos/{repo}"
PREVIEW_LINES = 12
# The file the page offers. It is not named AGENTS.md inside this repository: a second file by
# that name is a second instruction file, which every agent working here would load.
OURS_DOWNLOAD_URL = (
    "https://raw.githubusercontent.com/purpleeddy/agents-md-lab/main/docs/generated/"
    "agents-generic.md"
)
# The one line that differs between the text the experiment ran and the file offered here: an
# adopter's repository has no docs/rationale.md, so the pointer becomes the published page.
GENERIC_POINTER_FROM = "docs/rationale.md"
GENERIC_POINTER_TO = "https://purpleeddy.github.io/agents-md-lab/rationale"

# The version of the recommended file itself. v1.0 is the text the experiment ran; v1.0.1 fixes
# two defects across four rule lines after the independent review (see docs/methodology.md, "What
# the experiment tested and what is shipped"). The sha256 below is the generic text the
# experiment wrote, which is not recoverable from the working tree once the rules change, so it
# is recorded here with the two coverage numbers measured on it before the amendment.
OURS_VERSION = "1.0.1"
TESTED_GENERIC_SHA256 = "b8be420f0597e483469dbfb47dec94487103758016f2b03964d4c888f68fd832"
TESTED_GENERIC_MET = 9
TESTED_GENERIC_MET_CONTENT = 0

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


def load_criteria_content():
    """The second criteria set. It asks what a file contains rather than how it is written, and
    it runs on the same engine over the same text; the two sets are never merged."""
    with CRITERIA_CONTENT.open("rb") as handle:
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
        "A second, independent set of %d criteria, version %s, in "
        "`docs/criteria-content.json`. It asks what a file tells an agent about the project, "
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
    block = marker(name) + "\n" + body + "\n" + marker(name, True)
    return text[:start] + block + text[end + len(marker(name, True)):]


def esc(text):
    return html.escape(text, quote=True)


def generic_text():
    """The root file with its repository-specific Project section replaced by the empty template:
    the text the experiment wrote and the text this project offers for download. The transform
    lives in scripts/experiment.py, which wrote it for the runs, and is imported rather than
    repeated here."""
    import experiment  # local: the experiment module is only needed by the render step

    return experiment.generic_agents_md(OURS_FILE.read_text(encoding="utf-8"))


def download_text():
    """The generic text with its one repository-relative pointer replaced by the published page.
    That is the only difference from the text the experiment ran, and it costs the file the
    `pointer_not_copy` criterion, which recognises a path and not a URL: the number is published
    rather than worked around."""
    generic = generic_text()
    if generic.count(GENERIC_POINTER_FROM) != 1:
        raise RuntimeError(
            "the root file names %s %d times; the download file replaces exactly one pointer"
            % (GENERIC_POINTER_FROM, generic.count(GENERIC_POINTER_FROM))
        )
    return generic.replace(GENERIC_POINTER_FROM, GENERIC_POINTER_TO)


def ours_record(criteria, content):
    """This repository's own AGENTS.md, evaluated by the same engine. It is not a corpus entry.

    Two texts are recorded, because two different texts matter. `criteria` and `sha256` are the
    root file as it sits in this repository, which is what the compare table's own row shows.
    The content verdicts are computed from the generic text — the root file with its Project
    section replaced by the empty template, which is what the experiment ran and what the page
    offers for download — because the content criteria ask for exactly the things that section
    holds, and reporting them from a filled-in Project section would describe a file nobody
    downloads. Which text produced them is recorded in the entry."""
    body = OURS_FILE.read_bytes()
    text = body.decode("utf-8")
    verdicts = evaluate(text, OURS_FILE.name, criteria)
    generic = generic_text()
    generic_bytes = generic.encode("utf-8")
    generic_verdicts = evaluate(generic, OURS_FILE.name, criteria)
    content_verdicts = evaluate(generic, OURS_FILE.name, content)
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
        "content_text": "generic",
        "content_sha256": hashlib.sha256(generic_bytes).hexdigest(),
        "criteria_content": content_verdicts,
        "met_content": coverage(content_verdicts),
        "of_content": len(content["criteria"]),
        "generic": {
            "sha256": hashlib.sha256(generic_bytes).hexdigest(),
            "lines": count_lines(generic),
            "bytes": len(generic_bytes),
            "met": coverage(generic_verdicts),
            "of": len(criteria["criteria"]),
        },
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
    return '<td class="v %s">%s</td>' % (state, word)


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
        "<caption>Coverage of ten sourced criteria by ten published instruction files, "
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


def render_preview_html(data, criteria, content):
    """The hero card. The numbers are the offered file's, on both criteria sets, because that
    file is what the button downloads; the root file above it differs in the Project section and
    in one pointer line, and all three hashes are on the card so the texts can be told apart."""
    offered = download_text()
    lines = offered.split("\n")[:PREVIEW_LINES]
    ours = data["ours"]
    generic = ours["generic"]
    return (
        '<pre class="preview" aria-label="The first %d lines of AGENTS.md">%s</pre>\n'
        '<p class="filemeta" title="root sha256 %s, generic sha256 %s, offered file sha256 %s">'
        'MIT. v%s. %d lines. '
        "Rule criteria %d/%d \u00b7 Content criteria %d/%d (this file points at the rationale "
        "page by URL, which the pointer criterion does not count; the Project section you fill "
        "adds the commands).</p>"
        % (
            PREVIEW_LINES,
            esc("\n".join(lines)),
            esc(ours["sha256"]),
            esc(generic["sha256"]),
            esc(hashlib.sha256(offered.encode("utf-8")).hexdigest()),
            OURS_VERSION,
            generic["lines"],
            coverage(evaluate(offered, OURS_FILE.name, criteria)),
            len(criteria["criteria"]),
            coverage(evaluate(offered, OURS_FILE.name, content)),
            len(content["criteria"]),
        )
    )


def render_file_html():
    """The file the buttons hand over, for the copy button: the same text the download link
    serves, so copying and downloading cannot differ. A <template> is inert: the browser does
    not render it and no script is needed to keep it out of the page."""
    return '<template id="agents-md-text">%s</template>' % esc(download_text())


def render_criteria_json(criteria):
    """What the in-browser check needs: the engine fields, the criterion name and the example
    it offers when a criterion is not met. The question, the reason and the sources are already
    on the page, in the column popovers, so they are not repeated here."""
    dropped = ("question", "why", "sources", "notes")
    slim = {
        "version": criteria["version"],
        "criteria": [
            {k: v for k, v in criterion.items() if k not in dropped}
            for criterion in criteria["criteria"]
        ],
    }
    body = json.dumps(slim, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/json" id="criteria-data">%s</script>' % body


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


def claims(data, criteria, exp):
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
            "Among the %d surveyed files, %d ask for the smallest change, and %d carry a "
            "sibling CLAUDE.md that names AGENTS.md."
            % (total, met_count(data, "scope_restraint"), siblings),
            SIBLING_QUERY,
        ),
    ]
    items.append((
        "The generic file this project offers meets %d of the %d content criteria: what they "
        "ask for lives in the Project section that each repository fills in for itself."
        % (data["ours"]["met_content"], data["ours"]["of_content"]),
        OURS_QUERY,
    ))
    if exp is None:
        return items
    reported = experiment_cell(exp, "task2", "report_has_commands_and_results", "ours")
    baseline = experiment_cell(exp, "task2", "report_has_commands_and_results", "none")
    typo = sum(1 for run in exp["runs"] if run["task"] == "task3")
    items.append((
        "In the 90-run experiment, the brownfield task reported the command and its result in "
        "%d of %d runs under the recommended file and %d of %d with no file."
        % (reported["k"], reported["n"], baseline["k"], baseline["n"]),
        EXPERIMENT_QUERY
        % "d['by_task']['task2']['comparison']['report_has_commands_and_results']"
          "['conditions']['ours']['k']",
    ))
    items.append((
        "In the 90-run experiment, 0 of the %d typo-fix runs wrote a test or ran the suite "
        "twice, in any of the three conditions." % typo,
        EXPERIMENT_QUERY
        % "sum(r['metrics']['overprocess'] for r in d['runs'] if r['task'] == 'task3')",
    ))
    return items


def render_claims_html(data, criteria, exp):
    out = ['<ul class="claims">']
    for text, command in claims(data, criteria, exp):
        out.append("<li>%s<p class=\"verify\">Verify: <code>%s</code></p></li>" % (esc(text), esc(command)))
    out.append("</ul>")
    return "\n".join(out)


def render_claims_md(data, criteria, exp):
    out = []
    for text, command in claims(data, criteria, exp):
        out.append("- %s" % text)
        out.append("")
        out.append("  Verify: `%s`" % command)
        out.append("")
    return "\n".join(out).rstrip()


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


def render_criteria_md(criteria):
    """The ten criteria as a definition list for the methodology page."""
    out = []
    for index, criterion in enumerate(criteria["criteria"], start=1):
        sources = ", ".join(
            "[%s](references.md#ref-%s)" % (key, key) for key in criterion["sources"]
        )
        out.append("%d. **%s** (`%s`)" % (index, criterion["name"], criterion["id"]))
        out.append("   - Question: %s" % criterion["question"])
        out.append("   - Why: %s" % criterion["why"])
        out.append("   - Sources: %s" % sources)
        out.append("   - One way to meet it: %s" % criterion["example"])
    return "\n".join(out)


def render_shipped_md(criteria, content):
    """The three texts that matter to a reader: the one the experiment ran, the file in this
    repository now, and the generic file the page offers. Coverage on both criteria sets, from
    the same engine. The first row is a recorded constant, because the text it names no longer
    exists in the working tree; the other two are evaluated at render time."""
    root = OURS_FILE.read_text(encoding="utf-8")
    generic = generic_text()
    rows = [
        "| Text | sha256 | Rule criteria | Content criteria |",
        "| --- | --- | --- | --- |",
        "| Generic file the experiment ran (v1.0), recorded constant | `%s` | %d/%d | %d/%d |"
        % (
            TESTED_GENERIC_SHA256,
            TESTED_GENERIC_MET,
            len(criteria["criteria"]),
            TESTED_GENERIC_MET_CONTENT,
            len(content["criteria"]),
        ),
    ]
    for label, text in (
        ("Root `AGENTS.md` in this repository (v%s)" % OURS_VERSION, root),
        ("Generic text, this repository's Project section emptied (v%s)" % OURS_VERSION, generic),
        (
            "`docs/generated/agents-generic.md`, the file the button offers (v%s)" % OURS_VERSION,
            download_text(),
        ),
    ):
        rows.append(
            "| %s | `%s` | %d/%d | %d/%d |"
            % (
                label,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                coverage(evaluate(text, OURS_FILE.name, criteria)),
                len(criteria["criteria"]),
                coverage(evaluate(text, OURS_FILE.name, content)),
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
    name = {c["id"]: c["name"].lower() for c in content["criteria"]}
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
    """One sentence about the file five of this project's rules came from, with the criteria it
    meets and the ones it does not named from the criteria file."""
    names = {c["id"]: c["name"].lower() for c in criteria["criteria"]}
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
            "comparison.json was generated with content criteria version %s but "
            "docs/criteria-content.json is %s; run --refresh"
            % (data["criteria_content_version"], content["version"])
        )
    content_ids = {c["id"] for c in content["criteria"]}
    for record in data["files"]:
        if set(record.get("criteria_content", {})) != content_ids:
            raise RuntimeError(
                "%s in comparison.json does not carry the content criteria in "
                "docs/criteria-content.json; run --refresh" % record["key"]
            )
    data = with_ours(data, criteria, content)
    exp = load_experiment() if FINDINGS_MD.exists() or INDEX_HTML.exists() else None
    outputs = {
        COMPARISON_JSON: comparison_json_text(data, criteria, content),
        COMPARISON_MD: render_markdown(data, criteria, content),
        GENERIC_MD: download_text(),
    }
    if INDEX_HTML.exists():
        page = INDEX_HTML.read_text(encoding="utf-8")
        page = replace_block(page, "comparison", render_comparison_html(data, criteria), INDEX_HTML)
        page = replace_block(page, "labels", render_labels_css(criteria), INDEX_HTML)
        page = replace_block(page, "preview", render_preview_html(data, criteria, content), INDEX_HTML)
        page = replace_block(page, "file", render_file_html(), INDEX_HTML)
        page = replace_block(page, "criteria", render_criteria_json(criteria), INDEX_HTML)
        page = replace_block(page, "claims", render_claims_html(data, criteria, exp), INDEX_HTML)
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
        page = replace_block(page, "shipped", render_shipped_md(criteria, content), METHODOLOGY_MD)
        page = replace_block(page, "stuffed", render_stuffed_md(data), METHODOLOGY_MD)
        outputs[METHODOLOGY_MD] = page
    if FINDINGS_MD.exists():
        page = FINDINGS_MD.read_text(encoding="utf-8")
        page = replace_block(page, "excluded", render_excluded_md(data), FINDINGS_MD)
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
        page = replace_block(page, "claims", render_claims_md(data, criteria, exp), FINDINGS_MD)
        outputs[FINDINGS_MD] = page
    if README_MD.exists():
        page = README_MD.read_text(encoding="utf-8")
        page = replace_block(page, "summary", render_summary_md(data, criteria), README_MD)
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
