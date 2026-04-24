from typing import List, Optional
from pydantic import BaseModel, Field


class NewsEntities(BaseModel):
    sectors: List[str] = []
    stocks: List[str] = []
    macro_variables: List[str] = []


class NewsArticle(BaseModel):
    id: str
    date: str
    headline: str
    summary: str
    source: str
    sentiment: str  # BULLISH | BEARISH | NEUTRAL
    impact_level: str  # HIGH | MEDIUM | LOW
    scope: str = "MARKET"  # MARKET | SECTOR | STOCK
    entities: NewsEntities = Field(default_factory=NewsEntities)
    relevance_score: float = 0.5
    causal_keywords: List[str] = []
