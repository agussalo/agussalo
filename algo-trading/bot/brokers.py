"""Brokers: SimBroker (cuenta simulada local) y TestnetBroker (testnet de Binance via ccxt).

Ninguno opera con dinero real: TestnetBroker se niega a arrancar si el exchange no esta en modo sandbox.
"""
import json
import os
from pathlib import Path


class SimBroker:
    """Cuenta simulada: usa precios reales (datos publicos) pero las ordenes son ficticias."""

    def __init__(self, capital=10_000.0, fee=0.001, slippage=0.0005, path="paper_state.json"):
        self.fee, self.slippage, self.path = fee, slippage, Path(path)
        self.cash, self.qty = capital, 0.0
        if self.path.exists():
            d = json.loads(self.path.read_text())
            self.cash, self.qty = d["cash"], d["qty"]

    def save(self):
        self.path.write_text(json.dumps({"cash": self.cash, "qty": self.qty}))

    def equity(self, price):
        return self.cash + self.qty * price

    def buy_value(self, value, price):
        px = price * (1 + self.slippage)
        value = min(value, self.cash / (1 + self.fee))
        qty = value / px
        self.cash -= value * (1 + self.fee)
        self.qty += qty
        self.save()
        return qty, px

    def sell_all(self, price):
        px = price * (1 - self.slippage)
        qty = self.qty
        self.cash += qty * px * (1 - self.fee)
        self.qty = 0.0
        self.save()
        return qty, px


class TestnetBroker:
    """Ordenes de mercado reales pero en el TESTNET de Binance (dinero ficticio). Requiere claves de testnet."""

    def __init__(self, symbol, exchange="binance"):
        import ccxt

        key, secret = os.environ.get("TESTNET_API_KEY"), os.environ.get("TESTNET_API_SECRET")
        if not key or not secret:
            raise SystemExit("Faltan TESTNET_API_KEY / TESTNET_API_SECRET (claves del TESTNET, no de tu cuenta real).")
        self.ex = getattr(ccxt, exchange)({"apiKey": key, "secret": secret, "enableRateLimit": True})
        self.ex.set_sandbox_mode(True)
        if not self.ex.urls.get("test") or "test" not in str(self.ex.urls["api"]):
            raise SystemExit("El exchange no quedo en modo sandbox: me niego a operar.")
        self.symbol = symbol
        self.base, self.quote = symbol.split("/")
        self.ex.load_markets()

    def _bal(self, cur):
        return float(self.ex.fetch_balance()["total"].get(cur, 0.0))

    @property
    def qty(self):
        return self._bal(self.base)

    def equity(self, price):
        return self._bal(self.quote) + self.qty * price

    def buy_value(self, value, price):
        amount = float(self.ex.amount_to_precision(self.symbol, value / price))
        o = self.ex.create_order(self.symbol, "market", "buy", amount)
        return amount, float(o.get("average") or price)

    def sell_all(self, price):
        amount = float(self.ex.amount_to_precision(self.symbol, self.qty))
        o = self.ex.create_order(self.symbol, "market", "sell", amount)
        return amount, float(o.get("average") or price)
