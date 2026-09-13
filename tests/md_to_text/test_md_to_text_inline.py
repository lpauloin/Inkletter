from inkletter.md_to_text import parse_markdown_to_text


def test_emphasis_markers_are_dropped():
    actual = parse_markdown_to_text("Some *emphasis*, some **strong**, some ~~struck~~.")
    print(actual)
    assert actual == "Some emphasis, some strong, some struck.\n"


def test_code_span_is_literal():
    actual = parse_markdown_to_text("Type `make install` to finish.")
    print(actual)
    assert actual == "Type make install to finish.\n"


def test_link_renders_label_and_url():
    actual = parse_markdown_to_text("Visit [our site](https://example.com).")
    print(actual)
    assert actual == "Visit our site <https://example.com>.\n"


def test_link_with_label_equal_to_url():
    actual = parse_markdown_to_text("[https://example.com](https://example.com)")
    print(actual)
    assert actual == "https://example.com\n"


def test_autolink():
    actual = parse_markdown_to_text("Visit <https://example.com> now!")
    print(actual)
    assert actual == "Visit https://example.com now!\n"


def test_link_title_is_ignored():
    actual = parse_markdown_to_text('[site](https://example.com "A tooltip")')
    print(actual)
    assert actual == "site <https://example.com>\n"


def test_formatted_link_label_is_flattened():
    actual = parse_markdown_to_text("[the *full* guide](https://example.com)")
    print(actual)
    assert actual == "the full guide <https://example.com>\n"


def test_inline_html_tags_vanish():
    actual = parse_markdown_to_text("A <span>word</span> that matters<br>and the rest")
    print(actual)
    assert actual == "A word that mattersand the rest\n"


# --- Hashtags: text, as written ---


def test_a_hashtag_is_written_as_it_was():
    assert (
        parse_markdown_to_text("Nos #chiffres et #équipe_rh.") == "Nos #chiffres et #équipe_rh.\n"
    )


def test_a_hashtag_inside_a_style_is_written_as_it_was():
    assert parse_markdown_to_text("**Parlons #marketing**") == "Parlons #marketing\n"


def test_a_heading_stays_a_heading():
    assert parse_markdown_to_text("# Titre #tag") == "Titre #tag\n==========\n"


# --- A bare address is a link ---


def test_a_bare_address_is_a_link_in_the_text_too():
    assert (
        parse_markdown_to_text("Voir https://exemple.fr/page.") == "Voir https://exemple.fr/page.\n"
    )


def test_a_bare_address_reaches_the_url_factory():
    from inkletter import URLFactory

    class Short(URLFactory):
        def rewrite_link(self, url, is_button=False, is_bold=False):
            return "https://s.fr/x"

    actual = parse_markdown_to_text("Voir https://exemple.fr/page.", url_factory=Short())
    assert actual == "Voir https://exemple.fr/page <https://s.fr/x>.\n"


def test_a_bare_address_alone_in_bold_is_the_call_to_action():
    assert parse_markdown_to_text("**https://exemple.fr**") == "→ https://exemple.fr\n"


# --- An address and a number ---


def test_a_mail_link_keeps_its_scheme_for_the_mail_client():
    assert (
        parse_markdown_to_text("[Écrivez-nous](mailto:bonjour@exemple.fr)")
        == "Écrivez-nous <mailto:bonjour@exemple.fr>\n"
    )


def test_a_bare_address_between_brackets_is_written_once():
    assert (
        parse_markdown_to_text("Contact : <bonjour@exemple.fr>") == "Contact : bonjour@exemple.fr\n"
    )


def test_a_tel_link_keeps_its_scheme_too():
    assert parse_markdown_to_text("[Appelez](tel:+331)") == "Appelez <tel:+331>\n"
