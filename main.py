import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
from contextlib import asynccontextmanager

from utils.data_loader import DataLoader
from services.portfolio_analytics import build_portfolio_analysis
from services.advisor_service import generate_advisor_report
from services.evaluation_service import evaluate_advisor_report

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
logger = logging.getLogger("main")

# Initialize global data loader
data_loader = DataLoader()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Institutional Financial Advisor Agent v0.1.7")
    yield
    logger.info("Shutting down Institutional Financial Advisor Agent")

app = FastAPI(title="Financial Advisor Agent API", version="0.1.7", lifespan=lifespan)

# Robust CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    return {"app": "Institutional Financial Advisor", "version": "0.1.7", "status": "active"}

@app.get("/portfolios")
async def get_portfolios():
    """Returns a list of all portfolios for the dashboard."""
    portfolios = data_loader.get_portfolios()
    return {
        "portfolios": [
            {"portfolio_id": p.id, "user_name": p.user_name}
            for p in portfolios.values()
        ]
    }

@app.get("/api/advisor-evaluation/{portfolio_id}")
async def get_advisor_evaluation(portfolio_id: str):
    logger.info(f"Processing institutional evaluation for portfolio: {portfolio_id}")
    
    try:
        portfolio = data_loader.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            all_portfolios = data_loader.get_portfolios()
            if portfolio_id in all_portfolios:
                portfolio = all_portfolios[portfolio_id]
            else:
                raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

        # 1. Quantitative Analysis (Institutional Look-through)
        portfolio_analysis = build_portfolio_analysis(portfolio, data_loader)
        
        # 2. Market Context
        market_data = data_loader.get_market_data()
        market_sentiment_val = market_data.metadata.sentiment if market_data and hasattr(market_data.metadata, 'sentiment') else "NEUTRAL"
        market_context = {
            "market_sentiment": market_sentiment_val,
            "sector_trends": {k: v.sentiment for k, v in market_data.sector_performance.items()} if market_data else {},
            "news": data_loader.get_news()[:10]
        }

        # 3. Generate Strategic Report
        advisor_report = generate_advisor_report(market_context, portfolio_analysis.dict())

        # 4. Independent Audit
        evaluation = evaluate_advisor_report(advisor_report)

        # Build extremely compatible response
        response_data = {
            "portfolio_id": portfolio_id,
            "market_sentiment": market_sentiment_val, # Compatibility at root
            "portfolio_analysis": portfolio_analysis.dict(),
            "advisor_report": advisor_report.dict(),
            "evaluation": evaluation.dict()
        }
        
        # Add a "report" key for even older frontend compatibility if needed
        response_data["report"] = response_data["advisor_report"]
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal error in evaluation: {e}", exc_info=True)
        return {"error": "Failed to generate evaluation", "detail": str(e)}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
