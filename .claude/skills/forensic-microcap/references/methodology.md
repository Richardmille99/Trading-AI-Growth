# Metodología forense — reglas que el informe aplica

Cada regla dice qué calcular, de dónde sale el dato y cómo se marca lo que falta.

## 1. Datos y fuentes

| Dato | Fuente primaria | Notas |
|---|---|---|
| Índice de filings con hora | `https://data.sec.gov/submissions/CIK##########.json` (`acceptanceDateTime`, UTC) | Puede ir retrasado: completar con EDGAR full-text search `efts.sec.gov/LATEST/search-index?q=...&ciks=...&startdt=...` |
| Documentos | `https://www.sec.gov/Archives/edgar/data/<cik>/<accession sin guiones>/<doc>` | Los documentos largos se truncan al leerlos: leer exhibits (EX-99.1, EX-10.x) y portadas por separado; el índice de la carpeta da la hora de aceptación |
| O/S y no afiliados | Portada del último F-3/S-1/20-F/10-K, balance más reciente | Si hay varios denominadores en un mismo filing, usar el más reciente fechado y listar los demás en `os_alternates` con [VERIFY] |
| Instrumentos | Exhibits del 6-K/8-K de cada transacción, 424B3, prospectos de reventa | Extraer fórmula de precio, floor, techo, blockers, plazo, contraparte |
| Precios diarios | stockanalysis.com/stocks/<t>/history/, investing.com | Cierre previo = base de todo el informe |
| PRs con hora | GlobeNewswire, PR Newswire, Accesswire, TheFly (halts) | La hora importa para las yuxtaposiciones |
| Holders | 13D/13G, Forms 3/4/144, tabla de beneficiarios del prospecto | FPI: Forms 3/4 pueden no existir |

Nunca citar un dato que no se haya leído en la fuente. Lo que no se pudo leer o se contradice va con `[VERIFY: motivo]`.

## 2. Base actual (splits)

- Todo recuento y precio se expresa en base actual: conteo bruto ÷ producto de los ratios de los splits posteriores a su fecha.
- Las clases que no consolidaron (p. ej. Class B) no se dividen.
- Comprobar que el prospecto ajustó el precio y el número del instrumento; si no, marcarlo como contradicción.

## 3. Float

- Float = O/S de la clase cotizada − afiliados (cifra del emisor en la portada del F-3/S-1 si existe).
- Restar también bloques restringidos sin registro ni 144 abierto.
- Rechazar proveedores que sumen clases no cotizadas o usen un O/S antiguo; explicar la diferencia en `float_recon`.

## 4. Oferta (supply) y gates

Cada instrumento lleva un `gate`:

| gate | Significado | Entra en |
|---|---|---|
| `live` | Puede imprimirse hoy sin evento externo (registro efectivo, 3(a)(10), 144 abierto) | «Imprimible hoy» |
| `gated` | Espera EFFECT, reloj 144, financiación, conversión, concesión | «Bloqueado» |
| `price` | Solo se activa por encima/debajo de un precio | «Bloqueado» con marca de precio |
| `issued` | Ya en el O/S, riesgo de venta y no de dilución | Ledger, no FD |

Modelos de oferta (`supply.model`), todos calculados por `compute.py`:
- `fixed`: número fijo (con banda `shares_min`–`shares_max` cuando el uso es desconocido).
- `shelf_ib5`: baby shelf = 1/3 del public float valorado al máximo de 60 días, convertido en acciones al precio p.
- `dollars_discount`: dólares ÷ (descuento × max(p, floor)), con techo de precio y de acciones (ELOC, notas con floor).
- `cashless_bs`: warrant cashless con valor Black-Scholes calculado con el strike como subyacente; acciones = warrants × BS ÷ max(p, floor).

Rule 144 (emisor reportante): 6 meses desde el pago completo; afiliados con límite de volumen (mayor de 1% del O/S o la media de 4 semanas); conversiones y cashless heredan (tack) la fecha del instrumento original.

## 5. Capacidad de registro (Form F-3 / S-3)

- I.A.3 (puntualidad): todos los informes en plazo 12 meses (un 12b-25 dentro de la prórroga cuenta como en plazo). Leer también la casilla de la portada del informe anual.
- I.B.1: public float ≥ $75M → sin tope. Precio necesario = $75M ÷ no afiliados.
- I.B.5 (baby shelf): ventas primarias en 12 meses ≤ 1/3 del public float, valorado al cierre más alto de los 60 días previos a la venta. El tope en acciones sube cuando el precio cae por debajo de ese máximo.
- Shelf caduca a los 3 años del EFFECT; §10(a)(3) se re-testea con cada informe anual.

## 6. Nasdaq

- Bid ≥ $1 (5550(a)(2)); 30 sesiones seguidas debajo = aviso.
- Sin periodo de cura (5810(c)(3)(A)(iv)) si: reverse split en los 12 meses previos, o splits acumulados ≥ 250:1 en dos años. Calcular ambas fechas de fin.
- Patrimonio ≥ $2,5M; MVPHS ≥ $1M (línea de precio = $1M ÷ no afiliados); MVLS como alternativa.
- Calcular el colchón: 1 − 1/precio.

## 7. Caja

- Caja publicada + dos ritmos de consumo: flujo operativo (caja) y pérdida antes de capital circulante (pérdida − no monetarios).
- Pro forma a la fecha del informe con los meses transcurridos; runway en ambos ritmos.
- Listar obligaciones no netadas (sweeps, depósitos, true-ups, vencimientos) y cobros esperados.

## 8. Firmas y yuxtaposiciones

- **Firma de captación:** split seguido de papel nuevo (ELOC, RD, notas, shelf) en ≤ 9 semanas. Contar n de N.
- **Yuxtaposiciones:** filing o PR fuera de horario → sesión siguiente con volumen ≥ 10× la mediana; F-3/reventa → bombeo; exención de lock-up → caída; salida de caja (préstamos, compras) → split.
- **Repetición de noticias:** comparar previsiones y claims de PR con las cifras posteriores en los filings.
- **Ida y vuelta:** adquisición pagada con acciones seguida de venta en efectivo al mismo tercero o a uno recurrente.

## 9. Rúbrica de calificación

Seis componentes, nivel Alto / Medio / Bajo, con una frase de motivo que cite el número:

| Componente | Alto | Medio | Bajo |
|---|---|---|---|
| Oferta flotante | Imprimible hoy ≥ 25% del float o bloque gated ≥ 50% del float | 10–25% | < 10% |
| Dilución | O/S × ≥ 3 en 12 meses | × 1,5–3 | < × 1,5 |
| Frecuencia | ≥ 4 eventos de capital (financiaciones, S-8, splits) en 12 meses | 2–3 | ≤ 1 |
| Capacidad de oferta | Ruta registrada sin tope efectivo (≥ $10M disponible hoy) | Ruta viva pero capada o pendiente de EFFECT | Ninguna ruta |
| Necesidad de caja | Runway < 6 meses o going concern | 6–12 meses | > 12 meses |
| Cumplimiento | Aviso abierto sin cura o bid < $1 | Cumple pero sin periodo de cura / colchón < 30% | Cumple con margen |

Riesgo global = Alto si hay ≥ 3 Altos; Medio si Altos + Medios ≥ 3; si no, Bajo. Cuando falta un dato, elegir el grado más arriesgado de los adyacentes y decirlo en `grades_note`.

## 10. Estilo del texto

- Español, frases cortas, números con unidad y fecha. Separador de miles «.» y decimal «,».
- No afirmar fraude ni manipulación: describir mecánicas y coincidencias documentadas.
- Cada afirmación con número lleva su fuente (`[[etiqueta|url]]`) o se calcula en `compute.py` (`{m.clave}`).
