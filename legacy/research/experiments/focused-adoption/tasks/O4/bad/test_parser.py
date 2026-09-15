import unittest
from parser import parse_row

class ParserTest(unittest.TestCase):
    def test_comma(self):
        self.assertEqual(parse_row("a,b"), ["a", "b"])

    def test_semicolon(self):
        self.assertEqual(parse_row("a;b", ";"), ["a", "b"])
