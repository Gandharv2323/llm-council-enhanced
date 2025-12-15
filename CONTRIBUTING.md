# Contributing to LLM Council

Thank you for your interest in contributing to LLM Council! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
# Install dependencies
pip install -e .

# Or with uv
uv sync

# Run backend
python -m backend.main
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
llm-council/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── config.py        # Configuration
│   ├── council.py       # Core deliberation logic
│   ├── evaluation.py    # Pairwise preference aggregation
│   ├── calibration.py   # Confidence calibration tracking
│   ├── claims.py        # Claim extraction/verification
│   ├── benchmark.py     # Benchmark runner
│   ├── database.py      # SQLite storage
│   ├── resilience.py    # Fault tolerance
│   └── schemas.py       # Pydantic models
├── frontend/
│   └── src/
│       ├── components/  # React components
│       └── hooks/       # Custom React hooks
└── benchmarks/          # Benchmark datasets and results
```

## Contribution Guidelines

### Code Style

**Python:**
- Use type hints
- Follow PEP 8
- Use `ruff` for linting
- Prefer `async/await` for I/O operations

**JavaScript/React:**
- Use functional components with hooks
- Follow ESLint rules
- Use CSS modules or scoped CSS

### Commit Messages
```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Examples:
  feat(evaluation): add Bradley-Terry scoring
  fix(council): handle timeout in stage2
  docs(readme): update installation steps
```

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run tests: `pytest tests/`
5. Run linting: `ruff check backend/`
6. Submit PR against `main`

## Good First Issues

- [ ] Add dark mode toggle
- [ ] Implement response copy button
- [ ] Add model search/filter in config UI
- [ ] Create loading skeletons for stages
- [ ] Add keyboard shortcuts

## Research Contributions

We welcome research-oriented contributions:

- **Weighted voting**: Implement domain-specific expertise weighting
- **Calibration dashboard**: Visualize model calibration over time
- **Benchmark expansion**: Add new evaluation datasets
- **Sensitivity analysis**: Tools for testing query robustness

## Questions?

Open an issue for questions or discussions about the codebase.
