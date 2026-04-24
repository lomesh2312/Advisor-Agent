import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from models.portfolio import Portfolio, StockHolding, MutualFundHolding
from utils.data_loader import DataLoader

logger = logging.getLogger(__name__)

class StressTest(BaseModel):
    scenario: str
    impact_percent: float
    vulnerable_holdings: List[str]
    drawdown_estimate: str

class RiskDiagnostic(BaseModel):
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

class LookThroughResult(BaseModel):
    fund_name: str
    fund_weight: float
    decomposed_sectors: Dict[str, float]
    top_holdings: List[str]
    overlap_detected: bool = False

class PortfolioAnalysis(BaseModel):
    portfolio_id: str
    total_pnl: float
    pnl_percent: float
    top_sector: str
    effective_sector_exposure: Dict[str, float]
    risk_diagnostics: RiskDiagnostic
    stress_tests: List[StressTest]
    major_holdings: List[MajorHolding]
    total_current_value: float
    look_through_details: List[LookThroughResult]

def get_current_nav(mf: MutualFundHolding) -> float:
    nav = mf.current_nav if mf.current_nav is not None else mf.current_price
    return nav if nav is not None else mf.avg_nav

def get_total_current_value(portfolio: Portfolio) -> float:
    total = sum(s.current_price * s.quantity for s in portfolio.holdings.stocks)
    total += sum(get_current_nav(m) * m.units for m in portfolio.holdings.mutual_funds)
    return total

def calculate_pnl(portfolio: Portfolio) -> tuple[float, float]:
    total_pnl = 0.0
    total_investment = 0.0
    for stock in portfolio.holdings.stocks:
        investment = stock.avg_buy_price * stock.quantity
        total_investment += investment
        total_pnl += (stock.current_price - stock.avg_buy_price) * stock.quantity
    for mf in portfolio.holdings.mutual_funds:
        investment = mf.avg_nav * mf.units
        total_investment += investment
        total_pnl += (get_current_nav(mf) - mf.avg_nav) * mf.units
    pnl_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0
    return round(total_pnl, 2), round(pnl_percent, 2)

def compute_effective_sector_exposure(portfolio: Portfolio, data_loader: DataLoader) -> Dict[str, float]:
    effective_sectors = {}
    total_current_value = get_total_current_value(portfolio)
    if total_current_value == 0: return {}

    for stock in portfolio.holdings.stocks:
        sector = stock.sector.upper()
        val = stock.current_price * stock.quantity
        effective_sectors[sector] = effective_sectors.get(sector, 0.0) + val

    symbol_to_sector = {}
    mapping_obj = data_loader.get_sector_mapping()
    if mapping_obj and hasattr(mapping_obj, 'sectors'):
        for sector_name, sector_data in mapping_obj.sectors.items():
            if hasattr(sector_data, 'stocks'):
                for symbol in sector_data.stocks:
                    symbol_to_sector[symbol] = sector_name

    for mf in portfolio.holdings.mutual_funds:
        mf_val = get_current_nav(mf) * mf.units
        holdings = mf.top_holdings or []
        if not holdings:
            effective_sectors["OTHER"] = effective_sectors.get("OTHER", 0.0) + mf_val
            continue
        weight_per_holding = mf_val / len(holdings)
        for stock_symbol in holdings:
            sector = symbol_to_sector.get(stock_symbol, "OTHER").upper()
            effective_sectors[sector] = effective_sectors.get(sector, 0.0) + weight_per_holding

    exposure = {sector: round((val / total_current_value) * 100, 2) for sector, val in effective_sectors.items()}
    return dict(sorted(exposure.items(), key=lambda x: x[1], reverse=True))

def compute_look_through_details(portfolio: Portfolio, data_loader: DataLoader) -> List[LookThroughResult]:
    look_through = []
    total_val = get_total_current_value(portfolio)
    if total_val == 0: return []

    symbol_to_sector = {}
    mapping_obj = data_loader.get_sector_mapping()
    if mapping_obj and hasattr(mapping_obj, 'sectors'):
        for sector_name, sector_data in mapping_obj.sectors.items():
            if hasattr(sector_data, 'stocks'):
                for symbol in sector_data.stocks:
                    symbol_to_sector[symbol] = sector_name

    for mf in portfolio.holdings.mutual_funds:
        mf_val = get_current_nav(mf) * mf.units
        weight = round((mf_val / total_val) * 100, 2)
        
        sectors = {}
        holdings = mf.top_holdings or []
        if holdings:
            per_holding = 100.0 / len(holdings)
            for s in holdings:
                sec = symbol_to_sector.get(s, "OTHER").upper()
                sectors[sec] = sectors.get(sec, 0.0) + per_holding
        
        look_through.append(LookThroughResult(
            fund_name=mf.scheme_name,
            fund_weight=weight,
            decomposed_sectors={k: round(v, 2) for k, v in sectors.items()},
            top_holdings=holdings[:5]
        ))
    return look_through

def calculate_hhi(effective_exposure: Dict[str, float]) -> float:
    # HHI = sum of squared market shares
    total = sum(effective_exposure.values())
    if total == 0: return 0
    hhi = sum(((val / total) * 100)**2 for val in effective_exposure.values())
    return round(hhi, 2)

def run_stress_tests(effective_exposure: Dict[str, float]) -> List[StressTest]:
    scenarios = []
    # Banking Correction
    banking_exp = effective_exposure.get("BANKING", 0)
    scenarios.append(StressTest(
        scenario="Banking Sector -10% Correction",
        impact_percent=round(-(banking_exp * 0.1), 2),
        vulnerable_holdings=["HDFCBANK", "ICICIBANK", "SBIN"],
        drawdown_estimate=f"Est. {banking_exp * 0.1:.1f}% portfolio drag"
    ))
    # Crude Oil Spike
    energy_exp = effective_exposure.get("ENERGY", 0)
    scenarios.append(StressTest(
        scenario="Crude Oil Price Spike ($100/bbl)",
        impact_percent=round(energy_exp * 0.05 - 2.0, 2), # Negative net impact usually
        vulnerable_holdings=["RELIANCE", "BPCL", "ONGC"],
        drawdown_estimate="Supply chain cost escalation risk"
    ))
    # FII Outflow
    scenarios.append(StressTest(
        scenario="FII Mass Outflow Event",
        impact_percent=-4.5,
        vulnerable_holdings=["Large Caps", "Index Heavyweights"],
        drawdown_estimate="Broad market liquidity squeeze"
    ))
    return scenarios

def build_portfolio_analysis(portfolio: Portfolio, data_loader: DataLoader) -> PortfolioAnalysis:
    total_pnl, pnl_percent = calculate_pnl(portfolio)
    effective_exposure = compute_effective_sector_exposure(portfolio, data_loader)
    hhi = calculate_hhi(effective_exposure)
    
    top_sector_weight = max(effective_exposure.values()) if effective_exposure else 0.0
    div_score = round(max(0, 100 - (hhi / 100)), 2)
    
    risk_diagnostics = RiskDiagnostic(
        hhi=hhi,
        hhi_status="CONCENTRATED" if hhi > 2500 else "MODERATE" if hhi > 1500 else "DIVERSIFIED",
        overlap_risk="HIGH" if any(v > 40 for v in effective_exposure.values()) else "LOW",
        beta_sensitivity=1.12 if hhi > 2000 else 0.95,
        rate_sensitivity="HIGH" if effective_exposure.get("BANKING", 0) > 30 else "MODERATE",
        sector_concentration_risk=f"{top_sector_weight}% in Top Sector",
        diversification_score=div_score,
        top_sector_weight=top_sector_weight
    )

    major_holdings = []
    total_val = get_total_current_value(portfolio)
    for stock in portfolio.holdings.stocks:
        major_holdings.append(MajorHolding(name=stock.symbol, weight=round((stock.current_price * stock.quantity / total_val * 100), 2)))
    for mf in portfolio.holdings.mutual_funds:
        major_holdings.append(MajorHolding(name=mf.scheme_name, weight=round((get_current_nav(mf) * mf.units / total_val * 100), 2)))
    major_holdings.sort(key=lambda x: x.weight, reverse=True)

    return PortfolioAnalysis(
        portfolio_id=portfolio.id, total_pnl=total_pnl, pnl_percent=pnl_percent,
        top_sector=list(effective_exposure.keys())[0] if effective_exposure else "NONE",
        effective_sector_exposure=effective_exposure,
        risk_diagnostics=risk_diagnostics,
        stress_tests=run_stress_tests(effective_exposure),
        major_holdings=major_holdings[:5],
        total_current_value=total_val,
        look_through_details=compute_look_through_details(portfolio, data_loader)
    )
