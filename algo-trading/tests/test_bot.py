import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backtester import data
from backtester.strategies import sma_cross
from bot.bot import Bot
from bot.brokers import SimBroker


def _bot(tmp_path, **kw):
    br = SimBroker(10_000, path=tmp_path / "s.json")
    return br, Bot(br, sma_cross, state_path=tmp_path / "b.json", log_path=tmp_path / "t.csv", log=lambda *_: None, **kw)


def test_replay_opera_y_deja_registro(tmp_path):
    df = data.synthetic_ohlcv(n=1500)
    br, bot = _bot(tmp_path, stop=0.03, risk=0.01)
    acciones = []
    for i in range(200, len(df)):
        acciones.append(bot.step(df.iloc[:i], df["close"].iloc[i - 1]))
    assert "compra" in acciones and ("venta" in acciones or "stop" in acciones)
    trades = pd.read_csv(tmp_path / "t.csv")
    assert len(trades) > 2
    assert br.cash >= 0


def test_stop_vende_y_bloquea_reentrada(tmp_path):
    df = data.synthetic_ohlcv(n=600)
    br, bot = _bot(tmp_path, stop=0.03, risk=0.01)
    i = 200
    while br.qty == 0 and i < len(df):  # avanza hasta que compre
        bot.step(df.iloc[:i], df["close"].iloc[i - 1]); i += 1
    assert br.qty > 0
    entry = bot.st.entry
    assert bot.step(df.iloc[:i], entry * 0.96) == "stop"
    assert br.qty == 0 and bot.st.blocked


def test_no_entra_a_mitad_de_tendencia_al_arrancar(tmp_path):
    n = 300
    c = pd.Series(np.linspace(100, 200, n))  # tendencia alcista: la senal ya es 1
    df = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1.0},
                      index=pd.date_range("2025-01-01", periods=n, freq="1h"))
    br, bot = _bot(tmp_path)
    assert bot.step(df, 200.0) is None and br.qty == 0
