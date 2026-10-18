# Fundamentales de crecimiento y calidad del beneficio

## 1. Fuente: SEC XBRL `companyfacts`

`https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` (cabecera `User-Agent: nombre email`, ≤ 10 peticiones/s). `scripts/xbrl.py` descarga, elige la etiqueta disponible de cada concepto y devuelve trimestres discretos (deriva el Q4 de anual − 9 meses cuando falta).

| Concepto interno | Etiquetas us-gaap por orden de preferencia (ifrs-full para FPI) | Tipo |
|---|---|---|
| `revenue` | RevenueFromContractWithCustomerExcludingAssessedTax, Revenues, SalesRevenueNet, RevenueFromContractWithCustomerIncludingAssessedTax · ifrs: Revenue | flujo |
| `gross_profit` | GrossProfit (si falta: revenue − CostOfRevenue / CostOfGoodsAndServicesSold) | flujo |
| `op_income` | OperatingIncomeLoss | flujo |
| `net_income` | NetIncomeLoss · ifrs: ProfitLoss | flujo |
| `cfo` | NetCashProvidedByUsedInOperatingActivities | flujo (acumulado en el año → se discretiza) |
| `capex` | PaymentsToAcquirePropertyPlantAndEquipment (+ PaymentsToDevelopSoftware si existe) | flujo |
| `sbc` | ShareBasedCompensation, AllocatedShareBasedCompensationExpense | flujo |
| `diluted_shares` | WeightedAverageNumberOfDilutedSharesOutstanding | media del periodo |
| `shares_out` | dei:EntityCommonStockSharesOutstanding | puntual (portada) |
| `ar` | AccountsReceivableNetCurrent | saldo |
| `deferred_rev` | ContractWithCustomerLiabilityCurrent, DeferredRevenueCurrent | saldo |
| `rpo` | RevenueRemainingPerformanceObligation | saldo |
| `inventory` | InventoryNet | saldo |
| `cash` | CashAndCashEquivalentsAtCarryingValue (+ ShortTermInvestments / MarketableSecuritiesCurrent) | saldo |
| `debt` | LongTermDebt, LongTermDebtNoncurrent + LongTermDebtCurrent, ConvertibleNotesPayable | saldo |
| `total_assets` | Assets | saldo |
| `capitalized_sw` | CapitalizedComputerSoftwareAdditions | flujo |

Los KPIs que no están en XBRL (NRR, clientes > $100k, book-to-bill, backlog no RPO) se leen del 10-Q/10-K, del EX-99.1 de resultados o del transcript y se cargan a mano con su fuente.

## 2. Métricas (`scripts/fundamentals.py`)

| Métrica | Definición |
|---|---|
| Crecimiento interanual | (Q / Q−4) − 1 para ingresos, beneficio bruto, BPA diluido |
| Aceleración | crecimiento(Q) − crecimiento(Q−1), en pp |
| Margen bruto, operativo, FCF | sobre ingresos del trimestre y TTM |
| FCF | CFO − capex (− software capitalizado) |
| Rule of 40 | crecimiento TTM de ingresos + margen FCF TTM |
| SBC % ingresos | SBC TTM ÷ ingresos TTM |
| Dilución neta | acciones diluidas medias, interanual |
| DSO | cuentas por cobrar ÷ ingresos del trimestre × 91 |
| Ingresos diferidos y RPO | crecimiento interanual frente al de ingresos |
| Accruals (Sloan) | (beneficio neto TTM − CFO TTM) ÷ activos medios |
| Margen incremental | Δ resultado operativo TTM ÷ Δ ingresos TTM |
| Caja neta y runway | caja − deuda; meses de runway si el FCF es negativo |

## 3. Banderas de calidad (automáticas)

| Bandera | Regla |
|---|---|
| `COBROS > VENTAS` | Crecimiento de cuentas por cobrar − crecimiento de ingresos > 20 pp |
| `DSO AL ALZA` | DSO +15% interanual con crecimiento que desacelera |
| `DIFERIDOS SE FRENAN` | (perfil SaaS) crecimiento de diferidos o RPO < crecimiento de ingresos − 15 pp |
| `BENEFICIO SIN CAJA` | Beneficio neto TTM > 0 y CFO TTM < 0 |
| `ACCRUALS ALTOS` | Accruals de Sloan > 10% |
| `SBC PESADA` | SBC > 20% de ingresos TTM |
| `DILUCIÓN` | Acciones diluidas +5% interanual |
| `INVENTARIO > VENTAS` | (hardware, semis, consumo) crecimiento de inventario − crecimiento de ingresos > 25 pp |
| `CAPITALIZACIÓN` | Software capitalizado > 10% del gasto operativo o creciendo > 2× los ingresos |
| `NON-GAAP AGRESIVO` | (manual) ajustes non-GAAP > 30% de los ingresos o partidas «no recurrentes» repetidas |
| `RUNWAY CORTO` | FCF negativo y caja neta < 12 meses de consumo |

## 4. Valoración y expectativas

- EV = market cap (acciones de portada × precio) + deuda − caja.
- EV/ventas, EV/beneficio bruto y EV/ventas ÷ crecimiento (crecimiento-ajustado).
- **DCF inverso:** busca el crecimiento anual de ingresos de los años 1–5 que hace que el valor presente iguale el EV. Supuestos por defecto: margen FCF que converge linealmente al margen objetivo del perfil sectorial en el año 5; crecimiento que se desvanece linealmente hasta el terminal (3%) entre los años 6 y 10; tasa de descuento 10%; valor terminal por Gordon. Resultado: «el precio descuenta X% anual durante 5 años», comparado con el crecimiento actual.
- Sin estimaciones de consenso (fase 2) la columna de revisiones queda vacía, marcada `[VERIFY: sin consenso]`.

## 5. Perfiles sectoriales (`assets/sector_profiles.json`)

Cada perfil define el margen FCF objetivo del DCF inverso, las métricas que pesan en la nota de fundamentales y los KPIs manuales que hay que buscar.

| Perfil | KPIs manuales | Banderas extra |
|---|---|---|
| `saas` | NRR, RPO/cRPO, clientes > $100k, payback CAC | DIFERIDOS SE FRENAN, CAPITALIZACIÓN |
| `semis_hardware` | Book-to-bill, inventario en canal, concentración de clientes | INVENTARIO > VENTAS |
| `defense_gov` | Backlog financiado/no financiado, tasa de victoria, % ingresos públicos | TECHO ≠ INGRESO (catalizadores) |
| `biotech_commercial` | Prescripciones, ventas netas por producto, guía de producto | Dependencia de un producto |
| `consumer` | Ventas comparables, tiendas, inventario | INVENTARIO > VENTAS |
| `industrial_energy` | Backlog, book-to-bill, márgenes de proyecto | Contabilidad por grado de avance |
| `fintech` | Volumen procesado, take rate, provisiones | Calidad de la cartera |
| `generic` | — | — |

## 6. Nota de fundamentales (0–100, `scripts/fundamentals.py`)

Seis componentes, cada uno de 0 a 100, ponderados con los pesos del perfil. Si falta un componente se reparte su peso entre los demás y el informe lo dice.

| Componente | Regla |
|---|---|
| Crecimiento | Ingresos interanuales del último trimestre: ≥ 50% 100 · ≥ 30% 80 · ≥ 20% 60 · ≥ 10% 35 · ≥ 0% 15 · < 0% 0 |
| Aceleración | Δ pp frente al trimestre anterior: ≥ +10 100 · ≥ +3 75 · > −3 50 · > −10 25 · resto 0 |
| Margen bruto | Margen TTM frente al `gm_target` del perfil: ≥ objetivo 100 · hasta −10 pp 70 · hasta −20 pp 40 · peor 15 |
| Rule of 40 | ≥ 60 100 · ≥ 40 80 · ≥ 25 55 · ≥ 10 30 · resto 10 |
| Apalancamiento operativo | Margen incremental TTM: ≥ 30% 100 · ≥ 10% 70 · ≥ 0% 45 · < 0% 15 · ingresos que no crecen 30 |
| Calidad | 100 − 15 por cada bandera activa de §3 |

Lectura: ≥ 65 fuerte · 45–64 aceptable · < 45 débil.

## 7. Comparación con el grupo (`scripts/compute.py`)

`case.json → peers[]`: cada par con `rev_yoy`, `accel_pp`, `gm`, `rule40`, `ev_sales`, `rs_3m`, sacados con el mismo método (XBRL + precio del mismo día). El caso se añade solo.

- Percentil de cada métrica frente al resto del grupo (0–100; en EV/ventas, más bajo = mejor).
- **Percentil de fundamentales** = media de crecimiento, aceleración, margen bruto y Rule of 40.
- **Percentil de valor** = EV/ventas ÷ crecimiento (en %), más bajo = más barato.
- **Posición:** `leader` si fundamentales ≥ 80 y RS ≥ 80 · `strong` si ≥ 60 y ≥ 60 · `weak` si alguno < 40 · `neutral` el resto · `unknown` con menos de 3 pares o sin RS.
- Gráfico de cuadrantes: crecimiento (x) frente a EV/ventas (y), con las medianas del grupo. La zona interesante es «más crecimiento · múltiplo menor», siempre que la calidad (§3) no lo explique.
