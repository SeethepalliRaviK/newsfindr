"""Tests for core modules"""

import pytest
import json
from core.config import (
    TPM_LIMIT, TPM_SAFETY, MODEL_NAME, MAX_INTERESTS,
    MAX_RESULTS_PER_QUERY, MAX_BODY_CHARS
)
from core.models import (
    ExpandSearchQueriesInput, SearchInput, 
    CredibilityInput, SummarizeInput
)

def test_config_constants():
    """Verify configuration constants are set"""
    assert TPM_LIMIT == 8000
    assert TPM_SAFETY == 0.80
    assert MAX_INTERESTS == 2
    assert MAX_RESULTS_PER_QUERY == 3
    assert MAX_BODY_CHARS == 1000
    assert MODEL_NAME in ["openai/gpt-oss-120b", "llama-3.1-70b-versatile"]

def test_expand_search_queries_input():
    """Test ExpandSearchQueriesInput model"""
    data = {
        "interests": ["Technology", "AI"],
        "user_query": "latest news"
    }
    input_model = ExpandSearchQueriesInput(**data)
    assert input_model.interests == ["Technology", "AI"]
    assert input_model.user_query == "latest news"

def test_search_input():
    """Test SearchInput model"""
    data = {"query": "electric vehicles"}
    input_model = SearchInput(**data)
    assert input_model.query == "electric vehicles"

def test_credibility_input():
    """Test CredibilityInput model"""
    data = {"results": [{"url": "example.com", "title": "Test"}]}
    input_model = CredibilityInput(**data)
    assert input_model.results is not None

def test_summarize_input():
    """Test SummarizeInput model"""
    data = {"sources": [{"url": "example.com", "title": "Test"}]}
    input_model = SummarizeInput(**data)
    assert input_model.sources is not None
