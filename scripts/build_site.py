#!/usr/bin/env python3
"""Build the bilingual static guide without third-party dependencies."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://purpleeddy.github.io/agents-md-lab/"
PAGES = ("home", "rules", "examples", "guide", "evidence", "changelog")
PRINCIPLE_IDS = ("scope", "context", "implementation", "verification", "authorization", "data")
PREVIOUS_RULES = {
    "r1": "context", "r2": "scope", "r3": "implementation", "r4": "implementation",
    "r5": "context", "r6": "verification", "r7": "authorization", "r8": "data",
    "r9": "verification",
}


def escape(value):
    return html.escape(str(value), quote=True)


def page_path(locale, page="home", rule=None):
    prefix = "ko/" if locale == "ko" else ""
    suffix = "" if page == "home" else page + "/"
    if rule:
        suffix += rule.lower() + "/"
    return prefix + suffix + "index.html"


def relative(current, target):
    return posixpath.relpath(target, posixpath.dirname(current) or ".")


def instruction_items(text):
    """Read the flat bullet format used by the artifact and its translation."""
    lines = text.strip().splitlines()
    if not lines or any(not line.startswith('- ') or not line[2:].strip() for line in lines):
        raise ValueError('Instructions must be a nonempty flat bullet list.')
    return [line[2:] for line in lines]


def instruction_list(text):
    return '<ul class="instruction-list">' + ''.join(
        f'<li>{escape(item)}</li>' for item in instruction_items(text)) + '</ul>'


def extract_rules(text):
    sections = re.split(r"^## (.+)\n", text, flags=re.MULTILINE)
    rules = {}
    for heading, body in zip(sections[1::2], sections[2::2]):
        identifier = heading.strip().lower()
        if identifier in rules:
            raise ValueError(f"Duplicate baseline principle: {identifier}")
        if identifier not in PRINCIPLE_IDS:
            raise ValueError(f"Unknown baseline heading: {heading}")
        instruction_items(body)
        rules[identifier] = body.strip()
    if tuple(rules) != PRINCIPLE_IDS or any(not body for body in rules.values()):
        raise ValueError("The baseline must contain the six semantic principles, in order.")
    if re.search(r"<[^>]+>|Project settings", text):
        raise ValueError("The generic baseline must not contain project scaffolding or placeholders.")
    return rules


def source_urls(value):
    """Collect cited URLs across rules, adoption help, and evidence notes."""
    if isinstance(value, dict):
        if 'url' in value:
            yield value['url']
        for item in value.values():
            yield from source_urls(item)
    elif isinstance(value, list):
        for item in value:
            yield from source_urls(item)


def load_content(root):
    content = {locale: json.loads((root / f"site/content/{locale}.json").read_text())
               for locale in ("en", "ko")}
    revision = content["en"]["revision"]
    quotes = extract_rules((root / "templates/baseline.md").read_text())
    for locale, data in content.items():
        if data["locale"] != locale or data["revision"] != revision:
            raise ValueError("Locale and reviewed translation revisions must agree.")
        for key in ("title", "tagline", "nav", "labels", "home", "guide", "examples", "evidence", "changelog"):
            if not data.get(key):
                raise ValueError(f"Missing {locale} content: {key}")
        if tuple(rule["id"] for rule in data["rules"]) != PRINCIPLE_IDS:
            raise ValueError(f"Missing, duplicated, or reordered {locale} rules.")
        for rule in data["rules"]:
            for key in ("title", "why", "example", "applicability", "evidence"):
                if not rule.get(key):
                    raise ValueError(f"Missing {locale}/{rule['id']}/{key}")
            if not rule['example'].get('title'):
                raise ValueError(f"Missing story title: {locale}/{rule['id']}")
            if locale == 'ko':
                translation = rule.get('translation', {})
                if not isinstance(translation.get('text'), str) or not translation['text'].strip():
                    raise ValueError(f"Missing Korean translation: {rule['id']}")
                if len(instruction_items(translation['text'])) != len(instruction_items(quotes[rule['id']])):
                    raise ValueError(f"Korean instruction items must match the source: {rule['id']}")
                expected = hashlib.sha256(quotes[rule['id']].encode('utf-8')).hexdigest()
                if translation.get('sourceSha256') != expected:
                    raise ValueError(f"Stale translation source hash: {rule['id']}")
            if rule.get("revision") != revision:
                raise ValueError(f"Stale rule translation: {locale}/{rule['id']}")
            if rule["evidence"]["kind"] not in ("preference", "guidance", "observed"):
                raise ValueError("Unknown evidence category.")
        for url in source_urls(data):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("Sources must use absolute HTTPS links.")
    if list(source_urls(content['en'])) != list(source_urls(content['ko'])):
        raise ValueError("All evidence and adoption sources must match across languages.")
    for english, korean in zip(content["en"]["rules"], content["ko"]["rules"]):
        if english["evidence"]["kind"] != korean["evidence"]["kind"]:
            raise ValueError("Evidence classifications must match across languages.")
        if [s["url"] for s in english["evidence"]["sources"]] != [s["url"] for s in korean["evidence"]["sources"]]:
            raise ValueError("Evidence sources must match across languages.")
    return content


def paragraph(value, cls=""):
    return f'<p class="{cls}">{escape(value)}</p>'


def code(value, cls="", lang=None):
    language = f' lang="{escape(lang)}"' if lang else ''
    return f'<pre class="{cls}" tabindex="0"{language}><code>{escape(value)}</code></pre>'


def block(title, body, identifier="", cls="text-section"):
    anchor = f' id="{escape(identifier)}"' if identifier else ""
    return f'<section class="{cls}"{anchor}><h2>{escape(title)}</h2>{body}</section>'


def paragraphs(values):
    if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError('Narrative paragraphs must be a nonempty list of text.')
    return ''.join(paragraph(value) for value in values)


def build_outputs(root=ROOT):
    root = Path(root)
    baseline = (root / "templates/baseline.md").read_bytes()
    baseline_text = baseline.decode("utf-8")
    quotes = extract_rules(baseline_text)
    content = load_content(root)
    layout = (root / "site/layouts/page.html").read_text()
    outputs = {
        "docs/downloads/AGENTS.txt": baseline,
    }
    for name in ("site.css", "site.js"):
        outputs[f"docs/assets/{name}"] = (root / "site/assets" / name).read_bytes()

    def render(locale, page, rule=None, alias=None, embedded=False):
        data = content[locale]
        labels = data["labels"]
        current = page_path(locale) if embedded else page_path(locale, page, alias or rule)
        canonical = page_path(locale)
        other = "ko" if locale == "en" else "en"
        href = lambda target: escape(relative(current, target))
        link = lambda dest: href(page_path(locale)) + "#" + ("baseline" if dest == "home" else dest)
        title = data[page]["title"] if page not in ("home", "rules") else data["home"]["title"]
        nav = "".join(f'<a href="{link(item)}">{escape(data["nav"][item])}</a>' for item in PAGES)
        artifact_url = href("downloads/AGENTS.txt")
        controls = (f'<div class="actions"><button class="button primary" type="button" data-copy hidden>{escape(labels["copy"])}</button>'
                    f'<a class="button secondary" href="{artifact_url}" download="AGENTS.md">{escape(labels["download"])}</a></div>'
                    '<p class="copy-status" data-copy-status role="status" aria-live="polite"></p>'
                    f'<div class="copy-fallback" data-copy-fallback hidden><textarea readonly lang="en" aria-label="{escape(labels["englishArtifact"])}">'
                    f'{escape(baseline_text)}</textarea></div>')
        rule_cards = '<div class="rule-grid">' + "".join(
            f'<a class="rule-card" href="#{r["id"]}"><span class="rule-number">{r["id"]}</span>'
            f'<h3>{escape(r["title"])}</h3></a>'
            for r in data["rules"]) + '</div>'
        sidebar = ""
        if page == "home":
            title = data["home"]["title"]
            source_links = ' · '.join(
                f'<a href="{escape(source["url"])}">{escape(source["title"])}</a>'
                for source in data['home']['sources'])
            reviewed = escape(data['home']['reviewed'])
            provenance = (f'<p class="artifact-note" data-source-note>{source_links} · '
                          f'{escape(data["home"]["reviewedLabel"])} '
                          f'<time datetime="{reviewed}">{reviewed}</time></p>')
            body = ('<div class="document-home"><header class="document-heading">'
                    f'<div class="document-title"><h1>{escape(title)}</h1><span class="document-version">v{escape(data["revision"])}</span></div>'
                    f'{paragraph(data["home"]["intro"], "document-intro")}{provenance}</header>'
                    '<section class="source-document" id="baseline" aria-label="AGENTS.md">'
                    f'<div class="document-toolbar">{controls}<p class="artifact-note">{escape(labels["englishArtifact"])}</p></div>'
                    f'{code(baseline_text, "baseline-preview", lang="en")}</section>')
            body += block(labels.get("rulesTitle", data["nav"]["rules"]),
                          paragraph(labels.get("rulesIntro",data["tagline"]), "section-intro") +
                          f'<div class="shared-story"><h3>{escape(data["home"]["story"]["title"])}</h3>' +
                          paragraphs(data["home"]["story"]["paragraphs"]) + "</div>" + rule_cards, "rules")
            body += ''.join(render(locale, 'rules', item['id'], embedded=True) for item in data['rules'])
            body += ''.join(render(locale, section, embedded=True) for section in ('examples', 'guide', 'evidence', 'changelog'))
            body += '</div>'
        elif not embedded:
            target_id = rule or page
            target = link('home').split('#')[0]
            title = labels['migrationTitle']
            body = (f'<article class="guide-article" id="{alias or target_id}"><h1>{escape(title)}</h1>'
                    f'<p><a href="{target}#{target_id}">{escape(data["nav"]["home"])} · '
                    f'{escape(next((r["title"] for r in data["rules"] if r["id"] == rule), data["nav"][page]))}</a></p>')
            if rule:
                for section in ('role', 'why', 'example', 'applicability', 'evidence'):
                    body += block(labels[section], f'<a href="{target}#{rule}-{section}">{escape(labels[section])}</a>', section)
            body += '</article>'
        elif page == "rules":
            r = next(item for item in data["rules"] if item["id"] == rule)
            title = r["title"]
            kind = r['evidence']['kind']
            kind_label = next(k['title'] for k in data['evidence']['kinds'] if k['kind'] == kind)
            quote_id = ' id="role"' if locale == 'en' else ''
            body = (f'<article class="rule-article" id="{rule}"><header class="page-heading">'
                    f'<h1>{escape(title)}</h1></header><div class="quote-pair">'
                    f'<p class="quote-label">{escape(labels["original"])}</p>'
                    f'<blockquote class="rule-quote" lang="en"{quote_id}>{instruction_list(quotes[rule])}</blockquote>')
            if locale == 'ko':
                body += (f'<div class="rule-translation" lang="ko" id="role">'
                         f'<p class="quote-label">{escape(labels["translation"])}</p>'
                         f'{instruction_list(r["translation"]["text"])}</div>')
            body += ('</div><div class="rule-story">'
                     f'<section id="why"><h2>{escape(r["example"]["title"])}</h2>{paragraphs(r["why"])}</section>'
                     f'<div id="example">{paragraphs(r["example"]["paragraphs"])}</div>'
                     f'<div id="applicability">{paragraphs(r["applicability"])}</div></div>')
            if rule == 'implementation':
                body = body.replace('<section id="why">', '<section id="why"><span id="coherent-code"></span>')
                body = body.replace('<div id="applicability">', '<div id="applicability"><span id="reason-comments"></span>')
            sources = ''.join(f'<li><a href="{escape(s["url"])}">{escape(s["title"])}</a></li>' for s in r['evidence']['sources'])
            body += block(labels["evidence"],f'<span class="badge">{escape(kind_label)}</span>' + paragraph(r['evidence']['detail']) +
                          (f'<ul class="sources">{sources}</ul>' if sources else ''),"evidence")
            body += '</article>'
        else:
            info = data[page]
            body = f'<article class="guide-article"><header class="page-heading"><p class="eyebrow">AGENTS.MD / {escape(data["revision"])}</p><h1>{escape(title)}</h1>{paragraph(info["intro"],"lede")}</header>'
            if page == 'guide':
                body += '<div class="editor-notes">' + ''.join(
                    block(section['title'], paragraph(section['body']))
                    for section in data['home']['sections']) + '</div>'
                for i, step in enumerate(info['steps'],1):
                    body += block(f'{i:02d}. {step["title"]}',paragraph(step['body']),f'step-{i}')
                example = info.get('localContextExample')
                if example:
                    body += block(example['title'],'<span id="project-context"></span>' + paragraph(example['body']) + code(example['code'], lang='en'),"project-settings")
                adoption = info['claudeImport']
                body += block(adoption['title'], paragraph(adoption['body']) + code(adoption['code'], lang='en') +
                              f'<p><a href="{escape(adoption["source"]["url"])}">{escape(adoption["source"]["title"])}</a></p>', 'claude-code')
            elif page == 'examples':
                for item in info['items']:
                    body += block(item['title'],paragraphs(item['paragraphs']),item['id'])
            elif page == 'evidence':
                for item in info['kinds']:
                    body += block(item['title'],paragraph(item['body']),item['kind'])
                for i,item in enumerate(info['sections']):
                    section_body = paragraph(item['body'])
                    if item.get('source'):
                        section_body += f'<p><a href="{escape(item["source"]["url"])}">{escape(item["source"]["title"])}</a></p>'
                    body += block(item['title'],section_body,f'evidence-{i+1}')
                sources = {s['url']:s['title'] for r in data['rules'] for s in r['evidence']['sources']}
                body += block(labels['sources'],'<ul class="sources">' + ''.join(f'<li><a href="{escape(url)}">{escape(text)}</a></li>' for url,text in sources.items()) + '</ul>',"sources")
            else:
                for entry in info['entries']:
                    body += block(f'{entry["version"]} · {entry["date"]}', '<ul>' + ''.join(f'<li>{escape(change)}</li>' for change in entry['changes']) + '</ul>', 'v' + entry['version'].replace('.','-'))
            body += '</article>'
        if embedded:
            # Keep heading levels and deep links unique in the combined document.
            if rule:
                for section in ('role', 'why', 'example', 'applicability', 'evidence'):
                    body = body.replace(f'id="{section}"', f'id="{rule}-{section}"')
                body = body.replace('<h2>', '<h4>').replace('</h2>', '</h4>')
                body = body.replace('<h1>', '<h3>').replace('</h1>', '</h3>')
            else:
                body = body.replace('<article class="guide-article">', f'<article class="guide-article document-section" id="{page}">')
                body = body.replace('<h2>', '<h3>').replace('</h2>', '</h3>')
                body = body.replace('<h1>', '<h2>').replace('</h1>', '</h2>')
            return body
        mapping = {
            'LANG':locale,'TITLE':escape(title),'DESCRIPTION':escape(data['tagline']),
            'CSS':href('assets/site.css'),'JS':href('assets/site.js'),'HOME':link('home'),
            'NAV':nav,'SKIP':escape(labels['skipToContent']),'CONTENT':body,'SIDEBAR':sidebar,
            'OTHER_URL':href(page_path(other, page, alias or rule)),
            'OTHER_LANG':other,'OTHER_LABEL':'한국어' if other=='ko' else 'English',
            'COPY_SUCCESS':escape(labels['copySuccess']),'COPY_FAILURE':escape(labels['copyFailure']),
            'CANONICAL':ORIGIN+canonical.removesuffix('index.html'),
            'EN_URL':ORIGIN+page_path('en').removesuffix('index.html'),
            'KO_URL':ORIGIN+page_path('ko').removesuffix('index.html'),
            'FOOTER':escape(data['tagline']), 'REVISION':escape(data['revision']),
            'GUIDE':link('guide'),'GUIDE_LABEL':escape(data['nav']['guide']),
            'EVIDENCE':link('evidence'),'EVIDENCE_LABEL':escape(data['nav']['evidence']),
            'ARTIFACT_URL':artifact_url,
            'PRIMARY_LABEL': escape(labels['primaryNavigation']),
            'FOOTER_LABEL': escape(labels['footerNavigation']),
        }
        rendered = re.sub(r'\{\{([A-Z_]+)\}\}',lambda match: mapping[match.group(1)],layout)
        outputs['docs/'+current] = rendered.encode()

    for locale in ('en','ko'):
        for page in PAGES:
            render(locale,page)
        for rule in quotes:
            render(locale,'rules',rule)
        for previous, principle in PREVIOUS_RULES.items():
            render(locale, 'rules', principle, alias=previous)
    # Old public URLs remain explanatory entry points, not silent redirects.
    old_paths = ('methodology.html','findings.html','rationale.html','references.html','generated/comparison.html')
    for path in old_paths:
        evidence = relative(path,'index.html') + '#evidence'
        body = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>Sources · agents-md-lab</title>'
                f'<link rel="stylesheet" href="{relative(path,"assets/site.css")}"><main class="wrap guide-article">'
                '<h1>Read the sources and explanations.</h1><p>The guide is available in one document.</p>'
                f'<a class="button primary" href="{evidence}">Read the sources</a></main></html>')
        outputs['docs/'+path] = body.encode()
    outputs['docs/.nojekyll'] = b''
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Check generated files without changing them.')
    args = parser.parse_args()
    try:
        outputs = build_outputs()
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1,f'Content error: {error}\n')
    mismatches = []
    if args.check:
        allowed = set(outputs) | {'docs/_config.yml'}
        for path in (ROOT / 'docs').rglob('*'):
            if path.is_file() and path.relative_to(ROOT).as_posix() not in allowed:
                mismatches.append(path.relative_to(ROOT).as_posix() + ' (unexpected output)')
    for name, expected in outputs.items():
        path = ROOT/name
        if args.check:
            if not path.exists() or path.read_bytes()!=expected:
                mismatches.append(name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        parser.exit(1,'Generated files differ: '+', '.join(mismatches)+'\n')
    print(f'{"Verified" if args.check else "Built"} {len(outputs)} static files; English artifact sha256 {hashlib.sha256(outputs["docs/downloads/AGENTS.txt"]).hexdigest()[:12]}.')


if __name__ == '__main__':
    main()
