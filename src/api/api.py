from fastapi import APIRouter

from src.api.routes import accounts, auth, posts, symbols, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(posts.router)
api_router.include_router(symbols.router)
api_router.include_router(accounts.router)
