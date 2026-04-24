import logging
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from groq import Groq
from config import GROQ_API_KEY
try:
    from services.observability import langfuse, safe_flush
except ImportError:
    langfuse = None
    def safe_flush(): pass

logger = logging.getLogger(__name__)

class CausalChain(BaseModel):
    event: str = "N/A"
    macro_variable: str = "N/A"
    sector_impact: str = "N/A"
    affected_holdings: str = "N/A"
    estimated_portfolio_impact: float = 0.0
    confidence: float = 0.0
    strength: str = "MEDIUM"

class StrategicRecommendation(BaseModel):
    action: str = "N/A"
    current_allocation: float = 0.0
    target_allocation: float = 0.0
    shift: float = 0.0
    reasoning: str = "N/A"
    expected_benefit: str = "N/A"
    tradeoff: str = "N/A"

class SectorIntelligence(BaseModel):
    sector: str = "N/A"
    trend_signal: str = "NEUTRAL"
    change_percent: float = 0.0
    macro_rationale: str = "N/A"
    impact_on_portfolio: str = "N/A"

class AdvisorReport(BaseModel):
    portfolio_id: str
    executive_summary: str = "Generating report..."
    market_sentiment: str = "NEUTRAL"
    effective_sector_exposure: Dict[str, float] = {}
    risk_diagnostics: Dict[str, Any] = {}
    causal_driver_chains: List[CausalChain] = []
    stress_test_scenarios: List[Dict[str, Any]] = []
    material_risks: List[str] = []
    strategic_rebalancing_actions: List[StrategicRecommendation] = []
    sector_intelligence_view: List[SectorIntelligence] = []
    final_diagnosis: str = "N/A"
    confidence_level: str = "MEDIUM"
    latency_ms: float = 0.0

ADVISOR_SYSTEM_PROMPT = """You are a Senior Portfolio Strategist / CIO. Generate an institutional-grade risk and intelligence report.
TONE: Concise, analytical, high-signal. Resemble a premium wealth management diagnostic.
NO GENERIC PHRASES. Use quantified economic logic.

JSON SCHEMA:
{
  "portfolio_id": "string",
  "executive_summary": "string",
  "market_sentiment": "BULLISH|BEARISH|NEUTRAL",
  "effective_sector_exposure": {"SECTOR": float},
  "risk_diagnostics": {"hhi": float, "status": "string", "metrics": "string"},
  "causal_driver_chains": [{"event":"string","macro_variable":"string","sector_impact":"string","affected_holdings":"string","estimated_portfolio_impact":float,"confidence":float,"strength":"WEAK|MEDIUM|STRONG"}],
  "stress_test_scenarios": [{"scenario":"string","impact":float,"vulnerable_holdings":["string"]}],
  "material_risks": ["string"],
  "strategic_rebalancing_actions": [{"action":"string","current_allocation":float,"target_allocation":float,"shift":float,"reasoning":"string","expected_benefit":"string","tradeoff":"string"}],
  "sector_intelligence_view": [{"sector":"string","trend_signal":"BULLISH|BEARISH|NEUTRAL","change_percent":float,"macro_rationale":"string","impact_on_portfolio":"string"}],
  "final_diagnosis": "string",
  "confidence_level": "HIGH|MEDIUM|LOW"
}"""

def generate_advisor_report(market_context: Dict[str, Any], portfolio_analysis: Dict[str, Any]) -> AdvisorReport:
    portfolio_id = portfolio_analysis.get("portfolio_id", "UNKNOWN")
    try:
        client = Groq(api_key=GROQ_API_KEY)
        input_data = {
            "portfolio_id": portfolio_id,
            "stats": {"pnl_pct": portfolio_analysis.get("pnl_percent")},
            "exposure": portfolio_analysis.get("effective_sector_exposure"),
            "risk": portfolio_analysis.get("risk_diagnostics"),
            "stress": portfolio_analysis.get("stress_tests"),
            "market": market_context
        }
        
        if "news" in market_context:
            market_context["news"] = [n.dict() if hasattr(n, "dict") else n for n in market_context["news"]]

        import time
        start_time = time.time()
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": ADVISOR_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate Institutional Report for {portfolio_id}:\n{json.dumps(input_data, default=str)}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        latency = (time.time() - start_time) * 1000
        data = json.loads(completion.choices[0].message.content)
        
        # Robustness: Sync some fields from analysis if missing/hallucinated
        data["portfolio_id"] = portfolio_id
        data["effective_sector_exposure"] = portfolio_analysis.get("effective_sector_exposure", {})
        data["market_sentiment"] = data.get("market_sentiment") or market_context.get("market_sentiment", "NEUTRAL")
        
        data["latency_ms"] = round(latency, 2)
        
        safe_flush()
        return AdvisorReport(**data)
    except Exception as e:
        logger.error(f"Institutional Advisor Error: {e}")
        safe_flush()
        # Return a fallback report instead of crashing
        return AdvisorReport(
            portfolio_id=portfolio_id,
            executive_summary=f"Analysis engine experienced a transient error. Manual look-through suggests concentration in {portfolio_analysis.get('top_sector', 'equity')}.",
            effective_sector_exposure=portfolio_analysis.get("effective_sector_exposure", {}),
            market_sentiment="NEUTRAL",
            final_diagnosis="Maintain defensive posture while system recalibrates.",
            latency_ms=0.0
        )
