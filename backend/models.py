"""
Data models for the unified API application.

This module contains all SQLModel and Pydantic model definitions
for articles, sentiment analysis, and cryptocurrency data.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


# SQLModel classes (Database models)
class Article(SQLModel, table=True):
    """Database model for storing articles."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Analysis(SQLModel, table=True):
    """Database model for storing sentiment analysis results."""
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    label: str
    positive: float
    negative: float
    neutral: float
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# Pydantic classes (Request/Response models)
class ArticleCreate(SQLModel):
    """Request model for creating new articles."""
    title: str
    content: str


class AnalyzeRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str


class ChatRequest(BaseModel):
    """Request model for chat functionality."""
    message: str


class SentimentScores(BaseModel):
    """Model for sentiment analysis scores."""
    positive: float
    negative: float
    neutral: float


class SentimentResult(BaseModel):
    """Response model for sentiment analysis results."""
    text: str
    lang: str
    label: str
    scores: SentimentScores
    model: str


# Cryptocurrency API Models
class CryptoCoin(BaseModel):
    """Model for cryptocurrency information."""
    rank: Optional[int]
    symbol: str
    id: str
    name: str
    price_usd: Optional[float]
    market_cap_usd: Optional[float]
    change_24h_pct: Optional[float]
    total_volume_usd: Optional[float]
    last_updated: Optional[str]
    image_url: Optional[str] = None


class CryptoResponse(BaseModel):
    """Response model for cryptocurrency API endpoints."""
    coins: List[CryptoCoin]
    total_count: int
    last_updated: str
    page: int = 1
    per_page: int = 10
    total_pages: int = 1
    has_next: bool = False
    has_prev: bool = False