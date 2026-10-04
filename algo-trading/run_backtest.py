"""Uso:
    python run_backtest.py --strategy sma_cross --symbol BTC/USDT --days 365
    python run_backtest.py --synthetic            # sin conexion a internet
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backtester import data, engine
from backtester.walk_forward import resumen, walk_forward
from backtester.strategies import STRATEGIES


GRIDS = {
    "sma_cross": {"fast": [5, 10, 20, 40], "slow": [30, 60, 120, 200]},
    "rsi_reversion": {"period": [7, 14, 21], "low": [20, 30, 40], "high": [50, 55, 65]},
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=STRATEGIES, default="sma_cross")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1h")
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--exchange", default="binance")
    p.add_argument("--fee", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.0005)
    p.add_argument("--stop", type=float, default=None, help="stop-loss como fraccion, ej. 0.03 = 3%%")
    p.add_argument("--walk-forward", action="store_true", help="optimiza en ventanas moviles y mide fuera de muestra")
    p.add_argument("--train", type=int, default=2000, help="velas de entrenamiento (walk-forward)")
    p.add_argument("--test", type=int, default=500, help="velas de prueba (walk-forward)")
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--out", default="equity.png")
    a = p.parse_args()

    df = (
        data.synthetic_ohlcv()
        if a.synthetic
        else data.fetch_ohlcv(a.symbol, a.timeframe, a.days, a.exchange)
    )
    strat = STRATEGIES[a.strategy]

    if a.walk_forward:
        oos, elegidos = walk_forward(df, strat, GRIDS[a.strategy], a.train, a.test, a.stop, a.fee, a.slippage)
        for t, params, sh in elegidos:
            print(f"{t:%Y-%m-%d} eligio {params} (Sharpe en entrenamiento {sh:+.2f})")
        print("\nRESULTADO FUERA DE MUESTRA (lo unico honesto):")
        for k, v in resumen(df, oos).items():
            print(f"{k:>18}: {v:.2f}" if k == "sharpe" else f"{k:>18}: {v:.2%}")
        return

    pos = strat(df)
    res = engine.run_with_stop(df, pos, a.stop, a.fee, a.slippage) if a.stop else engine.run(df, pos, a.fee, a.slippage)

    for k, v in res.stats.items():
        print(f"{k:>18}: {v:.2%}" if isinstance(v, float) and k != "sharpe" else f"{k:>18}: {v:.2f}" if k == "sharpe" else f"{k:>18}: {v}")

    fig, ax = plt.subplots(figsize=(10, 4))
    res.equity.plot(ax=ax, label=a.strategy)
    (10_000 * df["close"] / df["close"].iloc[0]).plot(ax=ax, label="buy & hold", alpha=0.6)
    ax.legend(); ax.set_title("Equity"); fig.tight_layout(); fig.savefig(a.out)
    print(f"grafico: {a.out}")


if __name__ == "__main__":
    main()
