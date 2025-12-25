from contextlib import asynccontextmanager

from agno.agent import Agent
from agno.os import AgentOS
from agno.workflow import Workflow
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
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

    if settings.SCHEDULER_ENABLED:
        try:
            start_scheduler()
            yield
        finally:
            stop_scheduler()
            logger.info("FastAPI app shutdown")
    else:
        yield


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


# ———————————— 初始化 FastAPI 实例 ———————————— #
base_app: FastAPI = FastAPI(
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

# ———————————— 加载 AgentOS(可选) ———————————— #
if settings.AGENT_OS_ENABLED:
    example_agent_instance: Agent = example_agent("kimi")
    trader_agent_instance: Agent = trader_agent()
    nof1_workflow_instance: Workflow = create_nof1_workflow()

    agent_os = AgentOS(
        name="Quant Agent OS",
        agents=[example_agent_instance, trader_agent_instance],
        workflows=[nof1_workflow_instance],
        base_app=base_app,
    )

    app: FastAPI = agent_os.get_app()
    logger.info("AgentOS 已启用,包装 FastAPI 应用")
else:
    app = base_app
    logger.info("AgentOS 已禁用,直接使用 FastAPI 应用")

# ———————————— 注册路由、中间件与异常处理 ———————————— #
# 1. 异常处理
register_exception_handlers(app)

# 2. 中间件 (注意顺序: 从内到外添加, 越晚添加的越先执行)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)  # ty:ignore[invalid-argument-type]
app.add_middleware(RequestLoggingMiddleware)  # ty:ignore[invalid-argument-type]

# 3. 路由
app.include_router(api_router, prefix=settings.API_V1_STR)
