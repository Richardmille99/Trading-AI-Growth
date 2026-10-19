"""Registro reproducible de la Fase 1 manual + Fase 2 del universo computo_ia (19-oct-2026): catalizadores con consenso,
KPIs de los perfiles semis (centro de datos, guía, China, cartera), oferta y textos. Las cifras salen de los EX-99.1 y 8-K citados; el
consenso, de finviz (sorpresa del último informe y BPA del próximo trimestre). En modo actualización no se vuelve a
ejecutar: se edita el caso.
Uso: python computo_ia/data/build_fase2.py [ticker ...]"""
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
    "LRCX": "Equipos de grabado (etch) y depósito para fabricar chips de memoria y lógica, más servicio, recambios y mejoras de la base instalada",
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


# ---------------------------------------------------------------- LRCX
def lrcx():
    t = "LRCX"
    c, rows = base(t)
    pr = casekit.link(707549, "0000707549-26-000033", "lrcx_exhibitx991xq4x2026.htm", "EX-99.1 8-K 29-jul-2026: resultados 4T FY26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-28", "2026-07-29", "amc",
                         "Resultados 4T FY26: ingresos $6.722M (+30%), margen bruto 51,8%; guía del 1T FY27 de $8.100M ± $400M (+20% secuencial) y BPA $2,15 ± $0,15",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +0,9% y BPA +7,9%. La guía trimestral (+20% secuencial) no tiene consenso previo publicado aquí: sin sorpresa de guía. "
                              "EP de verdad: hueco del +26,1% y cierre del +18,0% con volumen 1,8×, ya devuelto (−38% desde el máximo).")
    kpis = [
        kp("Guía 1T FY27", "Ingresos $8.100M ± $400M; margen bruto 52% ± 1; margen operativo 39,5% ± 1; BPA $2,15 ± $0,15", "—", *pr),
        kp("Sistemas frente a servicio", "Sistemas $4.250M · servicio y otros $2.472M en el 4T FY26", "$3.438M · $1.734M (4T FY25)", *pr),
        kp("Regiones (4T FY26)", "Taiwán 27% · China 26% · Corea 20% · Japón 9% · EE. UU. 9%", "—", *pr),
        kp("Cartera (RPO)", "$2.434M a 28-jun-2026 (XBRL)", "$2.681M (jun-2025)", "quarters.json (XBRL 10-K FY26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-21", kind="earnings", text="Resultados 1T FY27 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["China pesa el 26% de los ingresos: cualquier restricción de exportación nueva llega directa a la guía.",
                         "La guía de +20% secuencial es la base del EP de julio: el 21-oct se juzga contra ella."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +30% con aceleración {m.accel_pp:pp}, beat de BPA del 8% y una guía muy fuerte; EP con hueco del +26%, ya devuelto.",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 4T FY26 (cerrado el 28-jun-2026). El capex no sale de companyfacts con la etiqueta estándar.",
        quality=["Fondo de comercio e intangibles bajos (15% del patrimonio).",
                 "El flujo operativo ($1.457M) va por debajo del beneficio ($2.277M) en el 4T FY26: capital circulante para atender la subida de pedidos."],
        supply_read=f"Sin dilución. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses (consejero delegado, CFO y consejeros), pequeñas frente a la capitalización ({{m.mcap:usdM}}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 23 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El de equipos que más acelera (memoria + lógica); se mueve con el ciclo de inversión de las fábricas, que ahora tira de la memoria (ver el universo memoria).",
        risks=["Exportaciones a China (26% de los ingresos).", "Ciclo de inversión de la memoria: si el precio de la memoria gira, el capex de MU, SK hynix y Samsung se frena.",
               "Resultados el 21-oct tras el cierre."],
        plan=["Resultados del 1T FY27 el 21-oct tras el cierre [VERIFY: fecha de finviz]: ya en la ventana de ≤ 3 sesiones, solo vale un EP.",
              "**EP A/B si:** ingresos ≥ $8.500M (techo de la guía), margen bruto ≥ 52% y guía del 2T FY27 con otro crecimiento secuencial.",
              "**D si:** ingresos en el punto medio o por debajo con guía plana: el mercado ya descuenta el pico del ciclo de memoria.",
              "Técnica: −38% desde el máximo, bajo la SMA 200; RS 1m en percentil 89 (rebote). Sin setup."],
        verdict="Ciclo de inversión en fábricas en plena subida (guía +20% secuencial), pero ligado al pico de la memoria y con China al 26%. El 21-oct es la prueba de la guía.")
    header = dict(verdict="Guía +20% secuencial y EP en julio, ya devuelto (−38%).",
                  setup="−38% desde máximos, bajo la SMA 200; sin setup.", catalyst="4T FY26: BPA +8%; guía muy fuerte; hueco +26%.",
                  quality="Balance limpio; caja por debajo del beneficio.", supply="Sin dilución.", group="El equipo que más acelera.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
