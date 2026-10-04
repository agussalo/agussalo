"""Motor de backtest vectorizado con comisiones y slippage."""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Result:
    equity: pd.Series
    returns: pd.Series
    position: pd.Series
    stats: dict


def periods_per_year(index: pd.DatetimeIndex) -> float:
    step = pd.Series(index).diff().median()
    return pd.Timedelta(days=365) / step


def run(df, position, fee=0.001, slippage=0.0005, capital=10_000.0) -> Result:
    """fee/slippage son fracciones por operacion sobre el nocional cambiado."""
    pos = position.shift(1).fillna(0.0)  # se opera en la vela siguiente
    asset_ret = df["close"].pct_change().fillna(0.0)
    turnover = pos.diff().abs().fillna(pos.abs())
    ret = pos * asset_ret - turnover * (fee + slippage)
    equity = capital * (1 + ret).cumprod()
    return Result(equity, ret, pos, stats(df, ret, equity, pos, turnover))


def stats(df, ret, equity, pos, turnover) -> dict:
    ppy = periods_per_year(df.index)
    total = equity.iloc[-1] / equity.iloc[0] - 1
    years = len(df) / ppy
    dd = equity / equity.cummax() - 1
    std = ret.std()
    bh = df["close"].iloc[-1] / df["close"].iloc[0] - 1
    return {
        "retorno_total": total,
        "retorno_anual": (1 + total) ** (1 / years) - 1 if years > 0 else np.nan,
        "sharpe": ret.mean() / std * np.sqrt(ppy) if std > 0 else np.nan,
        "max_drawdown": dd.min(),
        "operaciones": int((turnover > 0).sum()),
        "tiempo_en_mercado": pos.abs().mean(),
        "buy_and_hold": bh,
    }
