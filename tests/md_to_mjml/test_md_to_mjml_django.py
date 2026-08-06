from inkletter.django_tags import TagMask
from inkletter.md_to_html import parse_markdown_to_html
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body

# The real-world shape: one source, a transactional email whose content
# depends on the recipient. Snapshotted here, rendered for real by
# tests/test_django_rendering.py.
PARCEL_UPDATE = """\
# Your parcel is on its way

---

Hi {{ customer.first_name|default:'there' }},

Parcel {{ tracking_number }} left the warehouse, {% if express %}and lands tomorrow{% else %}and lands within three working days{% endif %}.

{% if signature_required %}

Someone has to sign for this one, so make sure a human is around when the courier knocks.

**[Reschedule the delivery]({% url 'delivery' %}#reschedule)**

{% else %}

Nobody home? The courier leaves it in your safe place and drops a card through the door.

**[Track your parcel]({{ tracking_url }})**

{% endif %}

Happy unboxing,
The logistics crew.
"""


def mjml(markdown):
    return parse_markdown_to_mjml(markdown, django_tags=True)


# --- The three corruptions, cured ---


def test_variable_in_a_link_href():
    actual = mjml("[a]({{ url }})")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <a href="{{ url }}">a</a>
</mj-text>""")
    assert actual == expected
    assert "%7B" not in actual


def test_statement_is_not_html_escaped():
    actual = mjml("{% if a < b %}yes{% endif %}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  {% if a < b %}yes{% endif %}
</mj-text>""")
    assert actual == expected


def test_url_statement_in_href_keeps_its_quotes():
    # the codegen escapes attribute values with quote=True, which would
    # turn ' into &#x27; and break the tag: the mask dodges it
    actual = mjml("[Confirm]({% url 'confirm' token %})")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <a href="{% url 'confirm' token %}">Confirm</a>
</mj-text>""")
    assert actual == expected
    assert "&#x27;" not in actual


def test_static_tag_in_image_src():
    actual = mjml("![Logo]({% static 'img/logo.png' %})")
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="{% static \'img/logo.png\' %}" alt="Logo"/>'
    )
    assert actual == expected


def test_tag_in_the_alt_attribute():
    actual = mjml("![{{ name }} logo](https://x.com/l.png)")
    print(actual)
    expected = wrap_mjml_body(
        '<mj-image src="https://x.com/l.png" alt="{{ name }} logo"/>'
    )
    assert actual == expected


# --- Flow control ---


def test_statement_becomes_a_raw_band():
    actual = mjml("Before.\n\n{% if paid %}\n\nInside.\n\n{% endif %}\n\nAfter.")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  Before.
</mj-text>
<mj-raw>
  {% if paid %}
</mj-raw>
<mj-text>
  Inside.
</mj-text>
<mj-raw>
  {% endif %}
</mj-raw>
<mj-text>
  After.
</mj-text>""")
    assert actual == expected


def test_conditional_around_a_button():
    actual = mjml("{% if paid %}\n\n**[Go]({{ url }})**\n\n{% endif %}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-raw>
  {% if paid %}
</mj-raw>
<mj-button href="{{ url }}">Go</mj-button>
<mj-raw>
  {% endif %}
</mj-raw>""")
    assert actual == expected


def test_button_with_tagged_label_and_href():
    actual = mjml("**[{{ label }}]({{ url }})**")
    print(actual)
    expected = wrap_mjml_body('<mj-button href="{{ url }}">{{ label }}</mj-button>')
    assert actual == expected


# --- Every context ---


def test_tag_in_a_heading():
    actual = mjml("# Hello {{ user.name }}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <h1>Hello {{ user.name }}</h1>
</mj-text>""")
    assert actual == expected


def test_tag_in_a_table_cell():
    actual = mjml("| Name |\n|---|\n| {{ item.name }} |")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-table>
  <tr>
    <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">Name</th>
  </tr>
  <tr>
    <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">{{ item.name }}</td>
  </tr>
</mj-table>""")
    assert actual == expected


def test_tag_in_a_list_item():
    actual = mjml("- {{ item.name }}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <ul>
    <li>
      {{ item.name }}
    </li>
  </ul>
</mj-text>""")
    assert actual == expected


def test_tag_in_a_blockquote():
    actual = mjml("> Signed, {{ user.name }}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <blockquote>
    Signed, {{ user.name }}
  </blockquote>
</mj-text>""")
    assert actual == expected


def test_tag_in_a_code_block_stays_literal():
    markdown = "```\n{{ not_rendered }}\n```"
    actual = mjml(markdown)
    print(actual)
    # code is literal for Markdown, so the plugin changes nothing here —
    # whether Django evaluates it at runtime is the author's business
    assert actual == parse_markdown_to_mjml(markdown)


def test_tag_in_a_code_span_stays_literal():
    markdown = "Type `{{ user.name }}` to interpolate."
    actual = mjml(markdown)
    print(actual)
    assert actual == parse_markdown_to_mjml(markdown)


# --- The real-world document ---


def test_parcel_update_document():
    actual = mjml(PARCEL_UPDATE)
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  <h1>Your parcel is on its way</h1>
</mj-text>
<mj-divider border-color="#e5e7eb" border-width="1px"/>
<mj-text>
  Hi {{ customer.first_name|default:'there' }},
</mj-text>
<mj-text>
  Parcel {{ tracking_number }} left the warehouse, {% if express %}and lands tomorrow{% else %}and lands within three working days{% endif %}.
</mj-text>
<mj-raw>
  {% if signature_required %}
</mj-raw>
<mj-text>
  Someone has to sign for this one, so make sure a human is around when the courier knocks.
</mj-text>
<mj-button href="{% url 'delivery' %}#reschedule">Reschedule the delivery</mj-button>
<mj-raw>
  {% else %}
</mj-raw>
<mj-text>
  Nobody home? The courier leaves it in your safe place and drops a card through the door.
</mj-text>
<mj-button href="{{ tracking_url }}">Track your parcel</mj-button>
<mj-raw>
  {% endif %}
</mj-raw>
<mj-text>
  Happy unboxing,<br/>
  The logistics crew.
</mj-text>""")
    assert actual == expected


# --- The mask ---


def test_mask_round_trip_is_exact():
    mask = TagMask()
    hidden = mask.hide("Hi {{ name }}, {% if a < b %}soon{% endif %}")
    print(hidden)
    assert "{{" not in hidden and "<" not in hidden
    assert mask.reveal(hidden) == "Hi {{ name }}, {% if a < b %}soon{% endif %}"


def test_mask_is_a_no_op_without_tags():
    mask = TagMask()
    assert mask.hide("nothing to hide") == "nothing to hide"
    assert mask.reveal("nothing to hide") == "nothing to hide"


def test_mask_index_survives_a_digit_right_after_a_tag():
    # without its terminator the index would read as 05 instead of 0
    mask = TagMask()
    hidden = mask.hide("{{ n }}5 items")
    print(hidden)
    assert mask.reveal(hidden) == "{{ n }}5 items"


def test_mask_steps_aside_when_the_source_holds_its_prefix():
    source = "Order inktag0x for {{ user.name }}"
    mask = TagMask(source)
    assert mask.prefix != "inktag"
    assert mask.reveal(mask.hide(source)) == source


def test_document_holding_the_prefix_is_left_alone():
    # end to end: the author literally wrote what looks like a token
    actual = mjml("Order inktag0x for {{ user.name }}")
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  Order inktag0x for {{ user.name }}
</mj-text>""")
    assert actual == expected


def test_no_token_leaks():
    actual = mjml(PARCEL_UPDATE)
    print(actual)
    assert "inktag" not in actual


# --- Final HTML ---


def test_final_html_keeps_tags_verbatim():
    html = parse_markdown_to_html(PARCEL_UPDATE, django_tags=True)
    assert "{{ customer.first_name|default:'there' }}" in html
    assert "{% if signature_required %}" in html
    assert "href=\"{% url 'delivery' %}#reschedule\"" in html
    assert "%7B" not in html
    assert "&#x27;" not in html
    assert "inktag" not in html


def test_conditional_branches_are_balanced_html():
    # whichever branch Django keeps at runtime, the HTML must stay valid:
    # each conditional fragment has to close everything it opens
    html = parse_markdown_to_html(PARCEL_UPDATE, django_tags=True)
    markers = ["{% if signature_required %}", "{% else %}", "{% endif %}"]
    starts = [html.index(marker) for marker in markers]
    for start, end in zip(starts, starts[1:]):
        fragment = html[start:end]
        assert fragment.count("<table") == fragment.count("</table")
        assert fragment.count("<div") == fragment.count("</div")


def test_html_pipeline_survives_a_lower_than():
    # mjml2html parses its input as XML: an unmasked < inside a tag makes
    # it raise. The tags must never reach it.
    html = parse_markdown_to_html("{% if a < b %}yes{% endif %}", django_tags=True)
    assert "{% if a < b %}yes{% endif %}" in html
