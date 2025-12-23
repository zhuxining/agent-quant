from enum import StrEnum
from textwrap import dedent

from app.data_feed.technical_indicator import TechnicalSnapshot
from app.prompt_build.formatters import fmt_list, fmt_number


class TechnicalPromptTemplate(StrEnum):
    """技术面 Prompt 模板枚举。"""

    COMPREHENSIVE = "comprehensive"
    INTRADAY_HOURLY = "intraday_hourly"
    DAILY_POST_MARKET = "daily_post_market"
    QUICK_SNAPSHOT = "quick_snapshot"
    MOMENTUM = "momentum"
    DAILY_FULL_DEBUG = "daily_full_debug"


def _trend_summary(snapshot: TechnicalSnapshot) -> str:
    ema20 = fmt_number(snapshot.daily_ema20_latest)
    ema50 = fmt_number(snapshot.daily_ema50_latest)
    macd_now = fmt_number(snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None)
    rsi14_now = fmt_number(snapshot.daily_rsi14_latest)
    return f"趋势: EMA20 {ema20} vs EMA50 {ema50}; MACD={macd_now}; RSI14={rsi14_now}"


def _volume_summary(snapshot: TechnicalSnapshot) -> str:
    vol_now = fmt_number(snapshot.daily_volume_latest)
    vol_sma5 = fmt_number(snapshot.daily_volume_sma_5)
    vol_sma20 = fmt_number(snapshot.daily_volume_sma_20)
    return f"量能: 当前 {vol_now} | 5日均 {vol_sma5} / 20日均 {vol_sma20}"


def _build_comprehensive(snapshot: TechnicalSnapshot) -> str:
    hourly_ema20_last = snapshot.hourly_ema20_series[-1] if snapshot.hourly_ema20_series else None
    hourly_macd_last = snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None
    hourly_rsi7_last = snapshot.hourly_rsi7_series[-1] if snapshot.hourly_rsi7_series else None
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )

    return dedent(
        f"""
        ### {snapshot.symbol}

        **当前概览**
        - 价格: {fmt_number(hourly_mid_price_last)}
        - 小时线最新: EMA20 {fmt_number(hourly_ema20_last)} | MACD {fmt_number(hourly_macd_last)} | RSI7 {fmt_number(hourly_rsi7_last)}

        **短期(1h, 由旧到新)**
        - 中间价: [{fmt_list(snapshot.hourly_mid_prices_series)}]
        - EMA20: [{fmt_list(snapshot.hourly_ema20_series)}]
        - MACD: [{fmt_list(snapshot.hourly_macd_series)}]
        - MACD Hist: [{fmt_list(snapshot.hourly_macd_hist_series)}]
        - RSI7: [{fmt_list(snapshot.hourly_rsi7_series)}]
        - RSI14: [{fmt_list(snapshot.hourly_rsi14_series)}]

        **长期(日线, 由旧到新)**
        - EMA20 vs EMA50: {fmt_number(snapshot.daily_ema20_latest)} / {fmt_number(snapshot.daily_ema50_latest)}
        - ATR3 vs ATR14: {fmt_number(snapshot.daily_atr3_latest)} / {fmt_number(snapshot.daily_atr14_latest)}
        - 成交量: 当前 {fmt_number(snapshot.daily_volume_latest)} / 5日均 {fmt_number(snapshot.daily_volume_sma_5)} / 20日均 {fmt_number(snapshot.daily_volume_sma_20)}
        - MACD: [{fmt_list(snapshot.daily_macd_series)}]
        - MACD Hist: [{fmt_list(snapshot.daily_macd_hist_series)}]
        - RSI14: [{fmt_list(snapshot.daily_rsi14_series)}]
        - 涨幅: 1日 {fmt_number(snapshot.daily_change_pct_1, suffix="%")} / 5日 {fmt_number(snapshot.daily_change_pct_5, suffix="%")}

        **信号摘要**
        - {_trend_summary(snapshot)}
        - {_volume_summary(snapshot)}
        """
    ).strip()


def _build_intraday_hourly(snapshot: TechnicalSnapshot) -> str:
    hourly_ema20_last = snapshot.hourly_ema20_series[-1] if snapshot.hourly_ema20_series else None
    hourly_macd_last = snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None
    hourly_rsi7_last = snapshot.hourly_rsi7_series[-1] if snapshot.hourly_rsi7_series else None
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )

    return dedent(
        f"""
        ### {snapshot.symbol}

        **当前(1h)**
        - 价格: {fmt_number(hourly_mid_price_last)}
        - 小时线最新: EMA20 {fmt_number(hourly_ema20_last)} | MACD {fmt_number(hourly_macd_last)} | RSI7 {fmt_number(hourly_rsi7_last)}

        **短线动量(1h 序列, 由旧到新)**
        - EMA20: [{fmt_list(snapshot.hourly_ema20_series)}]
        - MACD / Hist: [{fmt_list(snapshot.hourly_macd_series)}] / [{fmt_list(snapshot.hourly_macd_hist_series)}]
        - RSI7 / RSI14: [{fmt_list(snapshot.hourly_rsi7_series)}] / [{fmt_list(snapshot.hourly_rsi14_series)}]
        - 中间价: [{fmt_list(snapshot.hourly_mid_prices_series)}]

        **趋势与波动(参考日线)**
        - EMA20 vs EMA50: {fmt_number(snapshot.daily_ema20_latest)} / {fmt_number(snapshot.daily_ema50_latest)}
        - ATR14(日线): {fmt_number(snapshot.daily_atr14_latest)}
        - 成交量(日线): {fmt_number(snapshot.daily_volume_latest)} / 5日均 {fmt_number(snapshot.daily_volume_sma_5)} / 20日均 {fmt_number(snapshot.daily_volume_sma_20)}
        """
    ).strip()


def _build_daily_post_market(snapshot: TechnicalSnapshot) -> str:
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )
    return dedent(
        f"""
        ### {snapshot.symbol}

        **收盘概览(日线)**
        - 收盘价: {fmt_number(hourly_mid_price_last)}
        - EMA20 / EMA50: {fmt_number(snapshot.daily_ema20_latest)} / {fmt_number(snapshot.daily_ema50_latest)}
        - MACD: {fmt_number(snapshot.daily_macd_series[-1] if snapshot.daily_macd_series else None)} | RSI14: {fmt_number(snapshot.daily_rsi14_latest)}
        - 涨幅: 1日 {fmt_number(snapshot.daily_change_pct_1, suffix="%")} / 5日 {fmt_number(snapshot.daily_change_pct_5, suffix="%")}

        **趋势与波动**
        - EMA 方向: {_trend_summary(snapshot)}
        - ATR3 / ATR14: {fmt_number(snapshot.daily_atr3_latest)} / {fmt_number(snapshot.daily_atr14_latest)}
        - MACD Hist(近10): [{fmt_list(snapshot.daily_macd_hist_series)}]

        **量价**
        - {_volume_summary(snapshot)}
        """
    ).strip()


def _build_quick_snapshot(snapshot: TechnicalSnapshot) -> str:
    macd_hist_last = (
        snapshot.daily_macd_hist_series[-1] if snapshot.daily_macd_hist_series else None
    )
    hourly_macd_last = snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )

    return dedent(
        f"""
        ### {snapshot.symbol}

        - 价格: {fmt_number(hourly_mid_price_last)}
        - 趋势: EMA20 {fmt_number(snapshot.daily_ema20_latest)} vs EMA50 {fmt_number(snapshot.daily_ema50_latest)}
        - 动量: MACD(1h) {fmt_number(hourly_macd_last)} | MACD Hist(日) {fmt_number(macd_hist_last)} | RSI14 {fmt_number(snapshot.daily_rsi14_latest)}
        - 波动: ATR14 {fmt_number(snapshot.daily_atr14_latest)}
        - 量: {fmt_number(snapshot.daily_volume_latest)} / 5日均 {fmt_number(snapshot.daily_volume_sma_5)} / 20日均 {fmt_number(snapshot.daily_volume_sma_20)}
        """
    ).strip()


def _build_momentum(snapshot: TechnicalSnapshot) -> str:
    macd_hist_last = (
        snapshot.hourly_macd_hist_series[-1] if snapshot.hourly_macd_hist_series else None
    )
    macd_last = snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None
    rsi7_last = snapshot.hourly_rsi7_series[-1] if snapshot.hourly_rsi7_series else None
    rsi14_last = snapshot.hourly_rsi14_series[-1] if snapshot.hourly_rsi14_series else None
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )
    return dedent(
        f"""
        ### {snapshot.symbol}

        **动量核心**
        - 价格: {fmt_number(hourly_mid_price_last)}
        - MACD(1h): {fmt_number(macd_last)} | Hist: {fmt_number(macd_hist_last)}
        - RSI7 / RSI14(最新): {fmt_number(rsi7_last)} / {fmt_number(rsi14_last)}
        - EMA20 vs EMA50(日线): {fmt_number(snapshot.daily_ema20_latest)} / {fmt_number(snapshot.daily_ema50_latest)}

        **量价与涨幅**
        - 量能: {fmt_number(snapshot.daily_volume_latest)} / 5日均 {fmt_number(snapshot.daily_volume_sma_5)} / 20日均 {fmt_number(snapshot.daily_volume_sma_20)}
        - 涨幅: 1日 {fmt_number(snapshot.daily_change_pct_1, suffix="%")} / 5日 {fmt_number(snapshot.daily_change_pct_5, suffix="%")}

        **参考序列(短线, 由旧到新)**
        - MACD Hist: [{fmt_list(snapshot.hourly_macd_hist_series)}]
        - RSI7: [{fmt_list(snapshot.hourly_rsi7_series)}]
        - RSI14: [{fmt_list(snapshot.hourly_rsi14_series)}]
        """
    ).strip()


def _build_daily_full_debug(snapshot: TechnicalSnapshot) -> str:
    """日线全量指标排查用: 列出当前可用的所有字段。"""

    hourly_ema20_last = snapshot.hourly_ema20_series[-1] if snapshot.hourly_ema20_series else None
    hourly_macd_last = snapshot.hourly_macd_series[-1] if snapshot.hourly_macd_series else None
    hourly_rsi7_last = snapshot.hourly_rsi7_series[-1] if snapshot.hourly_rsi7_series else None
    hourly_mid_price_last = (
        snapshot.hourly_mid_prices_series[-1] if snapshot.hourly_mid_prices_series else None
    )

    return dedent(
        f"""
        ### {snapshot.symbol} (日线全量指标校验)

        **小时线最新数据**
        - 中间价: {fmt_number(hourly_mid_price_last)}

        **小时线最新值**
        - EMA20: {fmt_number(hourly_ema20_last)}
        - MACD: {fmt_number(hourly_macd_last)}
        - RSI7: {fmt_number(hourly_rsi7_last)}

        **短期序列(1h, 由旧到新)**
        - 中间价: [{fmt_list(snapshot.hourly_mid_prices_series)}]
        - EMA20: [{fmt_list(snapshot.hourly_ema20_series)}]
        - MACD: [{fmt_list(snapshot.hourly_macd_series)}]
        - MACD Hist: [{fmt_list(snapshot.hourly_macd_hist_series)}]
        - RSI7: [{fmt_list(snapshot.hourly_rsi7_series)}]
        - RSI14: [{fmt_list(snapshot.hourly_rsi14_series)}]

        **长期(日线)当前值**
        - EMA20: {fmt_number(snapshot.daily_ema20_latest)}
        - EMA50: {fmt_number(snapshot.daily_ema50_latest)}
        - ATR3: {fmt_number(snapshot.daily_atr3_latest)}
        - ATR14: {fmt_number(snapshot.daily_atr14_latest)}
        - Volume 当前: {fmt_number(snapshot.daily_volume_latest)}
        - Volume 5日均: {fmt_number(snapshot.daily_volume_sma_5)}
        - Volume 20日均: {fmt_number(snapshot.daily_volume_sma_20)}
        - RSI14 当前: {fmt_number(snapshot.daily_rsi14_latest)}
        - STOCH K: {fmt_number(snapshot.daily_stoch_k_latest)}
        - STOCH D: {fmt_number(snapshot.daily_stoch_d_latest)}
        - OBV: {fmt_number(snapshot.daily_obv_latest)}
        - AD: {fmt_number(snapshot.daily_ad_latest)}
        - 涨幅: 1日 {fmt_number(snapshot.daily_change_pct_1, suffix="%")} / 5日 {fmt_number(snapshot.daily_change_pct_5, suffix="%")}

        **长期(日线)序列(由旧到新)**
        - MACD: [{fmt_list(snapshot.daily_macd_series)}]
        - MACD Hist: [{fmt_list(snapshot.daily_macd_hist_series)}]
        - RSI14: [{fmt_list(snapshot.daily_rsi14_series)}]
        """
    ).strip()


_TEMPLATE_BUILDERS = {
    TechnicalPromptTemplate.COMPREHENSIVE: _build_comprehensive,
    TechnicalPromptTemplate.INTRADAY_HOURLY: _build_intraday_hourly,
    TechnicalPromptTemplate.DAILY_POST_MARKET: _build_daily_post_market,
    TechnicalPromptTemplate.QUICK_SNAPSHOT: _build_quick_snapshot,
    TechnicalPromptTemplate.MOMENTUM: _build_momentum,
    TechnicalPromptTemplate.DAILY_FULL_DEBUG: _build_daily_full_debug,
}


def build_technical_prompt(
    snapshots: list[TechnicalSnapshot],
    *,
    template: TechnicalPromptTemplate = TechnicalPromptTemplate.COMPREHENSIVE,
) -> str:
    """根据技术面快照列表构建结构化的 Markdown 提示。"""

    if not snapshots:
        return "## 当前所有标的的市场数据\n\n(暂无可用数据)"

    builder = _TEMPLATE_BUILDERS.get(template, _build_comprehensive)
    blocks = [builder(snapshot) for snapshot in snapshots]
    joined = "\n\n---\n\n".join(blocks)
    return dedent(
        f"""
        ## 当前所有标的的市场数据 ({template})

        {joined}
        """
    ).strip()


__all__ = ["TechnicalPromptTemplate", "build_technical_prompt"]
