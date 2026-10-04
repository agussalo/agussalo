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


def run_with_stop(df, position, stop=0.02, fee=0.001, slippage=0.0005, capital=10_000.0) -> Result:
    """Como `run`, pero cierra la posicion si el minimo de la vela toca entrada*(1-stop).

    - Entrada al `open` de la vela siguiente a la senal; salida por stop al precio del stop
      (o al `open` si la vela abre con gap por debajo).
    - Tras un stop se queda afuera hasta que la senal pase por 0 y vuelva a 1 (evita reentrar al instante).
    """
    want = position.shift(1).fillna(0.0).to_numpy()
    o, l, c = (df[k].to_numpy() for k in ("open", "low", "close"))
    cost = fee + slippage
    n = len(df)
    ret, pos = np.zeros(n), np.zeros(n)
    in_pos, entry, blocked, ref = False, 0.0, False, c[0]
    stops = 0
    for i in range(n):
        if want[i] == 0:
            blocked = False
        if in_pos:
            level = entry * (1 - stop)
            if l[i] <= level:  # stop
                px = min(level, o[i])
                ret[i] = px / ref - 1 - cost
                in_pos, blocked, stops = False, True, stops + 1
            elif want[i] == 0:  # salida por senal al open
                ret[i] = o[i] / ref - 1 - cost
                in_pos = False
            else:
                ret[i], pos[i] = c[i] / ref - 1, 1.0
        elif want[i] == 1 and not blocked:
            in_pos, entry = True, o[i]
            ret[i], pos[i] = c[i] / o[i] - 1 - cost, 1.0
        ref = c[i]
    ret_s = pd.Series(ret, index=df.index)
    equity = capital * (1 + ret_s).cumprod()
    pos_s = pd.Series(pos, index=df.index)
    turnover = pos_s.diff().abs().fillna(pos_s.abs())
    res = Result(equity, ret_s, pos_s, stats(df, ret_s, equity, pos_s, turnover))
    res.stats["stops_activados"] = stops
    return res
