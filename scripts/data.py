#!/usr/bin/env python3
"""Fetch the corpus described in data/manifest.toml and pin it in data/manifest.lock.json.

Usage:
  python3 scripts/data.py              fetch missing or changed entries, write the lock file
  python3 scripts/data.py --update     accept upstream content changes (rewrites sha256 for changed entries)
  python3 scripts/data.py --check-links  network check of every URL in the lock and docs/references.md,
                                          and Software Heritage presence for each swhid

Corpus files are cached under data/cache/ (gitignored) and never committed.
Contract: docs/design.md sections 3, 4 and 7.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lint  # noqa: E402  (type rule lives in the check registry)

MANIFEST = ROOT / "data" / "manifest.toml"
LOCK = ROOT / "data" / "manifest.lock.json"
CACHE = ROOT / "data" / "cache"
REFERENCES = ROOT / "docs" / "references.md"
USER_AGENT = "agents-md-lab/1 (+https://github.com/agents-md-lab)"

# SPDX identifiers accepted in the manifest. OSI-approved and Creative Commons licenses, plus
# source-available licenses that permit reading and analysis. Extending this set is a reviewed change.
ALLOWED_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0", "0BSD", "Zlib", "Unlicense",
    "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later", "EPL-2.0", "EUPL-1.2", "MulanPSL-2.0", "NCSA",
    "PostgreSQL", "Python-2.0", "BSL-1.0", "Artistic-2.0", "OFL-1.1", "Ruby", "CC0-1.0", "CC-BY-4.0",
    "CC-BY-SA-4.0", "FSL-1.1-ALv2", "FSL-1.1-MIT", "BUSL-1.1",
}
KEY_RE = re.compile(r"^[a-z0-9-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = ("key", "repo", "path", "commit", "license", "type", "reason")


def fail(msg: str) -> None:
    sys.exit(f"data: {msg}")


def raw_url(repo: str, commit: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def swhid(data: bytes) -> str:
    """Software Heritage content identifier = git blob SHA-1 of the bytes."""
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode("ascii"))
    h.update(data)
    return f"swh:1:cnt:{h.hexdigest()}"


def load_manifest() -> dict:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)


def validate(entry: dict) -> None:
    for field in REQUIRED:
        if field not in entry or entry[field] in ("", None):
            fail(f"{entry.get('key', '?')}: missing field '{field}'")
    if not KEY_RE.match(entry["key"]):
        fail(f"{entry['key']}: key must match {KEY_RE.pattern}")
    if not SHA_RE.match(entry["commit"]):
        fail(f"{entry['key']}: commit must be a full 40-hex SHA, not '{entry['commit']}'")
    if entry["license"] == "NONE":
        if not entry.get("license_note"):
            fail(f"{entry['key']}: license = \"NONE\" requires a license_note saying no license file exists and when that was checked (docs/design.md 7.1)")
    elif entry["license"] not in ALLOWED_LICENSES:
        fail(f"{entry['key']}: license '{entry['license']}' is not in the allowlist (docs/design.md 7.1)")
    if entry["type"] not in ("project", "generic"):
        fail(f"{entry['key']}: type must be project or generic")


def dump_lock(lock: dict) -> str:
    return json.dumps(lock, indent=2, sort_keys=True) + "\n"


def sync(update: bool) -> int:
    manifest = load_manifest()
    entries = manifest.get("files", [])
    keys = [e.get("key") for e in entries]
    if len(keys) != len(set(keys)):
        fail("duplicate keys in manifest")
    old = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {"lock_version": 1, "files": {}}
    new = {"lock_version": 1, "files": {}}
    CACHE.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        validate(entry)
        key = entry["key"]
        url = raw_url(entry["repo"], entry["commit"], entry["path"])
        cached = CACHE / f"{key}.md"
        prior = old["files"].get(key)
        data = None
        if cached.exists() and prior and prior.get("url") == url:
            data = cached.read_bytes()
            if hashlib.sha256(data).hexdigest() != prior["sha256"]:
                data = None  # cache is stale; refetch
        if data is None:
            status, data = fetch(url)
            if status != 200 or not data:
                fail(f"{key}: HTTP {status} for {url}")
            cached.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        if prior and prior.get("sha256") != digest and not update:
            fail(f"{key}: content changed upstream (lock {prior['sha256'][:12]}..., now {digest[:12]}...). "
                 f"Re-run with --update to accept, or pin a different commit.")
        text = data.decode("utf-8", errors="replace")
        detected = lint.detect_type(text)
        if detected != entry["type"]:
            fail(f"{key}: manifest says type={entry['type']} but the file {'contains' if detected == 'project' else 'contains no'} "
                 f"runnable command; set type = \"{detected}\" (docs/design.md 7.2)")
        locked = {
            "url": url,
            "sha256": digest,
            "bytes": len(data),
            "swhid": swhid(data),
            "swhid_verified": bool(prior.get("swhid_verified")) if prior and prior.get("swhid") == swhid(data) else False,
        }
        if entry.get("sibling"):
            sib_url = raw_url(entry["repo"], entry["commit"], entry["sibling"])
            sib_cache = CACHE / f"{key}.sibling.md"
            sib_prior = (prior or {}).get("sibling")
            if sib_cache.exists() and sib_prior and sib_prior.get("present"):
                sib_data = sib_cache.read_bytes()
                status = 200
            else:
                status, sib_data = fetch(sib_url)
                if status == 200:
                    sib_cache.write_bytes(sib_data)
            locked["sibling"] = {
                "path": entry["sibling"],
                "present": status == 200,
                "sha256": hashlib.sha256(sib_data).hexdigest() if status == 200 else None,
                "bytes": len(sib_data) if status == 200 else 0,
            }
        new["files"][key] = locked
    content = dump_lock(new)
    if LOCK.exists() and LOCK.read_text(encoding="utf-8") == content:
        print(f"data: {len(entries)} entries, lock unchanged")
    else:
        LOCK.write_text(content, encoding="utf-8")
        print(f"data: {len(entries)} entries, wrote {LOCK.relative_to(ROOT)}")
    return 0


URL_RE = re.compile(r"https?://[^\s<>()\]\"']+")


def check_links() -> int:
    problems = 0
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {"files": {}}
    changed = False
    for key, entry in lock["files"].items():
        status, _ = fetch(entry["url"])
        ok = 200 <= status < 400
        print(f"{'ok ' if ok else 'BAD'} {status} {entry['url']}")
        problems += 0 if ok else 1
        hex_id = entry["swhid"].rsplit(":", 1)[1]
        status, _ = fetch(f"https://archive.softwareheritage.org/api/1/content/sha1_git:{hex_id}/")
        verified = status == 200
        print(f"{'ok ' if verified else '-- '} {status} swh {key} {'(archived)' if verified else '(not archived yet)'}")
        if verified != entry.get("swhid_verified"):
            entry["swhid_verified"] = verified
            changed = True
    if changed:
        LOCK.write_text(dump_lock(lock), encoding="utf-8")
        print("data: updated swhid_verified flags in lock")
    if REFERENCES.exists():
        seen = set()
        for url in URL_RE.findall(REFERENCES.read_text(encoding="utf-8")):
            url = url.rstrip(".,;")
            if url in seen:
                continue
            seen.add(url)
            status, _ = fetch(url)
            ok = 200 <= status < 400
            print(f"{'ok ' if ok else 'BAD'} {status} {url}")
            problems += 0 if ok else 1
    print(f"check-links: {problems} problems")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="accept upstream content changes")
    ap.add_argument("--check-links", action="store_true", help="verify URLs and Software Heritage presence")
    args = ap.parse_args(argv)
    if args.check_links:
        return check_links()
    return sync(args.update)


if __name__ == "__main__":
    sys.exit(main())
