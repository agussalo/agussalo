# Guía: entender el trading algorítmico antes de automatizar

> Nada de esto es asesoramiento financiero. **Ningún sistema "nunca se equivoca".**
> El objetivo realista es: *ganar más de lo que perdés, en promedio, sobreviviendo a las rachas malas.*

Cada sección tiene una simulación que podés correr: `python guia/simulaciones.py 1` (o 2, 3, 4; sin número corre todas, y así coinciden los números de abajo). No necesita internet.

## 1. Acertar mucho no alcanza: la esperanza matemática
Lo que importa es `p·ganancia_prom − (1−p)·pérdida_prom`, medido en **R** (la unidad que arriesgás por operación).

| Estrategia | Aciertos | Gana / Pierde | Esperanza | 1000 ops simuladas |
|---|---|---|---|---|
| A | 60% | 1R / 2R | −0,20R | **−188R** |
| B | 40% | 3R / 1R | +0,60R | **+616R** |

La B se equivoca más veces y gana. La A acierta seguido y pierde. *Mirá siempre la esperanza, no el % de aciertos.*

## 2. Tamaño de posición: lo que decide si sobrevivís
Misma estrategia (50% de aciertos, gana 2R / pierde 1R: ventaja real y positiva), 100 operaciones, 2000 corridas:

| Riesgo por operación | Capital final (mediana) | Caída máxima típica | Corridas que perdieron >80% |
|---|---|---|---|
| 1% | ×1,6 | −6% | 0% |
| 5% | ×9 | −28% | 0% |
| 20% | ×289 | −81% | 8% |
| 50% | ×1 | −100% | 76% |

Con una ventaja real, arriesgar demasiado igual te funde. **Regla común: 0,5%–2% del capital por operación.**
(Ojo: los ×289 no son realistas: suponen ventaja perfecta y sin costos.)

## 3. Overfitting: optimizar sobre el pasado engaña
Probamos muchas combinaciones de medias móviles sobre precios **sin ninguna ventaja real** y elegimos la mejor:

- Sharpe promedio en los datos usados para optimizar: **+1,72** (parece genial)
- Sharpe promedio en datos nuevos: **−0,04** (nada: era un espejismo)

Moraleja: probar 1000 variantes y quedarte con la mejor encuentra suerte, no ventaja. Defensas: datos de prueba separados, *walk-forward*, pocas variables, y que la lógica tenga sentido económico.

## 4. Los costos se comen la ventaja
Misma estrategia rápida (643 operaciones):

| Costo por lado (comisión + slippage) | Retorno |
|---|---|
| 0% | +64% |
| 0,07% | +5% |
| 0,15% | −37% |
| 0,30% | −76% |

Operar mucho exige una ventaja grande por operación. Binance spot cobra ~0,1% por lado sin descuentos.

## 5. Vocabulario mínimo
- **Orden de mercado / límite / stop:** comprar ya al precio disponible / a un precio que fijás / cerrar automáticamente si va mal.
- **Apalancamiento:** operar con plata prestada. Multiplica ganancias *y* pérdidas; es lo que más cuentas liquida. Empezá sin él.
- **Drawdown:** caída desde el máximo de tu capital. Pensá cuánto aguantás emocionalmente.
- **Sharpe:** retorno por unidad de riesgo. Más de ~1 sostenido y con costos reales ya es bueno; si ves 5, sospechá un error.
- **Look-ahead bias:** usar información del futuro sin querer. El motor del repo ejecuta en la vela siguiente para evitarlo.
- **Walk-forward:** optimizar en una ventana, probar en la siguiente, y repetir rodando.

## 6. Stop-loss y walk-forward en el backtester

**Stop-loss** (`--stop 0.05` cierra si el precio cae 5% desde la entrada). Sobre el mismo mercado simulado, cruce de medias:

| Stop | Retorno | Stops activados |
|---|---|---|
| sin stop | +53,6% | 0 |
| 1% | −29,8% | 53 |
| 2% | +1,0% | 26 |
| 5% | +52,0% | 1 |

Un stop **no es gratis**: si es muy ajustado, el ruido normal del precio te saca de operaciones buenas una y otra vez. Hay que elegirlo según la volatilidad del activo, y medirlo en el backtest como cualquier otro parámetro.

**Walk-forward** (`--walk-forward`): optimiza en 2000 velas, opera las 500 siguientes que el sistema nunca vio, y repite rodando la ventana. Solo se reporta el resultado fuera de muestra:

```bash
python run_backtest.py --synthetic --walk-forward --stop 0.05                    # cruce de medias
python run_backtest.py --synthetic --walk-forward --strategy rsi_reversion       # RSI
```

Resultado en el mercado simulado: el cruce de medias dio +121,6% fuera de muestra (Sharpe 5,5) y el RSI −39,6% (comprar y mantener: −5,7%). Ojo con el primero: **los datos sintéticos tienen una tendencia cíclica incorporada**, por eso una estrategia de tendencia funciona tan bien. En precios reales un Sharpe así sería sospechoso. Lo que sí enseña el ejemplo: el walk-forward descarta sin piedad a la estrategia que no tiene ventaja.

## 7. Ruta recomendada
1. Correr y modificar las simulaciones hasta que te cierren. 
2. Backtest de las estrategias del repo con datos reales (`run_backtest.py`).
3. Probar stop-loss y walk-forward con datos reales (`--stop`, `--walk-forward`). Pendiente en el repo: tamaño de posición por riesgo.
4. Paper trading en el testnet durante semanas/meses.
5. Dinero real solo si el paper trading coincide con el backtest, con un monto que puedas perder entero.

## Señales de alarma
Promesas de "cero pérdidas", rendimientos fijos garantizados, "bots milagro" pagos, o pedirte que deposites en una plataforma que no conocés.
