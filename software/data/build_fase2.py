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


if __name__ == "__main__":
    for f in sys.argv[1:] or ["msft", "now"]:
        globals()[f]()
        print(f, "ok")
