# LLM Council 🏛️

> **Not an oracle. A deliberation.**

![llmcouncil](header.jpg)

LLM Council is a **deliberative AI engine** that makes model disagreement, confidence, and reasoning visible and measurable. Instead of getting one answer from one model, you get:

- ✅ **Multiple models debate** your question
- ✅ **Anonymized peer review** prevents bias
- ✅ **Disagreement is surfaced**, not hidden
- ✅ **Confidence is calibrated**, not claimed
- ✅ **Full audit trail** of deliberation

## How It Works

```
User Query
    ↓
Stage 1: All models answer independently → [4 responses]
    ↓
Stage 2: Models review each other (anonymized) → [rankings + evaluations]
    ↓
Aggregate Rankings (Bradley-Terry scoring)
    ↓
Stage 3: Chairman synthesizes final answer
    ↓
Output: { responses, evaluations, disagreements, final_answer }
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenRouter API key ([get one here](https://openrouter.ai/))

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/llm-council.git
cd llm-council

# Backend
pip install -e .

# Frontend
cd frontend && npm install && cd ..

# Configure API key
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
```

### Run

```bash
# Terminal 1 - Backend
python -m backend.main

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Open http://localhost:5173

## Features

### Core Deliberation
- **Stage 1**: Parallel queries to all council models
- **Stage 2**: Anonymized peer evaluation with structured output
- **Stage 3**: Chairman synthesis with full context

### Algorithmic Improvements
- **Bradley-Terry scoring**: Pairwise preference aggregation
- **Domain expertise weighting**: Math, code, creative, factual
- **Kendall's W**: Inter-rater agreement measurement
- **Claim extraction**: Identify points of agreement/disagreement

### Research-Grade Features
- **Benchmark runner**: Test on MMLU, TruthfulQA, HumanEval
- **Ablation framework**: Compare configurations systematically
- **Calibration tracking**: Measure stated vs actual confidence

### Engineering
- **SQLite storage**: Proper database, not JSON files
- **Circuit breaker**: Fault tolerance for model failures
- **Query caching**: Avoid redundant API calls
- **Docker deployment**: One-command containerized setup

## Configuration

Edit `backend/config.py`:

```python
COUNCIL_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "deepseek/deepseek-r1:free",
]

CHAIRMAN_MODEL = "google/gemini-2.0-flash-exp:free"
```

## Deployment (100% FREE) 🚀

### Deploy on Render.com (Recommended)

1. **Push to GitHub**
2. **Sign up for Render** (no credit card needed)
3. **New +** → **Blueprint**
4. Connect your repo
5. Add your `OPENROUTER_API_KEY` when asked
6. **Done!** You have a free, live URL.

*Note: The free tier spins down after inactivity (30s cold start).*

### Files Created for Deployment
| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (Frontend + Backend in one) |
| `render.yaml` | Render configuration |
| `docker-compose.yml` | Local testing |

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List conversations |
| POST | `/api/conversations` | Create conversation |
| POST | `/api/conversations/{id}/message` | Send query to council |
| GET | `/api/models` | List available models |
| POST | `/api/estimate` | Get cost estimate |

## Project Structure

```
llm-council/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── council.py       # Core deliberation
│   ├── evaluation.py    # Bradley-Terry scoring
│   ├── calibration.py   # Confidence tracking
│   ├── claims.py        # Claim extraction
│   ├── benchmark.py     # Benchmark runner
│   ├── database.py      # SQLite layer
│   └── resilience.py    # Fault tolerance
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── EpistemicPanel.jsx
│       │   ├── CostEstimator.jsx
│       │   └── DisagreementExplorer.jsx
│       └── hooks/
│           └── useStreaming.js
└── benchmarks/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Good First Issues
- Add dark mode
- Implement response copy button
- Create loading skeletons
- Add keyboard shortcuts

## Tech Stack

- **Backend**: FastAPI, Python 3.10+, async httpx
- **Frontend**: React 19, Vite
- **Storage**: SQLite
- **API**: OpenRouter (unified LLM access)

## License

MIT

---

**Why LLM Council?**

Single models hallucinate. Ensembles catch errors.  
Consensus reveals confidence. Disagreement reveals uncertainty.  
Transparency > black boxes.
