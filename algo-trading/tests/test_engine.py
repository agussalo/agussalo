import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backtester import engine


def _df(o, h, l, c):
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0},
                        index=pd.date_range("2025-01-01", periods=len(c), freq="1h"))


def test_stop_sale_al_precio_del_stop():
    # entra al open de la vela 1 (100); la vela 2 toca -5% -> sale a 95
    df = _df([100, 100, 100, 90], [100, 101, 100, 91], [100, 99, 90, 89], [100, 100, 96, 90])
    r = engine.run_with_stop(df, pd.Series([1.0, 1.0, 1.0, 1.0], index=df.index), stop=0.05, fee=0, slippage=0)
    assert r.stats["stops_activados"] == 1
    assert np.isclose(r.returns.iloc[2], 95 / 100 - 1)
    assert r.returns.iloc[3] == 0  # queda afuera tras el stop


def test_sin_stop_coincide_con_motor_vectorizado():
    rng = np.random.default_rng(0)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.01, 300))
    df = _df(np.r_[100, c[:-1]], c * 1.002, c * 0.998, c)
    pos = pd.Series((np.sin(np.arange(300) / 20) > 0).astype(float), index=df.index)
    a = engine.run(df, pos, 0.001, 0.0005).stats["retorno_total"]
    b = engine.run_with_stop(df, pos, stop=1e9, fee=0.001, slippage=0.0005).stats["retorno_total"]
    assert abs(a - b) < 0.02  # difieren solo en el precio de entrada (close vs open)


def test_sin_look_ahead():
    # la senal de la vela t solo gana desde t+1: si la senal es 1 solo en la vela 1, no gana el retorno de la vela 1
    df = _df([100, 100, 110], [100, 110, 110], [100, 100, 110], [100, 110, 110])
    r = engine.run(df, pd.Series([0.0, 1.0, 0.0], index=df.index), fee=0, slippage=0)
    assert r.returns.iloc[1] == 0


def test_tamano_por_riesgo_limita_la_perdida_del_stop():
    df = _df([100, 100, 100, 90], [100, 101, 100, 91], [100, 99, 90, 89], [100, 100, 96, 90])
    pos = pd.Series([1.0] * 4, index=df.index)
    r = engine.run_with_stop(df, pos, stop=0.05, fee=0, slippage=0, risk=0.01)  # f = 0.2
    assert np.isclose(r.returns.iloc[2], -0.01)
    assert np.isclose(r.position.max(), 0.2)
