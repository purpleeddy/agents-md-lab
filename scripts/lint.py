#!/usr/bin/env python3
"""Deterministic, source-cited checks for AGENTS.md / CLAUDE.md context files.

Usage:
  python3 scripts/lint.py FILE [FILE ...] [--type project|generic] [--format text|json|csv]
  python3 scripts/lint.py --corpus      lint every manifest entry + the author's file -> results/v1/checks.csv
  python3 scripts/lint.py --self-test   registry integrity: every source key and catalog row exists

Every check is a pure function of the file text. No network, no clock, no randomness.
The contract for adding a check is in docs/design.md section 5.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import statistics
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.toml"
LOCK = ROOT / "data" / "manifest.lock.json"
CACHE = ROOT / "data" / "cache"
RESULTS = ROOT / "results" / "v1"
CHECKS_CSV = RESULTS / "checks.csv"
RUN_JSON = RESULTS / "run.json"
REFERENCES = ROOT / "docs" / "references.md"
CATALOG = ROOT / "docs" / "checks.md"

CSV_COLUMNS = ("file", "check_id", "applicable", "pass", "value", "line")


# --------------------------------------------------------------------------- model

@dataclass(frozen=True)
class FileContext:
    key: str
    filename: str
    file_type: str  # "project" | "generic"
    text: str
    lines: tuple[str, ...]
    sibling: dict | None  # {"path": str, "present": bool, "text": str | None}


@dataclass(frozen=True)
class CheckResult:
    passed: bool | None
    value: float | None = None
    line: int | None = None
    note: str = ""


@dataclass(frozen=True)
class CheckSpec:
    id: str
    applies_to: str  # all | project | generic | agents-md | manifest
    source: tuple[str, ...]
    grade: str
    description: str
    measure: bool
    fn: Callable[[FileContext], CheckResult]


CHECKS: list[CheckSpec] = []


def check(id: str, applies_to: str, source: str, grade: str, description: str, measure: bool = False):
    def register(fn: Callable[[FileContext], CheckResult]):
        if any(c.id == id for c in CHECKS):
            raise ValueError(f"duplicate check id {id}")
        CHECKS.append(CheckSpec(id, applies_to, tuple(s.strip() for s in source.split(",")), grade, description, measure, fn))
        return fn
    return register


def applies(spec: CheckSpec, ctx: FileContext) -> bool:
    if spec.applies_to == "all":
        return True
    if spec.applies_to == "project":
        return ctx.file_type == "project"
    if spec.applies_to == "generic":
        return ctx.file_type == "generic"
    if spec.applies_to == "agents-md":
        return ctx.filename.upper() == "AGENTS.MD"
    if spec.applies_to == "manifest":
        return ctx.filename.upper() == "AGENTS.MD" and ctx.sibling is not None
    raise ValueError(f"unknown applies_to {spec.applies_to}")


# --------------------------------------------------------------------------- text helpers

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def iter_code(ctx: FileContext) -> Iterator[tuple[int, str]]:
    """Yield (line_no, code) for fenced-block lines and inline backtick spans."""
    in_fence = False
    for i, line in enumerate(ctx.lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            yield i, line
            continue
        for m in INLINE_CODE.finditer(line):
            yield i, m.group(1)


def iter_sentences(ctx: FileContext) -> Iterator[tuple[int, str]]:
    """Yield (line_no, sentence). A sentence is a bullet line or a period-terminated span within a line."""
    in_fence = False
    for i, line in enumerate(ctx.lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip():
            continue
        body = BULLET.sub("", line, count=1)
        if BULLET.match(line):
            yield i, body.strip()
            continue
        for part in SENTENCE_SPLIT.split(body):
            if part.strip():
                yield i, part.strip()


def iter_headings(ctx: FileContext) -> Iterator[tuple[int, int, str]]:
    in_fence = False
    for i, line in enumerate(ctx.lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            yield i, len(m.group(1)), m.group(2)


def first_sentence_match(ctx: FileContext, *patterns: re.Pattern) -> int | None:
    for line_no, sentence in iter_sentences(ctx):
        if all(p.search(sentence) for p in patterns):
            return line_no
    return None


def first_code_match(ctx: FileContext, *patterns: re.Pattern) -> int | None:
    for line_no, code in iter_code(ctx):
        if all(p.search(code) for p in patterns):
            return line_no
    return None


# --------------------------------------------------------------------------- patterns (docs/design.md 5.3)

RE_TEST = re.compile(
    r"\b(npm|pnpm|yarn|bun)\s+(run\s+)?test\b|\bpytest\b|\bpython3?\s+-m\s+(pytest|unittest)\b|\bgo\s+test\b"
    r"|\bcargo\s+test\b|\bmake\s+test\b|\bmix\s+test\b|\brake\s+test\b|\bbundle\s+exec\s+rspec\b|\brspec\b"
    r"|\bvitest\b|\bjest\b|\bdotnet\s+test\b|\b(gradle|gradlew|mvn)\s+test\b|\bzig\s+build\s+test\b|\bbin/rails\s+test\b",
    re.I,
)
RE_SINGLE = re.compile(
    r"\s-t\s|\s-k\s|--filter\b|--grep\b|::|\s-run\s|\s--\s+--test|\btest_name\b|<test|\s-t\s*['\"]"
    r"|(?:^|\s)\S*(?:tests?/|\.test\.|\.spec\.|/test_\w|_test\.\w)\S*",  # a path argument selecting one test file or directory
    re.I,
)
RE_LINT = re.compile(
    r"\b(eslint|ruff|flake8|pylint|mypy|pyright|tsc|clippy|golangci-lint|go\s+vet|credo|rubocop|prettier\s+--check|biome|typecheck|type-check|lint)\b",
    re.I,
)
RE_BUILD = re.compile(
    r"\b(npm|pnpm|yarn|bun)\s+run\s+build\b|\bcargo\s+build\b|\bgo\s+build\b|\bmake(\s+build)?\b|\bmix\s+compile\b"
    r"|\bzig\s+build\b|\btsc\s+-b\b|\bdotnet\s+build\b|\bgradle(w)?\s+build\b",
    re.I,
)
RE_PROHIBIT = re.compile(
    r"\b(never|do not|don't|must not|not allowed|forbidden|without (an )?explicit|ask (before|first)"
    r"|require[sd]? (approval|confirmation)|only with (approval|permission))\b"
    r"|\bno\b(?=[^.\n]{0,40}(rm\s+-rf|force|reset|drop|delet|destructive|history\s+rewrit|truncat))",  # "No history rewrite"
    re.I,
)
RE_DESTRUCTIVE = re.compile(
    r"rm\s+-rf|force[- ]push|--force\b|reset\s+--hard|drop\s+(table|database|column)|delete\s+(data|files|the database)"
    r"|destructive|irreversible|history\s+rewrit|\btruncate\b",
    re.I,
)
RE_SECRET = re.compile(r"\b(secret|credential|api key|token|password|private key|\.env)s?\b", re.I)
RE_SECRET_VERB = re.compile(r"\b(never|do not|don't|must not|redact|commit|print|paste|log|echo|expose)\b", re.I)
RE_INJECTION = re.compile(
    r"(prompt injection|hostile content|untrusted (input|content|text|instructions?))"
    r"|((instruction|prompt|command|text|directive)s?[^.\n]{0,60}\b(in|inside|found in|from|within|embedded in)\b[^.\n]{0,40}"
    r"\b(file|log|issue|comment|tool output|tool result|web page|document|output)s?\b[^.\n]{0,60}"
    r"\b(data|not (commands|instructions|orders)|untrusted|ignore|do not follow|are not|never follow)\b)"
    r"|(\b(treat|regard)\b[^.\n]{0,60}\bas (data|untrusted|input)\b)"
    r"|(\b(do not|don't|never)\s+(follow|obey|execute|act on)\b[^.\n]{0,40}\b(instruction|directive|command)s?\b)",
    re.I,
)
RE_DONE = re.compile(
    r"\b(done|complete|finish(ed|ing)|before (committing|merging|opening a pr|pushing|submitting|finishing|landing)|definition of done)\b",
    re.I,
)
RE_VERIFY = re.compile(r"\b(test|tests|lint|typecheck|type-check|build|ci|green|pass(es|ed|ing)?)\b", re.I)
RE_ETIQUETTE = re.compile(
    r"\b(commit messages?|commits? (should|must)|conventional commits|branch (names?|naming)|pull requests?"
    r"|PR (title|body|description)|open(ing)? a PR|squash|rebase)\b",
    re.I,
)
RE_OVERVIEW = re.compile(
    r"^(architecture|overview|project structure|directory structure|codebase structure|repository (layout|structure)"
    r"|file structure|codebase overview)\b",
    re.I,
)
RE_VAGUE = re.compile(
    r"\b(properly|appropriately|clean code|best practices|high[- ]quality|well[- ]written|nicely|as appropriate"
    r"|where appropriate|when appropriate|common sense|write good code)\b",
    re.I,
)
RE_EMPHASIS = re.compile(r"\b(NEVER|ALWAYS|MUST|IMPORTANT|CRITICAL|DO NOT)\b")
RE_POINTER = re.compile(
    r"(?<![\w])@[\w./-]+\.md"  # @path imports
    r"|\]\((?!https?://)[^)\s]+\.md\)"  # relative markdown links
    r"|`(?!https?://)[\w.-]+(?:/[\w.-]+)*/`"  # directory paths in code spans
    r"|\b[\w.-]+/[\w./-]*\.md\b"  # bare relative paths to .md files
)
RE_TOOL_PRIVATE = re.compile(r"\.claude/|\.cursor/|\.codex/|\.gemini/|\.windsurf/|copilot-instructions\.md")


# --------------------------------------------------------------------------- measurements

@check("measure-chars", "all", "anthropic-memory", "G", "Unicode characters", measure=True)
def measure_chars(ctx):
    return CheckResult(None, len(ctx.text))


@check("measure-bytes", "all", "openai-agents-md", "G", "UTF-8 bytes", measure=True)
def measure_bytes(ctx):
    return CheckResult(None, len(ctx.text.encode("utf-8")))


@check("measure-words", "all", "agent-readmes", "G", "Whitespace-separated words", measure=True)
def measure_words(ctx):
    return CheckResult(None, len(ctx.text.split()))


@check("measure-lines", "all", "anthropic-memory", "G", "Lines", measure=True)
def measure_lines(ctx):
    return CheckResult(None, len(ctx.lines))


@check("measure-tokens-approx", "all", "anthropic-bp", "G", "Approximate tokens (characters / 4)", measure=True)
def measure_tokens(ctx):
    return CheckResult(None, round(len(ctx.text) / 4))


@check("measure-h2", "all", "agent-readmes", "G", "Second-level headings", measure=True)
def measure_h2(ctx):
    return CheckResult(None, sum(1 for _, level, _ in iter_headings(ctx) if level == 2))


@check("measure-bullets", "all", "anthropic-memory", "G", "Bullet or numbered lines", measure=True)
def measure_bullets(ctx):
    return CheckResult(None, sum(1 for line in ctx.lines if BULLET.match(line)))


@check("measure-emphasis", "all", "anthropic-bp", "G", "Uppercase emphasis tokens (NEVER, ALWAYS, MUST, IMPORTANT, CRITICAL, DO NOT)", measure=True)
def measure_emphasis(ctx):
    return CheckResult(None, len(RE_EMPHASIS.findall(ctx.text)))


@check("measure-pointers", "all", "humanlayer", "G", "Pointers to other documents (imports, relative links, paths)", measure=True)
def measure_pointers(ctx):
    return CheckResult(None, len(RE_POINTER.findall(ctx.text)))


# --------------------------------------------------------------------------- checks

@check("len-lines", "all", "anthropic-memory, humanlayer", "G", "At most 200 lines")
def len_lines(ctx):
    n = len(ctx.lines)
    return CheckResult(n <= 200, n)


@check("len-bytes", "all", "openai-agents-md", "G", "At most 32 KiB (Codex default project_doc_max_bytes)")
def len_bytes(ctx):
    n = len(ctx.text.encode("utf-8"))
    return CheckResult(n <= 32768, n)


@check("cmd-test", "project", "agents-md-spec, anthropic-bp", "G", "A test command is given verbatim")
def cmd_test(ctx):
    line = first_code_match(ctx, RE_TEST)
    return CheckResult(line is not None, None, line)


@check("cmd-single", "project", "anthropic-bp", "G", "A way to run a single test is given")
def cmd_single(ctx):
    line = first_code_match(ctx, RE_TEST, RE_SINGLE)
    return CheckResult(line is not None, None, line)


@check("cmd-lint", "project", "anthropic-bp", "G", "A lint or typecheck command is given")
def cmd_lint(ctx):
    line = first_code_match(ctx, RE_LINT)
    return CheckResult(line is not None, None, line)


@check("cmd-build", "project", "agents-md-spec", "G", "A build command is given")
def cmd_build(ctx):
    line = first_code_match(ctx, RE_BUILD)
    return CheckResult(line is not None, None, line)


@check("rule-destructive", "all", "agent-readmes, ssojet", "G", "A guard against destructive or irreversible operations")
def rule_destructive(ctx):
    line = first_sentence_match(ctx, RE_PROHIBIT, RE_DESTRUCTIVE)
    return CheckResult(line is not None, None, line)


@check("rule-secrets", "all", "anthropic-bp", "G", "A rule about handling secrets")
def rule_secrets(ctx):
    line = first_sentence_match(ctx, RE_SECRET, RE_SECRET_VERB)
    return CheckResult(line is not None, None, line)


@check("rule-injection", "all", "anthropic-bp", "G", "Instructions found in files, logs, or tool output are treated as data")
def rule_injection(ctx):
    line = first_sentence_match(ctx, RE_INJECTION)
    return CheckResult(line is not None, None, line)


@check("verify-done", "all", "anthropic-bp", "G", "Completion is tied to a runnable verification")
def verify_done(ctx):
    line = first_sentence_match(ctx, RE_DONE, RE_VERIFY)
    return CheckResult(line is not None, None, line)


@check("etiquette", "all", "anthropic-bp", "G", "Commit, branch, or pull-request conventions exist")
def etiquette(ctx):
    line = first_sentence_match(ctx, RE_ETIQUETTE)
    return CheckResult(line is not None, None, line)


@check("pointers", "all", "anthropic-memory, humanlayer", "G", "Points to further documents instead of inlining them")
def pointers(ctx):
    n = len(RE_POINTER.findall(ctx.text))
    line = next((i for i, l in enumerate(ctx.lines, 1) if RE_POINTER.search(l)), None)
    return CheckResult(n >= 1, n, line)


@check("no-overview-dump", "all", "eth-agents-md, anthropic-bp", "G", "No architecture or directory-overview section longer than 40 lines")
def no_overview_dump(ctx):
    heads = list(iter_headings(ctx))
    worst, worst_line = 0, None
    for idx, (line_no, level, title) in enumerate(heads):
        if not RE_OVERVIEW.match(title):
            continue
        end = len(ctx.lines) + 1
        for nxt_line, nxt_level, _ in heads[idx + 1:]:
            if nxt_level <= level:
                end = nxt_line
                break
        length = end - line_no - 1
        if length > worst:
            worst, worst_line = length, line_no
    return CheckResult(worst <= 40, worst, worst_line)


@check("emphasis", "all", "anthropic-bp", "G", "Emphasized lines are at most max(3, 5% of lines)")
def emphasis(ctx):
    emphasized = [i for i, l in enumerate(ctx.lines, 1) if RE_EMPHASIS.search(l)]
    limit = max(3, 0.05 * len(ctx.lines))
    return CheckResult(len(emphasized) <= limit, len(emphasized), emphasized[0] if emphasized else None)


@check("vague", "all", "anthropic-memory", "G", "No unverifiable adjectives (properly, clean code, best practices, ...)")
def vague(ctx):
    hits = [(i, l) for i, l in enumerate(ctx.lines, 1) if RE_VAGUE.search(l)]
    count = sum(len(RE_VAGUE.findall(l)) for _, l in hits)
    return CheckResult(count == 0, count, hits[0][0] if hits else None)


@check("tool-leak", "agents-md", "anthropic-memory", "G", "A cross-tool AGENTS.md does not reference one tool's private paths")
def tool_leak(ctx):
    line = next((i for i, l in enumerate(ctx.lines, 1) if RE_TOOL_PRIVATE.search(l)), None)
    return CheckResult(line is None, None, line)


@check("pointer-file", "manifest", "anthropic-memory", "G", "The repository wires Claude Code to the shared file (CLAUDE.md is @AGENTS.md)")
def pointer_file(ctx):
    sib = ctx.sibling or {}
    if not sib.get("present"):
        return CheckResult(False, 0, None, "no CLAUDE.md beside AGENTS.md")
    text = (sib.get("text") or "").strip()
    first = next((l.strip() for l in text.splitlines() if l.strip()), "")
    ok = first == "@AGENTS.md" or text == "AGENTS.md"
    return CheckResult(ok, 1 if ok else 0, None, "" if ok else "CLAUDE.md does not start with @AGENTS.md")


# --------------------------------------------------------------------------- running

def make_context(key: str, filename: str, text: str, file_type: str | None = None, sibling: dict | None = None) -> FileContext:
    lines = tuple(text.splitlines())
    if file_type is None:
        file_type = detect_type(text)
    return FileContext(key, filename, file_type, text, lines, sibling)


def detect_type(text: str) -> str:
    """project iff any cmd-* check would pass. This is the single source of truth for the type rule."""
    probe = FileContext("probe", "AGENTS.md", "project", text, tuple(text.splitlines()), None)
    for spec in CHECKS:
        if spec.id.startswith("cmd-") and spec.fn(probe).passed:
            return "project"
    return "generic"


def run_checks(ctx: FileContext) -> list[tuple[CheckSpec, bool, CheckResult | None]]:
    out = []
    for spec in CHECKS:
        if applies(spec, ctx):
            out.append((spec, True, spec.fn(ctx)))
        else:
            out.append((spec, False, None))
    return out


def score(results) -> tuple[int, int]:
    passed = applicable = 0
    for spec, app, res in results:
        if spec.measure or not app:
            continue
        applicable += 1
        passed += 1 if res.passed else 0
    return passed, applicable


def rows_for(ctx: FileContext) -> list[dict]:
    rows = []
    for spec, app, res in run_checks(ctx):
        rows.append({
            "file": ctx.key,
            "check_id": spec.id,
            "applicable": "true" if app else "false",
            "pass": "" if (not app or res.passed is None) else ("true" if res.passed else "false"),
            "value": "" if (not app or res.value is None) else format_value(res.value),
            "line": "" if (not app or res.line is None) else str(res.line),
        })
    return rows


def format_value(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.3f}"


# --------------------------------------------------------------------------- corpus mode

def load_manifest() -> dict:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)


def load_lock() -> dict:
    return json.loads(LOCK.read_text(encoding="utf-8"))


def corpus_contexts() -> list[FileContext]:
    manifest = load_manifest()
    lock = load_lock()
    contexts = []
    for entry in manifest.get("files", []):
        key = entry["key"]
        locked = lock["files"].get(key)
        if locked is None:
            sys.exit(f"lint: {key} is not in {LOCK.name}; run `make data` first")
        cached = CACHE / f"{key}.md"
        if not cached.exists():
            sys.exit(f"lint: cache missing for {key}; run `make data` first")
        text = cached.read_text(encoding="utf-8")
        sibling = None
        if "sibling" in locked:
            sib_path = CACHE / f"{key}.sibling.md"
            sibling = {
                "path": locked["sibling"]["path"],
                "present": bool(locked["sibling"].get("present")),
                "text": sib_path.read_text(encoding="utf-8") if sib_path.exists() else None,
            }
        contexts.append(make_context(key, Path(entry["path"]).name, text, entry["type"], sibling))
    author = manifest.get("author")
    if author:
        path = ROOT / author["path"]
        text = path.read_text(encoding="utf-8")
        sib_file = path.parent / "CLAUDE.md"
        sibling = {"path": "CLAUDE.md", "present": sib_file.exists(), "text": sib_file.read_text(encoding="utf-8") if sib_file.exists() else None}
        contexts.append(make_context("author", path.name, text, author.get("type") or None, sibling))
    return contexts


def write_corpus() -> None:
    contexts = corpus_contexts()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for ctx in contexts:
        writer.writerows(rows_for(ctx))
    content = buf.getvalue()
    RESULTS.mkdir(parents=True, exist_ok=True)
    previous = CHECKS_CSV.read_text(encoding="utf-8") if CHECKS_CSV.exists() else None
    if previous == content:
        print(f"lint: {CHECKS_CSV.relative_to(ROOT)} unchanged ({len(contexts)} files, {len(CHECKS)} checks)")
        return
    CHECKS_CSV.write_text(content, encoding="utf-8")
    run = {
        "results_version": "v1",
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "python": ".".join(str(x) for x in sys.version_info[:3]),
        "lint_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "lock_sha256": hashlib.sha256(LOCK.read_bytes()).hexdigest(),
        "files": len(contexts),
        "checks": len(CHECKS),
    }
    RUN_JSON.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(f"lint: wrote {CHECKS_CSV.relative_to(ROOT)} and {RUN_JSON.relative_to(ROOT)} ({len(contexts)} files, {len(CHECKS)} checks)")


# --------------------------------------------------------------------------- self-test

def self_test() -> int:
    problems = []
    refs = REFERENCES.read_text(encoding="utf-8") if REFERENCES.exists() else ""
    defined = set(re.findall(r"^\[\^([\w-]+)\]:", refs, re.M))
    catalog = CATALOG.read_text(encoding="utf-8") if CATALOG.exists() else ""
    for spec in CHECKS:
        for key in spec.source:
            if key not in defined:
                problems.append(f"{spec.id}: source key '{key}' is not defined in docs/references.md")
        if f"`{spec.id}`" not in catalog:
            problems.append(f"{spec.id}: no row in docs/checks.md")
        if spec.grade not in {"G", "E+", "E-"}:
            problems.append(f"{spec.id}: bad grade {spec.grade}")
    for p in problems:
        print("self-test:", p)
    print(f"self-test: {len(CHECKS)} checks, {len(problems)} problems")
    return 1 if problems else 0


# --------------------------------------------------------------------------- CLI

def lint_files(paths: list[str], forced_type: str | None, fmt: str) -> int:
    all_rows = []
    for p in paths:
        path = Path(p)
        text = path.read_text(encoding="utf-8")
        sib = path.parent / "CLAUDE.md"
        sibling = None
        if path.name.upper() == "AGENTS.MD":
            sibling = {"path": "CLAUDE.md", "present": sib.exists(), "text": sib.read_text(encoding="utf-8") if sib.exists() else None}
        ctx = make_context(str(path), path.name, text, forced_type, sibling)
        results = run_checks(ctx)
        if fmt == "text":
            passed, applicable = score(results)
            print(f"{path}  (type: {ctx.file_type})")
            for spec, app, res in results:
                if spec.measure:
                    continue
                if not app:
                    status = "n/a "
                else:
                    status = "pass" if res.passed else "FAIL"
                detail = ""
                if app and res.value is not None:
                    detail += f" value={format_value(res.value)}"
                if app and res.line is not None:
                    detail += f" line={res.line}"
                if app and res.note:
                    detail += f" ({res.note})"
                print(f"  {status}  {spec.id:<18}{detail}")
            print(f"  score {passed}/{applicable}  (guideline conformance, grade G checks only; see docs/limitations.md)")
        else:
            all_rows.extend(rows_for(ctx))
    if fmt == "json":
        print(json.dumps(all_rows, indent=2))
    elif fmt == "csv":
        w = csv.DictWriter(sys.stdout, fieldnames=CSV_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(all_rows)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="context files to lint")
    ap.add_argument("--type", choices=("project", "generic"), help="override type detection")
    ap.add_argument("--format", choices=("text", "json", "csv"), default="text")
    ap.add_argument("--corpus", action="store_true", help="lint the manifest corpus into results/v1/checks.csv")
    ap.add_argument("--self-test", action="store_true", help="verify registry sources and catalog rows")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.corpus:
        write_corpus()
        return 0
    if not args.files:
        ap.print_help()
        return 2
    return lint_files(args.files, args.type, args.format)


if __name__ == "__main__":
    sys.exit(main())
