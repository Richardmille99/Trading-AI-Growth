"""Registro reproducible de la Fase 1 manual + Fase 2 del universo memoria (18-oct-2026): catalizadores con consenso, KPIs,
oferta y textos de MU, SNDK, RMBS, PENG, SKHY y SIMO. Las cifras de resultados salen de los EX-99.1 / 6-K (citados) y el
consenso de búsquedas web (citado; [VERIFY] si discrepa). En modo actualización no se vuelve a ejecutar: se edita el caso.
Uso: python3 memoria/data/build_fase2.py [mu sndk ...]"""
import json, os, sys

U = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(U, "..", ".claude", "skills", "growth-swing", "scripts"))
import casekit  # noqa: E402
from prices import read_csv  # noqa: E402

E = "https://www.sec.gov/Archives/edgar/data"


def pct(a, b):
    return round((a / b - 1) * 100, 1)


def kp(name, value, prior, label, url=""):
    return dict(name=name, value=value, prior=prior, src=[[label, url]])


def inv_days(q):
    """Días de inventario del último trimestre: inventario ÷ coste de ventas × 91."""
    x = q[-1]
    return round(x["inventory"] / (x["revenue"] - x["gross_profit"]) * 91)


def forensic_float(t):
    """float_shares = valor de no afiliados de la portada del 10-K ÷ cierre de esa fecha (forensic.py), con nota."""
    pf = json.load(open(f"{U}/data/{t}/forensic.json", encoding="utf-8")).get("public_float") or {}
    if not pf.get("float_shares"):
        return {}
    return dict(float_shares=float(pf["float_shares"]),
                note=f"Portada del {pf['form']} ({pf['filed']}): {casekit.usd_m(pf['usd'])} de no afiliados a {pf['date']} ÷ cierre de "
                     f"${es(pf['close'], 2)} = {es(pf['float_shares'] / 1e6, 1)}M acciones [VERIFY: estimación; no recoge cambios posteriores]")


def es(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def base(t):
    c = casekit.load(U, t)
    rows = read_csv(f"{U}/data/{t}/prices.csv")
    return c, rows


DESC = {
    "MU": "Fabricante integrado de DRAM, HBM y NAND; vende a centros de datos (nube y servidores), móviles y PC, y automoción",
    "SKHY": "Fabricante de DRAM (72% de los ingresos del 2T26), líder en HBM, y de NAND (28%); cotiza en Seúl y, desde julio de 2026, con ADR en Nasdaq",
    "SNDK": "Fabricante de NAND flash y SSD (fabricación en joint venture con Kioxia), escindido de Western Digital en febrero de 2025; centro de datos, edge y consumo",
    "RMBS": "Chips de interfaz para módulos de memoria DDR5 (buffers y PMIC) más licencias de patentes e IP de interfaz y seguridad",
    "SIMO": "Diseño de controladores NAND para SSD, eMMC y UFS (fabless), con SSD de centro de datos y soluciones de almacenamiento propias",
    "PENG": "Memoria especial (60% de las ventas del 4T FY26), sistemas y servicios de IA para neoclouds, y LED; integrador sin fábricas de chips",
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


# ---------------------------------------------------------------- MU
def mu():
    t = "MU"
    c, rows = base(t)
    q = c["financials"]["quarters"]
    pr = casekit.link(723125, "0000723125-26-000018", "a2026q4ex991-pressrelease.htm", "EX-99.1 8-K 30-sep-2026")
    fx = ["FXStreet: consenso ingresos ≈ $51.500M, BPA ≈ $31,82", "https://www.fxstreet.com/news/micron-impresses-with-542-billion-in-q4-revenue-202609302015"]
    at = ["AskTraders (LSEG): ingresos $51.070M, BPA $31,61; guía 1T FY27 frente a $57.020M y $35,40", "https://www.asktraders.com/?p=255274"]
    e = casekit.earnings(c, rows, "q4fy26", "2026-09-03", "2026-09-30", "amc",
                         "Resultados 4T FY26: ingresos $54.229M (+379%) frente a $51.070M de consenso (LSEG); BPA ajustado $33,42 frente a $31,61; guía 1T FY27 $61.500M ± $1.500M frente a $57.020M",
                         [pr, at, fx], rev_surprise=pct(54229, 51070), eps_surprise=pct(33.42, 31.61), guide_raise=True,
                         guide_change=pct(61500, 57020),
                         note="Consenso LSEG (AskTraders); FXStreet da ≈ $51.500M de ingresos y $31,82 de BPA: con esa base la sorpresa es ≈ +5% [VERIFY]. "
                              "La guía del 1T FY27 ($61.500M, margen bruto ≈ 86%) queda ≈ +8% sobre el consenso. Sin partidas no recurrentes en el beat: el BPA GAAP ($32,87) y el ajustado ($33,42) apenas difieren.")
    kpis = [
        kp("Unidades de negocio (4T FY26)", "Core Data Center $18.002M (margen bruto 90%) · Cloud Memory $16.283M (83%) · Mobile y Client $13.114M (90%) · Automoción y embebido $6.824M (84%)",
           "CDBU $1.577M · CMBU $4.543M · MCBU $3.760M · AEBU $1.434M (4T FY25)", *pr),
        kp("Guía 1T FY27", "Ingresos $61.500M ± $1.500M; margen bruto GAAP ≈ 85,95%; BPA GAAP $37,84 ± $1,00", "—", *pr),
        kp("Capex neto", "$10.770M en el 4T FY26; $27.370M en FY26 (20,5% de los ingresos del año)", "—", *pr),
        kp("Inventario (días, 4T FY26)", f"≈ {inv_days(q)} días (inventario ÷ coste de ventas × 91)", "—", "quarters.json (XBRL 10-K FY26)"),
        kp("Caja e inversiones", "$73.480M de caja, inversiones negociables y caja restringida a cierre de FY26", "—", *pr),
        kp("Acuerdos estratégicos con clientes", "La compañía cita «Strategic Customer Agreements» que dan visibilidad a la demanda [VERIFY: plazos, volúmenes y prepagos en el 10-K FY26]", "—", *pr),
        kp("Bits, ASP y % de HBM", "[VERIFY: prepared remarks del 30-sep-2026; el PR no los da]", "—", "")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    fl = forensic_float(t)
    events = [dict(date="2026-12-16", kind="earnings", text="Resultados 1T FY27 [VERIFY: fecha estimada; el 1T FY26 se publicó el 17-dic-2025]",
                   src=[["8-K 17-dic-2025 (Item 2.02)", f"{E}/723125/000072312525000044/mu-20251217.htm"]])]
    text = dict(
        narrative_flags=["El crecimiento (+379%) es sobre todo precio: el ciclo de memoria lo multiplica todo en la subida y también en la bajada. Los márgenes del 87% no son una base estable."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: beat de ingresos y de BPA, guía ≈ +8% sobre el consenso y aceleración {m.accel_pp:pp}. La confirmación de mercado fue tibia: abrió con −1% y cerró +3% al día siguiente, poco para una guía ≈ 8% sobre el consenso.",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 4T FY26 (cerrado el 3-sep-2026, 10-K del 9-oct). El 4T FY26 tuvo 14 semanas. En los 4T no hay acciones diluidas trimestrales en XBRL (BPA del 4T n/d).",
        quality=["Sin banderas automáticas. El FCF TTM es alto pese a un capex de $27.370M en FY26.",
                 "El margen bruto del 86,8% es de pico de ciclo: el perfil `semis_memory` lo compara con un objetivo de 40% de media de ciclo, así que la nota de margen bruto está en su máximo y no informa de la sostenibilidad."],
        supply_read="Oferta limpia: sin convertibles ni ampliaciones; recompró deuda con ofertas de compra en marzo-abril de 2026. Las ventas de insiders son pequeñas frente a la capitalización ({m.mcap:usdM}).",
        valuation=["EV/ventas {m.ev_sales:x1} TTM. Con la guía del 1T FY27 anualizada (≈ $246.000M) el múltiplo baja a ≈ 4×; el mercado descuenta que el pico de precios no dura. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Frente a SNDK, MU tiene más diversificación (DRAM, HBM y NAND) y menos caída desde máximos; frente a SKHY, menos cuota de HBM [VERIFY].",
        risks=["Giro del ciclo: más capacidad de DRAM/HBM en 2027 (MU, SK hynix, Samsung) o pausa del capex de IA.",
               "Precios: la subida de ingresos es sobre todo ASP; un estancamiento de precios frena el crecimiento de golpe.",
               "Capex creciente: si la demanda se frena, el FCF cae más que los ingresos."],
        plan=["Resultados del 1T FY27 hacia el 16-dic [VERIFY].",
              "**EP A/B si:** ingresos ≥ $64.600M (+5% sobre el punto medio de la guía), margen bruto ≥ 87% y guía del 2T FY27 ≥ +5% sobre el consenso.",
              "**D si:** ingresos dentro del rango ($60.000–63.000M) con guía plana: el mercado ya descuenta un pico.",
              "Técnica: −30% desde el máximo de 52 semanas; RS 3m en percentil 78. Sin setup; esperar una base o un EP en resultados."],
        verdict="El mejor negocio del universo hoy (fundamentales al máximo, oferta limpia), pero en pico de ciclo y con el mercado ya vendiendo la memoria. Es un candidato a EP en diciembre, no una compra de tendencia hoy.")
    header = dict(verdict="Superciclo en cifras (+379%, margen 87%) con guía sobre el consenso; el mercado descuenta el pico.",
                  setup="−30% desde máximos; sin setup.", catalyst="4T FY26: beat y guía +8% sobre el consenso; reacción plana.",
                  quality="Sin banderas; márgenes de pico de ciclo.", supply="Limpia: sin convertibles; deuda recomprada.",
                  group="RS 3m percentil 78 dentro de memoria.")
    finish(t, c, kpis, [e], [ins], dict(float_shares=fl.get("float_shares"), float_note=fl.get("note")), text, header, events, [pr, at, fx])


# ---------------------------------------------------------------- SNDK
def sndk():
    t = "SNDK"
    c, rows = base(t)
    q = c["financials"]["quarters"]
    pr = casekit.link(2023554, "0001628280-26-053346", "sndkq4-26ex991xpressrelease.htm", "EX-99.1 8-K 5-ago-2026")
    cm = ["Chartmill: consenso ingresos ≈ $8.562M, BPA ≈ $35,14", "https://www.chartmill.com/news/SNDK/Chartmill-52845-SanDisk-NASDAQSNDK-Beats-Q4-Estimates-But-Shares-Slide-After-Hours"]
    ew = ["Earnings Whispers: consenso $33,28 y $8.300M; consenso 1T FY27 $44,21 y $10.560M", "https://www.earningswhispers.com/epsdetails/SNDK"]
    rk = ["Rivkin: consenso $8.480M y $34,96", "https://rivkin.com.au/?p=37238"]
    e = casekit.earnings(c, rows, "q4fy26", "2026-07-03", "2026-08-05", "amc",
                         "Resultados 4T FY26: ingresos $8.965M (+372%; +51% secuencial) frente a ≈ $8.562M de consenso; BPA ajustado $39,25 frente a $35,14; guía 1T FY27 $10.300–10.800M",
                         [pr, cm, ew, rk], rev_surprise=pct(8965, 8562), eps_surprise=pct(39.25, 35.14), guide_raise=None, guide_change=None,
                         note="El consenso discrepa entre fuentes ($8.300–8.562M de ingresos; $33,28–35,14 de BPA): se usa el de Chartmill, el más alto, para no inflar la sorpresa [VERIFY]. "
                              "Sin consenso previo para la guía del 1T FY27 (después del informe, Earnings Whispers da $10.560M, en el punto medio de la guía). "
                              "El crecimiento secuencial fue ≈ 1/3 volumen y 2/3 precio, según la compañía. El neto GAAP ($6.903M) supera al ajustado ($6.162M): el beat se mide con el ajustado.")
    kpis = [
        kp("Mercados finales (4T FY26)", "Centro de datos $2.977M (33%; +103% secuencial) · Edge $5.432M (+48%) · Consumo $556M (−32%)", "Centro de datos $213M · Edge $1.103M · Consumo $585M (4T FY25)", *pr),
        kp("Origen del crecimiento secuencial", "≈ 1/3 más volumen y 2/3 más precio", "—", *pr),
        kp("Guía 1T FY27", "Ingresos $10.300–10.800M; margen bruto 83,0–85,0% (ajustado); BPA ajustado $44,00–46,00; ≈ 155M acciones", "—", *pr),
        kp("Acuerdos «New Business Model» (NBM)", "10 acuerdos firmados (5 en abril + 3 con clientes nuevos y 2 ampliaciones) [VERIFY: duración, volúmenes y prepagos; contrapartes sin nombre]", "5 (abril de 2026)", *pr),
        kp("Recompras", "Nuevo programa de $14.000M; $15.500M de autorización restante", "—", *pr),
        kp("Inversión en Nanya", "$1.000M por ≈ 139M acciones (3,9%), con 15% de descuento y lock-up de 3 años", "—", "8-K 25-mar-2026 (Item 1.01)", f"{E}/2023554/000119312526122705/d136592d8k.htm"),
        kp("Inventario (días, 4T FY26)", f"≈ {inv_days(q)} días", "—", "quarters.json (XBRL 10-K FY26)")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    fl = forensic_float(t)
    events = [dict(date="2026-11-05", kind="earnings", text="Resultados 1T FY27 [VERIFY: fecha estimada; el 1T FY26 se publicó el 6-nov-2025]",
                   src=[["8-K 6-nov-2025 (Item 2.02)", f"{E}/2023554/000162828025050180/sndk-20251106.htm"]])]
    text = dict(
        narrative_flags=["Los acuerdos NBM no tienen contraparte, volumen ni importe publicados: son una señal de demanda, no cartera verificable.",
                         "El 2/3 del crecimiento secuencial es precio: el NAND es aún más cíclico que la DRAM."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: beat de ingresos y de BPA con aceleración {m.accel_pp:pp}, pero el mercado lo vendió (hueco del −13%). Sin consenso previo para la guía, no se puntúa la sorpresa de guía.",
        financials_note="Trimestres de XBRL (companyfacts) hasta el 4T FY26 (cerrado el 3-jul-2026). Algunos flujos y saldos de 2023–2024 faltan (periodo previo a la escisión de Western Digital, feb-2025). El 1T FY26 (oct-25) tuvo 14 semanas.",
        quality=["Sin banderas automáticas; FCF TTM alto con capex bajo (la capacidad es de la joint venture con Kioxia).",
                 "Márgenes de pico de ciclo (84,6% en el 4T): el objetivo del perfil (40%) no dice nada de su sostenibilidad."],
        supply_read="Western Digital vendió en febrero de 2026 las 7,5M acciones que retenía de la escisión (S-3ASR y 424B7): sale ese exceso de papel. Recompras de $15.500M disponibles. Insiders: ver la fila de oferta.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; con la guía del 1T FY27 anualizada (≈ $42.200M) ≈ 4–5×. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Es el «líder enfriado» del universo: +800% en 12 meses y −45% desde el máximo con los fundamentales intactos.",
        risks=["Precio del NAND: dos tercios del crecimiento secuencial vienen del precio.", "Capacidad nueva de NAND (Kioxia, Samsung, SK hynix, YMTC) en 2027.",
               "Dependencia de la joint venture con Kioxia para la fabricación."],
        plan=["Resultados del 1T FY27 hacia el 5-nov [VERIFY].",
              "**EP A/B si:** ingresos ≥ $11.090M (+5% sobre el consenso de $10.560M), margen bruto ≥ 85% y guía del 2T FY27 ≥ +5% sobre el consenso.",
              "**D si:** ingresos dentro de la guía y margen < 83%: confirmaría que el precio del NAND ha tocado techo.",
              "Técnica: líder enfriado (−45% desde el máximo). Sin setup hoy; es el candidato más claro del universo a un EP en noviembre."],
        verdict="Fundamentales al máximo y líder enfriado: el mercado ya castiga el riesgo de pico del NAND. Candidato a EP el 5-nov si el informe vuelve a superar y la guía sube; si no, el ciclo manda.")
    header = dict(verdict="+372% y margen del 85%, pero el mercado vendió el informe: líder enfriado.",
                  setup="−45% desde máximos; sin setup.", catalyst="4T FY26: beat; hueco del −13%.", quality="Sin banderas; márgenes de pico.",
                  supply="WDC ya vendió su participación; recompras de $15.500M.", group="Líder enfriado del universo.")
    finish(t, c, kpis, [e], [ins], dict(float_shares=fl.get("float_shares"), float_note=fl.get("note")), text, header, events, [pr, cm, ew, rk,
           ["S-3ASR 17-feb-2026 (venta de WDC)", f"{E}/2023554/000119312526054652/d947131ds3asr.htm"]])


# ---------------------------------------------------------------- RMBS
def rmbs():
    t = "RMBS"
    c, rows = base(t)
    q = c["financials"]["quarters"]
    pr = casekit.link(917273, "0001193125-26-318063", "rmbs-ex99_1.htm", "EX-99.1 8-K 27-jul-2026")
    mb = ["MarketBeat: consenso BPA $0,72 e ingresos $199,3M", "https://www.marketbeat.com/stocks/NASDAQ/RMBS/earnings/"]
    hl = ["Hudson Labs: consenso $0,71 y $198,3M; guía 3T frente a $0,78 y $212,97M", "https://hudson-labs.com/research/rambus-q2-2026-earnings"]
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-27", "amc",
                         "Resultados 2T26: ingresos récord $207,4M (+20%) frente a $199,3M de consenso; BPA ajustado $0,77 frente a $0,72; guía 3T $210–216M (consenso $212,97M)",
                         [pr, mb, hl], rev_surprise=pct(207.4, 199.3), eps_surprise=pct(0.77, 0.72), guide_raise=False,
                         guide_change=pct(213, 212.97),
                         note="La guía del 3T queda en el consenso (punto medio $213M frente a $212,97M). El mercado vendió el informe (−9% al cierre); una fuente lo atribuye a la caída del margen bruto de producto hacia el 60% bajo [VERIFY]. Sin partidas no recurrentes en el beat.")
    kpis = [
        kp("Mezcla de ingresos (2T26)", "Producto $99,2M (+22%) · royalties $84,2M · contratos y otros $24,0M", "Producto $81,3M · royalties $68,6M · contratos $22,3M (2T25)", *pr),
        kp("Facturación de licencias (2T26)", "$84,1M", "—", *pr),
        kp("Guía 3T26", "Ingresos $210–216M; producto $110–116M; royalties $69–75M; BPA ajustado $0,75–0,82", "—", *pr),
        kp("Recompra acelerada (ASR)", "$100M con Mizuho; entrega inicial ≈ 796.000 acciones (5-ago-2026)", "—", "8-K 5-ago-2026 (Item 1.01)", f"{E}/917273/000119312526333887/d122300d8k.htm"),
        kp("Inventario (días, 2T26)", f"≈ {inv_days(q)} días; inventario +94% interanual", "—", "quarters.json (XBRL 10-Q 2T26)"),
        kp("Margen bruto de producto", "[VERIFY: 10-Q 2T26; una fuente lo sitúa en el 60% bajo]", "—", "")]
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    fl = forensic_float(t)
    events = [dict(date="2026-10-26", kind="earnings", text="Resultados 3T26 [VERIFY: fecha estimada; el 3T25 se publicó el 27-oct-2025]",
                   src=[["8-K 27-oct-2025 (Item 2.02)", f"{E}/917273/000119312525251595/rmbs-20251027.htm"]])]
    text = dict(
        narrative_flags=["El PR habla de «IA» y de «AI inference», pero la mitad de los ingresos son royalties y contratos con poco crecimiento; el motor es el producto (buffers y PMIC de DDR5)."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: beat de ingresos y de BPA con aceleración {m.accel_pp:pp}, pero guía en línea y el mercado lo vendió (−9%).",
        financials_note="Trimestres de XBRL; el 2T26 (jun-26) se leyó del XBRL incrustado del 10-Q porque companyfacts aún no lo tenía, y coincide con el EX-99.1. En los 4T no hay acciones diluidas trimestrales en XBRL.",
        quality=["**INVENTARIO > VENTAS** activa: inventario +94% interanual frente a ingresos +20%. Puede ser preparación para el 3T (guía de producto +11–17% secuencial) o acumulación [VERIFY: 10-Q].",
                 "SBC ≈ 7% de los ingresos; recompras que lo compensan (ASR de $100M)."],
        supply_read="Sin convertibles ni ampliaciones; recompras activas. Insiders: ver la fila de oferta.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM con crecimiento del 20%: el más caro por crecimiento del universo. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="Es el único del universo que no vive del precio de la memoria sino del contenido por módulo DDR5: crece menos, pero es menos cíclico. −50% desde el máximo.",
        risks=["Competencia en buffers DDR5 (Montage, Renesas) y presión en el margen de producto.", "Royalties planos: el crecimiento depende solo del producto.",
               "Resultados en ≈ 6 sesiones: solo vale un EP."],
        plan=["Resultados del 3T26 hacia el 26-oct [VERIFY]: en la ventana de ≤ 3 sesiones a partir del 21-oct, solo vale un EP.",
              "**EP A/B si:** ingresos ≥ $224M (+5% sobre el consenso de ≈ $213M), producto ≥ $116M (techo de la guía) y guía del 4T ≥ +5% sobre el consenso.",
              "**D si:** ingresos dentro de la guía y margen de producto en el 60% bajo: confirmaría la presión de precios.",
              "Técnica: −50% desde el máximo, bajo la SMA 200; RS 1m en percentil 89 (rebote). Sin setup."],
        verdict="Negocio de calidad (margen bruto del 80%, caja neta) con crecimiento moderado y caro; el mercado le quitó la prima de IA. Solo interesa con un EP el 26-oct.")
    header = dict(verdict="Calidad y caja, crecimiento del 20% y caro; el mercado vendió la guía en línea.",
                  setup="−50% desde máximos; sin setup.", catalyst="2T26: beat, guía en línea; −9%.", quality="Inventario > ventas.",
                  supply="Limpia; recompras.", group="El menos cíclico del universo.")
    finish(t, c, kpis, [e], [ins], dict(float_shares=fl.get("float_shares"), float_note=fl.get("note")), text, header, events, [pr, mb, hl], nonrec_items=False)


# ---------------------------------------------------------------- PENG
def peng():
    t = "PENG"
    c, rows = base(t)
    q = c["financials"]["quarters"]
    pr = casekit.link(1616533, "0001616533-26-000046", "pengq4-26form8xkxex991.htm", "EX-99.1 8-K 6-oct-2026")
    ew = ["Earnings Whispers: consenso $0,75 y $512,5M", "https://earningswhispers.com/epsdetails/PENG"]
    tk = ["TIKR: consenso $0,77 y $521M; FY27 frente a $2.210M y $3,38", "https://www.tikr.com/blog/penguin-solutions-soars-13-on-record-quarter-and-raised-outlook-the-proof-is-in-the-results"]
    cv = casekit.link(1616533, "0001193125-26-307989", "d103073d8k.htm", "8-K 17-jul-2026 (convertibles 2031)")
    sk = ["Schedule 13D/A de SK Telecom, 28-jul-2026", f"{E}/1616533/000119312526318891/xslSCHEDULE_13D_X02/primary_doc.xml"]
    e = casekit.earnings(c, rows, "q4fy26", "2026-08-28", "2026-10-06", "amc",
                         "Resultados 4T FY26: ventas récord $566,7M (+68%) frente a $521M de consenso; BPA ajustado $1,00 frente a $0,77; guía FY27 ≈ $2.430M (+40%) frente a $2.210M",
                         [pr, tk, ew], rev_surprise=pct(566.7, 521), eps_surprise=pct(1.00, 0.77), guide_raise=True, guide_change=pct(2430, 2210),
                         note="Se usa el consenso de TIKR (el más alto); con Earnings Whispers ($512,5M y $0,75) la sorpresa sería mayor [VERIFY]. "
                              "La guía de FY27 sube desde la preliminar de $2.170M a $2.430M ± 10 pp. El BPA GAAP ($1,29) incluye un beneficio fiscal de $57,6M y un gasto de $33,2M por la conversión anticipada de los bonos 2029/2030: el beat se mide con el ajustado.")
    kpis = [
        kp("Segmentos (4T FY26)", "Integrated Memory $340,8M (60%; +158%) · Advanced Computing $154,0M (+11%) · Optimized LED $71,9M (+7%)",
           "Memory $132,2M · Computing $138,3M · LED $67,4M (4T FY25)", *pr),
        kp("Guía FY27", "Ventas ≈ $2.430M (+40% ± 10 pp); BPA GAAP $3,50 ± $0,70; ajustado $4,45 ± $0,70; 63M acciones diluidas", "Preliminar: $2.170M (+30%)", *pr),
        kp("Clientes de infraestructura de IA", "6 nuevos en el 4T (4 neoclouds); 17 en FY26. Un neocloud con > $3.000M en contratos firmados y otro con $10.000M de cómputo contratado con un laboratorio de IA (36.000 GPU en Noruega) [VERIFY: lo que corresponde a Penguin no se publica]", "—", *pr),
        kp("Inventario y cobros (4T FY26)", f"Inventario $748,8M (+193%; ≈ {inv_days(q)} días); cuentas por cobrar $796,3M (+159%)", "$255,2M y $307,9M (4T FY25)", *pr),
        kp("Flujo operativo", "−$163,1M en el 4T y −$151,9M en FY26 por capital circulante (inventario y cobros)", "+$109,1M en FY25", *pr),
        kp("Suministro", "Nuevo acuerdo con un fabricante de memoria líder y un proveedor adicional de infraestructura de IA [VERIFY: nombres]", "—", *pr)]
    conv31 = dict(id="conv31", kind="convertible", name="Convertibles 0% 2031 ($750M, conversión ≈ $116,70)", shares=round(750000 * 8.5690),
                  capacity_usd=None, price_basis=116.70, gate="gated", date="2031-08-01",
                  notes="Conversión inicial de 8,5690 acciones por $1.000 (≈ $116,70, el doble de {m.price:px}); máximo 9,64M acciones con el ajuste por cambio de control. Capped call comprado por $49,1M. Convertibles solo si la acción supera el 130% del precio de conversión: fuera de dinero hoy. Los fondos recompraron parte de los bonos 2029 y 2030 (con un gasto de inducción de $33,2M en el 4T).",
                  src=[cv])
    pref = dict(id="pref_skt", kind="convertible", name="Preferentes convertibles de SK Telecom ($200M)", shares=6096103, capacity_usd=None,
                price_basis=round(200e6 / 6096103, 2), gate="live", date=None,
                notes="6,10M acciones (10,3%) en manos de Astra AI Infra LLC (SK Telecom), muy en dinero. SK Telecom es del mismo grupo que SK hynix (SKHY, en este universo). [VERIFY: restricciones de venta y derechos de conversión en el certificado de designación]",
                src=[sk])
    old = dict(id="conv2930", kind="convertible", name="Restos de los convertibles 2029 y 2030", shares=None, capacity_usd=None, price_basis=None,
               gate="live", date=None, notes="El 10-Q del 3T FY26 recoge $148,4M (2029) y $194,8M (2030), los 2029 convertibles por precio; en el 4T se recompraron $135,5M de los 2029 y se indujo la conversión de parte de ambos [VERIFY: saldo y acciones entregadas en el 10-K FY26].",
               src=[["10-Q 3T FY26", f"{E}/1616533/000161653326000043/peng-20260529.htm"]])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    fl = forensic_float(t)
    events = [dict(date="2027-01-05", kind="earnings", text="Resultados 1T FY27 [VERIFY: fecha estimada; el 1T FY26 se publicó el 6-ene-2026]",
                   src=[["8-K 6-ene-2026 (Item 2.02)", f"{E}/1616533/000161653326000008/peng-20260106.htm"]])]
    text = dict(
        narrative_flags=["Los contratos de $3.000M y $10.000M son de los clientes (neoclouds), no de Penguin: lo que le toca a la compañía no se publica.",
                         "«AI Factory Platform» es la marca; los números dicen que el motor del 4T fue la memoria (+158%), no los sistemas (+11%)."],
        catalyst_read="El 4T FY26 puntúa {m.cat_q4fy26_score:sc}: beat amplio, guía de FY27 +10% sobre el consenso y aceleración {m.accel_pp:pp}, con confirmación de mercado (+13% al cierre, volumen alto).",
        financials_note="Trimestres de XBRL hasta el 3T FY26; el **4T FY26 (ago-26) se cargó a mano** del EX-99.1 del 6-oct porque el 10-K aún no está presentado. Deuda del 4T = corriente + largo plazo. El neto del 4T incluye un beneficio fiscal de $57,6M y un gasto de inducción de $33,2M.",
        quality=["Seis banderas: COBROS > VENTAS, BENEFICIO SIN CAJA, ACCRUALS ALTOS, INVENTARIO > VENTAS, DILUCIÓN y RUNWAY CORTO. El crecimiento se financia con capital circulante: inventario +193% y cobros +159% frente a ventas +68%; CFO negativo en FY26.",
                 "La DILUCIÓN viene de las acciones de los convertibles en las diluidas; el RUNWAY CORTO no tiene en cuenta los $735M netos de los bonos 2031, ya en la caja de agosto.",
                 "Margen bruto del 27,5% (integrador): el más bajo del universo con diferencia."],
        supply_read="Mucho papel potencial: preferentes de SK Telecom (6,1M acciones, 10,3%, en dinero), convertibles 2031 (6,4M acciones a $116,70, fuera de dinero) y restos de los 2029/2030. Insiders: ver la fila de oferta.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM: el más barato del universo, coherente con un margen bruto del 28%. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El de mayor fuerza relativa del universo (percentil 100 a 1, 3 y 6 meses), pero el de peor calidad de beneficio.",
        risks=["Capital circulante: si las ventas se frenan, el inventario de memoria comprado en pico de precios se deprecia.", "Concentración en pocos neoclouds con financiación propia incierta.",
               "Oferta: preferentes de SK Telecom en dinero y convertibles."],
        plan=["Resultados del 1T FY27 hacia el 5-ene [VERIFY].",
              "Sin setup: tras el +13% del 7-oct no hay base. Vigilar un retroceso a la EMA 10/20 en tendencia (ema_crossback) con el stop bajo el mínimo del día del EP.",
              "**D si:** el 1T FY27 vuelve a dar CFO negativo con inventario creciendo más que las ventas."],
        verdict="El único con tendencia y confirmación de mercado, pero con la peor calidad de beneficio (capital circulante, margen bajo, mucho papel convertible). Táctico, no tesis.")
    header = dict(verdict="+68% con guía FY27 +10% sobre el consenso y EP confirmado; calidad de beneficio débil.",
                  setup="Tras el EP del 7-oct, sin base.", catalyst="4T FY26: beat amplio y guía al alza; +13%.", quality="6 banderas: capital circulante.",
                  supply="Preferentes SK Telecom 10,3% y convertibles 2031.", group="RS percentil 100.")
    finish(t, c, kpis, [e], [conv31, pref, old, ins], dict(float_shares=fl.get("float_shares"), float_note=fl.get("note")), text, header, events,
           [pr, tk, ew, cv, sk], nonrec_items=None)




# ---------------------------------------------------------------- SKHY
def skhy():
    t = "SKHY"
    c, rows = base(t)
    k6 = ["6-K 29-jul-2026: resultados preliminares 2T26", f"{E}/2120882/000119312526321989/d115239d6k.htm"]
    ip = ["424B4 9-jul-2026 (OPV del ADR)", f"{E}/2120882/000119312526299963/d32785d424b4.htm"]
    ed = ["Edaily: consenso FnGuide de beneficio operativo ₩63,99 billones", "https://en.edaily.co.kr/news/eda202607295090/"]
    jd = ["Korea JoongAng Daily: récord, pero la acción cae un 9,6% en Seúl", "https://www.koreajoongangdaily.com/business/sk-hynix-posts-record-q2-profit-on-ai-demand-but-shares-slide-on-growth-doubts/12796737"]
    rt = ["6-K 20-ago-2026: política de retribución y recompra de ₩40 billones", f"{E}/2120882/000119312526356139/d425596d6k.htm"]
    nx = ["6-K 14-oct-2026: conferencia del 3T26", f"{E}/2120882/000119312526420934/d413172d6k.htm"]
    rev_cons = 79.3187 + 4.6
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-28", "amc",
                         "Resultados 2T26: ingresos ₩79,32 billones (+257%) y beneficio operativo ₩60,54 billones (margen 76,3%), por debajo del consenso FnGuide (₩63,99 billones)",
                         [k6, ed, jd], rev_surprise=pct(79.3187, rev_cons), eps_surprise=pct(60.5426, 63.9868), guide_raise=None, guide_change=None,
                         note="Fallo frente al consenso: el beneficio operativo queda un 5,4% por debajo de FnGuide; se usa como sorpresa de beneficio porque no hay consenso de BPA comparable [VERIFY]. "
                              "Los ingresos quedan ≈ ₩4,6 billones por debajo (≈ −5,5%) [VERIFY: cifra exacta del consenso de ingresos]. "
                              "Publicado en Seúl el 29-jul a las 9:00 (28-jul a las 20:00 ET): la reacción del ADR es la sesión del 29-jul; en Seúl la acción cayó un 9,6%. "
                              "El neto (₩93,8 billones) supera a los ingresos por ₩53,2 billones de ganancias de valoración de instrumentos financieros: no recurrente.")
    kpis = [
        kp("Mezcla 2T26", "DRAM ₩56,98 billones (71,8%) · NAND ₩21,96 billones (27,7%)", "—", *k6),
        kp("Bits y precios (2T26 frente al 1T26)", "DRAM: bits ligeramente al alza, precio medio +«mid-30%» · NAND: bits +«mid-10%», precio medio +«mid-50%»", "—", *k6),
        kp("Cuota de mercado (1T26, IDC)", "HBM 56,4% · DRAM 29,1% · NAND 18,5% [VERIFY: % de HBM sobre ingresos no publicado]", "—", *ip),
        kp("Clientes ≥ 10% (1S26)", "A 13,35% · B 13,03%", "Un cliente 23,9% (2025)", "6-K informe semestral 1S26", f"{E}/2120882/000119312526354777/d147827d6k.htm"),
        kp("Inversión anunciada", "Yongin Fab 1 y P&T7 (₩45,5 billones con la OPV); M17 ₩19,1 billones; Yongin Fab 2 fases 1–6 ₩35,2 billones (7-ago)", "—", *ip),
        kp("Retribución al accionista", "> 50% del FCF acumulado 2025–2027; recompra para amortizar de hasta 24,07M acciones (≈ ₩40 billones) del 20-ago al 19-nov", "—", *rt),
        kp("Tipo de cambio de los trimestres", "₩1.523,5 por US$ (conversión de conveniencia del 424B4, 31-mar-2026)", "—", *ip)]
    sq = 146_100_000
    fl = dict(float_shares=float((728_866_596 - sq) * 10),
              float_note="Acciones en circulación (728,87M, 6-K 19-ago-2026) menos SK square (146,1M, obligada por ley a mantener ≥ 20%), en ADS equivalentes (1 ADS = 1/10 de acción). Solo 177,9M ADS cotizan en Nasdaq; el resto cotiza en Seúl [VERIFY]")
    supply = [dict(id="ipo_lockup", kind="lockup", name="Lock-up de la OPV del ADR (90 días, compañía y filiales)", shares=None, capacity_usd=None,
                   price_basis=149.0, gate="dated", date="2026-10-07",
                   notes="177,9M ADS a $149 (17,79M acciones nuevas, ≈ 2,4% del capital). Fin del lock-up ≈ 7-oct-2026, ya vencido [VERIFY: fecha exacta]. SK square no puede bajar del 20% por la ley coreana de holdings.",
                   src=[ip])]
    events = [dict(date="2026-10-27", kind="earnings", text="Resultados 3T26: conferencia el 28-oct a las 9:00 de Seúl = 27-oct a las 20:00 ET (tras el cierre en EE. UU.)", src=[nx])]
    text = dict(
        narrative_flags=["El neto del 2T26 (₩93,8 billones) es mayor que los ingresos por ganancias de valoración: no sirve para medir el negocio.",
                         "Solo ≈ 2,4% del capital cotiza como ADR: la liquidez y el precio los marca Seúl."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: crecimiento enorme (+257%) y aceleración {m.accel_pp:pp}, pero por debajo del consenso coreano y con la acción vendida en Seúl.",
        financials_note="Emisor extranjero (K-IFRS, wones): **trimestres cargados a mano** del 424B4 y de los 6-K del 2T26 y del informe semestral, convertidos a US$ a un tipo fijo de ₩1.523,5. **El 3T25 y el 4T25 no están en ningún documento de EDGAR** (SK hynix no era registrante y el folleto solo da años completos y el 1T): quedan como huecos (`gap`), y el TTM, el Rule of 40 y el margen TTM salen n/d. Del 2S25 solo se conoce el agregado (notas.md). Acciones diluidas en ADS equivalentes (× 10).",
        quality=["El neto GAAP está inflado por ganancias de valoración y dividendos cobrados (también inflan el CFO del 2T).",
                 "Sin TTM no se calculan varias banderas: la nota de fundamentales se apoya en el último trimestre."],
        supply_read="Sin convertibles; la recompra de ≈ ₩40 billones para amortizar reduce acciones hasta el 19-nov. El lock-up de la OPV venció ≈ 7-oct. El riesgo de oferta es el propio ADR: poco papel en Nasdaq frente a Seúl.",
        valuation=["Market cap {m.mcap:usdM}. Con el 2T26 anualizado (≈ $208.000M de ingresos), ≈ 4–5× ventas, en línea con MU. EV/ventas TTM n/d por los huecos."],
        group_read="Líder de HBM (56% de cuota en el 1T26 según IDC). Comparable con MU en tamaño; peor reacción a resultados y sin historial de precios suficiente para la fuerza relativa.",
        risks=["Consenso alto: el 2T26 ya falló frente a FnGuide.", "Capex masivo anunciado (Yongin, M17, P&T7) justo en pico de precios.",
               "Clientes: dos ≥ 13% (probablemente NVIDIA y un hyperscaler) [VERIFY].", "Riesgo de cambio ₩/US$ para el inversor en ADR."],
        plan=["Resultados del 3T26 el 27-oct tras el cierre (28-oct en Seúl): dentro de la ventana de ≤ 3 sesiones a partir del 22-oct, solo vale un EP.",
              "**EP A/B si:** beneficio operativo ≥ +5% sobre el consenso de FnGuide [VERIFY: consenso actualizado] y detalles de retribución que superen la recompra de ₩40 billones.",
              "**D si:** segundo fallo frente al consenso: confirmaría que las expectativas van por delante del ciclo.",
              "Técnica: ADR desde el 14-jul (≈ 70 sesiones); −32% desde el máximo. Sin setup."],
        verdict="El líder de HBM a un múltiplo parecido al de MU, pero con el último informe por debajo del consenso, poco ADR en circulación y huecos de datos. Esperar al 27-oct.")
    header = dict(verdict="Líder de HBM con +257%, pero falló el consenso del 2T26; datos con huecos.",
                  setup="ADR nuevo (≈ 70 sesiones); −32% desde máximos.", catalyst="2T26 por debajo del consenso (−5%).",
                  quality="Neto inflado por ganancias de valoración.", supply="Recompra de ₩40 billones; lock-up vencido.", group="Sin RS fiable aún.")
    finish(t, c, kpis, [e], supply, fl, text, header, events, [k6, ip, ed, jd, rt, nx])


# ---------------------------------------------------------------- SIMO
def simo():
    t = "SIMO"
    c, rows = base(t)
    pr = ["EX-99.1 6-K 30-jul-2026: resultados 2T26", f"{E}/1329394/000119312526324391/d114913dex991.htm"]
    wt = ["AP/Zacks (WTOP): consenso BPA $2,13 e ingresos $403,6M", "https://wtop.com/news/2026/07/silicon-motion-q2-earnings-snapshot/"]
    cm = ["Chartmill: consenso BPA $2,18 e ingresos $411,5M", "https://www.chartmill.com/news/SIMO/Chartmill-52160-Silicon-Motion-NASDAQSIMO-Surges-After-Smashing-Q2-Estimates"]
    cv = ["6-K 11-ago-2026: precio del convertible 2031", f"{E}/1329394/000119312526343271/d160732dex991.htm"]
    cv2 = ["6-K 13-ago-2026: cierre del convertible ampliado a $1.150M", f"{E}/1329394/000119312526349730/d149638dex991.htm"]
    ii = ["6-K 10-ago-2026 (EX-99.2): estados intermedios 1S26", f"{E}/1329394/000119312526341199/d124768dex992.htm"]
    nx = ["6-K: fecha de resultados del 3T26", f"{E}/1329394/000119312526417926/d140905dex991.htm"]
    dv = ["6-K 16-oct-2026: dividendo anual $2,30 por ADS (+15%)", f"{E}/1329394/000119312526424083/d413725dex991.htm"]
    e = casekit.earnings(c, rows, "q2_26", "2026-06-30", "2026-07-29", "amc",
                         "Resultados 2T26: ventas $451,0M (+127%; +32% secuencial) frente a $403,6M de consenso; BPA ajustado $2,43 por ADS frente a $2,13; guía 3T $519–541M",
                         [pr, wt, cm], rev_surprise=pct(451.0, 403.6), eps_surprise=pct(2.43, 2.13), guide_raise=None, guide_change=None,
                         note="Consenso de Zacks (AP); Chartmill da $411,5M y $2,18 [VERIFY]. Margen bruto 50,2% frente a 48,5–49,5% guiado. "
                              "El BPA GAAP ($3,99) incluye $74,7M de ganancias no realizadas en acciones de BIWIN y TWSC (clientes): el beat se mide con el ajustado. "
                              "La guía del 3T ($519–541M, +15–20% secuencial) no tiene consenso previo publicado [VERIFY].")
    kpis = [
        kp("Crecimiento por producto (2T26, interanual)", "Controladores SSD +50–55% · eMMC+UFS +95–100% · Ferri y Boot Drive +1.690–1.695%", "—", *pr),
        kp("Guía 3T26", "Ventas $519–541M; margen bruto 49,9–50,9%; margen operativo 24,4–25,7%; crecimiento de 2026 > 100%", "—", *pr),
        kp("Concentración de clientes (1S26)", "PHISEMI 38% · AFASTOR 10%; diez mayores 78%; China $508M de $793M", "Cuatro clientes 59% (1S25)", *ii),
        kp("Inventario", "$673M a jun-26 (desde $181M en mar-25); CFO negativo en el 1T y el 2T26", "—", *ii),
        kp("Arbitraje con MaxLinear (SIAC)", "Reclama la comisión de ruptura de $160M más daños; vistas en oct-25 y mar-26; sin laudo a 30-jun-2026", "—", *ii),
        kp("Dividendo", "$2,30 por ADS al año (+15%), en cuatro pagos de $0,575", "$2,00", *dv)]
    conv = dict(id="conv31", kind="convertible", name="Convertible 0% 2031 ($1.150M, conversión ≈ $380,50 por ADS)", shares=round(1_150_000 * 2.6281),
                capacity_usd=None, price_basis=380.50, gate="gated", date="2031-01-01",
                notes="2,6281 ADS por $1.000 (prima del 65% sobre $230,61); ≈ 3,02M ADS (≈ 9% de los 33,9M en circulación), fuera de dinero a {m.price:px}. Ampliado de $800M propuestos a $1.150M. [VERIFY: vencimiento exacto y capped call]",
                src=[cv, cv2])
    ins = casekit.insider_supply(f"{U}/data/{t}/insiders.json")
    fl = dict(float_shares=33_907_750.0, float_note="ADS equivalentes en circulación a 30-jun-2026 (135,63M ordinarias ÷ 4); los insiders tienen poco [VERIFY: % de directivos en el 20-F]")
    events = [dict(date="2026-10-28", kind="earnings", text="Resultados 3T26 tras el cierre; conferencia el 29-oct a las 8:00 ET", src=[nx])]
    text = dict(
        narrative_flags=["El neto GAAP incluye ganancias no realizadas en acciones de dos clientes chinos (BIWIN, TWSC): $74,7M en el 2T26.",
                         "El arbitraje con MaxLinear ($160M) es un activo contingente: no está en las cuentas y no debe sumarse al valor."],
        catalyst_read="El 2T26 puntúa {m.cat_q2_26_score:sc}: beat amplio (+12% en ventas, +14% en BPA), aceleración {m.accel_pp:pp} y EP de verdad (hueco del +24%), que luego se ha devuelto: la acción está un 40% bajo el máximo.",
        financials_note="Emisor extranjero (20-F/6-K, **US GAAP**): **trimestres cargados a mano** de los 6-K de resultados (mar-24 a jun-26), cada uno del release más reciente; las sumas cuadran con los anuales de 2024 y 2025 y con los estados intermedios del 1S26. Acciones en ADS (1 ADS = 4 ordinarias). El convertible de $1.150M (ago-26) es posterior al último balance.",
        quality=["El neto GAAP está inflado por ganancias de valoración de acciones de clientes.",
                 "Cuatro banderas: BENEFICIO SIN CAJA, ACCRUALS ALTOS, INVENTARIO > VENTAS y RUNWAY CORTO. Todas vienen del inventario (de $181M a $673M) y del CFO negativo del 1S26; el RUNWAY CORTO no recoge el convertible de $1.150M de agosto, posterior al último balance."],
        supply_read="Convertible 2031 fuera de dinero (≈ 3,0M ADS, ≈ 9%). Dividendo creciente. Fidelity tiene el 6,7%. Ventas de consejeros pequeñas.",
        valuation=["EV/ventas {m.ev_sales:x1} TTM; con la guía del 3T anualizada (≈ $2.120M) ≈ 3,5×. DCF inverso: {m.implied_g:pctf} anual."],
        group_read="El fabless del universo: crece más que RMBS y sin depender del precio de la memoria directamente, pero con el 48% de las ventas en dos clientes chinos.",
        risks=["Concentración: PHISEMI y AFASTOR = 48% de las ventas del 1S26.", "Inventario: $673M frente a $451M de ventas trimestrales.",
               "Arbitraje con MaxLinear: costes en opex; un laudo en contra quitaría el activo contingente.", "Resultados en ≈ 8 sesiones."],
        plan=["Resultados del 3T26 el 28-oct tras el cierre.",
              "**EP A/B si:** ventas ≥ $557M (+5% sobre el punto medio de la guía; consenso [VERIFY]), margen bruto ≥ 51% y guía del 4T con otro +15% secuencial.",
              "**D si:** ventas dentro de la guía y más inventario: el crecimiento sería relleno de canal.",
              "Técnica: −40% desde el máximo tras el EP de julio; RS 1m/3m débil. Sin setup."],
        verdict="Crecimiento fabless real (+127%) con margen del 50%, pero concentración china, inventario creciente y un EP ya devuelto. Candidato a EP el 28-oct; el arbitraje con MXL enlaza con el universo semis.")
    header = dict(verdict="+127% con beat amplio y EP en julio, ya devuelto; concentración china e inventario.",
                  setup="−40% desde máximos; sin setup.", catalyst="2T26: beat de ventas +12% y BPA +14%; hueco +24%.",
                  quality="Neto inflado por acciones de clientes.", supply="Convertible 2031 fuera de dinero.", group="Fabless del universo.")
    finish(t, c, kpis, [e], [conv, ins], fl, text, header, events, [pr, wt, cm, cv, cv2, ii, nx, dv])


if __name__ == "__main__":
    for f in sys.argv[1:] or ["mu", "sndk", "rmbs", "peng", "skhy", "simo"]:
        globals()[f]()
        print(f, "ok")
