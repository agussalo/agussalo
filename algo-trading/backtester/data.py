"""Descarga de velas OHLCV (ccxt) con cache en CSV y generador sintetico."""
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data"


def fetch_ohlcv(symbol="BTC/USDT", timeframe="1h", days=365, exchange="binance"):
    import ccxt

    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"{exchange}_{symbol.replace('/', '-')}_{timeframe}_{days}d.csv"
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)

    ex = getattr(ccxt, exchange)({"enableRateLimit": True})
    ms = ex.parse_timeframe(timeframe) * 1000
    since = ex.milliseconds() - days * 86_400_000
    rows = []
    while since < ex.milliseconds():
        batch = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not batch:
            break
        rows += batch
        since = batch[-1][0] + ms
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df.pop("ts"), unit="ms")
    df = df[~df.index.duplicated()]
    df.to_csv(path)
    return df


def synthetic_ohlcv(n=8760, seed=42, start_price=30_000.0, freq="1h"):
    """Camino aleatorio con tendencia/volatilidad cambiantes, para probar sin red."""
    rng = np.random.default_rng(seed)
    vol = 0.004 * np.exp(np.cumsum(rng.normal(0, 0.02, n)) * 0.2)
    drift = np.sin(np.arange(n) / 600) * 0.0004
    close = start_price * np.exp(np.cumsum(drift + rng.normal(0, 1, n) * vol))
    open_ = np.r_[start_price, close[:-1]]
    spread = np.abs(rng.normal(0, 1, n)) * vol * close
    idx = pd.date_range("2025-01-01", periods=n, freq=freq)
    return pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) + spread,
            "low": np.minimum(open_, close) - spread,
            "close": close,
            "volume": rng.uniform(10, 100, n),
        },
        index=idx,
    )
