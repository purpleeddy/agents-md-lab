"""Manifest validation, lock-file determinism, and Software Heritage identifiers."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import data  # noqa: E402

GOOD = {
    "key": "example",
    "repo": "owner/name",
    "path": "AGENTS.md",
    "commit": "0" * 40,
    "license": "MIT",
    "type": "generic",
    "reason": "fixture",
}


class Swhid(unittest.TestCase):
    def test_empty_blob_matches_git(self):
        # git hash-object of an empty file
        self.assertEqual(data.swhid(b""), "swh:1:cnt:e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_known_blob(self):
        # printf 'hello\n' | git hash-object --stdin
        self.assertEqual(data.swhid(b"hello\n"), "swh:1:cnt:ce013625030ba8dba906f756967f9e9ca394464a")


class Validation(unittest.TestCase):
    def test_good_entry_passes(self):
        data.validate(dict(GOOD))

    def test_rejects_branch_as_commit(self):
        with self.assertRaises(SystemExit):
            data.validate({**GOOD, "commit": "main"})

    def test_rejects_unlisted_license(self):
        with self.assertRaises(SystemExit):
            data.validate({**GOOD, "license": "NOASSERTION"})

    def test_rejects_bad_type(self):
        with self.assertRaises(SystemExit):
            data.validate({**GOOD, "type": "monorepo"})

    def test_rejects_missing_reason(self):
        entry = dict(GOOD)
        del entry["reason"]
        with self.assertRaises(SystemExit):
            data.validate(entry)

    def test_raw_url_is_commit_pinned(self):
        self.assertEqual(
            data.raw_url("owner/name", "a" * 40, "AGENTS.md"),
            "https://raw.githubusercontent.com/owner/name/" + "a" * 40 + "/AGENTS.md",
        )


class LockFormat(unittest.TestCase):
    def test_dump_is_sorted_and_newline_terminated(self):
        text = data.dump_lock({"files": {"b": {"z": 1, "a": 2}, "a": {}}, "lock_version": 1})
        self.assertTrue(text.endswith("\n"))
        parsed = json.loads(text)
        self.assertEqual(list(parsed), ["files", "lock_version"])
        self.assertEqual(list(parsed["files"]), ["a", "b"])
        self.assertEqual(list(parsed["files"]["b"]), ["a", "z"])

    def test_lock_has_no_timestamps(self):
        lock = ROOT / "data" / "manifest.lock.json"
        if not lock.exists():
            self.skipTest("lock not generated yet")
        for entry in json.loads(lock.read_text())["files"].values():
            self.assertNotIn("fetched_at", entry)
            self.assertEqual(set(entry) - {"sibling"}, {"url", "sha256", "bytes", "swhid", "swhid_verified"})


if __name__ == "__main__":
    unittest.main()
