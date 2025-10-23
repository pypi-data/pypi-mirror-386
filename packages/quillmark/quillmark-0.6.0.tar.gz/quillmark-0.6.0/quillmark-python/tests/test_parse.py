"""Tests for ParsedDocument."""

import pytest

from quillmark import ParsedDocument, ParseError
from typing import cast


def test_parse_markdown(taro_md):
    """Test parsing markdown with frontmatter."""
    parsed = ParsedDocument.from_markdown(taro_md)
    assert "Ice Cream" in cast(str, parsed.get_field("title"))
    assert "nutty" in cast(str, parsed.body())


def test_parse_invalid_yaml():
    """Test parsing invalid YAML frontmatter."""
    invalid_md = """---
title: [unclosed bracket
---

Content
"""
    with pytest.raises(ParseError):
        ParsedDocument.from_markdown(invalid_md)


def test_fields_access(taro_md):
    """Test accessing all fields."""
    parsed = ParsedDocument.from_markdown(taro_md)
    fields = parsed.fields
    assert "title" in fields
    assert "Ice Cream" in fields["title"]
    assert "body" in fields
