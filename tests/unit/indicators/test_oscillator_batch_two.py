from decimal import Decimal

from services.core.indicators.cci import CCIIndicator
from services.core.indicators.mfi import MFIIndicator
from services.core.indicators.roc import ROCIndicator
from services.core.indicators.stochastic import StochasticIndicator
from services.core.indicators.williams_r import WilliamsRIndicator


def test_stochastic_roc_and_cci_outputs_are_sensible(indicator_bars) -> None:
    stochastic_outputs = StochasticIndicator(k_period=14, d_period=3).compute(indicator_bars)
    roc_outputs = ROCIndicator(period=12).compute(indicator_bars)
    cci_outputs = CCIIndicator(period=20).compute(indicator_bars)

    assert {"percent_k", "percent_d"} <= {item.component for item in stochastic_outputs}
    stochastic_values = [item.value for item in stochastic_outputs if item.component == "percent_k"]
    assert stochastic_values
    assert all(Decimal("0") <= value <= Decimal("100") for value in stochastic_values)
    assert roc_outputs[-1].value > 0
    assert cci_outputs


def test_mfi_and_williams_r_stay_in_expected_ranges(indicator_bars) -> None:
    mfi_outputs = MFIIndicator(period=14).compute(indicator_bars)
    williams_outputs = WilliamsRIndicator(period=14).compute(indicator_bars)

    assert mfi_outputs
    assert all(Decimal("0") <= item.value <= Decimal("100") for item in mfi_outputs)
    assert williams_outputs
    assert all(Decimal("-100") <= item.value <= Decimal("0") for item in williams_outputs)
