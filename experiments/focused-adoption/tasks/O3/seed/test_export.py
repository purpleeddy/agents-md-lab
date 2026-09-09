import csv
import io
import unittest

class ExportTest(unittest.TestCase):
    def test_header(self):
        self.assertEqual(next(csv.reader(io.StringIO("name,total\n"))), ["name", "total"])
