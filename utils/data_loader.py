import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

from config import DATA_DIR
from models.portfolio import Portfolio, Holdings, StockHolding, MutualFundHolding, PortfolioAnalytics, RiskMetrics, DaySummary
from models.market import MarketData, MarketMetadata, Index, SectorPerformance, Stock, MacroSignals
from models.news import NewsArticle, NewsEntities

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads and caches all data from the data/ folder.
    Maps exact JSON key structure to Pydantic models.
    """

    def __init__(self):
        self._portfolios: Dict[str, Portfolio] = {}
        self._market_data: Optional[MarketData] = None
        self._news: List[NewsArticle] = []
        self._sector_mapping: Optional[Dict] = None
        self._mutual_funds: Optional[Dict] = None
        self._historical_data: Optional[Dict] = None
        self._load_all()


    def _load_json(self, filename: str) -> Optional[Dict]:
        path = DATA_DIR / filename
        if not path.exists():
            logger.warning(f"Data file not found: {path}")
            return None
        with open(path, "r") as f:
            return json.load(f)

    def _load_all(self):
        self._load_portfolios()
        self._load_market_data()
        self._load_news()
        self._load_sector_mapping()
        self._load_mutual_funds()
        self._load_historical_data()
        logger.info(
            f"DataLoader: {len(self._portfolios)} portfolios | "
            f"{len(self._news)} news articles | "
            f"Market data: {'loaded' if self._market_data else 'missing'}"
        )

    def _load_portfolios(self):
        raw = self._load_json("portfolios.json")
        if not raw:
            return
        for pid, p in raw.get("portfolios", {}).items():
            try:

                stocks = [StockHolding(**s) for s in p["holdings"].get("stocks", [])]


                mf_list = []
                for mf in p["holdings"].get("mutual_funds", []):

                    if "current_nav" not in mf or mf["current_nav"] is None:
                        mf["current_nav"] = mf.get("current_price", mf.get("avg_nav"))
                    mf_list.append(MutualFundHolding(**mf))

                holdings = Holdings(stocks=stocks, mutual_funds=mf_list)


                rm_raw = p["analytics"]["risk_metrics"]
                risk_metrics = RiskMetrics(
                    concentration_risk=rm_raw.get("concentration_risk", False),
                    single_stock_max_weight=rm_raw.get("single_stock_max_weight", 0.0),
                    single_sector_max_weight=rm_raw.get("single_sector_max_weight", 0.0),
                    beta=rm_raw.get("beta", 1.0),
                    volatility=rm_raw.get("volatility", "MODERATE"),
                    concentration_warning=rm_raw.get("concentration_warning"),
                )


                ds_raw = p["analytics"]["day_summary"]
                day_summary = DaySummary(
                    day_change_absolute=ds_raw.get("day_change_absolute", 0.0),
                    day_change_percent=ds_raw.get("day_change_percent", 0.0),
                    top_gainer=ds_raw.get("top_gainer"),
                    top_loser=ds_raw.get("top_loser"),
                )

                analytics = PortfolioAnalytics(
                    sector_allocation=p["analytics"].get("sector_allocation", {}),
                    asset_type_allocation=p["analytics"].get("asset_type_allocation", {}),
                    risk_metrics=risk_metrics,
                    day_summary=day_summary,
                )

                portfolio = Portfolio(
                    id=pid,
                    user_id=p["user_id"],
                    user_name=p["user_name"],
                    portfolio_type=p["portfolio_type"],
                    risk_profile=p["risk_profile"],
                    investment_horizon=p["investment_horizon"],
                    description=p["description"],
                    total_investment=p["total_investment"],
                    current_value=p["current_value"],
                    overall_gain_loss=p["overall_gain_loss"],
                    overall_gain_loss_percent=p["overall_gain_loss_percent"],
                    holdings=holdings,
                    analytics=analytics,
                )
                self._portfolios[pid] = portfolio
            except Exception as e:
                logger.error(f"Failed to parse portfolio {pid}: {e}", exc_info=True)

    def _load_market_data(self):
        raw = self._load_json("market_data.json")
        if not raw:
            return
        try:
            meta_raw = raw["metadata"]
            metadata = MarketMetadata(
                date=meta_raw["date"],
                market_status=meta_raw["market_status"],
                currency=meta_raw["currency"],
                sentiment="BEARISH",  
            )


            indices: Dict[str, Index] = {}
            for k, v in raw.get("indices", {}).items():
                try:
                    indices[k] = Index(
                        name=v["name"],
                        current_value=v["current_value"],
                        previous_close=v["previous_close"],
                        change_percent=v["change_percent"],
                        change_absolute=v["change_absolute"],
                        day_high=v["day_high"],
                        day_low=v["day_low"],
                        sentiment=v["sentiment"],
                    )
                except Exception as e:
                    logger.warning(f"Skipping index {k}: {e}")


            nifty = indices.get("NIFTY50")
            sensex = indices.get("SENSEX")
            if nifty and sensex:
                if nifty.sentiment == "BULLISH" and sensex.sentiment == "BULLISH":
                    metadata.sentiment = "BULLISH"
                elif nifty.sentiment == "BEARISH" and sensex.sentiment == "BEARISH":
                    metadata.sentiment = "BEARISH"
                else:
                    metadata.sentiment = "NEUTRAL"


            sector_perf: Dict[str, SectorPerformance] = {}
            for k, v in raw.get("sector_performance", {}).items():
                try:
                    sector_perf[k] = SectorPerformance(
                        change_percent=v["change_percent"],
                        sentiment=v["sentiment"],
                        key_drivers=v.get("key_drivers", []),
                        top_gainers=v.get("top_gainers", []),
                        top_losers=v.get("top_losers", []),
                    )
                except Exception as e:
                    logger.warning(f"Skipping sector {k}: {e}")


            stocks: Dict[str, Stock] = {}
            for symbol, v in raw.get("stocks", {}).items():
                try:
                    stocks[symbol] = Stock(
                        symbol=symbol,
                        name=v["name"],
                        sector=v["sector"],
                        sub_sector=v.get("sub_sector"),
                        current_price=v["current_price"],
                        previous_close=v["previous_close"],
                        change_percent=v["change_percent"],
                        change_absolute=v["change_absolute"],
                        volume=v["volume"],
                        avg_volume_20d=v.get("avg_volume_20d"),
                        market_cap_cr=v.get("market_cap_cr"),
                        pe_ratio=v.get("pe_ratio"),
                        beta=v.get("beta"),
                        week_52_high=v.get("52_week_high"),
                        week_52_low=v.get("52_week_low"),
                    )
                except Exception as e:
                    logger.warning(f"Skipping stock {symbol}: {e}")

            self._market_data = MarketData(
                metadata=metadata,
                indices=indices,
                sector_performance=sector_perf,
                stocks=stocks,
            )
        except Exception as e:
            logger.error(f"Failed to parse market data: {e}", exc_info=True)

    def _load_news(self):
        raw = self._load_json("news_data.json")
        if not raw:
            return
        for article in raw.get("news", []):
            try:
                ent_raw = article.get("entities", {})
                entities = NewsEntities(
                    sectors=ent_raw.get("sectors", []),
                    stocks=ent_raw.get("stocks", []),
                    macro_variables=ent_raw.get("keywords", []),
                )

                sentiment_raw = article.get("sentiment", "NEUTRAL")

                sentiment_map = {
                    "POSITIVE": "BULLISH",
                    "NEGATIVE": "BEARISH",
                    "MIXED": "NEUTRAL",
                    "NEUTRAL": "NEUTRAL",
                    "BULLISH": "BULLISH",
                    "BEARISH": "BEARISH",
                }
                sentiment = sentiment_map.get(sentiment_raw.upper(), "NEUTRAL")

                news_article = NewsArticle(
                    id=article["id"],
                    date=article.get("published_at", "")[:10],
                    headline=article["headline"],
                    summary=article["summary"],
                    source=article["source"],
                    sentiment=sentiment,
                    impact_level=article.get("impact_level", "MEDIUM"),
                    scope=article.get("scope", "MARKET"),
                    entities=entities,
                    relevance_score=abs(article.get("sentiment_score", 0.5)),
                    causal_keywords=ent_raw.get("keywords", []),
                )
                self._news.append(news_article)
            except Exception as e:
                logger.warning(f"Skipping news {article.get('id')}: {e}")

    def _load_sector_mapping(self):
        self._sector_mapping = self._load_json("sector_mapping.json")

    def _load_mutual_funds(self):
        self._mutual_funds = self._load_json("mutual_funds.json")

    def _load_historical_data(self):
        self._historical_data = self._load_json("historical_data.json")



    def get_portfolios(self) -> Dict[str, Portfolio]:
        return self._portfolios

    def get_portfolio_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        return self._portfolios.get(portfolio_id)

    def list_portfolio_ids(self) -> List[str]:
        return list(self._portfolios.keys())

    def get_market_data(self) -> Optional[MarketData]:
        return self._market_data

    def get_news(self, limit: int = 25) -> List[NewsArticle]:
        return self._news[:limit]

    def get_news_by_sector(self, sector: str) -> List[NewsArticle]:
        return [
            n for n in self._news
            if sector.upper() in [s.upper() for s in n.entities.sectors]
        ]

    def get_news_by_stock(self, symbol: str) -> List[NewsArticle]:
        return [
            n for n in self._news
            if symbol.upper() in [s.upper() for s in n.entities.stocks]
        ]

    def get_high_impact_news(self) -> List[NewsArticle]:
        return [n for n in self._news if n.impact_level == "HIGH"]

    def get_sector_mapping(self) -> Optional[Dict]:
        return self._sector_mapping

    def get_symbol_to_sector_map(self) -> Dict[str, str]:
        """Returns {SYMBOL: SECTOR_NAME} from sector_mapping.json"""
        mapping = {}
        if not self._sector_mapping:
            return mapping
        for sector_name, sector_data in self._sector_mapping.get("sectors", {}).items():
            for symbol in sector_data.get("stocks", []):
                mapping[symbol] = sector_name
        return mapping

    def get_macro_correlations(self) -> Dict[str, Any]:
        if not self._sector_mapping:
            return {}
        return self._sector_mapping.get("macro_correlations", {})

    def get_defensive_sectors(self) -> List[str]:
        if not self._sector_mapping:
            return []
        return self._sector_mapping.get("defensive_sectors", [])

    def get_rate_sensitive_sectors(self) -> List[str]:
        if not self._sector_mapping:
            return []
        return self._sector_mapping.get("rate_sensitive_sectors", [])

    def get_stock_info(self, symbol: str) -> Optional[Stock]:
        if self._market_data:
            return self._market_data.stocks.get(symbol)
        return None

    def get_mutual_funds_data(self) -> Optional[Dict]:
        return self._mutual_funds

    def get_historical_data(self) -> Optional[Dict]:
        return self._historical_data

    def get_sector_performance(self, sector: str) -> Optional[SectorPerformance]:
        if self._market_data:
            return self._market_data.sector_performance.get(sector)
        return None

    def get_news_relevant_to_portfolio(self, portfolio: Any, limit: int = 10) -> List[NewsArticle]:
        """Returns news relevant to the holdings of a portfolio"""
        stock_symbols = {s.symbol for s in portfolio.holdings.stocks}
        mf_holdings = set()
        for mf in portfolio.holdings.mutual_funds:
            mf_holdings.update(mf.top_holdings)

        all_symbols = stock_symbols | mf_holdings
        portfolio_sectors = {s.sector for s in portfolio.holdings.stocks}

        relevant = []
        seen = set()

        for article in self._news:
            if article.id in seen:
                continue
            if any(sym in article.entities.stocks for sym in all_symbols):
                relevant.append(article)
                seen.add(article.id)


        for article in self._news:
            if article.id in seen:
                continue
            if any(sec in article.entities.sectors for sec in portfolio_sectors):
                relevant.append(article)
                seen.add(article.id)


        for article in self._news:
            if article.id in seen:
                continue
            if article.scope == "MARKET_WIDE" and article.impact_level == "HIGH":
                relevant.append(article)
                seen.add(article.id)

        # Sort by relevance score desc
        relevant.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant[:limit]
