from inkletter.md_to_text import parse_markdown_to_text
from inkletter.shortener import URLFactory


class PrefixFactory(URLFactory):
    def rewrite_link(self, url):
        return f"https://short.test/?u={url}"


def test_rewritten_links_reach_the_text():
    actual = parse_markdown_to_text(
        "Visit [the site](https://example.com).", url_factory=PrefixFactory()
    )
    print(actual)
    assert actual == "Visit the site <https://short.test/?u=https://example.com>.\n"


def test_rewritten_button_href_reaches_the_text():
    # same pass-ordering invariant as SPEC-URLS: the Button inherits the
    # already rewritten Link href
    actual = parse_markdown_to_text(
        "**[Go](https://example.com/go)**", url_factory=PrefixFactory()
    )
    print(actual)
    assert actual == "→ Go : https://short.test/?u=https://example.com/go\n"
