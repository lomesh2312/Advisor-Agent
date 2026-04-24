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
    sentiment: str  
    impact_level: str  
    scope: str = "MARKET"  
    entities: NewsEntities = Field(default_factory=NewsEntities)
    relevance_score: float = 0.5
    causal_keywords: List[str] = []
