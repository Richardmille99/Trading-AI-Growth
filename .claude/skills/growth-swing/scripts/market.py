"""Market breadth for the regime (swing.md §1): % of members above their 20/50-day SMA and the Stockbee-style ratio
(days with a +4% move ÷ days with a −4% move, summed over 5 and 10 sessions).

Usage:
  python market.py --members market/members.json --out market/breadth.json [--no-download] [--days 20]

Prices are cached in market/data/<T>.csv (git-ignored: re-downloadable). breadth.json keeps the last `--days` sessions,
newest last, plus `state` of the newest one: 'strong' / 'weak' / 'mixed' (thresholds below). prices.py reads it to
adjust the trend proxy (prices.regime_proxy).
"""
import argparse, json, os, sys, time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prices import download, read_csv, write_csv  # noqa: E402

STRONG = dict(pct50=60, ratio10=1.5)   # ≥ both → strong
WEAK = dict(pct50=40, ratio10=0.67)    # below either → weak
MOVE = 0.04
MIN_MOVES = 3                          # ratio ignored with fewer ±4% moves in 10 sessions


def _ratio(up, down):
    return None if up == 0 and down == 0 else round(up / down, 2) if down else float(up)


def breadth_on(series, day):
    """Breadth for one session `day` from {ticker: rows}. Members without 50 prior sessions are left out."""
    n = a20 = a50 = 0
    for rows in series.values():
        i = next((k for k in range(len(rows) - 1, -1, -1) if rows[k]["date"] <= day), None)
        if i is None or i < 50 or rows[i]["date"] != day:
            continue
        c = [r["close"] for r in rows[i - 49:i + 1]]
        n += 1
        a20 += c[-1] > sum(c[-20:]) / 20
        a50 += c[-1] > sum(c) / 50
    return n, a20, a50


def moves(series, day):
    up = down = 0
    for rows in series.values():
        i = next((k for k, r in enumerate(rows) if r["date"] == day), None)
        if not i:
            continue
        ch = rows[i]["close"] / rows[i - 1]["close"] - 1
        up += ch >= MOVE
        down += ch <= -MOVE
    return up, down


def state(b):
    """strong / weak / mixed. The 10-session ratio only counts with at least MIN_MOVES ±4% moves (few moves = no signal)."""
    if b["pct_above_sma50"] is None:
        return "unknown"
    r10 = b["ratio_10d"] if b["up4_10d"] + b["down4_10d"] >= MIN_MOVES else None
    if b["pct_above_sma50"] >= STRONG["pct50"] and (r10 is None or r10 >= STRONG["ratio10"]):
        return "strong"
    if b["pct_above_sma50"] < WEAK["pct50"] or (r10 is not None and r10 < WEAK["ratio10"]):
        return "weak"
    return "mixed"


def breadth(series, days=20):
    """History of the last `days` sessions (dates taken from the longest member series)."""
    cal = max((rows for rows in series.values()), key=len)
    dates = [r["date"] for r in cal]
    mv = {d: moves(series, d) for d in dates[-(days + 10):]}
    out = []
    for k, d in enumerate(dates[-days:]):
        n, a20, a50 = breadth_on(series, d)
        j = dates.index(d)
        last5 = [mv[x] for x in dates[max(0, j - 4):j + 1] if x in mv]
        last10 = [mv[x] for x in dates[max(0, j - 9):j + 1] if x in mv]
        u5, d5 = sum(x[0] for x in last5), sum(x[1] for x in last5)
        u10, d10 = sum(x[0] for x in last10), sum(x[1] for x in last10)
        b = dict(date=d, n=n, pct_above_sma20=round(a20 / n * 100, 1) if n else None, pct_above_sma50=round(a50 / n * 100, 1) if n else None,
                 up4_5d=u5, down4_5d=d5, ratio_5d=_ratio(u5, d5), up4_10d=u10, down4_10d=d10, ratio_10d=_ratio(u10, d10))
        b["state"] = state(b)
        out.append(b)
    return out


def describe(b, source):
    return (f'Amplitud {source} ({b["date"]}, {b["n"]} valores): {b["pct_above_sma50"]:.0f}% sobre la SMA 50, '
            f'{b["pct_above_sma20"]:.0f}% sobre la SMA 20; +4%/−4% en 5 sesiones {b["up4_5d"]}/{b["down4_5d"]}, '
            f'en 10 sesiones {b["up4_10d"]}/{b["down4_10d"]} → {b["state"]}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", default="market/members.json")
    ap.add_argument("--out", default="market/breadth.json")
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--days", type=int, default=20)
    a = ap.parse_args()
    mem = json.load(open(a.members, encoding="utf-8"))
    cache = os.path.join(os.path.dirname(os.path.abspath(a.out)), "data")
    series, fails = {}, []
    for t in mem["tickers"]:
        p = os.path.join(cache, f"{t}.csv")
        if not a.no_download:
            try:
                _, rows = download(t)
                write_csv(p, rows)
                time.sleep(.2)
            except Exception as e:  # noqa: BLE001 — one missing member must not stop the rest
                fails.append(f"{t}: {e}")
        if os.path.exists(p):
            series[t] = read_csv(p)
    hist = breadth(series, a.days)
    res = dict(generated=date.today().isoformat(), source=mem["name"], members=len(mem["tickers"]), loaded=len(series),
               failed=fails, thresholds=dict(strong=STRONG, weak=WEAK, move=MOVE, min_moves=MIN_MOVES), latest=hist[-1], history=hist,
               evidence=describe(hist[-1], mem["name"]))
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(res["evidence"])
    if fails:
        print(f"sin precios: {fails}")


if __name__ == "__main__":
    main()
