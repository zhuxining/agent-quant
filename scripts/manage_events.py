#!/usr/bin/env python3
"""历史事件批量导入脚本。

从 CSV 文件批量导入历史事件到数据库。
CSV 格式：
  date,symbol,event_type,title,content,impact_score

示例：
  2024-01-15,000001.SZ,news,重大利好,公司发布超预期财报,5
  2024-02-20,000001.SZ,financial,业绩超预期,公司年报亏损,2
  =======================================

  支持的事件类型：
  - news: 新闻事件
  - financial: 财报事件
  - policy: 政策事件
  - macro: 宏观经济事件

  影响评分：
  - -5 到 -2：强负面
  - -1 到 -1：负面
  - 0：中性
  - 1 到 5：正面
"""

import argparse
import sys

import pandas as pd
from sqlmodel import Session, create_engine

from app.models.historical_event import EventType, HistoricalEvent


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="历史事件批量导入脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv_path", help="CSV 文件路径")
    parser.add_argument(
        "--source",
        default="manual",
        choices=["manual", "csv_import"],
        help="事件来源",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="不实际导入，只显示将要导入的事件",
    )

    return parser.parse_args()


def load_csv(csv_path: str) -> pd.DataFrame:
    """加载 CSV 文件。"""
    try:
        df = pd.read_csv(csv_path)

        required_columns = ["date", "symbol", "event_type", "title", "content", "impact_score"]

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"CSV 文件缺少必需列: {col}")

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["symbol"] = df["symbol"].astype(str).str.strip()
        df["event_type"] = df["event_type"].str.lower()
        df["impact_score"] = pd.to_numeric(df["impact_score"], errors="coerce")

        if "impact_score" not in df.columns:
            df["impact_score"] = 0

        df["impact_score"] = df["impact_score"].clip(-5, 5).astype(int)

        return df

    except FileNotFoundError:
        print(f"错误：找不到 CSV 文件: {csv_path}")
        sys.exit(1)

    except Exception as e:
        print(f"错误：加载 CSV 失败: {e}")
        sys.exit(1)


def validate_events(df: pd.DataFrame) -> tuple[list[str], bool]:
    """验证事件数据。"""
    errors = []

    for i, (_, row) in enumerate(df.iterrows()):
        if pd.isna(row["event_type"]) or pd.isna(row["symbol"]) or pd.isna(row["title"]):
            errors.append(f"第 {i + 1} 行：event_type、symbol 或 title 为空")

        if not pd.isna(row["impact_score"]) and not (-5 <= row["impact_score"] <= 5):
            errors.append(f"第 {i + 1} 行：impact_score 必须在 -5 到 5 之间")

    return errors, len(errors) == 0


def import_events(
    session: Session,
    df: pd.DataFrame,
    source: str,
) -> tuple[int, int]:
    """批量导入事件到数据库。"""
    success_count = 0
    failure_count = 0

    for i, (_, row) in enumerate(df.iterrows()):
        event_date = row["date"]
        if pd.isna(event_date):
            print(f"第 {i + 1} 行：日期为空，跳过")
            failure_count += 1
            continue

        symbol = row["symbol"]
        event_type_str = row["event_type"]

        event_type_map = {
            "news": EventType.NEWS,
            "financial": EventType.FINANCIAL,
            "policy": EventType.POLICY,
            "macro": EventType.MACRO,
        }

        event_type = event_type_map.get(event_type_str, EventType.MACRO)

        title = row["title"] if pd.notna(row["title"]) else "未命名事件"
        content = row["content"] if pd.notna(row["content"]) else ""
        impact_score = int(row["impact_score"])

        event = HistoricalEvent(
            event_date=event_date,
            symbol=symbol,
            event_type=event_type,
            title=title,
            content=content,
            impact_score=impact_score,
            source=source,
        )

        session.add(event)
        success_count += 1

        if (i + 1) % 100 == 0:
            print(f"进度: {i + 1}/{len(df)} 事件已导入")

    session.commit()
    print("\n导入完成！")
    print(f"  - 成功: {success_count} 条")
    print(f"  - 失败: {failure_count} 条")
    print(f"  - 总计: {len(df)} 条")

    return success_count, failure_count


def main():
    """主函数。"""
    args = parse_args()

    df = load_csv(args.csv_path)
    errors, is_valid = validate_events(df)

    if not is_valid:
        print("\n验证失败，发现以下错误：")
        for error in errors[:10]:
            print(f"  - {error}")
        sys.exit(1)

    from app.core.config import settings

    # Build sync database URL
    if settings.DATABASE_TYPE == "postgresql":
        database_url = str(settings.postgre_url).replace("+asyncpg", "")
    else:
        database_url = f"sqlite:///{settings.SQLITE_URL}"

    engine = create_engine(database_url)

    with Session(engine) as session:
        _success_count, failure_count = import_events(
            session=session,
            df=df,
            source=args.source,
        )

    sys.exit(0 if failure_count > 0 else 1)
