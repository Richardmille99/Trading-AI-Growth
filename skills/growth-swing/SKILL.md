---
name: growth-swing
description: Dossier de growth stocks para swing trading de semanas a meses (Qullamaggie, Stockbee, Oliver Kell). Verifica catalizadores (contratos públicos, productos, financiación, partnerships), audita fundamentales y calidad del beneficio, mide dilución y oferta, compara con el grupo y saca convicción, tamaño y horizonte. Úsala cuando el usuario pida analizar una growth stock, un catalizador o un EP, o comparar una acción con su tema o industria.
---

# Dossier growth-swing

Cada análisis produce un `case.json` con datos y fuentes y una página HTML con 10 secciones fijas. Los scripts hacen todos los cálculos y las notas; el texto solo interpreta. La entrada la da el precio: esta skill decide **convicción, tamaño y horizonte**. Es investigación, no consejo de inversión.

Archivos:
- `references/catalysts.md` — taxonomía, checklist, puntuación, topes y señales narrativas. **Léelo antes de puntuar un PR.**
- `references/fundamentals.md` — etiquetas XBRL, métricas, banderas de calidad, DCF inverso, nota de fundamentales, pares.
- `references/dilution_supply.md` — fuentes de oferta y nota de oferta.
- `references/swing.md` — régimen, setups, matriz de convicción, eventos y diario de calibración.
- `references/schema.md` — campos del caso, markup y métricas.
- `examples/EXMP_synthetic.json` — caso **sintético** completo; copia su forma, nunca sus cifras.
- `scripts/xbrl.py` · `catalysts.py` · `fundamentals.py` · `compute.py` · `validate.py` · `render.py` · `rank.py` (ranking de un universo de casos) · `tests/test_engines.py`.
- `assets/sector_profiles.json` · `assets/journal_template.csv` · `assets/report.css` · `assets/charts.js`.

## Procedimiento

1. **Lista de tareas**: perfil, fundamentales, catalizadores, oferta, pares, setup, caso, validar y renderizar, publicar, diario.
2. **Perfil sectorial.** Elige la clave de `sector_profiles.json` (`saas`, `semis_fabless`, `semis_idm`, `semis_manufacturing`, `ai_systems`, `semis_hardware`, `defense_gov`, `biotech_commercial`, `consumer`, `industrial_energy`, `fintech`, `generic`). Define el margen objetivo del DCF inverso, los pesos de la nota y los KPIs manuales que hay que buscar.
3. **Fundamentales.**
   - Con red hacia la SEC (Claude Code en local): `python scripts/xbrl.py --cik <cik> --ua "Nombre email" --out q.json` y copia `quarters` y `shares_out` al caso.
   - Sin red desde el shell: lee las tablas de los 10-Q/10-K o del EX-99.1 con WebFetch y escribe los trimestres a mano con el mismo formato (flujos discretos; deriva el Q4 como anual − 9 meses y discretiza el CFO acumulado). Marca con `[VERIFY]` lo que no salga de un filing.
   - KPIs del perfil en `manual.kpis` con su fuente.
4. **Catalizadores** (últimos 6–12 meses y los de hoy). Por cada PR:
   - Abre el 8-K y sus exhibits.
   - Busca a la contraparte. Para contratos públicos usa USASpending, SAM.gov y los anuncios diarios del DoD; distingue valor obligado de techo IDIQ.
   - Mira qué filing vino después: 424B, S-3, Form 4 y 144, lock-ups.
   - Rellena todos los campos de la checklist.
   - No subas una nota a mano: si el texto contradice la nota, corrige los datos de entrada, no la nota.
5. **Oferta.**
   - ATM: capacidad restante y ventas por trimestre (notas de patrimonio del 10-Q).
   - Shelf efectivo, warrants y convertibles con precio y fecha.
   - Lock-ups con fecha y acciones.
   - Forms 4 y 144: marca las ventas fuera de plan o mayores del 10% de la posición.
   - Float de no afiliados de la portada.
   - Si hay splits, reverse splits o equity lines, aplica `forensic-microcap` (base actual, Rule 144, baby shelf).
6. **Pares.**
   - Usa 4–8 compañías del mismo tema o industria.
   - Calcula sus métricas con el mismo método y la misma fecha de precio.
   - Sin datos de precio, `rs_3m` y `ev_sales` quedan `null` y la posición sale `unknown`.
7. **Setup y régimen.**
   - Con datos de precio: pivote, stop, ADR%, RS y EMAs.
   - Sin ellos: déjalos en `null`; el informe lo muestra y la convicción no puede ser Alta.
8. **Construir y comprobar.**
   - `python scripts/validate.py case.json` debe dar OK; lee los avisos.
   - `python scripts/render.py case.json <TICKER>_swing.html`.
   - Si tocas los scripts: `python tests/test_engines.py`.
9. **Publicar.**
   - Carga la skill de diseño de artifacts y publica el HTML como artifact (icono `chart`).
   - Resume en una línea la convicción y lo que la limita.
10. **Universo.** Con varios casos del mismo tema: `python scripts/rank.py <carpeta_casos> --universe universe.json --sync-peers` (pares = el resto del universo) y publica `ranking.html`.
11. **Diario.** Añade una fila al diario del usuario (cabeceras en `assets/journal_template.csv`) con las notas del día. Sin seguimiento de resultados a +5/+20/+60 sesiones, las notas no están calibradas: recuérdalo cuando se acumulen señales.

## Estructura fija del dossier

§0 Veredicto (convicción y tamaño + tiles Setup / Catalizador / Calidad / Oferta / Grupo) · §1 Snapshot · §2 Catalizadores · §3 Fundamentales · §4 Calidad del beneficio · §5 Dilución y oferta · §6 Valoración y expectativas · §7 Grupo y pares · §8 Precio y setup · §9 Riesgos y eventos · §10 Plan y veredicto · Fuentes.

## Reglas de criterio

- Un PR vale lo que se puede verificar fuera del emisor. Techo ≠ ingreso; MOU ≠ contrato; «seleccionada» ≠ adjudicada con fondos.
- PR seguido de financiación con descuento en ≤ 10 días se trata como herramienta de colocación, no como catalizador.
- La confirmación de mercado se muestra aparte. Un catalizador D con mercado fuerte es una operación táctica, no una tesis.
- Buenos fundamentales no garantizan revalorización. La convicción exige catalizador, calidad, oferta limpia y liderazgo en el grupo a la vez, dentro del régimen.
- Cada cifra lleva fuente o `[VERIFY]`. Nunca inventes datos de precio, consenso o pares. Para probar la plantilla usa solo casos marcados `synthetic: true`.
