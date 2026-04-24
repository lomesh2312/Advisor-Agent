import logging
import json
from typing import Dict, Any
from pydantic import BaseModel
from groq import Groq
from config import GROQ_API_KEY
try:
    from services.observability import langfuse, safe_flush
except ImportError:
    langfuse = None
    def safe_flush(): pass

logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    score: float
    rating: str
    feedback: str
    news_usage_score: float
    sector_reasoning_score: float
    portfolio_linkage_score: float
    penalties_applied: float
    risk_grade: str = "B"
    critique: str = ""

EVALUATION_SYSTEM_PROMPT = """You are a Senior Portfolio Auditor. Evaluate report on 10-point rubric.
SCORING (10): NEWS(4), SECTOR(3), PORTFOLIO LINKAGE(3).
PENALTIES: GENERIC LANGUAGE(-1), MISSING %(-1).
Return JSON: {"score":float,"rating":"HIGH|GOOD|MEDIUM|LOW","feedback":"string","news_usage_score":float,"sector_reasoning_score":float,"portfolio_linkage_score":float,"penalties_applied":float,"risk_grade":"A|B|C|D|F","critique":"string"}"""

def evaluate_advisor_report(report: Any) -> EvaluationResult:
    try:
        report_dict = report.model_dump() if hasattr(report, "model_dump") else report
        client = Groq(api_key=GROQ_API_KEY)
        audit_input = {
            "summary": report_dict.get("reasoning_summary"),
            "causal_chains": report_dict.get("causal_drivers", [])[:3],
            "risks": report_dict.get("material_risks", [])[:2],
            "actions": report_dict.get("strategic_actions", [])[:2]
        }
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": EVALUATION_SYSTEM_PROMPT}, {"role": "user", "content": f"Audit this Report:\n{json.dumps(audit_input)}"}],
            response_format={"type": "json_object"}, temperature=0.1
        )
        data = json.loads(completion.choices[0].message.content)
        safe_flush()
        return EvaluationResult(**data)
    except Exception as e:
        logger.error(f"Evaluator Error: {e}")
        safe_flush()
        return EvaluationResult(score=0.0, rating="LOW", feedback=str(e), news_usage_score=0, sector_reasoning_score=0, portfolio_linkage_score=0, penalties_applied=0, risk_grade="C", critique="Analysis coverage complete.")
