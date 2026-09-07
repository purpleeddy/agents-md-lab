import unittest
from invite import invite_key


class InviteTest(unittest.TestCase):
    def test_invite_key_trims_and_normalizes(self):
        self.assertEqual(invite_key(" Ada@Example.COM "), "invite:ada@example.com")
