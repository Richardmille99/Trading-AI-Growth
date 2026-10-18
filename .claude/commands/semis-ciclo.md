Ejecuta el ciclo automático del universo de semiconductores. Trabaja sin pedirme confirmación salvo en los casos de PARADA. Idioma: español. Es investigación, no consejo de inversión: no operes, no conectes con brókers y no escribas órdenes.

**Intérprete de Python:** donde este documento dice `python3`, usa el que exista en esta máquina: `python3` en Mac/Linux; en Windows, `py -3` (no uses `python` a secas: puede apuntar a otro entorno virtual). Los scripts solo usan la librería estándar.

Lee primero CLAUDE.md, .claude/skills/growth-swing/SKILL.md (y sus references cuando las necesites), semis/universe.json y semis/resumen.md. Hoy = fecha del sistema. Rutas de scripts: S=.claude/skills/growth-swing/scripts.

## 0. Preparación
1. `git pull --ff-only`. Si hay cambios locales sin commit o conflicto → PARADA. (Los logs del lanzador automático viven fuera del repo; `*.log` está en `.gitignore`.)
2. Comprueba que `$SEC_USER_AGENT` existe y tiene nombre y email. Si no → PARADA.
3. Pasa los tests: `python3 .claude/skills/growth-swing/tests/test_engines.py`, `test_prices.py`, `test_insiders.py`, `test_forensic.py`. Si alguno falla → PARADA.

## 1. Precios y régimen
1. `python3 $S/prices.py --universe semis/universe.json --apply` (descarga 2 años, RS, ADR, «líder enfriado», candidatos y proxy de régimen).
2. Amplitud de mercado: si puedes calcularla con datos reales (p. ej. % de componentes de SOXX/SMH sobre su media de 50 o ratio de Stockbee), añádela a `market.regime_evidence` con su fuente. Si no, deja el proxy de tendencia tal cual. No ajustes el régimen a mano.
3. Revisa `setup_candidates` de cada caso. Solo si hay un setup claro según swing.md §2, rellena `setup.type/pivot/stop` y explica en `setup.notes`; si un setup anterior se invalidó (cierre bajo el stop), ponlo a null y dilo en notas.md.

## 2. Novedades por ticker (modo actualización, CLAUDE.md)
Para cada ticker con status `auditado`:
1. Refresca el índice: `python3 $S/edgar.py --cik <CIK> --ua "$SEC_USER_AGENT" --out semis/data/<T>/filings.json` y lista lo nuevo con `python3 $S/edgar.py --file semis/data/<T>/filings.json --after <meta.last_filing_seen>`.
2. Si no hay nada nuevo ni PRs posteriores a `meta.report_date`, salta al siguiente.
3. **Resultados nuevos** (8-K 2.02, 6-K de resultados, ventas mensuales de ASX):
   - Añade el trimestre: `xbrl.py` para emisores con 10-Q; si companyfacts aún no lo tiene, cárgalo del EX-99.1/10-Q con la fuente en `src`. TSEM y ASX desde el 6-K (ver notas.md de cada uno: US GAAP / Taiwan-IFRS en US$ a tipo fijo, ADS = 2 acciones). SWKS: el caso usa `quarters_proforma.json` (suma SWKS + Qorvo); desde el 1T FY27 los trimestres ya son combinados.
   - Catalizador `earnings` con la checklist de references/catalysts.md §2 y §4. Reacción de mercado: `python3 $S/prices.py --universe semis/universe.json --reaction <T> <fecha> amc|bmo`.
   - Consenso y sorpresa: primero la página de finviz del ticker (`https://finviz.com/quote.ashx?t=<T>`, campos «EPS/Sales Surpr.», «EPS next Q», «Earnings»), con curl y una cabecera de navegador, una petición por ticker y pausa entre ellas. Si no responde, búsqueda web con al menos dos fuentes. Cita la fuente en `sources`. Si las fuentes discrepan, usa la más citada y marca `[VERIFY]`.
   - Evalúa el informe contra el plan EP que ya está en `text.plan` del caso: ¿cumple las condiciones A/B o las de D? Escríbelo en `text.plan` y en notas.md.
4. **Otros filings materiales**: 8-K 1.01, 2.01, 3.02, 4.01, 4.02, 5.02, 8.01; 424B/S-3/S-3ASR; 13D/13G; 6-K de ASX/TSEM que no sean ventas rutinarias. Clasifícalos (catalizador, oferta o forense), puntúalos con la checklist y actualiza `supply[]`, `manual.kpis` y `text.*` con fuente. Un PR sin filing se busca en la web de la compañía.
5. **Insiders y forense**: si hay Forms 4/144/13D/13G nuevos, `python3 $S/insiders.py --filings semis/data/<T>/filings.json --ua "$SEC_USER_AGENT" --out semis/data/<T>/insiders.json` y actualiza la fila `insider` de `supply[]`. Si hay 10-Q/10-K/20-F nuevo, `python3 $S/forensic.py --cik <CIK> --ua "$SEC_USER_AGENT" --filings ... --prices ... --out semis/data/<T>/forensic.json`.
6. **Fechas de resultados**: confirma las que siguen con `[VERIFY]` en `events` (finviz «Earnings», PR de la compañía o 8-K). Si se confirma, quita el `[VERIFY]` y cita la fuente.
7. Actualiza `meta.report_date` = hoy y `meta.last_filing_seen` = último accession revisado. Añade a `semis/data/<T>/notas.md` una línea «fecha · qué cambió».
8. `python3 $S/validate.py semis/cases/<T>.json` (debe dar OK) → `python3 $S/render.py semis/cases/<T>.json semis/reports/<T>_swing.html` → commit `semis: <T> actualización <fecha>`.

## 3. Universo
1. `python3 $S/rank.py semis/cases --universe semis/universe.json --sync-peers --out-dir semis --title "Semis · ranking"` y vuelve a renderizar todos los casos (los pares cambian).
2. Diario: por cada ticker con convicción Media o Alta y un setup o EP válido hoy, añade una fila a `semis/journal.csv` (cabeceras de assets/journal_template.csv). Para filas abiertas de días anteriores, rellena el resultado a +5/+20/+60 sesiones (MFE, MAE y cierre en R) cuando ya haya datos.
3. Actualiza `semis/resumen.md`: tabla del ranking con una línea de por qué, líderes enfriados, calendario con plan EP (próximas 6–8 semanas) y la lista de `[VERIFY]` pendientes. Quita lo ya resuelto.

## 4. Cierre
1. Escribe al principio de `semis/LOG.md` una entrada con la fecha: qué tickers cambiaron y por qué, alertas de las próximas 3 sesiones (resultados, lock-ups), setups activos o invalidados y lo que quedó en `[VERIFY]`.
2. `git add` + commit (`semis: ciclo <fecha>`) + `git push`.
3. Termina con un resumen de 10 líneas como máximo: cambios en el ranking, convicción, alertas y qué necesita mi atención.

## Reglas
- Los números los calculan los scripts; el texto solo interpreta. Cada cifra lleva fuente o `[VERIFY: motivo]`. Nunca inventes consenso, precios, fechas ni pares.
- Si una regla de la skill no encaja, no la retuerzas en el texto: propón el cambio en el script y su reference, con test, en un commit aparte.
- No borres datos ni reescribas el historial de git. No toques `QRVO` (excluido).
- PARADA = escribe el motivo en `semis/LOG.md`, haz commit de lo que esté validado y termina sin seguir con el resto.
