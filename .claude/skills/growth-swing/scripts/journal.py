"""Calibration journal (swing.md §4): add today's signals and fill outcomes at +5/+20/+60 sessions.

Usage:
  python journal.py --universe semis/universe.json --add [--min Media] [--date AAAA-MM-DD]
  python journal.py --universe semis/universe.json --update

--add     one row per case with conviction ≥ --min (Alta > Media > Baja) and a setup chosen by the analyst
          (setup.type with pivot and stop). Same ticker + setup + pivot already open → not added again.
--update  for each row with a pivot and stop: the trade triggers on the first session after `fecha` (within 5 sessions)
          whose high reaches the pivot; entry = max(open, pivot); R = entry − stop. Over 5/20/60 sessions from the entry
          (inclusive): MFE = (max high − entry) / R, MAE = (min low − entry) / R, close = (close − entry) / R.
          `salida` records 'no activada' or the first session whose low touched the stop ('stop AAAA-MM-DD').
          Windows without enough sessions stay empty and are filled by a later run.
Prices come from <universe>/data/<T>/prices.csv (run prices.py first).
"""
import argparse, csv, json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute import compute  # noqa: E402
from prices import read_csv  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "journal_template.csv")
LEVEL = {"Descartar": 0, "Baja": 1, "Media": 2, "Alta": 3}
WINDOWS = (5, 20, 60)
TRIGGER_WITHIN = 5


def header():
    return open(TEMPLATE, encoding="utf-8").readline().strip().split(",")


def read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path, rows):
    cols = header()
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def _f(v):
    return "" if v is None else f"{v:.2f}" if isinstance(v, float) else str(v)


def signal_row(case, day):
    m, R, _ = compute(case)
    st, p = case.get("setup") or {}, R["primary"] or {}
    return dict(fecha=day, ticker=case["meta"]["ticker"], setup=st.get("type") or "", catalizador_id=p.get("id", ""),
                catalizador_tipo=p.get("type", ""), nota_catalizador=p.get("grade", ""), score_catalizador=_f(p.get("score")),
                confirmacion_mercado=_f(p.get("market")), nota_fundamentales=_f(m.get("fund_score")), nota_oferta=_f(R["supply"]["total"]),
                grupo=R["group"], conviccion=R["conviction"], tamano_R=_f(m.get("size_r")),
                pivote=_f(st.get("pivot")), stop=_f(st.get("stop")), riesgo_adr=_f(m.get("risk_adr")), salida="", notas="")


def outcome(prices, fecha, pivot, stop):
    """{'salida', 'mfe_5d_R', …} for one signal (see module doc). Empty dict if it has not had a chance to trigger yet."""
    after = [r for r in prices if r["date"] > fecha]
    if not after:
        return {}
    k = next((i for i, r in enumerate(after[:TRIGGER_WITHIN]) if r["high"] >= pivot), None)
    if k is None:
        return dict(salida="no activada") if len(after) >= TRIGGER_WITHIN else {}
    entry = max(after[k]["open"], pivot)
    risk = entry - stop
    if risk <= 0:
        return dict(salida="stop ≥ entrada")
    path = after[k:]
    out = {}
    for n in WINDOWS:
        if len(path) < n:
            continue
        w = path[:n]
        out[f"mfe_{n}d_R"] = round((max(r["high"] for r in w) - entry) / risk, 2)
        out[f"mae_{n}d_R"] = round((min(r["low"] for r in w) - entry) / risk, 2)
        out[f"cierre_{n}d_R"] = round((w[-1]["close"] - entry) / risk, 2)
    hit = next((r["date"] for r in path if r["low"] <= stop), None)
    out["salida"] = f"stop {hit}" if hit else f"activada {after[k]['date']} a {entry:.2f}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--min", default="Media", choices=("Baja", "Media", "Alta"))
    ap.add_argument("--date", default=date.today().isoformat())
    a = ap.parse_args()
    root = os.path.dirname(os.path.abspath(a.universe))
    path = os.path.join(root, "journal.csv")
    rows = read(path)
    if a.add:
        uni = json.load(open(a.universe, encoding="utf-8"))
        for u in uni["tickers"]:
            cp = os.path.join(root, "cases", f'{u["ticker"]}.json')
            if u.get("status") == "excluido" or not os.path.exists(cp):
                continue
            case = json.load(open(cp, encoding="utf-8"))
            st = case.get("setup") or {}
            if not (st.get("type") and st.get("pivot") and st.get("stop")):
                continue
            r = signal_row(case, a.date)
            if LEVEL[r["conviccion"]] < LEVEL[a.min]:
                continue
            if any(x["ticker"] == r["ticker"] and x["setup"] == r["setup"] and x["pivote"] == r["pivote"] and
                   not x.get("cierre_60d_R") for x in rows):
                continue
            rows.append(r)
            print(f'+ {r["ticker"]} {r["setup"]} pivote {r["pivote"]} stop {r["stop"]} · {r["conviccion"]}')
    if a.update:
        cache = {}
        for r in rows:
            if not (r.get("pivote") and r.get("stop")) or r.get("cierre_60d_R") or r.get("salida") == "no activada":
                continue
            t = r["ticker"]
            if t not in cache:
                p = os.path.join(root, "data", t, "prices.csv")
                cache[t] = read_csv(p) if os.path.exists(p) else []
            res = outcome(cache[t], r["fecha"], float(r["pivote"]), float(r["stop"]))
            for k, v in res.items():
                r[k] = _f(v) if not isinstance(v, str) else v
            if res:
                print(f'~ {t} {r["fecha"]}: {res}')
    write(path, rows)
    print(f"{path}: {len(rows)} filas")


if __name__ == "__main__":
    main()
