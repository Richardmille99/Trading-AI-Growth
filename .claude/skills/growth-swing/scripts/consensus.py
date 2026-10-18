"""Analyst consensus per ticker → <universe>/data/<T>/consensus.json (history, newest last).

Usage:
  python consensus.py --universe semis/universe.json --ticker MU [MXL ...]          finviz quote page, 1 request/ticker
  python consensus.py --universe ... --ticker MU --html saved_page.html             parse a page saved by hand
  python consensus.py --universe ... --ticker MU --set eps_next_q=3.05 --set revenue_next_q=12.1e9 \\
         --source "Zacks 18-oct-2026|https://..." [--source "...|..."]               record values found by web search

Every record: date, source(s), the parsed fields and (finviz) the raw snapshot table. Parsed fields:
  eps_next_q, eps_this_y, eps_next_y (growth, %), eps_surprise_pct, sales_surprise_pct, earnings_date, earnings_session
  (amc / bmo / null), target_price, recom (1 = compra fuerte … 5 = venta), short_float_pct, inst_own_pct, insider_own_pct.
Exit code 2 when the page cannot be fetched (blocked network): use --set with two web sources instead (CLAUDE.md).
Values are as published by the source; this script never estimates a consensus.
"""
import argparse, html, json, os, re, sys, time, urllib.request
from datetime import date

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MONTHS = {m: i + 1 for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
_CELL = re.compile(r"<td[^>]*class=\"[^\"]*snapshot-td2[^\"]*\"[^>]*>(.*?)</td>", re.S | re.I)


def snapshot(page):
    """Finviz quote page → {label: value} from the snapshot table (cells alternate label, value)."""
    cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)) for c in _CELL.findall(page)]
    cells = [re.sub(r"\s+", " ", c).strip() for c in cells]
    return {cells[i]: cells[i + 1] for i in range(0, len(cells) - 1, 2) if cells[i]}


def num(v):
    if v is None:
        return None
    m = re.match(r"^\s*(-?[\d.,]+)\s*([KMBT%]?)", v)
    if not m:
        return None
    x = float(m.group(1).replace(",", ""))
    return x * {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(m.group(2), 1)


def earnings_date(v, today):
    """'Nov 03 AMC' / 'Oct 28 BMO' / 'Nov 03' → (AAAA-MM-DD, 'amc'|'bmo'|None), year nearest to `today`."""
    m = re.match(r"^\s*([A-Z][a-z]{2})\s+(\d{1,2})(?:\s+(AMC|BMO))?", v or "")
    if not m or m.group(1) not in MONTHS:
        return None, None
    t = date.fromisoformat(today)
    cands = []
    for y in (t.year - 1, t.year, t.year + 1):
        try:
            cands.append(date(y, MONTHS[m.group(1)], int(m.group(2))))
        except ValueError:
            pass
    d = min(cands, key=lambda x: abs((x - t).days))
    return d.isoformat(), (m.group(3) or "").lower() or None


def parse(snap, today):
    surpr = (snap.get("EPS/Sales Surpr.") or "").split()
    ed, sess = earnings_date(snap.get("Earnings"), today)
    return dict(eps_next_q=num(snap.get("EPS next Q")), eps_this_y=num(snap.get("EPS this Y")), eps_next_y=num(snap.get("EPS next Y")),
                eps_surprise_pct=num(surpr[0]) if len(surpr) > 0 else None, sales_surprise_pct=num(surpr[1]) if len(surpr) > 1 else None,
                earnings_date=ed, earnings_session=sess, target_price=num(snap.get("Target Price")), recom=num(snap.get("Recom")),
                short_float_pct=num(snap.get("Short Float")), inst_own_pct=num(snap.get("Inst Own")),
                insider_own_pct=num(snap.get("Insider Own")))


def fetch(ticker):
    req = urllib.request.Request(f"https://finviz.com/quote.ashx?t={ticker}&p=d",
                                 headers={"User-Agent": UA, "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _value(v):
    try:
        return float(v)
    except ValueError:
        return v


def record(path, rec):
    hist = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else dict(history=[])
    hist["history"].append(rec)
    hist["latest"] = rec
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(hist, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--ticker", nargs="+", required=True)
    ap.add_argument("--html")
    ap.add_argument("--set", action="append", default=[], metavar="campo=valor")
    ap.add_argument("--source", action="append", default=[], metavar="etiqueta|url")
    ap.add_argument("--date", default=date.today().isoformat())
    a = ap.parse_args()
    root = os.path.dirname(os.path.abspath(a.universe))
    failed = []
    for i, t in enumerate(a.ticker):
        path = os.path.join(root, "data", t, "consensus.json")
        if a.set:
            if len(a.source) < 1:
                ap.error("--set exige al menos un --source 'etiqueta|url' (CLAUDE.md: dos fuentes si vienen de búsqueda web)")
            vals = {k: _value(v) for k, v in (x.split("=", 1) for x in a.set)}
            rec = dict(date=a.date, source="manual", sources=[(x.split("|", 1) + [""])[:2] for x in a.source], **vals)
            record(path, rec)
            print(f"{t}: registrado {vals}")
            continue
        try:
            page = open(a.html, encoding="utf-8").read() if a.html else fetch(t)
        except Exception as e:  # noqa: BLE001
            failed.append(t)
            print(f"{t}: finviz no responde ({e}); usa búsqueda web y --set con fuentes")
            continue
        snap = snapshot(page)
        if not snap:
            failed.append(t)
            print(f"{t}: página sin tabla de snapshot (¿bloqueo o cambio de formato?)")
            continue
        rec = dict(date=a.date, source="finviz", sources=[[f"finviz {a.date}", f"https://finviz.com/quote.ashx?t={t}"]],
                   **parse(snap, a.date), raw=snap)
        record(path, rec)
        print(f'{t}: EPS next Q {rec["eps_next_q"]} · sorpresa BPA/ventas {rec["eps_surprise_pct"]}/{rec["sales_surprise_pct"]}% · '
              f'resultados {rec["earnings_date"]} {rec["earnings_session"] or ""}')
        if i + 1 < len(a.ticker):
            time.sleep(3)
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
