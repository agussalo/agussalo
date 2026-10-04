"""Bot de paper trading (SIN dinero real).

  python run_bot.py --mode sim                # cuenta simulada local, precios reales publicos (sin claves)
  python run_bot.py --mode testnet            # ordenes en el testnet de Binance (claves de testnet en variables de entorno)
  python run_bot.py --mode sim --once         # una sola pasada (para probar la conexion)
"""
import argparse
import time

import ccxt

from backtester.strategies import STRATEGIES
from bot.bot import Bot
from bot.brokers import SimBroker, TestnetBroker
import pandas as pd


def closed_candles(ex, symbol, timeframe, n=300):
    rows = ex.fetch_ohlcv(symbol, timeframe, limit=n + 1)[:-1]  # la ultima vela esta incompleta
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df.pop("ts"), unit="ms")
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["sim", "testnet"], default="sim")
    p.add_argument("--strategy", choices=STRATEGIES, default="sma_cross")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1h")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--stop", type=float, default=0.03)
    p.add_argument("--risk", type=float, default=0.01)
    p.add_argument("--capital", type=float, default=10_000.0, help="solo modo sim")
    p.add_argument("--poll", type=int, default=30, help="segundos entre revisiones")
    p.add_argument("--once", action="store_true")
    a = p.parse_args()

    data_ex = getattr(ccxt, a.exchange)({"enableRateLimit": True})  # datos publicos reales
    broker = SimBroker(a.capital) if a.mode == "sim" else TestnetBroker(a.symbol, a.exchange)
    bot = Bot(broker, STRATEGIES[a.strategy], a.stop, a.risk)
    print(f"Paper trading [{a.mode}] {a.symbol} {a.timeframe} {a.strategy} stop={a.stop:.1%} riesgo={a.risk:.1%}. Ctrl+C para parar.")
    price = None
    while True:
        try:
            candles = closed_candles(data_ex, a.symbol, a.timeframe)
            price = data_ex.fetch_ticker(a.symbol)["last"]
            bot.step(candles, price)
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:  # error de red: reintenta, no operes a ciegas
            print("error de red, reintento:", e)
        if a.once:
            if price is None:
                raise SystemExit("No pude obtener datos del exchange.")
            print(f"equity: {broker.equity(price):.2f}")
            break
        time.sleep(a.poll)


if __name__ == "__main__":
    main()
