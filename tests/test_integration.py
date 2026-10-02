"""Integration tests for full pipeline"""

import pytest
import os
from utils.database import (
    get_all_emails, fetch_interests, 
    fetch_interests_direct, get_db_path
)

def test_database_path():
    """Test database path detection"""
    try:
        db_path = get_db_path()
        assert db_path is not None
        assert "customer.db" in db_path
    except FileNotFoundError:
        pytest.skip("Database file not found")

def test_get_all_emails():
    """Test fetching all emails from database"""
    try:
        emails = get_all_emails()
        assert isinstance(emails, list)
        assert len(emails) > 0
    except FileNotFoundError:
        pytest.skip("Database file not found")

def test_fetch_interests_direct():
    """Test fetching interests directly from database"""
    try:
        # Use first available email if exists
        emails = get_all_emails()
        if emails:
            interests = fetch_interests_direct(emails[0])
            assert isinstance(interests, list)
    except FileNotFoundError:
        pytest.skip("Database file not found")

def test_fetch_interests_with_agent():
    """Test fetching interests with database fallback"""
    try:
        emails = get_all_emails()
        if emails:
            interests = fetch_interests(emails[0], use_agent=False)
            assert isinstance(interests, list)
    except FileNotFoundError:
        pytest.skip("Database file not found")

def test_database_nonexistent_email():
    """Test fetching interests for non-existent email"""
    try:
        interests = fetch_interests_direct("nonexistent@example.com")
        assert interests == []
    except FileNotFoundError:
        pytest.skip("Database file not found")
