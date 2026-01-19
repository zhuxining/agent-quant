# MODELS MODULE

SQLModel 数据库实体定义 (三层继承模式)

## STRUCTURE

```
app/models/
├── base_model.py        # Base class (UUID v7 PK)
├── user.py              # User entity
├── post.py              # Post entity
├── log.py               # Workflow execution logs
├── virtual_trade_*.py   # Virtual trading entities
│   ├── account.py
│   ├── order.py
│   ├── position.py
│   └── stock.py
└── backtest_*.py        # Backtest entities
    ├── run.py
    └── daily_equity.py
```

## WHERE TO LOOK

| Domain | Files | Notes |
|--------|-------|-------|
| Base | `base_model.py` | UUID v7, timestamps, soft delete |
| Auth | `user.py` | FastAPI-Users User model |
| Trading | `virtual_trade_*.py` | Account/order/position/stock |
| Backtest | `backtest_*.py` | Run metadata, daily equity |
| Logs | `log.py` | Workflow execution logs |

## CONVENTIONS

**Three-Layer Pattern** (MUST follow):
```
*Base        - Common fields (id, created_at, updated_at, is_deleted)
*Entity      - SQLModel(table=True) - DB table definition
*Create      - Pydantic model for input validation
*Update      - Pydantic model for updates
*Read        - Pydantic model for output
```

**Inheritance Rules**:
- ALL entities MUST inherit from `BaseModel` (app/models/base_model.py)
- Base class provides: UUID v7 PK, timestamptz timestamps, soft delete
- Table names: singular form of entity name
- Schema: `postgres` or `sqlite` based on `DATABASE_TYPE`

**Migrations**:
- Alembic configured (alembic/)
- New model → `uv run alembic revision --autogenerate -m "description"`
- Apply: `uv run alembic upgrade head`
