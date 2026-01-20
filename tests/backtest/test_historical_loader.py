"""向量化回测 CSV 加载测试。"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from app.data_feed import HistoricalDataLoader


def test_historical_loader_csv():
    """测试历史数据加载器 CSV 加载功能。"""
    loader = HistoricalDataLoader()

    # 创建测试 CSV 数据
    csv_data = """date,symbol,open,high,low,close,volume
2024-01-01,000001.SZ,10.5,11.0,10.3,10.8,1000000
2024-01-02,000001.SZ,10.8,11.2,10.7,11.0,1200000
2024-01-03,000001.SZ,11.0,11.5,11.0,11.3,1500000
"""

    # 写入临时文件
    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_data)
        temp_path = f.name

    try:
        # 测试加载
        df = loader.load_from_csv(temp_path, symbol="000001.SZ")

        # 验证结果
        assert not df.empty, "加载结果不应为空"
        assert list(df.columns) == ["date", "symbol", "open", "high", "low", "close", "volume"]
        assert len(df) == 3, f"应该加载3行数据,实际加载了{len(df)}行"

        # 验证数据类型
        assert df["date"].dtype.name == "object", "日期列应为object类型"
        assert df["open"].dtype.name == "float64", "open列应为float64"

        # 打印结果
        print(f"\n{'=' * 60}")
        print("CSV 加载测试结果")
        print(f"{'=' * 60}")
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print(f"前3行:\n{df.head(3)}")
        print(f"{'=' * 60}\n")

        return True

    finally:
        # 清理临时文件
        Path(temp_path).unlink(missing_ok=True)


def test_historical_loader_format_detection():
    """测试不同 CSV 格式的自动识别。"""
    loader = HistoricalDataLoader()

    # 测试 AkShare 格式
    akshare_csv = """date,open,high,low,close,volume,amount,change_pct
2024-01-01,10.5,11.0,10.3,10.8,1000000,10800000,2.86
"""

    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(akshare_csv)
        temp_path = f.name

    try:
        df = loader.load_from_csv(temp_path, symbol="000001.SZ")
        assert "date" in df.columns
        assert "symbol" in df.columns
        print(f"AkShare 格式识别成功，列: {df.columns.tolist()}")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    # 测试标准格式
    standard_csv = """date,symbol,open,high,low,close,volume
2024-01-01,000001.SZ,10.5,11.0,10.3,10.8,1000000
"""

    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(standard_csv)
        temp_path = f.name

    try:
        df = loader.load_from_csv(temp_path, symbol="000001.SZ")
        assert list(df.columns) == ["date", "symbol", "open", "high", "low", "close", "volume"]
        print(f"标准格式识别成功，列: {df.columns.tolist()}")
    finally:
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("测试 1: CSV 加载功能\n")
    test_historical_loader_csv()

    print("\n测试 2: 格式自动识别\n")
    test_historical_loader_format_detection()

    print("\n✅ 所有测试通过!")
