import unittest
from docs import build


class CliImplementationTest(unittest.TestCase):
    def test_build_uses_requested_cache_directory(self):
        self.assertEqual(build("cache-a"), "built examples in cache-a")
