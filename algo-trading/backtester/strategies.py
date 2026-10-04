"""Una estrategia es una funcion df -> Series de posicion deseada (1 largo, 0 fuera).

La senal calculada con la vela t se ejecuta recien en la vela t+1 (ver engine),
para evitar look-ahead bias.
"""
import numpy as np
import pandas as pd


def sma_cross(df: pd.DataFrame, fast=20, slow=50) -> pd.Series:
    f = df["close"].rolling(fast).mean()
    s = df["close"].rolling(slow).mean()
    return (f > s).astype(float).where(s.notna(), 0.0)


def rsi_reversion(df: pd.DataFrame, period=14, low=30, high=55) -> pd.Series:
    d = df["close"].diff()
    up = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    pos = pd.Series(np.nan, index=df.index)
    pos[rsi < low] = 1.0   # entra sobrevendido
    pos[rsi > high] = 0.0  # sale al recuperar
    return pos.ffill().fillna(0.0)


STRATEGIES = {"sma_cross": sma_cross, "rsi_reversion": rsi_reversion}
