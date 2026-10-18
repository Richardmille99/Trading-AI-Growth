# Research de acciones — reglas para todas las sesiones

Idioma: español. Investigación interna; nada de esto es consejo de inversión.

## Skills
- `.claude/skills/forensic-microcap/` — forense de micro caps (dilución, float, equity lines, Nasdaq).
- `.claude/skills/growth-swing/` — growth stocks para swing: catalizadores, fundamentales, oferta, pares, convicción, ranking.
Léelas antes de trabajar. Los números los calculan los scripts; el texto solo interpreta. Nunca escribas una cifra derivada de memoria.

## Estructura de un universo (ej. `semis/`)
```
semis/
  universe.json          tickers, CIK, subgrupo, pureza, perfil, estado de cada auditoría
  data/<T>/              crudo: quarters.json (xbrl.py), prices.csv, filings.json (índice EDGAR), notas.md
  cases/<T>.json         FUENTE DE VERDAD del análisis de cada ticker
  reports/<T>_swing.html dossier renderizado
  ranking.html / .csv    salida de rank.py
  journal.csv            diario de señales (cabeceras de assets/journal_template.csv)
```

## Reglas de trabajo
- Red: SEC exige cabecera `User-Agent` con nombre y email → usa la variable de entorno `SEC_USER_AGENT`. Máximo ~5 peticiones/s y en serie si hay 503.
- Cada cifra lleva fuente (`[[etiqueta|url]]`) o `[VERIFY: motivo]`. No inventes precios, consenso ni pares.
- Emisores extranjeros (20-F / 6-K, p. ej. ASX, TSEM): no hay trimestres en XBRL; se cargan a mano desde los 6-K de resultados (y ventas mensuales en Taiwán), indicando IFRS o US GAAP.
- `meta.report_date` = fecha de corte. `meta.last_filing_seen` = último accession revisado. `universe.json → tickers[].status` ∈ `pendiente` / `fundamentales` / `auditado` / `revisar`.
- **Modo actualización** (ticker ya auditado): no rehagas nada. Lee el caso, lista los filings posteriores a `last_filing_seen` y los PRs posteriores a `report_date`, añade solo lo nuevo (trimestre, catalizadores, oferta, insiders), recalcula, re-renderiza y escribe en `data/<T>/notas.md` un registro «fecha · qué cambió».
- Al terminar cada ticker: `validate.py` OK → `render.py` → `git add` + commit (`semis: <T> <fase> <fecha>`) + push. Lo que no está en git se pierde al cerrarse la sesión.
- Si una regla de la skill no encaja (p. ej. perfil sectorial), no la retuerzas en el texto: propón el cambio en el script y en su reference, con test.
