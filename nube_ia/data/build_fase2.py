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


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
