from services.core.indicators.donchian import DonchianChannelIndicator
from services.core.indicators.keltner import KeltnerChannelIndicator


def test_keltner_channel_and_donchian_channel_return_ordered_bands(indicator_bars) -> None:
    keltner_outputs = KeltnerChannelIndicator(ema_period=20, atr_period=10, multiplier=2).compute(indicator_bars)
    donchian_outputs = DonchianChannelIndicator(period=20).compute(indicator_bars)

    latest_keltner = [item for item in keltner_outputs if item.trade_date == indicator_bars[-1].trade_date]
    latest_donchian = [item for item in donchian_outputs if item.trade_date == indicator_bars[-1].trade_date]
    keltner_map = {item.component: item.value for item in latest_keltner}
    donchian_map = {item.component: item.value for item in latest_donchian}

    assert {"upper_band", "middle_band", "lower_band"} == set(keltner_map)
    assert keltner_map["upper_band"] > keltner_map["middle_band"] > keltner_map["lower_band"]
    assert {"upper_band", "middle_band", "lower_band"} == set(donchian_map)
    assert donchian_map["upper_band"] >= donchian_map["middle_band"] >= donchian_map["lower_band"]
