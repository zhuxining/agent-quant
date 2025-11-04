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
