import unittest
from units import to_milliseconds

class ApiTest(unittest.TestCase):
    def test_conversion(self):
        self.assertEqual(to_milliseconds(1.5), 1500)
