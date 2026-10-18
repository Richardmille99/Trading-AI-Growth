# Dilución y oferta en growth stocks

En growth la dilución rara vez viene de equity lines tóxicas. Viene de la compensación en acciones, de la colocación que sigue a una subida y de los bloques que se desbloquean. Para un swing lo decisivo es **cuánto papel puede venderse encima de tu entrada durante las próximas semanas**.

## 1. Fuentes de oferta que se registran (`case.json → supply[]`)

| `kind` | Qué mirar | Fuente |
|---|---|---|
| `atm` | Programa ATM: tamaño, agente, cuánto queda, ventas del último trimestre | 424B5, 10-Q (notas de patrimonio), 8-K |
| `shelf` | S-3/F-3 efectivo: capacidad restante; baby shelf I.B.5 si el float < $75M | EDGAR (EFFECT, 424B) |
| `secondary` | Oferta reciente o probable: precio, tamaño, vendedores (compañía o accionistas) | 424B4/B5, 8-K, PR |
| `convertible` | Precio de conversión, cap/floor, call, settlement en acciones; hedge de cobertura | 8-K, indenture |
| `warrants` | Strike, número, cashless, reset | 8-K, 10-Q |
| `lockup` | Fecha de fin de lock-up (IPO, SPAC, PIPE, secundaria) y acciones afectadas | Prospecto (Underwriting / Shares eligible for future sale) |
| `insider` | Forms 4 y 144: ventas, planes 10b5-1, tamaño frente al volumen | EDGAR Forms 4/144 |
| `sbc` | Concesiones anuales, RSUs que devengan en el trimestre | 10-K/10-Q, proxy |
| `pipe_resale` | Reventa registrada de un PIPE: precio base del inversor | S-1/S-3 de reventa |

Cada entrada: `shares`, `price_basis` (precio de entrada del vendedor, si se sabe), `gate` (`live` / `gated` / `dated`), `date` (para lock-ups y vencimientos), `notes`, `src`.

## 2. Reglas

- **Shelf efectivo + ATM con capacidad = oferta viva.** Penaliza la nota de oferta aunque la empresa tenga caja.
- **Secundaria en los 30 días tras un EP** es el patrón típico: si la caja es baja (runway < 18 meses) o la empresa ya usó el ATM en el trimestre, la probabilidad es alta. Se marca `RIESGO DE COLOCACIÓN`.
- **Lock-up dentro del periodo de tenencia** (las próximas 6–8 semanas) se marca y se compara con el float.
- **Insiders:** ventas fuera de plan 10b5-1 o > 10% de su posición en un trimestre se marcan. Compras en mercado abierto suman.
- **Precio base de los vendedores** (secundaria, PIPE, convertible, warrants): son niveles de oferta en el gráfico.
- La mecánica de base actual tras splits, Rule 144 y elegibilidad F-3/S-3 es la misma que en la skill `forensic-microcap` (methodology §2–§5).

## 3. Nota de oferta (`scripts/compute.py`)

Empieza en 100 y resta: ATM con capacidad viva −25 · shelf efectivo sin ATM −10 · `RIESGO DE COLOCACIÓN` −20 · lock-up en ventana > 10% del float −20 (5–10% −10) · ventas de insiders marcadas −10 · convertibles con conversión posible en ventana −10 · dilución neta > 5% interanual −10 · SBC > 20% −5. Nota: ≥ 75 limpia · 50–74 vigilar · < 50 pesada.
