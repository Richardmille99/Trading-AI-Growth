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
    "MOD": "Refrigeración para centros de datos y climatización comercial; separó Performance Technologies (vehículos e industria) el 1-oct-2026",
    "ETN": "Gestión eléctrica (Electrical Americas y Global), aeroespacial y movilidad (en separación); centros de datos como motor de pedidos",
    "POWL": "Equipos de distribución y control eléctrico a medida (switchgear, centros de potencia) para petroquímica, GNL, servicios públicos y centros de datos",
    "CEG": "Mayor productor de energía nuclear de EE. UU., más gas tras comprar Calpine, con contratos a largo plazo para centros de datos",
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
                "El informe del ≈ 22-oct es la prueba: solo un EP con cartera al alza cambiaría la lectura.")
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

def _evento_estimado(c, siguiente):
    """Fecha de resultados aún no anunciada: se deja la estimación de la Fase 1 con su motivo."""
    e = (c.get("events") or [{}])[0]
    return [dict(date=e.get("date"), kind="earnings", text=f"{siguiente} [VERIFY: fecha no anunciada; estimada como últimos resultados + 91 días]", src=e.get("src") or [])]


# ---------------------------------------------------------------- MOD
def mod():
    t = "MOD"
    c, rows = base(t)
    pr = casekit.link(67347, "0001104659-26-088230", "mod-20260729xex99d1.htm", "EX-99.1 8-K 29-jul-2026: resultados 1T FY27")
    sp_ = casekit.link(67347, "0001104659-26-112870", "tm2626618d1_8k.htm", "8-K 1-oct-2026: separación de Performance Technologies (fusión con Gentherm)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q1fy27", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 1T FY27: ventas $874,1M (+28%), centros de datos $348,6M (+90%) con margen bruto del 20,2% (−960 pb); reafirma la guía de FY27",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=False, guide_change=0.0,
                         note="Consenso de finviz: ventas −0,5% y BPA +18,0%. El margen de centros de datos cae 960 pb por la subida de producción. "
                              "EP: hueco del +8,6% y cierre del +8,9% con volumen 3,2×, ya devuelto.")
    kpis = [
        kp("Centros de datos", "$348,6M en el 1T FY27 (+90%); margen bruto 20,2% (−960 pb); beneficio operativo $46,3M (+33%)", "$183,7M (1T FY26)", *pr),
        kp("Climatización comercial", "$261,6M (+22%), con más baterías para centros de datos y $19,7M de compras", "$214,2M", *pr),
        kp("Separación de Performance Technologies", "Completada el 1-oct-2026: fusionada con Gentherm; los accionistas de Modine reciben el 43,6% de la sociedad combinada. Era el 32% de las ventas del 1T FY27 ($277,8M)", "—", *sp_),
        kp("FCF", "−$5,0M en el 1T FY27", "+$0,2M (1T FY26)", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 2T FY27 (primeros sin Performance Technologies)")
    text = dict(
        narrative_flags=["Tras la separación del 1-oct, Modine es casi solo centros de datos y climatización: los trimestres históricos (con Performance Technologies) no son comparables con los siguientes.",
                         "Crece mucho en centros de datos pero con el margen cayendo: está comprando volumen."],
        catalyst_read="El 1T FY27 puntúa {m.cat_q1fy27_score:sc}: +28% con desaceleración {m.accel_pp:pp}, guía solo reafirmada y margen de centros de datos a la baja; EP en el día, ya devuelto.",
        financials_note="Trimestres de XBRL hasta el 1T FY27, con Performance Technologies dentro. Desde el 2T FY27 esa división sale de las cuentas.",
        quality=["Margen bruto de centros de datos del 20,2% (−960 pb).", "FCF negativo en el 1T FY27."],
        supply_read=f"Sin ampliaciones. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, varias fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM (con Performance Technologies); PER adelantado ≈ 14 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más barato del universo por PER y ahora más puro en centros de datos, pero con el margen peor que VRT y NVT.",
        risks=["Margen de centros de datos.", "Transición tras la separación.", "Resultados ≈ 28-oct."],
        plan=["Resultados del 2T FY27 hacia el 28-oct [VERIFY: fecha no anunciada]: posiblemente ya dentro de la ventana de ≤ 3 sesiones.",
              "**EP A/B si:** centros de datos ≥ +90% con el margen recuperándose por encima del 22% y guía nueva para la Modine separada.",
              "**D si:** margen de centros de datos por debajo del 20%.",
              "Técnica: −52% desde el máximo, −29% bajo la SMA 200; RS en el percentil 0. Sin setup."],
        verdict="Centros de datos +90% y ahora más puro tras la separación, pero comprando crecimiento con margen y con la acción a la mitad de su máximo.")
    header = dict(verdict="Centros de datos +90% y separación completada; margen a la baja.",
                  setup="−52% desde máximos; sin setup.", catalyst="1T FY27: ventas −1%, BPA +18%; guía reafirmada.",
                  quality="Margen de centros de datos −960 pb.", supply="Sin ampliaciones.", group="El más barato por PER.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, sp_, fx])


# ---------------------------------------------------------------- ETN
def etn():
    t = "ETN"
    c, rows = base(t)
    pr = casekit.link(1551182, "0001551182-26-000027", "etn06302026exhibit99.htm", "EX-99 8-K 31-jul-2026: resultados 2T26")
    nb = casekit.link(1551182, "0001140361-26-007731", "ny20066192x2_424b5.htm", "424B5 mar-2026: bonos senior")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-31", "bmo",
                         "Resultados 2T26: ventas $8.531M (+21%, +14% orgánico) por encima del techo de su guía; pedidos de Electrical Americas +41%; sube la guía de crecimiento orgánico 2026 al 11–13%",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=None,
                         note="Consenso de finviz: ventas +4,6% y BPA +2,5%. La nota sube la guía orgánica sin dar la anterior en el mismo documento: sin cambio cuantificado. "
                              "Anuncia la separación de Mobility por una operación Reverse Morris Trust. El mercado abrió −0,3% y cerró +5,6%.")
    kpis = [
        kp("Pedidos y cartera", "Pedidos (media móvil de 12 meses) Electrical Americas +41%, Electrical Global +33%, Aerospace +17%; cartera total +43% interanual", "—", *pr),
        kp("Book-to-bill", "1,2 en los negocios eléctricos y en Aerospace (12 meses)", "—", *pr),
        kp("Guía 2026", "Crecimiento orgánico 11–13%; margen de segmentos 24,1–24,5%; BPA ajustado $13,40–13,60", "—", *pr),
        kp("Guía 3T26", "Orgánico 13,5–15,5%; margen de segmentos 24,6–25,0%; BPA ajustado $3,46–3,56", "—", *pr),
        kp("Deuda", "$18.520M a jun-2026 (XBRL), tras los bonos de marzo", "$9.885M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)")]
    shelf = dict(id="bonos26", kind="shelf", name="Bonos de marzo de 2026 bajo el shelf (cuatro 424B5)", shares=None, capacity_usd=None, price_basis=None, gate="live",
                 date="2026-03-09", notes="Deuda, no acciones: varias series de bonos y flotantes; la deuda casi se duplica en el año. [VERIFY: uso de los fondos (compra) en el 424B5]", src=[nb])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 3T26")
    text = dict(
        narrative_flags=["Separará Mobility (Reverse Morris Trust): Eaton quedará más concentrada en eléctrico y aeroespacial.",
                         "La deuda casi se duplica en el año ($9.885M → $18.520M) y el fondo de comercio supera al patrimonio (162%): crecimiento con compras."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +21% (+14% orgánico) con aceleración {m.accel_pp:pp}, pedidos fuertes y guía orgánica subida.",
        financials_note="Trimestres de XBRL hasta el 2T26. El beneficio operativo no sale de companyfacts con la etiqueta estándar.",
        quality=["Fondo de comercio e intangibles = 162% del patrimonio.", "FCF $874M en el 2T26 (+22%)."],
        supply_read=f"Sin ampliaciones; bonos en marzo. Ventas de directivos pequeñas ({casekit.usd_m(insider_total(t))}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 24 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El industrial grande del universo: menos puro que VRT en centros de datos, pero con pedidos eléctricos +41% y aeroespacial detrás.",
        risks=["Integración de compras y deuda.", "Separación de Mobility.", "Resultados ≈ 30-oct."],
        plan=["Resultados del 3T26 hacia el 30-oct [VERIFY: fecha no anunciada].",
              "**EP A/B si:** orgánico por encima del 15,5% (techo de la guía), BPA ajustado ≥ $3,72 (+5% sobre el consenso de $3,54) y otra subida de la guía anual.",
              "**D si:** pedidos eléctricos desacelerando.",
              "Técnica: en la SMA 200, −18% desde el máximo; RS 3m en percentil 77."],
        verdict="Industrial de calidad con pedidos eléctricos +41% y guía orgánica subida, más diversificado y con más deuda que los puros. El 30-oct medirá los pedidos.")
    header = dict(verdict="Orgánico +14%, pedidos eléctricos +41% y guía subida; deuda casi doble.",
                  setup="En la SMA 200; −18% desde máximos.", catalyst="2T26: ventas +5%, BPA +3%; guía orgánica subida.",
                  quality="Mucho fondo de comercio.", supply="Bonos, no acciones.", group="El industrial grande.")
    finish(t, c, kpis, [e], [shelf, ins], forensic_float(t), text, header, events, [pr, nb, fx])


# ---------------------------------------------------------------- POWL
def powl():
    t = "POWL"
    c, rows = base(t)
    pr = casekit.link(80420, "0000080420-26-000103", "ex991-powlq3xfy2026earning.htm", "EX-99.1 8-K 3-ago-2026: resultados 3T FY26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q3fy26", "2026-06-30", "2026-08-03", "amc",
                         "Resultados 3T FY26: ingresos $312M (+9%); pedidos récord de $934M (book-to-bill 3,0) con un pedido de centro de datos de más de $400M; cartera $2.400M (+69%)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas −1,6% y BPA −3,3% (fallo pequeño). No da guía numérica; espera mantener el margen bruto de los últimos 12 meses. "
                              "El mercado lo vendió: −12,8% en la apertura y −3,8% al cierre.")
    kpis = [
        kp("Pedidos y book-to-bill", "$934M en el 3T FY26 (book-to-bill 3,0): centro de datos > $400M (generación en el propio emplazamiento), petroquímica ≈ $75M, GNL ≈ $60M", "$362M (3T FY25)", *pr),
        kp("Cartera", "$2.400M a jun-2026 (+69% interanual, +35% trimestral)", "$1.400M (jun-2025) · $1.800M (mar-2026)", *pr),
        kp("Margen bruto", "30,6% en el 3T FY26", "—", *pr),
        kp("Capacidad", "Ampliación del astillero de Jacintoport hasta fin de FY26", "—", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 4T FY26")
    text = dict(
        narrative_flags=["El crecimiento de ingresos (+9%) va muy por detrás de los pedidos (book-to-bill 3,0): la cartera se convierte en ingresos con 1–2 años de retraso.",
                         "La familia Powell (≥ 10%) vende de forma continua fuera de planes 10b5-1."],
        catalyst_read="El 3T FY26 puntúa {m.cat_q3fy26_score:sc}: pedidos récord pero ingresos +9% y fallo pequeño frente al consenso; el mercado lo vendió.",
        financials_note="Trimestres de XBRL hasta el 3T FY26 (cierre fiscal en septiembre).",
        quality=["Sin deuda y fondo de comercio mínimo (2% del patrimonio).", "Margen bruto del 30,6%."],
        supply_read=f"Oferta limpia salvo las ventas de la familia Powell: {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 24 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El pequeño del eléctrico: la mayor aceleración de pedidos del universo (book-to-bill 3,0) con los ingresos todavía planos.",
        risks=["Conversión de la cartera en ingresos.", "Ventas de la familia Powell.", "Resultados ≈ 2-nov (cierre de FY26)."],
        plan=["Resultados del 4T FY26 hacia el 2-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos acelerando por encima del +15% con la cartera por encima de $2.400M.",
              "**D si:** ingresos planos otra vez: la cartera tardaría en llegar.",
              "Técnica: −50% desde el máximo, −22% bajo la SMA 200. Sin setup."],
        verdict="Pedidos récord (book-to-bill 3,0, cartera +69%) que aún no llegan a los ingresos (+9%), con balance limpio. Es una tesis de cartera a 12–24 meses, no un EP inmediato.")
    header = dict(verdict="Pedidos récord (book-to-bill 3,0) y cartera +69%; ingresos aún +9%.",
                  setup="−50% desde máximos; sin setup.", catalyst="3T FY26: fallo pequeño; pedidos récord.",
                  quality="Sin deuda.", supply="Familia Powell vendiendo.", group="El pequeño del eléctrico.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


# ---------------------------------------------------------------- CEG
def ceg():
    t = "CEG"
    c, rows = base(t)
    pr = casekit.link(1868275, "0001868275-26-000097", "ceg-20260806991.htm", "EX-99.1 8-K 6-ago-2026: resultados 2T26")
    sec = casekit.link(1868275, "0001104659-26-069201", "tm2615509-1_424b4.htm", "424B4 2-jun-2026: secundaria de 11,0M acciones")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-06", "bmo",
                         "Resultados 2T26: BPA operativo ajustado $2,55; sube la guía 2026 a $11,50–12,50; 920 MW más en contratos de 15–20 años; con Calpine integrada",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=None,
                         note="Consenso de finviz: ventas −2,9% y BPA +11,2%. La nota sube la guía de BPA operativo ajustado sin dar la anterior en el mismo documento. "
                              "Reacción tímida: +1,1% en la apertura y +3,4% al cierre con poco volumen.")
    kpis = [
        kp("Contratos de suministro", "920 MW más en contratos de 15–20 años con clientes con grado de inversión, desde 2029–2032", "—", *pr),
        kp("Guía 2026", "BPA operativo ajustado $11,50–12,50 (subida)", "—", *pr),
        kp("Crane (antigua Three Mile Island 1)", "FERC autoriza el traspaso de derechos de interconexión y la NRC aprueba la licencia de combustible: rearranque previsto en 2027", "—", *pr),
        kp("Deuda", "$19.474M a jun-2026 (XBRL), tras la compra de Calpine", "$7.286M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)")]
    sec_ = dict(id="sec26", kind="secondary", name="Secundaria de 11,0M acciones de los vendedores de Calpine (jun-2026)", shares=11_000_000, capacity_usd=None, price_basis=None,
                gate="dated", date="2026-06-02",
                notes="Venden accionistas recibidos en la compra de Calpine (ECP); la compañía no cobra y recompró 2,0M a los colocadores. ECP mantiene ≈ 4% (13G).", src=[sec])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 3T26")
    text = dict(
        narrative_flags=["Tras comprar Calpine, ECP y sus socios tienen acciones que pueden seguir vendiendo en secundarias.",
                         "La tesis de centros de datos se concreta en contratos de 15–20 años que empiezan en 2029–2032: no mueven los resultados de 2026."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: BPA por encima del consenso y guía subida, pero ingresos por debajo y reacción tímida.",
        financials_note="Trimestres de XBRL hasta el 2T26; la compra de Calpine (1T26) cambia la escala: deuda, ingresos y cartera no comparables con 2025.",
        quality=["Deuda casi triplicada por Calpine.", "Ingresos GAAP volátiles por coberturas."],
        supply_read="Secundaria de 11,0M acciones en junio (vendedores de Calpine), con recompra de 2,0M. ECP conserva ≈ 4%. Directivos sin ventas.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 20 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El nuclear del universo: contratos a 15–20 años con grado de inversión, más estable que VST pero con la secundaria de Calpine encima.",
        risks=["Más secundarias de los vendedores de Calpine.", "Paradas nucleares.", "Resultados ≈ 5-nov."],
        plan=["Resultados del 3T26 hacia el 5-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** BPA ≥ $3,91 (+5% sobre el consenso de $3,72), otra subida de la guía y contratos nuevos con hiperescalares con cifras.",
              "**D si:** guía mantenida y otra secundaria.",
              "Técnica: en tendencia (EMA alineadas), −34% desde el máximo; RS 1m/3m en percentil 92/100."],
        verdict="Contratos nucleares a largo plazo y guía subida, con la secundaria de los vendedores de Calpine como lastre de oferta. El 5-nov necesita contratos con cifras.")
    header = dict(verdict="Guía subida y 920 MW contratados a 15–20 años; secundaria de Calpine encima.",
                  setup="En tendencia; −34% desde máximos.", catalyst="2T26: BPA +11%, ventas −3%; guía subida.",
                  quality="Deuda triplicada por Calpine.", supply="Secundaria de 11,0M acciones.", group="El nuclear.")
    finish(t, c, kpis, [e], [sec_, ins], forensic_float(t), text, header, events, [pr, sec, fx])


if __name__ == "__main__":
    for f in sys.argv[1:] or ["fix", "vrt", "gev"]:
        globals()[f]()
        print(f, "ok")
