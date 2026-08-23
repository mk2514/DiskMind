# 🧠 DiskMind — Predictive AI Storage Copilot for Linux

> **From reactive disk cleanup to predictive storage intelligence.**

DiskMind is an AI-powered storage management system that learns how your storage is being used, detects duplicates and inactive data, predicts future storage pressure, identifies abnormal growth (anomaly detection), and recommends safe, explainable cleanup actions — all with **human approval required**.

---

## 🚀 Quick Start

### Frontend (Demo Mode — No Backend Required)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the UI runs with rich mock data by default.

### Backend (Full AI Mode)

```bash
# 1. Create a Python virtual environment
python3 -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (msys64 venv):
# .venv/bin/activate  or  .venv/Scripts/activate.bat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Generate demo data
python demo/generate_test_data.py

# 5. Start the backend
uvicorn backend.main:app --reload --port 8000
```

### Switch frontend to live backend

In `frontend/vite.config.ts`, change the `VITE_USE_MOCK` default from `'true'` to `'false'` — or set the env var:

```bash
VITE_USE_MOCK=false npm run dev
```

---

## 🏗️ Architecture

```
LINUX SYSTEM
     │
     ▼
Filesystem Collector (2-phase SHA-256 hashing, protected-path rules)
     │
     ▼
Storage Intelligence
  ├─ Inactivity Scoring (weighted multi-factor)
  ├─ Duplicate Detection (size pre-grouping → SHA-256)
  ├─ Risk Engine (PROTECTED / LOW / MEDIUM / HIGH)
  └─ File Classification (media, cache, log, build_artifact, ...)
     │
     ▼
ML Engine
  ├─ Forecast (Linear Regression → Random Forest on 30+ day history)
  └─ Anomaly Detection (Isolation Forest)
     │
     ▼
AI Layer
  ├─ Recommendation Engine (risk-aware, explainable)
  ├─ LLM Assistant (tool-calling GPT, metadata only — no file content)
  └─ What-If Simulator (before/after impact projection)
     │
     ▼
Human Approval Gate  ←  AI never deletes files directly
     │
     ▼
Safe Actions (move to Trash, archive, undo)
```

---

## 🖥️ Dashboard Screens

| Screen | Route | Description |
|--------|-------|-------------|
| Overview | `/` | Storage health score, SVG ring gauge, anomaly alerts, stat cards |
| Explorer | `/explorer` | Top directories + file-type breakdown with animated bars |
| Recommendations | `/recs` | Risk-badged AI recommendations with expandable explanations |
| Forecast | `/forecast` | Recharts area chart, countdown cards, anomaly list |
| AI Copilot | `/chat` | Tool-calling LLM chat with markdown rendering |
| Simulator | `/simulator` | What-If analysis: before/after utilization + timeline impact |

---

## 🔑 Key Design Decisions

| Principle | Implementation |
|-----------|---------------|
| **Safety first** | AI recommends; human approves. No auto-delete. |
| **Privacy** | No file content sent to LLM. Only metadata (path, size, type, dates). |
| **Explainability** | Every recommendation includes a plain-English explanation and confidence score. |
| **Local-first** | SQLite database. No cloud dependency (LLM is opt-in). |
| **Risk-aware** | PROTECTED → LOW → MEDIUM → HIGH tiering. SSH/GPG are absolute blockers. |

---

## 📁 Project Structure

```
diskmind/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── database/
│   │   ├── schema.sql             # SQLite schema
│   │   └── database.py            # Async DB handler
│   ├── collector/
│   │   ├── filesystem.py          # 2-phase hashing collector
│   │   └── system.py              # psutil disk snapshots
│   ├── intelligence/
│   │   ├── inactivity.py          # Weighted inactivity scoring
│   │   ├── risk.py                # Multi-factor risk engine
│   │   ├── duplicates.py          # Duplicate detection
│   │   └── classification.py     # File type classification
│   ├── ml/
│   │   ├── forecast.py            # Linear Regression + Random Forest
│   │   └── anomaly.py             # Isolation Forest
│   ├── ai/
│   │   ├── recommendations.py     # Recommendation engine
│   │   ├── assistant.py           # Tool-calling LLM orchestration
│   │   ├── tools.py               # Structured tool registry
│   │   └── prompts.py             # System prompts
│   ├── actions/
│   │   ├── simulator.py           # What-If analysis
│   │   └── trash.py               # Safe file operations
│   └── api/
│       ├── routes_storage.py      # Storage overview, scan, tree
│       ├── routes_ai.py           # Chat, recommendations, simulate
│       ├── routes_forecast.py     # Forecast + anomalies
│       └── routes_cleanup.py      # Approve, execute, undo
├── frontend/
│   └── src/
│       ├── api/client.ts          # Typed API client + mock data
│       ├── components/            # Sidebar, StorageRing, RiskBadge, etc.
│       ├── pages/                 # 6 dashboard screens
│       └── types/index.ts         # TypeScript type definitions
├── demo/
│   └── generate_test_data.py      # Synthetic dataset generator
└── .env.example                   # Environment config template
```

---

## ⚙️ Environment Variables

```env
OPENAI_API_KEY=sk-...          # Required for live AI (optional in demo mode)
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
DEMO_MODE=true                 # Skip real filesystem scan
SCAN_PATH=/home                # Root directory to scan
DB_PATH=./diskmind.db
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:5173
```
