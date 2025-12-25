from enum import StrEnum
from textwrap import dedent

from app.data_feed.technical_indicator import TechnicalIndicatorFeed, TechnicalSnapshot
from app.data_source.longport_source import LongportSource
from app.prompt_build.formatters import fmt_list, fmt_number


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

    SIMPLE = "simple"
    DETAILED = "detailed"


def _build_simple_prompt(symbol: str, source: LongportSource) -> str:
    """生成 SIMPLE 模板的 prompt."""
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
        - 1日涨幅: {fmt_number(snapshot.change_pct_1, suffix="%")}
        - 5日涨幅: {fmt_number(snapshot.change_pct_5, suffix="%")}

        **趋势(EMA)**
        - EMA5: {fmt_number(_last(snapshot.ema5_series))}
        - EMA10: {fmt_number(_last(snapshot.ema10_series))}
        - EMA20: {fmt_number(_last(snapshot.ema20_series))}
        - EMA60: {fmt_number(_last(snapshot.ema60_series))}

        **动量指标**
        - ADX14: {fmt_number(_last(snapshot.adx14_series))}
        - RSI7: {fmt_number(snapshot.rsi7_latest)} | RSI14: {fmt_number(snapshot.rsi14_latest)}
        - MACD: {fmt_number(_last(snapshot.macd_series))} | Signal: {fmt_number(_last(snapshot.macd_signal_series))}

        **波动与支撑**
        - ATR3: {fmt_number(snapshot.atr3_latest)} | ATR14: {fmt_number(snapshot.atr14_latest)}
        - BBANDS(5) 上/中/下: {fmt_number(snapshot.bbands_upper_latest)} / {fmt_number(snapshot.bbands_middle_latest)} / {fmt_number(snapshot.bbands_lower_latest)}

        **成交量**
        - 最新成交量: {fmt_number(snapshot.volume_latest)}
        - 5日均量: {fmt_number(snapshot.volume_sma_5)}
        - 20日均量: {fmt_number(snapshot.volume_sma_20)}
        """
    ).strip()


def _build_detailed_prompt(symbol: str, source: LongportSource) -> str:
    """生成 DETAILED 模板的 prompt."""
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
    template: TechnicalPromptTemplate = TechnicalPromptTemplate.SIMPLE,
    source: LongportSource | None = None,
) -> str:
    """根据模板和标的列表构建技术面 Prompt.

    Args:
        symbols: 标的列表
        template: Prompt 模板类型
        source: 数据源, 如果为 None 则创建默认实例

    Returns:
        完整的技术面 Prompt 字符串
    """

    if source is None:
        source = LongportSource()

    if not symbols:
        return "## 市场数据分析\n\n(暂无标的)"

    builders = {
        TechnicalPromptTemplate.SIMPLE: _build_simple_prompt,
        TechnicalPromptTemplate.DETAILED: _build_detailed_prompt,
    }

    builder = builders.get(template)
    if builder is None:
        raise ValueError(f"Unknown template: {template}")

    prompts = []
    for symbol in symbols:
        try:
            prompt = builder(symbol, source)
            prompts.append(prompt)
        except Exception as e:
            error_msg = f"### {symbol}\n\n(数据获取失败: {e!s})"
            prompts.append(error_msg)

    return "\n\n---\n\n".join(prompts)


__all__ = ["TechnicalPromptTemplate", "build_technical_prompt"]
