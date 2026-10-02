"""Pytest configuration and fixtures"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def mock_env():
    """Set up test environment"""
    os.environ["GROQ_API_KEY"] = "test-key-12345"
    yield
    # Cleanup
    if "GROQ_API_KEY" in os.environ:
        del os.environ["GROQ_API_KEY"]

@pytest.fixture
def sample_interests():
    """Sample user interests"""
    return ["Technology", "Automobile"]

@pytest.fixture
def sample_email():
    """Sample user email"""
    return "emma.a88fec03-c@gmail.com"

@pytest.fixture
def sample_query():
    """Sample search query"""
    return "latest news on electric vehicles"
