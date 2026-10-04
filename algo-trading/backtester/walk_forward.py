"""Walk-forward: optimizar en una ventana, operar la siguiente (que el modelo nunca vio), y rodar."""
import itertools

import numpy as np
import pandas as pd

from . import engine


def walk_forward(df, strategy, grid, train=2000, test=500, stop=None, fee=0.001, slippage=0.0005, min_trades=5, risk=None):
    """grid: dict {param: [valores]}. Devuelve (retornos fuera de muestra, lista de parametros elegidos)."""
    names = list(grid)
    combos = [dict(zip(names, v)) for v in itertools.product(*grid.values())]

    def backtest(sl, params, lo):
        pos = strategy(df.iloc[sl], **params)  # senal con calentamiento previo
        d, p = df.iloc[sl].iloc[lo:], pos.iloc[lo:]
        return engine.run_with_stop(d, p, stop, fee, slippage, risk=risk) if stop else engine.run(d, p, fee, slippage)

    oos, elegidos = [], []
    start = 0
    while start + train + test <= len(df):
        tr = slice(start, start + train)
        mejor, mejor_sh = None, -np.inf
        for params in combos:
            r = backtest(tr, params, 0)
            if r.stats["operaciones"] >= min_trades and r.stats["sharpe"] > mejor_sh:
                mejor, mejor_sh = params, r.stats["sharpe"]
        if mejor is None:
            mejor = combos[0]
        te = slice(start, start + train + test)  # entrenamiento incluido solo como calentamiento
        r = backtest(te, mejor, train)
        oos.append(r.returns)
        elegidos.append((df.index[start + train], mejor, mejor_sh))
        start += test
    return pd.concat(oos), elegidos


def resumen(df, oos: pd.Series) -> dict:
    """Metricas de los retornos fuera de muestra encadenados."""
    d = df.loc[oos.index]
    eq = (1 + oos).cumprod()
    ppy = engine.periods_per_year(d.index)
    return {
        "retorno_total": eq.iloc[-1] - 1,
        "sharpe": oos.mean() / oos.std() * np.sqrt(ppy) if oos.std() > 0 else np.nan,
        "max_drawdown": (eq / eq.cummax() - 1).min(),
        "buy_and_hold": d["close"].iloc[-1] / d["close"].iloc[0] - 1,
    }
