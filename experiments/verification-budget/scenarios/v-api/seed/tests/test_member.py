import unittest
from member import member_key


class MemberTest(unittest.TestCase):
    def test_member_key_trims_and_normalizes(self):
        self.assertEqual(member_key(" Ada@Example.COM "), "member:ada@example.com")
