from textwrap import dedent

from app.prompt_build.formatters import fmt_number, fmt_pct


def build_risk_control_prompt(
    decision: str,
    account_info: str,
) -> str:
    """构建风控 Prompt。

    Args:
        decision: 决策综合 Agent 的交易决策
        account_info: 账户信息

    Returns:
        格式化的 Markdown 字符串
    """
    return dedent(
        f"""
        ## 风险控制检查

        你是风控 Agent，负责验证交易决策的风险敞口、仓位限制、止损止盈规则。

        ### 待验证的交易决策
        {decision}

        ### 账户信息
        {account_info}

        **风控规则**:
        - 单笔交易风险 ≤ 账户总资产的 1%
        - 总仓位 ≤ 账户可用资金的 80%
        - 每个标的的持仓比例 ≤ 账户总资产的 20%
        - 必须设置止损位（建议使用 ATR 的 1-2 倍）
        - 必须设置止盈位（建议盈亏比 ≥ 2:1）
        - 连续 3 笔亏损后暂停交易，进行复盘

        **验证要求**:
        - 检查每笔交易的风险敞口
        - 验证总仓位是否超限
        - 检查止损止盈设置是否合理
        - 识别潜在的风险点
        - 如违反风控规则，拒绝交易决策并说明原因
        - 如符合风控规则，输出调整后的交易决策

        **输出格式**:
        请按照以下格式输出风控结果：

        ```json
        {{
          "passed": true/false,
          "reason": "风控检查结果说明",
          "adjusted_actions": [
            {{
              "symbol": "标的代码",
              "action": "buy/sell/hold/wait",
              "quantity": 数量（整数）,
              "weight": 权重（0-1）,
              "stop_loss": 止损价,
              "take_profit": 止盈价
            }}
          ]
        }}
        ```
        """
    ).strip()


__all__ = ["build_risk_control_prompt"]
