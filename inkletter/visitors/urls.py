import re

from inkletter.visitors.generic import NodeVisitor

REWRITABLE_SCHEMES = ("http://", "https://")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


class URLRewriter(NodeVisitor):
    """Runs every URL of the document through the client factory, in place.

    Contract: this pass runs last, after Annotation, so that what the
    document says about a link is already written in its node — a Button
    is annotated as one, a link inside bold text as bold — and the
    factory is told with the URL.

    Only addresses are offered to the factory. A target that names
    something rather than locating it — an entity URN, a `mailto:`, a
    `tel:` — is left alone: shortening it would destroy it, and a caller
    should not have to guard against being handed one.
    """

    def __init__(self, factory):
        super().__init__()
        self.factory = factory

    def visit_Link(self, node, scope):
        self.rewrite_href(node)
        self.generic_visit(node, scope)

    def visit_ImageLink(self, node, scope):
        self.rewrite_href(node)
        self.generic_visit(node, scope)  # reaches node.img -> visit_Image

    def visit_Button(self, node, scope):
        self.rewrite_href(node)
        self.generic_visit(node, scope)

    @staticmethod
    def is_an_address(url):
        """What a factory may be handed: a web address, or a path relative
        to one — a local image a factory uploads has no scheme at all.
        Anything else names something rather than locating it, and
        rewriting it would destroy it."""
        return url.startswith(REWRITABLE_SCHEMES) or not SCHEME.match(url)

    def visit_Image(self, node, scope):
        if self.is_an_address(node.url):
            node.url = self.checked("rewrite_image", node.url, self.factory.rewrite_image(node.url))

    def rewrite_href(self, node):
        if self.is_an_address(node.href):
            rewritten = self.factory.rewrite_link(
                node.href,
                is_button=node.annotations.get("button", False),
                is_bold=node.annotations.get("bold", False),
            )
            node.href = self.checked("rewrite_link", node.href, rewritten)

    def checked(self, method, url, rewritten):
        if not isinstance(rewritten, str):
            raise TypeError(
                f"{type(self.factory).__name__}.{method} returned"
                f" {rewritten!r} for {url!r}; expected a str"
            )
        return rewritten
