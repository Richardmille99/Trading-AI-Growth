# Esquema del caso (`case.json`, versión 1.0)

Un archivo por ticker: `casos/<TICKER>_<CIK>.json`. `examples/BIYA_0001944712.json` es la referencia completa; copiar su forma. `scripts/validate.py` comprueba claves obligatorias y que todas las métricas citadas existan.

## Markup en los campos de texto

| Escribe | Sale |
|---|---|
| `{m.clave}` / `{m.clave:fmt}` | Métrica de `compute.py`. fmt: `int` `M1` `M2` `x` `x1` `x1n` `pct` `pct0` `pct0x` `px` `px3` `usd` `usdM` |
| `[[etiqueta\|url]]` | Chip de fuente (url vacía = chip sin enlace) |
| `[VERIFY]` / `[VERIFY: nota]` | Insignia amarilla de verificación |
| `**texto**` | Negrita |

Regla: cualquier número derivado (ratios, múltiplos, runway, colchones, % de float) va como `{m.…}`; los números leídos de un filing pueden ir literales con su chip de fuente.

## Bloques

| Clave | Tipo | Contenido |
|---|---|---|
| `meta` | obj | `ticker`, `issuer`, `cik`, `exchange`, `report_date` (AAAA-MM-DD), `price_basis`, `descriptor`, `language` |
| `market` | obj | `prev_close`, `prev_close_date`, `change_pct`, `volume`, `high60`, `high60_date`, `daily` [[fecha, cierre, volumen]×20], `adv_window_note`, `src` |
| `shares` | obj | `os_primary`, `os_primary_label`, `os_alternates` [{value,label}], `non_affiliates`, `class_b` {shares, votes_per_share, convertible: true/false/null}, `authorized_A`, `reference_os` {label, shares}, `ipo_os`, `os_at_financials`, `splits` [{date, ratio, note}], `ladder` [{label, shares (base actual), src}] |
| `financials` | obj | `as_of`, `cash`, `equity`, `total_assets`, `big_asset` {label,value}, `cash_like` [{label,value}], `equity_adjustments` [{label,value}], `opcf` {value, months}, `pre_wc_burn` {loss, noncash, months}, `going_concern` |
| `compliance_inputs` | obj | `bid_min`, `mvphs_min`, `mvls_rule_line`, `no_cure_overlays` [{label, until}] |
| `chart` | obj | `pmin`, `pmax`, `ymax` (opcional), `price_marks` [[precio, etiqueta]] |
| `instruments` | lista | Ver abajo |
| `ledger_extra` | lista | Filas extra del ledger: `name`, `shares` (texto), `gate_level` (r/a/g/b), `gate_label`, `arming`, `src` |
| `header` | obj | `verdict`, `mixed`, `live`, `gated`, `actors`, `changes` |
| `grades` | obj | `overhead`, `dilution`, `frequency`, `offering`, `cash`, `compliance` → {level: Alto/Medio/Bajo, why} |
| `grades_note`, `alert` | texto | Nota de calificación y alerta ámbar/roja |
| `snapshot` | lista | [etiqueta, texto] × 10: Market cap, Cierre previo, Float/O/S, Caja/acción, Inst. ownership, Estado bursátil, Estado legal, Nexo China, Símbolos previos, Splits |
| `os_caption`, `supply_caption` | texto | Pies de los dos gráficos |
| `capital_intro` | texto | Intro de §3 |
| `registrations` | lista | [ruta, presentado/efectivo, capacidad, nivel r/a/g/b/v, estado] |
| `facilities` | lista | [facilidad, tamaño, precio y condiciones, nivel, estado] + `facilities_note` |
| `warrants_text`, `convertibles_text` | texto | §3.3 y §3.4 (o tablas descritas en texto si hay pocos) |
| `offerings`, `offerings_note`, `offerings_read` | lista/texto | [fecha, tipo, acciones aj., precio aj., captado, banco/inversor, vendible, fuente] |
| `timeline`, `timeline_note` | lista/texto | [fecha, tipo CAP/LEG/PR/GOV/FIN/MKT, evento], más reciente primero |
| `cash_text`, `cash_read` | lista/texto | Párrafos de §5 |
| `compliance`, `compliance_note` | lista/texto | [estándar, requisito, compañía, nivel, estado, fechas] |
| `legal_text` | texto | §7 |
| `governance_text` | lista | Párrafos de §8 |
| `ownership`, `float_recon` | lista/texto | [titular, tipo, acciones/%, base, perfil] |
| `catalysts`, `catalysts_note` | lista/texto | [fecha, evento · qué vigilar] |
| `today_text` | lista | Párrafos de §11 |
| `read` | obj | `ceo_headline`, `ceo` [puntos], `ladder` [[precio, significado]], `verdict` |
| `sources` | lista | [etiqueta, url] — solo páginas abiertas |

## Instrumento

```json
{"id": "elocA", "name": "Nombre completo con contraparte y fecha", "short": "Etiqueta de gráfico",
 "gate": "live|gated|price|issued", "shares_max": 0, "shares_min": 0,
 "supply": {"model": "fixed|shelf_ib5|dollars_discount|cashless_bs", "...": "parámetros"},
 "fd": true, "in_os": false, "basis": 3.12, "discount": 0.70, "chart": true,
 "gate_label": "VIVA — registrada", "arming": "Evento que lo arma, con fecha [VERIFY si falta]",
 "src": [["etiqueta", "url"]]}
```

Parámetros por modelo:
- `dollars_discount`: `dollars`, `discount`, `floor` (opcional), `cap_price` (opcional), `max_shares` (opcional)
- `cashless_bs`: `warrants`, `strike`, `vol` (def. 1,75), `term` (años, def. 5), `floor`
- `shelf_ib5`: usa `shares.non_affiliates` y `market.high60` salvo que se den `non_affiliates` / `high60`

Métricas generadas por instrumento: `{id}_max`, `{id}_min`, `{id}_pct_os`, `{id}_pct_float`, `{id}_pnl` (si `basis`), `{id}_px` y `{id}_proceeds` (si `discount`).

## Métricas globales principales

`prev_close os non_aff affiliates classB cum_split raw_equiv mcap_A mcap_AB voteshare_B headroom_A headroom_x growth_ref growth_ipo since_fin since_fin_pct adv_mean adv_median largest_vol largest_date largest_turnover printable_lo printable_hi printable_{lo,hi}_{xos,xfloat,xadv} gated_total gated_xfloat fd fd_xos fd_xfloat shelf_cap_now shelf_cap_high shelf_sh_now shelf_sh_floor ib1_px cash equity cash_ps burn_cash burn_prewc months_elapsed cash_pf_hi cash_pf_lo runway_lo runway_hi big_asset big_asset_pct_eq big_asset_pct_assets book_ps adj_equity adj_book_ps cash_like cash_like_ps bid_cushion mvphs mvphs_line mvls_line report_date`

Lista completa con valores: `python scripts/compute.py casos/<caso>.json`.
