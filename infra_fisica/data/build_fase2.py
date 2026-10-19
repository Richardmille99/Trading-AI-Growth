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
    "FIX": "Contratista de instalaciones mecánicas y eléctricas (climatización, fontanería, electricidad, módulos prefabricados) "
           "en EE. UU.; el 59% de los ingresos del 2T26 viene de clientes de tecnología (centros de datos)",
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


if __name__ == "__main__":
    for f in sys.argv[1:] or ["fix"]:
        globals()[f]()
        print(f, "ok")
