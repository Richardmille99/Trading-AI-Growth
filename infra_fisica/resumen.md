# Infraestructura física de la IA: electricidad, refrigeración, construcción y generación · resumen (corte 19-oct-2026)

Investigación interna, no es consejo de inversión. Precios al cierre del 2026-10-16. Las cifras salen de los casos (`cases/<T>.json`) y de `rank.py`; cada dossier en `reports/<T>_swing.html` lleva sus fuentes.

## Régimen

Proxy de tendencia (2026-10-16): QQQ 709.80 vs EMA 10/20/50 735.21/736.16/727.94; IWM 270.44 vs EMA 10/20/50 276.03/279.24/285.00 → risk_off. Amplitud Nasdaq-100 (lista aproximada) (2026-10-16, 98 valores): 45% sobre la SMA 50, 57% sobre la SMA 20; +4%/−4% en 5 sesiones 24/41, en 10 sesiones 44/53 → mixed. → **risk_off**: la matriz limita la convicción a Baja.

## Ranking

| # | Ticker | Negocio | Convicción | Lectura |
|---|---|---|---|---|
| 1 | PWR | 86.2 | Baja | +41%, cartera récord de $53.400M y EP en julio: el líder del universo. |
| 2 | NVT | 75.2 | Baja | +53% (+47% orgánico) y guía subida; líder enfriado con PER ≈ 21. |
| 3 | GEV | 67.6 | Baja | Pedidos +88% y cartera de $176.000M, pero fallo de BPA y la valoración más alta. |
| 4 | ETN | 64.1 | Baja | Orgánico +14%, pedidos eléctricos +41% y guía subida; deuda casi doble. |
| 5 | MOD | 61.9 | Baja | Centros de datos +90% y separación completada; margen a la baja. |
| 6 | VRT | 59.3 | Baja | Guía subida y caja récord, pero fallo en ventas y desaceleración: −46% desde máximos. |
| 7 | VST | 53.1 | Baja | EBITDA ajustado +31%, guía reafirmada; centros de datos aún sin cifras. |
| 8 | POWL | 46.5 | Baja | Pedidos récord (book-to-bill 3,0) y cartera +69%; ingresos aún +9%. |
| 9 | FIX | 76.9 | Descartar (resultados en ≤ 3 sesiones sin ser EP) | Cartera +73% y BPA +92%, pero el mercado lo vende: −31% desde máximos antes de resultados. |
| 10 | CEG | 43.5 | Descartar (catalizador D con fundamentales < 40) | Guía subida y 920 MW contratados a 15–20 años; secundaria de Calpine encima. |

«Descartar» lleva entre paréntesis la regla de la matriz que lo dispara; con resultados en ≤ 3 sesiones es una regla de calendario, no un juicio del negocio.

## Calendario y plan EP

| Fecha | Ticker | Evento | EP A/B si… | D si… |
|---|---|---|---|---|
| 2026-10-22 [VERIFY] | FIX | Resultados 3T26 tras el cierre | BPA ≥ $14,10 (+10% sobre el consenso de $12,85 de finviz), cartera ≥ $15.000M (book-to-bill > 1,2) y margen bruto ≥ 25%, con hueco y volumen. | cartera plana o a la baja frente a los $14.060M de junio: el mercado ya descuenta que la contratación de centros de datos ha tocado techo. |
| 2026-10-28 [VERIFY] | GEV | Resultados 3T26 antes de la apertura | BPA ≥ $4,19 (+5% sobre el consenso de $3,99 de finviz), pedidos ≥ $20.000M y guía de FCF mantenida o subida. | segundo fallo de BPA con pedidos a la baja: el mercado dejaría de pagar la cartera. |
| 2026-10-28 [VERIFY] | MOD | Resultados 2T FY27 (primeros sin Performance Technologies) | centros de datos ≥ +90% con el margen recuperándose por encima del 22% y guía nueva para la Modine separada. | margen de centros de datos por debajo del 20%. |
| 2026-10-28 [VERIFY] | VRT | Resultados 3T26 antes de la apertura | BPA ≥ $1,91 (+5% sobre el consenso de $1,82 de finviz), ventas sin fallo frente al consenso y guía anual de ventas por encima de $14.000M. | segundo fallo seguido en ventas o guía anual mantenida: confirmaría la desaceleración. |
| 2026-10-29 [VERIFY] | PWR | Resultados 3T26 antes de la apertura | BPA ≥ $5,20 (+5% sobre el consenso de $4,95 de finviz), cartera por encima de $53.400M y otra subida de la guía. | cartera plana: el crecimiento dependería solo de las compras. |
| 2026-10-30 [VERIFY] | ETN | Resultados 3T26 | orgánico por encima del 15,5% (techo de la guía), BPA ajustado ≥ $3,72 (+5% sobre el consenso de $3,54) y otra subida de la guía anual. | pedidos eléctricos desacelerando. |
| 2026-10-30 [VERIFY] | NVT | Resultados 3T26 antes de la apertura | BPA ≥ $1,46 (+5% sobre el consenso de $1,39 de finviz), orgánico ≥ +30% y otra subida de la guía. | orgánico por debajo del +30% con la guía mantenida. |
| 2026-11-02 [VERIFY] | POWL | Resultados 4T FY26 | ingresos acelerando por encima del +15% con la cartera por encima de $2.400M. | ingresos planos otra vez: la cartera tardaría en llegar. |
| 2026-11-05 [VERIFY] | CEG | Resultados 3T26 | BPA ≥ $3,91 (+5% sobre el consenso de $3,72), otra subida de la guía y contratos nuevos con hiperescalares con cifras. | guía mantenida y otra secundaria. |
| 2026-11-06 [VERIFY] | VST | Resultados 3T26 antes de la apertura | subida de la guía de EBITDA ajustado por encima de $7.600M o un contrato de suministro con un hiperescalar con cifras. | guía mantenida sin novedades de centros de datos. |

## Líderes enfriados

NVT

## Oferta y dilución a vigilar

- **PWR:** Ventas de insiders 12 meses: $137,5M; 6 marcados.
- **NVT:** Folleto para ventas de accionistas existentes (sep-2026); Ventas de insiders 12 meses: $61,8M; 11 marcados.
- **GEV:** Shelf automático S-3ASR (29-ene-2026), usado para bonos; Ventas de insiders 12 meses: $11,5M; 3 marcados.
- **ETN:** Bonos de marzo de 2026 bajo el shelf (cuatro 424B5); Ventas de insiders 12 meses: $22,6M; 7 marcados.
- **MOD:** Ventas de insiders 12 meses: $40,4M; 7 marcados.
- **VRT:** Shelf automático S-3ASR (19-feb-2026), usado para bonos; Ventas de insiders 12 meses: $128,2M; 7 marcados.
- **VST:** Shelf automático S-3ASR (9-sep-2026), usado para bonos subordinados; Ventas de insiders 12 meses: $86,3M; 6 marcados.
- **POWL:** Ventas de insiders 12 meses: $69,3M; 9 marcados.
- **FIX:** Ventas de insiders 12 meses: $185,2M; 12 marcados.
- **CEG:** Secundaria de 11,0M acciones de los vendedores de Calpine (jun-2026).

## Lo que sigue en [VERIFY]

- **PWR:** fecha de finviz.
- **NVT:** fecha de finviz; si hay accionistas nombrados y cuántas acciones.
- **GEV:** fecha de finviz; origen en el 10-K 2025.
- **ETN:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días; uso de los fondos (compra) en el 424B5.
- **MOD:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **VRT:** cartera y book-to-bill en la presentación del 2T26; fecha de finviz.
- **VST:** fecha de finviz.
- **POWL:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.
- **FIX:** fecha de finviz; la compañía aún no la ha anunciado (el 3T25 fue el 23-oct-2025); fecha no confirmada por la compañía.
- **CEG:** fecha no anunciada; fecha no anunciada; estimada como últimos resultados + 91 días.

## Método

- Universo creado el 19-oct-2026; Fase 1 con `new_case.py` y Fase 2 reproducible en `data/build_fase2.py` (consenso de finviz, KPIs y oferta de los filings citados en cada caso).
- Trimestres XBRL con el 4T derivado de la misma versión (arreglo de `xbrl.py` del 19-oct). Emisores extranjeros cargados a mano y descritos en el `financials_note` de su caso.
- Las sorpresas de BPA de finviz se descartan cuando el BPA está distorsionado (ganancias de participaciones, coberturas, cambios de criterio): se dice en la nota del catalizador.
