"""Registro reproducible de la Fase 1 manual + Fase 2 del universo infra_fisica (19-oct-2026): catalizadores con consenso,
KPIs del perfil industrial_energy (cartera, book-to-bill, margen), oferta y textos. Las cifras salen de los EX-99.1 y
10-Q citados; el consenso, de finviz (sorpresa del último informe y BPA del próximo trimestre). En modo actualización no
se vuelve a ejecutar: se edita el caso.
Uso: python infra_fisica/data/build_fase2.py [fix ...]"""
import json, os, sys

U = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(U, "..", ".claude", "skills", "growth-swing", "scripts"))
import casekit  # noqa: E402
from prices import read_csv  # noqa: E402

E = "https://www.sec.gov/Archives/edgar/data"


def kp(name, value, prior, label, url=""):
    return dict(name=name, value=value, prior=prior, src=[[label, url]])


def es(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fv(t):
    """Fuente finviz con la foto del día (consensus.py) y lo que da: sorpresa del último informe y fecha del próximo."""
    k = json.load(open(f"{U}/data/{t}/consensus.json", encoding="utf-8"))["latest"]
    return k, [f"finviz {k['date']}: sorpresa BPA {es(k['eps_surprise_pct'], 2)}% y ventas {es(k['sales_surprise_pct'], 2)}%; "
               f"BPA próximo trimestre ${es(k['eps_next_q'], 2)}", f"https://finviz.com/quote.ashx?t={t}"]


def forensic_float(t):
    """float_shares = valor de no afiliados de la portada del 10-K ÷ cierre de esa fecha (forensic.py), con nota."""
    pf = json.load(open(f"{U}/data/{t}/forensic.json", encoding="utf-8")).get("public_float") or {}
    if not pf.get("float_shares"):
        return {}
    return dict(float_shares=float(pf["float_shares"]),
                float_note=f"Portada del {pf['form']} ({pf['filed']}): {casekit.usd_m(pf['usd'])} de no afiliados a {pf['date']} ÷ cierre de "
                           f"${es(pf['close'], 2)} = {es(pf['float_shares'] / 1e6, 1)}M acciones; la portada excluye a los que trata "
                           f"como afiliados, así que es conservador")


def insider_total(t):
    return sum(o["sold_value"] for o in json.load(open(f"{U}/data/{t}/insiders.json", encoding="utf-8"))["owners"])


def base(t):
    return casekit.load(U, t), read_csv(f"{U}/data/{t}/prices.csv")


DESC = {
    "VST": "Generación eléctrica (gas, nuclear, carbón y solar) y venta minorista de electricidad, con Texas como mercado principal",
    "PWR": "Ingeniería y construcción de red eléctrica, generación y grandes instalaciones (incluidos centros de datos) en EE. UU., con compras recientes",
    "NVT": "Envolventes, conexiones y protección eléctrica, y refrigeración líquida para centros de datos",
    "FIX": "Contratista de instalaciones mecánicas y eléctricas (climatización, fontanería, electricidad, módulos prefabricados) "
           "en EE. UU.; el 59% de los ingresos del 2T26 viene de clientes de tecnología (centros de datos)",
    "VRT": "Equipos de energía y refrigeración para centros de datos (SAI, distribución eléctrica, gestión térmica y refrigeración líquida) y sus servicios",
    "GEV": "Turbinas de gas y servicios (Power), red eléctrica y conversión (Electrification, con Prolec GE desde feb-2026) y eólica (Wind)",
}


def finish(t, c, kpis, cats, supply, fl, text, header, events, sources, nonrec_items=None, adj_pct=None):
    c["manual"]["kpis"] = kpis
    c["manual"]["nongaap_recurring_items"] = nonrec_items
    c["manual"]["nongaap_adj_pct"] = adj_pct
    c["catalysts"] = cats
    c["meta"]["primary_catalyst"] = cats[0]["id"]
    c["supply"] = supply
    c["supply_context"].update(fl)
    c["text"].update(text)
    c["header"].update(header)
    c["events"] = events
    c["sources"] = sources
    c["meta"]["phase"] = "auditado"
    c["meta"]["descriptor"] = DESC[t] + ". Ingresos {m.revenue_ttm:usdM} TTM; último trimestre {m.rev_yoy:pctf} interanual."
    c["snapshot"][0] = ["Negocio", DESC[t]]
    casekit.save(U, t, c)


# ---------------------------------------------------------------- FIX
def fix():
    t = "FIX"
    c, rows = base(t)
    pr = casekit.link(1035983, "0001104659-26-086255", "fix-20260723xex99d1.htm", "EX-99.1 8-K 23-jul-2026: resultados 2T26")
    tq = casekit.link(1035983, "0001104659-26-086258", "fix-20260630x10q.htm", "10-Q 2T26 (ingresos por tipo de cliente, flujos)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-23", "amc",
                         "Resultados 2T26: ingresos $3.265,7M (+50%) y BPA $12,53 (+92%); cartera $14.060M (+73%); flujo operativo récord de $1.139M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: sorpresa de +9,3% en ingresos (≈ $2.990M implícito) y +19,9% en BPA (≈ $10,45). "
                              "La compañía no da guía: se puntúa sin sorpresa de guía. Sin partidas no recurrentes (BPA GAAP; no publica ajustado). "
                              "El mercado lo vendió pese al beat: −0,5% en la apertura y −5,3% al cierre del 24-jul.")
    kpis = [
        kp("Cartera de pedidos (backlog)", "$14.060M a 30-jun-2026 (+73% interanual, +13% trimestral); $13.700M a perímetro constante (+69%)",
           "$12.450M (31-mar-2026) · $8.120M (30-jun-2025)", *pr),
        kp("Book-to-bill (2T26, derivado)", "≈ 1,49: (cartera final − inicial + ingresos) ÷ ingresos = ($14.060M − $12.450M + $3.266M) ÷ $3.266M",
           "—", *pr),
        kp("Margen bruto (proxy del margen de proyecto)", "25,9% en el 2T26", "23,5% en el 2T25", *pr),
        kp("Clientes de tecnología (centros de datos)", "$1.917M en el 2T26, el 58,7% de los ingresos (+105% interanual)", "$934M, el 43,0% (2T25)", *tq),
        kp("Capital y caja", "Flujo operativo $1.530M en el 1S26; línea de crédito de $100M devuelta; recompras de $8,2M y dividendos de $52,8M en el 1S26",
           "Flujo operativo $164,5M en el 1S25", *tq)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-22", kind="earnings",
                   text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz; la compañía aún no la ha anunciado (el 3T25 fue el 23-oct-2025)]",
                   src=[fx])]
    text = dict(
        narrative_flags=["No da guía: el «beat» se mide solo contra el consenso de los analistas, y la cartera es la mejor señal adelantada.",
                         "El crecimiento depende cada vez más de un solo tipo de cliente: tecnología pasó del 43% al 59% de los ingresos en un año."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: crecimiento del +50% con aceleración {m.accel_pp:pp}, beat amplio (+9% en ingresos, +20% en BPA) "
                      "y margen al alza, pero sin guía y con el mercado vendiendo el informe (−5% al cierre).",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 2T26. El 4T25 se deriva como año − 9 meses con datos de la misma versión: un 10-Q de abril de "
                        "2026 etiquetaba mal el año 2025 con el valor del 1T (corregido en xbrl.py el 19-oct-2026).",
        quality=["Flujo operativo muy por encima del beneficio en el 1S26 ($1.530M frente a $812M de neto): anticipos de clientes en la facturación por avance de obra, "
                 "que pueden revertir cuando se frene la contratación.",
                 "Margen bruto al alza (23,5% → 25,9%) pese al crecimiento: no compra volumen con precio."],
        supply_read="Oferta limpia: sin convertibles ni ampliaciones, deuda mínima. Lo que pesa son las ventas de directivos: "
                    f"{casekit.usd_m(insider_total(t))} en 12 meses, casi todas fuera de planes 10b5-1 (consejero delegado, CFO y consejeros), "
                    "sin ninguna compra. Es poco frente a la capitalización ({m.mcap:usdM}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 24 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más ligado a la construcción física de los centros de datos dentro del universo; compite por la misma cartera que PWR (red) y complementa a VRT/NVT (equipos).",
        risks=["Concentración en tecnología (59% de los ingresos): una pausa del capex de los hiperescalares llega directa a la cartera.",
               "Ventas de directivos continuas fuera de plan.",
               "Mano de obra especializada: el cuello de botella de la ejecución.",
               "Resultados el ≈ 22-oct: dentro de la ventana de ≤ 3 sesiones."],
        plan=["Resultados del 3T26 el ≈ 22-oct tras el cierre [VERIFY: fecha no confirmada por la compañía]: la ventana de ≤ 3 sesiones ya está abierta, solo vale un EP.",
              "**EP A/B si:** BPA ≥ $14,10 (+10% sobre el consenso de $12,85 de finviz), cartera ≥ $15.000M (book-to-bill > 1,2) y margen bruto ≥ 25%, con hueco y volumen.",
              "**D si:** cartera plana o a la baja frente a los $14.060M de junio: el mercado ya descuenta que la contratación de centros de datos ha tocado techo.",
              "Técnica: −31% desde el máximo, bajo la SMA 50 y la 200; «líder enfriado roto». Sin setup hasta el informe."],
        verdict="Fundamentales de primera (cartera +73%, BPA +92%, caja récord) con el mercado vendiéndolo por miedo al pico del capex de IA. "
                "El informe del ≈ 22-oct es la prueba: solo un EP con cartera al alza cambiaría la lectura; la convicción sigue limitada por el régimen.")
    header = dict(verdict="Cartera +73% y BPA +92%, pero el mercado lo vende: −31% desde máximos antes de resultados.",
                  setup="−31% desde máximos, bajo la SMA 200; sin setup.",
                  catalyst="2T26: beat +9% en ingresos y +20% en BPA; cerró −5%.",
                  quality="Margen al alza; flujo de caja inflado por anticipos.",
                  supply="Limpia; ventas de directivos fuera de plan.",
                  group="El más ligado a la obra de centros de datos.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, tq, fx])


# ---------------------------------------------------------------- VRT
def vrt():
    t = "VRT"
    c, rows = base(t)
    pr = casekit.link(1674101, "0001628280-26-050323", "q22026exhibit991vrt07292026.htm", "EX-99.1 8-K 29-jul-2026: resultados 2T26")
    q1 = ["8-K 22-abr-2026: resultados 1T26 y guía anual previa", "https://www.sec.gov/Archives/edgar/data/1674101/000162828026026379/vrt-20260422.htm"]
    nb = casekit.link(1674101, "0001193125-26-071600", "d92394d424b5.htm", "424B5 25-feb-2026: bonos senior 2036–2066 ($2.100M)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 2T26: ventas $3.274M (+24%), BPA ajustado +60%; sube la guía 2026 a ventas de $14.000M (+31% orgánico) y BPA ajustado de $6,65–6,75",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=1.8,
                         note="Consenso de finviz: ventas −3,1% (fallo) y BPA +6,9%. Guía anual de ventas: punto medio de $13.750M a $14.000M (+1,8%); BPA ajustado de $6,35 a $6,70 (+5,5%). "
                              "El neto lleva un ajuste fiscal no recurrente de $39,5M (activos fiscales diferidos). El mercado lo compró: hueco del +6,4% y cierre del +2,0% con volumen 2,3×.")
    kpis = [
        kp("Guía 2026", "Ventas ≈ $14.000M (+31% orgánico, punto medio); BPA ajustado $6,65–6,75; capex ≈ 4% de las ventas", "Ventas $13.500–14.000M; BPA ajustado $6,30–6,40 (abr-2026)", *pr),
        kp("Cartera y pedidos", "La nota de resultados no los publica; la compañía habla de un entorno de demanda que «sigue creciendo» [VERIFY: cartera y book-to-bill en la presentación del 2T26]", "—", *pr),
        kp("Margen bruto", "37,7% en el 2T26", "34,0% en el 2T25", *pr),
        kp("Flujo de caja", "Operativo $1.100M (+241%) y libre ajustado $925M (+234%) en el 2T26", "—", *pr)]
    debt = dict(id="shelf26", kind="shelf", name="Shelf automático S-3ASR (19-feb-2026), usado para bonos", shares=None, capacity_usd=None, price_basis=None, gate="live",
                date="2026-02-19", notes="Sin límite de importe (emisor WKSI). Su único uso hasta hoy son bonos, no acciones: $600M al 4,85% (2036) y $500M en cada tramo de 2046, 2056 y 2066. No diluye. Registrada con un S-3ASR (shelf automático) del 19-feb.",
                src=[nb])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["La nota de resultados ya no da cartera ni book-to-bill: sin ese dato, el catalizador se mide con la guía."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: crecimiento del +24% con desaceleración {m.accel_pp:pp}, fallo en ventas frente al consenso (−3%) pero subida de la guía y del margen; el mercado lo compró en el día y lo ha devuelto después.",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión (corrige el CFO del 2T24).",
        quality=["Margen bruto al alza (34,0% → 37,7%) y caja muy por encima del beneficio en el 2T26.",
                 "Fondo de comercio e intangibles = 86% del patrimonio: crecimiento con adquisiciones."],
        supply_read=f"Sin ampliaciones de capital: lo de febrero son bonos ($2.100M). Lo que pesa son las ventas de consejeros: {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "muchas fuera de planes 10b5-1 y algunas de más de la mitad de su posición en un trimestre.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 22 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más puro del universo en centros de datos y el que más ha caído (−46% desde máximos): el mercado castiga la desaceleración del crecimiento.",
        risks=["Desaceleración: +30% en el 1T, +24% en el 2T.", "Ventas de consejeros fuertes y fuera de plan.", "Pausa del capex de IA de los hiperescalares.",
               "Resultados el 28-oct antes de la apertura."],
        plan=["Resultados del 3T26 el 28-oct antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** BPA ≥ $1,91 (+5% sobre el consenso de $1,82 de finviz), ventas sin fallo frente al consenso y guía anual de ventas por encima de $14.000M.",
              "**D si:** segundo fallo seguido en ventas o guía anual mantenida: confirmaría la desaceleración.",
              "Técnica: −46% desde el máximo, bajo la SMA 50 y la 200; RS débil. Sin setup."],
        verdict="Negocio de calidad (margen y caja al alza, guía subida) en plena corrección por la desaceleración y las ventas de consejeros. "
                "Solo un EP limpio el 28-oct cambiaría la lectura.")
    header = dict(verdict="Guía subida y caja récord, pero fallo en ventas y desaceleración: −46% desde máximos.",
                  setup="−46% desde máximos; sin setup.", catalyst="2T26: ventas −3% frente al consenso, BPA +7%, guía +1,8%.",
                  quality="Margen al alza; mucho fondo de comercio.", supply="Bonos, no acciones; consejeros vendiendo.",
                  group="El más puro en centros de datos.")
    finish(t, c, kpis, [e], [debt, ins], forensic_float(t), text, header, events, [pr, q1, nb, fx])


# ---------------------------------------------------------------- GEV
def gev():
    t = "GEV"
    c, rows = base(t)
    pr = casekit.link(1996810, "0001996810-26-000147", "gevpressrelease2q26.htm", "EX-99.1 8-K 22-jul-2026: resultados 2T26")
    tq = ["10-Q 2T26 (ganancia de $3.992M por Prolec GE)", "https://www.sec.gov/Archives/edgar/data/1996810/000199681026000148/gev-20260630.htm"]
    nb = casekit.link(1996810, "0001140361-26-003521", "ny20063664x4_424b5.htm", "424B5 3-feb-2026: bonos senior 2031–2056 ($2.600M)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-22", "bmo",
                         "Resultados 2T26: pedidos $24.200M (+88% orgánico), ventas $11.100M (+22%), cartera $176.000M; sube la guía 2026 (ventas $45.500–46.500M, FCF $11.500–12.500M)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=2.2,
                         note="Consenso de finviz: ventas +2,9% y BPA −22,1% (fallo). Guía de ventas: punto medio de $45.000M a $46.000M (+2,2%); flujo de caja libre de $7.000M a $12.000M. "
                              "El mercado vendió el informe: hueco del −5,4% y cierre del −8,7%.")
    kpis = [
        kp("Pedidos y cartera", "Pedidos $24.200M en el 2T26 (+88% orgánico; Power $16.729M, +135%); cartera total $176.000M (+$13.000M en el trimestre); Gas Power 116 GW contratados o reservados (objetivo ≥ 125 GW a fin de 2026)",
           "Pedidos 2T25: Power $7.109M", *pr),
        kp("Book-to-bill (2T26)", "≈ 2,2 (pedidos $24.200M ÷ ventas $11.100M)", "—", *pr),
        kp("Centros de datos", "Pedidos de Electrification para centros de datos > $5.000M en lo que va de 2026, más del doble de todo 2025", "—", *pr),
        kp("Margen", "EBITDA ajustado 11,3% (+340 pb orgánico); guía 12–14%. Wind sigue en pérdidas (≈ −$400M de EBITDA en 2026)", "—", *pr),
        kp("Capital", "Caja $13.100M; $3.900M devueltos a los accionistas en el año (recompras y dividendo)", "—", *pr)]
    debt = dict(id="shelf26", kind="shelf", name="Shelf automático S-3ASR (29-ene-2026), usado para bonos", shares=None, capacity_usd=None, price_basis=None, gate="live",
                date="2026-01-29", notes="Sin límite de importe (emisor WKSI). Su único uso hasta hoy son bonos, no acciones: $600M al 4,25% (2031), $1.000M al 4,875% (2036) y $1.000M al 5,5% (2056). No diluye.", src=[nb])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El neto del 1T26 ($4.745M) incluye una ganancia de $3.992M antes de impuestos por revalorizar la participación previa en Prolec GE al comprarla: no es del negocio.",
                         "El neto del 4T25 ($3.664M) también supera con mucho al operativo ($601M) [VERIFY: origen en el 10-K 2025]."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: pedidos y cartera excepcionales y guía de caja casi duplicada, pero fallo en BPA y el mercado lo vendió (−9% al cierre).",
        financials_note="Trimestres de XBRL hasta el 2T26. Caja, deuda, capex y SBC no salen de companyfacts con las etiquetas estándar: la caja ($13.100M) viene de la nota de resultados.",
        quality=["El beneficio neto TTM está inflado por la ganancia de Prolec GE ($3.992M): las métricas de margen neto y accruals hay que leerlas con eso.",
                 "Flujo operativo de $5.492M en el 2T26, muy por encima del beneficio: anticipos de clientes por la cartera (capital circulante favorable)."],
        supply_read=f"Sin ampliaciones: lo de febrero son bonos ($2.600M). Recompras en marcha. Ventas de directivos pequeñas ({casekit.usd_m(insider_total(t))} en 12 meses).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 38 (finviz), el más caro del universo. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La mayor cartera del universo ($176.000M) y la mejor visibilidad; por detrás de FIX y VRT en pureza de centros de datos.",
        risks=["Ejecución: subir la capacidad de turbinas a 20–30 GW al año.", "Wind en pérdidas.", "Valoración exigente.",
               "Resultados el 28-oct antes de la apertura."],
        plan=["Resultados del 3T26 el 28-oct antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** BPA ≥ $4,19 (+5% sobre el consenso de $3,99 de finviz), pedidos ≥ $20.000M y guía de FCF mantenida o subida.",
              "**D si:** segundo fallo de BPA con pedidos a la baja: el mercado dejaría de pagar la cartera.",
              "Técnica: −23% desde el máximo, en la SMA 200; RS 1m en percentil 77. Sin setup."],
        verdict="La mejor visibilidad del universo (cartera de $176.000M, pedidos +88%) con la valoración más alta y un fallo de BPA que el mercado castigó. El 28-oct dirá si la cartera pesa más que el margen.")
    header = dict(verdict="Pedidos +88% y cartera de $176.000M, pero fallo de BPA y la valoración más alta.",
                  setup="−23% desde máximos, en la SMA 200; sin setup.", catalyst="2T26: ventas +3%, BPA −22% frente al consenso; guía de FCF casi doble.",
                  quality="Neto inflado por Prolec GE; caja por anticipos.", supply="Bonos, no acciones; recompras.",
                  group="La mayor cartera del universo.")
    finish(t, c, kpis, [e], [debt, ins], forensic_float(t), text, header, events, [pr, tq, nb, fx])

# ---------------------------------------------------------------- PWR
def pwr():
    t = "PWR"
    c, rows = base(t)
    pr = casekit.link(1050915, "0001193125-26-324855", "d56853dex991.htm", "EX-99.1 8-K 30-jul-2026: resultados 2T26")
    nb = casekit.link(1050915, "0001193125-26-335074", "d115922d424b5.htm", "424B5 5-ago-2026: bonos senior")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-30", "bmo",
                         "Resultados 2T26: ingresos $9.557M (+41%), cartera total récord de $53.400M (RPO $33.600M); sube «significativamente» la guía 2026 a ingresos de $39.300–39.700M y BPA ajustado de $16,45–16,95",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=None,
                         note="Consenso de finviz: ventas +11,0% y BPA +28,2%. La guía sube «significativamente» con ayuda de las compras de Phalcon y Enerfab ($1.200–1.400M de ingresos en 2026); "
                              "la nota no da la cifra anterior: sin cambio de guía cuantificado. EP de verdad: hueco del +15,3% y cierre del +17,3% con volumen 2,4×.")
    kpis = [
        kp("Cartera de pedidos", "Total $53.400M y RPO $33.600M a jun-2026 (récords)", "RPO $19.160M (jun-2025) · $26.240M (mar-2026)", *pr),
        kp("Book-to-bill (2T26, sobre RPO, derivado)", "≈ 1,76: (RPO final − inicial + ingresos) ÷ ingresos = ($33.550M − $26.240M + $9.557M) ÷ $9.557M; incluye cartera de las compras", "—", *pr),
        kp("Guía 2026", "Ingresos $39.300–39.700M; BPA ajustado $16,45–16,95; EBITDA ajustado $4.090–4.210M; FCF $2.000–2.500M", "—", *pr),
        kp("Compras de 2026", "Phalcon (≈ 4.100 empleados, electricidad para centros de datos) y Enerfab (≈ 2.100, fabricación especial): $1.200–1.400M de ingresos en 2026", "—", *pr),
        kp("Recompras", "Programa nuevo de $1.000M (mayo-2026)", "$135M ejecutados en el anterior", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-29", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Parte del crecimiento y de la cartera viene de compras (Phalcon, Enerfab): el orgánico es menor que el +41%.",
                         "El consejero delegado ha vendido $120M en 12 meses, casi todo fuera de planes 10b5-1."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +41% con aceleración {m.accel_pp:pp}, beat amplio (+11% en ingresos, +28% en BPA), guía subida y EP con volumen.",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión (corrige el neto de los 4T).",
        quality=["Fondo de comercio e intangibles = 115% del patrimonio: crecimiento con compras.", "Flujo operativo récord ($1.095M) en el 2T26."],
        supply_read=f"Sin ampliaciones: bonos en agosto y recompras de hasta $1.000M. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "casi todas del consejero delegado y fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 32 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El líder del universo por nota de negocio y el único con EP reciente; la cartera ($53.400M) solo la supera GEV.",
        risks=["Integración de compras grandes.", "Ventas del consejero delegado.", "Mano de obra especializada.", "Resultados el 29-oct antes de la apertura."],
        plan=["Resultados del 3T26 el 29-oct antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 26-oct.",
              "**EP A/B si:** BPA ≥ $5,20 (+5% sobre el consenso de $4,95 de finviz), cartera por encima de $53.400M y otra subida de la guía.",
              "**D si:** cartera plana: el crecimiento dependería solo de las compras.",
              "Técnica: en tendencia (EMA alineadas), sobre la SMA 200 y −20% desde el máximo. Sin setup confirmado."],
        verdict="El mejor caso del universo: crecimiento +41%, cartera récord, guía subida y EP con volumen. Lo que vigilar son las compras y las ventas del consejero delegado.")
    header = dict(verdict="+41%, cartera récord de $53.400M y EP en julio: el líder del universo.",
                  setup="En tendencia; −20% desde máximos.", catalyst="2T26: ventas +11%, BPA +28%; guía subida; EP +17%.",
                  quality="Mucho fondo de comercio; caja récord.", supply="Bonos; CEO vendiendo.", group="Líder del universo.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, nb, fx])


# ---------------------------------------------------------------- NVT
def nvt():
    t = "NVT"
    c, rows = base(t)
    pr = casekit.link(1720635, "0001628280-26-051203", "q22026nvtpressrelease.htm", "EX-99.1 8-K 31-jul-2026: resultados 2T26")
    sh = casekit.link(1720635, "0001104659-26-108238", "tm2625115-2_424b5.htm", "424B5 16-sep-2026: folleto para ventas de accionistas")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-31", "amc",
                         "Resultados 2T26: ventas $1.471M (+53%, +47% orgánico), BPA ajustado $1,45 (+69%); sube «significativamente» la guía 2026 a crecimiento de ventas del +37–39% y BPA ajustado de $5,00–5,10",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=None,
                         note="Consenso de finviz: ventas +16,9% y BPA +25,0%. Centros de datos y productos nuevos aportan más de 30 puntos del crecimiento. La nota no da la guía anterior: sin cambio cuantificado. "
                              "El mercado abrió −0,9% y cerró +3,6%.")
    kpis = [
        kp("Crecimiento orgánico", "+47% en el 2T26; guía 2026 orgánica +32–34%", "—", *pr),
        kp("Centros de datos y refrigeración líquida", "Centros de datos y productos nuevos > 30 puntos del crecimiento; nueva ampliación de fábrica de refrigeración líquida", "—", *pr),
        kp("Guía 2026", "Ventas +37–39% (reportado); BPA ajustado $5,00–5,10", "—", *pr),
        kp("Caja", "Flujo operativo $189M (+107%) y FCF $167M (+125%) en el 2T26", "—", *pr)]
    shelf = dict(id="shelf_venta", kind="shelf", name="Folleto para ventas de accionistas existentes (sep-2026)", shares=None, capacity_usd=None, price_basis=None,
                 gate="live", date="2026-09-16",
                 notes="Permite a accionistas que se nombren en un suplemento vender acciones ordinarias; la compañía no recibe nada. [VERIFY: si hay accionistas nombrados y cuántas acciones]",
                 src=[sh])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-30", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Folleto de septiembre para que accionistas existentes vendan: posible oferta secundaria a la vista.",
                         "Directivos vendiendo con frecuencia fuera de planes 10b5-1 (11 marcados)."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +53% (+47% orgánico), beat amplio (+17% en ventas, +25% en BPA) y guía subida; reacción tibia (+3,6%).",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión. La caja no sale de companyfacts con la etiqueta estándar.",
        quality=["Fondo de comercio e intangibles = 112% del patrimonio: compras recientes.", "El flujo operativo va por debajo del beneficio en el 1S26."],
        supply_read=f"Folleto para ventas de accionistas (sep-2026) y deuda nueva (8-K 2.03 de septiembre). Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "11 marcados y muchas fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 21 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="«Líder enfriado» del universo: crece más que VRT en el 2T (+53% frente a +24%) y es más barato por PER.",
        risks=["Posible oferta secundaria.", "Ventas de directivos.", "Integración de compras.", "Resultados el 30-oct antes de la apertura."],
        plan=["Resultados del 3T26 el 30-oct antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 27-oct.",
              "**EP A/B si:** BPA ≥ $1,46 (+5% sobre el consenso de $1,39 de finviz), orgánico ≥ +30% y otra subida de la guía.",
              "**D si:** orgánico por debajo del +30% con la guía mantenida.",
              "Técnica: líder enfriado (−23% desde el máximo, en la SMA 200). Sin setup."],
        verdict="El que más crece de refrigeración (+47% orgánico) con PER razonable y señal de líder enfriado; en contra, posible secundaria y directivos vendiendo. Candidato a EP el 30-oct.")
    header = dict(verdict="+53% (+47% orgánico) y guía subida; líder enfriado con PER ≈ 21.",
                  setup="Líder enfriado; −23% desde máximos.", catalyst="2T26: ventas +17%, BPA +25% frente al consenso.",
                  quality="Mucho fondo de comercio.", supply="Folleto para secundaria; directivos vendiendo.", group="Líder enfriado.")
    finish(t, c, kpis, [e], [shelf, ins], forensic_float(t), text, header, events, [pr, sh, fx])

# ---------------------------------------------------------------- VST
def vst():
    t = "VST"
    c, rows = base(t)
    pr = casekit.link(1692819, "0001692819-26-000017", "vistra-20260630xearningsre.htm", "EX-99.1 8-K 7-ago-2026: resultados 2T26")
    nb = casekit.link(1692819, "0001140361-26-037577", "ef20082680_8k.htm", "8-K 24-sep-2026: bonos subordinados 2057 ($1.500M)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-07", "bmo",
                         "Resultados 2T26: EBITDA ajustado de operaciones $1.767M (+31%); reafirma la guía 2026 de EBITDA ajustado $6.800–7.600M; anuncia Helix Digital Infrastructure con KKR, KIA y NVIDIA",
                         [pr, fx], rev_surprise=None, eps_surprise=None,
                         guide_raise=False, guide_change=0.0,
                         note="La sorpresa de finviz (BPA −52,8%, ventas −26,5%) no se usa: el resultado GAAP lo distorsionan las coberturas, con $472M de pérdidas no realizadas en coberturas de años futuros. "
                              "La compañía mide su negocio con el EBITDA ajustado de operaciones (+31%). Reacción plana: +0,9% en la apertura y +1,6% al cierre.")
    kpis = [
        kp("EBITDA ajustado de operaciones", "$1.767M en el 2T26 (+31%); 1S26 $3.261M", "$1.349M (2T25)", *pr),
        kp("Guía 2026", "EBITDA ajustado de operaciones $6.800–7.600M y FCF antes de crecimiento $3.925–4.725M (reafirmada)", "—", *pr),
        kp("Centros de datos", "Helix Digital Infrastructure con KKR, KIA y NVIDIA; compromiso inicial de Vistra de hasta $1.000M", "—", *pr),
        kp("Deuda", "$19.595M a jun-2026 (XBRL); $1.500M en bonos subordinados 2057 en septiembre", "$15.770M (jun-2025)", *nb)]
    shelf = dict(id="shelf26", kind="shelf", name="Shelf automático S-3ASR (9-sep-2026), usado para bonos subordinados", shares=None, capacity_usd=None, price_basis=None,
                 gate="live", date="2026-09-09", notes="Sin límite de importe (emisor WKSI). Su uso hasta hoy son bonos subordinados (2057), no acciones.", src=[nb])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-06", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El beneficio GAAP y los ingresos se mueven con el valor de las coberturas: el BPA de finviz no sirve para medir la sorpresa.",
                         "La tesis de centros de datos se concreta en Helix (con NVIDIA y KKR), aún sin ingresos."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: EBITDA ajustado +31% con guía reafirmada (no subida); sin sorpresa medible por las coberturas.",
        financials_note="Trimestres de XBRL hasta el 2T26. Ingresos y neto GAAP incluyen la revalorización de coberturas: no comparables entre trimestres.",
        quality=["Resultado GAAP volátil por coberturas.", "Fondo de comercio e intangibles = 93% del patrimonio.", "Deuda al alza ($15.770M → $19.595M)."],
        supply_read=f"Sin ampliaciones: deuda subordinada en septiembre. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 15 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Generación eléctrica con exposición a centros de datos en Texas; más volátil que CEG y con más deuda.",
        risks=["Precios de la electricidad y coberturas.", "Deuda creciente.", "Resultados el 6-nov antes de la apertura."],
        plan=["Resultados del 3T26 el 6-nov antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 3-nov.",
              "**EP A/B si:** subida de la guía de EBITDA ajustado por encima de $7.600M o un contrato de suministro con un hiperescalar con cifras.",
              "**D si:** guía mantenida sin novedades de centros de datos.",
              "Técnica: en tendencia (EMA alineadas), en la SMA 200 y −30% desde el máximo."],
        verdict="Negocio que crece en EBITDA (+31%) con guía solo reafirmada y la tesis de centros de datos aún sin ingresos. El 6-nov necesita guía o contratos.")
    header = dict(verdict="EBITDA ajustado +31%, guía reafirmada; centros de datos aún sin cifras.",
                  setup="En tendencia; −30% desde máximos.", catalyst="2T26: sorpresa no medible (coberturas); guía reafirmada.",
                  quality="GAAP volátil; deuda al alza.", supply="Bonos subordinados.", group="Generación con centros de datos.")
    finish(t, c, kpis, [e], [shelf, ins], forensic_float(t), text, header, events, [pr, nb, fx])


if __name__ == "__main__":
    for f in sys.argv[1:] or ["fix", "vrt", "gev"]:
        globals()[f]()
        print(f, "ok")
