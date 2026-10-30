"""Writes the scenarios the JavaScript package must render as this one does.

Every document the Python suite renders as a post, a fragment or MJML — the
test that renders it names it — and every document of
`parity/documents.json`, rendered here once, the answer written down:

| File                         | Output                                 |
|------------------------------|----------------------------------------|
| `parity/linkedin.json`       | the post, its count, its lines — each  |
|                              | fragment's kind, display and cost — and|
|                              | what the feed will not show            |
| `parity/html_fragment.json`  | the fragment                           |
| `parity/mjml.json`           | the MJML                               |

`js/test/parity.test.ts` renders each case with the JavaScript package and
wants the same characters. A refusal is an answer too: its class and its
message.

A URL factory is replayed by name, each side implementing the same two:

| Factory   | What it does                                                    |
|-----------|-----------------------------------------------------------------|
| `width`   | rewrites nothing, declares its `link_length`                    |
| `marking` | `<url>#button` / `#bold` / `#link`, an image as `img:<url>`     |

    uv run python scripts/parity.py          # rewrite the three files
    uv run python scripts/parity.py --check  # fail if one is out of date
"""

import json
import os
import sys
from functools import partial
from importlib.metadata import version
from pathlib import Path

import pytest

import inkletter
from inkletter import (
    LengthError,
    URLFactory,
    parse_markdown_to_html_fragment,
    parse_markdown_to_mjml,
    render_linkedin,
)
from inkletter.exceptions import MarkupError, ThemeError
from inkletter.theme import DEFAULT_THEME

ROOT = Path(__file__).resolve().parent.parent
PARITY = ROOT / "parity"
OUTPUTS = ("linkedin", "html_fragment", "mjml")


class Width(URLFactory):
    def __init__(self, link_length):
        self.link_length = link_length


class Marking(URLFactory):
    def rewrite_link(self, url, is_button=False, is_bold=False):
        return f"{url}#{'button' if is_button else 'bold' if is_bold else 'link'}"

    def rewrite_image(self, url):
        return f"img:{url}"


def factory_of(case):
    if case.get("factory") == "marking":
        return Marking()
    if case.get("link_length") is not None:
        return Width(case["link_length"])
    return None


# --- Rendering a case ---


def answer(render, source, **options):
    """What a render says: its output, or the refusal it raises."""
    try:
        return {"expected": render(source, **options)}
    except (LengthError, MarkupError, ThemeError) as refusal:
        return {"error": type(refusal).__name__, "message": str(refusal)}


def linkedin(case):
    found = answer(
        render_linkedin,
        case["source"],
        unicode_styling=case.get("unicode_styling", False),
        url_factory=factory_of(case),
    )
    if "expected" not in found:
        return found
    render = found.pop("expected")
    return {
        "expected": render.text,
        "length": render.length,
        "lines": [
            [line.text, line.cost, [[s.kind, s.display, s.cost] for s in line.segments]]
            for line in render.lines
        ],
        "unrendered_formatting": render.unrendered_formatting,
        "unrendered_headings": render.unrendered_headings,
    }


def html_fragment(case):
    return answer(
        parse_markdown_to_html_fragment,
        case["source"],
        bold_link_is_button=case.get("bold_link_is_button", True),
        link_attributes=case.get("link_attributes", True),
        url_factory=factory_of(case),
    )


def mjml(case):
    theme = case.get("theme")
    return answer(
        parse_markdown_to_mjml,
        case["source"],
        theme=None if theme is None else inkletter.Theme.from_dict(theme),
        bold_link_is_button=case.get("bold_link_is_button", True),
        link_attributes=case.get("link_attributes", True),
        url_factory=factory_of(case),
    )


RENDERS = {"linkedin": linkedin, "html_fragment": html_fragment, "mjml": mjml}


# --- Collecting the cases ---


class Recorder:
    """Records every document the suite renders, with the test rendering
    it — a call with a factory of the test's own is replayed with `marking`,
    which says as much about where each URL went."""

    OPTIONS = {
        "linkedin": ("unicode_styling",),
        "html_fragment": ("bold_link_is_button", "link_attributes"),
        "mjml": ("bold_link_is_button", "link_attributes", "theme"),
    }

    def __init__(self):
        self.cases = {output: [] for output in OUTPUTS}

    def pytest_configure(self, config):
        for output, module, name in (
            ("linkedin", inkletter.md_to_linkedin, "parse_markdown_to_linkedin"),
            ("linkedin", inkletter.md_to_linkedin, "render_linkedin"),
            ("html_fragment", inkletter.md_to_html_fragment, "parse_markdown_to_html_fragment"),
            ("mjml", inkletter.md_to_mjml, "parse_markdown_to_mjml"),
        ):
            recording = partial(self.recorded, output, getattr(module, name))
            setattr(module, name, recording)
            setattr(inkletter, name, recording)

    def recorded(self, output, render, markdown_text, *args, **kwargs):
        self.record(output, markdown_text, kwargs)
        return render(markdown_text, *args, **kwargs)

    def record(self, output, source, kwargs):
        if not isinstance(source, str):
            return
        case = {"name": os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0], "source": source}
        for option in self.OPTIONS[output]:
            value = kwargs.get(option)
            if option == "theme":
                if value is not None and value != DEFAULT_THEME:
                    case["theme"] = mapping_of(value)
            elif value is not None:
                case[option] = value
        factory = kwargs.get("url_factory")
        if factory is not None:
            if type(factory).link_length is None and factory.link_length is None:
                case["factory"] = "marking"
            else:
                case["link_length"] = factory.link_length
        self.cases[output].append(case)


def mapping_of(theme):
    """A theme as the mapping both sides build it from: its fonts named as
    `[fonts]` names them, without the quotes a stack may spell them with."""
    mapping = theme.to_dict()
    mapping["fonts"] = {name.strip("\"'"): href for name, href in theme.fonts}
    return mapping


def collected():
    recorder = Recorder()
    code = pytest.main(["-qq", "-p", "no:cacheprovider", str(ROOT / "tests")], plugins=[recorder])
    if code != 0:
        sys.exit(f"the suite fails ({code}): fix it before writing what it answers")
    documents = json.loads((PARITY / "documents.json").read_text(encoding="utf-8"))["documents"]
    for output in OUTPUTS:
        for document in documents:
            case = {"name": document["name"], "source": document["source"]}
            if output == "linkedin":
                case.update(
                    {
                        key: document[key]
                        for key in ("unicode_styling", "link_length")
                        if key in document
                    }
                )
            recorder.cases[output].append(case)
            if output != "linkedin":
                recorder.cases[output].append(
                    {**case, "name": f"{case['name']} (marking)", "factory": "marking"}
                )
    return recorder.cases


def unique(cases):
    """One case per document and options, under the first name it met."""
    seen, kept = set(), []
    for case in cases:
        key = json.dumps(
            {k: v for k, v in case.items() if k != "name"}, sort_keys=True, ensure_ascii=False
        )
        if key not in seen:
            seen.add(key)
            kept.append(case)
    return kept


def written(output, cases):
    rendered = [{**case, **RENDERS[output](case)} for case in unique(cases)]
    payload = {"inkletter": version("inkletter"), "cases": rendered}
    return json.dumps(payload, ensure_ascii=False, indent=1) + "\n", len(rendered)


def main():
    check = "--check" in sys.argv[1:]
    cases = collected()
    stale = []
    for output in OUTPUTS:
        path = PARITY / f"{output}.json"
        text, count = written(output, cases[output])
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path.name)
        else:
            path.write_text(text, encoding="utf-8")
            print(f"{path.relative_to(ROOT)}: {count} cases")
    if stale:
        sys.exit(f"out of date, rerun scripts/parity.py: {', '.join(stale)}")


if __name__ == "__main__":
    main()
