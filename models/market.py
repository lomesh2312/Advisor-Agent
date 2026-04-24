from typing import Optional, List, Dict
from pydantic import BaseModel


class Index(BaseModel):
    name: str
    current_value: float
    previous_close: float
    change_percent: float
    change_absolute: float
    day_high: float
    day_low: float
    sentiment: str


class SectorPerformance(BaseModel):
    change_percent: float
    sentiment: str
    key_drivers: List[str] = []
    top_gainers: List[str] = []
    top_losers: List[str] = []


class Stock(BaseModel):
    symbol: str
    name: str
    sector: str
    sub_sector: Optional[str] = None
    current_price: float
    previous_close: float
    change_percent: float
    change_absolute: float
    volume: int
    avg_volume_20d: Optional[int] = None
    market_cap_cr: Optional[float] = None
    pe_ratio: Optional[float] = None
    beta: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None


class MarketMetadata(BaseModel):
    date: str
    market_status: str
    currency: str
    sentiment: Optional[str] = "NEUTRAL"


class MacroSignals(BaseModel):
    repo_rate: Optional[float] = None
    inflation_cpi: Optional[float] = None
    fii_flow_cr: Optional[float] = None
    dii_flow_cr: Optional[float] = None
    inr_usd: Optional[float] = None
    crude_oil_usd: Optional[float] = None
    vix: Optional[float] = None


class MarketData(BaseModel):
    metadata: MarketMetadata
    indices: Dict[str, Index] = {}
    sector_performance: Dict[str, SectorPerformance] = {}
    stocks: Dict[str, Stock] = {}
    macro_signals: Optional[MacroSignals] = None
