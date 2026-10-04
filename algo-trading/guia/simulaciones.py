"""Simulaciones didacticas. Correr: python guia/simulaciones.py [1|2|3|4]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backtester import data, engine
from backtester.strategies import sma_cross

rng = np.random.default_rng(7)


def sim1_esperanza():
    """Porcentaje de aciertos NO es lo que importa: importa ganar_prom*p - perder_prom*(1-p)."""
    print("\n== 1. Acertar mucho vs. tener esperanza positiva (1000 operaciones, riesgo 1R) ==")
    for nombre, p, gana, pierde in [("A: acierta 60%, gana 1R / pierde 2R", .60, 1, 2),
                                    ("B: acierta 40%, gana 3R / pierde 1R", .40, 3, 1)]:
        esp = p * gana - (1 - p) * pierde
        res = np.where(rng.random(1000) < p, gana, -pierde).sum()
        print(f"{nombre}\n   esperanza por operacion: {esp:+.2f}R   resultado simulado: {res:+.0f}R")


def sim2_tamano():
    """Misma ventaja (50% de aciertos, gana 2R / pierde 1R), distinto % de capital arriesgado."""
    print("\n== 2. Tamano de posicion: misma estrategia, distinto riesgo por operacion ==")
    print("   (ventaja real: +0.5R por operacion; 100 operaciones; 2000 corridas)")
    for r in (0.01, 0.05, 0.20, 0.50):
        finales, peores, quiebras = [], [], 0
        for _ in range(2000):
            win = rng.random(100) < 0.5
            eq = np.cumprod(np.where(win, 1 + 2 * r, 1 - r))
            finales.append(eq[-1])
            peores.append((eq / np.maximum.accumulate(eq)).min() - 1)
            quiebras += eq.min() < 0.2  # perdio mas del 80%
        print(f"   riesgo {r:>4.0%}/op | capital final mediano x{np.median(finales):>10.2f} "
              f"| caida maxima tipica {np.median(peores):>6.0%} | perdio >80%: {quiebras/20:>5.1f}% de las corridas")


def sim3_overfitting():
    """Precio SIN ventaja (camino aleatorio). Optimizamos el cruce de medias en la 1a mitad."""
    print("\n== 3. Overfitting: optimizar sobre ruido puro ==")
    ins, outs = [], []
    for seed in range(40):
        df = data.synthetic_ohlcv(n=6000, seed=100 + seed)
        # precio aleatorio sin tendencia: anulamos la deriva sinusoidal reconstruyendo con retornos mezclados
        ret = df["close"].pct_change().dropna().to_numpy()
        ret = rng.permutation(ret)
        df["close"] = 30000 * np.r_[1, np.cumprod(1 + ret)]
        a, b = df.iloc[:3000], df.iloc[3000:]
        mejor, mejor_s = None, -9
        for f in range(5, 60, 5):
            for s in range(20, 200, 20):
                if f >= s:
                    continue
                sh = engine.run(a, sma_cross(a, f, s)).stats["sharpe"]
                if sh > mejor_s:
                    mejor, mejor_s = (f, s), sh
        sh_out = engine.run(b, sma_cross(b, *mejor)).stats["sharpe"]
        ins.append(mejor_s); outs.append(sh_out)
        if seed < 5:
            print(f"   mercado {seed}: mejores parametros {mejor} | Sharpe en datos usados {mejor_s:+.2f} "
                  f"| Sharpe en datos NUEVOS {sh_out:+.2f}")
    print(f"   ... (40 mercados sin ninguna ventaja real)")
    print(f"   Sharpe promedio con los datos usados para optimizar: {np.mean(ins):+.2f}")
    print(f"   Sharpe promedio en datos nuevos:                     {np.mean(outs):+.2f}  <- la ventaja optimizada era un espejismo")


def sim4_costos():
    print("\n== 4. Costos: la misma estrategia con distintas comisiones+slippage ==")
    df = data.synthetic_ohlcv(n=8760, seed=42)
    pos = sma_cross(df, 5, 15)  # cruce rapido = opera mucho
    for fee, slip in [(0, 0), (0.0005, 0.0002), (0.001, 0.0005), (0.002, 0.001)]:
        st = engine.run(df, pos, fee, slip).stats
        print(f"   costo por lado {fee+slip:>6.2%} | retorno {st['retorno_total']:>8.1%} "
              f"| operaciones {st['operaciones']}")


if __name__ == "__main__":
    todas = {"1": sim1_esperanza, "2": sim2_tamano, "3": sim3_overfitting, "4": sim4_costos}
    for k in (sys.argv[1:] or todas):
        todas[k]()
