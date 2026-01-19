# API ROUTES MODULE

HTTP API 端点按功能域组织

## STRUCTURE

```
app/api/routes/
├── auth.py              # Authentication (FastAPI-Users)
├── user.py              # User profile
├── post.py              # Post CRUD
├── prompt.py            # Prompt management
└── watchlist.py         # Stock watchlist
```

## WHERE TO LOOK

| Feature | File | Routes |
|---------|------|--------|
| Auth | `auth.py` | Login, register, JWT endpoints |
| User | `user.py` | Profile, user info |
| Posts | `post.py` | CRUD operations |
| Prompts | `prompt.py` | Build/retrieve prompts |
| Watchlist | `watchlist.py` | Manage stock symbols |

## CONVENTIONS

**Dependencies** (MUST use):
```python
from app.core.deps import SessionDep, CurrentUserDep

async def my_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
):
    ...
```

**Responses** (MUST use envelope pattern):
```python
from app.utils.responses import success_response, error_response

return success_response(data=my_data)
# or
raise MyBusinessException("message")  # Auto-converts to error_response
```

**Exceptions** (MUST inherit from base):
```python
from app.utils.exceptions import (
    AppException,
    NotFoundException,
    BadRequestException,
)
```

**New Routes**:
1. Create file in `app/api/routes/`
2. Register in `app/api/__init__.py`
3. Use proper FastAPI router prefix/tags
4. Add tests in `tests/api/routes/`

## NOTES

- All routes require auth (except auth endpoints)
- FastAPI-Users handles auth (JWT, user management)
- Custom UserManager in `app/core/deps.py`
- Test fixtures: `tests/conftest.py`, `tests/utils/auth.py`
