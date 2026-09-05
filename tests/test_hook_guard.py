"""Tests for scripts/hook_guard.py, the PreToolUse guard named in .claude/settings.json.

The script is driven the way the harness drives it: as a subprocess reading one hook payload on
stdin. A blocked call has to exit 2 and name what stopped it, an allowed call has to exit 0 in
silence, and every case here is one line of the tier table in CONTRIBUTING.md.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "scripts" / "hook_guard.py"


class HookGuardTest(unittest.TestCase):
    def guard(self, payload, project):
        """One hook call. The project directory is passed in both places the script reads it, so
        that the result does not depend on which one the harness happens to set."""
        payload = dict(payload, cwd=str(project))
        result = subprocess.run(
            [sys.executable, str(GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=dict(os.environ, CLAUDE_PROJECT_DIR=str(project)),
        )
        self.assertEqual(result.stdout, "", "the guard printed to stdout")
        return result

    def bash(self, command, project=REPO_ROOT):
        return self.guard(
            {"tool_name": "Bash", "tool_input": {"command": command}}, project
        )

    def write(self, path, project=REPO_ROOT, tool="Edit"):
        return self.guard(
            {"tool_name": tool, "tool_input": {"file_path": str(path)}}, project
        )

    def assertBlocked(self, result, named):
        self.assertEqual(result.returncode, 2, "not blocked: %r" % result.stderr)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1, result.stderr)
        self.assertIn(named, result.stderr)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def repository(self, branch):
        """A throwaway repository on `branch`, for the pushes that carry no refspec. An unborn
        branch is enough: `symbolic-ref` reads HEAD and never a commit."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        subprocess.run(["git", "init", "-q", directory.name], check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "-C", directory.name, "symbolic-ref", "HEAD",
                        "refs/heads/" + branch], check=True, capture_output=True, text=True)
        return Path(directory.name)

    # Blocked: the writes.

    def test_a_write_to_the_project_settings_file_is_blocked(self):
        self.assertBlocked(self.write(REPO_ROOT / ".claude" / "settings.json"),
                           ".claude/settings.json")

    def test_a_write_to_the_guard_script_itself_is_blocked(self):
        self.assertBlocked(self.write(GUARD), "scripts/hook_guard.py is the guard itself")

    def test_a_write_to_a_workflow_file_is_blocked(self):
        self.assertBlocked(self.write(REPO_ROOT / ".github" / "workflows" / "ci.yml"),
                           ".github/workflows/ci.yml")

    # Blocked: the pushes.

    def test_a_push_that_sets_upstream_to_main_is_blocked(self):
        self.assertBlocked(self.bash("git push -u origin main"), "targets main")

    def test_a_push_of_head_to_main_is_blocked(self):
        self.assertBlocked(self.bash("git push origin HEAD:main"), "targets main")

    def test_a_push_with_a_plus_refspec_is_blocked(self):
        self.assertBlocked(self.bash("git push origin +feature/x"), "force push")

    def test_a_force_push_is_blocked(self):
        self.assertBlocked(self.bash("git push --force origin f"), "force push")

    def test_a_push_from_a_git_with_a_global_option_is_blocked(self):
        self.assertBlocked(self.bash("git -C . push origin main"), "targets main")

    def test_a_push_with_no_refspec_on_a_main_checkout_is_blocked(self):
        repository = self.repository("main")
        self.assertBlocked(self.bash("git push", project=repository), "main is checked out")

    def test_a_push_of_head_on_a_main_checkout_is_blocked(self):
        # `HEAD` names no branch of its own, so the branch it stands for is the one to look up.
        repository = self.repository("main")
        self.assertBlocked(self.bash("git push origin HEAD", project=repository),
                           "main is checked out")

    def test_both_refusals_qualify_the_delivery_they_point_at(self):
        """Under the shipped v1.2.0 line a push is not automatically permitted, so the tail the
        guard prints asks for the task to have called for delivery. Both refusal paths carry it:
        the refspec that names a protected branch and the push that names none on a protected
        checkout."""
        tail = "open a pull request instead, if the task asks for delivery."
        self.assertBlocked(self.bash("git push origin HEAD:main"), tail)
        repository = self.repository("main")
        self.assertBlocked(self.bash("git push", project=repository), tail)

    # Allowed.

    def test_a_plan_file_outside_the_project_is_allowed(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        home = Path(directory.name) / "home"
        project = Path(directory.name) / "project"
        plan = home / ".claude" / "plans" / "permission-tiers.md"
        plan.parent.mkdir(parents=True)
        project.mkdir()
        self.assertAllowed(self.write(plan, project=project))

    def test_a_write_to_a_published_page_is_allowed(self):
        self.assertAllowed(self.write(REPO_ROOT / "docs" / "index.html"))

    def test_a_push_of_a_task_branch_is_allowed(self):
        self.assertAllowed(self.bash("git push origin feature/x"))

    def test_a_push_of_head_to_a_task_branch_is_allowed(self):
        self.assertAllowed(self.bash("git push -u origin HEAD:feature/x"))

    def test_a_push_with_no_refspec_on_a_task_branch_is_allowed(self):
        repository = self.repository("feature/x")
        self.assertAllowed(self.bash("git push", project=repository))

    def test_a_push_of_head_on_a_task_branch_is_allowed(self):
        repository = self.repository("feature/x")
        self.assertAllowed(self.bash("git push origin HEAD", project=repository))

    def test_a_push_named_inside_a_quoted_argument_is_not_a_push(self):
        self.assertAllowed(self.bash('echo "git push origin main"'))

    def test_an_unknown_tool_name_is_allowed(self):
        self.assertAllowed(
            self.guard({"tool_name": "Grep", "tool_input": {"pattern": "push"}}, REPO_ROOT)
        )


if __name__ == "__main__":
    unittest.main()
