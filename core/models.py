"""Pydantic models for data validation"""

from pydantic import BaseModel, Field
from typing import List

class ExpandSearchQueriesInput(BaseModel):
    """Input model for search query expansion"""
    interests: List[str] = Field(description="List of user interests to expand")
    user_query: str = Field(description="Specific user query or topic")

class SearchInput(BaseModel):
    """Input model for DuckDuckGo search"""
    query: str = Field(description="Single news search query string")

class CredibilityInput(BaseModel):
    """Input model for credibility filtering"""
    results: dict | list = Field(description="DuckDuckGo search results or JSON string")

class SummarizeInput(BaseModel):
    """Input model for news summarization"""
    sources: dict | list = Field(description="Credible sources to summarize")

class NewsResult(BaseModel):
    """Model for news search result"""
    title: str
    url: str
    body: str
    date: str = ""

class UserProfile(BaseModel):
    """Model for user profile from database"""
    email_id: str
    interests: List[str]

class NewsArticle(BaseModel):
    """Model for final news article"""
    title: str
    url: str
    snippet: str
    source: str
    credibility_score: float = 0.0
