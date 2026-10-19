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
    "CLS": "Fabricación por encargo (EMS) de switches, servidores y almacenamiento para hiperescalares (CCS) y de electrónica para aeroespacial, defensa e industria (ATS)",
    "KLAC": "Equipos de inspección y metrología para fabricar chips (control de proceso), más servicio de la base instalada",
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

# ---------------------------------------------------------------- CLS
def cls():
    t = "CLS"
    c, rows = base(t)
    fs = casekit.link(1030894, "0001030894-26-000043", "cls-20260630prcondensedfs.htm", "8-K 27-jul-2026: estados resumidos 2T26")
    em = ["EMSNow: resultados 2T26 y guía (reproduce la nota de la compañía)", "https://www.emsnow.com/?p=55437"]
    of = casekit.link(1030894, "0001104659-26-091994", "tm2621135d3_424b5.htm", "424B5 6-ago-2026: 9.677.419 acciones a $310")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-27", "amc",
                         "Resultados 2T26: ingresos $4.699M (+62%), BPA ajustado $2,54 (+83%); sube la guía 2026 a ingresos de $20.500M (antes $19.000M) y BPA ajustado de $11,30 (antes $10,15)",
                         [fs, em, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=True, guide_change=7.9,
                         note="Consenso de finviz: ventas +7,1% y BPA +10,2%. Guía anual de ingresos +7,9% y de BPA ajustado +11,3% frente a la anterior. "
                              "La nota de resultados no está en el 8-K de EDGAR (solo los estados resumidos): la guía sale de EMSNow, que reproduce la nota. "
                              "EP: hueco del +3,1% y cierre del +10,0% con volumen 3,8×.")
    kpis = [
        kp("Guía 3T26", "Ingresos $5.250–5.550M; BPA ajustado $2,88–3,08; margen operativo ajustado ≈ 8,4%", "—", *em),
        kp("Guía 2026", "Ingresos $20.500M; BPA ajustado $11,30", "$19.000M y $10,15", *em),
        kp("Margen operativo ajustado", "8,2% en el 2T26, máximo histórico", "—", *em),
        kp("Ampliación de capital", "9.677.419 acciones nuevas a $310 (≈ $2.950M netos) en agosto de 2026, para capital circulante y capex; 124,66M acciones después", "—", *of)]
    sec = dict(id="follow26", kind="secondary", name="Ampliación de agosto de 2026 (9,68M acciones a $310)", shares=9_677_419, capacity_usd=None, price_basis=310.0,
               gate="dated", date="2026-08-06",
               notes="Colocación primaria: ≈ 8,4% más acciones (124,66M después; hasta 1,45M más si los colocadores ejercen su opción). La acción cotiza hoy por debajo de $310: "
                     "los que entraron en la ampliación están en pérdidas.", src=[of])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-26", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Amplió capital un 8% en agosto a $310, justo después de un informe fuerte: la acción ha vuelto por debajo de ese precio.",
                         "Ensamblador para hiperescalares (switches y servidores): margen bajo y dependencia de pocos clientes."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +62% con aceleración {m.accel_pp:pp}, beat amplio (+7% en ingresos, +10% en BPA) y guía anual +8%; EP con volumen 3,8×.",
        financials_note="Trimestres de XBRL (companyfacts) desde 2024 (10 trimestres): Celestica pasó a presentar 10-K/10-Q como emisor doméstico.",
        quality=["Margen bruto del 12% (ensamblaje): el perfil de fabricación (gm 25%) lo penaliza menos que el de semis.",
                 "Flujo operativo por debajo del beneficio en varios trimestres: inventario y cobros crecen con el volumen."],
        supply_read=f"Ampliación de capital del 8% en agosto (≈ $2.950M) y ventas de directivos fuertes: {casekit.usd_m(insider_total(t))} en 12 meses, "
                    "con el consejero delegado vendiendo $130,7M.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 16 (finviz), el más barato del universo. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El ensamblador del universo: crece como los chips (+62%) con margen de fabricante; más barato que SMCI y DELL por PER.",
        risks=["Concentración en hiperescalares.", "Dilución reciente y directivos vendiendo.", "Margen bajo: poco colchón si baja el volumen.",
               "Resultados el 26-oct tras el cierre."],
        plan=["Resultados del 3T26 el 26-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 21-oct.",
              "**EP A/B si:** ingresos ≥ $5.550M (techo de la guía), BPA ≥ $3,13 (+5% sobre el consenso de $2,98) y guía anual por encima de $20.500M.",
              "**D si:** ingresos dentro de la guía sin subirla: tras la ampliación, el mercado pediría más.",
              "Técnica: −34% desde el máximo, bajo la SMA 200. Sin setup."],
        verdict="Crecimiento de chip (+62%) con valoración de ensamblador y guía subida, pero amplió capital un 8% y los directivos venden. El 26-oct decide.")
    header = dict(verdict="+62% y guía +8%, pero ampliación del 8% en agosto y directivos vendiendo.",
                  setup="−34% desde máximos; sin setup.", catalyst="2T26: ventas +7%, BPA +10%; guía +8%; EP con volumen.",
                  quality="Margen de ensamblador.", supply="Ampliación del 8%; ventas del CEO.", group="El ensamblador del universo.")
    finish(t, c, kpis, [e], [sec, ins], forensic_float(t), text, header, events, [fs, em, of, fx])


# ---------------------------------------------------------------- KLAC
def klac():
    t = "KLAC"
    c, rows = base(t)
    pr = casekit.link(319201, "0000319201-26-000024", "exhibit991earningsrelease7.htm", "EX-99.1 8-K 28-jul-2026: resultados 4T FY26")
    qr = ["Quartr: guía del 1T FY27 en la conferencia del 28-jul (coincide con TIKR y Trefis)", "https://quartr.com/events/kla-corporation-klac-q4-2026_3YEy3X5h"]
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-30", "2026-07-28", "amc",
                         "Resultados 4T FY26: ingresos récord $3.658M (+15%), por encima del punto medio de su guía; guía del 1T FY27 $4.000M ± $200M (+9% secuencial)",
                         [pr, qr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +1,4% y BPA +4,5%. La guía se da en la conferencia (Quartr, TIKR y Trefis coinciden): ingresos $4.000M ± $200M, BPA ajustado $1,16 ± $0,10, "
                              "margen bruto 62,5% ± 1; sube la previsión del mercado de equipos de 2026 a la parte baja de $150.000M. El mercado lo vendió: −6,9% en la apertura y −10,8% al cierre.")
    kpis = [
        kp("Guía 1T FY27", "Ingresos $4.000M ± $200M; BPA ajustado $1,16 ± $0,10; margen bruto 62,5% ± 1", "—", *qr),
        kp("Mercado de equipos (WFE) 2026", "Parte baja de $150.000M, según la compañía (subida)", "—", *qr),
        kp("Caja y retorno", "FCF $817M en el 4T y $3.770M en FY26; $3.350M devueltos en FY26", "—", *pr),
        kp("Margen bruto", "61,3% en el 4T FY26", "62,0% en el 4T FY25", "quarters.json (XBRL 10-K FY26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 1T FY27 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["El informe batió por poco y la guía (+9% secuencial) es menos que la de LRCX (+20%): el mercado premia al que más acelera.",
                         "La cotización por acción refleja un desdoblamiento (BPA de $1,05 por trimestre): compárese siempre con cifras ajustadas por acciones."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +15% con aceleración {m.accel_pp:pp}, beat pequeño y guía sólida, pero el mercado lo vendió un 11%.",
        financials_note="Trimestres de XBRL hasta el 4T FY26. El beneficio operativo no sale de companyfacts con la etiqueta estándar.",
        quality=["El margen más alto del universo de equipos (≈ 61%) y FCF ≈ 100% del beneficio.", "Fondo de comercio e intangibles = 32% del patrimonio."],
        supply_read=f"Sin dilución: recompras y dividendo ($0,23 por acción). Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, en planes 10b5-1.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 25 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El de mayor calidad entre los equipos (inspección: menos cíclico), pero el que menos acelera; −44% desde máximos.",
        risks=["Ciclo de inversión de las fábricas.", "Exportaciones a China.", "Resultados el 28-oct tras el cierre."],
        plan=["Resultados del 1T FY27 el 28-oct tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 23-oct.",
              "**EP A/B si:** ingresos ≥ $4.200M (techo de la guía), BPA ≥ $1,24 (+5% sobre el consenso de $1,18) y guía del 2T FY27 con más crecimiento secuencial.",
              "**D si:** ingresos en el punto medio y guía plana: seguiría por detrás de LRCX.",
              "Técnica: −44% desde el máximo, bajo la SMA 200. Sin setup."],
        verdict="Calidad de primera (margen 61%, caja) con una guía sólida pero menos explosiva que la de LRCX, y el mercado vendiéndolo. El 28-oct medirá la aceleración.")
    header = dict(verdict="Margen y caja de primera, pero guía menos explosiva que LRCX y −44% desde máximos.",
                  setup="−44% desde máximos; sin setup.", catalyst="4T FY26: ventas +1%, BPA +5%; guía +9% secuencial; −11% al cierre.",
                  quality="Margen 61%; FCF ≈ beneficio.", supply="Sin dilución.", group="Calidad, menos aceleración.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, qr, fx])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
