"""Logica del bot (independiente del broker y de la red, para poder testearla).

Misma regla que el backtest: la senal se calcula con la ultima vela CERRADA; se entra con stop-loss
y tamano por riesgo; tras un stop se espera a que la senal pase por 0 antes de reentrar.
"""
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class State:
    last_ts: str = ""
    entry: float = 0.0
    blocked: bool = False
    initialized: bool = False


class Bot:
    def __init__(self, broker, strategy, stop=0.03, risk=0.01, state_path="bot_state.json",
                 log_path="paper_trades.csv", log=print):
        self.broker, self.strategy, self.stop, self.risk = broker, strategy, stop, risk
        self.state_path, self.log_path, self.log = Path(state_path), Path(log_path), log
        self.st = State(**json.loads(self.state_path.read_text())) if self.state_path.exists() else State()

    def _save(self):
        self.state_path.write_text(json.dumps(asdict(self.st)))

    def _record(self, ts, kind, qty, px, equity):
        new = not self.log_path.exists()
        with self.log_path.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts", "evento", "cantidad", "precio", "equity"])
            w.writerow([ts, kind, f"{qty:.8f}", f"{px:.2f}", f"{equity:.2f}"])
        self.log(f"{ts} {kind:<10} qty={qty:.6f} px={px:.2f} equity={equity:.2f}")

    def step(self, candles, price):
        """candles: velas CERRADAS (DataFrame OHLCV). price: ultimo precio. Se llama cada pocos segundos."""
        ts = str(candles.index[-1])
        holding = self.broker.qty > 0

        # 1) stop-loss: se revisa en cada llamada, no solo al cerrar la vela
        if holding and price <= self.st.entry * (1 - self.stop):
            q, px = self.broker.sell_all(price)
            self.st.blocked = True
            self._record(ts, "STOP", q, px, self.broker.equity(px))
            self._save()
            return "stop"

        # 2) senal: solo cuando aparece una vela cerrada nueva
        if ts == self.st.last_ts:
            return None
        self.st.last_ts = ts
        want = float(self.strategy(candles).iloc[-1])
        action = None
        if not self.st.initialized:  # al arrancar: si ya estaba "dentro" no entro a mitad de tendencia
            self.st.initialized, self.st.blocked = True, want == 1
        if want == 0:
            self.st.blocked = False
            if holding:
                q, px = self.broker.sell_all(price)
                self._record(ts, "VENTA", q, px, self.broker.equity(px))
                action = "venta"
        elif not holding and not self.st.blocked:
            f = min(1.0, self.risk / self.stop)
            q, px = self.broker.buy_value(self.broker.equity(price) * f, price)
            self.st.entry = px
            self._record(ts, "COMPRA", q, px, self.broker.equity(px))
            action = "compra"
        self._save()
        return action
