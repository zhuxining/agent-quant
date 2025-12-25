from collections.abc import Sequence
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUserDep
from app.data_feed.technical_indicator import TechnicalIndicatorFeed, TechnicalSnapshot
from app.prompt_build.technical_prompt import TechnicalPromptTemplate, build_technical_prompt
from app.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/prompt", tags=["prompt"])

_CACHE_TTL_SECONDS = 60
_snapshot_cache: dict[str, tuple[float, list[TechnicalSnapshot]]] = {}


def _cache_key(symbols: Sequence[str]) -> str:
    return ",".join(sorted(symbols))


def _get_cached_snapshots(symbols: Sequence[str]) -> list[TechnicalSnapshot] | None:
    now = monotonic()
    key = _cache_key(symbols)
    cached = _snapshot_cache.get(key)
    if not cached:
        return None
    ts, value = cached
    if now - ts > _CACHE_TTL_SECONDS:
        _snapshot_cache.pop(key, None)
        return None
    return value


def _set_cached_snapshots(symbols: Sequence[str], snapshots: list[TechnicalSnapshot]) -> None:
    key = _cache_key(symbols)
    _snapshot_cache[key] = (monotonic(), snapshots)


async def _get_snapshots(symbols: Sequence[str], use_cache: bool) -> list[TechnicalSnapshot]:
    if use_cache:
        cached = _get_cached_snapshots(symbols)
        if cached is not None:
            return cached

    feed = TechnicalIndicatorFeed()
    snapshots = feed.build_snapshots(symbols)
    if use_cache:
        _set_cached_snapshots(symbols, snapshots)
    return snapshots


@router.get("/technical", response_model=ResponseEnvelope[dict])
async def get_technical_prompt(
    current_user: CurrentUserDep,
    symbols: Annotated[str, Query(description="逗号分隔的股票代码, 例如: 00700.HK,09988.HK")],
    template: Annotated[
        TechnicalPromptTemplate, Query(description="技术面模版")
    ] = TechnicalPromptTemplate.SIMPLE,
    use_cache: Annotated[bool, Query(description="是否使用 60 秒缓存")] = True,
):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="symbols 不能为空")

    prompt = build_technical_prompt(symbol_list, template=template)

    return success_response(
        data={
            "prompt": prompt,
            "template": template.value,
            "symbols": symbol_list,
            "cached": use_cache,
        },
        message="生成成功",
    )
