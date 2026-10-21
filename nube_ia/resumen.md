# Nube de IA: hiperescalares y neoclouds · resumen (corte 19-oct-2026)

Investigación interna, no es consejo de inversión. Precios al cierre del 2026-10-16. Las cifras salen de los casos (`cases/<T>.json`) y de `rank.py`; cada dossier en `reports/<T>_swing.html` lleva sus fuentes.

## Ranking

| # | Ticker | Negocio | Convicción | Lectura |
|---|---|---|---|---|
| 1 | NBIS | 69.5 | Media | +454%, EBITDA positivo y EP del +34%; ATM, convertibles y warrants de NVIDIA. |
| 2 | CRWV | 62.8 | Media | +112% y cartera de $104.000M, pero insiders vendiendo $5.800M, convertible y ATM. |
| 3 | APLD | 69.0 | Baja | +322% con contratos a 15 años; cuentas en transición y pérdidas. |
| 4 | GOOGL | 58.2 | Baja | Cloud +82% y cartera de $519.500M, pero emite acciones: ampliación de $49.600M y ATM de $40.000M. |
| 5 | AMZN | 54.4 | Baja | AWS +37% (máximo en 18 trimestres) y EP en julio; FCF negativo por el capex. |
| 6 | META | 60.1 | Descartar (resultados en ≤ 3 sesiones sin ser EP) | Ingresos +28%, pero FCF casi nulo por el capex y fallo de BPA. |
| 7 | IREN | 39.0 | Descartar (catalizador D con fundamentales < 40) | $4.000M de ARR contratado, pero ingresos a la baja, pérdidas y deuda. |

«Descartar» lleva entre paréntesis la regla de la matriz que lo dispara; con resultados en ≤ 3 sesiones es una regla de calendario, no un juicio del negocio.

## Calendario y plan EP

| Fecha | Ticker | Evento | EP A/B si… | D si… |
|---|---|---|---|---|
| 2026-10-21 [VERIFY] | META | Resultados 3T26 tras el cierre | ingresos ≥ $64.000M (techo de la guía), BPA ≥ $6,93 (+5% sobre el consenso de $6,60 de finviz) y capex sin subir la guía. | otra subida de la guía de capex o gastos sin aceleración de ingresos: el mercado seguiría castigando el gasto. |
| 2026-10-28 [VERIFY] | GOOGL | Resultados 3T26 tras el cierre | Cloud acelera por encima del +82% y el BPA ajustado sin ganancias de participaciones supera el consenso de $3,02 de finviz en ≥ 5%. | ventas del ATM grandes en el 3T con capex al alza: dilución sin aceleración. |
| 2026-10-29 [VERIFY] | AMZN | Resultados 3T26 tras el cierre | AWS ≥ +37% (sin desacelerar), beneficio operativo por encima de $26.500M (techo de la guía) y BPA ≥ +5% sobre el consenso de $1,96 sin la partida de Anthropic. | AWS desacelera con más capex. |
| 2026-11-10 [VERIFY] | CRWV | Resultados 3T26 | ingresos y cartera por encima de lo esperado con margen operativo positivo y sin ventas grandes del ATM en el trimestre. | pérdidas crecientes con más dilución. |
| 2026-11-11 [VERIFY] | NBIS | Resultados 3T26 | ingresos por encima de $800M con EBITDA ajustado al alza y sin ventas grandes del ATM en el trimestre. | más dilución con el crecimiento desacelerando. |
| 2026-11-26 [VERIFY] | IREN | Resultados 1T FY27 | ingresos de nube de IA visibles en el trimestre y ARR operativo por encima de $1.000M. | retrasos en la puesta en marcha de capacidad. |
| 2027-01-06 [VERIFY] | APLD | Resultados 2T FY27 | EBITDA ajustado al alza con capacidad nueva en servicio y otro contrato de hiperescalar. | retrasos en Polaris Forge o Delta Forge. |

## Líderes enfriados

Ninguno según `prices.py` (swing.md §5).

## Oferta y dilución a vigilar

- **NBIS:** Programa de venta de hasta 25M acciones Clase A (nov-2025); Convertibles de marzo-2026: $2.590M al 1,25% 2031 ($183,22) y $1.750M al 2,625% 2033 ($180,31); Warrants prefinanciados de NVIDIA (21,07M acciones, mar-2026).
- **CRWV:** Convertible 2,875% 2033 ($4.200M, conversión ≈ $97,85); Programa de venta de acciones Clase A con ventas a plazo (sep-2026); Ventas de insiders 12 meses: $5.809,0M; 12 marcados.
- **APLD:** Ventas de insiders 12 meses: $25,0M; 7 marcados.
- **GOOGL:** Ampliación de junio de 2026 (acciones A/C y preferentes obligatorias, $49.600M netos); Programa de venta en mercado (ATM) de hasta $40.000M en acciones A y C; Ventas de insiders 12 meses: $182,4M; 5 marcados.
- **AMZN:** Compra de Globalstar con acciones o efectivo a elección; Ventas de insiders 12 meses: $456,9M; 4 marcados.
- **META:** Shelf automático S-3ASR (30-abr-2026), usado para bonos; Ventas de insiders 12 meses: $243,1M; 10 marcados.
- **IREN:** Convertible 1% 2033 ($3.000M, conversión ≈ $73,07); Reventa de acciones por accionistas (424B7, ago-2026); Ventas de insiders 12 meses: $0,4M; 1 marcados.

## Lo que sigue en [VERIFY]

- **NBIS:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; fechas exactas de vencimiento; hora exacta; importes en los 6-K de los anuncios.
- **CRWV:** fecha exacta de vencimiento; fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; importe máximo del programa y lo vendido; capacidad puesta a 0 hasta confirmarla.
- **APLD:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **GOOGL:** fecha de finviz; importe vendido; lo dirá el 10-Q del 3T26; reparto entre acciones ordinarias y preferentes, y precio de conversión de las series A y B, en el 8-K del 5-jun y sus 424B.
- **AMZN:** fecha de finviz; importe y acciones máximas a emitir en el 424B3.
- **META:** cargo fiscal en el 10-Q del 3T25; fecha de finviz.
- **IREN:** fecha exacta de vencimiento; fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; número de acciones y origen en el 424B7.

## Método

- Universo creado el 19-oct-2026; Fase 1 con `new_case.py` y Fase 2 reproducible en `data/build_fase2.py` (consenso de finviz, KPIs y oferta de los filings citados en cada caso).
- Trimestres XBRL con el 4T derivado de la misma versión (arreglo de `xbrl.py` del 19-oct). Emisores extranjeros cargados a mano y descritos en el `financials_note` de su caso.
- Las sorpresas de BPA de finviz se descartan cuando el BPA está distorsionado (ganancias de participaciones, coberturas, cambios de criterio): se dice en la nota del catalizador.
