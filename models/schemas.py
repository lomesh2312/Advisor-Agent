from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PortfolioSummary(BaseModel):
    portfolio_id: str
    user_name: str
    portfolio_type: str
    risk_profile: str
    total_investment: float
    current_value: float
    overall_pnl: float
    overall_pnl_pct: float


class StressTestResult(BaseModel):
    scenario: str
    impact_percent: float
    vulnerable_holdings: List[str]
    drawdown_estimate: str
    severity: str = "MEDIUM"


class RiskDiagnosticResult(BaseModel):
    hhi: float
    hhi_status: str
    overlap_risk: str
    beta_sensitivity: float
    rate_sensitivity: str
    sector_concentration_risk: str
    diversification_score: float
    top_sector_weight: float


class MajorHolding(BaseModel):
    name: str
    weight: float
    asset_type: str = "EQUITY"


class LookThroughResult(BaseModel):
    fund_name: str
    fund_weight: float
    decomposed_sectors: Dict[str, float]
    top_holdings: List[str]
    overlap_detected: bool = False


class PortfolioAnalysisResult(BaseModel):
    portfolio_id: str
    total_pnl: float
    pnl_percent: float
    top_sector: str
    effective_sector_exposure: Dict[str, float]
    direct_sector_exposure: Dict[str, float]
    mf_sector_exposure: Dict[str, float]
    risk_diagnostics: RiskDiagnosticResult
    stress_tests: List[StressTestResult]
    major_holdings: List[MajorHolding]
    look_through_details: List[LookThroughResult]
    overlap_coefficient: float
    total_current_value: float



class CausalChain(BaseModel):
    event: str
    macro_variable: str
    sector_impact: str
    affected_holdings: str
    estimated_portfolio_impact: float
    confidence: float
    strength: str = "MEDIUM"  


class ConflictResolution(BaseModel):
    signal_a: str
    signal_b: str
    conflict_type: str
    resolution: str
    net_bias: str


class PrioritizedSignal(BaseModel):
    rank: int
    signal: str
    source: str
    impact_magnitude: float
    confidence: float
    action_required: bool


class ReasoningChain(BaseModel):
    run_id: str
    query: str
    steps: List[Dict[str, Any]]
    causal_chains: List[CausalChain]
    conflicts_resolved: List[ConflictResolution]
    prioritized_signals: List[PrioritizedSignal]
    final_conclusion: str
    reasoning_confidence: float
    latency_ms: float



class StrategicRecommendation(BaseModel):
    action: str
    current_allocation: float
    target_allocation: float
    shift: float
    reasoning: str
    expected_benefit: str
    tradeoff: str


class SectorIntelligence(BaseModel):
    sector: str
    trend_signal: str
    change_percent: float
    macro_rationale: str
    impact_on_portfolio: str


class AdvisorReport(BaseModel):
    portfolio_id: str
    run_id: str = ""
    executive_summary: str
    market_sentiment: str = "NEUTRAL"
    effective_sector_exposure: Dict[str, float] = {}
    risk_diagnostics: Dict[str, Any] = {}
    causal_driver_chains: List[CausalChain] = []
    stress_test_scenarios: List[Dict[str, Any]] = []
    material_risks: List[str] = []
    strategic_rebalancing_actions: List[StrategicRecommendation] = []
    sector_intelligence_view: List[SectorIntelligence] = []
    final_diagnosis: str
    confidence_level: str = "MEDIUM"
    latency_ms: float = 0.0



class EvaluationResult(BaseModel):
    run_id: str = ""
    score: float
    rating: str  
    feedback: str
    news_usage_score: float
    sector_reasoning_score: float
    portfolio_linkage_score: float
    causal_completeness_score: float
    penalties_applied: float
    risk_grade: str = "B"
    critique: str = ""



class ChatRequest(BaseModel):
    query: str
    portfolio_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    sources_used: List[str] = []
    portfolio_id: Optional[str] = None
    reasoning_summary: Optional[str] = None
    confidence: float = 0.7
    latency_ms: float = 0.0



class SectorTrendResponse(BaseModel):
    sector: str
    change_percent: float
    sentiment: str
    key_drivers: List[str]
    top_gainers: List[str]
    top_losers: List[str]
    macro_link: str = ""


class MacroSignalResponse(BaseModel):
    signal_name: str
    value: float
    unit: str
    trend: str
    impact_sectors: List[str]
    interpretation: str



class NewsClassifyRequest(BaseModel):
    headline: str
    summary: str = ""


class NewsClassifyResponse(BaseModel):
    headline: str
    sentiment: str
    impact_level: str
    scope: str
    affected_sectors: List[str]
    affected_stocks: List[str]
    causal_keywords: List[str]


class CausalImpactRequest(BaseModel):
    news_ids: List[str]
    portfolio_id: Optional[str] = None


class CausalImpactResponse(BaseModel):
    news_count: int
    causal_chains: List[CausalChain]
    portfolio_impact_estimate: float
    high_impact_signals: List[str]



class TraceInfo(BaseModel):
    run_id: str
    endpoint: str
    latency_ms: float
    token_usage: int
    model: str
    timestamp: str
    status: str


class TokenUsageResponse(BaseModel):
    total_calls: int
    total_tokens: int
    avg_tokens_per_call: float
    model_breakdown: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    version: str
    groq_connected: bool
    data_loaded: bool
    portfolios_count: int
    news_count: int
    uptime_seconds: float
