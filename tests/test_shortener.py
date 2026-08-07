import io
import json
from urllib.error import URLError

import pytest

import inkletter.shortener as shortener
from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body
from inkletter.shortener import BitlyShortener


class FakeBitly:
    """Stands in for urlopen, capturing requests and counting calls."""

    def __init__(self):
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        payload = json.loads(request.data.decode("utf-8"))
        short = f"https://bit.ly/x{len(self.requests)}"
        assert payload["long_url"]
        return io.BytesIO(json.dumps({"link": short}).encode("utf-8"))


@pytest.fixture
def fake_bitly(monkeypatch):
    fake = FakeBitly()
    monkeypatch.setattr(shortener, "urlopen", fake)
    return fake


def test_shorten_calls_the_bitly_api(fake_bitly):
    result = BitlyShortener(token="tok-123").rewrite_link("https://x.com/page")

    assert result == "https://bit.ly/x1"
    request = fake_bitly.requests[0]
    assert request.full_url == "https://api-ssl.bitly.com/v4/shorten"
    assert request.get_header("Authorization") == "Bearer tok-123"
    assert json.loads(request.data.decode("utf-8")) == {
        "long_url": "https://x.com/page",
        "domain": "bit.ly",
    }


def test_custom_domain_is_sent(fake_bitly):
    BitlyShortener(token="t", domain="inklet.io").rewrite_link("https://x.com")

    assert json.loads(fake_bitly.requests[0].data.decode("utf-8"))["domain"] == ("inklet.io")


def test_images_are_never_shortened(fake_bitly):
    bitly = BitlyShortener(token="t")

    assert bitly.rewrite_image("https://x.com/i.png") == "https://x.com/i.png"
    assert fake_bitly.requests == []


def test_same_url_is_shortened_once(fake_bitly):
    bitly = BitlyShortener(token="t")

    first = bitly.rewrite_link("https://x.com/page")
    second = bitly.rewrite_link("https://x.com/page")

    assert first == second == "https://bit.ly/x1"
    assert len(fake_bitly.requests) == 1


def test_api_errors_propagate(monkeypatch):
    def failing(request):
        raise URLError("bitly is down")

    monkeypatch.setattr(shortener, "urlopen", failing)

    with pytest.raises(URLError, match="bitly is down"):
        BitlyShortener(token="t").rewrite_link("https://x.com")


def test_end_to_end_document(fake_bitly):
    markdown = (
        "Un [lien](https://x.com/page) et du texte.\n\n"
        "![img](https://x.com/i.png)\n\n"
        "**[Go](https://x.com/page)**"
    )
    actual = parse_markdown_to_mjml(markdown, url_factory=BitlyShortener(token="t"))
    print(actual)
    expected = wrap_mjml_body("""\
<mj-text>
  Un <a href="https://bit.ly/x1">lien</a> et du texte.
</mj-text>
<mj-image src="https://x.com/i.png" alt="img"/>
<mj-button href="https://bit.ly/x1">Go</mj-button>""")
    # the link and the button share the same long URL: one single API call
    assert len(fake_bitly.requests) == 1
    assert actual == expected
