"""Registro reproducible de la Fase 1 manual + Fase 2 del universo software (19-oct-2026): catalizadores con consenso,
KPIs del perfil saas (RPO/cRPO, suscripción, IA), oferta y textos. Las cifras salen de los EX-99.1 y 8-K citados; el
consenso, de finviz (sorpresa del último informe y BPA del próximo trimestre). En modo actualización no se vuelve a
ejecutar: se edita el caso.
Uso: python software/data/build_fase2.py [msft now ...]"""
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
    "ORCL": "Base de datos y aplicaciones con licencias y soporte, más nube de infraestructura (OCI) en plena expansión para IA",
    "CRM": "CRM en la nube por usuario (ventas, servicio, marketing), Slack, Tableau, MuleSoft e Informatica, con agentes de IA (Agentforce)",
    "ADBE": "Software creativo (Creative Cloud), de documentos (Acrobat) y de marketing (Experience Cloud) por suscripción, con IA generativa (Firefly)",
    "INTU": "Software fiscal (TurboTax), finanzas personales (Credit Karma) y contabilidad y servicios para pymes (QuickBooks, Mailchimp)",
    "WDAY": "Software de recursos humanos, finanzas y TI por suscripción para grandes empresas, con agentes de IA",
    "SNOW": "Plataforma de datos en la nube con cobro por consumo, con productos de IA (Cortex, CoCo)",
    "MDB": "Base de datos documental (Atlas en la nube por consumo y Enterprise Advanced en local) con funciones de IA (Voyage AI)",
    "CRWD": "Plataforma de seguridad de endpoints, nube e identidad por suscripción (Falcon), con modelo de consumo Falcon Flex",
    "ZS": "Seguridad de red en la nube (zero trust, SASE) por suscripción, con operaciones de seguridad (Red Canary)",
    "PANW": "Plataforma de seguridad de red (firewalls), nube (Prisma) y operaciones (Cortex), creciendo con compras",
    "PLTR": "Plataformas de análisis de datos e IA (Gotham para gobierno; Foundry y AIP para empresas), con fuerte peso del gobierno de EE. UU.",
    "APP": "Plataforma de publicidad móvil y de comercio electrónico con motor de IA propio (Axon), tras vender su negocio de juegos",
    "DDOG": "Observabilidad y seguridad en la nube con cobro por consumo; clientes nativos de IA en crecimiento",
    "NET": "Red global para seguridad, rendimiento y cómputo en el borde (Workers, IA en la red), con cobro por suscripción y uso",
    "FTNT": "Firewalls propios (FortiGate, con chips ASIC propios) y servicios de seguridad por suscripción, incluido SASE",
    "MSFT": "Nube (Azure), software de productividad (Microsoft 365, Copilot), LinkedIn, Windows y gaming (Xbox); socio e inversor de OpenAI",
    "NOW": "Plataforma de flujos de trabajo para empresas con licencia por usuario (TI, empleados, clientes) y agentes de IA; compró Armis (ciberseguridad) en 2026",
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


# ---------------------------------------------------------------- MSFT
def msft():
    t = "MSFT"
    c, rows = base(t)
    pr = casekit.link(789019, "0001193125-26-323632", "msft-ex99_1.htm", "EX-99.1 8-K 29-jul-2026: resultados 4T FY26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 4T FY26: ingresos $90.007M (+18%); Microsoft Cloud $59.300M (+27%); Azure > $100.000M en el año; cartera comercial $678.000M (+84%)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +2,7% y BPA +11,8%. La guía se da en la conferencia, no en la nota: sin sorpresa de guía. "
                              "El neto incluye ganancias de inversiones (OpenAI +$480M en el trimestre y $4.963M en FY26; Anthropic +$3.200M), que la compañía excluye en sus cifras ajustadas. "
                              "EP de verdad: hueco del +12,1% y cierre del +15,5% con volumen 2,8×.")
    kpis = [
        kp("Cartera contratada (RPO)", "Comercial $678.000M (+84%); total $684.000M en XBRL", "$375.000M (jun-2025)", *pr),
        kp("Microsoft Cloud y Azure", "Microsoft Cloud $59.300M en el 4T FY26 (+27%); Azure supera $100.000M en FY26", "—", *pr),
        kp("Copilot", "Microsoft 365 Copilot > 30M de licencias de pago", "—", *pr),
        kp("Capex", "$35.802M en el 4T FY26 (pagos de inmovilizado, XBRL); ≈ 40% de los ingresos del trimestre", "$17.079M (4T FY25)", "quarters.json (XBRL 10-K FY26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 1T FY27 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El beneficio neto lleva ganancias contables de inversiones en OpenAI y Anthropic: el BPA comparable es el ajustado.",
                         "La cartera de $678.000M está muy concentrada en contratos de IA (OpenAI incluido): mide demanda comprometida, no ingresos de este año."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: crecimiento del +18% sin aceleración ({m.accel_pp:pp}), beat de BPA del 12% y EP con volumen. "
                      "Es el único caso del universo con EP reciente confirmado.",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 4T FY26 (cerrado el 30-jun-2026).",
        quality=["El capex se ha duplicado en un año ($17.079M → $35.802M por trimestre): el FCF crece mucho menos que el beneficio.",
                 "Ganancias de inversiones (OpenAI, Anthropic) en el neto: no recurrentes."],
        supply_read=f"Sin dilución: recompras y dividendo. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, pequeñas frente a la capitalización ({{m.mcap:usdM}}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 22 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El líder del universo en fuerza relativa (RS 1m en percentil 100) y el único con EP reciente; a −4% de su máximo mientras el resto del software sigue lejos.",
        risks=["Capex de IA: si el retorno se retrasa, el FCF sufre.", "Concentración de la cartera en OpenAI.",
               "Resultados el 28-oct tras el cierre."],
        plan=["Resultados del 1T FY27 el 28-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** BPA ≥ $4,96 (+5% sobre el consenso de $4,72 de finviz), Azure acelerando y cartera comercial por encima de $678.000M.",
              "**D si:** Azure desacelera con más capex: el mercado empezaría a cuestionar el retorno de la inversión.",
              "Técnica: en tendencia (EMA 10/20/50 alineadas) y en una bandera de 15 sesiones; ver §8."],
        verdict="El líder del software por fuerza relativa, con EP en julio y una cartera contratada enorme; lo que vigilar es el capex, que crece el doble que los ingresos.")
    header = dict(verdict="EP en julio (+15%), cartera de $678.000M y a −4% del máximo: el líder del grupo.",
                  setup="Bandera de 15 sesiones (pivote ≈ $551); ver §8.", catalyst="4T FY26: BPA +12% frente al consenso; EP con volumen.",
                  quality="Capex duplicado; ganancias de OpenAI/Anthropic en el neto.", supply="Sin dilución.", group="Líder por RS.")
    notes = ("Candidato breakout_flag de prices.py (16-oct): pivote $551,15, stop $518,79, tras una subida del 44% y una base de 15 sesiones (profundidad 9%). "
             "No se confirma como setup sin ver el gráfico y con resultados el 28-oct: dentro de la ventana de ≤ 3 sesiones solo vale un EP.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx], setup_notes=notes)


# ---------------------------------------------------------------- NOW
def now():
    t = "NOW"
    c, rows = base(t)
    pr = casekit.link(1373715, "0001373715-26-000072", "erq2fy26.htm", "EX-99.1 8-K 22-jul-2026: resultados 2T26")
    q1 = casekit.link(1373715, "0001373715-26-000054", "erq1fy26.htm", "EX-99.1 8-K 22-abr-2026: guía anual previa")
    tl = casekit.link(1373715, "0001373715-26-000054", "now-20260417.htm", "8-K 17-abr-2026: préstamo de $4.000M para comprar Armis")
    nb = casekit.link(1373715, "0001193125-26-226644", "d60522d8k.htm", "8-K 15-may-2026: bonos de $4.000M (2028–2036)")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-22", "amc",
                         "Resultados 2T26: suscripción $3.877M (+24,5%), cRPO $13.200M (+21%); supera el techo de su guía y sube poco la anual (suscripción $15.760–15.780M)",
                         [pr, q1, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=0.1,
                         note="Consenso de finviz: ventas +1,5% y BPA +4,4%. Guía anual de suscripción: punto medio de $15.755M a $15.770M (+0,1%); guía de margen bruto de suscripción de 81,5% a 81%. "
                              "Parte del beat es adelanto de contratos federales on-premise del 3T al 2T, según la compañía. "
                              "El margen operativo GAAP cae al 4% por la compra de Armis (costes de integración, amortización y compensación). El mercado lo vendió: +4,8% en la apertura y −3,7% al cierre.")
    kpis = [
        kp("cRPO y RPO", "cRPO $13.200M (+21%); RPO $29.000M (+21%)", "—", *pr),
        kp("IA", "ServiceNow AI supera $1.000M de valor anual contratado", "—", *pr),
        kp("Guía 3T26", "Suscripción $3.975–3.980M (+20,5%); cRPO +19,5%; margen operativo ajustado 31%", "—", *pr),
        kp("Margen operativo", "GAAP 4% en el 2T26 (11% en el 2T25); ajustado $1.173M", "—", *pr),
        kp("Compra de Armis", "Financiada con un préstamo puente de $4.000M (vence el 16-oct-2026) y $4.000M en bonos 2028–2036", "—", *tl)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    sbc = dict(id="sbc", kind="sbc", name="Compensación en acciones (16,5% de los ingresos en el 2T26)", shares=None, capacity_usd=None, price_basis=None, gate="live",
               date=None, notes="La SBC sube con la compra de Armis (16,5% de los ingresos frente al 15,5% de hace un año); nuevos planes S-8 de jul/ago-2026 para empleados de las adquisiciones.",
               src=[pr])
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Parte del beat del 2T viene de adelantar contratos federales del 3T: el 3T tendrá una base más difícil.",
                         "La guía anual apenas se mueve (+0,1%) pese a «superar el techo» del trimestre."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: crecimiento del +24% con aceleración {m.accel_pp:pp}, beat pequeño (+1,5% en ingresos) y guía casi plana; el mercado lo vendió.",
        financials_note="Trimestres de XBRL hasta el 2T26. El 2T26 incluye Armis: margen GAAP y deuda no comparables con trimestres anteriores.",
        quality=["SBC alta (16,5% de los ingresos) y al alza por la adquisición.",
                 "Deuda nueva de $8.000M para comprar Armis: el préstamo puente vencía el 16-oct-2026 [VERIFY: refinanciación con los bonos de mayo]."],
        supply_read="Sin ampliaciones: la compra de Armis se pagó con deuda. La dilución viene de la SBC (16,5% de los ingresos) y de los planes de las adquisiciones. "
                    f"Ventas de directivos pequeñas ({casekit.usd_m(insider_total(t))}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 28 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Representante del modelo por usuario: crece más que CRM, pero −26% desde máximos y con una guía que no acompaña al rebote del grupo.",
        risks=["Base difícil del 3T por el adelanto federal.", "Integración de Armis y deuda nueva.", "Sustitución de licencias por agentes de IA.",
               "Resultados el 28-oct tras el cierre."],
        plan=["Resultados del 3T26 el 28-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** suscripción ≥ $4.020M (+1% sobre el techo de la guía), cRPO ≥ +20% y guía anual por encima de $15.780M.",
              "**D si:** cRPO por debajo del +19,5% guiado: confirmaría que el modelo por usuario se frena.",
              "Técnica: en tendencia (EMA alineadas) y sobre la SMA 200, pero −26% desde el máximo. Sin setup."],
        verdict="Crecimiento sólido (+24%) y una apuesta grande en seguridad con Armis, pero beat pequeño, guía plana y margen GAAP hundido por la compra. El 28-oct medirá si el modelo por usuario aguanta.")
    header = dict(verdict="+24% y cRPO +21%, pero guía plana y margen GAAP del 4% por Armis.",
                  setup="En tendencia; −26% desde máximos; sin setup.", catalyst="2T26: ventas +1,5%, BPA +4% frente al consenso; guía +0,1%.",
                  quality="SBC 16,5%; deuda nueva de $8.000M.", supply="Sin ampliaciones; dilución por SBC.", group="Modelo por usuario.")
    finish(t, c, kpis, [e], [sbc, ins], forensic_float(t), text, header, events, [pr, q1, tl, nb, fx])

# ---------------------------------------------------------------- FTNT
def ftnt():
    t = "FTNT"
    c, rows = base(t)
    pr = casekit.link(1262039, "0001262039-26-000018", "ftntq2-2026ex991.htm", "EX-99.1 8-K 29-jul-2026: resultados 2T26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 2T26: ingresos $2.048M (+26%), producto $773M (+52%), facturación $2.370M (+33%); supera el techo de su guía y sube la guía anual de ingresos al +19% ($8.020–8.180M)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=None,
                         note="Consenso de finviz: ventas +8,4% y BPA +20,6%. La nota sube la guía anual de ingresos «al +19%» sin dar la cifra anterior en el mismo documento: sin cambio de guía cuantificado. "
                              "El mercado abrió +7,0% y cerró solo +0,7%.")
    kpis = [
        kp("Facturación (billings)", "$2.370M en el 2T26 (+33%); guía 3T $2.250–2.350M; guía 2026 $9.350–9.550M", "—", *pr),
        kp("Producto frente a servicio", "Producto $773M (+52%): ciclo de renovación de firewalls; guía de servicio 2026 $5.180–5.220M", "—", *pr),
        kp("Guía 3T26", "Ingresos $2.010–2.100M; margen operativo ajustado 35–37%; BPA ajustado $0,83–0,87", "—", *pr),
        kp("Cartera (RPO)", "$7.730M a jun-2026 (XBRL)", "$6.640M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El crecimiento lo tira el producto (+52%, ciclo de renovación de firewalls): es menos recurrente que el servicio y suele ser cíclico."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +26% con aceleración {m.accel_pp:pp}, beat amplio (+8% en ingresos, +21% en BPA) y guía subida; el mercado no lo siguió (+0,7% al cierre).",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión.",
        quality=["Margen operativo del 34% GAAP y FCF por encima del beneficio.", "Sin ampliaciones ni filings de oferta en 12 meses."],
        supply_read=f"Oferta limpia: sin ampliaciones; deuda reducida a $497M. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, en su mayoría en planes 10b5-1.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 45 (finviz), caro para un ciclo de hardware. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El que más acelera de seguridad gracias al hardware; más caro por PER que PANW y ZS pese a crecer con producto.",
        risks=["Ciclo de renovación de firewalls: alto ahora, puede bajar en 2027.", "Valoración (PER adelantado ≈ 45).", "Resultados el 28-oct tras el cierre."],
        plan=["Resultados del 3T26 el 28-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** ingresos ≥ $2.100M (techo de la guía), facturación ≥ $2.350M y nueva subida de la guía anual.",
              "**D si:** facturación por debajo de $2.250M: el ciclo de producto se estaría agotando.",
              "Técnica: en tendencia (EMA alineadas), sobre la SMA 200 y −14% desde el máximo. Sin setup confirmado."],
        verdict="Aceleración real por el ciclo de renovación de firewalls, con oferta limpia y en tendencia, pero cara y dependiente del producto. El 28-oct dirá si el ciclo sigue.")
    header = dict(verdict="+26% con producto +52% y guía subida; en tendencia, pero caro.",
                  setup="En tendencia; −14% desde máximos.", catalyst="2T26: ventas +8%, BPA +21% frente al consenso; guía subida.",
                  quality="Margen 34%; FCF > beneficio.", supply="Limpia.", group="El que más acelera de seguridad.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])

# ---------------------------------------------------------------- PLTR
def pltr():
    t = "PLTR"
    c, rows = base(t)
    pr = casekit.link(1321655, "0001321655-26-000039", "a2026q2ex991pressrelease.htm", "EX-99.1 8-K 3-ago-2026: resultados 2T26")
    q1 = ["EX-99.1 8-K may-2026: guía anual previa ($7.650–7.662M)", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001321655&type=8-K"]
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-03", "amc",
                         "Resultados 2T26: ingresos $1.935M (+93%), comercial EE. UU. +149%; sube la guía 2026 a $8.150–8.158M (+82%) desde $7.650–7.662M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=6.5,
                         note="Consenso de finviz: ventas +6,8% y BPA +19,0%. Superó en un 7,5% su propia guía del 2T ($1.797–1.801M) y subió la anual un 6,5% (punto medio de $7.656M a $8.154M). "
                              "EP de verdad: hueco del +15,5% y cierre del +29,5% con volumen 4,3×.")
    kpis = [
        kp("Guía 2026", "Ingresos $8.150–8.158M (+82%); comercial EE. UU. > $3.424M (+134%); beneficio operativo ajustado $4.889–4.897M; FCF ajustado $4.500–4.700M",
           "Ingresos $7.650–7.662M; comercial EE. UU. > $3.224M (+120%) (may-2026)", *pr),
        kp("Cartera (RPO)", "$4.900M a jun-2026 (XBRL)", "$2.400M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Margen operativo GAAP", "47% en el 2T26 ($912M sobre $1.935M)", "27% en el 2T25", "quarters.json (XBRL 10-Q 2T26)"),
        kp("SBC", "$265M en el 2T26 (14% de los ingresos)", "$160M (2T25)", "quarters.json (XBRL 10-Q 2T26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-02", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Valoración extrema (PER adelantado ≈ 81 en finviz): el precio ya descuenta años de este crecimiento.",
                         "La única dilución viene de la SBC y los planes S-8 «evergreen»."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +93% con aceleración {m.accel_pp:pp}, beat de BPA del 19%, guía +6,5% y el mayor EP del universo (+29% al cierre).",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 2T26.",
        quality=["Margen operativo GAAP del 47% y FCF por encima del beneficio: el crecimiento se autofinancia.", "SBC del 14% de los ingresos."],
        supply_read=f"Sin ampliaciones: solo planes S-8 de empleados. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, en planes 10b5-1.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 81 (finviz), el más caro del universo. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El líder del software por nota de negocio y el que más crece (+93%); en tendencia y a −13% del máximo.",
        risks=["Valoración: cualquier decepción se paga con caídas grandes.", "Dependencia del gobierno de EE. UU.", "Resultados el 2-nov tras el cierre."],
        plan=["Resultados del 3T26 el 2-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 28-oct.",
              "**EP A/B si:** BPA ≥ $0,43 (+5% sobre el consenso de $0,41 de finviz), comercial EE. UU. por encima del +134% y otra subida de la guía anual sobre $8.158M.",
              "**D si:** guía anual mantenida: con esta valoración, no subirla es una decepción.",
              "Técnica: en tendencia (EMA alineadas), sobre la SMA 200 y −13% desde el máximo."],
        verdict="El caso de crecimiento más fuerte del software (+93%, guía +6,5%, EP del +29%) con la valoración más alta. El 2-nov necesita otra subida de guía.")
    header = dict(verdict="+93%, guía +6,5% y EP del +29%: el más fuerte del software, también el más caro.",
                  setup="En tendencia; −13% desde máximos.", catalyst="2T26: ventas +7%, BPA +19%; guía +6,5%; EP +29%.",
                  quality="Margen GAAP 47%; FCF > beneficio.", supply="Sin ampliaciones; SBC 14%.", group="Líder del software.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


# ---------------------------------------------------------------- APP
def app():
    t = "APP"
    c, rows = base(t)
    pr = casekit.link(1751008, "0001751008-26-000057", "exhibit991-2q26earningspre.htm", "EX-99.1 8-K 5-ago-2026: resultados 2T26")
    s3 = casekit.link(1751008, "0001751008-26-000047", "s-3asr.htm", "S-3ASR 6-may-2026: shelf automático")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-05", "amc",
                         "Resultados 2T26: ingresos $1.924M (+53%), neto $1.267M, FCF $863M; guía 3T de ingresos $2.055–2.085M y EBITDA ajustado $1.710–1.740M (83%)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas −0,9% (fallo pequeño) y BPA +0,1% (en línea). Desaceleración del +59% al +53%. El mercado lo castigó: −19,0% en la apertura y −19,7% al cierre.")
    kpis = [
        kp("Guía 3T26", "Ingresos $2.055–2.085M (+7–8% secuencial); EBITDA ajustado $1.710–1.740M (margen 83%)", "—", *pr),
        kp("FCF y recompras", "FCF $863M en el 2T26; 1,1M acciones recompradas o retenidas por $551M", "—", *pr),
        kp("Margen operativo GAAP", "78% en el 2T26 ($1.494M sobre $1.924M)", "76% en el 2T25", "quarters.json (XBRL 10-Q 2T26)")]
    shelf = dict(id="shelf26", kind="shelf", name="Shelf automático S-3ASR (6-may-2026)", shares=None, capacity_usd=None, price_basis=None, gate="live", date="2026-05-06",
                 notes="Sin límite de importe (emisor WKSI). [VERIFY: si es para la compañía o para reventas de accionistas; sin uso conocido hasta hoy]", src=[s3])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-04", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El consejero delegado (Foroughi, ≥ 10%) acumula cientos de ventas fuera de planes 10b5-1 en 12 meses, y un consejero (Vivas) ha vendido $264M.",
                         "Desaceleración del +59% al +53% con un fallo pequeño en ventas: el mercado castiga a los líderes que frenan."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +53% con desaceleración {m.accel_pp:pp}, en línea con el consenso y castigado (−20%). EP a la baja.",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión (el 4T23 salía con ingresos negativos por la reexpresión de la venta del negocio de apps).",
        quality=["Margen operativo GAAP del 78%, el más alto del universo.", "Fondo de comercio e intangibles = 59% del patrimonio."],
        supply_read=f"Sin ampliaciones; recompras fuertes. Shelf automático abierto desde mayo. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "con el consejero delegado vendiendo fuera de plan de forma continua.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 13 (finviz), barato para su margen. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más castigado del software (−64% desde el máximo) pese al mejor margen: el mercado duda de la sostenibilidad del crecimiento publicitario.",
        risks=["Desaceleración.", "Ventas continuas del consejero delegado.", "Concentración en publicidad de juegos y comercio electrónico.", "Resultados el 4-nov tras el cierre."],
        plan=["Resultados del 3T26 el 4-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 30-oct.",
              "**EP A/B si:** ingresos ≥ $2.085M (techo de la guía) con reaceleración interanual y BPA ≥ $4,24 (+5% sobre el consenso de $4,04).",
              "**D si:** otra desaceleración o fallo en ventas: confirmaría el techo del crecimiento.",
              "Técnica: −64% desde el máximo, −39% bajo la SMA 200; RS en el percentil 0. Sin setup."],
        verdict="Márgenes del 78% y PER ≈ 13, pero desacelerando, castigado un 20% tras resultados y con el consejero delegado vendiendo sin parar. Solo un EP con reaceleración cambiaría la lectura.")
    header = dict(verdict="Margen del 78% y PER ≈ 13, pero desacelera y cayó un 20% tras resultados.",
                  setup="−64% desde máximos; sin setup.", catalyst="2T26: en línea con el consenso; −20% al cierre.",
                  quality="Margen 78%.", supply="Recompras; CEO vendiendo fuera de plan.", group="El más castigado del software.")
    finish(t, c, kpis, [e], [shelf, ins], forensic_float(t), text, header, events, [pr, s3, fx])


# ---------------------------------------------------------------- DDOG
def ddog():
    t = "DDOG"
    c, rows = base(t)
    pr = casekit.link(1561550, "0001628280-26-053829", "ex-991x20260630x8k.htm", "EX-99.1 8-K 6-ago-2026: resultados 2T26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-06", "bmo",
                         "Resultados 2T26: ingresos $1.121M (+36%), clientes > $100.000 de ARR 4.720 (+23%), FCF $279M; guía 3T $1.135–1.145M y 2026 $4.450–4.470M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +3,9% y BPA +11,5%. La guía del 3T ($1.140M en el punto medio) solo supone +1,7% secuencial: guía conservadora, como suele. "
                              "Reacción tibia: +2,4% en la apertura y +2,0% al cierre.")
    kpis = [
        kp("Clientes grandes", "≈ 4.720 clientes con ARR > $100.000 (+23%)", "≈ 3.850 (jun-2025)", *pr),
        kp("Guía", "3T26 $1.135–1.145M; 2026 $4.450–4.470M", "—", *pr),
        kp("Cartera (RPO)", "$3.471M a jun-2026 (XBRL)", "$2.426M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Margen operativo GAAP", "≈ 0% (beneficio operativo de $5M); SBC $220M, el 20% de los ingresos", "−4% (2T25)", "quarters.json (XBRL 10-Q 2T26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-04", kind="earnings", text="Resultados 3T26 antes de la apertura [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Los fundadores (Pomel y Le-Quoc) han vendido más de $450M en 12 meses, en planes 10b5-1, hasta un 43–44% de su posición en un trimestre.",
                         "Rentable solo en cifras ajustadas: la SBC (20% de los ingresos) se come el margen GAAP."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +36% con aceleración {m.accel_pp:pp} y beat claro, pero sin subida de guía cuantificada y con reacción tibia.",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión.",
        quality=["SBC del 20% de los ingresos: margen GAAP ≈ 0.", "FCF ($279M) muy por encima del beneficio GAAP por la SBC."],
        supply_read=f"Sin ampliaciones. La oferta viene de la SBC y de las ventas de directivos: {casekit.usd_m(insider_total(t))} en 12 meses, la cifra más alta del software junto a NET.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 83 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Representante del modelo por consumo que se beneficia de los clientes nativos de IA; crece más que SNOW y MDB.",
        risks=["Ventas de fundadores.", "Dependencia de clientes nativos de IA.", "Valoración.", "Resultados el 4-nov antes de la apertura."],
        plan=["Resultados del 3T26 el 4-nov antes de la apertura [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 30-oct.",
              "**EP A/B si:** ingresos ≥ $1.180M (≈ +3% sobre el techo de la guía, su patrón de beat) y guía anual por encima de $4.470M.",
              "**D si:** ingresos dentro de la guía: se rompería el patrón de beats y el consumo de IA estaría frenando.",
              "Técnica: en tendencia (EMA alineadas), sobre la SMA 200 y −18% desde el máximo."],
        verdict="Crecimiento sólido del modelo por consumo (+36%) con beats repetidos, pero margen GAAP nulo por la SBC y fundadores vendiendo fuerte. El 4-nov medirá el consumo de IA.")
    header = dict(verdict="+36% con beats repetidos; SBC del 20% y fundadores vendiendo.",
                  setup="En tendencia; −18% desde máximos.", catalyst="2T26: ventas +4%, BPA +11%; reacción tibia.",
                  quality="Margen GAAP ≈ 0 por la SBC.", supply="Sin ampliaciones; ventas de fundadores.", group="Consumo con clientes de IA.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


# ---------------------------------------------------------------- NET
def net():
    t = "NET"
    c, rows = base(t)
    pr = casekit.link(1477333, "0001477333-26-000053", "q226exhibit991.htm", "EX-99.1 8-K 6-ago-2026: resultados 2T26")
    cv = casekit.link(1477333, "0000950103-26-012340", "dp251721_8k.htm", "8-K 13-ago-2026: convertible 0% 2031 de $2.500M")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-06", "amc",
                         "Resultados 2T26: ingresos $696,1M (+36%), cRPO +35%; pérdida operativa GAAP de $205,7M (30% de los ingresos); guía 3T $736–737M y 2026 $2.864–2.870M",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +4,7% y BPA ajustado +8,1%. La pérdida operativa GAAP se triplica (−$67M → −$206M) y el margen bruto baja del 74,9% al 71,8% "
                              "[VERIFY: causa en el 10-Q del 2T26]. El mercado abrió +11,8% y cerró +5,6%.")
    kpis = [
        kp("cRPO", "+35% interanual en el 2T26; RPO $2.732M (XBRL)", "RPO $1.977M (jun-2025)", *pr),
        kp("Márgenes", "Bruto GAAP 71,8% (74,9% un año antes); operativo GAAP −29,6%; ajustado +13,8%", "—", *pr),
        kp("FCF", "$56,4M (8% de los ingresos)", "$33,3M (6%)", *pr),
        kp("Guía", "3T26 ingresos $736–737M y beneficio operativo ajustado $129–130M; 2026 $2.864–2.870M", "—", *pr)]
    conv = dict(id="conv31", kind="convertible", name="Convertible 0% 2031 ($2.500M, conversión ≈ $496,94)", shares=round(2_500_000 * 2.0123), capacity_usd=None,
                price_basis=496.94, gate="gated", date="2031-08-15",
                notes="2,0123 acciones por $1.000 (≈ 5,03M acciones), fuera de dinero a {m.price:px}. Capped call de $259,5M que reduce la dilución hasta su techo. Vence el 15-ago-2031.",
                src=[cv])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-05", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El consejero delegado (Prince) ha vendido $340M en 12 meses, hasta un 97% de su posición directa en un trimestre (en plan 10b5-1), y la presidenta $247M.",
                         "Pérdida operativa GAAP en aumento y margen bruto a la baja mientras crece al +36%: la red de cómputo para IA cuesta."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +36% con aceleración {m.accel_pp:pp} y beat, pero pérdidas GAAP crecientes y margen bruto a la baja.",
        financials_note="Trimestres de XBRL hasta el 2T26. El convertible de $2.500M (agosto) es posterior al último balance.",
        quality=["Margen bruto a la baja (74,9% → 71,8%).", "Pérdida operativa GAAP del 30% de los ingresos.", "SBC $160M en el 2T26 (23% de los ingresos)."],
        supply_read=f"Convertible 2031 de $2.500M fuera de dinero con capped call. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, encabezadas por el consejero delegado.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 177 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Crece como DDOG (+36%) pero con márgenes peores y el PER más alto del universo.",
        risks=["Márgenes a la baja.", "Ventas del consejero delegado.", "Valoración extrema.", "Resultados el 5-nov tras el cierre."],
        plan=["Resultados del 3T26 el 5-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 31-oct.",
              "**EP A/B si:** ingresos ≥ $750M (≈ +2% sobre la guía), margen bruto estabilizado y guía anual por encima de $2.870M.",
              "**D si:** margen bruto por debajo del 71% y pérdida operativa creciente.",
              "Técnica: bajo las EMA, sobre la SMA 200 y −20% desde el máximo. Sin setup."],
        verdict="Crecimiento acelerando (+36%) con márgenes empeorando, PER extremo y el consejero delegado vendiendo casi toda su posición directa. Caso de alto riesgo.")
    header = dict(verdict="+36%, pero márgenes a la baja, PER ≈ 177 y el CEO vendiendo.",
                  setup="Bajo las EMA; −20% desde máximos.", catalyst="2T26: ventas +5%, BPA +8%.",
                  quality="Margen bruto a la baja; pérdida GAAP.", supply="Convertible 2031; ventas del CEO.", group="El más caro.")
    finish(t, c, kpis, [e], [conv, ins], forensic_float(t), text, header, events, [pr, cv, fx])

def _evento(c, siguiente, fecha=None):
    """Fecha de resultados aún no anunciada: estimación (últimos resultados + 91 días) con su motivo."""
    e = (c.get("events") or [{}])[0]
    return [dict(date=fecha or e.get("date"), kind="earnings", text=f"{siguiente} [VERIFY: fecha no anunciada; estimada como últimos resultados + 91 días]", src=[])]


def _std(t, c, rows, cid, qend, date, timing, headline, pr, note, guide_raise=None, guide_change=None, eps=True, extra_src=()):
    k, fx = fv(t)
    e = casekit.earnings(c, rows, cid, qend, date, timing, headline, [pr, *extra_src, fx], rev_surprise=round(k["sales_surprise_pct"], 1),
                         eps_surprise=round(k["eps_surprise_pct"], 1) if eps else None, guide_raise=guide_raise, guide_change=guide_change, note=note)
    return e, fx


# ---------------------------------------------------------------- ORCL
def orcl():
    t = "ORCL"
    c, rows = base(t)
    pr = casekit.link(1341439, "0001193125-26-387905", "orcl-ex99_1.htm", "EX-99.1 8-K 10-sep-2026: resultados 1T FY27")
    pf = casekit.link(1341439, "0001193125-26-037818", "d60756d424b5.htm", "424B5 feb-2026: preferentes obligatorias Serie D 6,50% ($5.000M)")
    e, fx = _std(t, c, rows, "q1fy27", "2026-08-31", "2026-09-10", "amc",
                 "Resultados 1T FY27: ingresos $19.345M (+30%); RPO $664.000M (+$209.000M); > $30.000M de contratos nuevos de nube de IA; FCF −$5.000M; guía FY27 ≥ $90.000M y BPA ajustado $8,10",
                 pr, "Consenso de finviz: ventas +1,1% y BPA +10,4%. FCF negativo (−$5.000M) por el capex de OCI ($28.499M en el trimestre). "
                     "La guía del 2T FY27 de BPA ajustado cae −14% a −18% interanual incluida una ganancia de inversión del año anterior. El mercado abrió +7,5% y cerró −1,7%.",
                 guide_raise=True)
    kpis = [
        kp("Cartera contratada (RPO)", "$664.000M a 31-ago-2026 (+$209.000M interanual); > $30.000M de contratos de nube de IA en el trimestre", "$455.300M (ago-2025)", *pr),
        kp("Capex y FCF", "Capex $28.499M en el trimestre (XBRL); FCF −$5.000M", "Capex $8.502M (1T FY26)", *pr),
        kp("Guía FY27", "Ingresos ≥ $90.000M; BPA ajustado $8,10; nube total +65–71% en el 2T", "—", *pr),
        kp("GPU entregadas", "> 300.000 GPU a clientes de nube de IA desde el fin del 4T, casi el triple de capacidad que en el 4T FY26", "—", *pr)]
    pref = dict(id="pref_d", kind="convertible", name="Preferentes de conversión obligatoria Serie D 6,50% ($5.000M, feb-2026)", shares=None, capacity_usd=None, price_basis=None,
                gate="dated", date="2029-01-15",
                notes="100M de acciones depositarias a $50; conversión obligatoria en acciones el 15-ene-2029 (dividendo del 6,50%). [VERIFY: tasas mínima y máxima de conversión en el 424B5]",
                src=[pf])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["La cartera de $664.000M está muy concentrada en contratos de IA (OpenAI incluido) y obliga a un capex enorme: FCF negativo y deuda creciente.",
                         "Financia parte con preferentes de conversión obligatoria ($5.000M): dilución segura en 2029."],
        catalyst_read="El 1T FY27 puntúa {m.cat_q1fy27_score:sc}: +30% con aceleración {m.accel_pp:pp}, cartera disparada y beat de BPA, pero FCF negativo y el mercado vendió el día.",
        financials_note="Trimestres de XBRL hasta el 1T FY27; regenerados el 19-oct con el 4T derivado de la misma versión. El margen bruto no sale de companyfacts.",
        quality=["FCF negativo por el capex de OCI.", "Fondo de comercio e intangibles = 98% del patrimonio."],
        supply_read="Preferentes obligatorias de $5.000M (conversión en 2029) y bonos en febrero y junio. "
                    f"Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 12 (finviz), el más barato del software grande. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El caso raro del software: −60% desde el máximo con la cartera más grande del grupo tras MSFT; el mercado duda del retorno del capex y de la concentración en OpenAI.",
        risks=["Concentración de la cartera en pocos clientes de IA.", "FCF negativo y deuda.", "Dilución de las preferentes en 2029.", "Resultados ≈ 10-dic."],
        plan=["Resultados del 2T FY27 hacia el 10-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** RPO por encima de $700.000M, nube +65% o más y FCF mejorando.",
              "**D si:** otro FCF negativo grande sin aceleración de ingresos.",
              "Técnica: −60% desde el máximo, −20% bajo la SMA 200. Sin setup."],
        verdict="La mayor apuesta del software por la nube de IA (RPO $664.000M) con FCF negativo, deuda y preferentes obligatorias. Barata por PER, pero con el retorno del capex por demostrar.")
    header = dict(verdict="RPO de $664.000M y +30%, pero FCF −$5.000M y −60% desde máximos.",
                  setup="−60% desde máximos; sin setup.", catalyst="1T FY27: ventas +1%, BPA +10%; guía FY27 ≥ $90.000M.",
                  quality="FCF negativo; mucho fondo de comercio.", supply="Preferentes obligatorias $5.000M.", group="La apuesta de IA del software.")
    finish(t, c, kpis, [e], [pref, ins], forensic_float(t), text, header, _evento(c, "Resultados 2T FY27"), [pr, pf, fx])


# ---------------------------------------------------------------- CRM
def crm():
    t = "CRM"
    c, rows = base(t)
    pr = casekit.link(1108524, "0001108524-26-000187", "crm-q2fy27xexhibit991.htm", "EX-99.1 8-K 26-ago-2026: resultados 2T FY27")
    e, fx = _std(t, c, rows, "q2fy27", "2026-07-31", "2026-08-26", "amc",
                 "Resultados 2T FY27: ingresos $11.345M (+11%, $456M de Informatica); cRPO +14% en moneda constante; sube la guía FY27 en $200M; ARR de Agentforce > $1.500M (+240%)",
                 pr, "Consenso de finviz: ventas +0,1% y BPA +80,5%; la sorpresa de BPA está inflada por la recompra acelerada de $25.000M (103M de acciones entregadas) "
                     "[VERIFY: base del consenso de BPA]. Orgánico ≈ +7% sin Informatica. EP de verdad: hueco del +11,9% y cierre del +22,6% con volumen 3,9×.",
                 guide_raise=True)
    kpis = [
        kp("IA", "ARR de Agentforce y Data 360 ≈ $3.900M (+210%); Agentforce > $1.500M (+240%)", "—", *pr),
        kp("cRPO", "+14% en moneda constante (acelera)", "—", *pr),
        kp("Recompra acelerada", "$25.000M; 103M acciones entregadas al inicio", "—", *pr),
        kp("Deuda", "$39.288M a jul-2026 (XBRL), tras financiar la recompra y Informatica", "$8.436M (jul-2025)", "quarters.json (XBRL 10-Q 2T FY27)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El BPA sube por la recompra acelerada de $25.000M financiada con deuda, no solo por el negocio.",
                         "El crecimiento orgánico ronda el +7%: Informatica aporta $456M del trimestre."],
        catalyst_read="El 2T FY27 puntúa {m.cat_q2fy27_score:sc}: +11% con desaceleración {m.accel_pp:pp}, guía subida y el EP más fuerte del software tras PLTR (+23% al cierre).",
        financials_note="Trimestres de XBRL hasta el 2T FY27. El neto del 2T ($3.526M) supera al operativo: revisar partidas no operativas en el 10-Q [VERIFY].",
        quality=["Fondo de comercio e intangibles = 170% del patrimonio (Informatica y compras).", "Deuda multiplicada por 4,7 en un año."],
        supply_read=f"Sin ampliaciones; recompra acelerada de $25.000M (reduce acciones). Planes S-8 de las compras. Directivos casi sin ventas ({casekit.usd_m(insider_total(t))}; con compras de $27,5M).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 15 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El representante del modelo por usuario que el mercado ha vuelto a premiar: EP en agosto y RS 3m en percentil 100 dentro del software.",
        risks=["Deuda alta tras la recompra.", "Crecimiento orgánico bajo.", "Resultados ≈ 25-nov."],
        plan=["Resultados del 3T FY27 hacia el 25-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** cRPO acelerando por encima del +14% y otra subida de la guía; ARR de Agentforce acelerando.",
              "**D si:** cRPO por debajo del +12%.",
              "Técnica: en tendencia (EMA alineadas), −11% desde el máximo y +21% sobre la SMA 200."],
        verdict="El modelo por usuario reaccionando con IA (Agentforce +240%) y un EP limpio, pero con crecimiento orgánico bajo y un BPA ayudado por una recompra con deuda.")
    header = dict(verdict="EP del +23% con Agentforce +240%; orgánico ≈ +7% y deuda ×4,7.",
                  setup="En tendencia; −11% desde máximos.", catalyst="2T FY27: guía +$200M; EP +23%.",
                  quality="Mucho fondo de comercio; deuda.", supply="Recompra acelerada.", group="Modelo por usuario premiado.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 3T FY27"), [pr, fx])


# ---------------------------------------------------------------- ADBE
def adbe():
    t = "ADBE"
    c, rows = base(t)
    pr = casekit.link(796343, "0000796343-26-000147", "adbeex991q326.htm", "EX-99.1 8-K 10-sep-2026: resultados 3T FY26")
    ce = casekit.link(796343, "0000796343-26-000144", "adbe-20260902.htm", "8-K 8-sep-2026: relevo del consejero delegado")
    e, fx = _std(t, c, rows, "q3fy26", "2026-08-28", "2026-09-10", "amc",
                 "Resultados 3T FY26: ingresos $6.760M (+13%); ARR total $27.500M; ARR de productos de IA +150%; 1.000M de usuarios activos al mes; sube los objetivos anuales",
                 pr, "Consenso de finviz: ventas +1,0% y BPA +0,9% (en línea). Sube los objetivos anuales de ingresos y BPA sin cifra comparada en la nota. "
                     "Relevo del consejero delegado (Narayen). Reacción plana: −2,7% en la apertura y +1,4% al cierre.",
                 guide_raise=True, extra_src=(ce,))
    kpis = [
        kp("ARR y RPO", "ARR $27.500M; RPO $22.160M (67% en 12 meses)", "—", *pr),
        kp("Suscripción por grupo", "Total $6.560M (+14%): profesionales y consumo $1.910M (+16%), creativos y marketing $4.650M (+13%)", "—", *pr),
        kp("Recompras", "≈ 9,5M acciones en el trimestre", "—", *pr),
        kp("Margen operativo GAAP", "35% en el 3T FY26 ($2.354M sobre $6.760M)", "36% en el 3T FY25", "quarters.json (XBRL 10-Q 3T FY26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["Relevo del consejero delegado tras casi 20 años (Narayen): el mercado espera la estrategia del nuevo.",
                         "PER adelantado ≈ 9: el mercado descuenta que la IA generativa sustituye parte de su negocio."],
        catalyst_read="El 3T FY26 puntúa {m.cat_q3fy26_score:sc}: +13% estable, en línea con el consenso, objetivos subidos y reacción plana.",
        financials_note="Trimestres de XBRL hasta el 3T FY26.",
        quality=["Margen operativo GAAP del 35% y FCF alto.", "Fondo de comercio e intangibles = 127% del patrimonio por las recompras (patrimonio bajo)."],
        supply_read=f"Sin dilución: recompras fuertes. Ventas del consejero delegado saliente {casekit.usd_m(insider_total(t))} en 12 meses, varias fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 9 (finviz), el más barato del software. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más barato del software por PER con márgenes de primera: el caso opuesto a PLTR.",
        risks=["Sustitución por IA generativa.", "Relevo en la dirección.", "Resultados ≈ 10-dic."],
        plan=["Resultados del 4T FY26 hacia el 10-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ARR de IA acelerando y guía de FY27 por encima del +10% con el nuevo consejero delegado.",
              "**D si:** guía de FY27 por debajo del +10%.",
              "Técnica: −33% desde el máximo, bajo la SMA 200. Sin setup."],
        verdict="Márgenes y caja de primera a PER ≈ 9, con un relevo en la dirección y el mercado temiendo la sustitución por IA. Caso de valor, no de momentum.")
    header = dict(verdict="+13% estable, margen 35% y PER ≈ 9; relevo del consejero delegado.",
                  setup="−33% desde máximos; sin setup.", catalyst="3T FY26: en línea; objetivos subidos.",
                  quality="Margen 35%.", supply="Recompras.", group="El más barato del software.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 4T FY26"), [pr, ce, fx])


# ---------------------------------------------------------------- INTU
def intu():
    t = "INTU"
    c, rows = base(t)
    pr = casekit.link(896878, "0000896878-26-000029", "fy26q4earningspressrelease.htm", "EX-99.1 8-K 25-ago-2026: resultados 4T FY26 y guía FY27")
    e, fx = _std(t, c, rows, "q4fy26", "2026-07-31", "2026-08-25", "amc",
                 "Resultados 4T FY26: ingresos $4.354M (+14%), FY26 > $20.000M (+14%); guía FY27 de ingresos $23.279–23.512M (+9–10%): desacelera",
                 pr, "Consenso de finviz: ventas +2,0%. La sorpresa de BPA de finviz (−39%) no se usa: la compañía cambió su BPA ajustado para incluir la compensación en acciones. "
                     "La guía de FY27 (+9–10%) queda por debajo del +14% de FY26. El mercado lo vendió: −9,5% en la apertura y −3,2% al cierre.",
                 eps=False)
    kpis = [
        kp("Guía FY27", "Ingresos $23.279–23.512M (+9–10%); Global Business Solutions $13.068–13.158M (+13–14%); 1T FY27 $4.294–4.313M (+11%)", "FY26 +14%", *pr),
        kp("Negocio online (FY26)", "Ecosistema online $9.900M (+19%; +23% sin Mailchimp); QuickBooks Online Accounting +23%", "—", *pr),
        kp("Consumo (FY26)", "TurboTax $5.300M (+7%; TurboTax Live +37%); Credit Karma $2.600M (+20%)", "—", *pr),
        kp("Cambio de criterio", "El BPA ajustado incluye desde FY27 la compensación en acciones ($5,81 por acción en la guía): no comparable con el histórico", "—", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["Guía de FY27 desacelerando al +9–10% y cambio de criterio del BPA ajustado: el mercado lo leyó como una rebaja.",
                         "El consumo (TurboTax +7%) se frena; el crecimiento lo lleva el negocio de pymes (QuickBooks)."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +14% con aceleración {m.accel_pp:pp}, pero una guía que desacelera y el mercado vendiéndolo.",
        financials_note="Trimestres de XBRL hasta el 4T FY26 (cierre en julio). Muy estacional: el 3T fiscal (impuestos) concentra el beneficio.",
        quality=["Fondo de comercio e intangibles = 98% del patrimonio (Credit Karma, Mailchimp).", "Estacionalidad fuerte por la campaña de impuestos."],
        supply_read=f"Sin ampliaciones; bonos en junio y shelf automático en septiembre. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 13 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El más castigado del modelo por usuario tras APP (−53% desde el máximo) por la desaceleración y el miedo a la IA en los impuestos.",
        risks=["Desaceleración del consumo.", "Sustitución por IA en la preparación de impuestos.", "Resultados ≈ 20-nov."],
        plan=["Resultados del 1T FY27 hacia el 20-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos por encima de $4.313M (techo de la guía) y guía de FY27 mantenida o subida.",
              "**D si:** rebaja de la guía de FY27.",
              "Técnica: −53% desde el máximo, −13% bajo la SMA 200. Sin setup."],
        verdict="Negocio sólido (QuickBooks +23%) desacelerando en conjunto (+9–10% guiado) y castigado a la mitad de su máximo. Caso de valor a la espera de un cambio de tendencia.")
    header = dict(verdict="Guía FY27 +9–10% (desacelera); −53% desde máximos.",
                  setup="−53% desde máximos; sin setup.", catalyst="4T FY26: ventas +2%; guía floja; −3% al cierre.",
                  quality="Estacional; mucho fondo de comercio.", supply="Sin ampliaciones.", group="El más castigado del modelo por usuario.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 1T FY27"), [pr, fx])


# ---------------------------------------------------------------- WDAY
def wday():
    t = "WDAY"
    c, rows = base(t)
    pr = casekit.link(1327811, "0001327811-26-000042", "wday-07312026x991.htm", "EX-99.1 8-K 27-ago-2026: resultados 2T FY27")
    rs = casekit.link(1327811, "0001327811-26-000048", "wday-20260929.htm", "8-K 29-sep-2026: reestructuración (Item 2.05) y guía reiterada")
    e, fx = _std(t, c, rows, "q2fy27", "2026-07-31", "2026-08-27", "amc",
                 "Resultados 2T FY27: ingresos $2.649M (+12,8%), suscripción $2.471M (+13,9%); cartera de suscripción a 12 meses $9.034M (+14,2%); sube la guía FY27 de suscripción a $9.940–9.950M (+13%)",
                 pr, "Consenso de finviz: ventas +0,5% y BPA +5,3%. Sube la guía de margen operativo ajustado al 31%. El 29-sep anunció una reestructuración ($65–80M de cargos) "
                     "y reiteró la guía. Reacción plana: −1,2% en la apertura y +0,7% al cierre.",
                 guide_raise=True, extra_src=(rs,))
    kpis = [
        kp("Cartera de suscripción", "A 12 meses $9.034M (+14,2%); total $27.403M (+8,0%)", "—", *pr),
        kp("Guía", "FY27 suscripción $9.940–9.950M (+13%) y margen operativo ajustado 31%; 3T suscripción $2.515M (+12%) y margen 30%", "—", *pr),
        kp("Reestructuración", "$65–80M de cargos (despidos y oficinas), $55–70M en el 3T FY27", "—", *rs),
        kp("Margen operativo GAAP", "11,8% en el 2T FY27", "10,6% en el 2T FY26", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El fundador (Duffield, ≥ 10%) ha vendido $557M en 12 meses, hasta un 91% de una posición en un trimestre (en plan 10b5-1); sigue con ≈ 19% (13G).",
                         "Reestructuración con despidos mientras crece al +13%: busca margen, no crecimiento."],
        catalyst_read="El 2T FY27 puntúa {m.cat_q2fy27_score:sc}: +13% estable, beat pequeño y guía de suscripción subida; reacción plana.",
        financials_note="Trimestres de XBRL hasta el 2T FY27. El catalizador de la Fase 1 era el 8-K de reestructuración (29-sep, también Item 2.02): corregido al informe del 27-ago. "
                        "El neto del 2T FY27 ($632M) supera al operativo [VERIFY: partida fiscal o de inversiones en el 10-Q].",
        quality=["Margen GAAP del 11,8% con la SBC al 17% de los ingresos.", "Fondo de comercio e intangibles = 87% del patrimonio."],
        supply_read=f"Sin ampliaciones; shelf automático desde mayo (posible uso para ventas del fundador [VERIFY]). Ventas de insiders {casekit.usd_m(insider_total(t))} en 12 meses, casi todo Duffield.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 14 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El modelo por usuario estable (+13%) y en tendencia, sin la aceleración de CRM ni el castigo de INTU.",
        risks=["Ventas del fundador.", "Crecimiento estancado en el +13%.", "Resultados ≈ 26-nov."],
        plan=["Resultados del 3T FY27 hacia el 26-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** suscripción por encima de $2.515M con la cartera a 12 meses acelerando sobre el +14%.",
              "**D si:** cartera a 12 meses por debajo del +13%.",
              "Técnica: en tendencia (EMA alineadas), +22% sobre la SMA 200 y −23% desde el máximo."],
        verdict="Negocio estable (+13%) con margen al alza y en tendencia, sin catalizador fuerte y con el fundador vendiendo. Ni líder ni rezagado del grupo.")
    header = dict(verdict="+13% estable, guía subida y reestructuración; el fundador vende.",
                  setup="En tendencia; −23% desde máximos.", catalyst="2T FY27: ventas +0,5%, BPA +5%; guía subida.",
                  quality="Margen GAAP 11,8%.", supply="Ventas del fundador.", group="Estable.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 3T FY27", "2026-11-26"), [pr, rs, fx])


# ---------------------------------------------------------------- SNOW
def snow():
    t = "SNOW"
    c, rows = base(t)
    pr = casekit.link(1640147, "0001640147-26-000033", "fy2027q2earnings.htm", "EX-99.1 8-K 2-sep-2026: resultados 2T FY27")
    cv = casekit.link(1640147, "0001640147-26-000043", "snow-20260928.htm", "8-K 28-sep-2026: convertibles 0% 2029 y 2031 ($3.750M)")
    e, fx = _std(t, c, rows, "q2fy27", "2026-07-31", "2026-09-02", "amc",
                 "Resultados 2T FY27: ingresos $1.547M (+35%), producto $1.490M (+37%); retención neta 126%; sube la guía FY27 de producto al +36%; 3T de producto $1.588–1.593M (+37–38%)",
                 pr, "Consenso de finviz: ventas +4,3% y BPA +38,8%. EP de verdad: hueco del +23,4% y cierre del +16,6% con volumen 4,2×.",
                 guide_raise=True)
    kpis = [
        kp("Retención y clientes", "Retención neta 126%; 828 clientes con > $1M de producto en 12 meses (+27%)", "—", *pr),
        kp("Guía", "3T FY27 producto $1.588–1.593M (+37–38%) y margen operativo ajustado 15,5%; FY27 producto +36%", "—", *pr),
        kp("RPO", "$9.000M (+30%)", "$6.900M (jul-2025)", *pr),
        kp("Margen operativo GAAP", "−17% en el 2T FY27 (SBC $424M, el 27% de los ingresos)", "−30% en el 2T FY26", "quarters.json (XBRL 10-Q 2T FY27)")]
    conv = dict(id="conv2931", kind="convertible", name="Convertibles 0% 2029 ($2.000M, $500,38) y 2031 ($1.750M, $483,98)", shares=round(2_000_000 * 1.9985 + 1_750_000 * 2.0662),
                capacity_usd=None, price_basis=483.98, gate="gated", date="2029-01-01",
                notes="≈ 4,00M + 3,62M acciones; fuera de dinero a {m.price:px}. [VERIFY: vencimientos exactos y capped call en el 8-K]", src=[cv])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El exconsejero delegado (Slootman, consejero) ha vendido $761M en 12 meses, hasta un 86% de su posición en un trimestre (en plan 10b5-1).",
                         "Pérdida GAAP por la SBC (27% de los ingresos): rentable solo en cifras ajustadas."],
        catalyst_read="El 2T FY27 puntúa {m.cat_q2fy27_score:sc}: +35% con aceleración {m.accel_pp:pp}, beat amplio, guía subida y EP con volumen 4,2×.",
        financials_note="Trimestres de XBRL hasta el 2T FY27; regenerados el 19-oct con el 4T derivado de la misma versión. Los convertibles de septiembre son posteriores al último balance.",
        quality=["SBC del 27% de los ingresos.", "Fondo de comercio e intangibles = 96% del patrimonio (patrimonio bajo por recompras)."],
        supply_read=f"Convertibles de $3.750M en septiembre (≈ 7,6M acciones, fuera de dinero). Ventas de insiders {casekit.usd_m(insider_total(t))} en 12 meses, encabezadas por Slootman.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 101 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El modelo por consumo acelerando más que DDOG y MDB (+37% en producto) con EP reciente; más caro y con más SBC.",
        risks=["SBC y valoración.", "Ventas de Slootman.", "Resultados ≈ 2-dic."],
        plan=["Resultados del 3T FY27 hacia el 2-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** producto ≥ $1.620M (≈ +2% sobre el techo de la guía) y guía FY27 por encima del +36%.",
              "**D si:** retención neta por debajo del 125%.",
              "Técnica: sobre la SMA 200 (+31%), bajo las EMA cortas; −20% desde el máximo."],
        verdict="El modelo por consumo acelerando (+37%) con EP en septiembre y guía subida, pero con SBC muy alta, convertibles nuevos y Slootman vendiendo.")
    header = dict(verdict="Producto +37%, EP en septiembre y guía subida; SBC 27% y convertibles.",
                  setup="Sobre la SMA 200; −20% desde máximos.", catalyst="2T FY27: ventas +4%, BPA +39%; EP +17%.",
                  quality="SBC 27%; pérdida GAAP.", supply="Convertibles $3.750M; Slootman vende.", group="Consumo que más acelera.")
    finish(t, c, kpis, [e], [conv, ins], forensic_float(t), text, header, _evento(c, "Resultados 3T FY27"), [pr, cv, fx])


# ---------------------------------------------------------------- MDB
def mdb():
    t = "MDB"
    c, rows = base(t)
    pr = casekit.link(1441816, "0001628280-26-059794", "mdb-073126xex991xrelease.htm", "EX-99.1 8-K 1-sep-2026: resultados 2T FY27")
    ce = casekit.link(1441816, "0001628280-26-063657", "mdb-20260924.htm", "8-K 24-sep-2026: salida del consejero delegado (CJ Desai)")
    e, fx = _std(t, c, rows, "q2fy27", "2026-07-31", "2026-09-01", "amc",
                 "Resultados 2T FY27: ingresos $771,7M (+30%, el mayor en años), Atlas +29%; RPO $1.519M (+91%), cRPO $797M (+73%); sube la guía FY27; FCF $137,6M",
                 pr, "Consenso de finviz: ventas +5,0% y BPA +17,6%. Pese al beat y la subida de guía, el mercado lo vendió: −12,7% en la apertura y −13,5% al cierre con volumen 4,9×. "
                     "El 24-sep salió el consejero delegado (CJ Desai); Dev Ittycheria vuelve como interino.",
                 guide_raise=True, extra_src=(ce,))
    kpis = [
        kp("Cartera", "RPO $1.519M (+91%); cRPO $797M (+73%)", "RPO $794M (jul-2025)", *pr),
        kp("Margen", "Operativo ajustado 24% (15% un año antes); GAAP positivo ($28M)", "—", *pr),
        kp("Dirección", "Sale el consejero delegado CJ Desai (24-sep-2026); Dev Ittycheria, consejero delegado interino", "—", *ce),
        kp("FCF", "$137,6M (casi el doble)", "$69,9M", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["Salida del consejero delegado tres semanas después de subir la guía: incertidumbre de dirección.",
                         "Caída del −13,5% con beat y guía subida: el mercado no se fía del ritmo de Atlas."],
        catalyst_read="El 2T FY27 puntúa {m.cat_q2fy27_score:sc}: +30% con aceleración {m.accel_pp:pp}, beat amplio y guía subida, pero EP a la baja (−13,5%) y salida del consejero delegado.",
        financials_note="Trimestres de XBRL hasta el 2T FY27.",
        quality=["Rentable en GAAP por primera vez de forma sostenida.", "SBC del 19% de los ingresos."],
        supply_read=f"Sin ampliaciones. Ventas de consejeros {casekit.usd_m(insider_total(t))} en 12 meses, varias fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 43 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="«Líder enfriado» del consumo: crece +30% con la cartera disparando, pero castigado por la dirección.",
        risks=["Relevo del consejero delegado.", "Ritmo de Atlas.", "Resultados ≈ 1-dic."],
        plan=["Resultados del 3T FY27 hacia el 1-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** Atlas acelerando sobre el +29%, nueva subida de guía y un consejero delegado definitivo.",
              "**D si:** guía mantenida con dirección interina.",
              "Técnica: líder enfriado (−29% desde el máximo, en la SMA 200). Sin setup."],
        verdict="Fundamentales acelerando (+30%, cartera +91%) castigados por el mercado y por la salida del consejero delegado. Candidato a EP si la dirección se aclara.")
    header = dict(verdict="+30%, cartera +91% y guía subida, pero −13,5% tras resultados y sin consejero delegado.",
                  setup="Líder enfriado; −29% desde máximos.", catalyst="2T FY27: ventas +5%, BPA +18%; −13,5% al cierre.",
                  quality="Rentable en GAAP.", supply="Sin ampliaciones.", group="Líder enfriado del consumo.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 3T FY27"), [pr, ce, fx])


# ---------------------------------------------------------------- CRWD
def crwd():
    t = "CRWD"
    c, rows = base(t)
    pr = casekit.link(1535527, "0001535527-26-000029", "crwd-20260826xex991.htm", "EX-99.1 8-K 26-ago-2026: resultados 2T FY27")
    e, fx = _std(t, c, rows, "q2fy27", "2026-07-31", "2026-08-26", "amc",
                 "Resultados 2T FY27: ingresos $1.471M (+26%); ARR nuevo neto récord de $333M (+51%); ARR $5.840M (+25%); sube la guía de ARR nuevo neto de FY27 en 630 pb, al +34%",
                 pr, "Consenso de finviz: ventas +2,1% y BPA +6,3%. EP de verdad: hueco del +10,1% y cierre del +20,5% con volumen 2,5×.",
                 guide_raise=True)
    kpis = [
        kp("ARR", "$5.840M (+25%); nuevo neto $333M (+51%); Falcon Flex $2.290M (+101%)", "—", *pr),
        kp("Módulos", "51% / 35% / 26% de clientes con 6+ / 7+ / 8+ módulos", "—", *pr),
        kp("Margen de suscripción", "GAAP 78%; ajustado 81%", "77% / 80%", *pr),
        kp("FCF", "$377,4M (récord del 2T)", "$283,6M", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El fundador (Kurtz) ha vendido $318M en 12 meses con decenas de ventas fuera de planes 10b5-1; el CFO, $158M.",
                         "PER adelantado ≈ 142: el más caro de seguridad."],
        catalyst_read="El 2T FY27 puntúa {m.cat_q2fy27_score:sc}: +26% estable, ARR nuevo neto +51% y guía subida, con EP del +20%.",
        financials_note="Trimestres de XBRL hasta el 2T FY27; regenerados el 19-oct con el 4T derivado de la misma versión.",
        quality=["Pérdida GAAP pequeña por la SBC ($377M, el 26% de los ingresos).", "FCF muy por encima del beneficio por la SBC."],
        supply_read=f"Sin ampliaciones; shelf automático desde septiembre. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, con muchas fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 142 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El líder de seguridad por ARR nuevo (+51%) y con EP reciente; más caro que PANW y ZS.",
        risks=["Valoración.", "Ventas del fundador fuera de plan.", "Resultados ≈ 1-dic."],
        plan=["Resultados del 3T FY27 hacia el 1-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ARR nuevo neto por encima de $333M (récord) y otra subida de la guía.",
              "**D si:** ARR nuevo neto desacelerando.",
              "Técnica: en tendencia (EMA alineadas), +42% sobre la SMA 200 y −21% desde el máximo."],
        verdict="El líder de seguridad acelerando el ARR nuevo (+51%) con EP en agosto y en tendencia, pero con la valoración más alta y el fundador vendiendo fuera de plan.")
    header = dict(verdict="ARR nuevo +51%, guía subida y EP del +20%; PER ≈ 142.",
                  setup="En tendencia; −21% desde máximos.", catalyst="2T FY27: ventas +2%, BPA +6%; EP +20%.",
                  quality="SBC 26%; FCF alto.", supply="Ventas del fundador fuera de plan.", group="Líder de seguridad.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 3T FY27"), [pr, fx])


# ---------------------------------------------------------------- ZS
def zs():
    t = "ZS"
    c, rows = base(t)
    pr = casekit.link(1713683, "0001713683-26-000156", "zs-07312026_991.htm", "EX-99.1 8-K 3-sep-2026: resultados 4T FY26")
    e, fx = _std(t, c, rows, "q4fy26", "2026-07-31", "2026-09-03", "amc",
                 "Resultados 4T FY26: ingresos $898M (+25%); ARR $3.771M (+25%; +20% sin Red Canary); guía FY27 de ARR +16,6–17,4% y 1T de ingresos $935–939M (+19%)",
                 pr, "Consenso de finviz: ventas +2,4% y BPA +9,3%. El crecimiento orgánico es menor que el publicado: Red Canary aporta $141M de ARR. "
                     "La guía de FY27 desacelera. El mercado lo vendió: −6,6% en la apertura y −4,5% al cierre.")
    kpis = [
        kp("ARR", "$3.771M (+25%); sin Red Canary $3.630M (+20%); nuevo neto $246M", "—", *pr),
        kp("Guía FY27", "ARR $4.396–4.426M (+16,6–17,4%); margen de FCF 23,0–23,5%; 1T ingresos $935–939M (+19%)", "—", *pr),
        kp("FCF", "4T FY26 $60,8M (7% de los ingresos) por capex de $218,5M; FY26 $779,1M (23%)", "4T FY25 $171,9M (24%)", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El +25% incluye la compra de Red Canary: el orgánico es +20% y la guía de FY27 baja al +17%.",
                         "El capex de centros de datos propios se dispara: FCF del 4T al 7% de los ingresos."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +25% con beat pequeño, pero orgánico +20% y guía desacelerando; el mercado lo vendió.",
        financials_note="Trimestres de XBRL hasta el 4T FY26.",
        quality=["SBC del 24% de los ingresos.", "Capex al alza ($200M en el 4T)."],
        supply_read=f"Sin ampliaciones. Ventas de directivos pequeñas ({casekit.usd_m(insider_total(t))}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 37 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La seguridad que desacelera: por detrás de CRWD (ARR nuevo +51%) y PANW (NGS +63%).",
        risks=["Desaceleración del ARR.", "Capex y FCF.", "Resultados ≈ 2-dic."],
        plan=["Resultados del 1T FY27 hacia el 2-dic [VERIFY: fecha no anunciada].",
              "**EP A/B si:** ingresos por encima de $939M y guía de ARR de FY27 subida por encima del +17,4%.",
              "**D si:** ARR nuevo neto a la baja.",
              "Técnica: en tendencia (EMA alineadas), +25% sobre la SMA 200 y −38% desde el máximo."],
        verdict="Seguridad en la nube de calidad que desacelera (orgánico +20%, guía +17%) con el FCF presionado por el capex. Rezagado del grupo de seguridad.")
    header = dict(verdict="+25% (+20% orgánico) y guía FY27 +17%: desacelera.",
                  setup="En tendencia; −38% desde máximos.", catalyst="4T FY26: ventas +2%, BPA +9%; guía floja.",
                  quality="SBC 24%; capex al alza.", supply="Limpia.", group="Seguridad que desacelera.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 1T FY27"), [pr, fx])


# ---------------------------------------------------------------- PANW
def panw():
    t = "PANW"
    c, rows = base(t)
    pr = casekit.link(1327567, "0001327567-26-000019", "ex991q426earningsrelease.htm", "EX-99.1 8-K 1-sep-2026: resultados 4T FY26")
    e, fx = _std(t, c, rows, "q4fy26", "2026-07-31", "2026-09-01", "amc",
                 "Resultados 4T FY26: ingresos $3.410M (+34%); ARR de nueva generación (NGS) $9.100M (+63%); RPO $21.200M (+34%); guía FY27 de NGS ARR +22–23% y FCF ajustado del 38%",
                 pr, "Consenso de finviz: ventas +1,7% y BPA +4,4%. El crecimiento incluye compras (ingresos de $2.594M a $3.002M de un trimestre a otro en el 3T FY26) "
                     "[VERIFY: crecimiento orgánico]. El mercado lo vendió: −4,4% en la apertura y −9,3% al cierre.")
    kpis = [
        kp("NGS ARR", "$9.100M (+63%); casi $1.000M de ARR nuevo neto en el trimestre; guía 1T FY27 $9.540–9.560M y FY27 $11.075–11.175M (+22–23%)", "—", *pr),
        kp("RPO", "$21.200M (+34%); guía FY27 $25.200–25.400M (+19–20%)", "$15.800M (jul-2025)", *pr),
        kp("FCF ajustado", "$1.300M en el 4T; margen del 38,4% en FY26; objetivo del 40% en FY28", "$954M (4T FY25)", *pr),
        kp("Compras", "Console (agentes de IA para empresas), además de la compra cerrada en el 3T FY26 (S-8 POS y 8-K de feb-2026)", "—", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    text = dict(
        narrative_flags=["El salto de ingresos del 3T FY26 (+16% secuencial) es inorgánico: el +34% no es comparable con el resto del grupo.",
                         "Pérdida neta GAAP en el 3T y el 4T FY26 por los costes de las compras."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +34% (con compras) y NGS ARR +63%, pero guía de FY27 desacelerando y el mercado lo vendió (−9%).",
        financials_note="Trimestres de XBRL hasta el 4T FY26; regenerados el 19-oct. El capex no sale de companyfacts con la etiqueta estándar.",
        quality=["Pérdida GAAP por costes de compras; FCF ajustado del 38%.", "Fondo de comercio e intangibles = 106% del patrimonio."],
        supply_read=f"Compras pagadas en parte con acciones (S-8 POS de feb-2026) y bonos (8-K de feb y abr-2026). Ventas de directivos {casekit.usd_m(insider_total(t))}, con compras de $10M.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 70 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La plataforma de seguridad que crece comprando; «líder enfriado» del grupo.",
        risks=["Integración de compras.", "Guía de FY27 desacelerando.", "Resultados ≈ 17-nov."],
        plan=["Resultados del 1T FY27 hacia el 17-nov [VERIFY: fecha no anunciada].",
              "**EP A/B si:** NGS ARR por encima de $9.560M (techo de la guía) y guía de FY27 subida.",
              "**D si:** RPO por debajo de $20.800M.",
              "Técnica: líder enfriado (−21% desde el máximo, +31% sobre la SMA 200)."],
        verdict="Plataforma de seguridad creciendo con compras (NGS ARR +63%) y FCF del 38%, pero con guía de FY27 desacelerando y pérdidas GAAP por la integración.")
    header = dict(verdict="NGS ARR +63% y FCF 38%, pero crecimiento con compras y guía floja.",
                  setup="Líder enfriado; −21% desde máximos.", catalyst="4T FY26: ventas +2%, BPA +4%; −9% al cierre.",
                  quality="Pérdida GAAP por compras.", supply="Compras con acciones.", group="Plataforma que compra.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, _evento(c, "Resultados 1T FY27"), [pr, fx])


if __name__ == "__main__":
    for f in sys.argv[1:] or ["msft", "now"]:
        globals()[f]()
        print(f, "ok")
