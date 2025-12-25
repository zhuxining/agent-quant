from enum import StrEnum
import json
from textwrap import dedent

from app.data_feed.technical_indicator import TechnicalIndicatorFeed, TechnicalSnapshot
from app.data_source.longport_source import LongportSource
from app.prompt_build.formatters import fmt_list, fmt_number, fmt_pct, fmt_series_number


def _last(values: list[float] | None) -> float | None:
    """获取列表的最后一个元素."""
    return values[-1] if values else None


def _fetch_snapshots_for_symbol(
    symbol: str,
    periods: list[str],
    source: LongportSource,
) -> dict[str, TechnicalSnapshot | None]:
    """为单个标的获取指定周期的快照."""
    feed = TechnicalIndicatorFeed(source=source)
    snapshots_by_period = {}
    for period in periods:
        snapshots = feed.build_snapshots([symbol], period=period)
        snapshots_by_period[period] = snapshots[0] if snapshots else None
    return snapshots_by_period


class TechnicalPromptTemplate(StrEnum):
    """技术面 Prompt 模板枚举。"""

    SINGLE_PERIOD_TXT = "single_period_txt"
    SINGLE_PERIOD_JSON = "single_period_json"
    MULTI_PERIOD_TXT = "multi_period_txt"


def _build_single_period_txt_prompt(symbol: str, source: LongportSource) -> str:
    """生成 SINGLE_PERIOD_TXT 模板的 prompt."""
    periods = ["1d"]
    snapshots = _fetch_snapshots_for_symbol(symbol, periods, source)
    snapshot = snapshots.get("1d")

    if snapshot is None:
        return f"### {symbol}\n\n(暂无数据)"

    return dedent(
        f"""
        ### {symbol} ({snapshot.period})

        **价格与涨幅**
        - 最新价格: {fmt_number(snapshot.latest_price)}
        - 1日涨幅: {fmt_pct(snapshot.change_pct_1)}
        - 5日涨幅: {fmt_pct(snapshot.change_pct_5)}

        **趋势(EMA)**
        - EMA5: [{fmt_list(snapshot.ema5_series)}]
        - EMA10: [{fmt_list(snapshot.ema10_series)}]
        - EMA20: [{fmt_list(snapshot.ema20_series)}]
        - EMA60: [{fmt_list(snapshot.ema60_series)}]

        **动量指标**
        - ADX14: [{fmt_list(snapshot.adx14_series)}]
        - RSI7: {fmt_number(snapshot.rsi7_latest)} | RSI14: {fmt_number(snapshot.rsi14_latest)}
        - MACD: [{fmt_list(snapshot.macd_series)}] | Signal: [{fmt_list(snapshot.macd_signal_series)}] | Histogram: [{fmt_list(snapshot.macd_hist_series)}]

        **波动与支撑**
        - ATR3: {fmt_number(snapshot.atr3_latest)} | ATR14: {fmt_number(snapshot.atr14_latest)}
        - BBANDS(5) 上/中/下: {fmt_number(snapshot.bbands_upper_latest)} / {fmt_number(snapshot.bbands_middle_latest)} / {fmt_number(snapshot.bbands_lower_latest)}

        **成交量**
        - 最新成交量: {fmt_number(snapshot.volume_latest)}
        - 5日均量: {fmt_number(snapshot.volume_sma_5)}
        - 20日均量: {fmt_number(snapshot.volume_sma_20)}
        """
    ).strip()


def _build_single_period_json_prompt(symbol: str, source: LongportSource) -> dict:
    """生成 JSON_SINGLE_PERIOD 模板的 prompt (返回字典)."""
    periods = ["1d"]
    snapshots = _fetch_snapshots_for_symbol(symbol, periods, source)
    snapshot = snapshots.get("1d")

    if snapshot is None:
        return {"symbol": symbol, "error": "暂无数据"}

    return {
        "symbol": snapshot.symbol,
        "period": snapshot.period,
        "price": {
            "latest": fmt_number(snapshot.latest_price),
            "change_1d_pct": snapshot.change_pct_1,
            "change_5d_pct": snapshot.change_pct_5,
        },
        "trend": {
            "ema_5_series": fmt_series_number(snapshot.ema5_series),
            "ema_10_series": fmt_series_number(snapshot.ema10_series),
            "ema_20_series": fmt_series_number(snapshot.ema20_series),
            "ema_60_series": fmt_series_number(snapshot.ema60_series),
        },
        "momentum": {
            "adx_14_series": fmt_series_number(snapshot.adx14_series),
            "rsi_7_latest": snapshot.rsi7_latest,
            "rsi_14_latest": snapshot.rsi14_latest,
            "macd_series": fmt_series_number(snapshot.macd_series),
            "macd_signal_series": fmt_series_number(snapshot.macd_signal_series),
            "macd_hist_series": fmt_series_number(snapshot.macd_hist_series),
        },
        "volatility": {
            "atr_3_latest": snapshot.atr3_latest,
            "atr_14_latest": snapshot.atr14_latest,
            "bbands": {
                "upper_latest": snapshot.bbands_upper_latest,
                "middle_latest": snapshot.bbands_middle_latest,
                "lower_latest": snapshot.bbands_lower_latest,
            },
        },
        "volume": {
            "latest": snapshot.volume_latest,
            "sma_5": snapshot.volume_sma_5,
            "sma_20": snapshot.volume_sma_20,
        },
        "liquidity": {
            "ad_series": snapshot.ad_series,
        },
    }


def _build_multi_period_txt_prompt(symbol: str, source: LongportSource) -> str:
    """生成 MULTI_PERIOD_TXT 模板的 prompt."""
    periods = ["1h", "1d", "4h"]
    snapshots = _fetch_snapshots_for_symbol(symbol, periods, source)

    content_parts = [f"## {symbol}"]

    # 1h 周期格式
    snapshot_1h = snapshots.get("1h")
    if snapshot_1h is not None:
        period_content = dedent(
            f"""
            ### 1H

            **短期背景 (1-h intervals, oldest → latest):**

            EMA 指标 (5-period): [{fmt_list(snapshot_1h.ema5_series)}]
            EMA 指标 (20-period): [{fmt_list(snapshot_1h.ema20_series)}]
            MACD 指标: [{fmt_list(snapshot_1h.macd_series)}]
            RSI (7-Period): {fmt_number(snapshot_1h.rsi7_latest)}
            RSI (14-Period): {fmt_number(snapshot_1h.rsi14_latest)}
            """
        ).strip()
        content_parts.append(period_content)

    # 1d 周期格式
    snapshot_1d = snapshots.get("1d")
    if snapshot_1d is not None:
        period_content = dedent(
            f"""
            ### 1D

            **长期背景 (1-d intervals, oldest → latest):**

            20-Period EMA: {fmt_number(_last(snapshot_1d.ema20_series))} vs. 60-Period EMA: {fmt_number(_last(snapshot_1d.ema60_series))}
            3-Period ATR: {fmt_number(snapshot_1d.atr3_latest)} vs. 14-Period ATR: {fmt_number(snapshot_1d.atr14_latest)}
            Current Volume: {fmt_number(snapshot_1d.volume_latest)} vs. Average Volume: {fmt_number(snapshot_1d.volume_sma_20)}
            MACD 指标: [{fmt_list(snapshot_1d.macd_series)}]
            RSI (14-Period): {fmt_number(snapshot_1d.rsi14_latest)}
            """
        ).strip()
        content_parts.append(period_content)

    # 4h 周期格式
    snapshot_4h = snapshots.get("4h")
    if snapshot_4h is not None:
        period_content = dedent(
            f"""
            ### 4H

            **中期背景 (4-h intervals, oldest → latest):**

            EMA 趋势 (20-period): [{fmt_list(snapshot_4h.ema20_series)}]
            ADX 强度: [{fmt_list(snapshot_4h.adx14_series)}]
            MACD 动量: [{fmt_list(snapshot_4h.macd_series)}]
            """
        ).strip()
        content_parts.append(period_content)

    return "\n\n".join(content_parts)


def build_technical_prompt(
    symbols: list[str],
    template: TechnicalPromptTemplate = TechnicalPromptTemplate.SINGLE_PERIOD_JSON,
    source: LongportSource | None = None,
) -> str:
    """根据模板和标的列表构建技术面 Prompt.

    Args:
        symbols: 标的列表
        template: Prompt 模板类型
        source: 数据源, 如果为 None 则创建默认实例

    Returns:
        Complete technical prompt string (JSON template returns JSON string)
    """
    if source is None:
        source = LongportSource()

    if not symbols:
        if template == TechnicalPromptTemplate.SINGLE_PERIOD_JSON:
            return json.dumps({"symbols": [], "error": "暂无标的"}, ensure_ascii=False)
        return "## 市场数据分析\n\n(暂无标的)"

    text_builders = {
        TechnicalPromptTemplate.SINGLE_PERIOD_TXT: _build_single_period_txt_prompt,
        TechnicalPromptTemplate.MULTI_PERIOD_TXT: _build_multi_period_txt_prompt,
    }

    json_builders = {
        TechnicalPromptTemplate.SINGLE_PERIOD_JSON: _build_single_period_json_prompt,
    }

    # 处理 JSON 模板
    if template in json_builders:
        builder = json_builders[template]
        prompts = []
        for symbol in symbols:
            try:
                prompt_dict = builder(symbol, source)
                prompts.append(prompt_dict)
            except Exception as e:
                error_dict = {"symbol": symbol, "error": f"数据获取失败: {e!s}"}
                prompts.append(error_dict)
        return json.dumps(prompts, ensure_ascii=False)

    # 处理文本模板
    if template in text_builders:
        builder = text_builders[template]
        prompts = []
        for symbol in symbols:
            try:
                prompt = builder(symbol, source)
                prompts.append(prompt)
            except Exception as e:
                error_msg = f"### {symbol}\n\n(数据获取失败: {e!s})"
                prompts.append(error_msg)
        return "\n\n---\n\n".join(prompts)

    raise ValueError(f"Unknown template: {template}")


__all__ = ["TechnicalPromptTemplate", "build_technical_prompt"]
