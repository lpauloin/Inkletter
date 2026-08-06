from inkletter.ast import *
from inkletter.visitors.tree import TreeVisitor, print_tree


def inlines(doc):
    """The inline nodes of a one-paragraph document."""
    return doc.children[0].children[0].children


# --- Inline tags ---


def test_variable_is_one_node(ast):
    doc = ast("Hello {{ user.name }}!", django_tags=True)
    print_tree(doc)
    text, tag, mark = inlines(doc)
    assert isinstance(text, LiteralText) and text.value == "Hello "
    assert isinstance(tag, TemplateTag) and tag.raw == "{{ user.name }}"
    assert isinstance(mark, LiteralText) and mark.value == "!"


def test_variable_wins_over_emphasis(ast):
    doc = ast("{{p*2*x}} and {{q*3*y}}", django_tags=True)
    print_tree(doc)
    first, _, second = inlines(doc)
    assert first.raw == "{{p*2*x}}"
    assert second.raw == "{{q*3*y}}"
    assert not any(isinstance(node, Emphasis) for node in inlines(doc))


def test_quoted_filter_argument_is_opaque(ast):
    doc = ast('Sent {{ date|date:"d/m/Y" }}', django_tags=True)
    print_tree(doc)
    assert inlines(doc)[1].raw == '{{ date|date:"d/m/Y" }}'


def test_inline_statement_keeps_the_lower_than(ast):
    doc = ast("{% if a < b %}yes{% endif %}", django_tags=True)
    print_tree(doc)
    opening, text, closing = inlines(doc)
    # a statement in the flow of a sentence stays inline: it must not be
    # mistaken for a block, and the < must survive
    assert isinstance(opening, TemplateTag) and opening.raw == "{% if a < b %}"
    assert isinstance(text, LiteralText) and text.value == "yes"
    assert isinstance(closing, TemplateTag) and closing.raw == "{% endif %}"


def test_inline_comment_tag(ast):
    doc = ast("a {# note #} b", django_tags=True)
    print_tree(doc)
    assert inlines(doc)[1].raw == "{# note #}"


def test_tag_glued_to_text(ast):
    doc = ast("hour{{ x|pluralize }}", django_tags=True)
    print_tree(doc)
    text, tag = inlines(doc)
    assert text.value == "hour"
    assert tag.raw == "{{ x|pluralize }}"


def test_code_span_wins_over_tag(ast):
    doc = ast("`{{ raw }}`", django_tags=True)
    print_tree(doc)
    (span,) = inlines(doc)
    assert isinstance(span, CodeSpan) and span.code == "{{ raw }}"


def test_unclosed_delimiter_stays_text(ast):
    doc = ast("Prices in {{ dollars", django_tags=True)
    print_tree(doc)
    (text,) = inlines(doc)
    assert isinstance(text, LiteralText) and text.value == "Prices in {{ dollars"


def test_entities_decode_around_tags_but_not_inside(ast):
    doc = ast("AT&amp;T {{ a &amp; b }}", django_tags=True)
    print_tree(doc)
    text, tag = inlines(doc)
    assert text.value == "AT&T "
    assert tag.raw == "{{ a &amp; b }}"


# --- Links and images ---


def test_link_with_a_spaced_variable_destination(ast):
    doc = ast("[a]({{ url }})", django_tags=True)
    print_tree(doc)
    (link,) = inlines(doc)
    assert isinstance(link, Link) and link.href == "{{ url }}"


def test_link_with_a_url_statement_destination(ast):
    doc = ast("[Confirm]({% url 'confirm' token %})", django_tags=True)
    print_tree(doc)
    (link,) = inlines(doc)
    assert link.href == "{% url 'confirm' token %}"


def test_link_destination_mixing_text_and_tags(ast):
    doc = ast('[a]({{base}}/p?x={{y}} "T")', django_tags=True)
    print_tree(doc)
    (link,) = inlines(doc)
    assert link.href == "{{base}}/p?x={{y}}"
    assert link.title == "T"


def test_image_with_a_static_tag_source(ast):
    doc = ast("![Logo]({% static 'img/logo.png' %})", django_tags=True)
    print_tree(doc)
    image = doc.children[0].children[0]
    assert isinstance(image, Image) and image.url == "{% static 'img/logo.png' %}"


def test_autolink_with_a_tag(ast):
    doc = ast("<{{ url }}>", django_tags=True)
    print_tree(doc)
    (link,) = inlines(doc)
    assert link.href == "{{ url }}"


def test_tag_in_an_image_alt_survives(ast):
    doc = ast("![{{ name }} logo](l.png)", django_tags=True)
    print_tree(doc)
    image = doc.children[0].children[0]
    # the alt is flattened to plain text: the tag has to make it through
    assert image.alt_text.value == "{{ name }} logo"


def test_bold_link_with_tags_becomes_a_button(ast):
    doc = ast("**[{{ label }}]({{ url }})**", django_tags=True)
    print_tree(doc)
    button = doc.children[0]
    assert isinstance(button, Button) and button.href == "{{ url }}"
    assert button.children[0].raw == "{{ label }}"


# --- Block statements ---


def test_statement_alone_is_a_block_node(ast):
    doc = ast("{% if paid %}", django_tags=True)
    print_tree(doc)
    (statement,) = doc.children
    assert isinstance(statement, TemplateStatement)
    assert statement.raw == "{% if paid %}"


def test_load_tag_at_the_top(ast):
    doc = ast("{% load i18n %}\n\nHello", django_tags=True)
    print_tree(doc)
    statement, paragraph = doc.children
    assert isinstance(statement, TemplateStatement)
    assert isinstance(paragraph, Paragraph)


def test_several_statements_on_one_line(ast):
    doc = ast("{% if a %}{% if b %}", django_tags=True)
    print_tree(doc)
    (statement,) = doc.children
    assert statement.raw == "{% if a %}{% if b %}"


def test_blank_line_needed_before_the_closing_tag(ast):
    # the golden rule: without a blank line, Markdown's lazy continuation
    # swallows the closing tag into the list item
    swallowed = ast("{% for i in items %}\n- {{ i }}\n{% endfor %}", django_tags=True)
    print_tree(swallowed)
    assert len(swallowed.children) == 2
    item_inlines = swallowed.children[1].elements[0].children[0].children
    assert item_inlines[-1].raw == "{% endfor %}"

    correct = ast("{% for i in items %}\n\n- {{ i }}\n\n{% endfor %}", django_tags=True)
    print_tree(correct)
    opening, listing, closing = correct.children
    assert isinstance(opening, TemplateStatement)
    assert isinstance(listing, List)
    assert isinstance(closing, TemplateStatement) and closing.raw == "{% endfor %}"


def test_loop_around_a_whole_table(ast):
    doc = ast(
        "{% for g in groups %}\n\n| A |\n|---|\n| {{ g.a }} |\n\n{% endfor %}",
        django_tags=True,
    )
    print_tree(doc)
    opening, table, closing = doc.children
    assert isinstance(opening, TemplateStatement)
    assert isinstance(table, Table)
    assert isinstance(closing, TemplateStatement)


def test_loop_around_table_rows_breaks_the_table(ast):
    # documented limitation: Markdown parses tables line by line, so a
    # looped row falls out of the table and becomes a paragraph
    doc = ast(
        "| A |\n|---|\n{% for i in items %}\n| {{ i.a }} |\n{% endfor %}",
        django_tags=True,
    )
    print_tree(doc)
    table, opening, orphan, closing = doc.children
    assert isinstance(table, Table) and not table.rows
    assert isinstance(opening, TemplateStatement)
    assert isinstance(orphan, Paragraph)
    assert isinstance(closing, TemplateStatement)


def test_statement_inside_a_list_item_stays_inline(ast):
    doc = ast("- {% if x %}a{% endif %}", django_tags=True)
    print_tree(doc)
    item_inlines = doc.children[0].elements[0].children[0].children
    assert isinstance(item_inlines[0], TemplateTag)


# --- Opt-in ---


def test_without_opt_in_tags_are_plain_markdown(ast):
    doc = ast("{{p*2*x}} and {{q*3*y}}")
    print_tree(doc)
    nodes = inlines(doc)
    assert any(isinstance(node, Emphasis) for node in nodes)
    assert not any(isinstance(node, TemplateTag) for node in nodes)


def test_source_without_tags_is_unaffected(ast):
    markdown = (
        "# Title\n\nSome **text** and a [link](https://x.com).\n\n"
        "- item\n- other\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    plain = TreeVisitor().render(ast(markdown))
    with_plugin = TreeVisitor().render(ast(markdown, django_tags=True))
    print(with_plugin)
    assert plain == with_plugin
