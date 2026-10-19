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


if __name__ == "__main__":
    for f in sys.argv[1:] or ["msft", "now"]:
        globals()[f]()
        print(f, "ok")
