# Autonomous Financial Advisor Agent

## Overview

**Autonomous Financial Advisor Agent** is an AI-powered multi-agent portfolio intelligence system that combines:

* Quantitative portfolio analytics
* Causal financial reasoning using LLMs
* Stress testing and risk diagnostics
* Institutional-style investment recommendations
* Independent reasoning evaluation/audit layer
* Interactive Streamlit intelligence dashboard
* FastAPI backend for API-driven deployment
* Observability with Langfuse tracing

Rather than acting as a simple chatbot or rule-based investment tool, this project behaves like an **autonomous portfolio research copilot**, generating **CIO-style diagnostic reports** using structured portfolio data, market signals, news catalysts, and LLM reasoning.

---

# Architecture

## System Architecture

```text
                    ┌─────────────────────────┐
                    │  Streamlit Frontend UI  │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │      FastAPI Backend    │
                    └──────────┬──────────────┘
                               │
      ┌────────────────────────┼────────────────────────┐
      ▼                        ▼                        ▼
┌──────────────┐       ┌───────────────┐       ┌────────────────┐
│ Data Loader  │       │Portfolio Engine│      │ Reasoning Engine│
│JSON Datasets │       │ Risk Analytics │      │ Groq LLM Agent  │
└──────┬───────┘       └──────┬────────┘       └────────┬───────┘
       │                      │                         │
       ▼                      ▼                         ▼
 Portfolio Data      Stress Tests / Exposure      Advisor Report
 Market Data         Concentration Metrics        Causal Chains
 News Data           Look-through Analysis        Rebalancing Actions
       │                                              │
       └──────────────────────┬───────────────────────┘
                              ▼
                     ┌─────────────────┐
                     │ Audit Evaluator │
                     │  Report Scoring │
                     └─────────────────┘
```

---

# Key Features

## 1. Institutional Portfolio Analytics

### Computes:

* Portfolio P&L analysis
* Sector exposure decomposition
* Mutual fund look-through analysis
* Diversification diagnostics
* Herfindahl concentration (HHI)
* Beta sensitivity estimation
* Sector concentration risk
* Portfolio overlap detection
* Stress test simulations

### Risk Metrics Generated

Examples:

* Diversification Score
* Top Sector Weight
* Concentration Risk
* Beta Sensitivity
* Rate Sensitivity
* Overlap Risk
* Drawdown Stress Scenarios

---

## 2. AI Advisor Report Generator

Uses Groq LLM (`llama-3.1-8b-instant` / configurable) to generate:

* Executive summary
* Market sentiment diagnosis
* Causal driver chains
* Material risks
* Stress test scenarios
* Sector intelligence view
* Strategic rebalancing actions
* Final portfolio diagnosis

Output is structured through Pydantic schemas for consistency.

---

## 3. Causal Reasoning Engine

Models financial causality:

```text
News Event
→ Macro Variable
→ Sector Impact
→ Affected Holdings
→ Portfolio P&L Impact
```

Example:

```text
Oil Shock
→ Inflation Pressure
→ Energy Outperforms
→ Reliance Overweight Benefits
→ Portfolio Positive Impact
```

Supports:

* Signal prioritization
* Conflict resolution
* Portfolio-linked reasoning
* Impact confidence scoring

---

## 4. Independent Audit / Evaluation Agent

Separate LLM-based evaluator scores generated reports.

### Rubric (10-point)

* News Usage (4)
* Sector Reasoning (3)
* Portfolio Linkage (3)

Penalties:

* Generic reasoning
* Missing quantified impacts

Returns:

* Audit Score
* Risk Grade (A–F)
* Critique
* Coverage feedback

This acts like a reasoning quality validator.

---

## 5. Streamlit Intelligence Dashboard

Includes:

* Portfolio selector
* Executive risk dashboard
* Exposure analytics charts
* Causal reasoning tab
* Stress testing view
* Rebalancing recommendations
* Audit metrics visualization

Built using:

* Streamlit
* Plotly
* Pandas

---

## 6. Observability

Integrated with Langfuse:

* LLM traces
* Prompt observability
* Agent monitoring
* Run diagnostics

---

# Tech Stack

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* Groq API
* Langfuse

## Frontend

* Streamlit
* Plotly
* Pandas

## AI / Agent Components

* Llama models via Groq
* Prompt engineered reasoning agents
* Evaluation agent
* Causal signal ranking agent

## Deployment

* Render
* Gunicorn

---

# Repository Structure

```bash
Advisor-Agent/
│
├── app_ui.py                     # Streamlit dashboard
├── main.py                       # FastAPI application
├── config.py                     # Configuration/env settings
├── requirements.txt
├── render.yaml
│
├── data/
│   ├── portfolios.json
│   ├── market_data.json
│   ├── news_data.json
│   ├── mutual_funds.json
│   ├── sector_mapping.json
│   └── historical_data.json
│
├── models/
│   ├── portfolio.py
│   ├── market.py
│   ├── news.py
│   └── schemas.py
│
├── services/
│   ├── advisor_service.py
│   ├── reasoning_service.py
│   ├── portfolio_analytics.py
│   ├── evaluation_service.py
│   └── observability.py
│
└── utils/
    └── data_loader.py
```

---

# Core Modules Explained

# 1. Data Layer (`utils/data_loader.py`)

Loads and validates:

* Portfolio holdings
* Market datasets
* News signals
* Mutual fund data
* Sector mappings
* Historical data

Uses Pydantic models for schema validation.

Features:

* Cached loading
* JSON parsing
* Model mapping
* NAV fallback handling
* Sector lookup decomposition

---

# 2. Portfolio Analytics Engine (`services/portfolio_analytics.py`)

## Major Functions

### calculate_pnl()

Computes:

```python
Profit/Loss
P&L %
```

---

### compute_effective_sector_exposure()

Combines:

* Direct stock exposure
* Mutual fund indirect exposure

Creates effective look-through sector weights.

---

### compute_look_through_details()

Decomposes mutual funds into:

* Hidden sector exposures
* Underlying holdings
* Overlap detection

Institutional-style look-through analysis.

---

### Stress Tests

Simulates scenarios like:

* Rate hikes
* Sector crashes
* Market drawdowns

Produces drawdown impact estimates.

---

# 3. Advisor Service (`advisor_service.py`)

Generates structured advisor reports.

## Schema Objects

### CausalChain

```python
Event
Macro Variable
Sector Impact
Affected Holdings
Estimated Impact
Confidence
Strength
```

---

### StrategicRecommendation

Contains:

* Current allocation
* Target allocation
* Allocation shift
* Benefit
* Trade-offs

---

### SectorIntelligence

Provides:

* Trend signal
* Macro rationale
* Sector impact analysis

---

# 4. Reasoning Service (`reasoning_service.py`)

Implements agent reasoning logic.

Prompts include:

* Chat system prompt
* Causal chain prompt
* Signal prioritization prompt

Supports:

* Portfolio-grounded answers
* News-driven causal chains
* Prioritized signal ranking
* Conflict resolution

---

# 5. Evaluation Service (`evaluation_service.py`)

Second-agent quality validator.

Returns:

```json
{
 score,
 rating,
 feedback,
 risk_grade,
 critique
}
```

Useful for:

* Agent self-evaluation
* Reasoning audits
* Hallucination reduction

---

# API Endpoints

## Root

```http
GET /
```

Returns:

```json
{
 "app":"Institutional Financial Advisor",
 "version":"0.1.7",
 "status":"active"
}
```

---

## List Portfolios

```http
GET /portfolios
```

Returns all sample portfolios.

---

## Generate Advisor Evaluation

```http
GET /api/advisor-evaluation/{portfolio_id}
```

Pipeline:

1 Portfolio analytics

2 Market context

3 Advisor report generation

4 Audit scoring

Response includes:

* Portfolio analysis
* Advisor report
* Evaluation report

---

# Data Models

## Portfolio Model

Contains:

* Stocks
* Mutual funds
* Risk profile
* Asset allocation
* Risk metrics

---

## Market Model

Includes:

* Indices
* Sector performance
* Macro signals
* Stock-level market data

---

## News Model

Contains:

* Sentiment
* Impact level
* Sector entities
* Causal keywords
* Relevance score

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/advisor-agent.git
cd advisor-agent
```

---

## Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create `.env`

```env
GROQ_API_KEY=your_key
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

# Running Backend

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

Runs on:

```bash
http://localhost:8000
```

---

# Running Streamlit UI

```bash
streamlit run app_ui.py
```

---

# Deployment (Render)

Included:

```yaml
render.yaml
```

Uses:

* Free Render web service
* Python runtime
* Gunicorn/Uvicorn startup
* Environment secret injection

---

# Example Workflow

```text
User selects portfolio
↓
Portfolio analytics engine runs
↓
Market + news context loaded
↓
LLM advisor generates report
↓
Evaluation agent audits report
↓
Dashboard shows intelligence output
```

---

# Example Use Cases

## Portfolio Risk Copilot

Analyze concentrated portfolios.

---

## Wealth Advisory Intelligence

Generate CIO-style portfolio diagnostics.

---

## Multi-Agent Financial Reasoning Research

Experiment with:

* Agentic finance systems
* Causal reasoning pipelines
* Self-evaluating agents

---

## Educational / Demonstration Platform

Demonstrates:

* Agent architecture
* Financial AI reasoning
* LLM structured outputs

---

# Project Highlights

## Institutional Concepts Implemented

✅ Look-through fund decomposition
✅ HHI concentration analysis
✅ Stress testing
✅ Sector risk diagnostics
✅ Causal market reasoning
✅ Independent evaluator agent
✅ Rebalancing intelligence
✅ Observability tracing

---

# Novel Aspects of the Project

What makes this stronger than a standard chatbot project:

## Not just Q&A

It combines:

* Quant models
* LLM reasoning
* Audit layer
* Decision support

---

## Multi-Agent Design

Distinct agent roles:

* Analyst agent
* Advisor agent
* Evaluator agent

This resembles practical agent orchestration.

---

## Structured Reasoning Outputs

Not plain text generation.

Produces typed financial intelligence objects.

---

# Potential Future Improvements

Possible extensions:

* Real-time market APIs
* RAG over financial research
* Vector memory for portfolio history
* Scenario Monte Carlo simulation
* Multi-LLM routing
* Autonomous trade policy engine
* Live broker integrations
* Fine-tuned financial reasoning model

---

# Sample Screens / Modules

Dashboard sections:

```text
Executive Summary
Exposure Analytics
Causal Reasoning
Risk & Stress
Rebalancing
Audit Score
```

---

# Requirements

```text
fastapi
uvicorn
pydantic
python-dotenv
groq
langfuse
streamlit
plotly
pandas
requests
gunicorn
```

---

# Performance Notes

Includes:

* Latency tracking
* Confidence levels
* Fallback defaults
* Exception handling
* Safe observability flush
* Compatibility response formatting

---

# Why This Project Matters

This project sits at intersection of:

* Agentic AI
* Quant Finance
* Explainable Reasoning
* Portfolio Intelligence
* Autonomous Decision Support

It goes beyond traditional CRUD finance dashboards and moves toward **autonomous financial research agents**.

---

# Authoring Concepts Demonstrated

This project demonstrates understanding of:

* FastAPI system design
* Pydantic modeling
* Agent orchestration
* Prompt engineering
* Financial analytics
* Explainable AI reasoning
* Evaluation pipelines
* Observability tooling
* Full-stack deployment

---

# License

MIT License

---

# Acknowledgements

Built with:

* Groq
* FastAPI
* Streamlit
* Plotly
* Langfuse
* Pydantic

---

## One-Line Summary

**An autonomous multi-agent financial intelligence platform that performs portfolio analytics, causal reasoning, risk diagnostics, and self-audited investment recommendations through FastAPI + Streamlit + LLM agents.**
