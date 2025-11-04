# 关于项目

获取股票市场数据，构建 Prompt 给 Agent，得到交易信号，模拟交易并记录分析结果。

## 技术栈

- [FastAPI](https://fastapi.tiangolo.com/)：
- [Pydantic](https://pydantic-docs.helpmanual.io/)：
- [SQLModel](https://sqlmodel.tiangolo.com/)：
- [Loguru](https://loguru.readthedocs.io/)：
- [FastAPI Users](https://fastapi-users.github.io/fastapi-users/)：
- [Pydantic AI](https://github.com/pydantic/pydantic-ai/):
- [Quantstats](https://github.com/ranaroussi/quantstats/):
- [Longport](https://open.longportapp.com/):

## 入门指南

**依赖安装：**

```sh
uv sync
```

**启动项目：**

```sh
uv run serve.py
```

**Lint and Formatter：**

```sh
uv run ruff check --fix
```

## 路线图

- Quant
  - 标的列表：制定要获取数据的股票标的列表
  - 行情获取：通过longport获取市场数据，通过ta-lib计算指标
  - 交易账户：初始化账户信息，每次交易更新最新持仓
  - 指令聚合：将股票数据、账户数据组装成 prompt
  - 模型调用：将 prompt 提供给多个 Agent 交易员
  - 交易执行：根据交易信号，执行交易动作并更新账户
  - 运行日志：记录 Agent 的输入输出信息
  - 交易回测：借助 quantstats 组合投资情况
  - 自动运行：根据定时任务自动运行，并将交易信号通知出去

- Front-end
  - 管理标的列表
  - 查看交易信号
  - 分析账户情况

## 架构设计

### 目录总览

- `src/main.py`：FastAPI 应用入口，与路由、依赖注入解耦。
- `src/core/`：配置、数据库等基础设施，`config.py` 暴露 `Settings`，供其余模块读取环境变量（如 Longport 凭证）。
- `src/quant/`：量化域层，按功能拆分为：
  - `core/`：通用数据结构（`MarketBar`、`IndicatorSnapshot` 等）与协议定义，约束服务接口。
  - `data_pipeline/`：行情拉取与指标计算，包含 `longport_source.py`、`market_feed.py`、`talib_calculator.py`、`snapshots.py` 等。
  - `accounts/`、`prompting/`、`execution/`、`backtest/`、`scheduler/`：分别负责账户管理、Prompt 构建、信号执行、回测、任务调度。
- `tests/`：Pytest 测试，含集成测试 `test_market_data_integration.py`，覆盖行情、指标与快照。

### 行情与指标流程

1. `LongportMarketDataSource`（`data_pipeline/longport_source.py`）使用 `Config.from_env()` 和 `QuoteContext` 连接 Longport，统一将返回值封装为 `MarketBar`。
2. `MarketDataService`（`data_pipeline/market_feed.py`）依赖数据源，提供 `fetch_window` 和 `fetch_period`，并可与其他数据源实现互换。
3. `TalibIndicatorCalculator`（`data_pipeline/talib_calculator.py`）基于 pandas/TA-Lib 计算 EMA、MACD、RSI、ATR 等指标，所有数值保留四位小数。
4. `IndicatorService` 向外暴露统一接口，`SnapshotAssembler`（`data_pipeline/snapshots.py`）将长短周期指标结构化为 Prompt 快照。
5. `PromptSnapshotService` 调用上述服务完成行情拉取、指标计算和快照组装，是 Agent Prompt 的核心入口。

### 日志与测试

- 使用 Loguru 记录行情、指标、快照等关键节点，便于观察数据管线的输入输出。
- `pytest.ini` 注册 `integration` 标记，可通过 `uv run pytest -s -m integration` 定向执行外部依赖测试。
- `tests/test_market_data_integration.py` 会对多个标的（如 `AAPL.US`、`510300.SH`）进行拉取并打印 MarketData/Indicator/Snapshot，验证链路可用性。

上述分层让各模块职责清晰，便于后续扩展额外数据源、指标或执行逻辑，同时保持测试与监控的透明度。
