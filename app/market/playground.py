# %%
# from data_feed import DataFeed
from longport_source import LongportSource
from talib_calculator import IndicatorCalculator

longport_data = LongportSource().get_candles_frame(symbol="510300.SH", interval="1d")
# # print(longport_data)

indicator_calculator = IndicatorCalculator().compute_ema(longport_data)
indicator_calculator1 = IndicatorCalculator().compute_change(indicator_calculator)
print(indicator_calculator1)

# data_feed = DataFeed().build_snapshot("510300.SH")
# print(data_feed)
