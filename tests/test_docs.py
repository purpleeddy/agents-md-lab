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
EXPERIMENT_RUNS = REPO_ROOT / "docs" / "data" / "experiment-runs.json"
ROUND2 = REPO_ROOT / "docs" / "data" / "experiment-round2.json"
ROUND2_RUNS = REPO_ROOT / "docs" / "data" / "experiment-round2-runs.json"
ROUND3_RUNS = REPO_ROOT / "docs" / "data" / "experiment-round3-runs.json"
ROUND4_RUNS = REPO_ROOT / "docs" / "data" / "experiment-round4-runs.json"
FINDINGS = DOCS / "findings.md"
EXPERIMENTS_README = REPO_ROOT / "experiments" / "README.md"
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

# The closing parenthesis of a Markdown link is not part of the URL. Swallowing it left
# "](" open, and a later link on the page then read as the target of this one.
URL = re.compile(r"https?://[^\s)]+")
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
        sets = json.loads((DOCS / "criteria.json").read_text(encoding="utf-8"))["sets"]
        for name, criteria in sets.items():
            for criterion in criteria["criteria"]:
                for key in criterion["sources"]:
                    self.assertIn(
                        key, defined, "%s criterion %s cites %s" % (name, criterion["id"], key)
                    )

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
    LINK = re.compile(
        r'(?:href="|\]\()(?:\.\./)?(?:docs/)?([a-z]+)\.(?:html|md)#([^"\)]+)'
    )
    # A relative link target, fragment stripped: the thing that has to be a file on disk.
    RELATIVE = re.compile(r'(?:href="|\]\()(?!https?:|mailto:|#)([^"\)#]+)')

    def slug(self, title):
        text = re.sub(r"<[^>]+>", "", title).replace("`", "").replace("*", "")
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        return re.sub(r"\s+", "-", text.strip()).lower()

    def anchors(self, page):
        text = page.read_text(encoding="utf-8")
        found = {self.slug(title) for title in self.HEADING.findall(text)}
        return found | set(self.EXPLICIT.findall(text))

    def sources(self):
        """Every page that links into this site, including the pre-registration record: a link
        that rots there is as broken as one on a published page, and until this test read the
        file, nothing checked it."""
        return [INDEX, README, EXPERIMENTS_README] + sorted(DOCS.glob("*.md"))

    def name(self, source):
        return str(source.relative_to(REPO_ROOT))

    def test_every_cross_page_fragment_exists(self):
        pages = {path.stem: path for path in DOCS.glob("*.md")}
        anchors = {name: self.anchors(path) for name, path in pages.items()}
        for source in self.sources():
            for page, fragment in self.LINK.findall(source.read_text(encoding="utf-8")):
                if page not in anchors:
                    continue
                self.assertIn(fragment, anchors[page], "%s links to %s#%s"
                              % (self.name(source), page, fragment))

    def test_every_relative_link_lands_on_a_file_that_exists(self):
        """A relative link is resolved against the directory of the page that carries it.
        `experiments/README.md` linked `references.md`, which resolves inside `experiments/`
        where no such file is. Markdown sources only: index.html is checked by the tests on
        the page itself."""
        for source in markdown_pages() + [EXPERIMENTS_README]:
            # Fences and code spans only: strip_markdown_code also blanks URLs, and a blanked
            # URL leaves an empty target behind that reads as a relative path.
            text = source.read_text(encoding="utf-8")
            text = CODE_SPAN.sub(" ", FENCE.sub(" ", text))
            for target in self.RELATIVE.findall(text):
                target = target.strip()
                if not target or target.startswith(("{{", "%", "$")):
                    continue
                resolved = (source.parent / target).resolve()
                # Jekyll publishes each Markdown page as .html, so a .html target counts when
                # its Markdown source is on disk.
                if not resolved.exists() and resolved.suffix == ".html":
                    resolved = resolved.with_suffix(".md")
                self.assertTrue(
                    resolved.exists(),
                    "%s links to %s, which is not a file" % (self.name(source), target),
                )


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

    def test_every_markdown_block_is_separated_from_its_markers_by_a_blank_line(self):
        """Kramdown reads a comment as the start of an HTML block and swallows the lines that
        follow it, so a table written straight under a `:start` marker reaches the browser as
        literal pipes. Each marker in a Markdown page needs a blank line beside it."""
        for path in (DOCS / "methodology.md", DOCS / "findings.md", README):
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").split("\n")
            for number, line in enumerate(lines):
                start = re.fullmatch(r"<!-- ([a-z0-9-]+):start -->", line)
                end = re.fullmatch(r"<!-- ([a-z0-9-]+):end -->", line)
                if start:
                    self.assertEqual(
                        lines[number + 1],
                        "",
                        "%s: no blank line after %s:start on line %d"
                        % (path.name, start.group(1), number + 1),
                    )
                if end:
                    self.assertEqual(
                        lines[number - 1],
                        "",
                        "%s: no blank line before %s:end on line %d"
                        % (path.name, end.group(1), number + 1),
                    )


class KnownIssuesTest(unittest.TestCase):
    """The independent review is recorded as a table with a response per row. Two reviewers gave
    24 findings each; the table merges them, and every finding has to appear in it."""

    def section(self):
        text = (DOCS / "rationale.md").read_text(encoding="utf-8")
        self.assertIn("## Known issues the review found in the file", text)
        after = text.split("## Known issues the review found in the file")[1]
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
        allowed = ("fixed in v1.0.1", "applied in v1.1.0", "applied in v1.2.0",
                   "enforceable by", "v1.1.0 candidate", "disagree because",
                   "covered by", "the line is cut in v1.1.0", "the rule stands")
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

    def test_no_phrase_of_the_unlicensed_corpus_file_is_published(self):
        # The one corpus file with no license is recorded by line number only. The check derives
        # its phrases from the cache at run time rather than storing them, so the guard against
        # reproducing that text does not reproduce it either.
        path = REPO_ROOT / "data" / "cache" / "corpus" / "karpathy-multica-694a2d72.md"
        if not path.exists():
            self.skipTest(
                "the corpus cache is not on disk: %s (run scripts/compare.py --refresh)" % path
            )
        cached = path.read_text(encoding="utf-8").split("\n")
        phrases = [
            line.strip()
            for number, line in enumerate(cached, start=1)
            if number % 5 == 0 and len(line.strip()) > 40
        ][:6]
        self.assertEqual(len(phrases), 6, "the cached file no longer yields six phrases")
        suffixes = {".md", ".html", ".json", ".js", ".css", ".py", ".toml"}
        published = [
            path
            for path in REPO_ROOT.rglob("*")
            if path.is_file()
            and path.suffix in suffixes
            and ".git" not in path.parts
            and "cache" not in path.parts
        ]
        hits = [
            str(path.relative_to(REPO_ROOT))
            for path in published
            for phrase in phrases
            if phrase in path.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual(hits, [])

    def test_the_muted_ink_passes_aa_on_every_light_surface(self):
        # --muted carries the captions, the evidence rows and the hero note. The tightest pairing
        # is on --surface-2, where the tinted rows sit; #71717A reached only 4.40 there.
        css = SITE_CSS.read_text(encoding="utf-8")
        root = css.split(":root {", 1)[1].split("}", 1)[0]
        token = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})", root))

        def luminance(value):
            channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            channels = [
                c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
            ]
            return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

        muted = luminance(token["--muted"])
        for name in ("--ground", "--surface", "--surface-2"):
            back = luminance(token[name])
            ratio = (max(muted, back) + 0.05) / (min(muted, back) + 0.05)
            self.assertGreaterEqual(round(ratio, 2), 4.5, name)

    def test_the_unmet_pill_is_filled_and_unbordered(self):
        # Both verdicts read as filled pills; the outline made the unmet one louder than the met
        # one, which is a ranking the page does not make.
        css = SITE_CSS.read_text(encoding="utf-8")
        rule = [line for line in css.split("\n") if line.startswith(".v.unmet .pill {")]
        self.assertEqual(len(rule), 1, css)
        self.assertNotIn("border-color", rule[0])

    def test_every_token_the_components_use_is_defined_in_the_light_root(self):
        # A component reading a token no theme defines renders with no colour at all, and the
        # light :root block is the one every theme starts from.
        css = SITE_CSS.read_text(encoding="utf-8")
        root = css.split(":root {", 1)[1].split("}", 1)[0]
        defined = set(re.findall(r"(--[\w-]+)\s*:", root))
        used = set(re.findall(r"var\((--[\w-]+)\)", css))
        self.assertEqual(sorted(used - defined), [])
        self.assertEqual(sorted(defined - used), [])

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
        criteria = json.loads((DOCS / "criteria.json").read_text(encoding="utf-8"))["sets"]["rules"]
        names = {c["id"]: c["name"] for c in criteria["criteria"]}
        for key, verdict in ours["criteria"].items():
            if not verdict["pass"]:
                self.assertIn(names[key], self.html)

    def test_the_check_panel_carries_the_privacy_line(self):
        self.assertIn("Nothing is sent or stored; the check runs in your browser.", self.html)

    def test_the_criteria_come_from_the_fetch_and_the_fallback_says_so(self):
        self.assertNotIn("criteria-data", self.html)
        self.assertNotIn("criteria-data", COMPARE_JS.read_text(encoding="utf-8"))
        self.assertIn("needs JavaScript and a network connection", self.html)
        # The copy button's text is inert markup, not a fetch, so it stays.
        self.assertIn('<template id="agents-md-text">', self.html)


class ClaimTest(unittest.TestCase):
    """Every claim on the front page carries a command, and every command prints the number the
    claim states. The commands are run here, so a claim cannot drift away from the data."""

    def test_each_claim_command_prints_a_number_the_claim_states(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        data = compare.with_ours(
            compare.read_json(compare.COMPARISON_JSON),
            compare.load_criteria(),
            compare.load_criteria_content(),
        )
        items = compare.claims(
            data,
            compare.load_criteria(),
            compare.load_experiment(),
            compare.load_round3(),
            compare.load_round4(),
        )
        self.assertGreaterEqual(len(items), 5)
        # The claim that reads the two round files is the one a skeptic would run first, so the
        # list must carry it and its command must open both.
        rounds = [c for _text, c in items if "experiment-round3.json" in c]
        self.assertEqual(len(rounds), 1)
        self.assertIn("experiment-round4.json", rounds[0])
        for text, command in items:
            result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                    cwd=str(REPO_ROOT))
            self.assertEqual(result.returncode, 0, command + result.stderr)
            printed = result.stdout.strip()
            self.assertIn(printed, re.findall(r"\d+", text), "%r not stated in %r" % (printed, text))


class ClaimsLiveOnOnePageTest(unittest.TestCase):
    """The list of checkable claims is on the front page and nowhere else. A skeptic arriving at
    the site meets it before any table; the findings page, which is read after, links to it
    instead of carrying a second copy that could drift away from the first."""

    def compare(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        return compare

    def test_the_front_page_carries_the_block_and_check_covers_it(self):
        """--check compares the whole of index.html against what the data renders, so the
        equality asserted here is the one it enforces. Stated in a test as well, because the
        renderer is what a later edit would drop."""
        compare = self.compare()
        data = compare.with_ours(
            compare.read_json(compare.COMPARISON_JSON),
            compare.load_criteria(),
            compare.load_criteria_content(),
        )
        rendered = compare.render_claims_html(
            data,
            compare.load_criteria(),
            compare.load_experiment(),
            compare.load_round3(),
            compare.load_round4(),
        )
        page = INDEX.read_text(encoding="utf-8")
        block = page.split("<!-- claims:start -->", 1)[1].split("<!-- claims:end -->", 1)[0]
        self.assertEqual(block.strip("\n"), rendered)
        # replace_block raises when a marker is missing, so --check fails rather than passing
        # quietly on a page the block was cut from.
        with self.assertRaises(RuntimeError):
            compare.replace_block("no markers here", "claims", "x", compare.INDEX_HTML)

    def test_the_findings_page_links_to_it_instead_of_repeating_it(self):
        page = FINDINGS.read_text(encoding="utf-8")
        self.assertNotIn("claims:start", page)
        self.assertNotIn("## Claims you can check", page)
        self.assertIn("[claims on the front page](index.html#how)", page)
        self.assertIn('<section id="how">', INDEX.read_text(encoding="utf-8"))

    def test_no_markdown_renderer_for_the_block_is_left_behind(self):
        self.assertFalse(hasattr(self.compare(), "render_claims_md"))


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
        content = json.loads((DOCS / "criteria.json").read_text(encoding="utf-8"))["sets"]["content"]
        script = (
            "const lab=require(%s);"
            "const d=require(%s);const c=require(%s).sets.content;"
            "process.stdout.write(lab.contentMatrix(d.files, c));"
            % (
                json.dumps(str(COMPARE_JS)),
                json.dumps(str(DOCS / "data" / "comparison.json")),
                json.dumps(str(DOCS / "criteria.json")),
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

    def test_the_per_run_records_are_a_separate_file_the_page_never_fetches(self):
        summary = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
        self.assertNotIn("runs", summary)
        rows = json.loads(EXPERIMENT_RUNS.read_text(encoding="utf-8"))["runs"]
        self.assertEqual(len(rows), 90)
        self.assertNotIn("experiment-runs.json", COMPARE_JS.read_text(encoding="utf-8"))
        self.assertNotIn("experiment-runs.json", INDEX.read_text(encoding="utf-8"))

    def test_the_round_two_file_renders_with_the_same_renderer(self):
        html = self.render("require(%s)" % json.dumps(str(ROUND2)))
        for task in ("task1", "task2", "task3"):
            self.assertIn("<h3>%s</h3>" % task, html)
        self.assertIn("Cost, turns and duration", html)
        self.assertIn("\u2191 better", html)

    def test_every_cell_is_ten_runs(self):
        data = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
        for task, entry in data["by_task"].items():
            for condition, cell in entry["cells"].items():
                self.assertEqual(cell["n"], 10, "%s %s" % (task, condition))
                self.assertEqual(cell["delivered_runs"], 10, "%s %s" % (task, condition))


# The sha256 of the root `AGENTS.md` as round 2 measured it, v1.2.0. It is a recorded constant
# here for the same reason it is one in compare.RECORDED_TEXTS: the file under test that round is
# not the file the working tree holds now.
ROUND2_SHA256 = "e1677f04d7abe4a61031fd7e3a66be4df8e9e072b1a0313f22f4512254b2b8dc"


class RoundTwoTest(unittest.TestCase):
    """The round-2 block on the findings page is rendered from docs/data/experiment-round2.json
    against the main run's `ours` cells. The rule it applies was fixed before the runs, so the
    tests here check that the block states what the two summaries actually hold, and that the
    same renderer prints a failure when the data fails."""

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        self.compare = compare
        self.exp = compare.load_experiment()
        self.round2 = compare.load_round2()
        page = FINDINGS.read_text(encoding="utf-8")
        self.block = page.split("<!-- round2:start -->", 1)[1].split("<!-- round2:end -->", 1)[0]

    def test_the_gated_metrics_are_the_sixteen_the_rule_names(self):
        """The list is pre-registered text: it may not be derived from the new data, and it may
        not quietly lose a metric."""
        pre_registration = PRE_REGISTRATION.read_text(encoding="utf-8")
        clause = pre_registration.split("(a) Advantage", 1)[1].split("(b) Disadvantage", 1)[0]
        named = re.findall(r"`(task\d)\.([a-z_]+)`\s+\d+/10", clause)
        self.assertEqual(sorted(named), sorted(self.compare.ROUND2_GATED))
        self.assertEqual(len(self.compare.ROUND2_GATED), 16)

    def test_only_the_gated_metrics_that_moved_carry_a_row(self):
        """The unchanged rows are the same twelve or so in every round, so the block prints the
        ones that moved and a line for the rest. A row that moved may not go missing, and a row
        that did not move may not come back."""
        for task, metric in self.compare.ROUND2_GATED:
            before = self.compare.round2_metric(self.exp, task, metric)
            after = self.compare.round2_metric(self.round2, task, metric)
            change = after["k"] - before["k"]
            row = "| %s | %s | %d/%d | %d/%d | %+d |" % (
                task, metric.replace("_", " "), before["k"], before["n"],
                after["k"], after["n"], change,
            )
            if change:
                self.assertIn(row, self.block)
            else:
                self.assertNotIn(row, self.block)

    def test_the_line_under_the_table_counts_the_metrics_that_did_not_move(self):
        moved = len(self.compare.ROUND2_GATED) - self.count_unchanged()
        self.assertIn(
            "%s of the sixteen gated advantage metrics moved and %s did not"
            % (self.compare.NUMBER_WORDS[moved].capitalize(),
                self.compare.NUMBER_WORDS[self.count_unchanged()]),
            " ".join(self.block.split()),
        )
        self.assertIn(
            "Results section](%s" % self.compare.ROUND2_RESULTS_URL,
            " ".join(self.block.split()),
        )

    def count_unchanged(self):
        return len([
            1 for task, metric in self.compare.ROUND2_GATED
            if self.compare.round2_metric(self.round2, task, metric)["k"]
            == self.compare.round2_metric(self.exp, task, metric)["k"]
        ])

    def test_the_verdict_states_the_outcome_the_data_gives(self):
        drops = [
            self.compare.round2_metric(self.exp, task, metric)["k"]
            - self.compare.round2_metric(self.round2, task, metric)["k"]
            for task, metric in self.compare.ROUND2_GATED
        ]
        harms = [
            self.compare.round2_metric(self.round2, task, metric)["k"]
            for task, metric in self.compare.ROUND2_DISADVANTAGE
        ]
        over = [
            entry for entry in self.compare.round2_cost(self.exp, self.round2)
            if entry[2] > entry[4]
        ]
        held = (
            max(drops) < 3
            and len([drop for drop in drops if drop >= 2]) < 2
            and max(harms) < 2
            and not over
        )
        for clause, ok in (("(a)", max(drops) < 3 and len([d for d in drops if d >= 2]) < 2),
                           ("(b)", max(harms) < 2), ("(c)", not over)):
            self.assertIn("Clause %s %s" % (clause, "holds" if ok else "fails"), self.block)
        self.assertEqual("All three clauses hold" in self.block, held)


    def test_the_verdict_names_the_deciding_numbers_and_stops(self):
        """The page states the three clauses in plain words once, above the rounds, and the
        metrics that rose are the table the verdict sits under. So the verdict carries the ratio
        that decided clause (c) for every task and does not reprint the gate sizes, the cost
        limit or the rows above it."""
        flat = " ".join(self.block.split())
        for task, _before, _after, ratio, _limit in self.compare.round2_cost(self.exp, self.round2):
            self.assertIn("%.2f\u00d7 on %s" % (ratio, task), flat)
        self.assertNotIn("against a limit of", flat)
        self.assertNotIn("`ours` median", flat)

    def test_the_verdict_does_not_reprint_the_rows_above_it(self):
        """Clause (a) held on this round, and the four metrics that rose are the four rows of
        the table. The verdict says none dropped and leaves the rows to the table."""
        flat = " ".join(self.block.split())
        self.assertIn("Clause (a) holds: no gated advantage metric dropped.", flat)
        for task, metric in self.compare.ROUND2_GATED:
            before = self.compare.round2_metric(self.exp, task, metric)["k"]
            after = self.compare.round2_metric(self.round2, task, metric)["k"]
            if after > before:
                self.assertNotIn(
                    "%s %s +%d" % (task, metric.replace("_", " "), after - before),
                    flat.split("Clause (a)", 1)[1],
                )

    def test_the_renderer_prints_a_failure_when_a_gated_metric_drops(self):
        """The block is not a fixed sentence: doctoring one metric down by 3 flips the verdict."""
        doctored = json.loads(json.dumps(self.round2))
        cell = doctored["by_task"]["task1"]["comparison"]["tests_written"]["conditions"]["ours"]
        cell["k"] = self.compare.round2_metric(self.exp, "task1", "tests_written")["k"] - 3
        text = self.compare.render_round2_md(self.exp, doctored)
        self.assertIn("Clause (a) fails", text)
        self.assertIn("The round fails", text)
        self.assertNotIn("All three clauses hold", text)

    def test_the_renderer_prints_a_failure_when_the_cost_limit_is_passed(self):
        doctored = json.loads(json.dumps(self.round2))
        before = self.exp["by_task"]["task3"]["cells"]["ours"]["medians"]["total_cost_usd"]
        doctored["by_task"]["task3"]["cells"]["ours"]["medians"]["total_cost_usd"] = before * 1.2
        text = self.compare.render_round2_md(self.exp, doctored)
        self.assertIn("Clause (c) fails", text)
        self.assertIn("The round fails", text)

    def test_the_round_two_summary_is_thirty_ours_runs_and_the_reused_cells(self):
        for task, entry in self.round2["by_task"].items():
            for condition, cell in entry["cells"].items():
                self.assertEqual(cell["n"], 10, "%s %s" % (task, condition))
                self.assertEqual(cell["delivered_runs"], 10, "%s %s" % (task, condition))
        rows = json.loads(ROUND2_RUNS.read_text(encoding="utf-8"))["runs"]
        ours = [row for row in rows if row["condition"] == "ours"]
        self.assertEqual(len(ours), 30)
        # Pinned to the recorded v1.2.0 hash rather than read from the root file: the thirty rows
        # are a record of the text round 2 measured, and they stay pinned whatever the shipped
        # file becomes. It happens to be that text again, after round 3 did not adopt v1.3.0.
        self.assertEqual({row["meta"]["condition_sha256"] for row in ours}, {ROUND2_SHA256})

    def test_the_page_labels_the_round_two_section_with_the_version_round_two_measured(self):
        source = COMPARE_JS.read_text(encoding="utf-8")
        self.assertIn(
            "Round 2, <code>ours</code> = v%s" % self.compare.ROUND2_VERSION, source
        )

    def test_the_page_reads_the_summary_and_never_the_per_run_file(self):
        source = COMPARE_JS.read_text(encoding="utf-8")
        self.assertIn("data/experiment-round2.json", source)
        self.assertNotIn("experiment-round2-runs.json", source)
        self.assertNotIn("experiment-round2-runs.json", INDEX.read_text(encoding="utf-8"))


# The sha256 of the root `AGENTS.md` as round 3 measured it, v1.3.0. Round 3 did not adopt it, so
# it is a recorded constant here and not the file the working tree holds.
ROUND3_SHA256 = "5714cfaa9540bb4039c7b358087d508fa3126dc4c315afcbd54138f0dc0560bd"


class RoundThreeTest(unittest.TestCase):
    """The round-3 block on the findings page is rendered from docs/data/experiment-round3.json
    against the round-2 `ours` cells, by the same renderer as round 2. The rule it applies was
    fixed before the runs and it returns a failure on this data, so the tests here check that the
    block states the failure the two summaries hold, and that the same renderer still prints the
    holding branch when the data holds."""

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        self.compare = compare
        self.round2 = compare.load_round2()
        self.round3 = compare.load_round3()
        page = FINDINGS.read_text(encoding="utf-8")
        self.block = page.split("<!-- round3:start -->", 1)[1].split("<!-- round3:end -->", 1)[0]

    def clause(self):
        """Clause (a) of the round-3 rule, not round 2's: the pre-registration carries both."""
        section = PRE_REGISTRATION.read_text(encoding="utf-8").split(
            "\n## Main run, round 3\n", 1
        )[1]
        return section.split("(a) Advantage", 1)[1].split("(b) Disadvantage", 1)[0]

    def test_the_gated_metrics_are_the_sixteen_the_rule_names(self):
        named = re.findall(r"`(task\d)\.([a-z_]+)`\s+\d+/10", self.clause())
        self.assertEqual(sorted(named), sorted(self.compare.ROUND3_GATED))
        self.assertEqual(len(self.compare.ROUND3_GATED), 16)

    def test_only_the_gated_metrics_that_moved_carry_a_row(self):
        """The unchanged rows are the same twelve or so in every round, so the block prints the
        ones that moved and a line for the rest. A row that moved may not go missing, and a row
        that did not move may not come back."""
        for task, metric in self.compare.ROUND3_GATED:
            before = self.compare.round2_metric(self.round2, task, metric)
            after = self.compare.round2_metric(self.round3, task, metric)
            change = after["k"] - before["k"]
            row = "| %s | %s | %d/%d | %d/%d | %+d |" % (
                task, metric.replace("_", " "), before["k"], before["n"],
                after["k"], after["n"], change,
            )
            if change:
                self.assertIn(row, self.block)
            else:
                self.assertNotIn(row, self.block)

    def test_the_line_under_the_table_counts_the_metrics_that_did_not_move(self):
        moved = len(self.compare.ROUND3_GATED) - self.count_unchanged()
        self.assertIn(
            "%s of the sixteen gated advantage metrics moved and %s did not"
            % (self.compare.NUMBER_WORDS[moved].capitalize(),
                self.compare.NUMBER_WORDS[self.count_unchanged()]),
            " ".join(self.block.split()),
        )
        self.assertIn(
            "Results section](%s" % self.compare.ROUND3_RESULTS_URL,
            " ".join(self.block.split()),
        )

    def count_unchanged(self):
        return len([
            1 for task, metric in self.compare.ROUND3_GATED
            if self.compare.round2_metric(self.round3, task, metric)["k"]
            == self.compare.round2_metric(self.round2, task, metric)["k"]
        ])

    def test_the_verdict_states_the_outcome_the_data_gives(self):
        drops = [
            self.compare.round2_metric(self.round2, task, metric)["k"]
            - self.compare.round2_metric(self.round3, task, metric)["k"]
            for task, metric in self.compare.ROUND3_GATED
        ]
        harms = [
            self.compare.round2_metric(self.round3, task, metric)["k"]
            for task, metric in self.compare.ROUND3_DISADVANTAGE
        ]
        over = [
            entry for entry in self.compare.round3_cost(self.round2, self.round3)
            if entry[2] > entry[4]
        ]
        clause_a = max(drops) < 3 and len([drop for drop in drops if drop >= 2]) < 2
        for clause, ok in (("(a)", clause_a), ("(b)", max(harms) < 2), ("(c)", not over)):
            self.assertIn("Clause %s %s" % (clause, "holds" if ok else "fails"), self.block)
        held = clause_a and max(harms) < 2 and not over
        self.assertEqual("All three clauses hold" in self.block, held)
        # This is the round that failed, and the page has to say so from the data. textwrap.fill
        # can break either phrase across lines, so the whitespace is normalised.
        self.assertFalse(held)
        self.assertIn("the delivery revision is not adopted", " ".join(self.block.split()))


    def test_the_verdict_names_the_deciding_numbers_and_stops(self):
        """The page states the three clauses in plain words once, above the rounds, and the
        metrics that rose are the table the verdict sits under. So the verdict carries the ratio
        that decided clause (c) for every task and does not reprint the gate sizes, the cost
        limit or the rows above it."""
        flat = " ".join(self.block.split())
        for task, _before, _after, ratio, _limit in self.compare.round3_cost(self.round2, self.round3):
            self.assertIn("%.2f\u00d7 on %s" % (ratio, task), flat)
        self.assertNotIn("against a limit of", flat)
        self.assertNotIn("`ours` median", flat)

    def test_the_renderer_prints_the_holding_branch_when_the_data_holds(self):
        """The failure is not a fixed sentence either: restoring the one metric and the one
        median that fail turns the same renderer to the adopting branch."""
        doctored = json.loads(json.dumps(self.round3))
        cell = doctored["by_task"]["task2"]["comparison"]["regression_test_added"]["conditions"]["ours"]
        cell["k"] = self.compare.round2_metric(self.round2, "task2", "regression_test_added")["k"]
        base = self.round2["by_task"]["task1"]["cells"]["ours"]["medians"]["total_cost_usd"]
        doctored["by_task"]["task1"]["cells"]["ours"]["medians"]["total_cost_usd"] = base
        text = self.compare.render_round3_md(self.round2, doctored)
        self.assertIn("Clause (a) holds", text)
        self.assertIn("Clause (c) holds", text)
        self.assertIn("All three clauses hold", text)
        self.assertNotIn("is not adopted", text)

    def test_the_renderer_prints_a_failure_when_a_disadvantage_boolean_rises(self):
        doctored = json.loads(json.dumps(self.round3))
        doctored["by_task"]["task3"]["comparison"]["overprocess"]["conditions"]["ours"]["k"] = 4
        text = self.compare.render_round3_md(self.round2, doctored)
        self.assertIn("Clause (b) fails", text)
        # textwrap.fill can break the phrase across lines, so the whitespace is normalised.
        self.assertIn("task3 overprocess is 4/10", " ".join(text.split()))

    def test_the_round_three_summary_is_thirty_ours_runs_and_the_reused_cells(self):
        for task, entry in self.round3["by_task"].items():
            for condition, cell in entry["cells"].items():
                self.assertEqual(cell["n"], 10, "%s %s" % (task, condition))
                self.assertEqual(cell["delivered_runs"], 10, "%s %s" % (task, condition))
        rows = json.loads(ROUND3_RUNS.read_text(encoding="utf-8"))["runs"]
        ours = [row for row in rows if row["condition"] == "ours"]
        self.assertEqual(len(ours), 30)
        self.assertEqual({row["meta"]["condition_sha256"] for row in ours}, {ROUND3_SHA256})
        self.assertEqual({row["meta"]["cli_version_reported"] for row in ours}, {"2.1.261"})
        # The reused cells are the main run's rows, as the pre-registration says and as the
        # Results section records: they were rebuilt from the committed main-run file.
        reused = [row for row in rows if row["condition"] != "ours"]
        main_run = [
            row for row in json.loads(EXPERIMENT_RUNS.read_text(encoding="utf-8"))["runs"]
            if row["condition"] != "ours"
        ]
        self.assertEqual(reused, main_run)

    def test_the_page_reads_the_summary_and_never_the_per_run_file(self):
        source = COMPARE_JS.read_text(encoding="utf-8")
        self.assertNotIn("experiment-round3-runs.json", source)
        self.assertNotIn("experiment-round3-runs.json", INDEX.read_text(encoding="utf-8"))


# The sha256 of the root `AGENTS.md` as round 4 measured it: v1.2.0, the shipped text. Round 4 is
# the control, so this is the same hash the shipped file carries, pinned here as a record of what
# the thirty rows measured rather than read from the working tree.
ROUND4_SHA256 = "e1677f04d7abe4a61031fd7e3a66be4df8e9e072b1a0313f22f4512254b2b8dc"


class RoundFourTest(unittest.TestCase):
    """The round-4 block on the findings page is rendered from docs/data/experiment-round4.json
    against the same round-2 `ours` cells round 3 was measured against, by the same renderer. Round
    4 re-ran the shipped text, so the block reports the arithmetic for information: the tests here
    check that it states what the two summaries hold and that it adopts nothing either way.

    There is no round-4 clause list in the pre-registration to read the metric names from, because
    the round adopts nothing and no gate was written for it; the constants reuse round 3's, which
    a round-3 test already pins to the pre-registered text."""

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        self.compare = compare
        self.round2 = compare.load_round2()
        self.round4 = compare.load_round4()
        page = FINDINGS.read_text(encoding="utf-8")
        self.block = page.split("<!-- round4:start -->", 1)[1].split("<!-- round4:end -->", 1)[0]

    def test_the_gated_metrics_are_the_sixteen_round_three_named(self):
        self.assertEqual(self.compare.ROUND4_GATED, self.compare.ROUND3_GATED)
        self.assertEqual(self.compare.ROUND4_DISADVANTAGE, self.compare.ROUND3_DISADVANTAGE)
        self.assertEqual(len(self.compare.ROUND4_GATED), 16)

    def test_only_the_gated_metrics_that_moved_carry_a_row(self):
        """The unchanged rows are the same twelve or so in every round, so the block prints the
        ones that moved and a line for the rest. A row that moved may not go missing, and a row
        that did not move may not come back."""
        for task, metric in self.compare.ROUND4_GATED:
            before = self.compare.round2_metric(self.round2, task, metric)
            after = self.compare.round2_metric(self.round4, task, metric)
            change = after["k"] - before["k"]
            row = "| %s | %s | %d/%d | %d/%d | %+d |" % (
                task, metric.replace("_", " "), before["k"], before["n"],
                after["k"], after["n"], change,
            )
            if change:
                self.assertIn(row, self.block)
            else:
                self.assertNotIn(row, self.block)

    def test_the_line_under_the_table_counts_the_metrics_that_did_not_move(self):
        moved = len(self.compare.ROUND4_GATED) - self.count_unchanged()
        self.assertIn(
            "%s of the sixteen gated advantage metrics moved and %s did not"
            % (self.compare.NUMBER_WORDS[moved].capitalize(),
                self.compare.NUMBER_WORDS[self.count_unchanged()]),
            " ".join(self.block.split()),
        )
        self.assertIn(
            "Results section](%s" % self.compare.ROUND4_RESULTS_URL,
            " ".join(self.block.split()),
        )

    def count_unchanged(self):
        return len([
            1 for task, metric in self.compare.ROUND4_GATED
            if self.compare.round2_metric(self.round4, task, metric)["k"]
            == self.compare.round2_metric(self.round2, task, metric)["k"]
        ])

    def test_the_two_columns_name_the_round_and_not_only_the_version(self):
        """Both columns carry v1.2.0, so the round is what tells them apart."""
        self.assertEqual(self.compare.ROUND4_VERSION, self.compare.ROUND2_VERSION)
        self.assertIn("v%s, round 2 `ours` k/n" % self.compare.ROUND2_VERSION, self.block)
        self.assertIn("v%s, round 4 `ours` k/n" % self.compare.ROUND4_VERSION, self.block)

    def test_the_verdict_states_the_outcome_the_data_gives(self):
        drops = [
            self.compare.round2_metric(self.round2, task, metric)["k"]
            - self.compare.round2_metric(self.round4, task, metric)["k"]
            for task, metric in self.compare.ROUND4_GATED
        ]
        harms = [
            self.compare.round2_metric(self.round4, task, metric)["k"]
            for task, metric in self.compare.ROUND4_DISADVANTAGE
        ]
        over = [
            entry for entry in self.compare.round4_cost(self.round2, self.round4)
            if entry[2] > entry[4]
        ]
        clause_a = max(drops) < 3 and len([drop for drop in drops if drop >= 2]) < 2
        for clause, ok in (("(a)", clause_a), ("(b)", max(harms) < 2), ("(c)", not over)):
            self.assertIn("Clause %s %s" % (clause, "holds" if ok else "fails"), self.block)
        # The control re-ran the shipped text, so neither branch of the block adopts a version or
        # names a revert set, which is what the two earlier rounds' blocks close with.
        flat = " ".join(self.block.split())
        self.assertNotIn("under the rule as it was written", flat)
        self.assertNotIn("revert set", flat)
        self.assertIn("reported for information and not as a gate", flat)


    def test_the_verdict_names_the_deciding_numbers_and_stops(self):
        """The page states the three clauses in plain words once, above the rounds, and the
        metrics that rose are the table the verdict sits under. So the verdict carries the ratio
        that decided clause (c) for every task and does not reprint the gate sizes, the cost
        limit or the rows above it."""
        flat = " ".join(self.block.split())
        for task, _before, _after, ratio, _limit in self.compare.round4_cost(self.round2, self.round4):
            self.assertIn("%.2f\u00d7 on %s" % (ratio, task), flat)
        self.assertNotIn("against a limit of", flat)
        self.assertNotIn("`ours` median", flat)

    def test_the_renderer_prints_the_other_branch_when_the_data_holds(self):
        """The information sentence is not fixed either: restoring the one metric that falls by
        five turns the same renderer to the branch that says the text reproduced its own cells."""
        doctored = json.loads(json.dumps(self.round4))
        cell = doctored["by_task"]["task2"]["comparison"]["regression_test_added"]["conditions"]["ours"]
        cell["k"] = self.compare.round2_metric(self.round2, "task2", "regression_test_added")["k"]
        text = self.compare.render_round4_md(self.round2, doctored)
        self.assertIn("Clause (a) holds", text)
        self.assertIn("Every clause holds", text)
        self.assertIn("adopts nothing", text)

    def test_the_round_four_summary_is_thirty_ours_runs_and_the_reused_cells(self):
        for task, entry in self.round4["by_task"].items():
            for condition, cell in entry["cells"].items():
                self.assertEqual(cell["n"], 10, "%s %s" % (task, condition))
                self.assertEqual(cell["delivered_runs"], 10, "%s %s" % (task, condition))
        rows = json.loads(ROUND4_RUNS.read_text(encoding="utf-8"))["runs"]
        ours = [row for row in rows if row["condition"] == "ours"]
        self.assertEqual(len(ours), 30)
        self.assertEqual({row["meta"]["condition_sha256"] for row in ours}, {ROUND4_SHA256})
        self.assertEqual({row["meta"]["cli_version_reported"] for row in ours}, {"2.1.261"})
        # The reused rows are the main run's, rebuilt from the committed main-run file as the
        # Results section records. They differ from it in one field only: `run_dir` carries a
        # `reconstructed/` prefix, which says where the row came from, so the comparison here
        # normalises that field and every other field has to match.
        def without_run_dir(row):
            return {key: value for key, value in row.items() if key != "run_dir"}

        reused = [row for row in rows if row["condition"] != "ours"]
        main_run = [
            row for row in json.loads(EXPERIMENT_RUNS.read_text(encoding="utf-8"))["runs"]
            if row["condition"] != "ours"
        ]
        self.assertEqual([without_run_dir(row) for row in reused],
                         [without_run_dir(row) for row in main_run])
        for row, origin in zip(reused, main_run):
            self.assertEqual(row["run_dir"], "reconstructed/" + origin["run_dir"])

    def test_the_page_reads_the_summary_and_never_the_per_run_file(self):
        source = COMPARE_JS.read_text(encoding="utf-8")
        self.assertNotIn("experiment-round4-runs.json", source)
        self.assertNotIn("experiment-round4-runs.json", INDEX.read_text(encoding="utf-8"))


# Every version name the project publishes carries three parts, so that a reader never has to
# guess whether "v1.1" and "v1.1.0" are the same text. Two names are exempt: the locked region of
# experiments/README.md, which cannot change after the tag, and the git tag `testset-v1.0` where
# the sentence below the Lock line says which commit it names.
VERSION_TOKEN = re.compile(r"\bv\d+(?:\.\d+)*")
# A slug carries the version with its dots removed (#line-audit-v101-to-v110), which is a slug and
# not a version name. Both forms are stripped before the scan: the link fragment, and the explicit
# `<a id="...">` a renamed heading leaves behind so the old link still lands.
ANCHOR = re.compile(r"#[a-z0-9-]+")
ANCHOR_ID = re.compile(r'<a id="[a-z0-9-]+">')
LOCK_HEADING = "\n## Lock\n"
TAG_SENTENCE = (
    "the tag `testset-v1.0.0`, added 2026-09-04, names the same commit as\n"
    "`testset-v1.0`, and the three-part name is the one used on the site. "
)
COMPARE_PY = REPO_ROOT / "scripts" / "compare.py"
PRE_REGISTRATION = REPO_ROOT / "experiments" / "README.md"


class VersionNotationTest(unittest.TestCase):
    def scanned(self):
        pages = [README, REPO_ROOT / "CONTRIBUTING.md", INDEX, COMPARE_PY]
        pages += sorted(DOCS.glob("*.md"))
        texts = {
            str(path.relative_to(REPO_ROOT)): path.read_text(encoding="utf-8") for path in pages
        }
        tail = PRE_REGISTRATION.read_text(encoding="utf-8").split(LOCK_HEADING, 1)[1]
        self.assertIn(TAG_SENTENCE, tail)
        texts["experiments/README.md below the Lock line"] = tail.replace(TAG_SENTENCE, "")
        return texts

    def test_every_version_name_has_three_parts(self):
        for name, text in self.scanned().items():
            for token in VERSION_TOKEN.findall(ANCHOR.sub("", ANCHOR_ID.sub("", text))):
                self.assertEqual(token.count("."), 2, "%s names %s" % (name, token))

    def test_the_front_page_names_the_shipped_version(self):
        """The version name the page states is the badge under the file itself, where someone
        citing or reproducing the text reads it. The prose above names each text by its role and
        sends the reader to the version table, so the badge is the one place a version is
        claimed, and it has to be the version the renderer ships."""
        source = COMPARE_PY.read_text(encoding="utf-8")
        version = re.search(r'^OURS_VERSION = "([^"]+)"', source, re.M).group(1)
        badge = [
            line for line in INDEX.read_text(encoding="utf-8").split("\n")
            if 'class="filemeta"' in line
        ]
        self.assertEqual(len(badge), 1)
        self.assertIn("v%s" % version, badge[0])


METHODOLOGY = DOCS / "methodology.md"
COMPARISON = DOCS / "data" / "comparison.json"


class CoverageSentenceTest(unittest.TestCase):
    """The pages state the shipped file's rule coverage in prose, outside any generated block.
    A prose number that drifts from the data is the defect these tests exist to catch."""

    def ours(self):
        return json.loads(COMPARISON.read_text(encoding="utf-8"))["ours"]

    def test_the_round_four_prose_claims_no_separation_it_cannot_show(self):
        """The paragraph that reads the round-4 cost ranges says the difference is not separable
        at ten runs a cell. A sentence that then calls the revert right on the merits contradicts
        the sentence above it, so the page must not carry one."""
        self.assertNotIn(
            "on the merits as well as by the rule", FINDINGS.read_text(encoding="utf-8")
        )

    def test_the_methodology_states_the_measured_rule_coverage(self):
        ours = self.ours()
        self.assertIn(
            "The recommended file meets %d of the %d rule criteria"
            % (ours["met"], ours["of"]),
            METHODOLOGY.read_text(encoding="utf-8"),
        )

    def test_the_methodology_names_every_unmet_rule_criterion(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import compare  # noqa: E402

        section = METHODOLOGY.read_text(encoding="utf-8").split(
            "## Why the recommended file meets the rule criteria", 1
        )[1].split("\n## ", 1)[0]
        names = compare.unmet_names(self.ours(), compare.load_criteria()).split(", ")
        self.assertEqual(len(names), self.ours()["of"] - self.ours()["met"])
        for name in names:
            self.assertIn("**%s**" % name, section)

    def test_the_readme_counts_the_unmet_rule_criteria(self):
        ours = self.ours()
        self.assertIn(
            "one of three of the ten rule criteria", README.read_text(encoding="utf-8")
        )
        self.assertEqual(ours["of"] - ours["met"], 3)


REVIEW_PHRASE = re.compile(r"independent review|independent reviewer", re.IGNORECASE)


class ReviewReferentTest(unittest.TestCase):
    """"Independent review" carries weight, and on this project it means a model session given
    the file text and no other context. A page that uses the phrase has to say so, so that no
    reader takes it for a human audit."""

    def pages(self):
        paths = sorted(DOCS.glob("*.md")) + [INDEX, README]
        return {str(p.relative_to(REPO_ROOT)): p.read_text(encoding="utf-8") for p in paths}

    def test_every_page_that_claims_a_review_says_what_the_reviewer_was(self):
        for name, text in self.pages().items():
            if REVIEW_PHRASE.search(text):
                self.assertIn("model session", text, name)


class ExploratoryMetricTest(unittest.TestCase):
    """The metric whose fall failed round 3 was pre-registered as exploratory, not confirmatory,
    and it also supplied one of round 2's four rises. A reader who never opens the
    pre-registration has to be able to learn that from the pages that state those results."""

    def test_the_pre_registration_still_calls_the_metric_exploratory(self):
        text = PRE_REGISTRATION.read_text(encoding="utf-8")
        self.assertIn("it is exploratory in the main run, not confirmatory", text)
        self.assertIn("criterion (e) passes without it", text)

    def test_the_findings_page_says_so_where_it_states_the_result(self):
        text = FINDINGS.read_text(encoding="utf-8")
        self.assertIn("exploratory", text)
        # Round 2's rises and rounds 3 and 4's failure each carry it.
        self.assertGreaterEqual(text.count("exploratory"), 3)

    def test_the_front_page_says_so_where_it_states_the_result(self):
        section = INDEX.read_text(encoding="utf-8").split('<section id="experiment">', 1)[1]
        section = section.split("</section>", 1)[0]
        self.assertIn("exploratory", section)


class ClosingSectionTest(unittest.TestCase):
    """The site ends in one place: a closing section on the front page that says what the work
    licenses and what it does not. Every page reaches it from its footer, so the two endings that
    used to sit apart now have one destination."""

    def test_the_front_page_carries_the_section(self):
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn('<section id="what-this-shows">', html)

    def test_every_footer_links_to_it(self):
        self.assertIn('href="#what-this-shows"', INDEX.read_text(encoding="utf-8"))
        self.assertIn(
            'href="index.html#what-this-shows"', LAYOUT.read_text(encoding="utf-8")
        )

    def test_both_endings_point_at_it(self):
        for path in (FINDINGS, DOCS / "methodology.md"):
            self.assertIn(
                "index.html#what-this-shows", path.read_text(encoding="utf-8"), path.name
            )


class GoverningCaveatTest(unittest.TestCase):
    """One sentence governs every number the experiment produced: a re-run of the same text moved
    a measure by five runs in ten. It was only in the README; the front page states it too, above
    the numbers rather than under them."""

    def test_the_front_page_experiment_section_opens_with_the_caveat(self):
        section = INDEX.read_text(encoding="utf-8").split('<section id="experiment">', 1)[1]
        section = section.split("</section>", 1)[0]
        self.assertIn("five runs in ten", section)
        self.assertLess(section.index("five runs in ten"), section.index("Three tasks"))

    def test_the_readme_still_carries_it(self):
        self.assertIn("five runs in ten", README.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- the prose budget
#
# The site files are held to a byte budget above. The prose was never held to anything, and it
# grew to half again the size of the tables it exists to explain. These are today's word counts,
# so nothing changes on the commit that adds them; a later commit edits a number downward, and
# the budget can only ever come down. experiments/README.md carries no budget: it is the
# pre-registration record rather than the report, it is written once and locked, and its length
# is the record's completeness and not prose that has to earn its place.
PROSE_BUDGET = {
    "README.md": 550,
    "docs/findings.md": 2958,
    "docs/methodology.md": 2195,
    "docs/rationale.md": 1492,
    "docs/references.md": 1724,
    "CONTRIBUTING.md": 599,
}

# A sentence of twelve words or more that stands on two of the budgeted pages. Each entry is the
# normalised sentence, exactly as prose_sentences returns it, with one line saying why it is
# still there. The list is emptied by the passes that cut the prose, and the test fails on an
# entry that no longer names a duplicate, so a stale line cannot sit here unnoticed.
DUPLICATE_ALLOWLIST = set()

# Phrases with which prose praises its own care instead of showing it. A reader cannot check
# "rigorous"; they can check a number.
SELF_PRAISE_PHRASES = (
    "said carefully",
    "worth noting",
    "it is important to",
    "as we have seen",
    "which is what a",
    "rigorous",
    "scrupulous",
    "carefully chosen",
)

# (file, phrase) pairs that stand today, keyed by phrase and not by sentence, because the sentence
# text moves whenever a line above it is rewrapped. The cutting passes emptied it, and the test
# fails on an entry that names no phrase on the page, so it stays empty.
SELF_PRAISE_ALLOWLIST = set()

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def prose_lines(path):
    """The lines of a Markdown page that are prose: no fenced code block, no table row. The
    word count below is taken from these, so a page does not pay for its data."""
    lines = []
    fenced = False
    for line in path.read_text(encoding="utf-8").split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if fenced or stripped.startswith("|"):
            continue
        lines.append(line)
    return lines


def prose_words(path):
    return sum(len(line.split()) for line in prose_lines(path))


def prose_sentences(path, min_words=1):
    """The prose of a page, split into sentences, normalised to one space and lower case.

    The duplicate check asks for twelve words or more, so that a short shared line such as a
    heading is not read as a copied paragraph. The self-praise check takes every sentence: the
    shortest of them, a heading, is where the praise usually is."""
    text = " ".join(prose_lines(path))
    out = []
    for sentence in SENTENCE_SPLIT.split(text):
        words = sentence.split()
        if len(words) >= min_words:
            out.append(" ".join(words).lower())
    return out


class ProseBudgetTest(unittest.TestCase):
    """The rule the project states for a rule line applies to its own prose: a line that does
    not earn its place is deleted. These three checks are what makes a cut stick."""

    def test_every_page_stays_inside_its_prose_budget(self):
        for name, budget in sorted(PROSE_BUDGET.items()):
            count = prose_words(REPO_ROOT / name)
            self.assertLessEqual(
                count,
                budget,
                "%s: %d words of prose, budget is %d" % (name, count, budget),
            )

    def test_no_sentence_lives_on_two_pages(self):
        where = {}
        for name in PROSE_BUDGET:
            for sentence in prose_sentences(REPO_ROOT / name, min_words=12):
                where.setdefault(sentence, set()).add(name)
        duplicates = {s: pages for s, pages in where.items() if len(pages) > 1}
        for sentence, pages in sorted(duplicates.items()):
            self.assertIn(
                sentence,
                DUPLICATE_ALLOWLIST,
                "the same sentence is on %s: %s" % (", ".join(sorted(pages)), sentence),
            )
        stale = DUPLICATE_ALLOWLIST - set(duplicates)
        self.assertFalse(
            stale,
            "no longer duplicated, delete from DUPLICATE_ALLOWLIST: %s" % sorted(stale),
        )

    def test_no_sentence_praises_the_care_taken_over_it(self):
        found = set()
        for name in PROSE_BUDGET:
            for sentence in prose_sentences(REPO_ROOT / name):
                for phrase in SELF_PRAISE_PHRASES:
                    if phrase in sentence:
                        found.add((name, phrase))
                        self.assertIn(
                            (name, phrase),
                            SELF_PRAISE_ALLOWLIST,
                            "%s praises its own care with %r: %s" % (name, phrase, sentence),
                        )
        stale = SELF_PRAISE_ALLOWLIST - found
        self.assertFalse(
            stale,
            "no longer present, delete from SELF_PRAISE_ALLOWLIST: %s" % sorted(stale),
        )


if __name__ == "__main__":
    unittest.main()
