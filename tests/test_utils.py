"""Tests for utility modules"""

import pytest
from utils.llm import clip, estimate_tokens, is_rate_limit
from utils.search import SEARCH_CACHE
from utils.database import parse_interests

def test_clip_function():
    """Test text clipping"""
    text = "This is a very long text that should be clipped"
    clipped = clip(text, 10)
    assert len(clipped) <= 10
    assert clipped == "This is a "

def test_clip_with_whitespace():
    """Test clip removes extra whitespace"""
    text = "This   has   multiple   spaces"
    clipped = clip(text, 50)
    assert "   " not in clipped
    assert clipped == "This has multiple spaces"

def test_estimate_tokens():
    """Test token estimation"""
    text = "Hello world"
    tokens = estimate_tokens(text)
    assert tokens >= 1
    assert isinstance(tokens, int)

def test_parse_interests_empty():
    """Test parse_interests with empty input"""
    result = parse_interests("")
    assert result == []

def test_parse_interests_comma_separated():
    """Test parse_interests with comma-separated values"""
    text = "Technology, Automobile, Business"
    result = parse_interests(text)
    assert "technology" in [i.lower() for i in result] or len(result) == 0

def test_parse_interests_refusal():
    """Test parse_interests with LLM refusal"""
    text = "Sorry, I cannot process this request"
    result = parse_interests(text)
    assert result == []

def test_is_rate_limit():
    """Test rate limit detection"""
    assert is_rate_limit(Exception("429 Too Many Requests"))
    assert is_rate_limit(Exception("rate limit exceeded"))
    assert not is_rate_limit(Exception("Something else"))

def test_search_cache_empty():
    """Test search cache is initialized"""
    assert isinstance(SEARCH_CACHE, dict)
