import os
import pathlib
import sys
import unittest


def consumers():
    work = pathlib.Path(os.environ["WORK_DIR"])
    sys.path.insert(0, str(work))
    try:
        from invite import invite_key
        from member import member_key
    finally:
        sys.path.pop(0)
    return member_key, invite_key


class Acceptance(unittest.TestCase):
    def test_member_consumer(self):
        member_key, _ = consumers()
        self.assertEqual(member_key(" Ada@Example.COM "), "member:ada@example.com")

    def test_invite_consumer(self):
        _, invite_key = consumers()
        self.assertEqual(invite_key(" Ada@Example.COM "), "invite:ada@example.com")


if __name__ == "__main__":
    unittest.main()
