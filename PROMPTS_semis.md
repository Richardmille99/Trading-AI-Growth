# Prompts para Claude Code (web) — universo semiconductores

Cuatro prompts: copia cada uno en una sesión nueva sobre tu repo, en este orden. Entre una fase y la siguiente, haz merge de la rama que deja la sesión, para que la siguiente parta de lo ya hecho.

---

## PROMPT 1 · Preparación + fundamentales de todo el universo + ranking preliminar

```
Lee CLAUDE.md y semis/universe.json. Vamos a auditar el universo de semiconductores con las skills growth-swing y forensic-microcap.

FASE 0 — Preparación (sin pedirme confirmación)
1. Si existe skills/, mueve skills/forensic-microcap y skills/growth-swing a .claude/skills/. Ejecuta python .claude/skills/growth-swing/tests/test_engines.py; debe pasar.
2. Comprueba la red: con curl y la cabecera User-Agent de $SEC_USER_AGENT, pide https://www.sec.gov/files/company_tickers.json, saca el CIK de MRVL y pide https://data.sec.gov/submissions/CIK<10 dígitos>.json; prueba también una descarga de precios diarios (prueba https://stooq.com/q/d/l/?s=mrvl.us&i=d y, si falla, https://query1.finance.yahoo.com/v8/finance/chart/MRVL?range=2y&interval=1d). Dime qué funciona. Si la SEC no responde, para y dime que añada los dominios al entorno.
3. Escribe .claude/skills/growth-swing/scripts/prices.py, con un test con CSV sintético en tests/:
   - Descarga 2 años de OHLCV diario de cada ticker y de SMH, SOXX, QQQ e IWM a semis/data/<T>/prices.csv.
   - Calcula ADR% de 20 sesiones, EMAs 10/20/50, SMA 200, máximo de 52 semanas y caída desde él.
   - Calcula la rentabilidad a 1, 3, 6 y 12 meses y su percentil RS dentro del universo + ETFs.
   - Calcula la etiqueta cooled_leader de references/swing.md §6.
   - Rellena setup.rs_1m/rs_3m/rs_6m, adr_pct, ema_stack y cooled_leader en cada caso.
   - Deja pivot y stop en null salvo que haya un setup claro según swing.md §2. En ese caso, propón tipo, pivote y stop y explícalo en setup.notes.
   Añade las funciones a SKILL.md y a references/schema.md.

FASE 1 — Fundamentales y clasificación (todos los tickers con status "pendiente")
Para cada ticker:
a) CIK desde https://www.sec.gov/files/company_tickers.json; índice de filings en semis/data/<T>/filings.json.
b) Trimestres:
   - Emisores con 10-Q: python scripts/xbrl.py --cik … --ua "$SEC_USER_AGENT" → semis/data/<T>/quarters.json (12 trimestres). Revisa a mano el último trimestre contra el 10-Q o el EX-99.1.
   - ASX y TSEM: no hay trimestres en XBRL. Cárgalos desde los 6-K de resultados, con la misma estructura y la fuente en cada trimestre. ASX publica ventas mensuales: guárdalas aparte.
   - CBRS: usa el S-1/424B4 y los 10-Q posteriores. Marca [VERIFY] lo que no tenga trimestre comparable.
   - SWKS: Qorvo entra desde el 5-oct-2026. Busca cifras pro forma combinadas (8-K, S-4, presentación) y explica en financials_note qué trimestres son comparables.
c) Pureza: lee la nota de segmentos y desagregación de ingresos del último 10-K/20-F. Calcula el % de ingresos por chips propios frente a módulos, cables, sistemas, nube o servicios de fabricación. Actualiza subgroup, purity y purity_pct en universe.json si mi clasificación preliminar es incorrecta, y explica por qué.
d) KPIs del perfil (sector_profiles.json) desde el 10-Q, la presentación o el transcript, con fuente.
e) Próxima fecha de resultados: anuncio oficial de la compañía (PR u 8-K). Si no está anunciada, ponla como estimada con [VERIFY]. Va en events.
f) Construye semis/cases/<T>.json:
   - meta.report_date = hoy y meta.last_filing_seen.
   - catalysts vacíos por ahora, salvo los resultados del último trimestre (tipo earnings, con los datos que haya; sorpresa vs consenso = null y [VERIFY: sin consenso]).
   - supply: solo lo que salga del 10-Q/10-K (recompras, shelf, convertibles). Lo completo va en la Fase 2.
   - Valida y renderiza. status = "fundamentales". Commit por ticker.
Al final: python scripts/rank.py semis/cases --universe semis/universe.json --sync-peers --out-dir semis --title "Semis · ranking preliminar".

Para y entrégame:
- la tabla del ranking;
- por subgrupo, 3 líneas sobre quién lidera en crecimiento, aceleración y calidad, y quién está «líder enfriado»;
- las banderas de calidad activas;
- el calendario de resultados ordenado por fecha;
- qué datos quedaron en [VERIFY].
No empieces la Fase 2.
```

---

## PROMPT 2 · Auditoría completa de un ticker (una sesión por ticker; puedes lanzar varias en paralelo)

Orden recomendado: los que publican resultados antes primero, para tener la auditoría lista antes del informe.

```
Lee CLAUDE.md, semis/universe.json y semis/cases/<TICKER>.json. Haz la auditoría completa de <TICKER> con la skill growth-swing (y forensic-microcap donde aplique) partiendo del caso existente; no rehagas los fundamentales salvo error.

1. Catalizadores de los últimos 12 meses: todos los PRs de la compañía y los 8-K (Items 1.01, 2.01, 2.02, 7.01, 8.01) o 6-K.
   - Clasifícalos y rellena la checklist completa de references/catalysts.md.
   - Comprueba qué publica la contraparte: hyperscalers, OEMs, gobierno (USASpending, SAM.gov, DoD Contracts, CHIPS Act).
   - Mira qué vino después de cada PR: 424B, S-3, Forms 4/144, lock-ups.
   - Aplica las señales narrativas de §7: narrativa de IA sin ingresos detrás, «design wins» sin fecha de producción, pipeline presentado como backlog.
2. Oferta:
   - Recompras activas y su uso real.
   - Shelf, ATM, convertibles (precio de conversión, call spreads, liquidación en acciones), warrants.
   - Lock-ups: en CBRS, el calendario exacto del prospecto, incluidas las liberaciones anticipadas.
   - Acciones emitidas en fusiones (SWKS: las acciones de ex-accionistas de Qorvo y quién las tiene).
   - Forms 4 y 144 de 12 meses: marca las ventas fuera de plan 10b5-1 o > 10% de la posición.
   - Grandes tenedores (13D/13G/13F) y float de no afiliados.
3. Forense de compañía grande:
   - concentración de clientes ≥ 10% y su evolución;
   - partes vinculadas;
   - cambios de auditor o de CFO, debilidades materiales, reexpresiones;
   - fondo de comercio e intangibles frente a patrimonio, deterioros;
   - diferencia GAAP vs non-GAAP y partidas «no recurrentes» repetidas;
   - inventario en canal y días de inventario;
   - litigios materiales;
   - para ADR/FPI, la estructura (ADR ratio, accionistas de control, holding).
   Todo con fuente.
4. Setup y plan con prices.csv:
   - ¿Hay setup válido hoy? Si los resultados caen en ≤ 3 sesiones, la matriz descarta los setups que no sean EP: dilo.
   - Escribe el plan para el día de resultados: qué tiene que pasar en el informe (crecimiento, aceleración, guía, margen, KPI clave) para que un gap sea un EP de calidad A/B y qué lo convertiría en D.
5. Textos del caso (header, text.*) con markup y fuentes. validate.py OK, render.py, status = "auditado", meta.last_filing_seen actualizado.
6. Re-ejecuta rank.py con --sync-peers. Commit y push.
Resume en 10 líneas: convicción y qué la limita, catalizador principal y su nota, banderas, oferta en ventana, fecha y plan de resultados.
```

---

## PROMPT 3 · Ranking final y plan de temporada de resultados

```
Lee CLAUDE.md y todos los casos de semis/cases/. Comprueba que todos están en status "auditado"; si alguno no, dime cuál y para.
1. Actualiza precios (prices.py) y recalcula setups.
2. python scripts/rank.py semis/cases --universe semis/universe.json --sync-peers --out-dir semis --title "Semis · ranking".
3. Escribe semis/resumen.md:
   - ranking con una línea de por qué cada uno está donde está;
   - comparación dentro de cada subgrupo;
   - los «líderes enfriados» con fundamentales intactos;
   - el calendario de resultados con el plan EP de cada uno;
   - lo que sigue en [VERIFY].
4. Añade a semis/journal.csv una fila por cada ticker con convicción Media o Alta.
Commit y push.
```

---

## PROMPT 4 · Actualización (cuando vuelvas a un ticker ya auditado)

```
Lee CLAUDE.md y semis/cases/<TICKER>.json. Modo actualización: lista los filings posteriores a meta.last_filing_seen y los PRs posteriores a meta.report_date.
- Añade solo lo nuevo: trimestre (xbrl.py o 6-K), catalizadores, oferta, Forms 4.
- Si el nuevo informe de resultados es un catalizador, puntúalo con su reacción de mercado.
- Recalcula, re-renderiza y re-ejecuta rank.py.
- Registra «fecha · qué cambió» en semis/data/<TICKER>/notas.md.
Commit y push. Resume qué ha cambiado en la nota y la convicción.
```
