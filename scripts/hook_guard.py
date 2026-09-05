#!/usr/bin/env python3
"""PreToolUse guard for this repository: the two rules a deny entry cannot express.

Reads the hook JSON on stdin. Exits 2 with a one-line reason on stderr to block the call and 0 to
allow it, printing nothing on the way through.

    Edit, Write, NotebookEdit   blocked when the file is inside this project and its
                                project-relative path is under `.claude/` or `.github/workflows/`,
                                or is this script. A path outside the project is allowed: it is
                                not this repository's to guard.
    Bash                        blocked when the command runs `git push` that carries a force
                                flag or a `+` refspec, or that targets `main` or `master`, named
                                in a refspec or as the checked-out branch of a bare push.

This is a convenience, not a guarantee. A hook sees one tool call, and a command line can always
be written in a form no parser anticipates. The guarantee is elsewhere: the deny list in
`.claude/settings.json` for the irreversible commands, and the GitHub ruleset on `main`, which
requires a pull request and rejects a force-push or a deletion, for the branch. Anything this
script cannot parse is allowed in silence. Standard library only.
"""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

WRITE_TOOLS = ("Edit", "Write", "NotebookEdit")
GUARDED_PREFIXES = (".claude/", ".github/workflows/")
GUARDED_FILES = ("scripts/hook_guard.py",)
PROTECTED_BRANCHES = ("main", "master")
FORCE_FLAGS = ("-f", "--force", "--force-with-lease", "--force-if-includes")
# git's own options that take their value as the next token, so that the subcommand after
# `git -C . push` is still found.
GIT_VALUE_OPTIONS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path",
                     "--config-env")
# `git push` options that take their value as the next token, so that the value is not read as a
# refspec.
PUSH_VALUE_OPTIONS = ("-o", "--push-option", "--repo", "--receive-pack", "--exec")
OPERATORS = (";", "&&", "||", "|", "&", "(", ")", "\n")
PREFIX = "Blocked by scripts/hook_guard.py: "


def project_dir(hook):
    """Where this repository is. `CLAUDE_PROJECT_DIR` is set by the harness that runs the hook and
    names the root even when the session works in a subdirectory; `cwd` is the fallback."""
    return os.environ.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or os.getcwd()


def tokens(command):
    """The command as a shell would read it. `punctuation_chars` is what splits `main; echo` into
    three tokens rather than leaving `main;` as a refspec no comparison matches."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def segments(command):
    """The commands a shell would run separately, each as a token list."""
    found = [[]]
    for token in tokens(command):
        if token in OPERATORS:
            found.append([])
        else:
            found[-1].append(token)
    return [segment for segment in found if segment]


def pushes(command):
    """The argument list after `push` for every `git push` in the command."""
    found = []
    for segment in segments(command):
        index = 0
        while index < len(segment):
            if os.path.basename(segment[index]) != "git":
                index += 1
                continue
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                option = segment[index]
                index += 1
                if option in GIT_VALUE_OPTIONS:
                    index += 1
            if index < len(segment) and segment[index] == "push":
                found.append(segment[index + 1:])
                break
    return found


def is_force(argument):
    """`--force`, `-f`, a lease flag with or without its value, and a short cluster such as
    `-fu`."""
    if argument in FORCE_FLAGS or argument.startswith("--force-with-lease="):
        return True
    return (len(argument) > 1 and argument[0] == "-" and argument[1] != "-"
            and argument[1:].isalpha() and "f" in argument[1:])


def destination(refspec):
    """The branch a refspec writes: the whole of `main`, the right side of `HEAD:main`."""
    name = refspec.split(":")[-1].lstrip("+")
    for prefix in ("refs/heads/",):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name


def names_a_branch(refspec):
    """`HEAD` on its own names no branch of its own: it is whichever branch is checked out, which
    is the question `current_branch` answers. `HEAD:main` names main and is read as a refspec."""
    return ":" in refspec or refspec != "HEAD"


def current_branch(cwd):
    """The checked-out branch, or an empty string when there is no repository or a detached HEAD."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "symbolic-ref", "--quiet", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def push_reason(arguments, cwd):
    positional = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        index += 1
        if argument == "--":
            positional.extend(arguments[index:])
            break
        if argument.startswith("+"):
            return ("the refspec `%s` starts with a plus, which forces the update; a force push "
                    "needs an explicit ask." % argument)
        if argument.startswith("-"):
            if is_force(argument):
                return ("this push carries `%s`; a force push needs an explicit ask and the "
                        "ruleset on main rejects it." % argument)
            if argument in PUSH_VALUE_OPTIONS:
                index += 1
            continue
        positional.append(argument)
    refspecs = [refspec for refspec in positional[1:] if names_a_branch(refspec)]
    for refspec in refspecs:
        branch = destination(refspec)
        if branch in PROTECTED_BRANCHES:
            return ("this push targets %s; push the branch this task created and open a pull "
                    "request instead, if the task asks for delivery." % branch)
    if not refspecs:
        branch = current_branch(cwd)
        if branch in PROTECTED_BRANCHES:
            return ("this push names no branch and %s is checked out; push the branch this task "
                    "created and open a pull request instead, if the task asks for delivery."
                    % branch)
    return ""


def bash_reason(hook):
    command = (hook.get("tool_input") or {}).get("command") or ""
    cwd = hook.get("cwd") or project_dir(hook)
    for arguments in pushes(command):
        reason = push_reason(arguments, cwd)
        if reason:
            return reason
    return ""


def write_reason(hook):
    tool_input = hook.get("tool_input") or {}
    # Edit and Write name the file in `file_path`, NotebookEdit in `notebook_path`.
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not raw:
        return ""
    project = Path(project_dir(hook)).expanduser().resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path(hook.get("cwd") or project) / path
    path = path.resolve()
    if not path.is_relative_to(project):
        return ""
    relative = path.relative_to(project).as_posix()
    if relative in GUARDED_FILES:
        return ("%s is the guard itself; changing what enforces the boundary needs an explicit "
                "ask." % relative)
    if relative.startswith(GUARDED_PREFIXES):
        return ("%s sets permissions or runs in CI; changing it needs an explicit ask."
                % relative)
    return ""


def main():
    try:
        hook = json.load(sys.stdin)
        if not isinstance(hook, dict):
            return 0
        tool = hook.get("tool_name")
        if tool in WRITE_TOOLS:
            reason = write_reason(hook)
        elif tool == "Bash":
            reason = bash_reason(hook)
        else:
            return 0
    except Exception:
        return 0
    if reason:
        print(PREFIX + reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
