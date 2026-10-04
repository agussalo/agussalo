"""Uso:
    python run_backtest.py --strategy sma_cross --symbol BTC/USDT --days 365
    python run_backtest.py --synthetic            # sin conexion a internet
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backtester import data, engine
from backtester.strategies import STRATEGIES


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=STRATEGIES, default="sma_cross")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1h")
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--exchange", default="binance")
    p.add_argument("--fee", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.0005)
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--out", default="equity.png")
    a = p.parse_args()

    df = (
        data.synthetic_ohlcv()
        if a.synthetic
        else data.fetch_ohlcv(a.symbol, a.timeframe, a.days, a.exchange)
    )
    res = engine.run(df, STRATEGIES[a.strategy](df), a.fee, a.slippage)

    for k, v in res.stats.items():
        print(f"{k:>18}: {v:.2%}" if isinstance(v, float) and k != "sharpe" else f"{k:>18}: {v:.2f}" if k == "sharpe" else f"{k:>18}: {v}")

    fig, ax = plt.subplots(figsize=(10, 4))
    res.equity.plot(ax=ax, label=a.strategy)
    (10_000 * df["close"] / df["close"].iloc[0]).plot(ax=ax, label="buy & hold", alpha=0.6)
    ax.legend(); ax.set_title("Equity"); fig.tight_layout(); fig.savefig(a.out)
    print(f"grafico: {a.out}")


if __name__ == "__main__":
    main()
