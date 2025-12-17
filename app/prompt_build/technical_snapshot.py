from __future__ import annotations

from textwrap import dedent

from app.data_feed.technical_indicator import TechnicalSnapshot
from app.prompt_build.formatters import fmt_list, fmt_number


def _build_single_snapshot_block(snapshot: TechnicalSnapshot) -> str:
    return dedent(
        f"""
        ### ALL {snapshot.symbol} DATA

        **Current Snapshot:**

        - current_price = {fmt_number(snapshot.current_price)}
        - current_ema20 = {fmt_number(snapshot.current_ema20)}
        - current_macd = {fmt_number(snapshot.current_macd)}
        - current_rsi (7 period) = {fmt_number(snapshot.current_rsi7)}

        **Short-term Context (1-h intervals, oldest → latest):**

        Mid prices: [{fmt_list(snapshot.short_term_mid_prices)}]
        EMA indicators (20-period): [{fmt_list(snapshot.short_term_ema20)}]
        MACD indicators: [{fmt_list(snapshot.short_term_macd)}]
        RSI indicators (7-Period): [{fmt_list(snapshot.short_term_rsi7)}]
        RSI indicators (14-Period): [{fmt_list(snapshot.short_term_rsi14)}]

        **Longer-term Context (1-d intervals, oldest → latest):**

        20-Period EMA: {fmt_number(snapshot.long_term_ema20)} vs. 50-Period EMA: {fmt_number(snapshot.long_term_ema50)}
        3-Period ATR: {fmt_number(snapshot.long_term_atr3)} vs. 14-Period ATR: {fmt_number(snapshot.long_term_atr14)}
        Current Volume: {fmt_number(snapshot.long_term_volume_current)} vs. Average Volume: {fmt_number(snapshot.long_term_volume_avg)}
        MACD indicators (4h): [{fmt_list(snapshot.long_term_macd)}]
        RSI indicators (14-Period): [{fmt_list(snapshot.long_term_rsi14)}]
        """
    ).strip()


def build_technical_snapshots(snapshots: list[TechnicalSnapshot]) -> str:
    """根据行情摘要列表构建整齐的多标的技术面提示片段。"""

    if not snapshots:
        return "## 当前所有标的的市场数据\n\n(暂无可用数据)"

    blocks = [_build_single_snapshot_block(snapshot) for snapshot in snapshots]
    joined = "\n\n---\n\n".join(blocks)
    return dedent(
        f"""
        ## 当前所有标的的市场数据

        {joined}
        """
    ).strip()


__all__ = ["build_technical_snapshots"]
