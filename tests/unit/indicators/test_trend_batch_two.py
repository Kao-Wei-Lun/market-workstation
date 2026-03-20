from decimal import Decimal

from services.core.indicators.adx import ADXIndicator
from services.core.indicators.atr import ATRIndicator
from services.core.indicators.ichimoku import IchimokuIndicator
from services.core.indicators.obv import OBVIndicator
from services.core.indicators.parabolic_sar import ParabolicSARIndicator
from services.core.indicators.supertrend import SupertrendIndicator


def test_adx_and_atr_outputs_have_expected_components_and_ranges(indicator_bars) -> None:
    adx_outputs = ADXIndicator(period=14).compute(indicator_bars)
    atr_outputs = ATRIndicator(period=14).compute(indicator_bars)

    assert {"plus_di", "minus_di", "adx"} <= {item.component for item in adx_outputs}
    assert all(item.value >= 0 for item in atr_outputs)
    adx_values = [item.value for item in adx_outputs if item.component == "adx"]
    assert adx_values
    assert all(Decimal("0") <= value <= Decimal("100") for value in adx_values)


def test_obv_ichimoku_supertrend_and_psar_return_expected_components(indicator_bars) -> None:
    obv_outputs = OBVIndicator().compute(indicator_bars)
    ichimoku_outputs = IchimokuIndicator().compute(indicator_bars)
    supertrend_outputs = SupertrendIndicator(period=10, multiplier=3).compute(indicator_bars)
    psar_outputs = ParabolicSARIndicator().compute(indicator_bars)

    assert obv_outputs[-1].value > obv_outputs[0].value
    assert {"conversion_line", "base_line", "leading_span_a", "leading_span_b", "lagging_span"} <= {
        item.component for item in ichimoku_outputs
    }
    assert {"value", "trend"} == {item.component for item in supertrend_outputs[-2:]}
    trend_values = {item.value for item in supertrend_outputs if item.component == "trend"}
    assert trend_values <= {Decimal("1"), Decimal("-1")}
    assert {"sar", "trend"} <= {item.component for item in psar_outputs}
