"""One local page for every universe: its ranking table and resumen.md.

Usage:
  python sitepage.py --universes universes.json --out site [--title "Research · growth-swing"]

universes.json: {"universes": [{"dir": "semis", "name": "Semis y adyacentes de IA"}, ...]}
Writes <out>/index.html and copies each <dir>/reports/*.html to <out>/<dir>/reports/ so the links work offline and the
folder can be published as is. Nothing is computed here: the ranking table is the one rank.py wrote and the text is resumen.md.
"""
import argparse, html, json, os, re, shutil, sys

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def markdown(md, shift=1):
    """Small Markdown subset used by resumen.md: headings, paragraphs, '-' lists, pipe tables, bold, code, links."""
    out, para, lst, tbl = [], [], [], []

    def flush():
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()
        if lst:
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in lst) + "</ul>")
            lst.clear()
        if tbl:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tbl if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
            if rows:
                head = "".join(f"<th>{_inline(c)}</th>" for c in rows[0])
                body = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
                out.append(f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            tbl.clear()

    for line in md.splitlines():
        s = line.rstrip()
        m = re.match(r"^(#{1,6})\s+(.*)", s)
        if m:
            flush()
            n = min(6, len(m.group(1)) + shift)
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif s.lstrip().startswith("|"):
            if para or lst:
                t = list(tbl)
                tbl.clear()
                flush()
                tbl.extend(t)
            tbl.append(s)
        elif re.match(r"^\s*[-*]\s+", s):
            if para or tbl:
                flush()
            lst.append(re.sub(r"^\s*[-*]\s+", "", s))
        elif not s.strip():
            flush()
        elif lst and line.startswith("  "):
            lst[-1] += " " + s.strip()
        else:
            if lst or tbl:
                flush()
            para.append(s.strip())
    flush()
    return "\n".join(out)


def ranking_table(path, prefix):
    """The <table> rank.py wrote, with report links pointing into <prefix>/reports/."""
    if not os.path.exists(path):
        return "<p>Sin ranking todavía (ejecuta rank.py).</p>"
    page = open(path, encoding="utf-8").read()
    m = re.search(r'<div class="tw">.*?</div>', page, re.S)
    return m.group(0).replace('href="reports/', f'href="{prefix}/reports/') if m else ""


def build(universes_path, out, title):
    root = os.path.dirname(os.path.abspath(universes_path))
    unis = json.load(open(universes_path, encoding="utf-8"))["universes"]
    css = open(os.path.join(ASSETS, "report.css"), encoding="utf-8").read()
    os.makedirs(out, exist_ok=True)
    nav, secs = [], []
    for u in unis:
        d = os.path.join(root, u["dir"])
        if not os.path.isdir(d):
            continue
        rep = os.path.join(d, "reports")
        if os.path.isdir(rep):
            dst = os.path.join(out, u["dir"], "reports")
            os.makedirs(dst, exist_ok=True)
            for f in os.listdir(rep):
                if f.endswith(".html"):
                    shutil.copy2(os.path.join(rep, f), os.path.join(dst, f))
        res = os.path.join(d, "resumen.md")
        md = open(res, encoding="utf-8").read() if os.path.exists(res) else ""
        head = re.match(r"#\s+(.*)\n", md)
        sub = f'<p class="lede">{html.escape(head.group(1))}</p>' if head else ""
        text = markdown(md[head.end():] if head else md) if md else "<p>Sin resumen todavía.</p>"
        anchor = re.sub(r"\W+", "-", u["dir"]).strip("-")
        nav.append(f'<a href="#{anchor}">{html.escape(u["name"])}</a>')
        secs.append(f'<section id="{anchor}"><h2>{html.escape(u["name"])}</h2>'
                    f'{sub}<h3>Ranking</h3>{ranking_table(os.path.join(d, "ranking.html"), u["dir"])}{text}</section>')
    page = (f"<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{html.escape(title)}</title>\n<style>\n{css}\n.unav{{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 16px}}</style></head><body>"
            f'<main class="wrap"><header class="case"><h1>{html.escape(title)}</h1><p class="desc">Investigación interna, no es consejo de '
            f'inversión. Cada cifra sale de los casos y de rank.py; cada dossier lleva sus fuentes.</p>'
            f'<nav class="unav">{" · ".join(nav)}</nav></header>'
            f"{''.join(secs)}</main></body></html>")
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    return os.path.join(out, "index.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universes", default="universes.json")
    ap.add_argument("--out", default="site")
    ap.add_argument("--title", default="Research · growth-swing")
    a = ap.parse_args()
    print("wrote", build(a.universes, a.out, a.title))


if __name__ == "__main__":
    sys.exit(main())
