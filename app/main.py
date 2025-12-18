from contextlib import asynccontextmanager

from agno.os import AgentOS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.routing import APIRoute
from loguru import logger

from app.agent import example_agent, trader_agent
from app.api import api_router
from app.core.config import settings
from app.core.db import create_db_and_tables
from app.core.init_data import create_trade_account, create_user
from app.scheduler import start_scheduler, stop_scheduler
from app.utils.exceptions import register_exception_handlers
from app.utils.logging import RequestLoggingMiddleware, setup_logging
from app.workflow.nof1_workflow import create_nof1_workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings)
    logger.info("FastAPI app startup")
    await create_db_and_tables()
    await create_user(settings.FIRST_SUPERUSER_EMAIL, settings.FIRST_SUPERUSER_PASSWORD)
    await create_trade_account()
    logger.success("Startup initialization complete")

    # 启动调度器
    start_scheduler()

    try:
        yield
    finally:
        stop_scheduler()
        logger.info("FastAPI app shutdown")


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


app: FastAPI = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.SWAGGER_UI_ENABLED else None,
    docs_url="/docs" if settings.SWAGGER_UI_ENABLED else None,
    redoc_url="/redoc" if settings.SWAGGER_UI_ENABLED else None,
    version=settings.VERSION,
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
    debug=(settings.ENVIRONMENT == "dev"),
)
register_exception_handlers(app)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.ENVIRONMENT == "prod":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

app.include_router(api_router, prefix=settings.API_V1_STR)

# ———————————— 加载Agent ———————————— #
example_agent = example_agent("kimi")
trader_agent = trader_agent()

# ———————————— 加载Workflow ———————————— #
nof1_workflow = create_nof1_workflow()

agent_os = AgentOS(
    name="Quant Agent OS",
    agents=[example_agent, trader_agent],
    workflows=[nof1_workflow],
    base_app=app,
)

app = agent_os.get_app()
