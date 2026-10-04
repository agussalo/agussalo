# Trading algoritmico (cripto) — backtester

Framework minimo en Python para probar estrategias sobre datos historicos de
cualquier exchange soportado por [ccxt](https://github.com/ccxt/ccxt).

```bash
pip install -r requirements.txt
python run_backtest.py --strategy sma_cross --symbol BTC/USDT --days 365
python run_backtest.py --strategy rsi_reversion --synthetic   # sin internet
python run_backtest.py --synthetic --stop 0.03                # con stop-loss 3%
python run_backtest.py --synthetic --walk-forward --stop 0.03 # validacion fuera de muestra
python -m pytest tests                                        # tests del motor
```

- `backtester/data.py` — descarga OHLCV con cache en `data/` + datos sinteticos.
- `backtester/strategies.py` — estrategias (`df -> posicion 0/1`). Agrega las tuyas aca.
- `guia/GUIA.md` — **empezá acá**: guía didáctica con simulaciones (`guia/simulaciones.py`).
- `backtester/walk_forward.py` — optimiza en ventanas moviles y mide solo fuera de muestra.
- `backtester/engine.py` — motor vectorizado (+ `run_with_stop` con stop-loss): comisiones, slippage, ejecucion en la vela siguiente (sin look-ahead), Sharpe, drawdown.

## Advertencias
- Un buen backtest **no** garantiza ganancias: cuidado con overfitting, costos reales y cambios de regimen.
- Siguiente paso recomendado: validacion walk-forward, luego paper trading (testnet) antes de usar dinero real.
- Esto no es asesoramiento financiero.
