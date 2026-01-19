# VIRTUAL TRADE MODULE

虚拟交易业务逻辑 (账户、订单、持仓)

## STRUCTURE

```
app/virtual_trade/
├── account.py           # 账户管理
├── order.py             # 订单执行
└── position.py          # 持仓跟踪
```

## WHERE TO LOOK

| Domain | File | Notes |
|--------|------|-------|
| Account | `account.py` | Balance, metadata, account state |
| Orders | `order.py` | Buy/sell execution, status tracking |
| Positions | `position.py` | Current holdings, P&L |

## CONVENTIONS

**Order Lifecycle**:
1. Create: `Order(symbol, quantity, side, price, ...)`
2. Execute: Update status → EXECUTED
3. Update Position: Adjust holdings based on fill
4. Log: Record transaction details

**Position Tracking**:
- Real-time P&L calculation
- Average cost basis
- Position size (quantity)
- Reference current market price

**Account State**:
- Cash balance
- Total equity (cash + positions)
- Available margin
- Trading limits (if configured)

## NOTES

- Used by workflow `execute_trades_step` to update trading state
- Separate from real trading - sandbox for testing strategies
- Database models: `VirtualTradeAccount`, `VirtualTradeOrder`, `VirtualTradePosition`, `VirtualTradeStock`
- No real money involved - purely for strategy validation
