"""Self-contained pilot fixtures; graders and references stay outside candidates.

Materialize only ``files`` and give the candidate ``prompt``. Execute ``checks``
as a separate Python script with the candidate root on PYTHONPATH. SOLUTIONS is
exclusively for harness self-tests, never candidate input.
"""

from textwrap import dedent


def _code(text):
    return dedent(text).lstrip()


TASKS = {}
SOLUTIONS = {}


def _task(key, prompt, initial, visible, checks, solution, extra=None):
    files = {
        "app.py": _code(initial),
        "tests/test_app.py": "import unittest\nfrom app import *\n\n" + _code(visible),
        **(extra or {}),
    }
    TASKS[key] = {
        "prompt": prompt + (
            " Use only the Python standard library. Preserve existing tests and "
            "unrelated files. Keep tests/test_app.py byte-for-byte unchanged; add "
            "regression tests in a new test file and run "
            "`python3 -m unittest discover -s tests -v`."
        ),
        "files": files,
        "checks": "import unittest\nfrom app import *\n\n" + _code(checks)
        + "\nif __name__ == '__main__':\n    unittest.main()\n",
        "protected": ["tests/test_app.py", *(extra or {})],
    }
    SOLUTIONS[key] = {"app.py": _code(solution)}


_task(
    "interval_overlap",
    "Fix overlaps(a, b) in app.py. Intervals are numeric (start, end) pairs "
    "with half-open bounds [start, end). Touching intervals and empty intervals "
    "do not overlap. Reversed bounds must raise ValueError. Preserve symmetry.",
    """
    def overlaps(a, b):
        return a[0] <= b[1] and b[0] <= a[1]
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_interior(self):
            self.assertTrue(overlaps((1, 4), (2, 3)))
            self.assertFalse(overlaps((1, 2), (3, 4)))
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_boundaries(self):
            for a, b, expected in [((1, 2), (2, 3), False),
                                   ((2, 2), (1, 3), False),
                                   ((1, 4), (2, 3), True),
                                   ((-3, -1), (-2, 0), True),
                                   ((0, 0), (0, 0), False)]:
                self.assertEqual(overlaps(a, b), expected)
                self.assertEqual(overlaps(b, a), expected)
        def test_reversed(self):
            for a, b in [((3, 1), (0, 4)), ((0, 4), (3, 1))]:
                with self.assertRaises(ValueError):
                    overlaps(a, b)
    """,
    """
    def overlaps(a, b):
        if a[0] > a[1] or b[0] > b[1]:
            raise ValueError('Reversed interval')
        return max(a[0], b[0]) < min(a[1], b[1])
    """,
)

_task(
    "pagination",
    "Implement collect_pages(fetch, max_pages=10). fetch(cursor) returns "
    "(items, next_cursor); start with cursor None and stop when next_cursor "
    "is None. Preserve item order and duplicates. Follow empty pages. Raise "
    "ValueError before any fetch for max_pages < 1. Raise RuntimeError before "
    "fetching a repeated cursor or exceeding max_pages. Cursors are strings "
    "or None; an empty string is a valid cursor.",
    """
    def collect_pages(fetch, max_pages=10):
        items, cursor = fetch(None)
        return list(items)
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_single_page(self):
            self.assertEqual(collect_pages(lambda c: ([1], None)), [1])
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_multiple_and_empty(self):
            pages = {None: ([1, 1], ''), '': ([], 'last'), 'last': ([2], None)}
            seen = []
            def fetch(cursor):
                seen.append(cursor)
                return pages[cursor]
            self.assertEqual(collect_pages(fetch, 3), [1, 1, 2])
            self.assertEqual(seen, [None, '', 'last'])
        def test_guards(self):
            for limit, expected_calls in [(0, []), (1, [None]), (5, [None, 'x'])]:
                seen = []
                def fetch(cursor):
                    seen.append(cursor)
                    return [], 'x'
                with self.assertRaises(ValueError if limit == 0 else RuntimeError):
                    collect_pages(fetch, limit)
                self.assertEqual(seen, expected_calls)
    """,
    """
    def collect_pages(fetch, max_pages=10):
        if max_pages < 1:
            raise ValueError('max_pages must be positive')
        result, seen, cursor = [], set(), None
        for _ in range(max_pages):
            if cursor in seen:
                raise RuntimeError('Repeated cursor')
            seen.add(cursor)
            items, cursor = fetch(cursor)
            result.extend(items)
            if cursor is None:
                return result
        raise RuntimeError('Page limit exceeded')
    """,
)

_task(
    "keyword_interface",
    "Extend format_label(name, prefix='Hello') with a keyword-only suffix "
    "argument defaulting to '!'. Keep both existing positional arguments "
    "compatible. Strip surrounding whitespace from name only, return "
    "prefix + ' ' + stripped name + suffix, and reject blank names with "
    "ValueError. A third positional argument must raise TypeError. "
    "The existing caller in caller.py must continue to work.",
    """
    def format_label(name, prefix='Hello'):
        return prefix + ' ' + name + '!'
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_legacy(self):
            self.assertEqual(format_label('Ada'), 'Hello Ada!')
            self.assertEqual(format_label('Ada', 'Hi'), 'Hi Ada!')
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_interface(self):
            from caller import greeting
            self.assertEqual(greeting(), 'Hi Ada!')
            self.assertEqual(format_label(' Ada ', suffix='.'), 'Hello Ada.')
            self.assertEqual(format_label('Ada', ' Hi ', suffix=''), ' Hi  Ada')
            with self.assertRaises(TypeError):
                format_label('Ada', 'Hi', '?')
            for blank in ['', '  ', '\\t\\n']:
                with self.assertRaises(ValueError):
                    format_label(blank)
    """,
    """
    def format_label(name, prefix='Hello', *, suffix='!'):
        name = name.strip()
        if not name:
            raise ValueError('Name is blank')
        return prefix + ' ' + name + suffix
    """,
    {"caller.py": "from app import format_label\n\ndef greeting():\n    return format_label('Ada', 'Hi')\n"},
)

_task(
    "csv_totals",
    "Fix totals(text) to parse CSV with exactly the header name,amount. "
    "Support CSV quoting, embedded commas and newlines in names, and CRLF. "
    "Sum integer amounts per exact name, preserving first-seen key order. "
    "Skip blank rows. Empty text and header-only input return {}. Raise "
    "ValueError for wrong headers, rows with other than two fields, or "
    "non-integer amounts. Negative amounts are valid.",
    """
    def totals(text):
        result = {}
        for line in text.splitlines()[1:]:
            name, amount = line.split(',')
            result[name] = int(amount)
        return result
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_simple(self):
            self.assertEqual(totals('name,amount\\na,2\\n'), {'a': 2})
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_csv(self):
            text = 'name,amount\\r\\n"a,b",2\\r\\n\\r\\n"line\\nbreak",3\\r\\n"a,b",-1\\r\\n'
            result = totals(text)
            self.assertEqual(result, {'a,b': 1, 'line\\nbreak': 3})
            self.assertEqual(list(result), ['a,b', 'line\\nbreak'])
            self.assertEqual(totals(''), {})
            self.assertEqual(totals('name,amount\\n'), {})
        def test_invalid(self):
            for text in ['amount,name\\n2,a', 'name,amount\\na,2,3',
                         'name,amount\\na', 'name,amount\\na,nope']:
                with self.assertRaises(ValueError, msg=text):
                    totals(text)
    """,
    """
    import csv
    import io

    def totals(text):
        rows = csv.reader(io.StringIO(text, newline=''))
        header = next(rows, None)
        if header is None:
            return {}
        if header != ['name', 'amount']:
            raise ValueError('Unexpected header')
        result = {}
        for row in rows:
            if not row:
                continue
            if len(row) != 2:
                raise ValueError('Expected two fields')
            name, amount = row
            result[name] = result.get(name, 0) + int(amount)
        return result
    """,
)

_task(
    "scoped_normalization",
    "Fix normalize_tags(tags) so it strips whitespace, lowercases, removes "
    "empty tags and duplicates, and preserves first occurrence order. "
    "Accept any iterable of strings, including generators, without mutating "
    "the input. Keep render_title's existing behavior unchanged; it belongs "
    "to a separate feature. notes.txt is unrelated user work and must stay intact.",
    """
    def normalize_tags(tags):
        return sorted(set(tag.lower() for tag in tags))

    def render_title(title):
        return 'Title: ' + title
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_existing(self):
            self.assertEqual(normalize_tags(['A', 'a']), ['a'])
            self.assertEqual(render_title('  Draft '), 'Title:   Draft ')
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_order_and_input(self):
            values = [' Z ', '', 'a', 'z', ' A ', '  ', 'B']
            before = values[:]
            self.assertEqual(normalize_tags(values), ['z', 'a', 'b'])
            self.assertEqual(values, before)
            self.assertEqual(normalize_tags(iter(values)), ['z', 'a', 'b'])
            self.assertEqual(normalize_tags([]), [])
        def test_other_feature(self):
            self.assertEqual(render_title(' mIxEd '), 'Title:  mIxEd ')
    """,
    """
    def normalize_tags(tags):
        result, seen = [], set()
        for tag in tags:
            tag = tag.strip().lower()
            if tag and tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    def render_title(title):
        return 'Title: ' + title
    """,
    {"notes.txt": "User draft: retain capitalization in titles.\n"},
)

_task(
    "merge_defaults",
    "Fix merge_defaults(settings, defaults). Return a new dict with default "
    "values only for keys missing from settings. Explicit None, False, 0, "
    "and empty strings must be preserved. Keep all settings keys, do not "
    "mutate either input, and preserve shallow reference semantics for "
    "nested values. Existing tests must remain intact.",
    """
    def merge_defaults(settings, defaults):
        result = dict(settings)
        for key, value in defaults.items():
            if not result.get(key):
                result[key] = value
        return result
    """,
    """
    class ExistingTests(unittest.TestCase):
        def test_defaults(self):
            self.assertEqual(merge_defaults({'x': 2}, {'x': 1, 'y': 3}),
                             {'x': 2, 'y': 3})
    """,
    """
    class ContractTests(unittest.TestCase):
        def test_falsy(self):
            for value in [None, False, 0, '', [], {}]:
                settings, defaults = {'x': value, 'extra': 8}, {'x': 7, 'y': 9}
                result = merge_defaults(settings, defaults)
                self.assertIs(result['x'], value)
                self.assertEqual(result, {'x': value, 'extra': 8, 'y': 9})
                self.assertEqual(settings, {'x': value, 'extra': 8})
                self.assertEqual(defaults, {'x': 7, 'y': 9})
                self.assertIsNot(result, settings)
                self.assertIsNot(result, defaults)
        def test_shallow(self):
            nested = [1]
            result = merge_defaults({}, {'nested': nested})
            self.assertIs(result['nested'], nested)
            self.assertEqual(merge_defaults({}, {}), {})
    """,
    """
    def merge_defaults(settings, defaults):
        result = dict(defaults)
        result.update(settings)
        return result
    """,
)
