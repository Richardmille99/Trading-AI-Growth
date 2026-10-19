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


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
