import pytest

from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body
from inkletter.shortener import URLFactory


class PrefixFactory(URLFactory):
    """Test factory rewriting both kinds with distinct prefixes."""

    def rewrite_link(self, url):
        return f"https://short.test/?u={url}"

    def rewrite_image(self, url):
        return f"https://img.test/?u={url}"


class LinkOnlyFactory(URLFactory):
    def rewrite_link(self, url):
        return f"https://short.test/?u={url}"


# --- Defaults ---


def test_no_factory_output_is_unchanged():
    markdown = "Un [lien](https://x.com) et ![img](https://x.com/i.png)"
    assert parse_markdown_to_mjml(markdown) == parse_markdown_to_mjml(markdown, url_factory=None)


def test_base_factory_is_identity():
    markdown = "Un [lien](https://x.com) et une image :\n\n![img](https://x.com/i.png)"
    assert parse_markdown_to_mjml(markdown) == parse_markdown_to_mjml(
        markdown, url_factory=URLFactory()
    )


# --- Both kinds rewritten ---


def test_links_and_images_are_rewritten():
    markdown = "Un [lien](https://x.com/page)\n\n![img](https://x.com/i.png)"
    actual = parse_markdown_to_mjml(markdown, url_factory=PrefixFactory())
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  Un <a href="https://short.test/?u=https://x.com/page">lien</a>
</mj-text>
<mj-image src="https://img.test/?u=https://x.com/i.png" alt="img"/>""")
    assert actual == expected


def test_image_link_rewrites_both_fields():
    actual = parse_markdown_to_mjml(
        "[![alt](https://x.com/i.png)](https://x.com/page)",
        url_factory=PrefixFactory(),
    )
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="https://img.test/?u=https://x.com/i.png"'
        ' href="https://short.test/?u=https://x.com/page" alt="alt"/>'
    )
    assert actual == expected


def test_link_only_factory_leaves_images_untouched():
    markdown = "Un [lien](https://x.com/page)\n\n![img](https://x.com/i.png)"
    actual = parse_markdown_to_mjml(markdown, url_factory=LinkOnlyFactory())
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  Un <a href="https://short.test/?u=https://x.com/page">lien</a>
</mj-text>
<mj-image src="https://x.com/i.png" alt="img"/>""")
    assert actual == expected


# --- Full scope: nested contexts and layout conventions ---


def test_urls_rewritten_in_every_context():
    markdown = (
        "# Un [titre](https://x.com/h)\n\n"
        "- [item](https://x.com/li) ![ico](https://x.com/li.png)\n\n"
        "> [cite](https://x.com/q)\n\n"
        "| [cell](https://x.com/td) |\n|---|\n| ![t](https://x.com/td.png) |\n\n"
        "![a](https://x.com/a.png) ![b](https://x.com/b.png)\n\n"
        "![J](https://x.com/j.png) Un média-objet."
    )
    actual = parse_markdown_to_mjml(markdown, url_factory=PrefixFactory())
    print(actual)
    assert "https://x.com/h" not in actual.replace("https://short.test/?u=https://x.com/h", "")
    for original in ("h", "li", "q", "td"):
        assert f"https://short.test/?u=https://x.com/{original}" in actual
    for original in ("li.png", "td.png", "a.png", "b.png", "j.png"):
        assert f"https://img.test/?u=https://x.com/{original}" in actual


# --- Buttons: the pass-ordering invariant ---


def test_button_href_is_rewritten():
    actual = parse_markdown_to_mjml("**[Go](https://x.com/go)**", url_factory=PrefixFactory())
    print(actual)
    expected = wrap_mjml_body(
        '<mj-button href="https://short.test/?u=https://x.com/go">Go</mj-button>'
    )
    assert actual == expected


def test_button_href_is_rewritten_in_final_html():
    html = parse_markdown_to_html("**[Go](https://x.com/go)**", url_factory=PrefixFactory())
    assert 'href="https://short.test/?u=https://x.com/go"' in html


def test_bold_link_without_button_is_rewritten_too():
    actual = parse_markdown_to_mjml(
        "**[Go](https://x.com/go)**",
        url_factory=PrefixFactory(),
        bold_link_is_button=False,
    )
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <strong><a href="https://short.test/?u=https://x.com/go">Go</a></strong>
</mj-text>""")
    assert actual == expected


# --- Escaping interaction ---


def test_rewritten_url_with_ampersand_is_escaped():
    class UTMFactory(URLFactory):
        def rewrite_link(self, url):
            return f"{url}?utm_source=news&utm_medium=email"

    actual = parse_markdown_to_mjml("[lien](https://x.com/page)", url_factory=UTMFactory())
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <a href="https://x.com/page?utm_source=news&amp;utm_medium=email">lien</a>
</mj-text>""")
    assert actual == expected


# --- Errors ---


def test_non_str_return_raises_a_named_typeerror():
    class Broken(URLFactory):
        def rewrite_link(self, url):
            return None

    with pytest.raises(TypeError, match=r"Broken\.rewrite_link returned None"):
        parse_markdown_to_mjml("[x](https://x.com)", url_factory=Broken())


def test_factory_exceptions_propagate():
    class Failing(URLFactory):
        def rewrite_link(self, url):
            raise RuntimeError("quota exceeded")

    with pytest.raises(RuntimeError, match="quota exceeded"):
        parse_markdown_to_mjml("[x](https://x.com)", url_factory=Failing())


# --- A spy, to prove the factory is called and with what ---


class SpyFactory(URLFactory):
    """Records its calls: an unchanged URL would not prove anything on
    its own, since a factory may well return what it was given."""

    def __init__(self):
        self.links = []
        self.images = []

    def rewrite_link(self, url):
        self.links.append(url)
        return f"https://short.test/?u={url}"

    def rewrite_image(self, url):
        self.images.append(url)
        return f"https://img.test/?u={url}"
