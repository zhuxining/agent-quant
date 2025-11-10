# %%

from longport_source import LongportSource
from talib_calculator import IndicatorCalculator

longport_data = LongportSource().get_candles_frame(symbol="510300.SH", interval="1h")
# print(longport_data)

indicator_calculator = IndicatorCalculator().compute_ema(longport_data)
indicator_calculator1 = IndicatorCalculator().compute_rsi(indicator_calculator)
print(indicator_calculator1)
