Ejecuta el ciclo automático de todos los universos activos de `universes.json` (o solo de los que te indique en $ARGUMENTS, p. ej. `semis`). Trabaja sin pedirme confirmación salvo en los casos de PARADA. Idioma: español. Es investigación, no consejo de inversión: no operes, no conectes con brókers y no escribas órdenes.

**Intérprete de Python:** donde este documento dice `python3`, usa el que exista en esta máquina: `python3` en Mac/Linux; en Windows, `py -3` (no uses `python` a secas: puede apuntar a otro entorno virtual). Los scripts solo usan la librería estándar.

Lee primero CLAUDE.md, .claude/skills/growth-swing/SKILL.md (y sus references cuando las necesites) y `universes.json`. Para cada universo `U` (= su `dir`): `U/universe.json`, `U/resumen.md` y sus `cycle_notes`, que son obligatorias. Hoy = fecha del sistema. Rutas de scripts: S=.claude/skills/growth-swing/scripts.

## 0. Preparación
1. `git pull --ff-only`. Si hay cambios locales sin commit o conflicto → PARADA. (Los logs del lanzador automático viven fuera del repo; `*.log` está en `.gitignore`.)
2. Comprueba que `$SEC_USER_AGENT` existe y tiene nombre y email. Si no → PARADA.
3. Pasa los tests: `test_engines.py`, `test_prices.py`, `test_insiders.py`, `test_forensic.py` y `test_tools.py` de `.claude/skills/growth-swing/tests/`. Si alguno falla → PARADA.

## 1. Por cada universo U

### 1.1 Precios
1. `python3 $S/prices.py --universe U/universe.json --apply` (RS, ADR, «líder enfriado» y candidatos de setup).
2. Revisa `setup_candidates` de cada caso. Solo si hay un setup claro según swing.md §1, rellena `setup.type/pivot/stop` y explícalo en `setup.notes`; si un setup anterior se invalidó (cierre bajo el stop), ponlo a null y dilo en notas.md.

### 1.2 Altas (tickers con status `pendiente`)
1. `python3 $S/new_case.py --universe U/universe.json --ticker <T>` (CIK, filings, trimestres XBRL con respaldo del documento, precios, últimos resultados con reacción y próximos estimados). Emisores extranjeros: carga antes `U/data/<T>/quarters.json` desde los 6-K (CLAUDE.md) y pasa `--earn-date/--earn-timing/--earn-url`.
2. Completa la Fase 1 a mano: contrasta el último trimestre con el EX-99.1, KPIs del perfil (`sector_profiles.json`) con fuente, pureza y subgrupo con la nota de segmentos, descriptor y `financials_note`.
3. Haz la Fase 2 (auditoría) según la skill: catalizadores de 12 meses, consenso (paso 1.3.3), oferta, `insiders.py`, `forensic.py`, plan EP. Si no puedes terminarla en este ciclo, deja el status en `fundamentales` y dilo en el LOG; nunca marques `auditado` sin ella.
4. validate → render → commit `U: <T> <fase> <fecha>`.

### 1.3 Novedades por ticker auditado (modo actualización, CLAUDE.md)
1. Refresca el índice: `python3 $S/edgar.py --cik <CIK> --ua "$SEC_USER_AGENT" --out U/data/<T>/filings.json` y lista lo nuevo con `python3 $S/edgar.py --file U/data/<T>/filings.json --after <meta.last_filing_seen>`.
2. Si no hay nada nuevo ni PRs posteriores a `meta.report_date`, salta al siguiente.
3. **Resultados nuevos** (8-K 2.02, 6-K de resultados, ventas mensuales):
   - Trimestre: `python3 $S/xbrl.py --cik <CIK> --ua "$SEC_USER_AGENT" --filings U/data/<T>/filings.json --out U/data/<T>/quarters.json` (lee del documento el 10-Q/10-K que companyfacts aún no tiene). Emisores extranjeros y casos especiales: según `cycle_notes` y notas.md.
   - Catalizador `earnings` con la checklist de references/catalysts.md §2 y §4 (usa `casekit.earnings`). La sesión (bmo/amc) sale de `session` en filings.json; la reacción: `python3 $S/prices.py --universe U/universe.json --reaction <T> <fecha> amc|bmo`.
   - Consenso y sorpresa: `python3 $S/consensus.py --universe U/universe.json --ticker <T>` (finviz). Si sale con código 2 (bloqueado), búsqueda web con al menos dos fuentes y regístralas con `consensus.py --set campo=valor --source "etiqueta|url"`. Cita la fuente en `sources`. Si discrepan, usa la más citada y marca `[VERIFY]`.
   - Evalúa el informe contra el plan EP que ya está en `text.plan`: ¿cumple las condiciones A/B o las de D? Escríbelo en `text.plan` y en notas.md.
4. **Otros filings materiales**: 8-K 1.01, 2.01, 3.02, 4.01, 4.02, 5.02, 8.01; 424B/S-3/S-3ASR; 13D/13G; 6-K que no sean ventas rutinarias. Clasifícalos (catalizador, oferta o forense), puntúalos con la checklist y actualiza `supply[]`, `manual.kpis` y `text.*` con fuente. Un PR sin filing se busca en la web de la compañía.
5. **Insiders y forense**: si hay Forms 4/144/13D/13G nuevos, `python3 $S/insiders.py --filings U/data/<T>/filings.json --ua "$SEC_USER_AGENT" --out U/data/<T>/insiders.json` y actualiza la fila `insider` de `supply[]` (`casekit.insider_supply`). Si hay 10-Q/10-K/20-F nuevo, `python3 $S/forensic.py --cik <CIK> --ua "$SEC_USER_AGENT" --filings ... --prices ... --out U/data/<T>/forensic.json`.
6. **Fechas de resultados**: confirma las que siguen con `[VERIFY]` en `events` (`earnings_date` de consensus.json, PR de la compañía o 8-K). Si se confirma, quita el `[VERIFY]` y cita la fuente.
7. Actualiza `meta.report_date` = hoy y `meta.last_filing_seen` = último accession revisado. Añade a `U/data/<T>/notas.md` una línea «fecha · qué cambió».
8. `python3 $S/validate.py U/cases/<T>.json` (debe dar OK) → `python3 $S/render.py U/cases/<T>.json U/reports/<T>_swing.html` → commit `U: <T> actualización <fecha>`.

### 1.4 Cierre del universo
1. `python3 $S/rank.py U/cases --universe U/universe.json --sync-peers --out-dir U --title "<title de universes.json>"` y vuelve a renderizar todos los casos (los pares cambian).
2. Diario: `python3 $S/journal.py --universe U/universe.json --add --update` (señales con convicción ≥ Media y setup; resultados a +5/+20/+60 sesiones).
3. Actualiza `U/resumen.md`: tabla del ranking con una línea de por qué, líderes enfriados, calendario con plan EP (próximas 6–8 semanas) y la lista de `[VERIFY]` pendientes. Quita lo ya resuelto.

## 2. Cierre
1. `python3 $S/sitepage.py --universes universes.json --out site` (índice local de todos los universos; `site/` no se versiona).
2. Escribe al principio de `LOG.md` (raíz) una entrada con la fecha: qué tickers cambiaron y por qué (por universo), altas nuevas, alertas de las próximas 3 sesiones (resultados, lock-ups), setups activos o invalidados y lo que quedó en `[VERIFY]`.
3. `git add` + commit (`ciclo <fecha>`) + `git push`.
4. Termina con un resumen de 12 líneas como máximo: cambios en los rankings, convicción, alertas y qué necesita mi atención.

## Reglas
- Los números los calculan los scripts; el texto solo interpreta. Cada cifra lleva fuente o `[VERIFY: motivo]`. Nunca inventes consenso, precios, fechas ni pares.
- Si una regla de la skill no encaja, no la retuerzas en el texto: propón el cambio en el script y su reference, con test, en un commit aparte.
- No borres datos ni reescribas el historial de git. No toques los tickers con status `excluido`.
- PARADA = escribe el motivo en `LOG.md`, haz commit de lo que esté validado y termina sin seguir con el resto.
