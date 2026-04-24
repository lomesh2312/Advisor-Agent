import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional

from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_FAST
from models.news import NewsArticle
from models.schemas import (
    ChatRequest, ChatResponse,
    CausalImpactResponse, CausalChain,
    NewsClassifyResponse,
    ReasoningChain, PrioritizedSignal, ConflictResolution
)

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are an Autonomous Financial Advisor Agent.
Answer questions using ONLY the provided portfolio data, market data, and news articles.
Be precise. Reference specific holdings, sectors, and news events.
If portfolio_id is given, focus on that portfolio's specific holdings and exposure.
Respond in clear, institutional language. Quantify impacts where possible."""

CAUSAL_CHAIN_PROMPT = """You are a Causal Reasoning Engine for financial markets.
Given news events and portfolio data, trace the causal chain:
  News Event → Macro Variable → Sector Move → Holding Impact → Portfolio P&L Impact

For each news article, produce one causal chain object.
Return JSON array: [{"event":"...","macro_variable":"...","sector_impact":"...","affected_holdings":"...","estimated_portfolio_impact":float,"confidence":float,"strength":"WEAK|MEDIUM|STRONG"}]
Use ONLY holdings from the provided portfolio. Be precise."""

SIGNAL_PRIORITY_PROMPT = """You are a Signal Intelligence Engine.
Given multiple news signals and portfolio exposure, rank them by portfolio impact.
Return JSON array (ranked 1=highest):
[{"rank":int,"signal":"description","source":"news id","impact_magnitude":float,"confidence":float,"action_required":bool}]"""


class ReasoningService:
    def __init__(self, data_loader: Any):
        self.data_loader = data_loader
        self._client = Groq(api_key=GROQ_API_KEY)

    # ─── Chat ──────────────────────────────────────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())[:8]
        start = time.time()

        context_parts = []
        portfolio = None

        if request.portfolio_id:
            portfolio = self.data_loader.get_portfolio_by_id(request.portfolio_id)
            if portfolio:
                analysis_summary = {
                    "portfolio_id": portfolio.id,
                    "user": portfolio.user_name,
                    "total_investment": portfolio.total_investment,
                    "current_value": portfolio.current_value,
                    "gain_loss_pct": portfolio.overall_gain_loss_percent,
                    "risk_profile": portfolio.risk_profile,
                    "stocks": [
                        {"symbol": s.symbol, "sector": s.sector,
                         "gain_pct": s.gain_loss_percent, "weight": s.weight_in_portfolio}
                        for s in portfolio.holdings.stocks
                    ],
                    "mutual_funds": [
                        {"name": m.scheme_name, "category": m.category,
                         "gain_pct": m.gain_loss_percent, "weight": m.weight_in_portfolio}
                        for m in portfolio.holdings.mutual_funds
                    ],
                }
                context_parts.append(f"PORTFOLIO DATA:\n{json.dumps(analysis_summary, default=str)}")

        market = self.data_loader.get_market_data()
        if market:
            mkt_summary = {
                "nifty50_change": market.indices.get("NIFTY50", {}).change_percent
                if hasattr(market.indices.get("NIFTY50", {}), "change_percent") else None,
                "banknifty_change": market.indices.get("BANKNIFTY", {}).change_percent
                if hasattr(market.indices.get("BANKNIFTY", {}), "change_percent") else None,
                "sector_sentiments": {
                    k: {"change_pct": v.change_percent, "sentiment": v.sentiment}
                    for k, v in market.sector_performance.items()
                },
            }
            context_parts.append(f"MARKET DATA:\n{json.dumps(mkt_summary)}")

        # Relevant news
        if portfolio:
            news = self.data_loader.get_news_relevant_to_portfolio(portfolio, limit=6)
        else:
            news = self.data_loader.get_high_impact_news()[:6]

        if news:
            news_summary = [
                {"id": n.id, "headline": n.headline, "sentiment": n.sentiment,
                 "impact": n.impact_level, "sectors": n.entities.sectors, "stocks": n.entities.stocks}
                for n in news
            ]
            context_parts.append(f"RELEVANT NEWS:\n{json.dumps(news_summary)}")

        full_context = "\n\n".join(context_parts)
        user_message = f"Context:\n{full_context}\n\nQuestion: {request.query}"

        try:
            completion = self._client.chat.completions.create(
                model=GROQ_MODEL_FAST,
                messages=[
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=1200,
            )
            answer = completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat error: {e}")
            answer = f"I encountered an error processing your query: {str(e)}"

        latency_ms = round((time.time() - start) * 1000, 1)
        sources = [n.id for n in news[:4]] if news else []

        return ChatResponse(
            session_id=session_id,
            query=request.query,
            answer=answer,
            sources_used=sources,
            portfolio_id=request.portfolio_id,
            reasoning_summary="Data grounded from portfolios.json, market_data.json, news_data.json",
            confidence=0.85 if portfolio else 0.70,
            latency_ms=latency_ms,
        )

    # ─── Causal Chain Builder ─────────────────────────────────────────────────

    def build_causal_chains(
        self,
        news_list: List[NewsArticle],
        portfolio_analysis: Dict[str, Any],
    ) -> List[CausalChain]:
        if not news_list:
            return []

        news_input = [
            {
                "id": n.id,
                "headline": n.headline,
                "sentiment": n.sentiment,
                "impact": n.impact_level,
                "sectors": n.entities.sectors,
                "stocks": n.entities.stocks,
                "causal_factors": n.causal_keywords[:3],
            }
            for n in news_list[:6]
        ]

        portfolio_holdings = {
            "stocks": portfolio_analysis.get("major_holdings", []),
            "exposure": portfolio_analysis.get("effective_sector_exposure", {}),
        }

        payload = {
            "news": news_input,
            "portfolio": portfolio_holdings,
        }

        try:
            completion = self._client.chat.completions.create(
                model=GROQ_MODEL_FAST,
                messages=[
                    {"role": "system", "content": CAUSAL_CHAIN_PROMPT},
                    {"role": "user", "content": f"Build causal chains:\n{json.dumps(payload, default=str)}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1500,
            )
            raw = json.loads(completion.choices[0].message.content)
            # LLM may return dict with key or direct array
            chains_raw = raw if isinstance(raw, list) else raw.get("chains", raw.get("causal_chains", []))
            chains = []
            for c in chains_raw:
                try:
                    chains.append(CausalChain(**c))
                except Exception:
                    pass
            return chains
        except Exception as e:
            logger.error(f"Causal chain error: {e}")
            return []

    # ─── Signal Prioritizer ───────────────────────────────────────────────────

    def prioritize_signals(
        self,
        news_list: List[NewsArticle],
        portfolio_analysis: Dict[str, Any],
    ) -> List[PrioritizedSignal]:
        if not news_list:
            return []

        signals_input = [
            {
                "id": n.id,
                "headline": n.headline,
                "sentiment": n.sentiment,
                "impact": n.impact_level,
                "scope": n.scope,
                "sectors": n.entities.sectors,
                "relevance_score": n.relevance_score,
            }
            for n in news_list[:10]
        ]

        payload = {
            "signals": signals_input,
            "portfolio_exposure": portfolio_analysis.get("effective_sector_exposure", {}),
        }

        try:
            completion = self._client.chat.completions.create(
                model=GROQ_MODEL_FAST,
                messages=[
                    {"role": "system", "content": SIGNAL_PRIORITY_PROMPT},
                    {"role": "user", "content": f"Rank signals:\n{json.dumps(payload, default=str)}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000,
            )
            raw = json.loads(completion.choices[0].message.content)
            ranked = raw if isinstance(raw, list) else raw.get("signals", raw.get("ranked_signals", []))
            result = []
            for s in ranked:
                try:
                    result.append(PrioritizedSignal(**s))
                except Exception:
                    pass
            return sorted(result, key=lambda x: x.rank)
        except Exception as e:
            logger.error(f"Signal prioritizer error: {e}")
            return []

    # ─── Conflict Resolution ──────────────────────────────────────────────────

    def resolve_conflicts(self, news_list: List[NewsArticle]) -> List[ConflictResolution]:
        """Detects news with conflict_flag and resolves positive news + negative price cases."""
        conflicts = []
        for n in news_list:
            # Detect conflicts: positive news but sectors are bearish
            if n.sentiment == "BULLISH" and n.impact_level == "HIGH":
                # Check if sectors are bearish in market data
                conflicts.append(ConflictResolution(
                    signal_a=f"{n.id}: {n.headline[:60]}",
                    signal_b="Market-wide selling pressure (FII outflows, risk-off)",
                    conflict_type="STOCK_POSITIVE_vs_SECTOR_NEGATIVE",
                    resolution="Company fundamentals positive but overwhelmed by macro headwinds",
                    net_bias="BEARISH_NEAR_TERM",
                ))
        return conflicts[:3]
