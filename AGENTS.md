# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-19
**Commit:** HEAD
**Branch:** main

## OVERVIEW

Agent Quant is a trading agent system integrating LLMs to generate trading signals from market data analysis. Fetches stock market data, builds prompts for AI agents, executes virtual trades, and analyzes performance.

**Key Languages**: Python >=3.14
**Package Manager**: uv
**Framework**: FastAPI with Agno integration

## STRUCTURE

```
./
├── app/              # FastAPI application
│   ├── agent/        # LLM agent definitions
│   ├── api/          # HTTP API endpoints
│   ├── backtest/     # Backtesting engine
│   ├── core/         # Configuration, DB, deps
│   ├── data_feed/    # Market data processing
│   ├── data_source/  # Market data adapters (Longport)
│   ├── models/       # SQLModel entities
│   ├── prompt_build/ # Prompt assembly for LLMs
│   ├── scheduler/    # APScheduler tasks
│   ├── utils/        # Cross-cutting utilities
│   ├── virtual_trade/# Virtual trading logic
│   └── workflow/     # Workflow orchestration (NOF1)
├── tests/            # pytest tests
└── serve.py          # Development server entry
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| API routes | `app/api/routes/` | Feature-based organization |
| DB models | `app/models/` | Three-layer pattern: Base, Entity, Create/Update/Read |
| Agents | `app/agent/` | Agno-based definitions |
| Workflow | `app/workflow/` | NOF1 trading workflow with steps |
| Virtual trade | `app/virtual_trade/` | Account, order, position logic |
| Backtest | `app/backtest/` | QuantStats integration |
| Configuration | `app/core/config.py` | Settings from .env |
| Dependencies | `app/core/deps.py` | DB session, auth deps |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `create_nof1_workflow` | function | `app/workflow/nof1_workflow.py` | Main workflow factory |
| `trader_agent` | function | `app/agent/trader_agent.py` | LLM trading agent |
| `run_backtest` | function | `app/backtest/run_backtest.py` | Backtest entry point |
| `SessionDep` | type alias | `app/core/deps.py` | DB session injection |
| `CurrentUserDep` | type alias | `app/core/deps.py` | Auth user injection |
| `BaseModel` | class | `app/models/base_model.py` | Base for all models (UUID v7 PK) |

## CONVENTIONS

**Deviation from standard:**

- **Type Hints**: Use modern `T | None` syntax (no `Optional[T]`)
- **Imports**: `from __future__ import annotations` NOT required (Python 3.14+ PEP 649)
- **Language**: All documentation in Chinese
- **Line Length**: 100 characters (Ruff config)
- **Model Pattern**: Three-layer inheritance required (Base, Entity, CRUD models)
- **Primary Keys**: UUID v7 mandatory (via `app/models/base_model.py`)
- **API Response**: Must use envelope pattern from `app/utils/responses.py`
- **Exception Handling**: Use custom exceptions from `app/utils/exceptions.py`

## ANTI-PATTERNS (THIS PROJECT)

None explicitly defined. Standard Python/FastAPI best practices apply.

## UNIQUE STYLES

- **Modular Prompts**: Prompt assembly broken into fragments in `app/prompt_build/` (technical, account, formatters)
- **Workflow Steps**: NOF1 workflow uses discrete steps in `app/workflow/steps/` (fetch, build, execute, notify)
- **Virtual Trade Logic**: Account/order/position tracked separately in `app/virtual_trade/`
- **Scheduler Integration**: APScheduler tasks defined in `app/scheduler/jobs.py`, started in `app/main.py` lifespan

## COMMANDS

```bash
# Install dependencies
uv sync

# Run development server
uv run serve.py

# Lint and auto-fix
uv run ruff check --fix

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/api/routes/test_auth.py::test_login_success

# Exclude integration tests
uv run pytest -m "not integration"

# Apply DB migrations
uv run alembic upgrade head
```

## NOTES

- **Database Schema**: Uses PostgreSQL or SQLite via `DATABASE_TYPE` config
- **Market Data**: Longport API integration via `app/data_source/longport_source.py`
- **Technical Indicators**: TA-Lib calculations via `app/utils/talib_calculator.py`
- **Test DB**: SQLite in-memory per test session (see `tests/conftest.py`)
- **Authentication**: FastAPI-Users with JWT, custom UserManager in `app/core/deps.py`
- **Alembic Configured**: Exclude `alembic/` from Ruff (see pyproject.toml)
- **Async Scheduler**: APScheduler `AsyncIOScheduler` started in FastAPI lifespan
