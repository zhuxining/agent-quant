from textwrap import dedent


def build_decision_synthesis_prompt(
    news_result: str,
    technical_result: str,
    fundamental_result: str,
    account_info: str,
) -> str:
    """构建决策综合 Prompt（Team Leader）。

    Args:
        news_result: 新闻情绪 Agent 的分析结果
        technical_result: 技术分析 Agent 的分析结果
        fundamental_result: 基本面分析 Agent 的分析结果
        account_info: 账户信息

    Returns:
        格式化的 Markdown 字符串
    """
    return dedent(
        f"""
        ## 多维度交易决策分析

        你是 Team Leader，负责汇总新闻情绪、技术面、基本面的分析结论，结合账户信息，给出最终交易决策。

        ### 新闻情绪分析
        {news_result}

        ### 技术面分析
        {technical_result}

        ### 基本面分析
        {fundamental_result}

        ### 账户信息
        {account_info}

        **决策要求**:
        - 综合三个维度的分析结果，评估投资机会
        - 考虑账户当前的仓位和资金情况
        - 给出明确的交易建议（buy/sell/hold/wait）
        - 对于 buy 建议，指定标的代码、建议数量或权重
        - 对于 sell 建议，指定标的代码和数量
        - 说明决策逻辑和权重分配
        - 评估决策的置信度（0-1）
        - 识别主要风险点

        **输出格式**:
        请按照以下格式输出交易决策：

        ```json
        {{
          "actions": [
            {{
              "symbol": "标的代码",
              "action": "buy/sell/hold/wait",
              "quantity": 数量（整数，如不适用则为 null）,
              "weight": 权重（浮点数，0-1，如不适用则为 null）
            }}
          ],
          "explanation": "决策说明",
          "confidence": 0.0-1.0
        }}
        ```
        """
    ).strip()


__all__ = ["build_decision_synthesis_prompt"]
