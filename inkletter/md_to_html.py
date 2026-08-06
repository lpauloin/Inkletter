from mjml import mjml2html

from inkletter.md_to_mjml import render_mjml


def parse_mjml_to_html(mjml_text):
    return mjml2html(mjml_text)


def parse_markdown_to_html(
    markdown_text,
    theme=None,
    bold_link_is_button=True,
    url_factory=None,
    django_tags=False,
):
    # compile first, reveal after: Django tags never cross mjml2html
    mjml, mask = render_mjml(
        markdown_text,
        theme=theme,
        bold_link_is_button=bold_link_is_button,
        url_factory=url_factory,
        django_tags=django_tags,
    )
    return mask.reveal(parse_mjml_to_html(mjml))
