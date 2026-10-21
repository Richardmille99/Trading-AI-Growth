# Cómputo de IA: chips, foundry, equipos, redes y servidores · resumen (corte 19-oct-2026)

Investigación interna, no es consejo de inversión. Precios al cierre del 2026-10-16. Las cifras salen de los casos (`cases/<T>.json`) y de `rank.py`; cada dossier en `reports/<T>_swing.html` lleva sus fuentes.

## Ranking

| # | Ticker | Negocio | Convicción | Lectura |
|---|---|---|---|---|
| 1 | NVDA | 87.5 | Alta | +106%, centro de datos +117% y guía +12% secuencial; PER ≈ 14. |
| 2 | LITE | 82.7 | Alta | +109%, guía +24% y EP en agosto; dilución por canjes ya hecha. |
| 3 | TSM | 79.8 | Alta | +41% en US$, márgenes récord y guía +12–16% secuencial; PER ≈ 18. |
| 4 | CLS | 86.0 | Media | +62% y guía +8%, pero ampliación del 8% en agosto y directivos vendiendo. |
| 5 | AVGO | 86.0 | Media | IA +221%, guía +93% y cartera de $179.200M; −32% desde máximos. |
| 6 | ASML | 82.2 | Media | +55% en €, demanda por encima de la oferta hasta 2028 y recompras. |
| 7 | AMD | 79.6 | Media | Centro de datos +107% y guía +13%, pero beat pequeño y −7% tras resultados. |
| 8 | CIEN | 76.1 | Media | +37%, guía FY26 +35% y margen al alza; −46% desde máximos. |
| 9 | COHR | 70.8 | Media | +34% y guía +12% secuencial a PER ≈ 17; FCF negativo por el capex. |
| 10 | DELL | 69.6 | Media | Cartera de servidores de IA de $95.000M, guía +69% y EP; Silver Lake vendiendo. |
| 11 | ANET | 68.0 | Media | +38%, margen 45% y sin deuda; beat amplio y guía +9%. |
| 12 | AMAT | 67.3 | Media | Guía +12% secuencial y caja récord; −43% desde máximos. |
| 13 | SMCI | 66.2 | Media | +93% y guía FY27 de $65.000–72.000M a PER ≈ 6; ampliación de ≈ $5.000M. |
| 14 | ARM | 58.3 | Media | +22% y margen bruto del 97%, pero PER ≈ 77 y cartera plana. |
| 15 | KLAC | 56.4 | Media | Margen y caja de primera, pero guía menos explosiva que LRCX y −44% desde máximos. |
| 16 | LRCX | 68.5 | Descartar (resultados en ≤ 3 sesiones sin ser EP) | Guía +20% secuencial y EP en julio, ya devuelto (−38%). |

«Descartar» lleva entre paréntesis la regla de la matriz que lo dispara; con resultados en ≤ 3 sesiones es una regla de calendario, no un juicio del negocio.

## Calendario y plan EP

| Fecha | Ticker | Evento | EP A/B si… | D si… |
|---|---|---|---|---|
| 2026-10-21 [VERIFY] | LRCX | Resultados 1T FY27 tras el cierre | ingresos ≥ $8.500M (techo de la guía), margen bruto ≥ 52% y guía del 2T FY27 con otro crecimiento secuencial. | ingresos en el punto medio o por debajo con guía plana: el mercado ya descuenta el pico del ciclo de memoria. |
| 2026-10-26 [VERIFY] | CLS | Resultados 3T26 tras el cierre | ingresos ≥ $5.550M (techo de la guía), BPA ≥ $3,13 (+5% sobre el consenso de $2,98) y guía anual por encima de $20.500M. | ingresos dentro de la guía sin subirla: tras la ampliación, el mercado pediría más. |
| 2026-10-28 [VERIFY] | KLAC | Resultados 1T FY27 tras el cierre | ingresos ≥ $4.200M (techo de la guía), BPA ≥ $1,24 (+5% sobre el consenso de $1,18) y guía del 2T FY27 con más crecimiento secuencial. | ingresos en el punto medio y guía plana: seguiría por detrás de LRCX. |
| 2026-11-03 [VERIFY] | AMD | Resultados 3T26 tras el cierre | ingresos ≥ $13.300M (techo de la guía), centro de datos acelerando y guía del 4T por encima del consenso. | otro beat pequeño con guía plana. |
| 2026-11-03 [VERIFY] | ANET | Resultados 3T26 tras el cierre | ingresos ≥ $3.450M (+4,5% sobre la guía), BPA ≥ $1,13 (+5% sobre el consenso de $1,08) y guía del 4T con más crecimiento. | ingresos en la guía y margen a la baja. |
| 2026-11-04 [VERIFY] | ARM | Resultados 2T FY27 | BPA ≥ $0,49 (+5% sobre el consenso de $0,47) con royalties de centro de datos acelerando. | ingresos de licencias a la baja. |
| 2026-11-04 [VERIFY] | COHR | Resultados 1T FY27 tras el cierre | ingresos ≥ $2.400M (techo de la guía), margen bruto ≥ 41% y guía del 2T FY27 con más crecimiento. | margen bruto por debajo del 39,5%. |
| 2026-11-05 [VERIFY] | LITE | Resultados 1T FY27 tras el cierre | ingresos ≥ $1.300M (+4% sobre el punto medio de la guía), BPA ≥ $4,42 (+5% sobre el consenso de $4,21) y guía del 2T FY27 con más crecimiento. | ingresos en la guía con margen plano. |
| 2026-11-10 [VERIFY] | SMCI | Resultados 1T FY27 | ventas ≥ $15.500M (techo de la guía) y guía de FY27 mantenida o subida. | otro fallo en ventas o flujo operativo muy negativo. |
| 2026-11-12 [VERIFY] | AMAT | Resultados 4T FY26 tras el cierre | ingresos ≥ $10.750M (techo de la guía), BPA ≥ $4,26 (+5% sobre el consenso de $4,06) y guía del 1T FY27 con más crecimiento. | ingresos en el punto medio con guía plana. |
| 2026-11-25 [VERIFY] | NVDA | Resultados 3T FY27 | ingresos ≥ $110.200M (techo de la guía), BPA ≥ $2,59 (+5% sobre el consenso de $2,47) y guía del 4T con otro +10% secuencial. | ingresos en el punto medio con guía plana. |
| 2026-12-01 [VERIFY] | DELL | Resultados 3T FY27 | BPA ≥ $6,89 (+5% sobre el consenso de $6,56), cartera de servidores de IA por encima de $95.000M y otra subida de la guía. | cartera de IA a la baja. |
| 2026-12-02 [VERIFY] | AVGO | Resultados 4T FY26 | ingresos ≥ $36.000M (+3% sobre la guía), IA por encima de $21.700M y guía del 1T FY27 con más crecimiento de IA. | IA en la guía sin aceleración. |
| 2026-12-03 [VERIFY] | CIEN | Resultados 4T FY26 | ingresos ≥ $1.800M (techo de la guía) y guía de FY27 por encima del +25%. | guía de FY27 por debajo del +20%. |
| 2027-01-13 [VERIFY] | ASML | Resultados 4T26 | ventas ≥ €15.200M (techo de la guía), pedidos récord y guía de 2027 por encima del consenso. | pedidos a la baja o guía de 2027 plana. |
| 2027-01-14 [VERIFY] | TSM | Resultados 4T26 | ingresos ≥ $54.300M (techo de la guía), margen bruto ≥ 66% y guía del 1T27 sin la caída estacional. | margen bruto por debajo del 65%. |

## Líderes enfriados

Ninguno según `prices.py` (swing.md §5).

## Oferta y dilución a vigilar

- **NVDA:** Ventas de insiders 12 meses: $1.997,1M; 9 marcados.
- **LITE:** Canjes de convertibles por acciones (2026); Ventas de insiders 12 meses: $175,8M; 11 marcados.
- **CLS:** Ampliación de agosto de 2026 (9,68M acciones a $310); Ventas de insiders 12 meses: $252,7M; 7 marcados.
- **AVGO:** Ventas de insiders 12 meses: $1.174,2M; 7 marcados.
- **AMD:** Acciones para la compra de World Labs (≈ $8.200M); Ventas de insiders 12 meses: $368,7M; 4 marcados.
- **CIEN:** Convertible 0% 2031 ($2.875M, conversión ≈ $746,66); Ventas de insiders 12 meses: $99,0M; 6 marcados.
- **COHR:** Ventas de insiders 12 meses: $1.118,2M; 12 marcados.
- **DELL:** Ventas de Silver Lake (≥ 10%); Ventas de insiders 12 meses: $3.577,7M; 19 marcados.
- **ANET:** Ventas de insiders 12 meses: $1.511,1M; 3 marcados.
- **AMAT:** Ventas de insiders 12 meses: $180,6M; 9 marcados.
- **SMCI:** Ampliación de junio de 2026 (45,45M acciones a $27,50); Preferentes de conversión obligatoria Serie A 7% ($3.750M); Ventas de insiders 12 meses: $27,9M; 2 marcados.
- **ARM:** Ventas de insiders 12 meses: $72,2M; 7 marcados.
- **KLAC:** Ventas de insiders 12 meses: $112,3M; 7 marcados.
- **LRCX:** Ventas de insiders 12 meses: $170,1M; 8 marcados.

## Lo que sigue en [VERIFY]

- **NVDA:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; inventario y cobros en el 10-Q.
- **LITE:** convertibles que quedan vivos tras los canjes, en el 10-K FY26; fecha de finviz.
- **TSM:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; la nota no da capex ni flujos; están en el informe de gestión trimestral y en el 20-F.
- **CLS:** fecha de finviz.
- **AVGO:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **ASML:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **AMD:** fecha de finviz; número de acciones al cierre de la operación.
- **CIEN:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; vencimiento exacto y capped call.
- **COHR:** fecha de finviz.
- **DELL:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **ANET:** fecha de finviz.
- **AMAT:** fecha de finviz.
- **SMCI:** fecha de conversión obligatoria y tasas mínima y máxima en el 424B5; fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **ARM:** % de SoftBank en el 20-F; fecha de finviz.
- **KLAC:** fecha de finviz.
- **LRCX:** fecha de finviz.

## Método

- Universo creado el 19-oct-2026; Fase 1 con `new_case.py` y Fase 2 reproducible en `data/build_fase2.py` (consenso de finviz, KPIs y oferta de los filings citados en cada caso).
- Trimestres XBRL con el 4T derivado de la misma versión (arreglo de `xbrl.py` del 19-oct). Emisores extranjeros cargados a mano y descritos en el `financials_note` de su caso.
- Las sorpresas de BPA de finviz se descartan cuando el BPA está distorsionado (ganancias de participaciones, coberturas, cambios de criterio): se dice en la nota del catalizador.
