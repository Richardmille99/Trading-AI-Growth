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
    "AMD": "CPU de servidor (EPYC) y PC, GPU de IA (Instinct) y chips embebidos (antigua Xilinx)",
    "ANET": "Switches Ethernet y software de red para centros de datos de IA, nube y empresas",
    "COHR": "Transceptores ópticos y láseres para centros de datos, más materiales y láseres industriales",
    "LITE": "Láseres y transceptores ópticos para redes de centros de datos de IA y telecomunicaciones (incluye Cloud Light)",
    "AMAT": "Equipos de depósito, grabado, implantación e inspección para fabricar chips, y servicio de la base instalada",
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

# ---------------------------------------------------------------- AMD
def amd():
    t = "AMD"
    c, rows = base(t)
    pr = casekit.link(2488, "0000002488-26-000121", "q22026991.htm", "EX-99.1 8-K 4-ago-2026: resultados 2T26")
    wl = casekit.link(2488, "0000002488-26-000182", "amd-20260926.htm", "8-K 26-sep-2026: compra de World Labs (≈ $8.200M en acciones)")
    nb = casekit.link(2488, "0001193125-26-352628", "d173126d424b5.htm", "424B5 14-ago-2026: bonos senior")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-27", "2026-08-04", "amc",
                         "Resultados 2T26: ingresos $11.536M (+50%), centro de datos $6.700M (+107%); guía 3T ≈ $13.000M ± $300M (+13% secuencial) con margen bruto ajustado ≈ 56%",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +2,0% y BPA +2,7%: beat pequeño. La nota menciona el control de exportaciones de EE. UU. sobre las GPU MI308. "
                              "El mercado lo vendió: −6,6% en la apertura y −7,0% al cierre.")
    kpis = [
        kp("Segmentos (2T26)", "Centro de datos $6.700M (+107%; EPYC e Instinct) · Cliente y gaming $3.800M (+6%) · Embebidos $977M (+19%)", "—", *pr),
        kp("Guía 3T26", "Ingresos ≈ $13.000M ± $300M; margen bruto ajustado ≈ 56%", "—", *pr),
        kp("Producto", "Lanzada la familia Instinct MI400 (MI455X, MI430X) y la 6.ª generación de EPYC", "—", *pr),
        kp("Compra de World Labs", "≈ $8.200M pagados en acciones de AMD (acuerdo del 26-sep-2026)", "—", *wl)]
    wla = dict(id="worldlabs", kind="secondary", name="Acciones para la compra de World Labs (≈ $8.200M)", shares=None, capacity_usd=None, price_basis=None,
               gate="gated", date="2026-09-26",
               notes="Contraprestación en acciones de AMD: ≈ 0,9% de la capitalización. [VERIFY: número de acciones al cierre de la operación]", src=[wl])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-03", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Beat pequeño (+2%) tras una subida grande: el mercado pide más al segundo proveedor de GPU.",
                         "Compra de World Labs por ≈ $8.200M en acciones: dilución pequeña pero nueva."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +50% con aceleración {m.accel_pp:pp} y centro de datos +107%, pero beat pequeño y el mercado lo vendió (−7%).",
        financials_note="Trimestres de XBRL hasta el 2T26.",
        quality=["Fondo de comercio e intangibles = 61% del patrimonio (Xilinx, ZT Systems).", "Capex duplicado en el 2T26 ($808M)."],
        supply_read=f"Bonos en agosto ($1.250M) y compra de World Labs con acciones. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 34 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El segundo de los chips de IA: crece más que NVDA en porcentaje en el 2T (+50%), pero con margen y escala menores.",
        risks=["Exportaciones a China (MI308).", "Competencia de NVDA y de los ASIC.", "Resultados el 3-nov tras el cierre."],
        plan=["Resultados del 3T26 el 3-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 29-oct.",
              "**EP A/B si:** ingresos ≥ $13.300M (techo de la guía), centro de datos acelerando y guía del 4T por encima del consenso.",
              "**D si:** otro beat pequeño con guía plana.",
              "Técnica: sobre la SMA 200 (+37%) pero bajo las EMA cortas; −18% desde el máximo. Sin setup."],
        verdict="Centro de datos duplicando (+107%) y guía del 3T +13%, pero beats pequeños que el mercado ya no premia. El 3-nov necesita un beat claro.")
    header = dict(verdict="Centro de datos +107% y guía +13%, pero beat pequeño y −7% tras resultados.",
                  setup="Sobre la SMA 200; −18% desde máximos.", catalyst="2T26: ventas +2%, BPA +3%; −7% al cierre.",
                  quality="Mucho fondo de comercio.", supply="Compra con acciones (World Labs).", group="Segundo en GPU.")
    finish(t, c, kpis, [e], [wla, ins], forensic_float(t), text, header, events, [pr, wl, nb, fx])


# ---------------------------------------------------------------- ANET
def anet():
    t = "ANET"
    c, rows = base(t)
    pr = casekit.link(1596532, "0001596532-26-000174", "ex991q226-earningsrelease.htm", "EX-99.1 8-K 4-ago-2026: resultados 2T26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-08-04", "amc",
                         "Resultados 2T26: ingresos $3.036M (+37,7%; +12,1% secuencial); guía 3T ≈ $3.300M, margen operativo ajustado 48–49%, BPA ajustado $1,06–1,08",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +7,3% y BPA +15,1%. Guía del 3T +8,7% secuencial. El mercado abrió +10,3% y cerró +3,6%.")
    kpis = [
        kp("Guía 3T26", "Ingresos ≈ $3.300M; margen operativo ajustado 48–49%; BPA ajustado $1,06–1,08", "—", *pr),
        kp("Producto", "Plataformas de red de IA de 1,6 Tbps (serie 7060XE7, con óptica lineal enchufable y refrigeración líquida)", "—", *pr),
        kp("Margen operativo GAAP", "45% en el 2T26 ($1.378M sobre $3.036M)", "45% en el 2T25", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Caja", "$13.343M a jun-2026, sin deuda (XBRL)", "$8.844M (jun-2025)", "quarters.json (XBRL 10-Q 2T26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-03", kind="earnings", text="Resultados 3T26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Las ventas de insiders de 12 meses son grandes en dólares, pero casi todas en planes 10b5-1 y de fundadores y fondos; los marcados son pequeños."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: +38% con aceleración {m.accel_pp:pp}, beat amplio (+7% en ventas, +15% en BPA) y guía +9% secuencial.",
        financials_note="Trimestres de XBRL hasta el 2T26; regenerados el 19-oct con el 4T derivado de la misma versión (los 4T salían con neto negativo).",
        quality=["Margen operativo GAAP del 45% y caja neta de $13.343M.", "Sin fondo de comercio relevante (5% del patrimonio)."],
        supply_read=f"Oferta limpia: sin ampliaciones ni filings de oferta en 12 meses. Ventas de insiders {casekit.usd_m(insider_total(t))} en 12 meses, sobre todo en planes 10b5-1.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 34 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La red Ethernet de los clústeres de IA: márgenes del 45% y balance sin deuda; por encima de CIEN y COHR en calidad.",
        risks=["Concentración en hiperescalares (Microsoft, Meta).", "Competencia de NVIDIA en redes.", "Resultados el 3-nov tras el cierre."],
        plan=["Resultados del 3T26 el 3-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 29-oct.",
              "**EP A/B si:** ingresos ≥ $3.450M (+4,5% sobre la guía), BPA ≥ $1,13 (+5% sobre el consenso de $1,08) y guía del 4T con más crecimiento.",
              "**D si:** ingresos en la guía y margen a la baja.",
              "Técnica: sobre la SMA 200 (+11%), bajo las EMA cortas; −17% desde el máximo."],
        verdict="Calidad máxima del cómputo de IA (margen 45%, sin deuda, beat amplio) a un PER razonable. El 3-nov dirá si la red de IA sigue acelerando.")
    header = dict(verdict="+38%, margen 45% y sin deuda; beat amplio y guía +9%.",
                  setup="Sobre la SMA 200; −17% desde máximos.", catalyst="2T26: ventas +7%, BPA +15%.",
                  quality="Margen 45%; caja neta.", supply="Limpia.", group="La red de los clústeres de IA.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


# ---------------------------------------------------------------- COHR
def cohr():
    t = "COHR"
    c, rows = base(t)
    pr = casekit.link(820318, "0001193125-26-346860", "d128030dex991.htm", "EX-99.1 8-K 12-ago-2026: resultados 4T FY26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-30", "2026-08-12", "amc",
                         "Resultados 4T FY26: ingresos $2.046M (+34%); guía del 1T FY27 $2.200–2.400M (+12% secuencial en el punto medio), margen bruto ajustado 39,5–41,5%, BPA ajustado $1,85–2,05",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +3,1% y BPA +7,6%. El mercado lo vendió: −3,0% en la apertura y −8,0% al cierre.")
    kpis = [
        kp("Guía 1T FY27", "Ingresos $2.200–2.400M; margen bruto ajustado 39,5–41,5%; gastos operativos ajustados $400–420M; BPA ajustado $1,85–2,05", "—", *pr),
        kp("Margen bruto", "38,5% en el 4T FY26", "35,7% en el 4T FY25", "quarters.json (XBRL 10-K FY26)"),
        kp("Capex", "$556M en el 4T FY26 (27% de los ingresos): ampliación de capacidad de transceptores", "$131M (4T FY25)", "quarters.json (XBRL 10-K FY26)"),
        kp("Salida de Bain Capital", "Bain (≥ 10%) vendió ≈ $1.075M en 12 meses, el 100% de su posición declarada", "—", "Forms 4 (EDGAR), insiders.json")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-04", kind="earnings", text="Resultados 1T FY27 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Bain Capital ha salido del capital (≈ $1.075M vendidos): la oferta de ese bloque ya está hecha.",
                         "El capex se ha cuadruplicado ($131M → $556M por trimestre): el FCF del 4T fue negativo."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +34% con aceleración {m.accel_pp:pp} y guía +12% secuencial, pero el mercado lo vendió (−8%).",
        financials_note="Trimestres de XBRL hasta el 4T FY26; regenerados el 19-oct con el 4T derivado de la misma versión. El beneficio operativo no sale de companyfacts con la etiqueta estándar.",
        quality=["Margen bruto al alza (35,7% → 38,5%).", "FCF negativo por el capex.", "Fondo de comercio e intangibles = 67% del patrimonio."],
        supply_read=f"Sin ampliaciones; la salida de Bain ya está ejecutada. Ventas de insiders {casekit.usd_m(insider_total(t))} en 12 meses, casi todo Bain.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 17 (finviz), el más barato de la óptica. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="La óptica barata del universo (PER ≈ 17) frente a LITE (≈ 25): crece menos (+34% frente a +109%) y con margen menor.",
        risks=["Capex alto y FCF negativo.", "Competencia en transceptores (LITE, fabricantes chinos).", "Resultados el 4-nov tras el cierre."],
        plan=["Resultados del 1T FY27 el 4-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 30-oct.",
              "**EP A/B si:** ingresos ≥ $2.400M (techo de la guía), margen bruto ≥ 41% y guía del 2T FY27 con más crecimiento.",
              "**D si:** margen bruto por debajo del 39,5%.",
              "Técnica: −45% desde el máximo, bajo la SMA 200; RS en el percentil 11. Sin setup."],
        verdict="Óptica para IA a precio de saldo (PER ≈ 17) con guía +12% secuencial, pero con FCF negativo por el capex y la acción en tendencia bajista.")
    header = dict(verdict="+34% y guía +12% secuencial a PER ≈ 17; FCF negativo por el capex.",
                  setup="−45% desde máximos; sin setup.", catalyst="4T FY26: ventas +3%, BPA +8%; −8% al cierre.",
                  quality="Margen al alza; FCF negativo.", supply="Salida de Bain ya hecha.", group="La óptica barata.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


# ---------------------------------------------------------------- LITE
def lite():
    t = "LITE"
    c, rows = base(t)
    pr = casekit.link(1633978, "0001628280-26-055726", "lite_ex991xq4fy26.htm", "EX-99.1 8-K 11-ago-2026: resultados 4T FY26")
    ex = casekit.link(1633978, "0001193125-26-249535", "d112771d8k.htm", "8-K 29-may-2026: canje de bonos 2028 por ≈ 5,0M acciones")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q4fy26", "2026-06-27", "2026-08-11", "amc",
                         "Resultados 4T FY26: ingresos $1.006M (+109%); guía del 1T FY27 de $1.250M en el punto medio (+24% secuencial); pérdida GAAP de $7.200M por canje de convertibles (contable, sin caja)",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None, nonrec=False,
                         note="Consenso de finviz: ventas +1,9% y BPA ajustado +8,8%. La pérdida neta GAAP (−$7.162M) sale de una pérdida contable de $7.800M por cancelar convertibles a cambio de acciones: "
                              "no afecta a la caja, pero sí al número de acciones. EP: hueco del +9,6% y cierre del +13,6%.")
    kpis = [
        kp("Guía 1T FY27", "Ingresos ≈ $1.250M en el punto medio (+24% secuencial): «modelo objetivo más de un trimestre antes de lo previsto»", "—", *pr),
        kp("Margen bruto", "47,4% en el 4T FY26", "33,3% en el 4T FY25", "quarters.json (XBRL 10-K FY26)"),
        kp("Canje de convertibles", "Deuda de $3.282M a $1.637M en el 4T; acciones básicas de 70,3M (sep-2025) a 89,7M (ago-2026), +28%", "—", *ex),
        kp("Flujo operativo", "$363M en el 4T FY26", "$64M (4T FY25)", "quarters.json (XBRL 10-K FY26)")]
    conv = dict(id="conv_canje", kind="convertible", name="Canjes de convertibles por acciones (2026)", shares=None, capacity_usd=None, price_basis=None,
                gate="dated", date="2026-05-29",
                notes="Varios canjes privados (8-K 3.02 de mar, abr y may-2026): por ejemplo ≈ 5,0M acciones por $650,4M de bonos 2028. Las acciones básicas suben un 28% en un año. "
                      "[VERIFY: convertibles que quedan vivos tras los canjes, en el 10-K FY26]", src=[ex])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-05", kind="earnings", text="Resultados 1T FY27 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["La pérdida GAAP de $7.200M es contable (canje de convertibles), pero la dilución es real: +28% de acciones básicas en un año.",
                         "Crecimiento del +109% con margen bruto del 33% al 47%: el ciclo de transceptores para IA en su punto más fuerte."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: +109% con aceleración {m.accel_pp:pp}, guía +24% secuencial y EP con hueco del +10%.",
        financials_note="Trimestres de XBRL hasta el 4T FY26. El neto del 4T (−$7.162M) lleva la pérdida contable del canje: las métricas de beneficio TTM salen distorsionadas.",
        quality=["Neto GAAP distorsionado por la pérdida contable de $7.800M.", "Margen bruto disparado (33% → 47%) y flujo operativo al alza."],
        supply_read=f"La oferta fuerte ya ocurrió: canjes de convertibles por acciones (+28% de acciones básicas). Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 25 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El que más crece del cómputo de IA (+109%) y con el margen que más mejora; frente a COHR, más caro pero mucho más rápido.",
        risks=["Ciclo de transceptores: muy alto ahora.", "Dilución acumulada.", "Resultados el 5-nov tras el cierre."],
        plan=["Resultados del 1T FY27 el 5-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 31-oct.",
              "**EP A/B si:** ingresos ≥ $1.300M (+4% sobre el punto medio de la guía), BPA ≥ $4,42 (+5% sobre el consenso de $4,21) y guía del 2T FY27 con más crecimiento.",
              "**D si:** ingresos en la guía con margen plano.",
              "Técnica: sobre la SMA 200 (+9%), bajo las EMA cortas; −26% desde el máximo."],
        verdict="El caso de crecimiento más fuerte del cómputo (+109%, guía +24%, EP en agosto) con márgenes disparados; la dilución por canjes ya está hecha. Candidato a EP el 5-nov.")
    header = dict(verdict="+109%, guía +24% y EP en agosto; dilución por canjes ya hecha.",
                  setup="Sobre la SMA 200; −26% desde máximos.", catalyst="4T FY26: ventas +2%, BPA +9%; EP +14%.",
                  quality="Margen 33% → 47%; neto GAAP distorsionado.", supply="Canjes por acciones (+28%).", group="El que más crece.")
    finish(t, c, kpis, [e], [conv, ins], forensic_float(t), text, header, events, [pr, ex, fx])


# ---------------------------------------------------------------- AMAT
def amat():
    t = "AMAT"
    c, rows = base(t)
    pr = casekit.link(6951, "0001628280-26-056699", "exhibit991q32026earningsre.htm", "EX-99.1 8-K 13-ago-2026: resultados 3T FY26")
    k, fx = fv(t)
    e = casekit.earnings(c, rows, "q3fy26", "2026-07-26", "2026-08-13", "amc",
                         "Resultados 3T FY26: ingresos $9.115M (+25%), flujo operativo récord de $3.037M; guía del 4T FY26 $10.250M ± $500M (+12% secuencial) y BPA ajustado $4,02 ± $0,20",
                         [pr, fx], rev_surprise=round(k["sales_surprise_pct"], 1), eps_surprise=round(k["eps_surprise_pct"], 1),
                         guide_raise=None, guide_change=None,
                         note="Consenso de finviz: ventas +1,3% y BPA +2,9%. Sube sus expectativas de Semiconductor Systems para 2026 y espera «otro año fuerte» en 2027; 13 trimestres seguidos de mejora del margen bruto. "
                              "El mercado lo vendió: −6,6% en la apertura y −5,1% al cierre.")
    kpis = [
        kp("Guía 4T FY26", "Ingresos $10.250M ± $500M; BPA ajustado $4,02 ± $0,20", "—", *pr),
        kp("Margen bruto", "50,3% en el 3T FY26 (13 trimestres seguidos al alza)", "48,8% en el 3T FY25", *pr),
        kp("Caja y retorno", "Flujo operativo récord de $3.037M; $860M devueltos ($440M en recompras y $420M en dividendos)", "—", *pr)]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    events = [dict(date="2026-11-12", kind="earnings", text="Resultados 4T FY26 tras el cierre [VERIFY: fecha de finviz]", src=[fx])]
    text = dict(
        narrative_flags=["Beats pequeños (+1–3%) que el mercado no premia en equipos: lo que mueve es la guía."],
        catalyst_read="El 3T FY26 puntúa {m.cat_q3fy26_score:sc}: +25% con aceleración {m.accel_pp:pp}, guía +12% secuencial, pero beat pequeño y el mercado lo vendió (−5%).",
        financials_note="Trimestres de XBRL hasta el 3T FY26 (cerrado el 26-jul-2026). El 3T FY25 llevaba una provisión fiscal de $410M.",
        quality=["Margen bruto al alza 13 trimestres seguidos.", "Fondo de comercio e intangibles bajos (16% del patrimonio)."],
        supply_read=f"Sin dilución: recompras y dividendo. Ventas de directivos {casekit.usd_m(insider_total(t))} en 12 meses, con el consejero delegado ($105M) en parte fuera de plan.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; PER adelantado ≈ 22 (finviz). DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El mayor de los equipos por ingresos; acelera menos que LRCX pero más que KLAC.",
        risks=["Exportaciones a China.", "Ciclo de inversión de las fábricas.", "Resultados el 12-nov tras el cierre."],
        plan=["Resultados del 4T FY26 el 12-nov tras el cierre [VERIFY: fecha de finviz]: la ventana de ≤ 3 sesiones empieza el 7-nov.",
              "**EP A/B si:** ingresos ≥ $10.750M (techo de la guía), BPA ≥ $4,26 (+5% sobre el consenso de $4,06) y guía del 1T FY27 con más crecimiento.",
              "**D si:** ingresos en el punto medio con guía plana.",
              "Técnica: −43% desde el máximo, bajo la SMA 200. Sin setup."],
        verdict="Equipos de fabricación en plena subida (guía +12% secuencial, márgenes al alza, caja récord) con el mercado vendiendo el sector. El 12-nov dirá si la guía de 2027 sostiene el ciclo.")
    header = dict(verdict="Guía +12% secuencial y caja récord; −43% desde máximos.",
                  setup="−43% desde máximos; sin setup.", catalyst="3T FY26: ventas +1%, BPA +3%; −5% al cierre.",
                  quality="Margen al alza 13 trimestres.", supply="Sin dilución.", group="El mayor de los equipos.")
    finish(t, c, kpis, [e], [ins], forensic_float(t), text, header, events, [pr, fx])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        globals()[f]()
        print(f, "ok")
