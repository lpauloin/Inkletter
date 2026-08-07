from inkletter.cli import render_preview


def preview(markdown_text, mjml="<mjml/>", html="<p>x</p>"):
    return render_preview(markdown_text, mjml, html)


def test_markdown_content_is_escaped():
    rendered = preview("Un <script>alert(1)</script> et du **gras**")

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_mjml_content_is_escaped():
    rendered = preview("x", mjml="<mj-text>a & b</mj-text>")

    assert "&lt;mj-text&gt;a &amp; b&lt;/mj-text&gt;" in rendered


def test_the_email_is_embedded_as_a_javascript_string():
    rendered = preview("x", html="<p>hi</p>")

    assert 'const htmlContent = "\\u003cp\\u003ehi\\u003c/p\\u003e";' in rendered


def test_an_email_holding_a_script_tag_cannot_end_the_block():
    # a literal </script> in the string would close the <script> block
    # early and spill the rest of the email into the page
    rendered = preview("x", html="<script>bad()</script>")
    embedded = rendered.split("const htmlContent = ")[1].split("\n")[0]

    assert "</script>" not in embedded
    assert "\\u003c/script\\u003e" in embedded


def test_a_slot_name_in_the_content_is_not_substituted():
    # one pass over the page: what lands in a slot is never re-scanned
    rendered = preview("{{ HTML_CONTENT }}")

    assert "{{ HTML_CONTENT }}" in rendered  # the markdown pane, verbatim
    assert rendered.count("const htmlContent") == 1


def test_preview_survives_without_the_highlight_cdn():
    # offline, hljs is undefined: the script must not die before
    # injecting the rendered email into the iframe
    rendered = preview("x")

    assert "if (window.hljs) hljs.highlightAll();" in rendered
    assert "iframe.srcdoc = htmlContent;" in rendered
