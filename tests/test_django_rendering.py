"""The round trip: Markdown source, Django templates, rendered emails.

The other test files check that Inkletter writes the right text. This
one hands that text to Django and checks that the email comes out right
— the only proof that does not rely on our own reading of the template
language. Django is a test-only dependency: Inkletter never imports it.
"""

import subprocess
import sys

import django
import pytest
from django.conf import settings
from django.template import Context, Template
from django.urls import path

if not settings.configured:
    settings.configure(
        ROOT_URLCONF=__name__,
        TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates"}],
    )
    django.setup()

# {% url 'delivery' %} needs somewhere to point to
urlpatterns = [
    path("delivery/", lambda request: None, name="delivery"),
    path("confirm/<token>/", lambda request: None, name="confirm"),
]

from inkletter.md_to_html import parse_markdown_to_html  # noqa: E402
from inkletter.md_to_text import parse_markdown_to_text  # noqa: E402

PARCEL_UPDATE = """\
# Your parcel is on its way

Hi {{ customer.first_name|default:'there' }},

Parcel {{ tracking_number }} left the warehouse, {% if express %}and lands tomorrow{% else %}and lands within three working days{% endif %}.

{% if signature_required %}

Someone has to sign for this one, so make sure a human is around when the courier knocks.

**[Reschedule the delivery]({% url 'delivery' %}#reschedule)**

{% else %}

Nobody home? The courier leaves it in your safe place and drops a card through the door.

**[Track your parcel]({% url 'delivery' %})**

{% endif %}

Happy unboxing,
The logistics crew.
"""

SIGNED_FOR = {
    "customer": {"first_name": "Iris"},
    "tracking_number": "TR-4821",
    "express": True,
    "signature_required": True,
}
LEAVE_SAFE = {
    "customer": {},
    "tracking_number": "TR-7390",
    "express": False,
    "signature_required": False,
}

# Both outputs are built from the same source and sent together in the
# multipart email: every test that can run on both, runs on both.
BUILDERS = {"html": parse_markdown_to_html, "text": parse_markdown_to_text}


def build(output, markdown):
    """The Django template Inkletter produces for this output."""
    return BUILDERS[output](markdown, django_tags=True)


def render(output, markdown, context):
    return Template(build(output, markdown)).render(Context(context))


both_outputs = pytest.mark.parametrize("output", list(BUILDERS))


# --- The output is a Django template ---


@both_outputs
def test_output_compiles_as_a_django_template(output):
    template = build(output, PARCEL_UPDATE)
    print(template)
    Template(template)  # raises TemplateSyntaxError if we mangled a tag


@both_outputs
def test_variables_are_substituted(output):
    rendered = render(output, "Hi {{ customer.first_name }},", SIGNED_FOR)
    print(rendered)
    assert "Iris" in rendered


@both_outputs
def test_quoted_filter_argument_survives(output):
    # if the codegen had escaped the quotes into &#x27;, Django would
    # either raise here or hand back the literal default
    rendered = render(output, "Hi {{ customer.first_name|default:'there' }},", LEAVE_SAFE)
    print(rendered)
    assert "there" in rendered
    assert "&#x27;" not in rendered


@both_outputs
def test_url_tag_resolves(output):
    rendered = render(output, "**[Confirm]({% url 'confirm' 'abc' %})**", {})
    print(rendered)
    assert "/confirm/abc/" in rendered


@both_outputs
def test_conditional_selects_the_right_branch(output):
    signed = render(output, PARCEL_UPDATE, SIGNED_FOR)
    left_safe = render(output, PARCEL_UPDATE, LEAVE_SAFE)
    print(signed)
    print(left_safe)
    assert "has to sign for this one" in signed
    assert "has to sign for this one" not in left_safe
    assert "safe place" in left_safe
    assert "safe place" not in signed


@both_outputs
def test_no_template_syntax_left(output):
    for context in (SIGNED_FOR, LEAVE_SAFE):
        rendered = render(output, PARCEL_UPDATE, context)
        print(rendered)
        assert "{{" not in rendered
        assert "{%" not in rendered
        assert "inktag" not in rendered


# --- The email itself ---


@pytest.mark.parametrize("context", [SIGNED_FOR, LEAVE_SAFE])
def test_rendered_html_is_balanced(context):
    # whichever branch Django keeps, the email must still be valid HTML:
    # a conditional that swallowed half a table would wreck the layout
    rendered = render("html", PARCEL_UPDATE, context)
    print(rendered)
    assert rendered.count("<table") == rendered.count("</table")
    assert rendered.count("<div") == rendered.count("</div")
    assert rendered.count("<tr") == rendered.count("</tr")


@both_outputs
def test_loop_over_a_whole_table_repeats_rows(output):
    markdown = (
        "{% for item in items %}\n\n"
        "| Item | Qty |\n|---|---|\n| {{ item.name }} | {{ item.qty }} |\n\n"
        "{% endfor %}"
    )
    context = {
        "items": [
            {"name": "Alpha", "qty": 1},
            {"name": "Beta", "qty": 2},
            {"name": "Gamma", "qty": 3},
        ]
    }
    rendered = render(output, markdown, context)
    print(rendered)
    for name in ("Alpha", "Beta", "Gamma"):
        assert name in rendered


def test_autoescape_off_keeps_text_readable():
    # Django escapes for HTML even in a .txt template: without the tag,
    # an ampersand in the data reaches the reader as &amp;
    company = {"company": "Ben & Jerry"}
    escaped = render("text", "Sent by {{ company }}.", company)
    print(escaped)
    assert "Ben &amp; Jerry" in escaped

    readable = render(
        "text",
        "{% autoescape off %}\n\nSent by {{ company }}.\n\n{% endautoescape %}",
        company,
    )
    print(readable)
    assert "Ben & Jerry" in readable


def test_image_source_resolves():
    rendered = render("html", "![Logo]({{ logo_url }})", {"logo_url": "https://x/l.png"})
    print(rendered)
    assert 'src="https://x/l.png"' in rendered


@both_outputs
def test_button_href_resolves(output):
    rendered = render(output, "**[Go]({{ target }})**", {"target": "https://x.com/go"})
    print(rendered)
    assert "https://x.com/go" in rendered


@both_outputs
def test_quota_alert_document_renders(output):
    rendered = render(output, PARCEL_UPDATE, SIGNED_FOR)
    print(rendered)
    assert "Iris" in rendered
    assert "TR-4821" in rendered
    assert "/delivery/#reschedule" in rendered
    assert "The logistics crew." in rendered


def test_both_outputs_agree_on_content():
    # the pair travels together in the multipart email: the reader must
    # get the same message whichever part their client shows
    html = render("html", PARCEL_UPDATE, SIGNED_FOR)
    text = render("text", PARCEL_UPDATE, SIGNED_FOR)
    print(html)
    print(text)
    for value in (
        "Iris",
        "TR-4821",
        "/delivery/#reschedule",
        "has to sign for this one",
    ):
        assert value in html
        assert value in text


# --- Django stays out of the runtime ---


def test_inkletter_does_not_import_django():
    code = "import inkletter, sys; print('django' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    print(result.stdout)
    assert result.stdout.strip() == "False"
