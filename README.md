# Crypto Fraud Attribution MVP

A hackathon-ready prototype implementing the PRD's final MVP flow:

Victim report → case creation → wallet validation → transaction collection → transaction graph → 3–5 hop tracing → entity detection → rule-based risk scoring → investigation dashboard → monitoring alerts → PDF report.

## What works
- Create an investigation case
- Validate an EVM-style wallet address
- Run deterministic demo blockchain tracing for 3–5 hops
- Build wallet/entity graph data
- Detect a known exchange endpoint
- Explain rule-based risk score
- Show an investigation dashboard
- Start monitoring and receive demo alerts
- Export a PDF investigation report

## Important prototype note
The app starts in **demo blockchain mode** so it works without paid APIs or API keys. The blockchain provider is isolated in `backend/app/blockchain.py`; replace `DemoBlockchainProvider` with a live EVM indexer/RPC/explorer provider for production data.

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Demo wallet
Use any valid EVM-style address, for example:
`0x1111111111111111111111111111111111111111`

The demo provider derives a trace from the wallet you enter, so the UI still demonstrates the complete flow.

## Run both with Docker Compose
```bash
docker compose up --build
```
This starts the backend on port 8000 and the frontend on port 3000, wired together automatically.
