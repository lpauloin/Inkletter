from inkletter.md_to_linkedin import parse_markdown_to_linkedin

# --- Links ---
#
# A feed shows no anchors: a link is its address, in full, and the label
# only survives as the words that introduce it.


def test_a_link_reads_as_label_then_address():
    actual = parse_markdown_to_linkedin("Voir [notre étude](https://exemple.fr/etude) ici.")
    print(actual)
    assert actual == "Voir notre étude : https://exemple.fr/etude ici."


def test_a_bare_address_is_printed_once():
    # the parser encapsulates it so that a factory can rewrite it; the
    # label is then the address itself, and printing both would show the
    # same link twice
    actual = parse_markdown_to_linkedin("Tout est sur https://exemple.fr/page aujourd'hui.")
    print(actual)
    assert actual == "Tout est sur https://exemple.fr/page aujourd'hui."


def test_no_angle_brackets_around_an_address():
    assert "<" not in parse_markdown_to_linkedin("[là](https://exemple.fr)")


# --- The three styles the platform does not have ---


def test_formatting_is_removed_rather_than_left_on_screen():
    actual = parse_markdown_to_linkedin("Du **gras**, de l'*italique*, du ~~barré~~.")
    print(actual)
    assert actual == "Du gras, de l'italique, du barré."


def test_unicode_substitutes_are_opt_in():
    actual = parse_markdown_to_linkedin("Du **gras**.", unicode_styling=True)
    print(actual)
    assert actual == "Du 𝗴𝗿𝗮𝘀."


def test_italic_and_strikethrough_have_their_own_substitutes():
    actual = parse_markdown_to_linkedin("*ita* ~~bar~~", unicode_styling=True)
    print(actual)
    assert actual == "𝘪𝘵𝘢 b̶a̶r̶"


def test_a_substitute_only_touches_letters():
    actual = parse_markdown_to_linkedin("**Étude 2026 !**", unicode_styling=True)
    print(actual)
    assert actual == "É𝘁𝘂𝗱𝗲 2026 !"


def test_a_mention_inside_bold_is_never_substituted():
    # the words around it are; its marker's letters would stop resolving
    actual = parse_markdown_to_linkedin(
        "**Merci [Acme](urn:li:organization:12345678)**", unicode_styling=True
    )
    print(actual)
    assert actual == "𝗠𝗲𝗿𝗰𝗶 @[urn:li:organization:12345678|Acme]"


# --- Left alone ---


def test_a_hashtag_travels_as_written():
    # nothing to encode: bare hashtags are what the platform resolves
    actual = parse_markdown_to_linkedin("Notre #étude et #Marketing2026.")
    print(actual)
    assert actual == "Notre #étude et #Marketing2026."


def test_reserved_characters_are_never_escaped():
    # measured on real posts: ( ) * _ ~ # go out as they came in
    actual = parse_markdown_to_linkedin("Un (aparté) et un tilde ~ ici.")
    print(actual)
    assert actual == "Un (aparté) et un tilde ~ ici."


def test_a_code_span_keeps_its_text_without_its_backticks():
    actual = parse_markdown_to_linkedin("La commande `inkletter preview`.")
    print(actual)
    assert actual == "La commande inkletter preview."


# --- What is laid out on one line arrives on one line ---


def test_a_label_spread_over_two_lines_is_one_line():
    actual = parse_markdown_to_linkedin("[un\nlien](https://exemple.fr)")
    print(actual)
    assert actual == "un lien : https://exemple.fr"


def test_a_padded_label_is_trimmed():
    actual = parse_markdown_to_linkedin("[ là ](https://exemple.fr)")
    print(actual)
    assert actual == "là : https://exemple.fr"


def test_a_padded_mention_name_is_trimmed():
    actual = parse_markdown_to_linkedin("[ Acme ](urn:li:organization:1)")
    print(actual)
    assert actual == "@[urn:li:organization:1|Acme]"


# --- Where a feed cannot write or dial, the address and the number are words ---


def test_a_mail_link_shows_its_address_not_its_scheme():
    assert (
        parse_markdown_to_linkedin("[Écrivez-nous](mailto:bonjour@exemple.fr)")
        == "Écrivez-nous : bonjour@exemple.fr"
    )


def test_a_bare_address_between_brackets_shows_once():
    assert (
        parse_markdown_to_linkedin("Contact : <bonjour@exemple.fr>")
        == "Contact : bonjour@exemple.fr"
    )


def test_a_mail_link_labelled_with_its_address_shows_once():
    assert (
        parse_markdown_to_linkedin("[bonjour@exemple.fr](mailto:bonjour@exemple.fr)")
        == "bonjour@exemple.fr"
    )


def test_a_tel_link_shows_its_number():
    assert (
        parse_markdown_to_linkedin("[Appelez-nous](tel:+33100000000)")
        == "Appelez-nous : +33100000000"
    )


def test_a_mail_link_in_bold_takes_the_look_alikes_on_its_words_only():
    actual = parse_markdown_to_linkedin(
        "**[Écrivez](mailto:bonjour@exemple.fr) vite**", unicode_styling=True
    )
    assert actual == "É𝗰𝗿𝗶𝘃𝗲𝘇 : bonjour@exemple.fr 𝘃𝗶𝘁𝗲"


# --- A label is read as words, whatever it is made of ---


def test_a_label_holding_code_reads_as_its_text():
    actual = parse_markdown_to_linkedin("[la commande `inkletter`](https://exemple.fr)")
    assert actual == "la commande inkletter : https://exemple.fr"


def test_a_hand_written_anchor_spells_out_its_address():
    actual = parse_markdown_to_linkedin('Voir <a href="https://exemple.fr">le site</a> ici.')
    assert actual == "Voir le site : https://exemple.fr ici."
