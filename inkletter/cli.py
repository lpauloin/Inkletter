from pathlib import Path
import tempfile
import webbrowser

import click
from jinja2 import Environment, FileSystemLoader

from inkletter.md_to_html import parse_markdown_to_html, parse_mjml_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml
from inkletter.theme import THEMES, Theme, ThemeError

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

@click.group()
def cli():
    """Inkletter CLI — Convert and preview Markdown as MJML"""
    pass


def conversion_options(command):
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
    command = click.option(
        "--no-theme", is_flag=True, help="Generate bare MJML without any theme."
    )(command)
    return command


def load_theme(theme_name: str | None, no_theme: bool) -> Theme | None:
    if no_theme:
        return None
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
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", encoding="utf-8", delete=False
    ) as f:
        f.write(content)
        return Path(f.name)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, writable=True, path_type=Path), help="Output HTML file path")
@theme_options
@conversion_options
def preview(
    filepath: Path,
    output: Path | None,
    theme_name: str | None,
    no_theme: bool,
    no_bold_link_button: bool,
):
    """
    Convert a Markdown file into MJML, then into HTML, and preview it in a browser.
    """
    theme = load_theme(theme_name, no_theme)
    try:
        # Load Markdown
        markdown_text = filepath.read_text(encoding="utf-8")

        # Markdown → MJML
        mjml_code = parse_markdown_to_mjml(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
        )

        # MJML → HTML
        html_output = parse_mjml_to_html(mjml_code)

        # Render with Jinja2
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("preview.html")
        rendered = template.render(
            MD_CONTENT=markdown_text,
            MJML_CONTENT=mjml_code,
            HTML_CONTENT=html_output,
        )
    except Exception as e:
        raise click.ClickException(str(e))

    out_path = write_output(rendered, output)

    webbrowser.open(out_path.resolve().as_uri())

    click.secho(f"✅ Preview opened in browser:\n{out_path}", fg="green")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, writable=True, path_type=Path), help="Output MJML file path")
@theme_options
@conversion_options
def md2mjml(
    filepath: Path,
    output: Path | None,
    theme_name: str | None,
    no_theme: bool,
    no_bold_link_button: bool,
):
    """Convert Markdown to MJML, print it or save it to a file."""
    theme = load_theme(theme_name, no_theme)
    try:
        markdown_text = filepath.read_text(encoding="utf-8")
        mjml_code = parse_markdown_to_mjml(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
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
@click.option("-o", "--output", type=click.Path(dir_okay=False, writable=True, path_type=Path), help="Output HTML file path")
@click.option("--view/--no-view", default=False, help="Open the result in a browser (default: false)")
@theme_options
@conversion_options
def md2html(
    filepath: Path,
    output: Path | None,
    view: bool,
    theme_name: str | None,
    no_theme: bool,
    no_bold_link_button: bool,
):
    """Convert Markdown to HTML, optionally save and open it."""
    theme = load_theme(theme_name, no_theme)
    try:
        markdown_text = filepath.read_text(encoding="utf-8")
        html_output = parse_markdown_to_html(
            markdown_text,
            theme=theme,
            bold_link_is_button=not no_bold_link_button,
        )
    except Exception as e:
        raise click.ClickException(str(e))

    out_path = write_output(html_output, output)

    click.secho(f"✅ HTML written to: {out_path}", fg="green")

    if view:
        webbrowser.open(out_path.resolve().as_uri())
