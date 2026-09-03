"""Tests for the published pages: docs/index.html, docs/compare.js and the Markdown pages.

These check the things a reader can see: that every citation key resolves, that every generated
block is what the data renders, that the vocabulary the project committed to is kept, that the
page loads nothing from a third-party host, and that the two published files stay inside their
size budgets.
"""

import hashlib
import html
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
SITE_CSS = DOCS / "site.css"
STAR_JS = DOCS / "star.js"
LAYOUT = DOCS / "_layouts" / "default.html"
REFERENCES = DOCS / "references.md"
README = REPO_ROOT / "README.md"
EXPERIMENT = REPO_ROOT / "docs" / "data" / "experiment.json"
NODE = shutil.which("node")

INDEX_MAX_BYTES = 60 * 1024
COMPARE_JS_MAX_BYTES = 28 * 1024
SITE_CSS_MAX_BYTES = 22 * 1024
STAR_JS_MAX_BYTES = 3 * 1024

# Hosts the page is allowed to link to. Everything else must be a relative path or a fragment:
# the page loads no font, script, style or image from anywhere but itself.
ALLOWED_HOSTS = ("https://github.com/", "https://raw.githubusercontent.com/")

# The one request the page makes to another host, and the only place it may be written: the
# star count is read from GitHub's API in docs/star.js, which is the only file that talks to
# another host.
STARS_URL = "https://api.github.com/repos/purpleeddy/agents-md-lab"
STAR_LINK = (
    '<a class="star" href="https://github.com/purpleeddy/agents-md-lab" target="_blank" '
    'rel="noopener" aria-label="Star agents-md-lab on GitHub"'
)

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


class AnchorTest(unittest.TestCase):
    """Every link into another page of this site lands on a heading that exists. The published
    pages are Markdown converted by kramdown, whose heading id is the text lower-cased with
    everything but letters, digits, spaces and hyphens removed and the spaces turned into
    hyphens; an explicit `<a id="...">` counts too."""

    HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
    EXPLICIT = re.compile(r'<a id="([^"]+)">')
    LINK = re.compile(r'(?:href="|\]\()(?:docs/)?([a-z]+)\.(?:html|md)#([^"\)]+)')

    def slug(self, title):
        text = re.sub(r"<[^>]+>", "", title).replace("`", "").replace("*", "")
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        return re.sub(r"\s+", "-", text.strip()).lower()

    def anchors(self, page):
        text = page.read_text(encoding="utf-8")
        found = {self.slug(title) for title in self.HEADING.findall(text)}
        return found | set(self.EXPLICIT.findall(text))

    def test_every_cross_page_fragment_exists(self):
        pages = {path.stem: path for path in DOCS.glob("*.md")}
        anchors = {name: self.anchors(path) for name, path in pages.items()}
        sources = [INDEX, README] + list(pages.values())
        for source in sources:
            for page, fragment in self.LINK.findall(source.read_text(encoding="utf-8")):
                if page not in anchors:
                    continue
                self.assertIn(fragment, anchors[page], "%s links to %s#%s"
                              % (source.name, page, fragment))


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
        for path in (INDEX, DOCS / "methodology.md", DOCS / "findings.md", README):
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            starts = re.findall(r"<!-- ([a-z-]+):start -->", text)
            ends = re.findall(r"<!-- ([a-z-]+):end -->", text)
            self.assertEqual(starts, ends, path.name)


class KnownIssuesTest(unittest.TestCase):
    """The independent review is recorded as a table with a response per row. Two reviewers gave
    24 findings each; the table merges them, and every finding has to appear in it."""

    def section(self):
        text = (DOCS / "rationale.md").read_text(encoding="utf-8")
        self.assertIn("## Known issues (independent review, 2026-09-03)", text)
        after = text.split("## Known issues (independent review, 2026-09-03)")[1]
        return after.split("\n## ")[0]

    def rows(self):
        return [
            line for line in self.section().split("\n")
            if line.startswith("| ") and not line.startswith("|---")
            and not line.startswith("| Findings")
        ]

    def test_the_table_stays_under_twenty_rows(self):
        self.assertLessEqual(len(self.rows()), 20)

    def test_every_finding_of_both_reviews_has_a_row(self):
        listed = set(re.findall(r"\b([AB]\d{1,2})\b",
                                " ".join(row.split("|")[1] for row in self.rows())))
        expected = {"A%d" % i for i in range(1, 25)} | {"B%d" % i for i in range(1, 25)}
        self.assertEqual(expected - listed, set())

    def test_every_row_carries_a_response(self):
        allowed = ("fixed in v1.0.1", "applied in v1.1", "enforceable by the example settings",
                   "v1.1 candidate", "disagree because", "covered by", "the line is cut in v1.1",
                   "the rule stands")
        for row in self.rows():
            response = row.split("|")[5]
            self.assertTrue(any(word in response for word in allowed), row)


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
        for text in (self.html, LAYOUT.read_text(encoding="utf-8")):
            for url in re.findall(r'(?:src|href)="([^"]+)"', text):
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
        self.assertLessEqual(SITE_CSS.stat().st_size, SITE_CSS_MAX_BYTES)
        self.assertLessEqual(STAR_JS.stat().st_size, STAR_JS_MAX_BYTES)

    def test_every_page_carries_the_star_link(self):
        for text in (self.html, LAYOUT.read_text(encoding="utf-8")):
            self.assertIn(STAR_LINK, text)

    def test_the_star_count_is_the_only_request_to_another_host(self):
        star = STAR_JS.read_text(encoding="utf-8")
        self.assertIn(STARS_URL, star)
        self.assertEqual(re.findall(r"https?://[^\"'\s]+", star), [STARS_URL])
        self.assertEqual(re.findall(r"https?://", COMPARE_JS.read_text(encoding="utf-8")), [])
        for text in (self.html, LAYOUT.read_text(encoding="utf-8")):
            self.assertIn('<script src="star.js"></script>', text)

    def test_each_criteria_set_carries_its_own_caption(self):
        self.assertIn("Coverage of ten sourced rule criteria", self.html)
        self.assertIn(
            "Coverage of eight sourced content criteria",
            COMPARE_JS.read_text(encoding="utf-8"),
        )

    def test_the_verdicts_are_pills(self):
        self.assertIn('<td class="v met"><span class="pill">met</span></td>', self.html)
        self.assertIn('<td class="v unmet"><span class="pill">not met</span></td>', self.html)
        self.assertIn(".pill", SITE_CSS.read_text(encoding="utf-8"))

    def test_the_pages_share_one_stylesheet(self):
        # The front page and the Markdown pages are styled by the same file, so the two cannot
        # drift apart; index.html keeps only the generated stacked-table labels inline.
        self.assertIn('<link rel="stylesheet" href="site.css">', self.html)
        layout = LAYOUT.read_text(encoding="utf-8")
        self.assertIn('<link rel="stylesheet" href="site.css">', layout)
        self.assertIn("{{ content }}", layout)
        self.assertNotIn("theme:", (DOCS / "_config.yml").read_text(encoding="utf-8"))

    def test_every_navigation_target_exists(self):
        # The layout's navigation names published pages; a page publishes from its Markdown
        # source, so the source has to be there.
        for text in (self.html, LAYOUT.read_text(encoding="utf-8")):
            for target in re.findall(r'href="([a-z]+)\.html', text):
                self.assertTrue((DOCS / (target + ".md")).exists() or target == "index", target)

    def test_the_compare_section_offers_both_criteria_sets(self):
        self.assertIn('<select id="criteria-set">', self.html)
        self.assertIn('id="content-matrix"', self.html)
        # Without JavaScript the content table is only in the generated Markdown, so the page
        # has to say where.
        self.assertIn(
            "https://github.com/purpleeddy/agents-md-lab/blob/main/docs/generated/comparison.md",
            self.html,
        )
        self.assertIn("Show this repository's file (written to these criteria)", self.html)

    def test_the_download_button_offers_the_root_file(self):
        self.assertIn(
            '<a class="btn ghost" href="https://raw.githubusercontent.com/purpleeddy/'
            'agents-md-lab/main/AGENTS.md">Download (save as AGENTS.md)</a>',
            self.html,
        )
        # The copy button and the hero preview show the same text the download link serves, and
        # the card names that file's one hash.
        root = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        # The preview is HTML-escaped, so the line is compared in the form the page carries.
        self.assertIn(html.escape(root.split("\n")[5], quote=True), self.html)
        digest = hashlib.sha256(root.encode("utf-8")).hexdigest()
        self.assertIn('title="sha256 ' + digest + '"', self.html)

    def test_the_hero_card_states_the_file_on_one_line_and_the_caveat_on_another(self):
        # The numbers are the offered file's; the sentence next to them says why they read as
        # they do. The three hashes stay in the title attribute, which the test above checks.
        self.assertRegex(
            self.html,
            r'<p class="filemeta" title="[^"]+">v[\d.]+ \u00b7 MIT \u00b7 \d+ lines '
            r'\u00b7 Rule criteria \d+/\d+ \u00b7 Content criteria \d+/\d+</p>',
        )
        self.assertIn(
            '<p class="filenote">Written to the rule criteria, so meeting them is expected,',
            self.html,
        )
        # The card names the criteria it does not meet, from the data, so it cannot round up.
        import json

        ours = json.loads((DOCS / "data" / "comparison.json").read_text(encoding="utf-8"))["ours"]
        criteria = json.loads((DOCS / "criteria.json").read_text(encoding="utf-8"))
        names = {c["id"]: c["name"] for c in criteria["criteria"]}
        for key, verdict in ours["criteria"].items():
            if not verdict["pass"]:
                self.assertIn(names[key], self.html)

    def test_the_check_panel_carries_the_privacy_line(self):
        self.assertIn("Nothing is sent or stored; the check runs in your browser.", self.html)


class ClaimTest(unittest.TestCase):
    """Every claim on the page carries a command, and every command prints the number the claim
    states. The commands are run here, so a claim cannot drift away from the data."""

    def test_each_claim_command_prints_a_number_the_claim_states(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        data = compare.with_ours(
            compare.read_json(compare.COMPARISON_JSON),
            compare.load_criteria(),
            compare.load_criteria_content(),
        )
        items = compare.claims(data, compare.load_criteria(), compare.load_experiment())
        self.assertGreaterEqual(len(items), 5)
        for text, command in items:
            result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                    cwd=str(REPO_ROOT))
            self.assertEqual(result.returncode, 0, command + result.stderr)
            printed = result.stdout.strip()
            self.assertIn(printed, re.findall(r"\d+", text), "%r not stated in %r" % (printed, text))


@unittest.skipIf(NODE is None, "node is not installed")
class ExperimentRendererTest(unittest.TestCase):
    """The experiment section is built in JavaScript from experiment.json. It is rendered here
    in Node against the committed run file, so the shape is checked without a browser."""

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

    def test_the_committed_run_file_renders_tables_and_a_chart(self):
        html = self.render("require(%s)" % json.dumps(str(EXPERIMENT)))
        for task in ("task1", "task2", "task3"):
            self.assertIn("<h3>%s</h3>" % task, html)
        self.assertIn("<svg class=\"chart\"", html)
        self.assertIn("per cell", html)
        self.assertIn("↑ better", html)
        self.assertIn("Cost, turns and duration", html)

    def test_the_content_matrix_agrees_with_the_committed_data(self):
        data = json.loads((DOCS / "data" / "comparison.json").read_text(encoding="utf-8"))
        content = json.loads((DOCS / "criteria-content.json").read_text(encoding="utf-8"))
        script = (
            "const lab=require(%s);"
            "const d=require(%s);const c=require(%s);"
            "process.stdout.write(lab.contentMatrix(d.files, c));"
            % (
                json.dumps(str(COMPARE_JS)),
                json.dumps(str(DOCS / "data" / "comparison.json")),
                json.dumps(str(DOCS / "criteria-content.json")),
            )
        )
        result = subprocess.run([NODE, "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        html = result.stdout
        for record in data["files"]:
            self.assertIn("%d/%d" % (record["met_content"], record["of_content"]), html)
        for criterion in content["criteria"]:
            self.assertIn(criterion["name"], html)
        self.assertIn("of %d files" % len(data["files"]), html)

    def test_an_empty_file_renders_nothing_so_the_planned_sentence_stands(self):
        self.assertEqual(self.render('{"by_task":{},"generated_utc":"x"}'), "")

    def test_the_intervals_come_from_the_file(self):
        data = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
        entry = data["by_task"]["task1"]["comparison"]["tests_written"]["conditions"]["ours"]
        html = self.render("require(%s)" % json.dumps(str(EXPERIMENT)))
        self.assertIn("[%.2f, %.2f]" % (entry["lo"], entry["hi"]), html)

    def test_every_cell_is_ten_runs(self):
        data = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
        for task, entry in data["by_task"].items():
            for condition, cell in entry["cells"].items():
                self.assertEqual(cell["n"], 10, "%s %s" % (task, condition))
                self.assertEqual(cell["delivered_runs"], 10, "%s %s" % (task, condition))


if __name__ == "__main__":
    unittest.main()
