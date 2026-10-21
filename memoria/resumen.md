# Memoria: DRAM, HBM, NAND y módulos · resumen (corte 18-oct-2026, revisado el 19-oct)

Investigación interna, no es consejo de inversión. Precios al cierre del 16-oct-2026. El 19-oct se revisaron los [VERIFY] contra los filings y fuentes externas (ver «Método»). Las cifras salen de los casos (`cases/<T>.json`) y de `rank.py`; cada dossier en `reports/<T>_swing.html` lleva sus fuentes.

## Lo primero: convicción y ciclo

**MU y SNDK salen «Alta»** (catalizador A, fundamentales 100, oferta 90, grupo líder/fuerte) y los otros cuatro, «Media».

Lo segundo es el ciclo. Los cuatro fabricantes y diseñadores crecen entre el +127% y el +379% interanual, con márgenes brutos de pico (85–87% en MU y SNDK). Aun así, el mercado ya vende el pico: todo el universo está entre un 30% y un 50% por debajo de su máximo de 52 semanas, y SMH, un 20%. Las notas de fundamentales salen al máximo porque miden el trimestre, no la duración del ciclo; para eso están los KPIs de precio por bit e inventario de cada caso.

## Ranking

| # | Ticker | Negocio | Por qué está ahí |
|---|---|---|---|
| 1 | MU | 97,0 | +379% interanual, margen bruto del 86,8%, guía del 1T FY27 de $61.500M (≈ +8% sobre el consenso de LSEG) y catalizador A (95). Oferta limpia y el mejor valor relativo del universo. El mercado reaccionó tibio y está un 30% bajo el máximo. |
| 2 | SNDK | 90,2 | +372% y +51% secuencial (dos tercios por precio), beats del 5,7% en ingresos y del 12,3% en BPA (consenso de Rivkin y finviz). El mercado vendió el informe (−13% de hueco): **líder enfriado** con los fundamentales intactos, −45% desde el máximo. |
| 3 | SKHY | 84,5 | Líder de HBM, +257%, pero el 2T26 quedó un 5% por debajo del consenso coreano (FnGuide) y en Seúl cayó un 9,6%. ADR desde julio (≈ 70 sesiones), con huecos en el 3T y el 4T de 2025: sin TTM ni valor relativo (puntuado 50). |
| 4 | SIMO | 73,3 | Controladores NAND: +127%, beat del 12% en ventas y EP del +24% en julio, ya devuelto (−40%). Cuatro banderas por inventario y CFO negativo; dos clientes chinos son el 48% de las ventas. |
| 5 | PENG | 67,0 | El único en tendencia (RS percentil 100) y con EP confirmado el 7-oct (+13%, guía de FY27 +10% sobre el consenso). Pero tiene la peor calidad de beneficio (seis banderas: inventario +193%, cobros +159%, CFO negativo) y mucho papel convertible. |
| 6 | RMBS | 65,0 | Calidad (margen bruto del 80%, caja neta), pero crece «solo» un 20% con guía en línea (catalizador C) y es el más caro (11× ventas). −50% desde el máximo y bajo la SMA 200. |

## Por subgrupo

- **DRAM y HBM (MU, SKHY).** Tamaño parecido (≈ $995.000M de capitalización cada una). MU tiene mejor reacción a resultados, guía sobre el consenso y datos completos. SKHY lidera en HBM (56% en el 1T26 según IDC), pero pierde cuota: del 58% al 50% en el 2T26 según Counterpoint, con Samsung del 21% al 33% y MU del 21% al 18%. Además falló el consenso y su ADR es apenas un 2,4% del capital. MU tiene además contratos plurianuales take-or-pay que dan visibilidad: $134.000M de obligaciones pendientes y $13.000M de depósitos de clientes (10-K FY26).
- **NAND (SNDK).** El de mayor aceleración (+121 pp) y el más dependiente del precio, con $59.800M de obligaciones pendientes en sus acuerdos NBM (10-K FY26). El riesgo es el NAND, no la compañía: Western Digital ya vendió su participación y hay $15.500M de recompras disponibles.
- **Interfaz y controladores (RMBS, SIMO).** RMBS es el menos cíclico (contenido por módulo DDR5), con crecimiento moderado y caro. SIMO crece mucho más, pero con concentración china e inventario. SIMO reclama $160M a MaxLinear (MXL, universo semis) en un arbitraje: es un activo contingente, no está en las cuentas.
- **Módulos y sistemas (PENG).** La memoria ya es el 60% de las ventas (+158%). Es el más barato (1,8× ventas), en línea con un margen bruto del 28%. SK Telecom, del grupo de SK hynix, tiene preferentes convertibles por el 10,3%.

## Líderes enfriados con fundamentales intactos

- **SNDK**: +800% en 12 meses, −45% desde el máximo, RS 1m/3m en percentil 11/44, un 7% sobre la SMA 200; aceleración +121 pp y fundamentales 100. Candidato a un **EP el 29-oct** (fecha confirmada por la compañía).
- Cerca: MU (RS a 3 meses en percentil 78, demasiado alta para «enfriado»), SIMO (RS 1m/3m 22/0, pero la rentabilidad a 12 meses no supera la mediana del universo).

## Calendario y plan EP

| Fecha | Ticker | Evento | EP de calidad A/B si… | Se vuelve D si… |
|---|---|---|---|---|
| 26-oct (tras el cierre) | RMBS | Resultados 3T26 | ingresos ≥ $224M, producto ≥ $116M, guía 4T ≥ +5% sobre el consenso | ingresos dentro de la guía y margen de producto en el 60% bajo |
| 27-oct (tras el cierre; 28-oct en Seúl) | SKHY | Resultados 3T26 | beneficio operativo ≥ +5% sobre el consenso (≈ ₩78 billones a mediados de septiembre; FnGuide de la víspera [VERIFY]) y retribución por encima de la recompra de ₩40 billones | segundo fallo frente al consenso |
| 28-oct (tras el cierre) | SIMO | Resultados 3T26 | ventas ≥ $557M, margen bruto ≥ 51%, guía 4T con otro +15% secuencial | ventas dentro de la guía con más inventario |
| 29-oct (tras el cierre) | SNDK | Resultados 1T FY27 | ingresos ≥ $11.090M (+5% sobre $10.560M), margen ≥ 85%, guía 2T ≥ +5% | ingresos dentro de la guía y margen < 83% |
| ≈ 16–23-dic [VERIFY: no anunciada] | MU | Resultados 1T FY27 | ingresos ≥ $64.600M, margen ≥ 87%, guía 2T ≥ +5% | ingresos dentro del rango con guía plana |
| ≈ 5-ene [VERIFY: no anunciada] | PENG | Resultados 1T FY27 | — (sin plan EP: vigilar el capital circulante) | CFO negativo otra vez con inventario creciendo más que las ventas |

Regla de la matriz: con resultados a ≤ 3 sesiones solo vale un EP. RMBS entra en esa ventana el 21-oct, SKHY el 22-oct, SIMO el 23-oct y SNDK el 26-oct.

**Sin setups activos.** Ningún caso tiene un setup claro según swing.md §1: todo el grupo está en corrección salvo PENG, que no tiene base tras el EP del 7-oct.

## Diario (`journal.csv`)

Sin filas todavía: en el próximo `/ciclo` entran los valores con convicción Media o Alta que tengan setup (MU y SNDK salen Alta; el resto, Media).

## Lo que sigue en [VERIFY]

Quedan 9 marcas, todas sobre datos que aún no existen o que tienen una sola fuente:

- **Fechas no anunciadas:** MU (≈ 16–23-dic) y PENG (≈ 5-ene).
- **PENG:** saldo final de los convertibles 2029/2030 y float de la portada; los dará el 10-K FY26 (plazo ≈ 27-oct).
- **SKHY:** consenso de FnGuide del 3T26 la víspera (hoy, ≈ ₩78 billones según la prensa de mediados de septiembre).
- **SIMO:** consenso de ventas del 3T26 (≈ $529,8M), con una sola fuente (Benzinga).

Lo que no se publica ya no lleva [VERIFY] y se dice en el caso: el % de HBM sobre ingresos (MU y SKHY), los nombres de las contrapartes NBM de SNDK y de los clientes de SKHY, y la parte de Penguin en los contratos de $3.000M y $10.000M de sus clientes.

## Método

- Universo creado con `new_case.py` (alta automática). MU, SNDK, RMBS y PENG desde XBRL; RMBS con el 2T26 leído del XBRL del documento, y el 4T FY26 de PENG cargado del EX-99.1 porque el 10-K aún no está presentado. SKHY (K-IFRS, ₩ a US$ a tipo fijo) y SIMO (US GAAP) cargados a mano desde el 424B4 y los 6-K.
- Perfil nuevo `semis_memory` (`gm_target` 0,40 de media de ciclo, más peso en aceleración) para MU, SKHY y SNDK; `semis_fabless` para RMBS y SIMO; `semis_hardware` para PENG.
- Regla nueva en `validate.py`: un trimestre intermedio sin datos publicados se marca `gap: true` con motivo, en vez de inventarlo (SKHY 3T25 y 4T25).
- Fase 2 reproducible en `data/build_fase2.py`.
- Revisión del 19-oct (registrada en cada `notas.md`): los trimestres de MU, SNDK, RMBS y PENG cuadran con el XBRL de la SEC (ninguna diferencia > 0,5%); los cargados a mano (4T FY26 de PENG, 1T y 2T26 de SKHY, 2T26 de SIMO) cuadran con sus EX-99.1 y 6-K. Consenso cruzado con finviz, que responde desde el PC local. Cambio que mueve la nota: SNDK pasa al consenso más citado (Rivkin = finviz) y su catalizador sube de A 76 a A 80. Correcciones: SNDK presenta el 29-oct, no ≈ 5-nov; el neto del 4T de PENG lleva un beneficio fiscal de $57,6M; el canje de julio de PENG entregó ≈ 8,7M acciones; SKHY pierde cuota de HBM frente a Samsung.
- Excluidos: WDC y STX (discos duros) y NLST (OTC, litigios de patentes: forensic-microcap).
