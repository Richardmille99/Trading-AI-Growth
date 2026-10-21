"""Render a growth-swing dossier (HTML) from a case JSON.

Usage: python render.py case.json [out.html]

Text markup (applied after HTML-escaping):
  {m.key} or {m.key:fmt}    metric from compute.py
     fmt: int M1 M2 usdM px x1 n1 pct (already %) pctf pctf0 (fraction → %) pp (signed pp) sc (score 0 dec)
  [[label|url]]             source chip (url may be empty)
  [VERIFY] / [VERIFY: note] verification badge
  **text**                  bold
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute import compute  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
MINUS = "−"
TYPE_ES = {"gov_contract": "Contrato público", "commercial_contract": "Contrato comercial", "partnership": "Partnership",
           "product": "Producto", "financing": "Financiación", "earnings": "Resultados", "mna": "M&A",
           "index_analyst": "Índice / analista", "other": "Otro"}
BIND_ES = {"definitive": "definitivo", "purchase_order": "orden de compra", "award_funded": "adjudicación con fondos",
           "award_unfunded": "adjudicación sin fondos", "idiq_ceiling": "techo IDIQ", "option_exercise": "ejercicio de opción",
           "loi": "LOI", "mou": "MOU", "partnership_undefined": "alianza sin términos", "none": "ninguno"}
KIND_ES = {"atm": "ATM", "shelf": "Shelf", "secondary": "Secundaria", "convertible": "Convertible", "warrants": "Warrants",
           "lockup": "Lock-up", "insider": "Insiders", "sbc": "SBC", "pipe_resale": "Reventa PIPE"}
GATE = {"live": ("r", "viva"), "gated": ("a", "bloqueada"), "dated": ("b", "con fecha")}
SETUP_ES = {"ep": "Episodic pivot (EP)", "breakout_flag": "Ruptura de bandera", "vcp": "VCP", "momentum_burst": "Momentum burst",
            "wedge_pop": "Wedge pop", "ema_crossback": "EMA crossback", "base_n_break": "Base n' break",
            "exhaustion_watch": "Vigilar agotamiento"}
SETUP_SHORT = {"ep": "EP", "breakout_flag": "Bandera", "vcp": "VCP", "momentum_burst": "Burst", "wedge_pop": "Wedge",
               "ema_crossback": "Crossback", "base_n_break": "Base break", "exhaustion_watch": "Agotam."}
GROUP_ES = {"leader": "líder", "strong": "fuerte", "neutral": "neutral", "weak": "débil", "unknown": "desconocido"}
COMP_ES = {"growth": "Crecimiento", "accel": "Aceleración", "gross_margin": "Margen bruto", "rule40": "Rule of 40",
           "op_leverage": "Apalancamiento operativo", "quality": "Calidad (banderas)"}
CAT_MAX = {"verificable": 25, "vinculante": 20, "materialidad": 20, "economia": 10, "historial": 10, "juxtaposiciones": 15,
           "crecimiento": 25, "aceleracion": 20, "sorpresa": 20, "guia": 25, "calidad": 10}


def _num(v, dec):
    s = f"{abs(v):,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return (MINUS if v < 0 else "") + s


def fmt(v, kind=None):
    if v is None:
        return "n/d"
    if isinstance(v, str):
        return v
    if isinstance(v, bool):
        return "sí" if v else "no"
    k = kind or ("int" if float(v).is_integer() else "n1")
    if k == "int": return _num(round(v), 0)
    if k == "M1": return _num(v / 1e6, 1) + "M"
    if k == "M2": return _num(v / 1e6, 2) + "M"
    if k == "usdM": return (MINUS if v < 0 else "") + "$" + _num(abs(v) / 1e6, 1) + "M"
    if k == "px": return (MINUS if v < 0 else "") + "$" + _num(abs(v), 2)
    if k == "x1": return _num(v, 1) + "×"
    if k == "x2": return _num(v, 2) + "×"
    if k == "n1": return _num(v, 1)
    if k == "sc": return _num(round(v), 0)
    if k == "pct": return _num(v, 1) + "%"
    if k == "pctf": return _num(v * 100, 1) + "%"
    if k == "pctf0": return _num(v * 100, 0) + "%"
    if k == "pp": return ("+" if v > 0 else "") + _num(v, 1) + " pp"
    raise ValueError(f"unknown format {k}")


def sign_cls(v):
    return "" if v is None else "pos" if v > 0 else "neg" if v < 0 else ""


class Renderer:
    def __init__(self, case):
        self.c = case
        self.m, self.R, self.chart = compute(case)
        self.missing = set()

    def t(self, s):
        if s is None:
            return ""
        s = html.escape(str(s), quote=False)

        def metric(mo):
            key, kind = mo.group(1), mo.group(2)
            if key not in self.m:
                self.missing.add(key)
                return f'<span class="v">?{key}</span>'
            return fmt(self.m[key], kind)
        s = re.sub(r"\{m\.([A-Za-z0-9_]+)(?::([A-Za-z0-9]+))?\}", metric, s)

        def link(mo):
            label, url = mo.group(1), mo.group(2).strip()
            if url:
                return f'<a class="src" href="{html.escape(url, quote=True)}">{label}</a>'
            return f'<span class="src">{label}</span>'
        s = re.sub(r"\[\[([^\]|]+)\|([^\]]*)\]\]", link, s)
        s = re.sub(r"\[VERIFY(?::\s*([^\]]+))?\]",
                   lambda mo: f'<span class="v">VERIFY{(" " + mo.group(1)) if mo.group(1) else ""}</span>', s)
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    def srcs(self, pairs):
        return " ".join(self.t(f"[[{a}|{b}]]") for a, b in (pairs or []))

    @staticmethod
    def table(head, rows, numeric=(), row_cls=None):
        th = "".join(f'<th class="n">{h}</th>' if i in numeric else f"<th>{h}</th>" for i, h in enumerate(head))
        out = []
        for j, r in enumerate(rows):
            tds = "".join(f'<td class="n">{c}</td>' if i in numeric else f"<td>{c}</td>" for i, c in enumerate(r))
            cls = f' class="{row_cls[j]}"' if row_cls and row_cls[j] else ""
            out.append(f"<tr{cls}>{tds}</tr>")
        return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(out)}</tbody></table></div>'

    @staticmethod
    def st(level, label):
        return f'<span class="st {level}">{label}</span>'

    @staticmethod
    def gr(g):
        return f'<span class="gr {g}">{g}</span>'

    def flags(self, fl):
        return '<span class="fl">' + "".join(self.st("r", html.escape(f)) for f in fl) + "</span>" if fl else "—"

    def section(self, no, sid, title, body):
        return f'<section id="{sid}"><div class="sh"><span class="no">§{no}</span><h2>{title}</h2></div>{body}</section>'

    def parts(self, comps, maxes):
        out = []
        for k, v in comps.items():
            mx = maxes.get(k, 100)
            w = 0 if v is None else max(0, min(100, v / mx * 100))
            lab = COMP_ES.get(k, k.replace("_", " ").capitalize())
            out.append(f'<div class="part"><span class="lb">{lab}</span><span class="tr"><i style="width:{w:.0f}%"></i></span>'
                       f'<span class="vl">{"n/d" if v is None else fmt(v, "sc")}/{mx}</span></div>')
        return f'<div class="parts">{"".join(out)}</div>'

    # ---------- header ----------
    def header(self):
        c, m, R, meta = self.c, self.m, self.R, self.c["meta"]
        h = c.get("header", {})
        strip = (f'<div class="strip"><span>Caso <b>{meta["ticker"]}</b></span><span>CIK {meta.get("cik", "n/d")}</span>'
                 f'<span>{html.escape(meta["exchange"])}</span><span>Corte {meta["report_date"]}</span>'
                 f'<span>Perfil {html.escape(R["fund"]["profile"]["label"])}</span><span>Tema {html.escape(meta.get("theme", "n/d"))}</span></div>')
        syn = ('<div class="synthetic"><b>CASO SINTÉTICO.</b> Empresa, pares y cifras inventados para probar la plantilla; '
               'no describen a ninguna compañía real.</div>') if meta.get("synthetic") else ""
        p = R["primary"]
        fs, ss = m["fund_score"], R["supply"]["total"]

        def lvl_score(v, hi, lo):
            return "na" if v is None else "up" if v >= hi else "mid" if v >= lo else "down"
        cat_l = {"A": "up", "B": "up", "C": "mid", "D": "down"}.get(p["grade"] if p else None, "na")
        st = c.get("setup", {})
        grp = R["group"]
        if not st.get("type") or m["pivot"] is None:
            set_l = "na"
        elif st["type"] == "exhaustion_watch":
            set_l = "down"
        elif (m["risk_adr"] or 0) > 1 or (m["ext_pivot"] or 0) > .05:
            set_l = "mid"
        else:
            set_l = "up"
        risk_txt = f'riesgo {fmt(m["risk_adr"], "x1")} ADR' if m["risk_adr"] else ""
        tiles = [
            ("Setup", set_l, SETUP_SHORT.get(st.get("type"), "n/d"), risk_txt, h.get("setup")),
            ("Catalizador", cat_l, p["grade"] if p else "—", f'{p["score"]}/100' if p else "", h.get("catalyst")),
            ("Calidad", lvl_score(fs, 65, 45), fmt(fs, "sc"), R["fund"]["score"]["label"] or "", h.get("quality")),
            ("Oferta", lvl_score(ss, 75, 50), fmt(ss, "sc"), R["supply"]["label"], h.get("supply")),
            ("Grupo", {"leader": "up", "strong": "up", "neutral": "mid", "weak": "down"}.get(grp, "na"),
             GROUP_ES[grp], f'fund. p{fmt(m["fund_pct"], "sc")} · RS p{fmt(m["rs_pct"], "sc")}', h.get("group")),
        ]
        tl = "".join(f'<div class="tile {cls}"><span class="k">{k}</span><span class="g"><b>{html.escape(str(big))}</b>'
                     f'<span>{html.escape(str(small))}</span></span><p>{self.t(txt)}</p></div>'
                     for k, cls, big, small, txt in tiles)
        verdict = (f'<div class="verdict"><span class="k">Convicción</span><span class="lv">{R["conviction"]}</span>'
                   f'<span class="sz">{fmt(m["size_r"], "x2").replace("×", " R")}</span>'
                   f'<p>{self.t(h.get("verdict"))}</p></div>')
        return (f'<header class="case" id="s0">{strip}<h1>{html.escape(meta["issuer"])} <em>{meta["ticker"]}</em></h1>'
                f'<p class="desc">{self.t(meta.get("descriptor"))}</p>{syn}<div class="board">{verdict}{tl}</div></header>')

    def s1(self):
        rows = "".join(f"<div><dt>{html.escape(k)}</dt><dd>{self.t(v)}</dd></div>" for k, v in self.c.get("snapshot", []))
        return self.section(1, "s1", "Snapshot", f'<dl class="kv">{rows}</dl>')

    def s2(self):
        R, txt = self.R, self.c.get("text", {})
        rows, cls = [], []
        for k in sorted(R["catalysts"], key=lambda x: x["date"] or "", reverse=True):
            val = "—"
            if k.get("value_firm"):
                val = fmt(k["value_firm"], "usdM") + " firme"
            elif k.get("value_ceiling"):
                val = fmt(k["value_ceiling"], "usdM") + " techo"
            rows.append([k["date"], self.t(k["headline"]), TYPE_ES.get(k["type"], k["type"]),
                         BIND_ES.get(k.get("binding"), "—") if k["type"] not in ("earnings", "financing", "index_analyst") else "—",
                         val, f'{self.gr(k["grade"])} {k["score"]}', k["verdict"], self.flags(k["flags"]),
                         "—" if k["market"] is None else str(k["market"]), self.srcs(k["src"])])
            cls.append("me" if R["primary"] and k["id"] == R["primary"]["id"] else "")
        p = R["primary"]
        caps = "".join(f"<li>{html.escape(x)}</li>" for x in p["caps"]) if p and p["caps"] else ""
        red = "".join(f"<li>{self.t(x)}</li>" for x in txt.get("narrative_flags", []))
        body = ('<p class="lede">Cada catalizador se puntúa con la checklist de verificación (references/catalysts.md). '
                'La confirmación de mercado va aparte y nunca se suma: un D con mercado fuerte es una operación corta, no una tesis. '
                'Fila resaltada = catalizador principal del setup.</p>'
                + self.table(["Fecha", "Titular", "Tipo", "Vínculo", "Valor", "Nota", "Veredicto", "Banderas", "Mercado", "Fuente"],
                             rows, numeric=(8,), row_cls=cls))
        if p:
            body += (f'<h3>2.1 Desglose del principal · {self.t(p["headline"])}</h3>'
                     + self.parts(p["components"], CAT_MAX)
                     + (f'<ul class="pl">{caps}</ul>' if caps else "")
                     + (f'<p class="cap">{self.t(p.get("note"))}</p>' if p.get("note") else ""))
        if red:
            body += f'<h3>2.2 Señales narrativas</h3><ul class="pl">{red}</ul>'
        body += f'<div class="read">{self.t(txt.get("catalyst_read"))}</div>'
        return self.section(2, "s2", "Catalizadores", body)

    def s3(self):
        F, q = self.R["fund"], self.c["financials"]["quarters"]
        ser = {s["period"]: s for s in F["series"]}
        rows = []
        for x in q[-8:][::-1]:
            s = ser.get(x["period"], {})
            rev = x.get("revenue")
            fcf = None if x.get("cfo") is None or x.get("capex") is None else x["cfo"] - x["capex"] - (x.get("capitalized_sw") or 0)
            a = s.get("accel")
            rows.append([x["period"], fmt(rev, "usdM"), fmt(s.get("yoy"), "pctf"),
                         f'<span class="{sign_cls(a)}">{fmt(a, "pp")}</span>',
                         fmt(x["gross_profit"] / rev if rev and x.get("gross_profit") is not None else None, "pctf"),
                         fmt(x["op_income"] / rev if rev and x.get("op_income") is not None else None, "pctf"),
                         fmt(fcf / rev if rev and fcf is not None else None, "pctf")])
        kp = [[self.t(k["name"]), self.t(k.get("value")), self.t(k.get("prior")), self.srcs(k.get("src"))]
              for k in self.c.get("manual", {}).get("kpis", [])]
        want = F["profile"].get("kpis", [])
        sc = F["score"]
        miss = f' Componentes sin dato (peso redistribuido): {", ".join(COMP_ES[k] for k in sc["missing"])}.' if sc["missing"] else ""
        body = ('<div class="chart" id="growth"></div>'
                '<div class="legend"><span><i style="background:var(--accent)"></i>Último trimestre</span>'
                '<span><i style="background:var(--dot)"></i>Trimestres anteriores</span>'
                '<span><i style="background:var(--up)"></i>Acelera</span><span><i style="background:var(--down)"></i>Desacelera</span></div>'
                + self.table(["Trimestre", "Ingresos", "Interanual", "Aceleración", "M. bruto", "M. operativo", "M. FCF"], rows,
                             numeric=(1, 2, 3, 4, 5, 6))
                + f'<p class="cap">{self.t(self.c.get("text", {}).get("financials_note"))}</p>'
                + f'<h3>3.1 Nota de fundamentales · {fmt(sc["total"], "sc")}/100 ({sc["label"]})</h3>'
                + self.parts(sc["components"], {})
                + f'<p class="cap">Pesos del perfil: {", ".join(f"{COMP_ES[k]} {fmt(v * 100, "sc")}%" for k, v in sc["weights"].items())}.{miss}</p>'
                + '<h3>3.2 KPIs del perfil (manuales)</h3>'
                + (self.table(["KPI", "Último", "Anterior", "Fuente"], kp) if kp else "")
                + (f'<p class="cap">KPIs que pide el perfil: {", ".join(want)}.</p>' if want else ""))
        return self.section(3, "s3", "Fundamentales de crecimiento", body)

    def s4(self):
        rows, cls = [], []
        for f in self.R["fund"]["flags"]:
            state = self.st("x", "n/d") if f["on"] is None else self.st("r", "ACTIVA") if f["on"] else self.st("g", "no")
            v = f["value"]
            val = "n/d" if v is None else fmt(v, "pp") if "pp" in f["rule"] else fmt(v, "n1") + " meses" if "meses" in f["rule"] \
                else fmt(v, "usdM") if f["name"] == "BENEFICIO SIN CAJA" else fmt(v, "pctf")
            rows.append([f'<b>{html.escape(f["name"])}</b>', state, val, html.escape(f["rule"])])
            cls.append("" if f["on"] else "off")
        body = (self.table(["Bandera", "Estado", "Valor", "Regla"], rows, numeric=(2,), row_cls=cls)
                + "".join(f"<p>{self.t(p)}</p>" for p in self.c.get("text", {}).get("quality", [])))
        return self.section(4, "s4", "Calidad del beneficio", body)

    def s5(self):
        S, m = self.R["supply"], self.m
        rows = []
        for s in S["rows"]:
            lv, lab = GATE.get(s.get("gate"), ("x", s.get("gate") or "n/d"))
            vs = s.get("vs_price")
            pb = "—" if not s.get("price_basis") else f'{fmt(s["price_basis"], "px")} <span class="{sign_cls(vs)}">({fmt(vs, "pctf0")})</span>'
            sh = fmt(s.get("shares"), "int") if s.get("shares") else (fmt(s.get("capacity_usd"), "usdM") + " cap." if s.get("capacity_usd") else "—")
            date = (s.get("date") or "—") + (" · en ventana" if s["in_window"] else "")
            rows.append([self.t(s["name"]), KIND_ES.get(s["kind"], s["kind"]), sh, fmt(s.get("pct_float"), "pctf"), pb,
                         self.st(lv, lab), date, self.t(s.get("notes")), self.srcs(s.get("src"))])
        rr = [[html.escape(r["rule"]), self.st("r", "aplica") if r["applied"] else self.st("x", "no"),
               fmt(r["delta"], "int") if r["applied"] else "0", self.t(r["detail"])] for r in S["rules"]]
        body = (f'<p class="lede">Lo que importa para un swing: cuánto papel puede venderse encima de la entrada en las próximas '
                f'{self.R["window"] // 7} semanas. Float de referencia {fmt(m["float_shares"], "M1")}; '
                f'oferta viva a precio actual ≈ {fmt(m["overhang_pct"], "pctf")} del float.</p>'
                + self.table(["Fuente", "Tipo", "Acciones / capacidad", "% float", "Precio base (vs actual)", "Gate", "Fecha",
                              "Notas", "Fuente"], rows, numeric=(2, 3))
                + f'<h3>5.1 Nota de oferta · {S["total"]}/100 ({S["label"]})</h3>'
                + self.table(["Regla", "Estado", "Puntos", "Detalle"], rr, numeric=(2,))
                + f'<div class="read">{self.t(self.c.get("text", {}).get("supply_read"))}</div>')
        return self.section(5, "s5", "Dilución y oferta", body)

    def s6(self):
        m = self.m
        kv = [("Precio", fmt(m["price"], "px") + f' · {html.escape(self.c["meta"].get("price_basis", ""))}'),
              ("Acciones (portada)", fmt(m["shares_out"], "M2")), ("Market cap", fmt(m["mcap"], "usdM")),
              ("Caja neta", fmt(m["net_cash"], "usdM")), ("EV", fmt(m["ev"], "usdM")),
              ("Ingresos TTM", fmt(m["revenue_ttm"], "usdM")), ("EV / ventas", fmt(m["ev_sales"], "x1")),
              ("EV / beneficio bruto", fmt(m["ev_gp"], "x1")), ("EV/ventas ÷ crecimiento", fmt(m["ev_sales_g"], "x2")),
              ("DCF inverso", (fmt(m["implied_g"], "pctf") + " anual 5 años") if m["implied_g"] is not None else "n/d"),
              ("Crecimiento TTM actual", fmt(m["rev_ttm_yoy"], "pctf")),
              ("Margen FCF objetivo", fmt(m["fcf_target"], "pctf0") + " (perfil) en el año 5")]
        rows = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in kv)
        body = (f'<dl class="kv">{rows}</dl><p class="cap">DCF inverso: crecimiento de ingresos de los años 1–5 que iguala el valor '
                'presente al EV. Margen FCF desde el TTM actual hasta el objetivo del perfil en el año 5; crecimiento que se desvanece '
                'hasta el 3% entre los años 6 y 10; descuento 10%; terminal de Gordon.</p>'
                + "".join(f"<p>{self.t(p)}</p>" for p in self.c.get("text", {}).get("valuation", [])))
        return self.section(6, "s6", "Valoración y expectativas", body)

    def s7(self):
        rows, cls = [], []
        for r in self.R["peers"]:
            rows.append([f'<b>{html.escape(r["ticker"])}</b>', html.escape(r.get("name") or ""), fmt(r.get("rev_yoy"), "pctf"),
                         fmt(r.get("accel_pp"), "pp"), fmt(r.get("gm"), "pctf"), fmt(r.get("rule40"), "n1"),
                         fmt(r.get("ev_sales"), "x1"), fmt(r.get("rs_3m"), "sc"), fmt(r["fund_pct"], "sc"),
                         fmt(r["rs_pct"], "sc"), fmt(r["value_pct"], "sc")])
            cls.append("me" if r["subject"] else "")
        body = (f'<p class="lede">Posición en el grupo: <b>{GROUP_ES[self.R["group"]]}</b>. Percentiles frente a los demás miembros '
                '(0–100). Fundamentales = media de crecimiento, aceleración, margen bruto y Rule of 40. Valor = EV/ventas ÷ crecimiento, '
                'más alto = más barato.</p>'
                '<div class="chart" id="quadrant"></div>'
                '<p class="cap">Líneas discontinuas = medianas del grupo. Punto resaltado = caso analizado.</p>'
                + self.table(["Ticker", "Nombre", "Crec.", "Acel.", "M. bruto", "R40", "EV/ventas", "RS 3m", "P. fund.", "P. RS", "P. valor"],
                             rows, numeric=tuple(range(2, 11)), row_cls=cls)
                + f'<div class="read">{self.t(self.c.get("text", {}).get("group_read"))}</div>')
        return self.section(7, "s7", "Grupo y pares", body)

    def s8(self):
        st, m = self.c.get("setup", {}), self.m
        adr_flag = ' <span class="st a">&gt; 1 ADR</span>' if m["risk_adr"] and m["risk_adr"] > 1 else ""
        kv = [("Setup", SETUP_ES.get(st.get("type"), "n/d")), ("Pivote", fmt(m["pivot"], "px")), ("Stop", fmt(m["stop"], "px")),
              ("Riesgo / acción", f'{fmt(m["risk_ps"], "px")} · {fmt(m["risk_pct"], "pctf")}'),
              ("ADR% (20 s.)", fmt(m["adr_pct"], "pct")), ("Riesgo en ADRs", fmt(m["risk_adr"], "x1") + adr_flag),
              ("Precio vs pivote", fmt(m["ext_pivot"], "pctf")),
              ("RS 1m / 3m / 6m", " / ".join(fmt(st.get(k), "sc") for k in ("rs_1m", "rs_3m", "rs_6m"))),
              ("EMAs 10 > 20 > 50", fmt(st.get("ema_stack")))]
        rows = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in kv)
        body = f'<dl class="kv">{rows}</dl><p>{self.t(st.get("notes"))}</p>'
        return self.section(8, "s8", "Precio y setup", body)

    def s9(self):
        rows, cls = [], []
        for e in self.R["events"]:
            ses = "" if e["sessions"] is None else f' · {e["sessions"]} sesiones'
            rows.append([e["date"] + ses, html.escape(e.get("kind", "")), self.t(e["text"]),
                         self.st("a", "en ventana") if e["in_window"] else "—", self.srcs(e.get("src"))])
            cls.append("" if e["in_window"] or e["sessions"] is not None else "off")
        risks = "".join(f"<li>{self.t(x)}</li>" for x in self.c.get("text", {}).get("risks", []))
        body = (self.table(["Fecha", "Tipo", "Evento · efecto esperado", "Ventana", "Fuente"], rows, row_cls=cls)
                + f'<h3>9.1 Riesgos de la tesis</h3><ul class="pl">{risks}</ul>')
        return self.section(9, "s9", "Riesgos y eventos", body)

    def s10(self):
        R, m, txt = self.R, self.m, self.c.get("text", {})
        p = R["primary"]
        inputs = (f'Catalizador {p["grade"] if p else "—"} · fundamentales {fmt(m["fund_score"], "sc")} · oferta {R["supply"]["total"]} · '
                  f'grupo {GROUP_ES[R["group"]]} · resultados en ≤ 3 sesiones: {"sí" if R["earnings_soon"] else "no"}')
        trace = "".join(f"<li>{html.escape(x)}</li>" for x in R["trace"])
        plan = "".join(f"<li>{self.t(x)}</li>" for x in txt.get("plan", []))
        body = (f'<div class="two"><div><h3>10.1 Matriz de convicción</h3><p class="lede">{inputs}</p><ol class="trace">{trace}</ol>'
                f'<p><b>{R["conviction"]}</b> · tamaño {fmt(m["size_r"], "x2").replace("×", " R")} · {html.escape(R["horizon"])}</p></div>'
                f'<div><h3>10.2 Plan</h3><ul class="pl">{plan}</ul></div></div>'
                f'<div class="read">{self.t(txt.get("verdict"))}</div>')
        return self.section(10, "s10", "Plan y veredicto", body)

    def footer(self):
        items = "".join(f'<li><a href="{html.escape(u, quote=True)}">{html.escape(l)}</a></li>' if u else f"<li>{html.escape(l)}</li>"
                        for l, u in self.c.get("sources", []))
        return (f'<footer><p><b>Fuentes</b></p><ol>{items}</ol>'
                '<p>Marco mecánico de investigación; no es consejo de inversión. Las notas solo valen lo que valide el diario de calibración. '
                'Las marcas <span class="v">VERIFY</span> señalan datos que faltan o no se han contrastado. '
                f'Plantilla growth-swing v{self.c.get("schema_version", "1.0")}.</p></footer>')

    def bar(self):
        names = ["Snapshot", "Catalizadores", "Fundamentales", "Calidad", "Oferta", "Valoración", "Grupo", "Setup", "Eventos", "Plan"]
        links = '<a href="#s0">Veredicto</a>' + "".join(f'<a href="#s{i}">§{i} {n}</a>' for i, n in enumerate(names, 1))
        meta = self.c["meta"]
        return (f'<div class="bar"><div class="in"><span class="tk">{meta["ticker"]}<span>·</span>swing</span>'
                f'<nav aria-label="Secciones">{links}</nav></div></div>')

    def render(self):
        css = open(os.path.join(ASSETS, "report.css"), encoding="utf-8").read()
        js = open(os.path.join(ASSETS, "charts.js"), encoding="utf-8").read()
        data = json.dumps(self.chart, ensure_ascii=False).replace("</", "<\\/")
        meta = self.c["meta"]
        main = "".join([self.header(), self.s1(), self.s2(), self.s3(), self.s4(), self.s5(), self.s6(), self.s7(),
                        self.s8(), self.s9(), self.s10(), self.footer()])
        if self.missing:
            raise KeyError(f"metrics referenced but not computed: {sorted(self.missing)}")
        fonts = ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700"
                 "&family=IBM+Plex+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap")
        return (f'<!doctype html>\n<html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{meta["ticker"]} Swing Dossier</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="stylesheet" href="{fonts}">\n'
                f'<style>\n{css}\n</style>\n{self.bar()}<main class="wrap">{main}</main>\n'
                f'<script type="application/json" id="chart-data">{data}</script>\n<script>\n{js}\n</script>\n')


def main():
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else f'{case["meta"]["ticker"]}_swing.html'
    page = Renderer(case).render()
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out} ({len(page):,} bytes); VERIFY flags: {page.count('class=\"v\"')}")


if __name__ == "__main__":
    main()
