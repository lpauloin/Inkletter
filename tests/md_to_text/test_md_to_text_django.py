from inkletter.md_to_text import parse_markdown_to_text

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


def text(markdown):
    return parse_markdown_to_text(markdown, django_tags=True)


def test_variable_in_a_paragraph():
    actual = text("Hi {{ customer.first_name }},")
    print(actual)
    assert actual == "Hi {{ customer.first_name }},\n"


def test_tag_in_h1_is_left_alone():
    # nothing rewrites the rendered line, so a tag in a title stays the
    # tag it was: {{ CUSTOMER.NAME }} would not be the same variable
    actual = text("# Hi {{ customer.name }}")
    print(actual)
    assert actual == "Hi {{ customer.name }}\n======================\n"


def test_h1_underline_matches_the_rendered_width():
    actual = text("# {{ greeting }}")
    print(actual)
    assert actual == "{{ greeting }}\n==============\n"


def test_statement_is_its_own_line():
    actual = text("Before.\n\n{% if express %}\n\nInside.\n\n{% endif %}")
    print(actual)
    assert actual == "Before.\n\n{% if express %}\n\nInside.\n\n{% endif %}\n"


def test_tag_in_a_table_cell_drives_the_column_width():
    actual = text("| Item | Qty |\n|---|---|\n| {{ item.name }} | {{ n }} |")
    print(actual)
    assert actual == """\
Item            | Qty
----------------+--------
{{ item.name }} | {{ n }}
"""


def test_button_with_a_tagged_href():
    actual = text("**[Track]({% url 'delivery' %})**")
    print(actual)
    assert actual == "→ Track : {% url 'delivery' %}\n"


def test_link_with_a_tagged_href():
    actual = text("Read [the delivery terms]({{ terms_url }}).")
    print(actual)
    assert actual == "Read the delivery terms <{{ terms_url }}>.\n"


def test_no_escaping_at_all():
    actual = text("{% if a < b %}yes{% endif %}")
    print(actual)
    assert actual == "{% if a < b %}yes{% endif %}\n"


def test_parcel_update_document():
    actual = text(PARCEL_UPDATE)
    print(actual)
    assert actual == """\
Your parcel is on its way
=========================

----------------------------------------

Hi {{ customer.first_name|default:'there' }},

Parcel {{ tracking_number }} left the warehouse, {% if express %}and lands tomorrow{% else %}and lands within three working days{% endif %}.

{% if signature_required %}

Someone has to sign for this one, so make sure a human is around when the courier knocks.

→ Reschedule the delivery : {% url 'delivery' %}#reschedule

{% else %}

Nobody home? The courier leaves it in your safe place and drops a card through the door.

→ Track your parcel : {{ tracking_url }}

{% endif %}

Happy unboxing,
The logistics crew.
"""
