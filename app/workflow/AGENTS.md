# WORKFLOW MODULE

NOF1 量化交易工作流编排模块

## STRUCTURE

```
app/workflow/
├── nof1_workflow.py    # 工作流定义和入口
└── steps/              # 工作流步骤
    ├── fetch_market_data.py
    ├── fetch_account_data.py
    ├── build_prompts.py
    ├── risk_check.py
    ├── execute_trades.py
    ├── notification.py
    └── utils.py
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Create workflow | `nof1_workflow.py` | `create_nof1_workflow()` factory |
| Run workflow | `nof1_workflow.py` | `run_nof1_workflow()` async entry |
| Step definitions | `steps/*.py` | Individual step implementations |
| Agent integration | `nof1_workflow.py` | `agent_decision_step` uses trader_agent() |

## CONVENTIONS

- Agno Workflow framework (7-step pipeline)
- Steps use `Step()` from `agno.workflow.step`
- Workflow state persisted to DB (PostgreSQL/SQLite)
- Timeout: 120s per step, max 2 retries
- Backtest: pass `end_date` to simulate historical data

## WORKFLOW STEPS

1. Fetch Market Data - Technical indicators
2. Fetch Account Data - Account/position state
3. Build Prompts - Assemble LLM context
4. Agent Decision - trader_agent() generates signals
5. Risk Check - Validate trading rules
6. Execute Trades - Update virtual orders/positions
7. Notification - Log and notify

## NOTES

- Workflow can be paused/resumed via session_id
- Debug mode: `debug_mode=True` for verbose logs
- DB: `AsyncPostgresDb` or `AsyncSqliteDb` based on `DATABASE_TYPE`
- Input: `NOF1WorkflowInput(symbols, account_number, end_date)`
