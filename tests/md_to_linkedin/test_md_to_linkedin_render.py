"""The render a preview reads: the post line by line, each fragment saying
what the feed shows of it and what it costs, and what the feed will not
show."""

from inkletter import URLFactory, render_linkedin
from inkletter.codeblock import Segment


class Width(URLFactory):
    link_length = 23


def segments(markdown_text, **options):
    return [list(line.segments) for line in render_linkedin(markdown_text, **options).lines]


def test_the_render_is_the_post_and_its_count():
    render = render_linkedin("Bonjour **tout le monde**")
    assert render.text == "Bonjour tout le monde"
    assert render.length == 21


def test_a_mention_shows_its_name_and_costs_it():
    (line,) = segments("Merci [Acme](urn:li:organization:1)")
    assert line == [Segment("text", "Merci ", 6), Segment("mention", "Acme", 4)]


def test_a_hashtag_is_its_own_fragment():
    (line,) = segments("Vu #salon")
    assert line == [Segment("text", "Vu ", 3), Segment("hashtag", "#salon", 6)]


def test_a_domain_shows_as_written_and_costs_the_short_link():
    (line,) = segments("Voir exemple.com", url_factory=Width())
    assert line == [Segment("text", "Voir ", 5), Segment("link", "exemple.com", 23)]


def test_a_labelled_link_shows_its_address():
    (line,) = segments("[le site](https://exemple.fr)")
    assert line[-1] == Segment("link", "https://exemple.fr", 18)


def test_a_quote_marker_is_shown_as_the_feed_shows_it():
    (line,) = segments("> Citée")
    assert line == [Segment("text", "> ", 2), Segment("text", "Citée", 5)]


def test_the_blank_lines_the_post_ends_on_are_not_lines():
    render = render_linkedin("Un\n\nDeux\n\n\n")
    assert [line.text for line in render.lines] == ["Un", "", "Deux"]


def test_the_shown_text_reads_like_the_feed():
    render = render_linkedin("Merci [Acme](urn:li:organization:1), voir exemple.com")
    assert render.text == "Merci @[urn:li:organization:1|Acme], voir https://exemple.com"
    assert render.shown_text == "Merci Acme, voir exemple.com"


def test_styles_the_feed_will_not_show_are_said():
    assert render_linkedin("Un **mot**").unrendered_formatting is True
    assert render_linkedin("Un mot").unrendered_formatting is False


def test_look_alikes_stand_in_for_the_styles():
    assert render_linkedin("Un **mot**", unicode_styling=True).unrendered_formatting is False


def test_a_link_alone_in_bold_is_the_ask_and_no_style():
    assert render_linkedin("**[Lire](https://exemple.fr)**").unrendered_formatting is False


def test_a_heading_the_feed_will_not_show_is_said():
    assert render_linkedin("# Titre").unrendered_headings is True
    assert render_linkedin("# Titre", unicode_styling=True).unrendered_headings is True
    assert render_linkedin("Titre").unrendered_headings is False
