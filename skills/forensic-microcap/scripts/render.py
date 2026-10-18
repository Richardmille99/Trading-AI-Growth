"""Render a forensic dilution & supply report (HTML) from a case JSON.

Usage: python render.py case.json [out.html]

Text fields accept a small markup, applied after HTML-escaping:
  {m.key} or {m.key:fmt}   metric from compute.py   fmt: int M1 M2 x x1 x1n pct pct0 pct0x px px3 usd usd0 usdM
  [[label|url]]            source chip (url may be empty)
  [VERIFY] / [VERIFY: note] verification badge
  **text**                 bold
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute import compute  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
MINUS = "−"


def _num(v, dec):
    s = f"{abs(v):,.{dec}f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return (MINUS if v < 0 else "") + s


def fmt(v, kind=None):
    if isinstance(v, str) or v is None:
        return "n/d" if v is None else v
    k = kind or ("int" if float(v).is_integer() else "x1n")
    if k == "int": return _num(round(v), 0)
    if k == "M1": return _num(v / 1e6, 1) + "M"
    if k == "M2": return _num(v / 1e6, 2) + "M"
    if k == "x": return _num(v, 2) + "×"
    if k == "x1": return _num(v, 1) + "×"
    if k == "x1n": return _num(v, 1)
    if k == "pct": return _num(v, 1) + "%"
    if k == "pct0": return _num(v, 0) + "%"
    if k == "pct0x": return _num(v * 100, 0) + "%"
    if k == "px": return ("" if v >= 0 else MINUS) + "$" + _num(abs(v), 2)
    if k == "px3": return "$" + _num(v, 3)
    if k in ("usd", "usd0"): return ("" if v >= 0 else MINUS) + "$" + _num(abs(round(v)), 0)
    if k == "usdM": return ("" if v >= 0 else MINUS) + "$" + _num(abs(v) / 1e6, 2) + "M"
    raise ValueError(f"unknown format {k}")


class Renderer:
    def __init__(self, case):
        self.c = case
        self.m, self.chart = compute(case)
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
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return s

    def srcs(self, pairs):
        return " ".join(self.t(f"[[{a}|{b}]]") for a, b in (pairs or []))

    def table(self, head, rows, numeric=()):
        th = "".join(f"<th>{h}</th>" for h in head)
        out = []
        for r in rows:
            tds = "".join(f'<td class="n">{c}</td>' if i in numeric else f"<td>{c}</td>" for i, c in enumerate(r))
            out.append(f"<tr>{tds}</tr>")
        return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(out)}</tbody></table></div>'

    @staticmethod
    def st(level, label):
        return f'<span class="st {level}">{label}</span>'

    def section(self, no, sid, title, body):
        return f'<section id="{sid}"><div class="sh"><span class="no">§{no}</span><h2>{title}</h2></div>{body}</section>'

    # ---------- blocks ----------
    def header(self):
        c, m, meta = self.c, self.m, self.c["meta"]
        h = c["header"]
        strip = (f'<div class="strip"><span>Caso <b>{meta["ticker"]}</b></span><span>CIK {meta["cik"]}</span>'
                 f'<span>{meta["exchange"]}</span><span>Corte {meta["report_date"]}</span>'
                 f'<span>Base: {html.escape(meta["price_basis"])}</span></div>')
        tiles = [
            ("t-mixed wide", h.get("verdict", "MIXTO"), h["mixed"]),
            ("t-live", "Vivo hoy · dilución", h["live"]),
            ("t-gate", "Bloqueado hasta", h["gated"]),
            ("t-act", "Actores · qué necesitan", h["actors"]),
            ("t-chg", "Cambia el cuadro", h["changes"]),
        ]
        tl = "".join(f'<div class="tile {cls}"><span class="lab"><i></i>{lab}</span><p>{self.t(txt)}</p></div>'
                     for cls, lab, txt in tiles)
        return (f'<header class="case" id="s0">{strip}<h1>{html.escape(meta["issuer"])} '
                f'<em>({meta["exchange"].split()[0]}: {meta["ticker"]})</em></h1>'
                f'<p class="desc">{self.t(meta["descriptor"])}</p><div class="tiles">{tl}</div></header>')

    def grades(self):
        g = self.c["grades"]
        order = [("overhead", "Oferta flotante"), ("dilution", "Dilución"), ("frequency", "Frecuencia"),
                 ("offering", "Capacidad de oferta"), ("cash", "Necesidad de caja"), ("compliance", "Cumplimiento")]
        levels = [g[k]["level"] for k, _ in order]
        nA, nM = levels.count("Alto"), levels.count("Medio")
        overall = "Alto" if nA >= 3 else ("Medio" if nA + nM >= 3 else "Bajo")
        bars = '<span class="bars"><span></span><span></span><span></span></span>'
        cells = [f'<div class="meter overall {overall}"><span class="k">Riesgo global</span>{bars}'
                 f'<span class="val">{overall}</span><span class="why">{nA} Altos y {nM} Medios en seis componentes</span></div>']
        for k, lab in order:
            cells.append(f'<div class="meter {g[k]["level"]}"><span class="k">{lab}</span>{bars}'
                         f'<span class="val">{g[k]["level"]}</span><span class="why">{self.t(g[k]["why"])}</span></div>')
        return (f'<div class="meters" aria-label="Calificaciones">{"".join(cells)}</div>'
                f'<p class="note">{self.t(self.c.get("grades_note"))}</p>'
                f'<div class="alert">{self.t(self.c.get("alert"))}</div>')

    def s1(self):
        rows = "".join(f"<div><dt>{html.escape(k)}</dt><dd>{self.t(v)}</dd></div>" for k, v in self.c["snapshot"])
        return self.section(1, "s1", "Snapshot", f'<dl class="kv">{rows}</dl>')

    def gate_rows(self):
        m, rows = self.m, []
        lvl = {"live": "r", "gated": "a", "price": "a", "issued": "b"}
        for i in self.c["instruments"]:
            iid = i["id"]
            if i.get("supply", {}).get("model") == "shelf_ib5":
                shares = f'{fmt(m["shelf_sh_floor"], "int")}–{fmt(m["shelf_sh_now"], "int")}'
            elif "shares_min" in i:
                shares = f'{fmt(m[iid + "_min"], "int")}–{fmt(m[iid + "_max"], "int")}'
            else:
                shares = fmt(m[iid + "_max"], "int")
            rows.append([self.t(i["name"]), shares, self.st(lvl.get(i["gate"], "a"), self.t(i["gate_label"])),
                         self.t(i["arming"]), self.srcs(i.get("src"))])
        for e in self.c.get("ledger_extra", []):
            rows.append([self.t(e["name"]), self.t(e["shares"]), self.st(e["gate_level"], self.t(e["gate_label"])),
                         self.t(e["arming"]), self.srcs(e.get("src"))])
        return rows

    def s2(self):
        body = ('<p class="lede">Base actual: conteos anteriores a cada split divididos por su ratio. Barras = conteos declarados '
                'en balances, portadas y prospectos; escala logarítmica. Pasa el cursor por cada barra para ver cifra y fuente.</p>'
                '<div class="chart" id="ladder"></div><div class="legend" id="ladder-legend"></div>'
                f'<p class="cap">{self.t(self.c["os_caption"])}</p>'
                '<h3>2.1 Oferta por nivel de precio + ledger de gates</h3>'
                '<div class="chart" id="supply"></div><div class="legend" id="supply-legend"></div>'
                f'<p class="cap">{self.t(self.c["supply_caption"])}</p>'
                + self.table(["Capa", "Acciones", "Gate", "Evento que la arma", "Fuente"], self.gate_rows(), numeric=(1,)))
        return self.section(2, "s2", "O/S histórico y dilución potencial", body)

    def s3(self):
        c = self.c
        reg = [[self.t(r[0]), self.t(r[1]), self.t(r[2]), self.st(r[3], self.t(r[4]))] for r in c["registrations"]]
        fac = [[self.t(r[0]), self.t(r[1]), self.t(r[2]), self.st(r[3], self.t(r[4]))] for r in c["facilities"]]
        off = [[self.t(x) for x in r] for r in c["offerings"]]
        body = (f'<p>{self.t(c["capital_intro"])}</p>'
                '<h3>3.1 Registros y capacidad primaria</h3>' + self.table(["Ruta", "Presentado / efectivo", "Capacidad", "Estado"], reg) +
                '<h3>3.2 Facilidades activas</h3>' + self.table(["Facilidad", "Tamaño / registrado", "Precio y condiciones", "Estado"], fac) +
                f'<p class="cap">{self.t(c.get("facilities_note"))}</p>'
                f'<h3>3.3 Warrants en circulación</h3><p>{self.t(c.get("warrants_text"))}</p>'
                f'<h3>3.4 Convertibles y tasa variable</h3><p>{self.t(c.get("convertibles_text"))}</p>'
                f'<h3>3.5 Ofertas y emisiones completadas</h3><p class="lede">{self.t(c.get("offerings_note"))}</p>'
                + self.table(["Fecha", "Tipo", "Acciones (aj.)", "Precio (aj.)", "Captado", "Banco / inversor", "Vendible", "Fuente"], off, numeric=(2,))
                + f'<div class="read">{self.t(c.get("offerings_read"))}</div>')
        return self.section(3, "s3", "Estructura de capital y oferta viva", body)

    def s4(self):
        rows = [[self.t(d), f'<span class="ty {ty}">{ty}</span>', self.t(x)] for d, ty, x in self.c["timeline"]]
        body = ('<p class="lede">Más reciente primero; horas = aceptación EDGAR o hora del wire, ET. Tipos: CAP capital/oferta · '
                'LEG legal · PR promocional · GOV gobierno · FIN financiero · MKT mercado.</p>'
                + self.table(["Fecha", "Tipo", "Evento"], rows) + f'<p class="cap">{self.t(self.c.get("timeline_note"))}</p>')
        return self.section(4, "s4", "Timeline financiero, legal y de PR", body)

    def s5(self):
        body = "".join(f"<p>{self.t(p)}</p>" for p in self.c["cash_text"]) + f'<div class="read">{self.t(self.c.get("cash_read"))}</div>'
        return self.section(5, "s5", "Caja y going concern", body)

    def s6(self):
        rows = [[self.t(r[0]), self.t(r[1]), self.t(r[2]), self.st(r[3], self.t(r[4])), self.t(r[5])] for r in self.c["compliance"]]
        body = self.table(["Estándar", "Requisito", "Compañía", "Estado", "Fechas"], rows) + f'<p class="cap">{self.t(self.c.get("compliance_note"))}</p>'
        return self.section(6, "s6", "Cumplimiento bursátil", body)

    def s7(self):
        return self.section(7, "s7", "Legal y regulatorio", f'<p>{self.t(self.c.get("legal_text"))}</p>')

    def s8(self):
        return self.section(8, "s8", "Nexo China / extranjero y gobierno", "".join(f"<p>{self.t(p)}</p>" for p in self.c["governance_text"]))

    def s9(self):
        rows = [[self.t(x) for x in r] for r in self.c["ownership"]]
        body = self.table(["Titular", "Tipo", "Acciones / %", "Base", "Perfil · vendibilidad"], rows) + f'<p class="cap">{self.t(self.c.get("float_recon"))}</p>'
        return self.section(9, "s9", "Propiedad", body)

    def s10(self):
        rows = [[self.t(d), self.t(x)] for d, x in self.c["catalysts"]]
        body = self.table(["Fecha", "Evento · qué vigilar"], rows) + f'<p class="cap">{self.t(self.c.get("catalysts_note"))}</p>'
        return self.section(10, "s10", "Catalizadores y fechas clave", body)

    def s11(self):
        return self.section(11, "s11", "Catalizador de hoy", "".join(f"<p>{self.t(p)}</p>" for p in self.c["today_text"]))

    def s12(self):
        r = self.c["read"]
        ceo = "".join(f"<li>{self.t(x)}</li>" for x in r["ceo"])
        lad = "".join(f"<li><b>{fmt(p, 'px3' if round(p, 2) != p else 'px')}</b><span>{self.t(x)}</span></li>" for p, x in sorted(r["ladder"]))
        body = (f'<div class="two"><div><h3>12.1 Lente del CEO</h3><p>{self.t(r["ceo_headline"])}</p><ul class="pl">{ceo}</ul></div>'
                f'<div><h3>12.2 Lente del trader — escalera de presión de oferta</h3><ul class="lad">{lad}</ul></div></div>'
                f'<div class="read">{self.t(r["verdict"])}</div>')
        return self.section(12, "s12", "La lectura — síntesis y veredicto", body)

    def footer(self):
        items = "".join(f'<li><a href="{html.escape(u, quote=True)}">{html.escape(l)}</a></li>' for l, u in self.c["sources"])
        return (f'<footer><p><b>Fuentes</b> (abiertas para este informe):</p><ol>{items}</ol>'
                f'<p>Base cierre previo en todo el informe. Investigación interna; no es consejo de inversión. '
                f'Las marcas <span class="v">VERIFY</span> señalan datos que faltan o se contradicen entre filings. '
                f'Plantilla forensic-microcap v{self.c.get("schema_version", "1.0")}.</p></footer>')

    def rail(self):
        meta = self.c["meta"]
        names = ["Snapshot", "O/S y dilución", "Capital y oferta", "Timeline", "Caja", "Cumplimiento", "Legal",
                 "Nexo y gobierno", "Propiedad", "Catalizadores", "Hoy", "Lectura"]
        links = '<a href="#s0"><span>§0</span>Cabecera</a>' + "".join(
            f'<a href="#s{i}"><span>§{i}</span>{n}</a>' for i, n in enumerate(names, 1))
        return (f'<aside class="rail"><div><div class="tk">{meta["ticker"]}</div><div class="cik">CIK {meta["cik"]}<br>corte {meta["report_date"]}</div></div>'
                f'<nav aria-label="Secciones">{links}</nav></aside>')

    def render(self):
        css = open(os.path.join(ASSETS, "report.css"), encoding="utf-8").read()
        js = open(os.path.join(ASSETS, "charts.js"), encoding="utf-8").read()
        gate_es = {"live": "viva", "gated": "bloqueada", "price": "por precio", "issued": "emitida"}
        chart = dict(self.chart)
        chart["layers"] = [dict(L, gate=gate_es.get(L["gate"], L["gate"])) for L in chart["layers"]]
        data = json.dumps(chart, ensure_ascii=False).replace("</", "<\\/")
        meta = self.c["meta"]
        main = "".join([self.header(), self.grades(), self.s1(), self.s2(), self.s3(), self.s4(), self.s5(), self.s6(),
                        self.s7(), self.s8(), self.s9(), self.s10(), self.s11(), self.s12(), self.footer()])
        if self.missing:
            raise KeyError(f"metrics referenced but not computed: {sorted(self.missing)}")
        fonts = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..800"
                 "&family=IBM+Plex+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap")
        return (f'<title>{meta["ticker"]} Forensic File</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="stylesheet" href="{fonts}">\n'
                f'<style>\n{css}\n</style>\n<div class="shell">{self.rail()}<main>{main}</main></div>\n'
                f'<script type="application/json" id="chart-data">{data}</script>\n<script>\n{js}\n</script>\n')


def main():
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else f'{case["meta"]["ticker"]}_forensic.html'
    r = Renderer(case)
    page = r.render()
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out} ({len(page):,} bytes); VERIFY flags: {page.count('class=\"v\"')}")


if __name__ == "__main__":
    main()
