# Capa de swing: régimen, setups, convicción y diario

La entrada la da el precio. Esta skill decide **convicción, tamaño y horizonte** con lo que hay detrás del movimiento. Es un marco mecánico de investigación, no una recomendación.

## 1. Régimen de mercado (`case.json → market_regime`)

`risk_on` / `neutral` / `risk_off`, con la evidencia: ratio de Stockbee (nº de acciones +4% ÷ −4% en 5 y 10 días), % sobre la media de 20 y 50 sesiones, T2108, tendencia del Nasdaq y del Russell 2000 frente a sus medias de 10/20/50. Sin datos de mercado se deja `unknown` y la convicción máxima baja un escalón.

**Cálculo mecánico** (`scripts/prices.py` → `regime_proxy`, con la amplitud de `scripts/market.py`):

1. **Tendencia.** QQQ e IWM con cierre > EMA 20 > EMA 50 → `risk_on`; los dos bajo su EMA 50 → `risk_off`; el resto → `neutral`.
2. **Amplitud** sobre el Nasdaq-100 (`market/members.json`, lista aproximada), misma sesión que los índices:
   - `strong`: ≥ 60% sobre la SMA 50 y ratio +4%/−4% de 10 sesiones ≥ 1,5.
   - `weak`: < 40% sobre la SMA 50, o ratio de 10 sesiones < 0,67.
   - El ratio solo cuenta con al menos 3 movimientos de ±4% en las 10 sesiones; con menos, decide el % sobre la SMA 50.
   - `mixed`: el resto.
3. **Ajuste de un escalón:** `risk_on` con amplitud `weak` → `neutral`; `risk_off` con amplitud `strong` → `neutral`; `neutral` con amplitud `weak` y < 30% sobre la SMA 50 → `risk_off`. Sin `breadth.json` de la misma sesión se usa solo la tendencia y la evidencia lo dice.

T2108 (% sobre la media de 40 sesiones de todo el mercado) no se calcula: el Nasdaq-100 es una muestra de grandes compañías y la amplitud de small caps puede ir por otro lado.

## 2. Setups (`case.json → setup.type`)

| `type` | Escuela | Definición operativa |
|---|---|---|
| `ep` | Qullamaggie / Stockbee | Gap ≥ 10% con volumen ≥ 3–5× la media (Stockbee 9M EP: ≥ 9M acciones) sobre un catalizador fundamental, idealmente en una acción olvidada |
| `breakout_flag` | Qullamaggie | Subida previa ≥ 30–100% y consolidación de 2–8 semanas con rango que se estrecha y medias de 10/20 subiendo |
| `vcp` | Minervini | Contracciones sucesivas de volatilidad con volumen decreciente |
| `momentum_burst` | Stockbee | +4% con volumen mayor que el día anterior tras una fase de rango |
| `wedge_pop` | Oliver Kell | Ruptura de una cuña bajista recuperando las EMAs de 10/20 |
| `ema_crossback` | Oliver Kell | Retroceso a la EMA de 10/20 en tendencia y rebote |
| `base_n_break` | Oliver Kell | Ruptura de una base tras el primer impulso |
| `exhaustion_watch` | Oliver Kell | Extensión parabólica: vigilar, no entrar |

Campos: `type`, `pivot`, `stop` (mínimo del día de entrada o de la base), `adr_pct` (rango medio diario 20 sesiones), `rs_1m`, `rs_3m`, `rs_6m` (percentil de rentabilidad en el universo), `ema_stack` (10>20>50), `notes`. Sin datos de precio estos campos quedan `null` y el informe lo muestra.

## 3. Matriz de convicción (`scripts/compute.py`)

Entradas: nota del catalizador principal (A–D), nota de fundamentales (0–100), nota de oferta (0–100), posición en el grupo (`leader` / `strong` / `neutral` / `weak` / `unknown`), régimen y eventos en la ventana.

1. **Descartar** si: oferta < 35; o catalizador D con fundamentales < 40; o resultados en ≤ 3 sesiones para un setup que no sea `ep`.
2. **Alta** si: catalizador A o B, fundamentales ≥ 65, oferta ≥ 60, grupo `leader` o `strong`.
3. **Media** si: catalizador ≥ C, fundamentales ≥ 45 y oferta ≥ 50.
4. **Baja** en el resto.
5. Régimen `risk_off` → máximo Baja. Régimen `unknown` o grupo `unknown` → baja un escalón desde Alta.

| Convicción | Tamaño (múltiplo del riesgo base) | Horizonte orientativo |
|---|---|---|
| Alta | 1,0 R | Semanas; parciales a los 3–5 días y resto con la EMA de 10/20 |
| Media | 0,5 R | 3–10 sesiones; parciales a los 3–5 días |
| Baja | 0,25 R | Táctico, 1–3 sesiones, o pasar |
| Descartar | 0 | — |

Riesgo por acción = pivote − stop; también en ADRs ((pivote − stop) ÷ (ADR% × pivote)). Más de 1 ADR de riesgo se marca.

## 4. Eventos en la ventana

Resultados, fin de lock-up, vencimiento de una oferta o warrant, junta, decisión regulatoria (PDUFA), rebalanceo de índices. Cada uno con fecha y efecto esperado; los que caen en las próximas 6–8 semanas se destacan.

## 5. Diario de calibración (`assets/journal_template.csv`)

Una fila por señal: fecha, ticker, setup, catalizador y nota, nota de fundamentales, nota de oferta, convicción, pivote, stop, y resultado a +5, +20 y +60 sesiones (máximo favorable, máximo adverso y cierre, en R). Cada trimestre se compara el rendimiento por nota: si A no supera a C, se recalibran los pesos. Sin este registro las notas son opinión.

## 6. Etiqueta «líder enfriado» (`setup.cooled_leader`)

No es un setup de entrada: marca candidatos a vigilar para un EP en resultados o una base nueva. Se cumple cuando, a la vez:
- rentabilidad de 12 meses por encima de la mediana del universo analizado;
- RS 1m y RS 3m < 50 (percentil dentro del universo + ETF del sector);
- caída desde el máximo de 52 semanas entre 20% y 50%;
- precio a ≤ 10% de la media de 200 sesiones, o por encima;
- fundamentales intactos: aceleración del último trimestre ≥ −3 pp y nota de fundamentales ≥ 45.

Si se cumple todo menos lo último, es `cooled_leader_broken` (enfriado por motivo fundamental): no se trata como oportunidad.
