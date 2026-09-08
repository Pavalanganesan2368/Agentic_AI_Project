# AI E-Commerce Customer Support Agent

An academic internship project demonstrating an agentic customer-support workflow for e-commerce. The application combines product retrieval, persistent customer memory, order tools, returns, recommendations, complaint logging, and a Streamlit dashboard.

## Features

- Catalog ingestion from CSV with persisted local retrieval index
- Grounded product answers containing catalog price and availability
- Intent routing for product search, orders, returns, recommendations, and complaints
- Persistent SQLite customer interactions, returns, complaints, tier, and preferences
- Order lookup with customer ownership checks
- Return-window validation, RA generation, refund amount, and shipping instructions
- Recommendations from query and interaction history
- Friendly validation and error handling
- Tests for retrieval, persistence, order status, returns, recommendations, routing, and inputs

## Architecture

```text
Customer -> Streamlit UI -> SupportAgent -> Intent Router
                                      |-> ProductCatalog retrieval
                                      |-> Order / Return tools -> SQLite memory
                                      |-> Recommendation tool
                                      |-> Complaint tool
                                      -> Grounded response -> Customer
```

The default implementation is deterministic and offline-friendly. The `ProductCatalog` class is the vector-store boundary: it currently uses a persisted TF-IDF-like index, and can be replaced by FAISS or Chroma without changing the agent or UI. An LLM provider can be added behind `SupportAgent` using environment configuration; no credentials are required for the included demo.

## Project structure

```text
app.py                 Streamlit entry point
src/config.py          Environment-backed settings
src/catalog.py         Catalog ingestion and retrieval
src/database.py        SQLite memory and persistence
src/tools.py           Order, return, recommendation, complaint tools
src/agent.py           Intent routing and response generation
src/models.py          Typed domain models
data/products.csv      Sample product catalog
data/orders.json       Sample orders
tests/                 Pytest suite
```

## Installation

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Never commit `.env`; API keys and payment information are not stored by this project.

## Run

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit. Use customer ID `demo-user` to try the included order `ORD-1001`. The chat can answer queries such as `wireless headphones`, track an order, recommend products, or log a complaint.

## Test

```bash
pytest -q
```

## Security notes

The demo deliberately stores no card numbers, passwords, tokens, or payment credentials. Production deployment should add authenticated customer identity, encrypted sensitive contact fields, rate limits, audit logging, and PCI-compliant payment-provider integrations. Shipping and payment APIs should be wrapped with timeouts and retries before being enabled.
