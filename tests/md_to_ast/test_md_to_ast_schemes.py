"""What a link's target names, read by its scheme — the standard splitter's,
not a prefix — and the node it becomes. A URN names an entity: a Mention.
Everything else is a Link, which says its scheme for whoever asks."""

import pytest

from inkletter.ast import *
from inkletter.md_to_ast import ASTRenderer


def walk(node):
    yield node
    for child in node.get_children():
        yield from walk(child)


def links(doc):
    return [node for node in walk(doc) if isinstance(node, (Link, ImageLink, Image, Mention))]


@pytest.mark.parametrize(
    ("target", "scheme"),
    [
        ("https://exemple.fr/page", "https"),
        ("http://exemple.fr", "http"),
        ("HTTPS://EXEMPLE.FR", "https"),
        ("mailto:bonjour@exemple.fr", "mailto"),
        ("tel:+33100000000", "tel"),
        ("asset:vis_ab12cd34", "asset"),
        ("/chemin/relatif", ""),
        ("page.html", ""),
    ],
)
def test_a_link_says_its_scheme(ast, target, scheme):
    (link,) = links(ast(f"[là]({target})"))
    assert isinstance(link, (UrlLink, MailLink, TelLink))
    assert link.scheme == scheme


def test_a_target_the_splitter_refuses_is_no_scheme_and_no_crash(ast):
    # which targets it refuses depends on the Python; what must hold is
    # that a document never fails to parse over one
    (link,) = links(ast("[là](http://[unclosed)"))
    assert isinstance(link.scheme, str)


def test_the_scheme_follows_a_rewritten_href(ast):
    (link,) = links(ast("[là](https://exemple.fr)"))
    link.href = "mailto:x@y.fr"
    assert link.scheme == "mailto"


def test_an_image_and_an_image_link_say_theirs(ast):
    (image_link, image) = links(ast("[![alt](logo.png)](https://exemple.fr)"))
    assert isinstance(image_link, ImageLink) and image_link.scheme == "https"
    assert isinstance(image, Image) and image.scheme == ""


@pytest.mark.parametrize(
    "urn", ["urn:li:organization:105581663", "urn:li:person:abc", "URN:li:organization:1"]
)
def test_a_urn_is_a_mention(ast, urn):
    (mention,) = links(ast(f"[Croco.code]({urn})"))
    assert isinstance(mention, Mention)
    assert mention.urn == urn


def test_a_bare_address_is_a_link_with_its_scheme(ast):
    (link,) = links(ast("Voir https://exemple.fr/page."))
    assert link.scheme == "https"


def test_the_dispatch_is_one_table(ast):
    # a scheme added later gets its node here, once
    assert ASTRenderer.LINKS_BY_SCHEME == {"urn": Mention, "mailto": MailLink, "tel": TelLink}
    assert Link.scheme_of("urn:li:organization:1") in ASTRenderer.LINKS_BY_SCHEME
    assert Link.scheme_of("https://exemple.fr") not in ASTRenderer.LINKS_BY_SCHEME


# --- What each scheme becomes ---


def test_a_mention_is_a_link_that_names_someone(ast):
    (mention,) = links(ast("[Croco.code](urn:li:organization:1)"))
    assert isinstance(mention, Link)
    assert mention.href == mention.urn == "urn:li:organization:1"


def test_a_mailto_is_a_mail_link_that_knows_its_address(ast):
    (link,) = links(ast("[Écrivez-nous](mailto:bonjour@exemple.fr)"))
    assert isinstance(link, MailLink)
    assert link.address == "bonjour@exemple.fr"


def test_a_bare_address_between_brackets_is_a_mail_link(ast):
    (link,) = links(ast("<bonjour@exemple.fr>"))
    assert isinstance(link, MailLink)
    assert link.address == "bonjour@exemple.fr"


def test_a_tel_is_a_tel_link_that_knows_its_number(ast):
    (link,) = links(ast("[Appelez](tel:+33100000000)"))
    assert isinstance(link, TelLink)
    assert link.number == "+33100000000"


def test_a_title_reaches_every_kind_of_link(ast):
    (link,) = links(ast('[nous](mailto:a@b.fr "Le titre")'))
    assert link.title == "Le titre"


# --- The call to action is a link one may follow, never a mention ---


def buttons(doc):
    return [node for node in walk(doc) if isinstance(node, Button)]


def test_a_lone_bold_mention_is_no_button(ast):
    assert buttons(ast("**[Croco](urn:li:organization:1)**")) == []


@pytest.mark.parametrize("target", ["https://exemple.fr", "mailto:a@b.fr", "tel:+331"])
def test_a_lone_bold_link_one_may_follow_is_a_button(ast, target):
    assert len(buttons(ast(f"**[Allez-y]({target})**"))) == 1


# --- Link is abstract: every link in a tree is one of its kinds ---


def test_no_link_in_a_tree_is_a_bare_link(ast):
    doc = ast(
        "[a](https://a.fr) [b](mailto:b@b.fr) [c](tel:+33) [d](urn:li:organization:1) [e](page.html)"
    )
    kinds = [type(node) for node in links(doc)]
    assert kinds == [UrlLink, MailLink, TelLink, Mention, UrlLink]
    assert Link not in kinds
    assert all(isinstance(node, Link) for node in links(doc))


# --- What a bold asks ---


def strong(doc):
    (node,) = [node for node in walk(doc) if isinstance(node, Strong)]
    return node


@pytest.mark.parametrize("target", ["https://exemple.fr", "mailto:a@b.fr", "tel:+331"])
def test_a_lone_bold_link_is_the_ask(ast, target):
    doc = ast(f"**[Allez-y]({target})**", bold_link_is_button=False)
    assert strong(doc).ask.href == target


def test_a_lone_bold_mention_asks_nothing(ast):
    doc = ast("**[Croco](urn:li:organization:1)**", bold_link_is_button=False)
    assert strong(doc).ask is None


def test_a_bold_link_among_words_asks_nothing(ast):
    doc = ast("**voir [le site](https://exemple.fr)**", bold_link_is_button=False)
    assert strong(doc).ask is None


# --- What each kind says of itself, when a tree is printed ---


def test_each_kind_of_link_prints_what_it_is(ast):
    doc = ast("[a](https://a.fr) [b](mailto:b@b.fr) [c](tel:+33) [d](urn:li:organization:1) #tag")
    printed = [repr(node) for node in walk(doc) if isinstance(node, (Link, Hashtag))]
    assert printed == [
        "UrlLink(href='https://a.fr', title='None')",
        "MailLink(address='b@b.fr')",
        "TelLink(number='+33')",
        "Mention(urn='urn:li:organization:1')",
        "Hashtag(name='tag')",
    ]


def test_a_target_the_splitter_refuses_has_no_scheme(monkeypatch):
    # which targets the splitter refuses depends on the Python — so the
    # refusal is staged, and what must hold is that it never surfaces
    import inkletter.ast

    def refuse(target):
        raise ValueError("Invalid IPv6 URL")

    monkeypatch.setattr(inkletter.ast, "urlsplit", refuse)
    assert Link.scheme_of("http://[::1") == ""
