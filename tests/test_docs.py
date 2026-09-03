"""Tests for the published pages: docs/index.html, docs/compare.js and the Markdown pages.

These check the things a reader can see: that every citation key resolves, that every generated
block is what the data renders, that the vocabulary the project committed to is kept, that the
page loads nothing from a third-party host, and that the two published files stay inside their
size budgets.
"""

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
INDEX = DOCS / "index.html"
COMPARE_JS = DOCS / "compare.js"
REFERENCES = DOCS / "references.md"
README = REPO_ROOT / "README.md"
PILOT = REPO_ROOT / "experiments" / "pilot-round2.json"
NODE = shutil.which("node")

INDEX_MAX_BYTES = 60 * 1024
COMPARE_JS_MAX_BYTES = 25 * 1024

# Hosts the page is allowed to link to. Everything else must be a relative path or a fragment:
# the page loads no font, script, style or image from anywhere but itself.
ALLOWED_HOSTS = ("https://github.com/", "https://raw.githubusercontent.com/")

FORBIDDEN = re.compile(
    r"\b(best|scores?|scored|scoring|ranks?|ranked|ranking|evolved|winner)\b", re.IGNORECASE
)

# Phrases that contain a forbidden word and are still allowed, each for one reason:
#   - the two interval names are the statistics' own names;
#   - "best practices" is the title of a cited vendor page, quoted in docs/criteria.json and
#     rendered from there into the pages;
#   - "no ranking" / "not a ranking" is the project saying it does not rank, which is the point
#     of the rule.
ALLOWED_PHRASES = (
    "Wilson score interval",
    "hybrid-score interval",
    "best practices",
    "Best practices for Claude Code",
    "no ranking",
    "not a ranking",
    "Not a ranking",
)

URL = re.compile(r"https?://\S+")
FENCE = re.compile(r"```.*?```", re.DOTALL)
CODE_SPAN = re.compile(r"`[^`\n]*`")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HIDDEN_ELEMENT = re.compile(r"<(script|template|pre|style)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")
ANCHOR_DEF = re.compile(r'<a id="ref-([A-Za-z0-9_-]+)"></a>')
REFERENCE_LINK = re.compile(r"references\.(?:md|html)#ref-([A-Za-z0-9_-]+)")
FOOTNOTE_SYNTAX = re.compile(r"(?<!\\)\[\^")


def markdown_pages():
    """The README is added in a later commit than the docs pages; until it exists there is
    nothing to check in it."""
    pages = sorted(DOCS.glob("*.md"))
    if README.exists():
        pages.append(README)
    return pages


def strip_markdown_code(text):
    """Prose only: a URL and a code span are not sentences the reader reads."""
    return URL.sub(" ", CODE_SPAN.sub(" ", FENCE.sub(" ", text)))


def index_text():
    """The words a reader actually sees: no comments, no script, template, pre or style
    content, and no tags or attributes."""
    text = HIDDEN_ELEMENT.sub(" ", HTML_COMMENT.sub(" ", INDEX.read_text(encoding="utf-8")))
    text = TAG.sub(" ", text)
    return text.replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"')


def without_allowed(text):
    for phrase in ALLOWED_PHRASES:
        text = text.replace(phrase, " ")
    return text


def defined_keys():
    """A citation resolves to an explicit anchor, not to a kramdown footnote: kramdown drops a
    footnote definition nothing refers to, so the anchors are what survives publication."""
    return set(ANCHOR_DEF.findall(REFERENCES.read_text(encoding="utf-8")))


class CitationTest(unittest.TestCase):
    def test_no_page_uses_footnote_syntax(self):
        for path in markdown_pages():
            text = strip_markdown_code(path.read_text(encoding="utf-8"))
            self.assertIsNone(FOOTNOTE_SYNTAX.search(text), path.name)

    def test_every_anchor_is_defined_once(self):
        keys = ANCHOR_DEF.findall(REFERENCES.read_text(encoding="utf-8"))
        self.assertEqual(sorted(keys), sorted(set(keys)))

    def test_every_criteria_source_has_a_definition(self):
        defined = defined_keys()
        criteria = json.loads((DOCS / "criteria.json").read_text(encoding="utf-8"))
        for criterion in criteria["criteria"]:
            for key in criterion["sources"]:
                self.assertIn(key, defined, "criterion %s cites %s" % (criterion["id"], key))

    def test_every_reference_link_points_at_a_defined_key(self):
        defined = defined_keys()
        pages = [path.read_text(encoding="utf-8") for path in markdown_pages()]
        pages.append(INDEX.read_text(encoding="utf-8"))
        for text in pages:
            for key in REFERENCE_LINK.findall(text):
                self.assertIn(key, defined)

    def test_a_markdown_page_links_to_a_markdown_page(self):
        # GitHub Pages rewrites .md links in a Markdown source; GitHub's own file view needs
        # them. index.html is a static file and keeps its .html links.
        for path in markdown_pages():
            text = strip_markdown_code(path.read_text(encoding="utf-8"))
            for target in re.findall(r"\]\((?!https?:)([^)#]*\.html)", text):
                self.assertEqual(target, "index.html", "%s links to %s" % (path.name, target))


class GeneratedBlockTest(unittest.TestCase):
    def test_check_passes_on_every_generated_block(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "compare.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_marked_block_is_closed(self):
        for path in (INDEX, DOCS / "methodology.md", README):
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            starts = re.findall(r"<!-- ([a-z]+):start -->", text)
            ends = re.findall(r"<!-- ([a-z]+):end -->", text)
            self.assertEqual(starts, ends, path.name)


class VocabularyTest(unittest.TestCase):
    def test_no_forbidden_word_in_the_markdown_pages(self):
        for path in markdown_pages():
            text = without_allowed(strip_markdown_code(path.read_text(encoding="utf-8")))
            found = FORBIDDEN.findall(text)
            self.assertEqual(found, [], "%s uses %s" % (path.name, found))

    def test_no_forbidden_word_in_the_page_text(self):
        found = FORBIDDEN.findall(without_allowed(index_text()))
        self.assertEqual(found, [], "docs/index.html uses %s" % (found,))


class PageTest(unittest.TestCase):
    def setUp(self):
        self.html = INDEX.read_text(encoding="utf-8")

    def test_no_third_party_resource(self):
        for url in re.findall(r'(?:src|href)="([^"]+)"', self.html):
            if url.startswith("#") or "://" not in url:
                continue
            self.assertTrue(url.startswith(ALLOWED_HOSTS), url)

    def test_every_internal_link_has_a_target(self):
        ids = set(re.findall(r'id="([^"]+)"', self.html))
        for target in re.findall(r'href="#([^"]+)"', self.html):
            self.assertIn(target, ids)

    def test_the_page_declares_its_language_and_title(self):
        self.assertIn('<html lang="en">', self.html)
        self.assertIn("<title>agents-md-lab</title>", self.html)
        self.assertIn('<meta name="description"', self.html)

    def test_sizes_stay_inside_the_budget(self):
        self.assertLessEqual(INDEX.stat().st_size, INDEX_MAX_BYTES)
        self.assertLessEqual(COMPARE_JS.stat().st_size, COMPARE_JS_MAX_BYTES)

    def test_the_check_panel_carries_the_privacy_line(self):
        self.assertIn("Nothing is sent or stored; the check runs in your browser.", self.html)


@unittest.skipIf(NODE is None, "node is not installed")
class ExperimentRendererTest(unittest.TestCase):
    """The experiment section is built in JavaScript from experiment.json. It is rendered here
    in Node against a recorded run file, so the shape is checked without a browser."""

    def render(self, source):
        script = (
            "const lab=require(%s);"
            "const data=%s;"
            "process.stdout.write(lab.renderExperiment(data));"
            % (json.dumps(str(COMPARE_JS)), source)
        )
        result = subprocess.run([NODE, "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_a_recorded_run_file_renders_tables_and_a_chart(self):
        html = self.render("require(%s)" % json.dumps(str(PILOT)))
        for task in ("task1", "task2", "task3"):
            self.assertIn("<h3>%s</h3>" % task, html)
        self.assertIn("<svg class=\"chart\"", html)
        self.assertIn("per cell", html)
        self.assertIn("↑ better", html)
        self.assertIn("Cost, turns and duration", html)

    def test_an_empty_file_renders_nothing_so_the_planned_sentence_stands(self):
        self.assertEqual(self.render('{"by_task":{},"generated_utc":"x"}'), "")

    def test_the_intervals_come_from_the_file(self):
        data = json.loads(PILOT.read_text(encoding="utf-8"))
        entry = data["by_task"]["task1"]["comparison"]["tests_written"]["conditions"]["ours"]
        html = self.render("require(%s)" % json.dumps(str(PILOT)))
        self.assertIn("[%.2f, %.2f]" % (entry["lo"], entry["hi"]), html)


if __name__ == "__main__":
    unittest.main()
