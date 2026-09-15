#!/usr/bin/env python3
"""Run current checks and the unchanged research checks in an isolated restore.

The public clone supplies history. Local recovery backups and private research
records are never prerequisites. Original optional skips remain visible gaps.
"""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_HISTORY = ("870a8cf",)


def verify_snapshot(snapshot, manifest, *, allow_git=False):
    """Reject missing, extra, changed, or unsafe entries before using a snapshot."""
    snapshot = Path(snapshot)
    expected = set()
    for entry in manifest["files"]:
        name = entry["path"]
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or not relative.parts
                or ".git" in relative.parts or name in expected):
            raise ValueError(f"Unsafe or duplicate archive path: {name}")
        expected.add(name)
        path = snapshot / name
        if any((snapshot / parent).is_symlink() for parent in relative.parents):
            raise ValueError(f"Archive path traverses a symlink: {name}")
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError as error:
            raise ValueError(f"Missing archive file: {name}") from error
        target = entry.get("symlink")
        if target is not None:
            if not stat.S_ISLNK(mode) or os.readlink(path) != target:
                raise ValueError(f"Changed archive link: {name}")
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(snapshot.resolve()):
                raise ValueError(f"Archive link leaves snapshot: {name}")
            payload = target.encode("utf-8")
        else:
            if not stat.S_ISREG(mode):
                raise ValueError(f"Archive entry is not a regular file: {name}")
            payload = path.read_bytes()
        if stat.S_IMODE(mode) != entry["mode"]:
            raise ValueError(f"Changed archive mode: {name}")
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"Changed archive contents: {name}")
    actual = set()
    for directory, subdirs, files in os.walk(snapshot, followlinks=False):
        directory = Path(directory)
        if allow_git and directory == snapshot:
            subdirs[:] = [name for name in subdirs if name != ".git"]
        for name in subdirs[:]:
            if (directory / name).is_symlink():
                actual.add((directory / name).relative_to(snapshot).as_posix())
                subdirs.remove(name)
        actual.update((directory / name).relative_to(snapshot).as_posix() for name in files)
    if actual != expected:
        raise ValueError("Archive file inventory differs: "
                         f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")


def git(repository, *arguments):
    result = subprocess.run(["git", "-C", str(repository), *arguments],
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"Required Git history unavailable ({' '.join(arguments)}). "
                         "Use a full-history clone; no private backup is required.\n"
                         + result.stderr.strip())
    return result.stdout.strip()


def restore_legacy(repository, destination):
    """Restore public tracked source with the real historical objects it checks."""
    repository, destination = Path(repository), Path(destination)
    manifest = json.loads((repository / "legacy/manifest.json").read_text(encoding="utf-8"))
    snapshot = repository / "legacy/research"
    verify_snapshot(snapshot, manifest)
    if git(repository, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Required Git history is incomplete: use a full-history clone.")
    for commit in (manifest["commit"], *manifest.get("required_history", REQUIRED_HISTORY)):
        git(repository, "cat-file", "-e", f"{commit}^{{commit}}")
    result = subprocess.run(
        ["git", "clone", "--quiet", "--no-checkout", "--no-hardlinks",
         str(repository), str(destination)], capture_output=True, text=True)
    if result.returncode:
        raise ValueError("Cannot create isolated historical clone: " + result.stderr.strip())
    git(destination, "checkout", "--quiet", "--detach", manifest["commit"])
    # The snapshot may include tracked edits that had not been committed at freeze time.
    shutil.copytree(snapshot, destination, dirs_exist_ok=True, symlinks=True)
    verify_snapshot(destination, manifest, allow_git=True)
    return destination


def run_command(label, arguments, directory):
    print(f"\n{label}: {' '.join(arguments)}", flush=True)
    result = subprocess.run(arguments, cwd=directory, capture_output=True, text=True)
    output = result.stdout + result.stderr
    unverified = []
    for line in output.splitlines():
        # Verbose unittest output identifies every original skip; successful test
        # names add little beside its final count and are the only lines omitted.
        if re.search(r" \.\.\. ok$", line):
            continue
        if " ... skipped " in line:
            unverified.append(line)
            print("UNVERIFIED: " + line)
        else:
            print(line)
    print(f"{label}: {'PASSED' if result.returncode == 0 else 'FAILED'} "
          f"(exit {result.returncode})", flush=True)
    return result.returncode, unverified


def run_legacy(repository):
    results = []
    try:
        with tempfile.TemporaryDirectory(prefix="aml-legacy-") as temporary:
            restored = restore_legacy(repository, Path(temporary) / "research")
            print("Legacy restore: PASSED (source hashes, modes, inventory, history)", flush=True)
            commands = (
                ("Legacy tests", [sys.executable, "-m", "unittest", "-v"]),
                ("Legacy generated outputs", [sys.executable, "scripts/compare.py", "--check"]),
                ("Legacy fixtures", [sys.executable, "scripts/experiment.py", "--dry-run"]),
            )
            for label, arguments in commands:
                results.append(run_command(label, arguments, restored))
    except (OSError, ValueError, KeyError) as error:
        print(f"Legacy restore: FAILED / UNVERIFIED: {error}", flush=True)
        results.append((1, ["Historical checks could not all run."]))
    return results


def main():
    results = [run_command("Active tests", [sys.executable, "-m", "unittest", "discover",
                                           "-s", "tests", "-t", ".", "-v"], ROOT)]
    results.append(run_command("Site generated outputs",
                               [sys.executable, "scripts/build_site.py", "--check"], ROOT))
    results.extend(run_legacy(ROOT))
    failed = any(code != 0 for code, _ in results)
    skipped = sum(len(gaps) for _, gaps in results)
    print(f"\nRequired commands: {'FAILED' if failed else 'PASSED'}. "
          f"Unverified coverage: {skipped} skipped or unavailable checks.")
    if skipped:
        print("A successful process exit does not mean all coverage was verified.")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
