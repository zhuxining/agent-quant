from textwrap import dedent

from app.prompt_build.formatters import fmt_number, fmt_pct


def build_fundamental_analysis_prompt(
    symbol: str,
    financial_data: dict,
) -> str:
    """构建基本面分析 Prompt。

    Args:
        symbol: 股票代码
        financial_data: 基本面数据字典，包含 PE、PB、ROE 等指标

    Returns:
        格式化的 Markdown 字符串
    """
    if not financial_data:
        return dedent(
            f"""
            ## 基本面分析: {symbol}

            (暂无基本面数据）
            """
        ).strip()

    key_metrics = []
    for key, value in financial_data.items():
        if key in ["股票代码", "股票简称"]:
            continue
        if isinstance(value, (int, float)):
            key_metrics.append(f"- **{key}**: {fmt_number(value)}")
        elif value:
            key_metrics.append(f"- **{key}**: {value}")

    return dedent(
        f"""
        ## 基本面分析: {symbol}

        以下是该股票的基本面指标和财务数据。

        {chr(10).join(key_metrics)}

        **分析要求**:
        - 评估估值水平（PE、PB 等估值指标）
        - 分析财务健康度（负债率、现金流等）
        - 评估盈利能力（ROE、净利润率等）
        - 识别成长性（营收增长率、利润增长率等）
        - 给出基本面评分（1-5 分，5 为优秀）
        - 评估长期投资价值（强烈买入/买入/持有/卖出）
        """
    ).strip()


__all__ = ["build_fundamental_analysis_prompt"]
