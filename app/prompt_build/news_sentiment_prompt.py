from textwrap import dedent


def build_news_sentiment_prompt(
    symbol: str,
    news_data: list[dict],
) -> str:
    """构建新闻情绪分析 Prompt。

    Args:
        symbol: 股票代码
        news_data: 新闻数据列表，每个元素包含 title, content, publish_time 等字段

    Returns:
        格式化的 Markdown 字符串
    """
    if not news_data:
        return dedent(
            f"""
            ## 新闻情绪分析: {symbol}

            (暂无新闻数据）
            """
        ).strip()

    news_items = []
    for idx, news in enumerate(news_data[:10], start=1):
        title = news.get("title", "")
        content = news.get("content", "")
        publish_time = news.get("publish_time", "")
        source = news.get("source", "")

        content_snippet = content[:200] + "..." if len(content) > 200 else content

        news_items.append(
            dedent(
                f"""
                ### 新闻 {idx}

                **标题**: {title}
                **来源**: {source}
                **时间**: {publish_time}

                **摘要**:
                {content_snippet}
                """
            ).strip()
        )

    return dedent(
        f"""
        ## 新闻情绪分析: {symbol}

        以下是近期的相关新闻，请分析情绪倾向、关键词和潜在风险。

        {"\n\n".join(news_items)}

        **分析要求**:
        - 分析每条新闻的情绪倾向（正面/负面/中性）
        - 提取关键词和主要话题
        - 识别潜在的利好或利空因素
        - 评估新闻对股价的短期影响
        - 给出情绪评分（-1 到 1，-1 极度负面，0 中性，1 极度正面）
        """
    ).strip()


__all__ = ["build_news_sentiment_prompt"]
