from click.testing import CliRunner

import inkletter.cli as cli_module
from inkletter.cli import cli


def test_md2mjml_prints_to_stdout(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello **world**", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md)])

    assert result.exit_code == 0
    assert result.output.startswith("<mjml>")
    assert "<strong>world</strong>" in result.output


def test_md2mjml_writes_output_file(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("# Title", encoding="utf-8")
    out = tmp_path / "out.mjml"

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "-o", str(out)])

    assert result.exit_code == 0
    content = out.read_text(encoding="utf-8")
    assert content.startswith("<mjml>")
    assert "<h1>Title</h1>" in content


def test_md2html_writes_output_file(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello **world**", encoding="utf-8")
    out = tmp_path / "out.html"

    result = CliRunner().invoke(cli, ["md2html", str(md), "-o", str(out)])

    assert result.exit_code == 0
    content = out.read_text(encoding="utf-8")
    assert "<strong>world</strong>" in content
    assert "<mjml>" not in content


def test_md2mjml_missing_input_fails():
    result = CliRunner().invoke(cli, ["md2mjml", "/nonexistent/input.md"])

    assert result.exit_code != 0


def test_md2mjml_conversion_error_sets_exit_code(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(cli_module, "parse_markdown_to_mjml", boom)
    md = tmp_path / "in.md"
    md.write_text("text", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md)])

    assert result.exit_code != 0
    assert "boom" in result.output


def test_md2html_conversion_error_sets_exit_code(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(cli_module, "parse_markdown_to_html", boom)
    md = tmp_path / "in.md"
    md.write_text("text", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2html", str(md)])

    assert result.exit_code != 0
    assert "boom" in result.output


# --- Themes ---


def test_md2mjml_is_themed_by_default(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md)])

    assert result.exit_code == 0
    assert "<mj-head>" in result.output


def test_md2mjml_no_theme(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "--no-theme"])

    assert result.exit_code == 0
    assert "<mj-head>" not in result.output


def test_md2mjml_theme_preset(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "--theme", "dark"])

    assert result.exit_code == 0
    assert 'background-color="#0f172a"' in result.output


def test_md2mjml_theme_file(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")
    toml = tmp_path / "theme.toml"
    toml.write_text('[layout]\nwidth = "640px"\n', encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "--theme", str(toml)])

    assert result.exit_code == 0
    assert '<mj-body width="640px"' in result.output


def test_md2mjml_unknown_theme_fails_and_lists_presets(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "--theme", "nope"])

    assert result.exit_code != 0
    assert "dark" in result.output  # the error lists the available presets


def test_md2mjml_invalid_theme_file_fails(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("Hello", encoding="utf-8")
    toml = tmp_path / "theme.toml"
    toml.write_text('[links]\ncolour = "#fff"\n', encoding="utf-8")

    result = CliRunner().invoke(cli, ["md2mjml", str(md), "--theme", str(toml)])

    assert result.exit_code != 0
    assert "unknown key" in result.output


def test_md2html_theme_preset(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("A [link](https://x.com)", encoding="utf-8")
    out = tmp_path / "out.html"

    result = CliRunner().invoke(
        cli, ["md2html", str(md), "-o", str(out), "--theme", "red"]
    )

    assert result.exit_code == 0
    assert "#b91c1c" in out.read_text(encoding="utf-8")  # Red.DARK link color


def test_md2mjml_no_bold_link_button(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("**[Go](https://x.com)**", encoding="utf-8")

    with_button = CliRunner().invoke(cli, ["md2mjml", str(md), "--no-theme"])
    without = CliRunner().invoke(
        cli, ["md2mjml", str(md), "--no-theme", "--no-bold-link-button"]
    )

    assert with_button.exit_code == 0 and without.exit_code == 0
    assert "<mj-button" in with_button.output
    assert "<mj-button" not in without.output
    assert "<strong><a" in without.output
