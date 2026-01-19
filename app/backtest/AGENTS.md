# BACKTEST MODULE

回测引擎,集成 QuantStats 性能分析

## STRUCTURE

```
app/backtest/
├── engine.py            # 核心回测逻辑
├── run_backtest.py     # 回测入口
├── report.py           # 报告生成 (HTML/JSON)
└── equity.py           # 权益曲线计算
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Run backtest | `run_backtest.py` | `run_backtest()` main entry |
| Core logic | `engine.py` | Reuses NOF1 workflow with end_date |
| Reports | `report.py` | QuantStats integration |
| Equity curves | `equity.py` | Daily P&L tracking |

## CONVENTIONS

**Backtest Strategy**:
- Reuse existing workflow (`app/workflow/nof1_workflow.py`)
- Pass `end_date` parameter to simulate historical data points
- Execute workflow sequentially across time periods
- Record each run's metrics to `backtest_run` and `backtest_daily_equity` tables

**QuantStats Usage**:
- Generate HTML reports with metrics (Sharpe, Max DD, etc.)
- Generate JSON for programmatic access
- Report output: `<run_id>/report.html` and `metrics.json`

## NOTES

- Entry point: `run_backtest()` in `run_backtest.py`
- Database: Uses configured DB (PostgreSQL/SQLite)
- Performance metrics stored in `BacktestDailyEquity` model
- Reports saved to filesystem (check config for output path)
- Compatible with NOF1 workflow - same agent, same logic, historical data
