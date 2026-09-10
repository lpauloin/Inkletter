import pytest

from inkletter.exceptions import LengthError
from inkletter.md_to_linkedin import parse_markdown_to_linkedin


@pytest.fixture
def measured():
    """What the render counted for a document: the one refusal carries
    it, so a ceiling nothing fits under reads it back."""

    def measure(markdown_text, **options):
        with pytest.raises(LengthError) as refusal:
            parse_markdown_to_linkedin(markdown_text, max_length=-1, **options)
        return refusal.value.length

    return measure
