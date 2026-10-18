# Esquema de `case.json` (growth-swing v1.0)

Ejemplo completo: `examples/EXMP_synthetic.json` (caso **sintético**). Importes en USD sin escalar, acciones en unidades, ratios como fracción (0,25 = 25%) salvo donde se indica.

## meta
`ticker`, `issuer`, `cik`, `exchange`, `report_date` (AAAA-MM-DD, fecha de corte), `price_basis` (texto), `profile` (clave de `assets/sector_profiles.json`), `theme`, `group`, `descriptor` (markup), `primary_catalyst` (id; si falta, el de mayor nota), `synthetic` (bool: muestra el aviso).

## market
`price`, `price_date` (los rellena `prices.py --apply`), `regime` (`risk_on` / `neutral` / `risk_off` / `unknown`), `regime_evidence` (markup).

## financials
`quarters[]` de antiguo a reciente, tal como los devuelve `scripts/xbrl.py`: `period`, `end`, `revenue`, `gross_profit`, `op_income`, `net_income`, `cfo`, `capex`, `capitalized_sw`, `sbc`, `diluted_shares`, `basic_shares` (opcional; se usa en la dilución cuando un trimestre tiene pérdidas y el otro beneficios), `ar`, `deferred_rev`, `rpo`, `inventory`, `cash` (incluye inversiones a corto), `debt`, `total_assets`. Flujos discretos por trimestre; saldos a fin de periodo; `null` si no hay dato. Además `shares_out` (portada), `shares_out_date`, `source`.

## manual
`kpis[]` (`name`, `value`, `prior`, `src`), `nongaap_adj_pct` (fracción), `nongaap_recurring_items` (bool). Sin estos campos la bandera NON-GAAP queda n/d.

## catalysts[]
Campos en `references/catalysts.md` §2. Obligatorios: `id`, `type`, `date`, `headline`, `sources` ([[etiqueta, url]]). Opcional `note` (markup) para el desglose.

## supply[] y supply_context
Cada fuente: `id`, `kind` (`atm` / `shelf` / `secondary` / `convertible` / `warrants` / `lockup` / `insider` / `sbc` / `pipe_resale`), `name`, `shares`, `capacity_usd` (ATM y shelf), `price_basis`, `gate` (`live` / `gated` / `dated`), `date`, `flagged` (insiders), `notes`, `src`.
`supply_context`: `float_shares`, `window_days` (56 por defecto), `ep_recent_days`, `atm_used_last_q` (bool).

## peers[]
`ticker`, `name`, `rev_yoy`, `accel_pp` (pp), `gm`, `rule40` (puntos), `ev_sales`, `rs_3m` (percentil 0–100).

## setup
`type` (ver `references/swing.md` §2), `pivot`, `stop`, `adr_pct` (en %), `rs_1m`, `rs_3m`, `rs_6m`, `ema_stack` (bool), `notes` (markup). Sin datos de precio: `null`.
`cooled_leader`: `"cooled_leader"` / `"cooled_leader_broken"` / `null` (swing.md §6; lo escribe `scripts/prices.py --apply`).
`setup_candidates[]`: propuestas mecánicas de `prices.py` (`type`, `date`, `pivot`, `stop`, `why`); no cuentan para la convicción hasta que el analista copia una a `type`/`pivot`/`stop`.

## events[]
`date`, `kind` (`earnings`, `lockup`, `regulatory`, `offering`, `index`, `meeting`, `other`), `text`, `src`. `earnings` en ≤ 3 sesiones descarta setups que no sean EP.

## header (tiles §0, markup)
`verdict`, `setup`, `catalyst`, `quality`, `supply`, `group`.

## snapshot
Lista de pares `[etiqueta, texto con markup]`.

## text (markup)
`narrative_flags[]`, `catalyst_read`, `financials_note`, `quality[]`, `supply_read`, `valuation[]`, `group_read`, `risks[]`, `plan[]`, `verdict`.

## sources
Lista `[etiqueta, url]` (url vacía permitida).

## Markup
`{m.clave:formato}` · `[[etiqueta|url]]` · `[VERIFY: nota]` · `**negrita**`.
Formatos: `int`, `M1`, `M2`, `usdM`, `px`, `x1`, `x2`, `n1`, `sc` (nota sin decimales), `pct` (ya en %), `pctf` / `pctf0` (fracción → %), `pp` (con signo).

## Métricas disponibles (`m`)
- **Fundamentales:** `rev_q`, `rev_yoy`, `rev_yoy_prev`, `accel_pp`, `gp_yoy`, `eps_q`, `eps_yoy`, `gm_q`, `opm_q`, `fcf_q`, `fcfm_q`, `revenue_ttm`, `gross_profit_ttm`, `op_income_ttm`, `net_income_ttm`, `cfo_ttm`, `capex_ttm`, `capitalized_sw_ttm`, `sbc_ttm`, `rev_ttm_prev`, `rev_ttm_yoy`, `gm_ttm`, `opm_ttm`, `fcf_ttm`, `fcfm_ttm`, `rule40`, `sbc_pct`, `dil_yoy`, `dso`, `dso_prev`, `dso_chg`, `ar_yoy`, `inv_yoy`, `def_yoy`, `rpo_yoy`, `accruals`, `incr_margin`, `cash`, `debt`, `net_cash`, `runway_m`, `capsw_opex`, `capsw_yoy`.
- **Nota:** `fund_score`, `fs_growth`, `fs_accel`, `fs_gross_margin`, `fs_rule40`, `fs_op_leverage`, `fs_quality`, `flags_on`.
- **Catalizadores:** `cat_<id>_score`, `cat_<id>_mat` (materialidad), `cat_<id>_mkt` (confirmación), `cat_score` (principal).
- **Valoración:** `price`, `shares_out`, `mcap`, `ev`, `ev_sales`, `ev_gp`, `ev_sales_g`, `fcf_target`, `implied_g`, `implied_vs_now_pp`.
- **Oferta:** `supply_score`, `lockup_pct`, `overhang_pct`, `float_shares`.
- **Grupo:** `fund_pct`, `rs_pct`, `value_pct`, `n_peers`.
- **Setup:** `pivot`, `stop`, `risk_ps`, `risk_pct`, `risk_adr`, `adr_pct`, `ext_pivot`, `size_r`.
