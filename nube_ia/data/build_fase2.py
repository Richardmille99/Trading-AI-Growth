"""Registro reproducible de la Fase 1 manual + Fase 2 del universo nube_ia (19-oct-2026): catalizadores con consenso,
KPIs del perfil (capex, FCF, cartera contratada, concentración, deuda), oferta y textos. Las cifras salen de los EX-99.1 y 8-K citados; el
consenso, de finviz (sorpresa del último informe y BPA del próximo trimestre). En modo actualización no se vuelve a
ejecutar: se edita el caso.
Uso: python nube_ia/data/build_fase2.py [ticker ...]"""
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
    """Fuente finviz con la foto del día (consensus.py): sorpresa del último informe, fecha y BPA del próximo."""
    k = json.load(open(f"{U}/data/{t}/consensus.json", encoding="utf-8"))["latest"]
    return k, [f"finviz {k['date']}: sorpresa BPA {es(k['eps_surprise_pct'], 2)}% y ventas {es(k['sales_surprise_pct'], 2)}%; "
               f"BPA próximo trimestre ${es(k['eps_next_q'], 2)}", f"https://finviz.com/quote.ashx?t={t}"]


def forensic_float(t):
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
    "NBIS": "Nube de IA de pila completa (GPU, almacenamiento y software) con centros de datos propios en Europa y EE. UU., más Avride y TripleTen",
    "CRWV": "Nube especializada en GPU para IA (alquiler de cómputo a laboratorios e hiperescalares), con centros de datos propios y arrendados",
    "IREN": "Centros de datos propios con energía renovable, en transición de la minería de bitcoin a la nube de GPU para IA",
    "APLD": "Diseño, construcción y alquiler de centros de datos para IA y HPC a hiperescalares (Polaris Forge, Delta Forge)",
    "GOOGL": "Búsqueda, YouTube y suscripciones (Google Services), nube con TPU propias (Google Cloud) y apuestas (Other Bets)",
    "AMZN": "Comercio electrónico (Norteamérica e internacional), publicidad y nube (AWS, con chips Trainium propios)",
    "META": "Publicidad en Facebook, Instagram, WhatsApp y Threads (Family of Apps) y realidad virtual y gafas (Reality Labs); capex de IA para uso propio, sin vender nube",
}


def finish(t, c, kpis, cats, supply, fl, text, header, events, sources, nonrec_items=None, adj_pct=None, setup_notes=None):
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
    if setup_notes:
        c["setup"]["notes"] = setup_notes
    c["meta"]["phase"] = "auditado"
    c["meta"]["descriptor"] = DESC[t] + ". Ingresos {m.revenue_ttm:usdM} TTM; último trimestre {m.rev_yoy:pctf} interanual."
    c["snapshot"][0] = ["Negocio", DESC[t]]
    casekit.save(U, t, c)


# ---------------------------------------------------------------- META
def meta():
    t = "META"
    c, rows = base(t)
    pr = casekit.link(1326801, "0001628280-26-050596", "meta-06302026xexhibit991.htm", "EX-99.1 8-K 29-jul-2026: resultados 2T26")
    nb = casekit.link(1326801, "0001193125-26-204128", "d134616d8k.htm", "8-K 4-may-2026: bonos de $25.000M (2031–2066)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 2T26: ingresos $60.801M (+28%), gastos +55% (incluye $2.400M legales y $1.180M de despidos); capex $31.080M; FCF $784M; guía 3T $61.000–64.000M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +1,0% y BPA −14,0% (fallo, por los cargos legales y de despidos). Guía de capex 2026 estrechada a $130.000–145.000M y de gastos a $165.000–169.000M. "
                              "El mercado lo vendió: hueco del −10,2% y cierre del −8,0% con volumen 2,3×.")
    kpis = [
        kp("Usuarios y anuncios (2T26)", "3.600M de personas activas al día (+3%); impresiones +14%; precio por anuncio +12%", "—", *pr),
        kp("Capex", "$31.080M en el 2T26 (incluye arrendamientos financieros); guía 2026 $130.000–145.000M", "$125.000–145.000M (guía previa)", *pr),
        kp("Flujo de caja libre", "$784M en el 2T26 con $31.862M de flujo operativo: el capex se come casi toda la caja", "—", *pr),
        kp("Guía 3T26", "Ingresos $61.000–64.000M (+19–25% interanual); gastos 2026 $165.000–169.000M; tipo fiscal 15–17%", "—", *pr),
        kp("Deuda", "$83.664M a jun-2026 (XBRL), tras $25.000M de bonos en mayo", "$28.832M (jun-2025)", *nb)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    shelf = dict(id="shelf26", kind="shelf", name="Shelf automático S-3ASR (30-abr-2026), usado para bonos", shares=None, capacity_usd=None, price_basis=None, gate="live",
                 date="2026-04-30", notes="Sin límite de importe (emisor WKSI). Su único uso hasta hoy son $25.000M en bonos (mayo), no acciones.", src=[nb])
    events = [dict(date="2026-10-21", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El capex de IA (≈ $130.000–145.000M en 2026) se come el flujo de caja: el FCF del 2T fue de solo $784M y la deuda se ha triplicado en un año.",
                         "META no vende nube: el retorno del capex tiene que salir de los anuncios."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +28% de ingresos con desaceleración {m.accel_pp:pp}, fallo de BPA por cargos y el mercado vendiendo el gasto (−8% al cierre).",
        financials_note="Trimestres de XBRL hasta el 2T26. El neto del 3T25 ($2.709M) es anormalmente bajo frente al operativo ($20.535M) [VERIFY: cargo fiscal en el 10-Q del 3T25].",
        quality=["SBC creciente ($7.658M en el 2T26).", "FCF casi nulo por el capex: la nota de calidad del beneficio debe leerse con eso."],
        supply_read=f"Sin dilución por ampliaciones: financia el capex con deuda ($25.000M en bonos en mayo). Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "con la CFO vendiendo hasta el 91% de su posición en un trimestre (en plan 10b5-1).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 21 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El hiperescalar que más gasta sin vender nube; RS 1m/3m en percentil 100 dentro del universo pese a la caída tras resultados.",
        risks=["Retorno del capex de IA.", "Deuda creciente para financiarlo.", "Cargos legales (UE y EE. UU.).", "Resultados el 21-oct tras el cierre."],
        plan=["Resultados del 3T26 el 21-oct tras el cierre [VERIFY: fecha de finviz]: ya en la ventana de ≤ 3 sesiones, solo vale un EP.",
              "**EP A/B si:** ingresos ≥ $64.000M (techo de la guía), BPA ≥ $6,93 (+5% sobre el consenso de $6,60 de finviz) y capex sin subir la guía.",
              "**D si:** otra subida de la guía de capex o gastos sin aceleración de ingresos: el mercado seguiría castigando el gasto.",
              "Técnica: en tendencia (EMA alineadas), −8% desde el máximo y sobre la SMA 200. Sin setup confirmado."],
        verdict="Anuncios creciendo al +28% y fuerza relativa alta, pero con el FCF casi a cero por el capex y deuda al alza. El 21-oct medirá si el mercado sigue tolerando el gasto.")
    header = dict(verdict="Ingresos +28%, pero FCF casi nulo por el capex y fallo de BPA.",
                  setup="En tendencia; −8% desde máximos.", catalyst="2T26: ventas +1%, BPA −14% frente al consenso; −8% al cierre.",
                  quality="FCF casi nulo; SBC alta.", supply="Bonos, no acciones.", group="RS alta en el universo.")
    finish(t, c, kpis, [e], [shelf, ins], forensic_float(t), text, header, events, [pr, nb, fx])

# ---------------------------------------------------------------- GOOGL
def googl():
    t = "GOOGL"
    c, rows = base(t)
    pr = casekit.link(1652044, "0001652044-26-000066", "googexhibit991q22026.htm", "EX-99.1 8-K 22-jul-2026: resultados 2T26")
    atm = casekit.link(1652044, "0001193125-26-336853", "d140593d424b5.htm", "424B5 6-ago-2026: programa de venta de acciones de hasta $40.000M")
    pf = casekit.link(1652044, "0001193125-26-259830", "d36818d8k.htm", "8-K 5-jun-2026: preferentes de conversión obligatoria (series A y B)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-22", "amc",
                         "Resultados 2T26: ingresos $119.796M (+24%), Google Cloud $24.800M (+82%); margen operativo 34%; el neto incluye $98.000M de ganancias no realizadas en participaciones",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=None,
                         guide_raise=None, guide_change=None, nonrec=True,
                         note="Consenso de finviz: ventas +2,9%. La sorpresa de BPA de finviz (+217%) no se usa: el BPA GAAP ($9,11) lleva $98.000M de ganancias no realizadas en participaciones. "
                              "Alphabet no da guía. El mercado lo vendió: −6,1% en la apertura y −7,1% al cierre.")
    kpis = [
        kp("Google Cloud", "$24.800M en el 2T26 (+82%): IA para empresas e infraestructura de IA", "—", *pr),
        kp("Cartera contratada (RPO)", "$519.500M a jun-2026 (XBRL)", "$108.200M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Capex", "$44.924M en el 2T26 (XBRL)", "$22.446M (2T25)", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Servicios", "Google Services $94.500M (+15%): Búsqueda +17%, suscripciones +15%, YouTube +13%", "—", *pr),
        kp("Financiación de 2026", "Junio: $49.600M netos en acciones A y C y preferentes de conversión obligatoria; programa de venta en mercado de hasta $40.000M; $20.300M en bonos en el 2T", "—", *pr)]
    raise_ = dict(id="equity26", kind="secondary", name="Ampliación de junio de 2026 (acciones A/C y preferentes obligatorias, $49.600M netos)", shares=None, capacity_usd=None,
                  price_basis=None, gate="dated", date="2026-06-05",
                  notes="Para capex de IA. [VERIFY: reparto entre acciones ordinarias y preferentes, y precio de conversión de las series A y B, en el 8-K del 5-jun y sus 424B]",
                  src=[pr, pf])
    atm_ = dict(id="atm26", kind="atm", name="Programa de venta en mercado (ATM) de hasta $40.000M en acciones A y C", shares=None, capacity_usd=40_000_000_000.0,
                price_basis=None, gate="live", date="2026-06-01",
                notes="Acuerdo de distribución con Goldman, J.P. Morgan y Morgan Stanley (junio), ampliado a 13 bancos más en agosto. [VERIFY: importe vendido; lo dirá el 10-Q del 3T26]",
                src=[atm, pr])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Alphabet emite acciones para financiar el capex de IA ($49.600M en junio y un ATM de hasta $40.000M): es un cambio de régimen para una empresa que recompraba.",
                         "El BPA GAAP del 2T está dominado por $98.000M de ganancias no realizadas: no sirve para medir el negocio."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +24% con aceleración {m.accel_pp:pp} y Cloud +82%, pero el mercado lo vendió (−7%) por la ampliación y el capex.",
        financials_note="Trimestres de XBRL hasta el 2T26. El neto del 1T y 2T26 está inflado por ganancias de participaciones (no operativas).",
        quality=["Capex duplicado en un año ($22.446M → $44.924M por trimestre).", "Neto dominado por ganancias no realizadas en el 2T26."],
        supply_read="Dilución nueva y grande: ampliación de $49.600M netos en junio (ordinarias y preferentes obligatorias) y un ATM vivo de hasta $40.000M. "
                    f"Ventas de directivos y fondos GV {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 22 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La nube que más acelera (Cloud +82%) y la mayor cartera contratada después de MSFT, pero la única del grupo que emite acciones.",
        risks=["Dilución: ATM de hasta $40.000M vivo.", "Retorno del capex.", "Regulación de la búsqueda.", "Resultados el 28-oct tras el cierre."],
        plan=["Resultados del 3T26 el 28-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** Cloud acelera por encima del +82% y el BPA ajustado sin ganancias de participaciones supera el consenso de $3,02 de finviz en ≥ 5%.",
              "**D si:** ventas del ATM grandes en el 3T con capex al alza: dilución sin aceleración.",
              "Técnica: en tendencia (EMA alineadas), en la SMA 200 y −16% desde el máximo. Sin setup."],
        verdict="La nube que más crece (+82%) con una cartera de $519.500M, pero financiando el capex con acciones por primera vez. El 28-oct medirá si la aceleración compensa la dilución.")
    header = dict(verdict="Cloud +82% y cartera de $519.500M, pero emite acciones: ampliación de $49.600M y ATM de $40.000M.",
                  setup="En tendencia; −16% desde máximos.", catalyst="2T26: ventas +3% frente al consenso; −7% al cierre.",
                  quality="Neto inflado por participaciones; capex doble.", supply="Ampliación y ATM vivo.", group="La nube que más acelera.")
    finish(t, c, kpis, [e], [raise_, atm_, ins], forensic_float(t), text, header, events, [pr, atm, pf, fx], nonrec_items=True)


# ---------------------------------------------------------------- AMZN
def amzn():
    t = "AMZN"
    c, rows = base(t)
    pr = casekit.link(1018724, "0001018724-26-000024", "amzn-20260630xex991.htm", "EX-99.1 8-K 30-jul-2026: resultados 2T26")
    gs = casekit.link(1018724, "0001104659-26-098339", "tm2617924-6_424b3.htm", "424B3 18-ago-2026: compra de Globalstar (efectivo o acciones a elección)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-30", "amc",
                         "Resultados 2T26: ventas $200.606M (+20%), AWS $42.200M (+37%, su mayor crecimiento en 18 trimestres); el neto incluye $53.400M de ganancias por Anthropic; guía 3T de ventas $197.000–202.000M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=None,
                         guide_raise=None, guide_change=None, nonrec=True,
                         note="Consenso de finviz: ventas +1,8%. La sorpresa de BPA de finviz (+215%) no se usa: el neto lleva $53.400M de ingresos no operativos, sobre todo por la participación en Anthropic. "
                              "EP de verdad: hueco del +12,5% y cierre del +15,3% con volumen 2,6×.")
    kpis = [
        kp("AWS", "$42.200M en el 2T26 (+37%); beneficio operativo $16.600M; el negocio de IA de AWS supera $25.000M de ritmo anual", "$10.200M de beneficio operativo (2T25)", *pr),
        kp("Guía 3T26", "Ventas $197.000–202.000M (+9–12%; ≈ +4 pp sin Prime Day); beneficio operativo $22.500–26.500M", "—", *pr),
        kp("Flujo de caja libre", "−$7.600M en 12 meses: el capex sube $66.100M interanual", "+$18.200M (12 meses a jun-2025)", *pr),
        kp("Deuda", "$132.995M a jun-2026 (XBRL), con bonos en dólares y libras en julio y septiembre", "$56.082M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)")]
    gsat = dict(id="globalstar", kind="secondary", name="Compra de Globalstar con acciones o efectivo a elección", shares=None, capacity_usd=None, price_basis=None,
                gate="dated", date="2026-08-18", notes="Los accionistas de Globalstar eligen efectivo o acciones de Amazon. [VERIFY: importe y acciones máximas a emitir en el 424B3]; "
                                                       "pequeño frente a la capitalización.", src=[gs])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-29", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El neto del 2T ($62.647M) lleva $53.400M de ganancias por Anthropic: no es del negocio.",
                         "FCF negativo en 12 meses por el capex de IA: el negocio genera caja, pero toda se reinvierte."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +20% con aceleración {m.accel_pp:pp}, AWS acelerando al +37% y EP con volumen (+15% al cierre).",
        financials_note="Trimestres de XBRL hasta el 2T26. El capex no sale de companyfacts con la etiqueta estándar (la nota de resultados da el FCF).",
        quality=["Neto inflado por Anthropic ($53.400M en el 2T26).", "FCF de 12 meses negativo (−$7.600M) por el capex."],
        supply_read="Sin ampliaciones: financia el capex con bonos. La compra de Globalstar puede emitir algo de acciones. "
                    f"Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, en planes 10b5-1.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 24 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El único hiperescalar con EP reciente: AWS acelerando y el mercado premiándolo, frente a GOOGL y META vendidos tras resultados.",
        risks=["Capex: FCF negativo.", "Margen del comercio electrónico.", "Resultados el 29-oct tras el cierre."],
        plan=["Resultados del 3T26 el 29-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 26-oct.",
              "**EP A/B si:** AWS ≥ +37% (sin desacelerar), beneficio operativo por encima de $26.500M (techo de la guía) y BPA ≥ +5% sobre el consenso de $1,96 sin la partida de Anthropic.",
              "**D si:** AWS desacelera con más capex.",
              "Técnica: en tendencia (EMA alineadas), −12% desde el máximo y sobre la SMA 200. Sin setup confirmado."],
        verdict="AWS acelerando (+37%) con un EP limpio en julio; lo que pesa es el FCF negativo por el capex. El 29-oct medirá si la aceleración sigue.")
    header = dict(verdict="AWS +37% (máximo en 18 trimestres) y EP en julio; FCF negativo por el capex.",
                  setup="En tendencia; −12% desde máximos.", catalyst="2T26: ventas +2% frente al consenso; EP +15%.",
                  quality="Neto inflado por Anthropic; FCF negativo.", supply="Bonos; Globalstar con acciones a elección.", group="El hiperescalar con EP.")
    finish(t, c, kpis, [e], [gsat, ins], forensic_float(t), text, header, events, [pr, gs, fx], nonrec_items=True)

def _evento_estimado(c, siguiente):
    """Fecha de resultados aún no anunciada: se deja la estimación de la Fase 1 con su motivo."""
    e = (c.get("events") or [{}])[0]
    return [dict(date=e.get("date"), kind="earnings", text=f"{siguiente} [VERIFY: fecha no anunciada; estimada como últimos resultados + 91 días]", src=e.get("src") or [])]


# ---------------------------------------------------------------- CRWV
def crwv():
    t = "CRWV"
    c, rows = base(t)
    pr = casekit.link(1769628, "0001769628-26-000362", "coreweave2q26earningspress.htm", "EX-99.1 8-K 11-ago-2026: resultados 2T26")
    cv = casekit.link(1769628, "0001769628-26-000432", "crwv-20260917.htm", "8-K 22-sep-2026: convertible 2,875% 2033 de $4.200M")
    atm = casekit.link(1769628, "0001628280-26-062362", "coreweave-424b5.htm", "424B5 17-sep-2026: programa de venta de acciones (ATM con ventas a plazo)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-11", "amc",
                         "Resultados 2T26: ingresos $2.575M (+112%); cartera de ingresos ≈ $104.000M (más > $25.000M firmados a principios del 3T); 1,5 GW de potencia activa y 3,7 GW contratados",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +0,8% y BPA +14,5% (pérdida menor de la esperada). La guía se da en la conferencia, no en la nota. "
                              "EP de verdad: hueco del +20,4% y cierre del +19,3% con volumen 3,0×, ya devuelto (−56% desde el máximo).")
    kpis = [
        kp("Cartera de ingresos", "≈ $104.000M a jun-2026, sin contar > $25.000M de compromisos nuevos de principios del 3T; RPO $103.700M (XBRL)", "RPO $30.100M (jun-2025)", *pr),
        kp("Potencia", "1,5 GW activos (+≈ 500 MW en el trimestre) y ≈ 3,7 GW contratados", "—", *pr),
        kp("Capex", "$6.422M en el 2T26 y $7.695M en el 1T26 (XBRL)", "$2.453M (2T25)", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Resultado", "Pérdida neta de $626M en el 2T26; flujo operativo $679M", "—", "quarters.json (XBRL 10-Q 2T26)")]
    conv = dict(id="conv33", kind="convertible", name="Convertible 2,875% 2033 ($4.200M, conversión ≈ $97,85)", shares=round(4_200_000 * 10.2194), capacity_usd=None,
                price_basis=97.85, gate="gated", date="2033-01-01",
                notes="10,2194 acciones por $1.000 (≈ 42,9M acciones), prima del 22,5% sobre el 17-sep; fuera de dinero a {m.price:px}. Con capped call. [VERIFY: fecha exacta de vencimiento]",
                src=[cv])
    atm_ = dict(id="atm26", kind="atm", name="Programa de venta de acciones Clase A con ventas a plazo (sep-2026)", shares=None, capacity_usd=0.0, price_basis=None,
                gate="live", date="2026-09-17",
                notes="Acuerdo de distribución con varios bancos, incluidas ventas a plazo con collar. [VERIFY: importe máximo del programa y lo vendido; capacidad puesta a 0 hasta confirmarla]",
                src=[atm])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 3T26")
    text = dict(
        narrative_flags=["Los insiders han vendido ≈ $5.800M en 12 meses: Magnetar (≥ 10%) $2.990M y los fundadores ≈ $900–1.000M cada uno, hasta el 89–95% de su posición en un trimestre.",
                         "Financia el crecimiento con deuda, convertibles y ahora un ATM: la dilución potencial crece cada trimestre."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +112% sostenido y EP con volumen en agosto, ya devuelto por completo.",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión. La deuda del 2T26 no sale de companyfacts con la etiqueta estándar.",
        quality=["Pérdidas netas crecientes ($626M en el 2T26) con capex de $6.000–7.700M por trimestre.", "Flujo operativo positivo por anticipos de clientes."],
        supply_read=f"La oferta más pesada del estudio: ventas de insiders de {casekit.usd_m(insider_total(t))} en 12 meses, convertible de $4.200M y un ATM nuevo. "
                    "Magnetar sigue con ≈ 14,9% (13G).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; sin PER (pérdidas). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El neocloud más grande: cartera de $104.000M y +112%, pero el más diluido y con más ventas de insiders del universo.",
        risks=["Dilución (ATM, convertibles) y ventas de insiders.", "Deuda y capex.", "Concentración de clientes (Microsoft, OpenAI).", "Resultados ≈ 10-nov."],
        plan=["Resultados del 3T26 hacia el 10-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos y cartera por encima de lo esperado con margen operativo positivo y sin ventas grandes del ATM en el trimestre.",
              "**D si:** pérdidas crecientes con más dilución.",
              "Técnica: −56% desde el máximo, −32% bajo la SMA 200. Sin setup."],
        verdict="Crecimiento real (+112%, cartera de $104.000M) con la peor estructura de oferta del estudio: insiders saliendo, convertibles y un ATM nuevo. Alto riesgo.")
    header = dict(verdict="+112% y cartera de $104.000M, pero insiders vendiendo $5.800M, convertible y ATM.",
                  setup="−56% desde máximos; sin setup.", catalyst="2T26: ventas +1%, BPA +15%; EP +19% ya devuelto.",
                  quality="Pérdidas crecientes; capex enorme.", supply="La más pesada: ATM, convertible, insiders.", group="El neocloud más grande.")
    finish(t, c, kpis, [e], [conv, atm_, ins], forensic_float(t), text, header, events, [pr, cv, atm, fx])


# ---------------------------------------------------------------- IREN
def iren():
    t = "IREN"
    c, rows = base(t)
    pr = casekit.link(1878848, "0001878848-26-000051", "irenreportsfy26results.htm", "EX-99.1 8-K 27-ago-2026: resultados FY26")
    cv = casekit.link(1878848, "0001140361-26-021285", "ef20073507_8k.htm", "8-K 14-may-2026: convertible 1% 2033 de $3.000M")
    rs = casekit.link(1878848, "0001140361-26-031055", "ny20079234x1_424b7.htm", "424B7 4-ago-2026: reventa de acciones por accionistas")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-30", "2026-08-27", "amc",
                         "Resultados FY26: ARR contratado de $4.000M para la capacidad de 2026 y $1.000M de ARR operativo; nuevo contrato plurianual con un laboratorio de IA; $2.800M de financiación de GPU",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=None,
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +3,7%; la sorpresa de BPA (−246%) no se usa: la pérdida del 4T ($684M) refleja la transición de la minería a la nube de IA. "
                              "Los ingresos caen (−27% interanual) mientras crece la nube. El mercado lo vendió: −7,1% en la apertura y −12,5% al cierre.")
    kpis = [
        kp("ARR de IA", "$4.000M contratados para la capacidad de 2026; $1.000M operativos hoy", "—", *pr),
        kp("Cartera (RPO)", "$5.100M a jun-2026 (XBRL)", "$195M (sep-2025)", "quarters.json (XBRL 10-K FY26)"),
        kp("Financiación", "$2.800M de financiación de GPU (≈ 90% del capex asociado); convertible de $3.000M en mayo; deuda $7.593M (XBRL)", "Deuda $963M (jun-2025)", *pr),
        kp("Ingresos", "$137M en el 4T FY26 (−27%): la minería de bitcoin baja mientras arranca la nube", "$187M (4T FY25)", "quarters.json (XBRL 10-K FY26)")]
    conv = dict(id="conv33", kind="convertible", name="Convertible 1% 2033 ($3.000M, conversión ≈ $73,07)", shares=round(3_000_000 * 13.6848), capacity_usd=None,
                price_basis=73.07, gate="gated", date="2033-01-01",
                notes="13,6848 acciones por $1.000 (≈ 41,1M acciones), fuera de dinero a {m.price:px}; capped call de $201,3M. [VERIFY: fecha exacta de vencimiento]", src=[cv])
    resale = dict(id="reventa26", kind="pipe_resale", name="Reventa de acciones por accionistas (424B7, ago-2026)", shares=None, capacity_usd=None, price_basis=None,
                  gate="live", date="2026-08-04", notes="Acciones emitidas antes a los vendedores, registradas para su reventa. [VERIFY: número de acciones y origen en el 424B7]", src=[rs])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 1T FY27")
    text = dict(
        narrative_flags=["Empresa en transición: los ingresos de hoy (minería) caen y los de mañana (nube de IA, $4.000M de ARR contratado) aún no están en las cuentas.",
                         "Financiación fuerte con deuda y convertibles: deuda de $963M a $7.593M en un año."],
        catalyst_read="El FY26 puntúa {m.cat_q4fy26_score:sc}: contratos de IA grandes pero ingresos a la baja y pérdidas; el mercado lo vendió (−12,5%).",
        financials_note="Trimestres de XBRL hasta el 4T FY26 (IREN presenta 10-K/10-Q desde 2025); regenerados el 19-oct con el 4T derivado de la misma versión.",
        quality=["Pérdidas crecientes ($684M en el 4T FY26).", "Flujo operativo del 4T ($1.811M) inflado por anticipos de clientes."],
        supply_read="Convertible de $3.000M fuera de dinero, reventa de acciones registrada en agosto y deuda creciente. Insiders apenas venden.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM (sobre ingresos de minería, no comparable). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El neocloud en transición: más barato que CRWV y NBIS por capitalización, con el riesgo de ejecución más alto.",
        risks=["Ejecución de la nube de IA.", "Deuda y convertibles.", "Precio del bitcoin.", "Resultados ≈ fin de noviembre."],
        plan=["Resultados del 1T FY27 hacia el 26-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos de nube de IA visibles en el trimestre y ARR operativo por encima de $1.000M.",
              "**D si:** retrasos en la puesta en marcha de capacidad.",
              "Técnica: −64% desde el máximo, −39% bajo la SMA 200. Sin setup."],
        verdict="Apuesta de transición a la nube de IA con $4.000M de ARR contratado, pero con ingresos a la baja, pérdidas y deuda creciente. El más especulativo del universo.")
    header = dict(verdict="$4.000M de ARR contratado, pero ingresos a la baja, pérdidas y deuda.",
                  setup="−64% desde máximos; sin setup.", catalyst="FY26: contratos de IA; −12,5% al cierre.",
                  quality="Pérdidas; caja por anticipos.", supply="Convertible y reventa registrada.", group="Neocloud en transición.")
    finish(t, c, kpis, [e], [conv, resale, ins], forensic_float(t), text, header, events, [pr, cv, rs, fx])


# ---------------------------------------------------------------- APLD
def apld():
    t = "APLD"
    c, rows = base(t)
    pr = casekit.link(1144879, "0001144879-26-000057", "apldq127earningsrelease.htm", "EX-99.1 8-K 7-oct-2026: resultados 1T FY27")
    q = c["financials"]["quarters"]
    # El XBRL cambia de etiqueta: hasta el 3T FY26 solo «RevenueFromContract» (sin alquileres); desde el 1T FY27, «Revenues» total.
    ult = next(x for x in q if x["end"] == "2026-08-31")
    ult["revenue"] = 341_900_000.0
    ult["gross_profit"] = 341_900_000.0 - 245_700_000.0
    ult["src"] = ("Ingresos totales («Revenues», incluye alquileres a hiperescalares) de la nota y del 10-Q del 1T FY27; bruto = ingresos − coste de ingresos ($245,7M). "
                  "Los trimestres anteriores solo tienen ingresos por contratos en XBRL: el interanual mezcla bases.")
    if not any(x["end"] == "2026-05-31" for x in q):
        q.insert(q.index(ult), {"period": "may-26", "end": "2026-05-31", **{k: None for k in ult if k not in ("period", "end", "src")},
                                "gap": True, "gap_note": "el 10-K FY26 da el año en «Revenues» y los 9 meses en otra etiqueta: el 4T no se puede derivar sin mezclar bases"})
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q1fy27", "2026-08-31", "2026-10-07", "amc",
                         "Resultados 1T FY27: ingresos $341,9M (+322%, operaciones continuadas); EBITDA ajustado $64,4M; nuevo alquiler de 210 MW a 15 años con un hiperescalar (≈ $5.200M)",
                         [pr, fx], rev_surprise=None, eps_surprise=None,
                         guide_raise=None, guide_change=None,
                         note="La sorpresa de finviz (ventas +194%, BPA −178%) no se usa: compara bases distintas tras la venta del negocio de nube (operaciones discontinuadas). "
                              "Pérdida neta atribuible de $221M; ajustada de $4,1M. Reacción plana: +2,3% en la apertura y +0,2% al cierre.")
    kpis = [
        kp("Contratos", "Delta Forge 2: 210 MW a 15 años con su hiperescalar con grado de inversión (≈ $5.200M de ingresos base); Polaris Forge 1 edificio 2 (75 MW) en servicio desde el 1-jul-2026", "—", *pr),
        kp("Resultado ajustado", "Ingresos ajustados $300,4M; EBITDA ajustado $64,4M; resultado operativo neto $58,8M", "—", *pr),
        kp("Ingresos (bases)", "$341,9M totales en el 1T FY27 frente a $80,9M solo por contratos en el 1T FY26", "—", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = _evento_estimado(c, "Resultados 2T FY27")
    text = dict(
        narrative_flags=["Las cuentas mezclan bases: venta del negocio de nube (discontinuado) y alquileres de centros de datos que entran como ingresos totales desde este trimestre.",
                         "El 13D que aparece en sus filings lo presenta la propia APLD por su 97,5% de la filial escindida: no es un accionista entrando."],
        catalyst_read="El 1T FY27 puntúa {m.cat_q1fy27_score:sc}: ingresos +322% con contratos a 15 años, pero pérdida GAAP y reacción plana.",
        financials_note="Trimestres de XBRL con dos ajustes manuales (19-oct): el 1T FY27 usa los ingresos totales de la nota ($341,9M) y may-26 queda como hueco "
                        "porque el 10-K da el año y los 9 meses en etiquetas distintas. TTM y crecimiento interanual mezclan bases.",
        quality=["Pérdida neta atribuible de $221M en el 1T FY27.", "Margen bruto bajo (≈ 28%) en la fase de puesta en marcha."],
        supply_read="Financiación con líneas de crédito por proyecto (junio-2026). Ventas de directivos pequeñas, varias fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM (bases mezcladas). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El casero de centros de datos del universo (alquila a hiperescalares), más parecido a un REIT en construcción que a CRWV o NBIS.",
        risks=["Ejecución de la construcción.", "Concentración en un hiperescalar.", "Deuda por proyecto.", "Resultados ≈ ene-2027."],
        plan=["Resultados del 2T FY27 hacia el 6-ene-2027 [VERIFY: fecha no anunciada].",
              "**EP A/B si:** EBITDA ajustado al alza con capacidad nueva en servicio y otro contrato de hiperescalar.",
              "**D si:** retrasos en Polaris Forge o Delta Forge.",
              "Técnica: −63% desde el máximo, −42% bajo la SMA 200. Sin setup."],
        verdict="Contratos a 15 años con un hiperescalar (≈ $5.200M) y ingresos +322%, pero cuentas en transición, pérdidas y la acción en tendencia bajista.")
    header = dict(verdict="+322% con contratos a 15 años; cuentas en transición y pérdidas.",
                  setup="−63% desde máximos; sin setup.", catalyst="1T FY27: sorpresa no medible (bases distintas).",
                  quality="Pérdida GAAP; margen de arranque.", supply="Deuda por proyecto.", group="El casero del universo.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])

# ---------------------------------------------------------------- NBIS
def nbis():
    t = "NBIS"
    c, rows = base(t)
    pr = casekit.link(1513845, "0001104659-26-094568", "tm2622968d1_ex99-1.htm", "6-K 12-ago-2026: resultados 2T26")
    fs = casekit.link(1513845, "0001104659-26-094844", "nbis-20260812xex99d2.htm", "6-K 12-ago-2026: estados intermedios 1S26 (ATM, convertibles, warrants de NVIDIA)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-12", "bmo",
                         "Resultados 2T26: ingresos $582,3M (+454%), EBITDA ajustado $236,2M; capex $5.657M en el trimestre; ingresos diferidos de $5.975M por anticipos de clientes",
                         [pr, fs, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=None, guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +2,2%; la sorpresa de BPA (+83%) no se usa: el neto mezcla revalorizaciones de participaciones. "
                              "EP de verdad: hueco del +17,0% y cierre del +34,1% con volumen 3,2×. Hora de publicación en Ámsterdam antes de la apertura de EE. UU. [VERIFY: hora exacta].")
    kpis = [
        kp("Crecimiento y EBITDA", "Ingresos $582,3M (+454%); EBITDA ajustado $236,2M (−$21,0M un año antes)", "—", *pr),
        kp("Capex y anticipos", "Capex $5.657M en el 2T26 y $8.130M en el 1S26; ingresos diferidos $979M corrientes + $4.996M no corrientes (anticipos de clientes)", "—", *fs),
        kp("Clientes", "Contratos de infraestructura de IA con Microsoft (sep-2025) y Meta (mar-2026) [VERIFY: importes en los 6-K de los anuncios]", "—", *fs),
        kp("Balance", "Caja $8.042M y deuda $8.546M a jun-2026; activos totales $27.962M", "—", *fs)]
    atm = dict(id="atm25", kind="atm", name="Programa de venta de hasta 25M acciones Clase A (nov-2025)", shares=25_000_000 - 12_729_493,
               capacity_usd=(25_000_000 - 12_729_493) * 165.47, price_basis=223.60, gate="live", date="2025-11-12",
               notes="Vendidas 12,73M acciones en el 2T26 a $223,60 de media ($2.811M netos); quedan ≈ 12,27M (capacidad en dólares calculada al cierre del 16-oct, $165,47).", src=[fs])
    conv = dict(id="conv3133", kind="convertible", name="Convertibles de marzo-2026: $2.590M al 1,25% 2031 ($183,22) y $1.750M al 2,625% 2033 ($180,31)",
                shares=round(2_590_000 * 5.4579 + 1_750_000 * 5.546), capacity_usd=None, price_basis=180.31, gate="gated", date=None,
                notes="≈ 14,1M + 9,7M acciones, cerca del dinero a {m.price:px}. Liquidación en efectivo, acciones o ambos. [VERIFY: fechas exactas de vencimiento]", src=[fs])
    nv = dict(id="nvda_warrants", kind="warrants", name="Warrants prefinanciados de NVIDIA (21,07M acciones, mar-2026)", shares=21_065_936, capacity_usd=None, price_basis=0.0001,
              gate="live", date="2026-03-11", notes="$2.000M pagados por NVIDIA (≈ $94,94 por acción); ejercicio a $0,0001, ya incluidos en el BPA básico.", src=[fs])
    events = _evento_estimado(c, "Resultados 3T26")
    text = dict(
        narrative_flags=["La dilución financia el capex: ATM (12,73M acciones vendidas en el 2T), convertibles de $4.340M y warrants de NVIDIA por 21,07M acciones.",
                         "NVIDIA es a la vez proveedor e inversor (warrants prefinanciados de $2.000M)."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +454% y EBITDA positivo con el EP más fuerte del estudio (+34% al cierre).",
        financials_note="Emisor extranjero (20-F/6-K, US GAAP en US$, operaciones continuadas): **trimestres cargados a mano** de los estados intermedios (6-K del 3T25, 1T26 y 2T26) "
                        "y del 20-F 2025; 4T = año − 9 meses. Flujos de 2024 sin derivar. Bruto = ingresos − coste de ingresos sin amortización (Nebius la presenta aparte).",
        quality=["Capex muy por encima de la caja operativa.", "Neto volátil por revalorizaciones de participaciones (ClickHouse, Toloka)."],
        supply_read="La oferta más activa del universo junto a CRWV: ATM con ≈ 12,27M acciones por vender, convertibles de $4.340M cerca del dinero y warrants de NVIDIA. "
                    "Goldman Sachs declara ≈ 5,1% (13G).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; sin PER. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El neocloud que más crece (+454%) y con EBITDA positivo; más diluido que IREN, menos que CRWV en ventas de insiders.",
        risks=["Dilución (ATM y convertibles).", "Capex y deuda.", "Concentración en Microsoft y Meta.", "Resultados ≈ 11-nov."],
        plan=["Resultados del 3T26 hacia el 11-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos por encima de $800M con EBITDA ajustado al alza y sin ventas grandes del ATM en el trimestre.",
              "**D si:** más dilución con el crecimiento desacelerando.",
              "Técnica: «líder enfriado roto» (−43% desde el máximo, en la SMA 200)."],
        verdict="El crecimiento más rápido del estudio (+454%) con EBITDA positivo y NVIDIA de socio, financiado con mucha dilución. Caso de alto riesgo y alto potencial.")
    header = dict(verdict="+454%, EBITDA positivo y EP del +34%; ATM, convertibles y warrants de NVIDIA.",
                  setup="Líder enfriado roto; −43% desde máximos.", catalyst="2T26: ventas +2%; EP +34%.",
                  quality="Capex enorme; neto volátil.", supply="ATM, convertibles y warrants.", group="El neocloud que más crece.")
    finish(t, c, kpis, [e], [atm, conv, nv], {}, text, header, events, [pr, fs, fx])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
