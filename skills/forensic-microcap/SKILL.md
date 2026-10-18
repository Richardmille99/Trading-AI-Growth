---
name: forensic-microcap
description: Plantilla y procedimiento por defecto para informes forenses de micro caps (dilución, float, equity lines, warrants, shelf, reventas, cumplimiento Nasdaq, pump and dump, contrapartes). Úsala cuando el usuario pida analizar un ticker de forma forense o un informe de dilución y oferta.
---

# Informe forense de micro caps

Cada análisis produce **dos cosas**: un `case.json` con todos los datos y sus fuentes, y una página HTML generada desde ese caso con la estructura fija de 12 secciones. Los números derivados los calcula `scripts/compute.py`; el texto nunca hace aritmética de memoria.

Archivos:
- `references/methodology.md` — reglas (base actual, float, gates, Rule 144, F-3 I.A.3/I.B.1/I.B.5, Nasdaq sin cura, caja, firmas, rúbrica). **Léelo antes de empezar.**
- `references/schema.md` — campos del caso, markup de texto y métricas disponibles.
- `examples/BIYA_0001944712.json` — caso completo de referencia; copia su forma.
- `scripts/compute.py` · `scripts/validate.py` · `scripts/render.py` · `assets/report.css` · `assets/charts.js`.

## Procedimiento

1. **Arranca con la lista de tareas** (reunir filings, contratos, precios/PRs, construir caso, validar y renderizar, publicar).
2. **Índice de filings con hora.** `WebFetch https://data.sec.gov/submissions/CIK<10 dígitos>.json` (horas en UTC → pasar a ET). Si el índice va retrasado, `https://efts.sec.gov/LATEST/search-index?q="<emisor>"&ciks=<cik>&startdt=...&enddt=...` lista filings y exhibits recientes. `browse-edgar` está bloqueado por robots; no insistir.
3. **Documentos.** `https://www.sec.gov/Archives/edgar/data/<cik>/<accession sin guiones>/<archivo>`. Los prospectos largos se truncan: lee primero portadas (O/S, no afiliados, precio, I.B.5) y luego exhibits sueltos (EX-99.1 estados financieros con notas de equity, préstamos, partes vinculadas y hechos posteriores; EX-10.x contratos). La carpeta del accession da la hora exacta de aceptación. Si SEC devuelve 503, espera y lanza las peticiones de una en una.
4. **Contratos de cada instrumento.** Para cada ELOC/SESA, warrant, nota, SPA, acuerdo 3(a)(10), S-8 y reventa: contraparte, fecha, tamaño en acciones y dólares, fórmula de precio, floor, techo, blocker, plazo, registro y estado (EFFECT), uso hasta hoy. Ajusta todo a base actual.
5. **Mercado y PRs.** 20 sesiones de cierre y volumen, cierre previo, máximo de 60 días, sesiones extremas; PRs y halts con hora. Busca las yuxtaposiciones de la metodología.
6. **Personas y contrapartes.** Holders (13D/13G, tabla de beneficiarios), directivos y cambios, auditor y cambios, underwriter, compradores de filiales, prestatarios. Marca con `[VERIFY]` cualquier UBO o relación no publicada.
7. **Construye `casos/<TICKER>_<CIK>.json`** copiando la forma del ejemplo. Números derivados como `{m.clave}`; números de filings con `[[etiqueta|url]]`; huecos y contradicciones con `[VERIFY: motivo]`. Calificaciones con la rúbrica de la metodología.
8. **Valida y renderiza:**
   ```bash
   python scripts/compute.py casos/X.json     # revisa las métricas
   python scripts/validate.py casos/X.json    # debe terminar en OK
   python scripts/render.py casos/X.json X_forensic.html
   ```
   Abre la página una vez (captura o vista previa) y revisa los dos gráficos y el ancho móvil.
9. **Publica** la página como artifact (título `<TICKER> Forensic File`). En el chat: una frase de qué es la página, los hallazgos que cambian la lectura y los VERIFY principales. Guarda o entrega también el `case.json`.

## Estructura fija del informe

§0 cabecera (Mixto · Vivo hoy · Bloqueado hasta · Actores · Cambia el cuadro) + siete calificaciones + alerta · §1 Snapshot · §2 O/S histórico y FD (log) y §2.1 oferta por precio + ledger de gates · §3 capital: 3.1 registros, 3.2 facilidades, 3.3 warrants, 3.4 convertibles, 3.5 ofertas completadas · §4 timeline · §5 caja · §6 cumplimiento · §7 legal · §8 nexo y gobierno · §9 propiedad y reconciliación del float · §10 catalizadores · §11 catalizador de hoy · §12 lente del CEO, escalera del trader y veredicto · fuentes.

No cambies la estructura por caso: si una sección no aplica, dilo en una frase (p. ej. «Ninguno declarado»). Si un instrumento no encaja en los modelos de oferta, añade el modelo en `compute.py` (con su fórmula documentada en el docstring) en vez de calcular a mano.

## Reglas de contenido

- Nunca afirmes fraude o manipulación; describe mecánicas y coincidencias documentadas.
- Cita solo páginas abiertas. Lo que no se pudo leer va con `[VERIFY]`.
- Español, frases cortas, miles con «.» y decimales con «,»; fechas absolutas; horas en ET.
- Investigación interna; no es consejo de inversión (el pie lo dice).
