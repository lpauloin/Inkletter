from inkletter.ast import *
from inkletter.django_tags import contains_tag
from inkletter.visitors.generic import NodeVisitor


class URLRewriter(NodeVisitor):
    """Runs every URL of the document through the client factory, in place.

    Contract: this pass runs before BlockTextMerger, so Buttons inherit
    the already rewritten Link href (see parse_markdown_to_ast).

    With `protected`, an URL holding a Django template tag is left alone
    and the factory is never called for it: the URL is not resolved yet,
    so there is nothing a shortener could do with it.
    """

    def __init__(self, factory, protected=False):
        self.factory = factory
        self.protected = protected

    def visit_Link(self, node, scope):
        node.href = self.rewrite(self.factory.rewrite_link, node.href)
        self.generic_visit(node, scope)

    def visit_Image(self, node, scope):
        node.url = self.rewrite(self.factory.rewrite_image, node.url)

    def visit_ImageLink(self, node, scope):
        node.href = self.rewrite(self.factory.rewrite_link, node.href)
        self.generic_visit(node, scope)  # reaches node.img -> visit_Image

    def rewrite(self, method, url):
        if self.protected and contains_tag(url):
            return url
        rewritten = method(url)
        if not isinstance(rewritten, str):
            raise TypeError(
                f"{type(self.factory).__name__}.{method.__name__} returned"
                f" {rewritten!r} for {url!r}; expected a str"
            )
        return rewritten
