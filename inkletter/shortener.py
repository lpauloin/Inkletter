"""URL rewriting factories.

The client subclasses URLFactory and overrides only what concerns it:
a shortener implements rewrite_link and leaves image sources untouched
by simple inheritance.
"""

import json
from urllib.request import Request, urlopen


class URLFactory:
    """Rewrites every URL of the document. The defaults keep them as-is."""

    # The width of the links this factory produces, when it is fixed —
    # a shortener's codes are all the same length. The LinkedIn output
    # prices every link at it instead of at the address written in the
    # document, so that a post is counted for what will be published even
    # before the short links exist. Left as None, each address counts for
    # what it says.
    link_length = None

    def rewrite_link(self, url, is_button=False, is_bold=False):
        """Click URLs: links, image links, buttons.

        What the document says about a link travels with it: `is_button`
        when the link is the button — a bold link alone in its paragraph,
        where buttons exist — and `is_bold` when it sits inside bold text,
        which is how an output without buttons still tells the call to
        action from a link cited in passing. A shortener that does not
        care ignores both.
        """
        return url

    def rewrite_image(self, url):
        """Image source URLs."""
        return url


class BitlyShortener(URLFactory):
    """Shortens click URLs through the Bitly v4 API.

    Image sources are left untouched (rewrite_image is inherited as-is),
    and every distinct URL is shortened once (in-memory cache). API and
    network errors propagate to the caller.
    """

    API = "https://api-ssl.bitly.com/v4/shorten"

    def __init__(self, token, domain="bit.ly"):
        self.token = token
        self.domain = domain
        self._cache = {}

    def rewrite_link(self, url, is_button=False, is_bold=False):
        if url not in self._cache:
            self._cache[url] = self.shorten(url)
        return self._cache[url]

    def shorten(self, url):
        request = Request(
            self.API,
            data=json.dumps({"long_url": url, "domain": self.domain}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request) as response:
            return json.loads(response.read())["link"]
