# Catalizadores — taxonomía, verificación y puntuación

El objetivo es separar los PRs que cambian el negocio de los que solo cambian el precio un día. Cada catalizador se registra en `case.json → catalysts[]` y lo puntúa `scripts/catalysts.py`. Nunca se puntúa de memoria.

## 1. Tipos

| `type` | Qué es | Dónde verificar |
|---|---|---|
| `gov_contract` | Adjudicación o contrato con una administración (DoD, NASA, DOE, agencias civiles, gobiernos extranjeros) | USASpending.gov (API `api.usaspending.gov/api/v2/search/spending_by_award/`), SAM.gov (adjudicaciones), anuncios diarios de contratos del DoD (defense.gov/News/Contracts), sitio de la agencia, 8-K Item 1.01 |
| `commercial_contract` | Contrato, orden de compra o acuerdo de suministro con un cliente privado | 8-K Item 1.01 + exhibit EX-10.x, PR o filing de la contraparte, RPO/backlog en el siguiente 10-Q |
| `partnership` | Alianza, colaboración, integración, distribución | Lo mismo; casi nunca hay exhibit. Comprobar qué publica la contraparte |
| `product` | Lanzamiento, aprobación regulatoria (FDA, FAA, FCC, CE), certificación, primer envío | Base de datos del regulador (FDA Drugs@FDA / 510(k) / PMA), web del producto, ingresos en el trimestre siguiente |
| `financing` | Ampliación, convertible, deuda, inversión estratégica | 424B, 8-K, S-3/F-3, términos (precio frente al mercado, warrants, descuento) |
| `earnings` | Resultados trimestrales y guía | 8-K Item 2.02 con EX-99.1, 10-Q, transcript |
| `mna` | Compra, venta, fusión | 8-K Items 1.01/2.01, proxy/S-4, contraprestación (acciones o caja) |
| `index_analyst` | Inclusión en índices, inicio de cobertura, upgrades | Anuncio del proveedor del índice; no cambia el negocio |
| `other` | Resto | — |

## 2. Lo que se registra (checklist)

Comunes: `date`, `time_et` (premarket / horario / after-hours), `headline`, `sources[]`, `counterparty`, `counterparty_named`, `counterparty_confirms` (la contraparte lo publica o figura en un registro público), `filed_8k_101`, `exhibit_attached`, `binding`, `value_firm` (comprometido / obligado / con fondos), `value_ceiling` (techo «de hasta»), `duration_years`, `economics_disclosed` (calendario de ingresos, márgenes), `recurring`, `issuer_history` (`converted` / `partial` / `not_converted` / `unknown`), `pr_count_90d`, `financing_after_days` (días hasta la siguiente financiación dilutiva; `null` si no hubo), `financing_discount_pct`, `insider_selling_after` (bool), `lockup_within_days`, `promo_language` (bool: superlativos, «transformacional», «revolucionario», TAM sin cifras propias).

Valores de `binding`, de más a menos vinculante:
`definitive` · `purchase_order` · `award_funded` · `award_unfunded` · `idiq_ceiling` · `option_exercise` · `loi` · `mou` · `partnership_undefined` · `none`

Para `earnings`: `rev_growth_yoy`, `rev_growth_yoy_prev`, `rev_surprise_pct`, `eps_surprise_pct`, `guide_raise` (true/false/null), `guide_change_pct`, `gm_change_bp`, `nonrecurring_in_beat`.

Para `financing`: `financing_type` (`atm` / `registered_direct` / `underwritten` / `convertible` / `pipe` / `strategic` / `debt`), `price_vs_market_pct` (+ prima / − descuento), `warrants` (bool), `strategic_investor` (nombre).

Reacción de mercado (se rellena cuando haya datos de precio; puntuación aparte): `gap_pct`, `rvol`, `close_in_range` (0–1), `day2_follow` (bool), `dollar_volume`, `estimate_revisions` (`up` / `flat` / `down` / `unknown`).

## 3. Puntuación (0–100) para contratos, partnerships y productos

| Componente | Peso | Cómo puntúa |
|---|---|---|
| Verificable | 25 | Contraparte nombrada 5 · la contraparte lo confirma o figura en registro público 10 · 8-K 1.01 5 · exhibit 5 |
| Vinculante | 20 | definitive/purchase_order/award_funded 20 · option_exercise 16 · award_unfunded 12 · idiq_ceiling 8 · loi 5 · mou 3 · partnership_undefined 1 · none 0 |
| Materialidad | 20 | Valor firme anualizado ÷ ingresos TTM: ≥25% 20 · 10–25% 14 · 3–10% 8 · >0–3% 3 · desconocido 0 |
| Economía | 10 | Calendario o márgenes revelados 6 · recurrente 4 |
| Historial | 10 | converted 10 · partial 5 · unknown 3 · not_converted 0; −3 si `pr_count_90d` ≥ 6 |
| Sin juxtaposiciones | 15 | Parte de 15 y resta: financiación ≤ 10 días después −10 (−15 si con descuento ≥ 10%) · venta de insiders −5 · lock-up ≤ 30 días −5 · lenguaje promocional −3 |

Topes que anulan la suma:
- `binding` en loi / mou / partnership_undefined / none y sin `value_firm` → máximo **C**.
- Financiación con descuento en los 10 días siguientes → máximo **C** y bandera `PR→FINANCIACIÓN`.
- Solo techo IDIQ (sin valor obligado) → la materialidad se calcula con 0 y bandera `TECHO ≠ INGRESO`.
- `issuer_history = not_converted` y `promo_language` → máximo **D**.

Nota: **A** ≥ 75 · **B** 60–74 · **C** 40–59 · **D** < 40. Veredicto: A = `real`, B = `real parcial`, C = `por confirmar`, D = `especulación`.

## 4. Puntuación de resultados (`earnings`)

| Componente | Peso | Regla |
|---|---|---|
| Crecimiento | 25 | Crecimiento interanual de ingresos ≥ 40% 25 · 25–40% 18 · 15–25% 10 · < 15% 3 |
| Aceleración | 20 | Δ crecimiento ≥ +10 pp 20 · +3 a +10 15 · ±3 8 · < −3 0 |
| Sorpresa | 20 | Sorpresa de ingresos ≥ 5% 10 / 2–5% 6 / > 0 3; sorpresa de BPA ≥ 10% 10 / > 0 5 |
| Guía | 25 | Sube ≥ 5% 25 · sube < 5% 18 · mantiene 8 · baja 0 · sin guía 5 |
| Calidad | 10 | Margen bruto ≥ +100 pb 10 · ≥ 0 6 · < 0 2; −10 si el beat incluye partidas no recurrentes |

## 5. Puntuación de financiación

Arranca en 50: estratégica a prima +35 · con prima +15 · descuento ≥ 15% −25 · descuento 5–15% −15 · ATM −10 · warrants −10 · convertible con precio variable −25. Positiva solo si la nota final ≥ 60.

## 6. Confirmación de mercado (aparte, 0–100)

Gap ≥ 10% 20 · RVOL ≥ 5 25 (≥ 3 15) · cierre en el tercio superior 20 · continuación el día 2 15 · revisiones al alza 20. Se muestra junto a la nota del catalizador, nunca se suma: un catalizador D con confirmación alta es una operación corta, no una tesis.

## 7. Señales rojas narrativas (heredadas del forense de micro caps)

- Repetición: el mismo «acuerdo» anunciado varias veces con distinto nombre.
- Contraparte sin presencia verificable, recién constituida o vinculada al emisor.
- Cifras de pipeline, «oportunidades» o TAM presentadas como ingresos.
- PR de noche o en premarket seguido de una oferta registrada en 24–72 horas.
- Previsiones anteriores incumplidas (comparar cada guía con el dato real posterior).
- Cambio de narrativa (IA, cripto, defensa, cuántica) sin cambio en los ingresos.
