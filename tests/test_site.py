"""Behavioral checks for the published guide and its reproducible archive runner."""

import contextlib
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SECTION_IDS = ("scope", "context", "implementation", "verification", "authorization", "data")
OLD_RULE_TARGETS = {
    "r1": "context", "r2": "scope", "r3": "implementation", "r4": "implementation",
    "r5": "context", "r6": "verification", "r7": "authorization", "r8": "data",
    "r9": "verification",
}


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    imported = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported)
    return imported


class Page(HTMLParser):
    def __init__(self, data):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.resources = []
        self.downloads = []
        self.text = []
        self.lang = None
        self.headings = []
        self.primary_links = []
        self.instruction_list_counts = []
        self._instruction_list = False
        self.rule_quotes = []
        self.rule_quote_languages = []
        self.rule_translations = []
        self.translation_languages = []
        self.paragraphs = []
        self.heading_labels = []
        self.story_pre_blocks = []
        self.collapsed_rule_ids = []
        self._primary_navigation = False
        self._quote_parts = None
        self._quote_kind = None
        self._quote_language = None
        self._paragraph_parts = None
        self._heading_parts = None
        self._heading_tag = None
        self._article = None
        self._details_depth = 0
        self._translation_depth = 0
        self._translation_paragraph = False
        self._translation_parts = None
        self._translation_language = None
        self.feed(data.decode("utf-8"))

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        classes = attributes.get("class", "").split()
        if tag == "div" and self._translation_depth:
            self._translation_depth += 1
        elif tag == "div" and "rule-translation" in classes:
            self._translation_depth = 1
            self._translation_parts = []
            self._translation_language = attributes.get("lang")
        if "id" in attributes:
            self.ids.append(attributes["id"])
            if attributes["id"] in SECTION_IDS and self._details_depth:
                self.collapsed_rule_ids.append(attributes["id"])
        if tag == "article":
            self._article = attributes.get("id")
        if tag == "details":
            self._details_depth += 1
            if self._article in SECTION_IDS:
                self.collapsed_rule_ids.append(self._article)
        if tag == "pre" and self._article in (*SECTION_IDS, "examples"):
            self.story_pre_blocks.append(self._article)
        if tag == "ul" and "instruction-list" in classes:
            self._instruction_list = True
            self.instruction_list_counts.append(0)
        if tag == "li" and self._instruction_list:
            self.instruction_list_counts[-1] += 1
            if self._quote_parts is not None:
                self._quote_parts.append("- ")
        if tag == "p" or (tag == "li" and self._translation_depth):
            self._paragraph_parts = []
            self._translation_paragraph = bool(self._translation_depth and "quote-label" not in classes)
        if tag == "html":
            self.lang = attributes.get("lang")
        if tag == "nav" and "primary-nav" in attributes.get("class", "").split():
            self._primary_navigation = True
        if tag == "blockquote" and ("rule-quote" in classes or "rule-translation" in classes):
            self._quote_parts = []
            self._quote_kind = "translation" if "rule-translation" in classes else "original"
            self._quote_language = attributes.get("lang")
        if tag == "a" and "href" in attributes:
            self.links.append(attributes["href"])
            if self._primary_navigation:
                self.primary_links.append(attributes["href"])
            if "download" in attributes:
                self.downloads.append((attributes["href"], attributes["download"]))
        if tag in {"script", "img", "source", "iframe", "video", "audio"}:
            if attributes.get("src"):
                self.resources.append(attributes["src"])
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.resources.append(attributes["href"])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(tag)
            self._heading_tag = tag
            self._heading_parts = []

    def handle_data(self, data):
        self.text.append(data)
        if self._quote_parts is not None:
            self._quote_parts.append(data)
        if self._paragraph_parts is not None:
            self._paragraph_parts.append(data)
        if self._heading_parts is not None:
            self._heading_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "nav":
            self._primary_navigation = False
        if tag == "article":
            self._article = None
        if tag == "details":
            self._details_depth -= 1
        if tag == "li" and self._instruction_list and self._quote_parts is not None:
            self._quote_parts.append("\n")
        if tag == "ul":
            self._instruction_list = False
        if tag in ("p", "li") and self._paragraph_parts is not None:
            self.paragraphs.append("".join(self._paragraph_parts))
            if self._translation_paragraph:
                self._translation_parts.append(("- " if tag == "li" else "") + "".join(self._paragraph_parts) + ("\n" if tag == "li" else ""))
            self._paragraph_parts = None
            self._translation_paragraph = False
        if tag == "div" and self._translation_depth:
            self._translation_depth -= 1
            if not self._translation_depth:
                self.rule_translations.append("".join(self._translation_parts).strip())
                self.translation_languages.append(self._translation_language)
        if tag == self._heading_tag:
            self.heading_labels.append("".join(self._heading_parts))
            self._heading_parts = None
            self._heading_tag = None
        if tag == "blockquote" and self._quote_parts is not None:
            if self._quote_kind == "translation":
                self.rule_translations.append("".join(self._quote_parts))
                self.translation_languages.append(self._quote_language)
            else:
                self.rule_quotes.append("".join(self._quote_parts).strip())
                self.rule_quote_languages.append(self._quote_language)
            self._quote_parts = None


class PublishedSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = module("build_site")
        cls.outputs = cls.builder.build_outputs(ROOT)
        cls.pages = {name: Page(data) for name, data in cls.outputs.items()
                     if name.endswith(".html")}
        cls.english = json.loads((ROOT / "site/content/en.json").read_text())
        cls.korean = json.loads((ROOT / "site/content/ko.json").read_text())

    def test_download_is_exactly_the_english_source(self):
        baseline = (ROOT / "templates/baseline.md").read_bytes()
        self.assertEqual(self.outputs["docs/downloads/AGENTS.txt"], baseline)
        self.assertNotRegex(baseline.decode(), r"[\uac00-\ud7af]")
        for path in ("docs/index.html", "docs/ko/index.html"):
            downloads = self.pages[path].downloads
            self.assertTrue(downloads, path)
            current_found = False
            for href, filename in downloads:
                resolved = urljoin("https://local.test/" + path, href)
                current_found = True
                self.assertEqual(filename, "AGENTS.md")
                self.assertEqual(urlsplit(resolved).path, "/docs/downloads/AGENTS.txt")
            self.assertTrue(current_found, path)

    def test_homepage_leads_with_the_complete_source_document(self):
        baseline = (ROOT / 'templates/baseline.md').read_text()
        for path in ('docs/index.html', 'docs/ko/index.html'):
            document = self.outputs[path].decode()
            self.assertIn('<h1>AGENTS.md</h1>', document)
            self.assertLess(document.index('id="baseline"'), document.index('id="rules"'))
            previews = re.findall(
                r'<pre class="baseline-preview"[^>]*><code>(.*?)</code></pre>',
                document, re.S)
            self.assertEqual(len(previews), 1, path)
            self.assertEqual(html.unescape(previews[0]), baseline, path)

    def test_intro_displays_official_sources_and_review_date(self):
        for locale, content in (('', self.english), ('ko/', self.korean)):
            document = self.outputs[f'docs/{locale}index.html'].decode()
            heading = document.split('<header class="document-heading">', 1)[1].split('</header>', 1)[0]
            self.assertIn(html.escape(content['home']['intro'], quote=True), heading)
            self.assertIn('data-source-note', heading)
            self.assertIn('<time datetime="2026-09-14">2026-09-14</time>', heading)
            for source in content['home']['sources']:
                self.assertIn(f'href="{html.escape(source["url"], quote=True)}"', heading)
            self.assertEqual({urlsplit(source['url']).netloc for source in content['home']['sources']},
                             {'developers.openai.com', 'code.claude.com'})

    def test_korean_intro_breaks_between_sentences(self):
        document = self.outputs['docs/ko/index.html'].decode()
        intro = re.search(r'<p class="document-intro">(.*?)</p>', document, re.S).group(1)
        self.assertIn('에이전트용 지침입니다.\n요청한 작업을', html.unescape(intro))
        self.assertIn('끝까지 마치고, 필요한 코드를', html.unescape(intro))
        self.assertEqual(intro.count('\n'), 1)
        english = self.outputs['docs/index.html'].decode()
        english_intro = re.search(r'<p class="document-intro">(.*?)</p>', english, re.S).group(1)
        self.assertNotIn('\n', english_intro)

    def test_all_rules_have_matching_translations_and_verbatim_quotes(self):
        canonical = (ROOT / "templates/baseline.md").read_text()
        matches = re.findall(r"^## ([^\n]+)\n\n(.*?)(?=\n## |\Z)",
                             canonical, re.M | re.S)
        self.assertEqual([heading for heading, _ in matches],
                         [identifier.title() for identifier in SECTION_IDS])
        for content in (self.english, self.korean):
            self.assertEqual([rule["id"] for rule in content["rules"]],
                             list(SECTION_IDS))
            self.assertEqual(content["revision"], "1.0.0")
            for rule in content["rules"]:
                self.assertNotIn("role", rule)
                for key in ("why", "example", "applicability", "evidence", "revision"):
                    self.assertTrue(rule[key], (rule["id"], key))
        for locale in ("", "ko/"):
            path = f"docs/{locale}index.html"
            self.assertEqual(self.pages[path].rule_quotes,
                             [quote.strip() for _, quote in matches], path)
            self.assertEqual(self.pages[path].rule_quote_languages, ["en"] * len(SECTION_IDS))

    def test_instructions_render_as_matching_semantic_lists(self):
        counts = [4, 4, 5, 5, 3, 3]
        self.assertEqual(self.pages["docs/index.html"].instruction_list_counts, counts)
        self.assertEqual(self.pages["docs/ko/index.html"].instruction_list_counts,
                         [count for count in counts for _ in range(2)])

    def test_malformed_or_unpaired_instruction_lists_stop_generation(self):
        for mutation in ("plain-paragraph", "empty-item", "nested-item", "missing-translation-item"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = self.source_copy(directory)
                path = root / "site/content/ko.json"
                data = json.loads(path.read_text())
                lines = data["rules"][0]["translation"]["text"].splitlines()
                if mutation == "plain-paragraph":
                    lines[0] = lines[0][2:]
                elif mutation == "empty-item":
                    lines[0] = "- "
                elif mutation == "nested-item":
                    lines[1] = "  " + lines[1]
                else:
                    lines.pop()
                data["rules"][0]["translation"]["text"] = "\n".join(lines)
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    self.builder.build_outputs(root)

    def test_korean_notes_pair_source_bound_translations(self):
        english, korean = self.pages["docs/index.html"], self.pages["docs/ko/index.html"]
        self.assertEqual(english.rule_translations, [])
        self.assertEqual(korean.rule_translations,
                         [rule["translation"]["text"] for rule in self.korean["rules"]])
        self.assertEqual(korean.translation_languages, ["ko"] * len(SECTION_IDS))
        self.assertNotIn("뜻", korean.heading_labels)
        canonical = (ROOT / "templates/baseline.md").read_text()
        paragraphs = {heading.lower(): body.strip() for heading, body in re.findall(
            r"^## ([^\n]+)\n\n(.*?)(?=\n## |\Z)", canonical, re.M | re.S)}
        for rule in self.korean["rules"]:
            expected = hashlib.sha256(paragraphs[rule["id"]].encode("utf-8")).hexdigest()
            self.assertEqual(rule["translation"]["sourceSha256"], expected, rule["id"])
            self.assertRegex(rule["title"], r"^[가-힣 ]+\(" + rule["id"].title() + r"\)$")
            self.assertIn(rule["title"], korean.heading_labels)

    def test_each_locale_is_one_complete_document_with_in_page_navigation(self):
        expected_sections = {"baseline", "rules", "guide", "examples", "evidence", "changelog"}
        for locale, content in (("", self.english), ("ko/", self.korean)):
            path = f"docs/{locale}index.html"
            page = self.pages[path]
            self.assertTrue(expected_sections <= set(page.ids), path)
            self.assertTrue(set(SECTION_IDS) <= set(page.ids), path)
            destinations = [urlsplit(urljoin("https://local.test/" + path, href))
                            for href in page.primary_links]
            self.assertEqual({target.fragment for target in destinations}, expected_sections, path)
            for target in destinations:
                self.assertEqual(target.netloc, "local.test")
                self.assertIn(target.path, ("/" + path, "/docs/" + locale), path)
            for href in page.links:
                target = urlsplit(urljoin("https://local.test/" + path, href))
                if target.netloc == "local.test" and (target.path.endswith(".html") or target.path.endswith("/")):
                    self.assertIn(target.path, ("/docs/index.html", "/docs/ko/index.html", "/docs/", "/docs/ko/"),
                                  (path, href))
            rendered = " ".join(" ".join(page.text).split())
            required_text = [content["home"]["story"]["title"], *content["home"]["story"]["paragraphs"]]
            for rule in content["rules"]:
                required_text.extend(rule["why"])
                required_text.extend(rule["applicability"])
                required_text.append(rule["example"]["title"])
                required_text.extend(rule["example"]["paragraphs"])
                required_text.append(rule["evidence"]["detail"])
                for section in ("role", "why", "example", "applicability", "evidence"):
                    self.assertIn(f'{rule["id"]}-{section}', page.ids, path)
            required_text.extend(step["body"] for step in content["guide"]["steps"])
            required_text.append(content["guide"]["claudeImport"]["code"])
            for example in content["examples"]["items"]:
                required_text.append(example["title"])
                required_text.extend(example["paragraphs"])
            required_text.extend(section["body"] for section in content["evidence"]["sections"])
            required_text.extend(change for entry in content["changelog"]["entries"] for change in entry["changes"])
            for text in required_text:
                self.assertIn(" ".join(text.split()), rendered, path)

    def test_the_task_story_and_report_are_readable_prose_not_collapsed_code(self):
        for locale, content in (("", self.english), ("ko/", self.korean)):
            page = self.pages[f"docs/{locale}index.html"]
            self.assertEqual(page.story_pre_blocks, [])
            self.assertEqual(page.collapsed_rule_ids, [])
            self.assertEqual([item["id"] for item in content["examples"]["items"]],
                             ["report-change", "report-check", "report-gap"])
            prose = list(content["home"]["story"]["paragraphs"])
            for rule in content["rules"]:
                prose.extend(rule["why"])
                prose.extend(rule["example"]["paragraphs"])
                prose.extend(rule["applicability"])
            for item in content["examples"]["items"]:
                prose.extend(item["paragraphs"])
            rendered_paragraphs = {" ".join(paragraph.split()) for paragraph in page.paragraphs}
            for paragraph in prose:
                self.assertIn(" ".join(paragraph.split()), rendered_paragraphs)
            for previous in ("project-context", "coherent-code", "reason-comments"):
                self.assertIn(previous, page.ids)

    def test_generic_artifact_has_no_project_configuration(self):
        canonical = (ROOT / "templates/baseline.md").read_text()
        self.assertNotRegex(canonical, r"(?i)Project settings")
        self.assertNotRegex(canonical, r"<[^>\n]+>")
        self.assertNotRegex(canonical, r"(?m)^## R\d+\b")
        for repository_fact in ("agents-md-lab", "scripts/build_site.py", "scripts/check_all.py"):
            self.assertNotIn(repository_fact, canonical)

    def test_first_release_has_no_previous_version_artifacts(self):
        self.assertEqual(
            {path for path in self.outputs if path.startswith("docs/downloads/")},
            {"docs/downloads/AGENTS.txt"},
        )
        self.assertFalse((ROOT / "templates/history").exists())
        for content in (self.english, self.korean):
            self.assertEqual(content["revision"], "1.0.0")
            self.assertEqual([entry["version"] for entry in content["changelog"]["entries"]], ["1.0.0"])
        for path, page in self.pages.items():
            self.assertNotRegex(" ".join(page.text), r"[23]\.[01]\.0", path)

    def test_old_localized_rule_routes_keep_deep_link_destinations(self):
        sections = ("role", "why", "example", "applicability", "evidence")
        for locale in ("", "ko/"):
            previous_routes = {**OLD_RULE_TARGETS, **{identifier: identifier for identifier in SECTION_IDS}}
            for previous, current in previous_routes.items():
                path = f"docs/{locale}rules/{previous}/index.html"
                self.assertIn(path, self.pages)
                page = self.pages[path]
                self.assertIn(previous, page.ids, path)
                resolved = set()
                for link in page.links:
                    destination = urlsplit(urljoin("https://local.test/" + path, link))
                    target_path = destination.path
                    if target_path.endswith("/"):
                        target_path += "index.html"
                    resolved.add((destination.netloc, target_path, destination.fragment))
                target = f"/docs/{locale}index.html"
                self.assertIn(("local.test", target, current), resolved, path)
                for section in sections:
                    self.assertIn(section, page.ids, path)
                    self.assertIn(("local.test", target, f"{current}-{section}"), resolved, path)

    def test_previous_section_pages_point_to_the_complete_document(self):
        for locale in ("", "ko/"):
            for section in ("guide", "examples", "evidence", "changelog", "rules"):
                path = f"docs/{locale}{section}/index.html"
                self.assertIn(path, self.pages)
                destinations = [urlsplit(urljoin("https://local.test/" + path, href))
                                for href in self.pages[path].links]
                self.assertTrue(any(target.netloc == "local.test"
                                    and target.path in (f"/docs/{locale}index.html", f"/docs/{locale}")
                                    and target.fragment == section for target in destinations), path)

    def test_navigation_resources_and_anchors_work_under_both_base_paths(self):
        for prefix in ("/", "/agents-md-lab/"):
            for path, page in self.pages.items():
                base = "https://local.test" + prefix + path.removeprefix("docs/")
                self.assertEqual(len(page.ids), len(set(page.ids)), path)
                for href in page.links + page.resources:
                    resolved = urlsplit(urljoin(base, href))
                    if resolved.netloc != "local.test":
                        self.assertNotIn(href, page.resources, (path, href))
                        self.assertIn(resolved.scheme, {"https", "mailto"}, (path, href))
                        continue
                    self.assertTrue(resolved.path.startswith(prefix), (path, href, prefix))
                    target = "docs/" + unquote(resolved.path.removeprefix(prefix))
                    if target.endswith("/"):
                        target += "index.html"
                    self.assertIn(target, self.outputs, (path, href, target))
                    if resolved.fragment:
                        self.assertIn(target, self.pages, (path, href))
                        self.assertIn(unquote(resolved.fragment), self.pages[target].ids,
                                      (path, href))

    def test_locale_pages_have_readable_structure_and_matching_routes(self):
        for path, page in self.pages.items():
            if path.startswith("docs/ko/"):
                self.assertEqual(page.lang, "ko", path)
                counterpart = path.replace("docs/ko/", "docs/", 1)
                self.assertIn(counterpart, self.pages)
            else:
                self.assertEqual(page.lang, "en", path)
            self.assertEqual(page.headings.count("h1"), 1, path)
            self.assertTrue(page.text, path)

    def test_core_payload_is_bounded_and_no_live_evaluator_is_shipped(self):
        for path, page in self.pages.items():
            resources = set()
            for href in page.resources:
                resolved = urlsplit(urljoin("https://local.test/" + path, href))
                if resolved.netloc == "local.test":
                    resources.add(resolved.path.lstrip("/"))
            size = len(self.outputs[path]) + sum(len(self.outputs[name]) for name in resources)
            self.assertLessEqual(size, 150 * 1024, path)
        self.assertNotIn("docs/compare.js", self.outputs)
        self.assertNotIn("docs/star.js", self.outputs)

    def source_copy(self, directory):
        root = Path(directory)
        for name in ("site", "templates"):
            shutil.copytree(ROOT / name, root / name)
        return root

    def test_untrusted_editorial_text_is_escaped_as_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_copy(directory)
            path = root / "site/content/en.json"
            data = json.loads(path.read_text())
            payload = '<img src="https://unwanted.test/pixel" onerror="alert(1)"> & example'
            data["rules"][0]["why"][0] = payload
            path.write_text(json.dumps(data))
            outputs = self.builder.build_outputs(root)
        page = Page(outputs["docs/index.html"])
        self.assertIn(payload, page.text)
        self.assertNotIn("https://unwanted.test/pixel", page.resources)

    def test_missing_or_stale_translation_stops_generation(self):
        for mutation in ("missing-rule", "duplicate-rule", "reordered-rules", "stale-revision"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = self.source_copy(directory)
                path = root / "site/content/ko.json"
                data = json.loads(path.read_text())
                if mutation == "missing-rule":
                    data["rules"].pop()
                elif mutation == "duplicate-rule":
                    data["rules"][-1] = data["rules"][0]
                elif mutation == "reordered-rules":
                    data["rules"][0], data["rules"][1] = data["rules"][1], data["rules"][0]
                else:
                    data["rules"][0]["revision"] = data["revision"] + "-stale"
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    self.builder.build_outputs(root)

    def test_missing_empty_or_stale_korean_quote_translation_stops_generation(self):
        for mutation in ("missing", "empty-text", "non-text", "stale-hash"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = self.source_copy(directory)
                path = root / "site/content/ko.json"
                data = json.loads(path.read_text())
                rule = data["rules"][0]
                if mutation == "missing":
                    del rule["translation"]
                elif mutation == "empty-text":
                    rule["translation"]["text"] = "  "
                elif mutation == "non-text":
                    rule["translation"]["text"] = 5
                else:
                    rule["translation"]["sourceSha256"] = "0" * 64
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    self.builder.build_outputs(root)

    def test_same_version_english_change_invalidates_translation_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_copy(directory)
            path = root / "templates/baseline.md"
            original = path.read_text()
            updated = original.replace("Complete the requested outcome", "Finish the requested outcome", 1)
            self.assertNotEqual(original, updated)
            path.write_text(updated)
            translation_path = root / "site/content/ko.json"
            unchanged_translation = translation_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "[Ss]tale translation source hash"):
                self.builder.build_outputs(root)
            self.assertEqual(translation_path.read_bytes(), unchanged_translation)

    def test_invalid_narrative_paragraphs_stop_generation(self):
        for mutation in ("string-instead-of-list", "empty-story", "non-text-paragraph",
                         "shared-story-string", "empty-final-report"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = self.source_copy(directory)
                path = root / "site/content/en.json"
                data = json.loads(path.read_text())
                rule = data["rules"][0]
                if mutation == "string-instead-of-list":
                    rule["why"] = "Do not render a string as individual characters."
                elif mutation == "empty-story":
                    rule["example"]["paragraphs"] = []
                elif mutation == "non-text-paragraph":
                    rule["applicability"] = [42]
                elif mutation == "shared-story-string":
                    data["home"]["story"]["paragraphs"] = "A story must be a paragraph list."
                else:
                    data["examples"]["items"][0]["paragraphs"] = []
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    self.builder.build_outputs(root)

    def test_unsafe_source_scheme_stops_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_copy(directory)
            path = root / "site/content/en.json"
            data = json.loads(path.read_text())
            rule = next(rule for rule in data["rules"] if rule["evidence"]["sources"])
            rule["evidence"]["sources"][0]["url"] = "javascript:alert(1)"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                self.builder.build_outputs(root)

    def test_duplicate_canonical_rule_stops_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_copy(directory)
            path = root / "templates/baseline.md"
            path.write_text(path.read_text() + "\n## Scope\n\nConflicting text.\n")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                self.builder.build_outputs(root)

    def test_missing_canonical_section_stops_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_copy(directory)
            path = root / "templates/baseline.md"
            path.write_text(re.sub(r"\n## Context\n.*?(?=\n## )", "", path.read_text(), flags=re.S))
            with self.assertRaises(ValueError):
                self.builder.build_outputs(root)

    def test_extra_or_project_configuration_sections_stop_generation(self):
        for heading in ("Project settings", "Unrelated section"):
            with self.subTest(heading=heading), tempfile.TemporaryDirectory() as directory:
                root = self.source_copy(directory)
                path = root / "templates/baseline.md"
                path.write_text(path.read_text() + f"\n## {heading}\n\nExtra content.\n")
                with self.assertRaises(ValueError):
                    self.builder.build_outputs(root)

    def test_generated_check_rejects_stale_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, payload in self.outputs.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            (root / "docs/stale-evaluator.js").write_text("outdated code")
            with patch.object(self.builder, "ROOT", root):
                with patch.object(self.builder, "build_outputs", return_value=self.outputs):
                    with patch.object(sys, "argv", ["build_site.py", "--check"]):
                        with contextlib.redirect_stderr(io.StringIO()) as output:
                            with self.assertRaises(SystemExit) as result:
                                self.builder.main()
            self.assertEqual(result.exception.code, 1)
            self.assertIn("stale-evaluator.js (unexpected output)", output.getvalue())


class ArchiveRunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = module("check_all")

    def snapshot(self, directory):
        path = Path(directory) / "sample.txt"
        path.write_text("preserved source\n")
        return {"commit": "example", "files": [{
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mode": stat.S_IMODE(path.stat().st_mode), "symlink": None,
        }]}

    def test_snapshot_accepts_exact_source_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.snapshot(directory)
            self.runner.verify_snapshot(directory, manifest)
            (Path(directory) / "sample.txt").write_text("changed source\n")
            with self.assertRaisesRegex(ValueError, "Changed archive contents"):
                self.runner.verify_snapshot(directory, manifest)

    def test_snapshot_rejects_extra_files_and_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.snapshot(directory)
            (Path(directory) / "extra.txt").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                self.runner.verify_snapshot(directory, manifest)
            manifest["files"][0]["path"] = "../sample.txt"
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                self.runner.verify_snapshot(directory, manifest)

    def test_snapshot_rejects_replacing_a_file_with_an_external_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.snapshot(directory)
            path = Path(directory) / "sample.txt"
            path.unlink()
            path.symlink_to(ROOT / "README.md")
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                self.runner.verify_snapshot(directory, manifest)

    def test_skipped_coverage_is_reported_without_changing_command_exit(self):
        result = type("Result", (), {
            "returncode": 0, "stdout": "",
            "stderr": "test_optional (legacy.Test) ... skipped 'cache is not on disk'\nOK (skipped=1)\n",
        })()
        with patch.object(self.runner.subprocess, "run", return_value=result):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code, gaps = self.runner.run_command("Legacy tests", ["python3"], ROOT)
        self.assertEqual(code, 0)
        self.assertEqual(len(gaps), 1)
        self.assertIn("UNVERIFIED", output.getvalue())
        self.assertIn("cache is not on disk", output.getvalue())

    def test_command_failures_remain_failures(self):
        result = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "FAILED (errors=5)\n"})()
        with patch.object(self.runner.subprocess, "run", return_value=result):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code, _ = self.runner.run_command("Legacy tests", ["python3"], ROOT)
        self.assertEqual(code, 1)
        self.assertIn("FAILED (errors=5)", output.getvalue())

    def test_missing_history_is_a_failure_without_running_legacy_commands(self):
        with patch.object(self.runner, "restore_legacy", side_effect=ValueError("Missing history")):
            with patch.object(self.runner, "run_command") as command:
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    results = self.runner.run_legacy(ROOT)
        command.assert_not_called()
        self.assertNotEqual(results[0][0], 0)
        self.assertIn("FAILED / UNVERIFIED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
