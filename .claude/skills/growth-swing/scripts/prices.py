"""Daily prices → setup metrics, RS percentiles and the cooled-leader tag (references/swing.md §1, §2, §6).

Usage:
  python prices.py --universe semis/universe.json [--etfs SMH,SOXX,QQQ,IWM] [--no-download] [--apply]

  download  2 years of daily OHLCV per ticker (status ≠ excluido) and ETF → <universe_dir>/data/<T>/prices.csv
            (stooq first, Yahoo chart API as fallback; columns date,open,high,low,close,adj_close,volume)
  metrics   ADR% 20, EMA 10/20/50, SMA 200, 52-week high and drawdown, returns 1/3/6/12 months,
            RS percentile of each return inside universe + ETFs → <universe_dir>/data/prices_metrics.json
  --apply   writes setup.rs_1m/rs_3m/rs_6m, adr_pct, ema_stack, cooled_leader, setup_candidates and
            market.price/price_date/regime into <universe_dir>/cases/<T>.json. pivot, stop and type are never
            written: candidates are proposals for the analyst (setup.notes explains the choice).

  --reaction T AAAA-MM-DD amc|bmo   prints the market-reaction fields (catalysts.md §6) for a catalyst and exits.

Returns use adjusted close; ADR, EMAs, highs and candidates use raw (split-adjusted) OHLC.
"""
import argparse, csv, io, json, os, statistics, sys, time, urllib.error, urllib.request
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HORIZONS = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}
UA_BROWSER = "Mozilla/5.0 (X11; Linux x86_64) research-script"


# ---------- download ----------
def _get(url, ua=UA_BROWSER):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def from_stooq(ticker):
    txt = _get(f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d")
    rows = list(csv.DictReader(io.StringIO(txt)))
    if not rows or "Close" not in rows[0]:
        raise ValueError("stooq sin datos")
    rows = rows[-520:]
    return [dict(date=r["Date"], open=float(r["Open"]), high=float(r["High"]), low=float(r["Low"]),
                 close=float(r["Close"]), adj_close=float(r["Close"]), volume=float(r.get("Volume") or 0)) for r in rows]


def from_yahoo(ticker):
    d = json.loads(_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=2y&interval=1d"))
    res = d["chart"]["result"][0]
    q, adj = res["indicators"]["quote"][0], res["indicators"].get("adjclose", [{}])[0].get("adjclose")
    out = []
    for i, ts in enumerate(res["timestamp"]):
        vals = [q[k][i] for k in ("open", "high", "low", "close")]
        if any(v is None for v in vals):
            continue
        day = datetime.fromtimestamp(ts + res["meta"].get("gmtoffset", 0), tz=timezone.utc).date().isoformat()
        out.append(dict(date=day, open=vals[0], high=vals[1], low=vals[2], close=vals[3],
                        adj_close=(adj[i] if adj and adj[i] is not None else vals[3]), volume=q["volume"][i] or 0))
    return out


_UNREACHABLE = set()  # sources that failed at the network level: skipped for the rest of the run


def download(ticker):
    errs = []
    for name, fn in (("stooq", from_stooq), ("yahoo", from_yahoo)):
        if name in _UNREACHABLE:
            continue
        try:
            rows = fn(ticker)
            if len(rows) >= 30:
                return name, rows
            errs.append(f"{name}: {len(rows)} filas")
        except urllib.error.URLError as e:  # blocked or down (HTTPError is a subclass: a 404 only skips this ticker)
            if not isinstance(e, urllib.error.HTTPError):
                _UNREACHABLE.add(name)
            errs.append(f"{name}: {e}")
        except Exception as e:  # format: try the next source
            errs.append(f"{name}: {e}")
    raise RuntimeError(f"{ticker}: sin precios ({'; '.join(errs)})")


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "adj_close", "volume"])
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return [dict(date=r["date"], **{k: float(r[k]) for k in ("open", "high", "low", "close", "adj_close", "volume")})
                for r in csv.DictReader(fh)]


# ---------- indicators ----------
def ema(vals, n):
    if len(vals) < n:
        return None
    k, e = 2 / (n + 1), sum(vals[:n]) / n
    for v in vals[n:]:
        e = v * k + e * (1 - k)
    return e


def sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


def adr_pct(rows, n=20):
    """Average daily range in % (Qullamaggie): mean(high / low) − 1 over n sessions."""
    if len(rows) < n:
        return None
    return (sum(r["high"] / r["low"] for r in rows[-n:]) / n - 1) * 100


def ret(rows, n):
    if len(rows) <= n:
        return None
    return rows[-1]["adj_close"] / rows[-1 - n]["adj_close"] - 1


def metrics(rows):
    c = [r["close"] for r in rows]
    hi52 = max(r["high"] for r in rows[-252:])
    e10, e20, e50 = ema(c, 10), ema(c, 20), ema(c, 50)
    s200 = sma(c, 200)
    vol50 = sma([r["volume"] for r in rows[:-1]], 50)
    return dict(
        last_date=rows[-1]["date"], close=c[-1], sessions=len(rows), adr_pct=adr_pct(rows),
        ema10=e10, ema20=e20, ema50=e50, sma200=s200,
        ema_stack=None if None in (e10, e20, e50) else bool(e10 > e20 > e50),
        high_52w=hi52, dd_52w=c[-1] / hi52 - 1, vs_sma200=None if not s200 else c[-1] / s200 - 1,
        vol50=vol50, rvol_last=rows[-1]["volume"] / vol50 if vol50 else None,
        ret={h: ret(rows, n) for h, n in HORIZONS.items()})


def percentile(v, others):
    """Share of the other members with a lower value (ties count half), 0–100."""
    vals = [o for o in others if o is not None]
    if v is None or not vals:
        return None
    return (sum(1 for o in vals if o < v) + 0.5 * sum(1 for o in vals if o == v)) / len(vals) * 100


def rs_table(M):
    """RS percentile of each horizon's return inside the whole set (universe + ETFs)."""
    out = {}
    for t in M:
        out[t] = {h: percentile(M[t]["ret"][h], [M[o]["ret"][h] for o in M if o != t]) for h in HORIZONS}
    return out


# ---------- candidates (swing.md §2) — proposals only ----------
def candidates(rows, m):
    """Mechanical screens for a few setups. Each candidate carries a proposed pivot/stop and why.
    The analyst confirms or rejects; nothing here is written to setup.type/pivot/stop."""
    out = []
    if len(rows) < 60:
        return out
    # EP: gap ≥ 10% on ≥ 3× volume in the last 10 sessions
    for i in range(len(rows) - 10, len(rows)):
        prev, r = rows[i - 1], rows[i]
        v50 = sma([x["volume"] for x in rows[:i]], 50)
        gap = r["open"] / prev["close"] - 1
        if gap >= .10 and v50 and r["volume"] >= 3 * v50:
            out.append(dict(type="ep", date=r["date"], pivot=r["high"], stop=r["low"],
                            why=f"gap {gap * 100:.1f}% con volumen {r['volume'] / v50:.1f}× la media de 50"))
    # breakout_flag / base: prior run ≥ 30% then a 10–40 session base with a narrowing range and EMA10 > EMA20
    for n in (10, 15, 20, 30, 40):
        base, before = rows[-n:], rows[-n - 63:-n]
        if len(before) < 20:
            continue
        run = max(x["high"] for x in before) / min(x["low"] for x in before) - 1
        top, bot = max(x["high"] for x in base), min(x["low"] for x in base)
        depth = 1 - bot / top
        half = n // 2
        r1 = max(x["high"] for x in base[:half]) / min(x["low"] for x in base[:half]) - 1
        r2 = max(x["high"] for x in base[half:]) / min(x["low"] for x in base[half:]) - 1
        if run >= .30 and depth <= .25 and r2 < r1 and m["ema10"] and m["ema20"] and m["ema10"] > m["ema20"] \
                and m["close"] >= top * .95:
            out.append(dict(type="breakout_flag", date=rows[-1]["date"], pivot=top, stop=min(x["low"] for x in base[half:]),
                            why=f"subida previa {run * 100:.0f}%, base de {n} sesiones con profundidad {depth * 100:.0f}% "
                                f"y rango que se estrecha ({r1 * 100:.0f}% → {r2 * 100:.0f}%)"))
            break
    # exhaustion: > 60% above EMA50 or > 5 ADR above EMA10
    if (m["ema50"] and m["close"] / m["ema50"] - 1 > .60) or (
            m["adr_pct"] and m["ema10"] and (m["close"] / m["ema10"] - 1) * 100 > 5 * m["adr_pct"]):
        out.append(dict(type="exhaustion_watch", date=rows[-1]["date"], pivot=None, stop=None,
                        why="extensión sobre la EMA 50 o > 5 ADR sobre la EMA 10"))
    return out


# ---------- cooled leader (swing.md §6) ----------
def cooled_leader(t, M, RS, universe_tickers, fund=None):
    """'cooled_leader', 'cooled_leader_broken' or None. fund = (accel_pp, fund_score) or None if no case yet."""
    r12 = [M[x]["ret"]["12m"] for x in universe_tickers if M.get(x) and M[x]["ret"]["12m"] is not None]
    mine = M[t]["ret"]["12m"]
    if mine is None or len(r12) < 3:
        return None
    price_ok = (mine > statistics.median(r12)
                and RS[t]["1m"] is not None and RS[t]["1m"] < 50 and RS[t]["3m"] is not None and RS[t]["3m"] < 50
                and -.50 <= M[t]["dd_52w"] <= -.20
                and M[t]["vs_sma200"] is not None and M[t]["vs_sma200"] >= -.10)
    if not price_ok:
        return None
    if fund is None:
        return None
    accel, score = fund
    intact = accel is not None and accel >= -3 and score is not None and score >= 45
    return "cooled_leader" if intact else "cooled_leader_broken"


# ---------- market reaction to a catalyst (catalysts.md §6) ----------
def reaction(rows, day, timing="amc"):
    """gap_pct, rvol (vs 50 prior sessions), close_in_range, day2_follow for a catalyst released on `day`.
    timing 'amc' (after the close) → next session; 'bmo' (before the open) → same session. None if not traded yet."""
    idx = next((i for i, r in enumerate(rows) if (r["date"] > day if timing == "amc" else r["date"] >= day)), None)
    if idx is None or idx == 0:
        return None
    r, prev = rows[idx], rows[idx - 1]
    v50 = sum(x["volume"] for x in rows[max(0, idx - 50):idx]) / min(50, idx)
    rng = r["high"] - r["low"]
    return dict(gap_pct=round((r["open"] / prev["close"] - 1) * 100, 2), rvol=round(r["volume"] / v50, 2) if v50 else None,
                close_in_range=round((r["close"] - r["low"]) / rng, 2) if rng else None,
                day2_follow=bool(rows[idx + 1]["close"] > r["close"]) if idx + 1 < len(rows) else None,
                dollar_volume=round(r["volume"] * r["close"]), estimate_revisions="unknown",
                reaction_date=r["date"], reaction_close_chg_pct=round((r["close"] / prev["close"] - 1) * 100, 2))


# ---------- regime proxy (swing.md §1) ----------
def regime_proxy(M, idx=("QQQ", "IWM"), breadth=None):
    """Trend proxy: both indices with close > EMA20 > EMA50 → risk_on; both below EMA50 → risk_off; else neutral.
    `breadth` (latest row of market.py's breadth.json, with 'state' and an 'evidence' text) adjusts it one step:
    risk_on with weak breadth → neutral; risk_off with strong breadth → neutral; neutral with weak breadth and
    < 30% of members over their SMA 50 → risk_off. Without breadth the evidence says so."""
    if any(i not in M or M[i]["ema50"] is None for i in idx):
        return "unknown", "Sin datos de índices."
    up = [M[i]["close"] > M[i]["ema20"] > M[i]["ema50"] for i in idx]
    down = [M[i]["close"] < M[i]["ema50"] for i in idx]
    trend = "risk_on" if all(up) else "risk_off" if all(down) else "neutral"
    ev = "; ".join(f'{i} {M[i]["close"]:.2f} vs EMA 10/20/50 {M[i]["ema10"]:.2f}/{M[i]["ema20"]:.2f}/{M[i]["ema50"]:.2f}'
                   for i in idx)
    ev = f"Proxy de tendencia ({M[idx[0]]['last_date']}): {ev} → {trend}."
    if not breadth or breadth.get("state") in (None, "unknown"):
        return trend, ev + " Sin amplitud (market.py no ejecutado o sin datos)."
    st, reg = breadth["state"], trend
    if trend == "risk_on" and st == "weak":
        reg = "neutral"
    elif trend == "risk_off" and st == "strong":
        reg = "neutral"
    elif trend == "neutral" and st == "weak" and (breadth.get("pct_above_sma50") or 100) < 30:
        reg = "risk_off"
    return reg, ev + " " + breadth.get("evidence", f"Amplitud: {st}") + (f". Régimen ajustado: {trend} → {reg}." if reg != trend else ".")


def load_breadth(path, last_date):
    """Latest breadth row from market.py if it is from the same session as the indices (else None)."""
    if not path or not os.path.exists(path):
        return None
    b = json.load(open(path, encoding="utf-8"))
    row = dict(b["latest"], evidence=b.get("evidence", ""))
    return row if row["date"] == last_date else None


def apply_to_case(case, t, M, RS, CAND, uni_tickers, regime, regime_ev, src):
    from compute import compute
    m, _, _ = compute(case)
    st = case.setdefault("setup", {})
    st.update(rs_1m=RS[t]["1m"], rs_3m=RS[t]["3m"], rs_6m=RS[t]["6m"], adr_pct=M[t]["adr_pct"], ema_stack=M[t]["ema_stack"],
              cooled_leader=cooled_leader(t, M, RS, uni_tickers, (m["accel_pp"], m["fund_score"])),
              setup_candidates=CAND[t])
    for k in ("type", "pivot", "stop", "notes"):
        st.setdefault(k, None)
    mk = case.setdefault("market", {})
    mk.update(price=M[t]["close"], price_date=M[t]["last_date"], regime=regime, regime_evidence=regime_ev)
    case["meta"]["price_basis"] = f'cierre del {M[t]["last_date"]} ({src})'
    return case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--etfs", default="SMH,SOXX,QQQ,IWM")
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--breadth", help="breadth.json de market.py (por defecto market/breadth.json junto a la carpeta del universo)")
    ap.add_argument("--reaction", nargs=3, metavar=("TICKER", "AAAA-MM-DD", "amc|bmo"),
                    help="solo imprime la reacción de mercado a un catalizador (JSON para el caso) y sale")
    a = ap.parse_args()
    if a.reaction:
        t, day, timing = a.reaction
        rows = read_csv(os.path.join(os.path.dirname(os.path.abspath(a.universe)), "data", t, "prices.csv"))
        print(json.dumps(reaction(rows, day, timing), ensure_ascii=False))
        return
    root = os.path.dirname(os.path.abspath(a.universe))
    uni = json.load(open(a.universe, encoding="utf-8"))
    tickers = [u["ticker"] for u in uni["tickers"] if u.get("status") != "excluido"]
    etfs = [e for e in a.etfs.split(",") if e]
    mpath = os.path.join(root, "data", "prices_metrics.json")
    srcs = json.load(open(mpath, encoding="utf-8")).get("sources", {}) if os.path.exists(mpath) else {}
    if not a.no_download:
        for t in tickers + etfs:
            src, rows = download(t)
            srcs[t] = src
            write_csv(os.path.join(root, "data", t, "prices.csv"), rows)
            print(f"{t}: {len(rows)} sesiones ({src}) hasta {rows[-1]['date']}")
            time.sleep(.3)
    M, CAND = {}, {}
    for t in tickers + etfs:
        p = os.path.join(root, "data", t, "prices.csv")
        if not os.path.exists(p):
            print(f"{t}: falta {p}")
            continue
        rows = read_csv(p)
        M[t] = metrics(rows)
        CAND[t] = candidates(rows, M[t])
    RS = rs_table(M)
    bpath = a.breadth or os.path.join(os.path.dirname(root), "market", "breadth.json")
    regime, regime_ev = regime_proxy(M, breadth=load_breadth(bpath, M.get("QQQ", {}).get("last_date")))
    out = dict(generated=date.today().isoformat(), universe_plus_etfs=list(M), regime=regime, regime_evidence=regime_ev,
               metrics=M, rs=RS, candidates=CAND, sources=srcs)
    json.dump(out, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for t in M:
        r12 = M[t]["ret"]["12m"]
        r12 = "   n/d" if r12 is None else f"{r12 * 100:6.1f}%"
        print(f'{t:<5} {M[t]["close"]:>9.2f} ADR {M[t]["adr_pct"] or 0:4.1f}% dd52 {M[t]["dd_52w"] * 100:6.1f}% 12m {r12} '
              f'RS1/3/6 {RS[t]["1m"] or 0:3.0f}/{RS[t]["3m"] or 0:3.0f}/{RS[t]["6m"] or 0:3.0f} '
              f'cand {[c["type"] for c in CAND[t]]}')
    print(f"régimen (proxy): {regime}")
    if a.apply:
        for t in tickers:
            p = os.path.join(root, "cases", f"{t}.json")
            if not os.path.exists(p) or t not in M:
                continue
            case = json.load(open(p, encoding="utf-8"))
            apply_to_case(case, t, M, RS, CAND, tickers, regime, regime_ev,
                          {"yahoo": "Yahoo Finance chart API", "stooq": "Stooq"}.get(srcs.get(t), "prices.csv"))
            json.dump(case, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{t}: caso actualizado (cooled_leader={case['setup']['cooled_leader']})")


if __name__ == "__main__":
    main()
