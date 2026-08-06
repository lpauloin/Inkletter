from jinja2 import Environment, FileSystemLoader

from inkletter.cli import TEMPLATES_DIR


def render_preview(markdown_text, mjml="<mjml/>", html="<p>x</p>"):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    return env.get_template("preview.html").render(
        MD_CONTENT=markdown_text,
        MJML_CONTENT=mjml,
        HTML_CONTENT=html,
    )


def test_markdown_content_is_escaped():
    rendered = render_preview("Un <script>alert(1)</script> et du **gras**")

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_mjml_content_is_escaped():
    rendered = render_preview("x", mjml="<mj-text>a & b</mj-text>")

    assert "&lt;mj-text&gt;a &amp; b&lt;/mj-text&gt;" in rendered


def test_preview_survives_without_the_highlight_cdn():
    # offline, hljs is undefined: the script must not die before
    # injecting the rendered email into the iframe
    rendered = render_preview("x")

    assert "if (window.hljs) hljs.highlightAll();" in rendered
    assert "iframe.srcdoc = htmlContent;" in rendered
