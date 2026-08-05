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
