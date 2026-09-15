import unittest
from legacy import legacy_status


class LegacyFailureTest(unittest.TestCase):
    def test_old_failure_is_real_and_unrelated(self):
        self.assertEqual(legacy_status(), "ready")
