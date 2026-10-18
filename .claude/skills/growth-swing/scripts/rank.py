"""Rank a universe of growth-swing cases.

Usage:
  python rank.py <cases_dir> [--universe universe.json] [--sync-peers] [--out-dir DIR]

--sync-peers  rewrites each case's `peers` with the other cases of the universe (same method, same date),
              so percentiles and group position are computed inside the universe. Run it before ranking.
Outputs ranking.csv and ranking.html in --out-dir (default: parent of cases_dir).

Order: conviction first (Alta > Media > Baja > Descartar), then the "negocio" score:
  negocio = 0.45·fundamentales + 0.20·catalizador + 0.20·oferta + 0.15·valor relativo
  catalizador = best score among business catalysts (contracts, partnerships, products, earnings, M&A) dated
                within 120 days before report_date; financing never counts; none → 50 (marked).
  valor relativo = percentile of EV/sales ÷ growth inside the universe; missing → 50 (marked).
"""
import argparse, csv, glob, html, json, os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute import compute, STEP  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
BUSINESS = {"gov_contract", "commercial_contract", "partnership", "product", "earnings", "mna"}
WEIGHTS = {"fund": .45, "cat": .20, "supply": .20, "value": .15}


def load(cases_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(cases_dir, "*.json"))):
        c = json.load(open(p, encoding="utf-8"))
        out[c["meta"]["ticker"]] = (p, c)
    return out


def subject_row(case):
    m, R, _ = compute(case)
    target = R["fund"]["profile"]["gm_target"]
    return dict(ticker=case["meta"]["ticker"], name=case["meta"]["issuer"], rev_yoy=m["rev_yoy"], accel_pp=m["accel_pp"],
                gm=m["gm_ttm"], gm_rel=None if m["gm_ttm"] is None else m["gm_ttm"] - target,
                rule40=m["rule40"], ev_sales=m["ev_sales"], rs_3m=case.get("setup", {}).get("rs_3m"))


def sync_peers(cases):
    rows = {t: subject_row(c) for t, (_, c) in cases.items()}
    for t, (p, c) in cases.items():
        c["peers"] = [rows[o] for o in sorted(rows) if o != t]
        json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def cat_component(R, report_date):
    lo = report_date - timedelta(days=120)
    best = None
    for k in R["catalysts"]:
        if k["type"] in BUSINESS and k.get("date") and lo <= date.fromisoformat(k["date"]) <= report_date:
            if best is None or k["score"] > best["score"]:
                best = k
    return best


def rank(cases, universe):
    uni = {u["ticker"]: u for u in (universe or {}).get("tickers", [])}
    rows = []
    for t, (_, c) in cases.items():
        m, R, _ = compute(c)
        rd = date.fromisoformat(c["meta"]["report_date"])
        best = cat_component(R, rd)
        parts = dict(fund=m["fund_score"], cat=best["score"] if best else None, supply=R["supply"]["total"], value=m["value_pct"])
        marks = [k for k, v in parts.items() if v is None]
        negocio = sum(WEIGHTS[k] * (50 if v is None else v) for k, v in parts.items())
        nxt = next((e for e in R["events"] if e.get("kind") == "earnings" and e["sessions"] is not None), None)
        u = uni.get(t, {})
        rows.append(dict(
            ticker=t, name=c["meta"]["issuer"], subgroup=u.get("subgroup", c["meta"].get("group", "")),
            purity=u.get("purity", ""), conviction=R["conviction"], negocio=negocio, missing=",".join(marks),
            fund=m["fund_score"], rev_yoy=m["rev_yoy"], accel_pp=m["accel_pp"], flags=m["flags_on"],
            cat=(f'{best["grade"]} {best["score"]} ({best["id"]})' if best else ""), supply=R["supply"]["total"],
            value_pct=m["value_pct"], ev_sales=m["ev_sales"], group=R["group"],
            cooled=c.get("setup", {}).get("cooled_leader") or "", earnings=(f'{nxt["date"]} · {nxt["sessions"]} ses.' if nxt else ""),
            report=f'reports/{t}_swing.html', trace=" | ".join(R["trace"])))
    rows.sort(key=lambda r: (-STEP.index(r["conviction"]), -r["negocio"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def _f(v, kind):
    if v is None or v == "":
        return "n/d"
    if kind == "pct":
        return f"{v * 100:.1f}%".replace(".", ",")
    if kind == "pp":
        return (f"{v:+.1f} pp").replace(".", ",")
    if kind == "x":
        return f"{v:.1f}×".replace(".", ",")
    return f"{v:.0f}"


def write(rows, out_dir, title):
    os.makedirs(out_dir, exist_ok=True)
    keys = ["rank", "ticker", "name", "subgroup", "purity", "conviction", "negocio", "fund", "rev_yoy", "accel_pp", "flags",
            "cat", "supply", "value_pct", "ev_sales", "group", "cooled", "earnings", "missing", "trace", "report"]
    with open(os.path.join(out_dir, "ranking.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows({k: r[k] for k in keys} for r in rows)
    css = open(os.path.join(ASSETS, "report.css"), encoding="utf-8").read()
    lvl = {"Alta": "g", "Media": "a", "Baja": "x", "Descartar": "r"}
    body = []
    for r in rows:
        body.append("<tr>" + "".join([
            f'<td class="n">{r["rank"]}</td>',
            f'<td><a href="{html.escape(r["report"])}"><b>{r["ticker"]}</b></a><br><span class="lede">{html.escape(r["subgroup"])}</span></td>',
            f'<td>{html.escape(r["purity"])}</td>',
            f'<td><span class="st {lvl[r["conviction"]]}">{r["conviction"]}</span></td>',
            f'<td class="n"><b>{_f(r["negocio"], "n")}</b>{" *" if r["missing"] else ""}</td>',
            f'<td class="n">{_f(r["fund"], "n")}</td>',
            f'<td class="n">{_f(r["rev_yoy"], "pct")}</td>',
            f'<td class="n">{_f(r["accel_pp"], "pp")}</td>',
            f'<td class="n">{r["flags"]}</td>',
            f'<td>{html.escape(r["cat"]) or "—"}</td>',
            f'<td class="n">{r["supply"]}</td>',
            f'<td class="n">{_f(r["value_pct"], "n")}</td>',
            f'<td class="n">{_f(r["ev_sales"], "x")}</td>',
            f'<td>{html.escape(str(r["cooled"])) or "—"}</td>',
            f'<td>{html.escape(r["earnings"]) or "—"}</td>']) + "</tr>")
    head = ["#", "Ticker", "Pureza", "Convicción", "Negocio", "Fund.", "Crec.", "Acel.", "Banderas", "Catalizador",
            "Oferta", "P. valor", "EV/ventas", "Líder enfriado", "Resultados"]
    num = {0, 4, 5, 6, 7, 8, 10, 11, 12}
    th = "".join(f'<th class="n">{h}</th>' if i in num else f"<th>{h}</th>" for i, h in enumerate(head))
    page = ('<!doctype html>\n<html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{html.escape(title)}</title>\n<style>\n{css}\n</style>\n<main class=\"wrap\">"
            f'<header class="case"><h1>{html.escape(title)}</h1><p class="desc">Orden: convicción y, dentro de cada nivel, '
            f'nota de negocio = 0,45·fundamentales + 0,20·catalizador (≤ 120 días) + 0,20·oferta + 0,15·valor relativo. '
            f'* = componente sin dato, puntuado 50.</p></header>'
            f'<section><div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div></section></main>')
    open(os.path.join(out_dir, "ranking.html"), "w", encoding="utf-8").write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases_dir")
    ap.add_argument("--universe")
    ap.add_argument("--sync-peers", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--title", default="Ranking del universo")
    a = ap.parse_args()
    cases = load(a.cases_dir)
    if a.sync_peers:
        sync_peers(cases)
        cases = load(a.cases_dir)
    uni = json.load(open(a.universe, encoding="utf-8")) if a.universe else None
    rows = rank(cases, uni)
    out = a.out_dir or os.path.dirname(os.path.abspath(a.cases_dir.rstrip("/")))
    write(rows, out, a.title)
    for r in rows:
        print(f'{r["rank"]:>2} {r["ticker"]:<7} {r["conviction"]:<9} negocio {r["negocio"]:5.1f} {r["missing"]}')


if __name__ == "__main__":
    main()
