from pathlib import Path
import html
import json
import re
import tempfile
import webbrowser

import click

from inkletter.md_to_html import parse_markdown_to_html, parse_mjml_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.md_to_text import parse_markdown_to_text
from inkletter.exceptions import ThemeError
from inkletter.theme import THEMES, Theme

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

#: The named slots of the preview page. Substituted in one pass, so a
#: value holding the text of another slot is never itself substituted.
PREVIEW_SLOTS = re.compile(r"\{\{ (MD_CONTENT|MJML_CONTENT|HTML_CONTENT) \}\}")


def render_preview(markdown_text, mjml_code, html_output):
    """Fill the three slots of the preview page.

    Three substitutions in one static page never needed a templating
    engine. The two code panes are HTML-escaped; the email itself goes
    into a JavaScript string, so it is JSON-encoded with < > & escaped
    on top — an email holding </script> would otherwise end the block
    early. That last part is what the tojson filter used to do here.
    """
    page = (TEMPLATES_DIR / "preview.html").read_text(encoding="utf-8")
    embedded = json.dumps(html_output)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        embedded = embedded.replace(char, escape)
    values = {
        "MD_CONTENT": html.escape(markdown_text),
        "MJML_CONTENT": html.escape(mjml_code),
        "HTML_CONTENT": embedded,
    }
    return PREVIEW_SLOTS.sub(lambda match: values[match.group(1)], page)


@click.group()
def cli():
    """Inkletter CLI — Convert and preview Markdown as MJML"""
    pass


def conversion_options(command):
    command = click.option(
        "--no-link-attributes",
        "no_link_attributes",
        is_flag=True,
        help="Treat {width=96px} after an image as plain text instead of an attribute.",
    )(command)
    command = click.option(
        "--no-bold-link-button",
        "no_bold_link_button",
        is_flag=True,
        help="Keep lone bold links as links instead of turning them into buttons.",
    )(command)
    return command


def theme_options(command):
    command = click.option(
        "-t",
        "--theme",
        "theme_name",
        metavar="NAME_OR_FILE",
        help=f"Theme preset ({', '.join(sorted(THEMES))}) or path to a .toml theme file.",
    )(command)
    return command


def load_theme(theme_name: str | None) -> Theme:
    if theme_name is None:
        return Theme()
    try:
        path = Path(theme_name)
        if path.suffix == ".toml" or path.exists():
            return Theme.from_toml(path)
        return Theme.named(theme_name)
    except ThemeError as e:
        raise click.ClickException(str(e))


def write_output(content: str, output: Path | None) -> Path:
    """Write content to the given path, or to a temp file if none is given."""
    if output:
        output.write_text(content, encoding="utf-8")
        return output
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as f:
        f.write(content)
        return Path(f.name)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output HTML file path",
)
@theme_options
@conversion_options
def preview(
    filepath: Path,
    output: Path | None,
    theme_name: str | None,
    no_bold_link_button: bool,
    no_link_attributes: bool,
):
    """
    Convert a Markdown file into MJML, then into HTML, and preview it in a browser.
    """
    theme = load_theme(theme_name)
    try:
        # Load Markdown
        markdown_text = filepath.read_text(encoding="utf-8")

        mjml_code = parse_markdown_to_mjml(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
            link_attributes=not no_link_attributes,
        )
        html_output = parse_mjml_to_html(mjml_code)

        rendered = render_preview(markdown_text, mjml_code, html_output)
    except Exception as e:
        raise click.ClickException(str(e))

    out_path = write_output(rendered, output)

    webbrowser.open(out_path.resolve().as_uri())

    click.secho(f"✅ Preview opened in browser:\n{out_path}", fg="green")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output MJML file path",
)
@theme_options
@conversion_options
def md2mjml(
    filepath: Path,
    output: Path | None,
    theme_name: str | None,
    no_bold_link_button: bool,
    no_link_attributes: bool,
):
    """Convert Markdown to MJML, print it or save it to a file."""
    theme = load_theme(theme_name)
    try:
        markdown_text = filepath.read_text(encoding="utf-8")
        mjml_code = parse_markdown_to_mjml(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
            link_attributes=not no_link_attributes,
        )
    except Exception as e:
        raise click.ClickException(str(e))

    if output:
        output.write_text(mjml_code, encoding="utf-8")
        click.secho(f"✅ MJML written to: {output}", fg="green")
    else:
        click.echo(mjml_code)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output HTML file path",
)
@click.option(
    "--view/--no-view",
    default=False,
    help="Open the result in a browser (default: false)",
)
@theme_options
@conversion_options
def md2html(
    filepath: Path,
    output: Path | None,
    view: bool,
    theme_name: str | None,
    no_bold_link_button: bool,
    no_link_attributes: bool,
):
    """Convert Markdown to HTML, optionally save and open it."""
    theme = load_theme(theme_name)
    try:
        markdown_text = filepath.read_text(encoding="utf-8")
        html_output = parse_markdown_to_html(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
            link_attributes=not no_link_attributes,
        )
    except Exception as e:
        raise click.ClickException(str(e))

    out_path = write_output(html_output, output)

    click.secho(f"✅ HTML written to: {out_path}", fg="green")

    if view:
        webbrowser.open(out_path.resolve().as_uri())


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output text file path",
)
@conversion_options
def md2txt(
    filepath: Path,
    output: Path | None,
    no_bold_link_button: bool,
    no_link_attributes: bool,
):
    """Convert Markdown to the plain-text email alternative."""
    try:
        markdown_text = filepath.read_text(encoding="utf-8")
        text = parse_markdown_to_text(
            markdown_text,
            bold_link_is_button=not no_bold_link_button,
            link_attributes=not no_link_attributes,
        )
    except Exception as e:
        raise click.ClickException(str(e))

    if output:
        output.write_text(text, encoding="utf-8")
        click.secho(f"✅ Text written to: {output}", fg="green")
    else:
        click.echo(text, nl=False)
