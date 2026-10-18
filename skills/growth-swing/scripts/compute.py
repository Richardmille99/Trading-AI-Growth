"""Assemble a growth-swing case: catalysts, fundamentals, quality, supply, valuation, peers, conviction.

compute(case) -> (m, R, chart)
  m      flat metrics for the {m.key:fmt} markup
  R      structured results used by render.py
  chart  data embedded for charts.js
Usage: python compute.py case.json   (prints the key results)
"""
import json, os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalysts import score_catalyst  # noqa: E402
from fundamentals import analyze, reverse_dcf  # noqa: E402

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
STEP = ["Descartar", "Baja", "Media", "Alta"]
SIZE = {"Alta": 1.0, "Media": 0.5, "Baja": 0.25, "Descartar": 0.0}
HORIZON = {"Alta": "Semanas; parciales a los 3–5 días y resto con la EMA de 10/20",
           "Media": "3–10 sesiones; parciales a los 3–5 días",
           "Baja": "Táctico, 1–3 sesiones, o pasar", "Descartar": "—"}


def load_profiles():
    return json.load(open(os.path.join(ASSETS, "sector_profiles.json"), encoding="utf-8"))


def _d(s):
    return date.fromisoformat(s)


def business_days(a, b):
    """Sessions strictly after a up to and including b (weekdays only)."""
    if b <= a:
        return 0
    n, d = 0, a
    while d < b:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


# ---------- supply (references/dilution_supply.md §3) ----------
def supply_score(case, f, today, window, price):
    sup, ctx = case.get("supply", []), case.get("supply_context", {})
    flt = ctx.get("float_shares")
    rules = []

    def rule(name, applied, delta, detail=""):
        rules.append(dict(rule=name, applied=bool(applied), delta=delta if applied else 0, detail=detail))

    atm_live = [s for s in sup if s["kind"] == "atm" and s.get("gate") == "live" and (s.get("capacity_usd") or 0) > 0]
    shelf_live = [s for s in sup if s["kind"] == "shelf" and s.get("gate") == "live"]
    rule("ATM con capacidad viva", atm_live, -25,
         ", ".join(f'{s["name"]}' for s in atm_live))
    rule("Shelf efectivo sin ATM", shelf_live and not atm_live, -10)
    runway = f["runway_m"]
    ep_recent = case.get("setup", {}).get("type") == "ep" or (ctx.get("ep_recent_days") is not None and ctx["ep_recent_days"] <= 30)
    weak_cash = (runway is not None and runway < 18) or bool(ctx.get("atm_used_last_q"))
    rule("RIESGO DE COLOCACIÓN", ep_recent and weak_cash, -20,
         "EP reciente + " + ("runway < 18 meses" if runway is not None and runway < 18 else "ATM usado el último trimestre") if ep_recent and weak_cash else "")
    lk_sh = sum(s.get("shares") or 0 for s in sup if s["kind"] == "lockup" and s.get("date")
                and today <= _d(s["date"]) <= today + timedelta(days=window))
    lk_pct = lk_sh / flt if flt else None
    rule("Lock-up en ventana > 10% del float", lk_pct is not None and lk_pct > .10, -20, "")
    rule("Lock-up en ventana 5–10% del float", lk_pct is not None and .05 <= lk_pct <= .10, -10, "")
    ins = [s for s in sup if s["kind"] == "insider" and s.get("flagged")]
    rule("Ventas de insiders marcadas", ins, -10, ", ".join(s["name"] for s in ins))
    conv = [s for s in sup if s["kind"] == "convertible" and (s.get("gate") == "live" or (
        s.get("date") and today <= _d(s["date"]) <= today + timedelta(days=window)))]
    rule("Convertibles con conversión posible en ventana", conv, -10, ", ".join(s["name"] for s in conv))
    rule("Dilución neta > 5% interanual", f["dil_yoy"] is not None and f["dil_yoy"] > .05, -10)
    rule("SBC > 20% de ingresos", f["sbc_pct"] is not None and f["sbc_pct"] > .20, -5)
    total = max(0, 100 + sum(r["delta"] for r in rules))
    label = "limpia" if total >= 75 else "vigilar" if total >= 50 else "pesada"
    live_sh = sum((s.get("shares") or 0) for s in sup if s.get("gate") == "live" and s["kind"] not in ("atm", "shelf"))
    atm_sh = sum(s["capacity_usd"] / price for s in atm_live) if price else None
    flags = ["RIESGO DE COLOCACIÓN"] if any(r["applied"] and r["rule"] == "RIESGO DE COLOCACIÓN" for r in rules) else []
    rows = []
    for s in sup:
        in_win = bool(s.get("date") and today <= _d(s["date"]) <= today + timedelta(days=window))
        rows.append(dict(s, in_window=in_win, pct_float=(s.get("shares") / flt) if flt and s.get("shares") else None,
                         vs_price=(s["price_basis"] / price - 1) if price and s.get("price_basis") else None))
    return dict(total=total, label=label, rules=rules, flags=flags, lockup_pct=lk_pct, rows=rows,
                live_shares=live_sh, atm_shares_at_px=atm_sh,
                overhang_pct=((live_sh + (atm_sh or 0)) / flt) if flt else None)


# ---------- peers (references/fundamentals.md §7) ----------
PEER_KEYS = [("rev_yoy", True), ("accel_pp", True), ("gm", True), ("rule40", True), ("ev_sales", False), ("rs_3m", True)]


def _pct(v, others, higher_better=True):
    vals = [o for o in others if o is not None]
    if v is None or not vals:
        return None
    below = sum(1 for o in vals if (o < v if higher_better else o > v))
    ties = sum(1 for o in vals if o == v)
    return (below + 0.5 * ties) / len(vals) * 100


def peers_table(subject, peers):
    rows = [dict(subject, subject=True)] + [dict(p, subject=False) for p in peers]
    for i, r in enumerate(rows):
        others = rows[:i] + rows[i + 1:]
        r["pct"] = {k: _pct(r.get(k), [o.get(k) for o in others], hb) for k, hb in PEER_KEYS}
        fp = [r["pct"][k] for k in ("rev_yoy", "accel_pp", "gm", "rule40") if r["pct"][k] is not None]
        r["fund_pct"] = sum(fp) / len(fp) if fp else None
        r["rs_pct"] = r["pct"]["rs_3m"]
        g = r.get("rev_yoy")
        r["ev_sales_g"] = r["ev_sales"] / (g * 100) if r.get("ev_sales") and g and g > 0 else None
    for i, r in enumerate(rows):
        others = rows[:i] + rows[i + 1:]
        r["value_pct"] = _pct(r["ev_sales_g"], [o["ev_sales_g"] for o in others], higher_better=False)
    s = rows[0]
    if len(peers) < 3 or s["fund_pct"] is None or s["rs_pct"] is None:
        pos = "unknown"
    elif s["fund_pct"] >= 80 and s["rs_pct"] >= 80:
        pos = "leader"
    elif s["fund_pct"] >= 60 and s["rs_pct"] >= 60:
        pos = "strong"
    elif s["fund_pct"] < 40 or s["rs_pct"] < 40:
        pos = "weak"
    else:
        pos = "neutral"
    rows.sort(key=lambda r: -(r["fund_pct"] if r["fund_pct"] is not None else -1))
    return rows, pos


# ---------- conviction (references/swing.md §3) ----------
def conviction(cat, fund, supply, group, regime, earnings_soon, setup_type):
    trace = []
    fv = fund if fund is not None else -1
    discard = []
    if supply < 35: discard.append(f"oferta {supply:.0f} < 35")
    if cat == "D" and fv < 40: discard.append("catalizador D con fundamentales < 40")
    if earnings_soon and setup_type != "ep": discard.append("resultados en ≤ 3 sesiones sin ser EP")
    if discard:
        return "Descartar", ["Descartar: " + "; ".join(discard)]
    alta_fail = [x for ok, x in [(cat in ("A", "B"), f"catalizador {cat} (pide A/B)"),
                                  (fv >= 65, f"fundamentales {max(fv, 0):.0f} < 65"),
                                  (supply >= 60, f"oferta {supply:.0f} < 60"),
                                  (group in ("leader", "strong"), f"grupo {group} (pide líder/fuerte)")] if not ok]
    media_fail = [x for ok, x in [(cat in ("A", "B", "C"), f"catalizador {cat} (pide ≥ C)"),
                                   (fv >= 45, f"fundamentales {max(fv, 0):.0f} < 45"),
                                   (supply >= 50, f"oferta {supply:.0f} < 50")] if not ok]
    if not alta_fail:
        level = "Alta"; trace.append("Alta: catalizador A/B, fundamentales ≥ 65, oferta ≥ 60, grupo líder/fuerte")
    elif not media_fail:
        level = "Media"; trace.append("Media: catalizador ≥ C, fundamentales ≥ 45, oferta ≥ 50")
        trace.append("no llega a Alta: " + "; ".join(alta_fail))
    else:
        level = "Baja"; trace.append("Baja: no llega a Media: " + "; ".join(media_fail))
    if regime == "risk_off" and STEP.index(level) > 1:
        level = "Baja"; trace.append("régimen risk_off → máximo Baja")
    if level == "Alta" and (regime == "unknown" or group == "unknown"):
        level = "Media"; trace.append("régimen o grupo desconocido → baja un escalón")
    return level, trace


def compute(case):
    profiles = load_profiles()
    meta, mk = case["meta"], case.get("market", {})
    today = _d(meta["report_date"])
    window = case.get("supply_context", {}).get("window_days", 56)
    price = mk.get("price")
    fin = case["financials"]
    FA = analyze(fin["quarters"], meta.get("profile", "generic"), profiles, case.get("manual", {}))
    f = FA["metrics"]
    m = {k: v for k, v in f.items() if not isinstance(v, str)}
    m["fund_score"] = FA["score"]["total"]
    for k, v in FA["score"]["components"].items():
        m["fs_" + k] = v
    m["flags_on"] = sum(1 for x in FA["flags"] if x["on"])

    # catalysts
    cats = []
    for c in case.get("catalysts", []):
        r = score_catalyst(c, f["revenue_ttm"])
        r.update(date=c.get("date"), headline=c.get("headline"), binding=c.get("binding"), src=c.get("sources", []),
                 value_firm=c.get("value_firm"), value_ceiling=c.get("value_ceiling"), counterparty=c.get("counterparty"),
                 note=c.get("note"))
        cats.append(r)
        m[f'cat_{r["id"]}_score'] = r["score"]
        m[f'cat_{r["id"]}_mat'] = r["materiality_ratio"]
        m[f'cat_{r["id"]}_mkt'] = r["market"]
    pid = meta.get("primary_catalyst")
    primary = next((c for c in cats if c["id"] == pid), None) or (max(cats, key=lambda c: c["score"]) if cats else None)

    # valuation
    so = fin.get("shares_out")
    mcap = price * so if price and so else None
    ev = None if mcap is None or f["net_cash"] is None else mcap - f["net_cash"]
    m.update(price=price, shares_out=so, mcap=mcap, ev=ev,
             ev_sales=ev / f["revenue_ttm"] if ev and f["revenue_ttm"] else None,
             ev_gp=ev / f["gross_profit_ttm"] if ev and f["gross_profit_ttm"] and f["gross_profit_ttm"] > 0 else None)
    m["ev_sales_g"] = m["ev_sales"] / (f["rev_yoy"] * 100) if m["ev_sales"] and f["rev_yoy"] and f["rev_yoy"] > 0 else None
    tgt = FA["profile"]["fcf_target"]
    m["fcf_target"] = tgt
    m["implied_g"] = reverse_dcf(ev, f["revenue_ttm"], f["fcfm_ttm"], tgt)
    m["implied_vs_now_pp"] = None if m["implied_g"] is None or f["rev_ttm_yoy"] is None else (m["implied_g"] - f["rev_ttm_yoy"]) * 100

    # supply
    S = supply_score(case, f, today, window, price)
    m.update(supply_score=S["total"], lockup_pct=S["lockup_pct"], overhang_pct=S["overhang_pct"],
             float_shares=case.get("supply_context", {}).get("float_shares"))

    # peers
    st = case.get("setup", {})
    subject = dict(ticker=meta["ticker"], name=meta["issuer"], rev_yoy=f["rev_yoy"], accel_pp=f["accel_pp"],
                   gm=f["gm_ttm"], rule40=f["rule40"], ev_sales=m["ev_sales"], rs_3m=st.get("rs_3m"))
    P, group = peers_table(subject, case.get("peers", []))
    s_row = next(r for r in P if r["subject"])
    m.update(fund_pct=s_row["fund_pct"], rs_pct=s_row["rs_pct"], value_pct=s_row["value_pct"], n_peers=len(P) - 1)

    # setup and risk
    piv, stp, adr = st.get("pivot"), st.get("stop"), st.get("adr_pct")
    m["risk_ps"] = piv - stp if piv and stp else None
    m["risk_pct"] = m["risk_ps"] / piv if m["risk_ps"] else None
    m["risk_adr"] = m["risk_pct"] / (adr / 100) if m["risk_pct"] and adr else None
    m["pivot"], m["stop"], m["adr_pct"] = piv, stp, adr
    m["ext_pivot"] = price / piv - 1 if price and piv else None

    # events
    evs = []
    earnings_soon = False
    for e in sorted(case.get("events", []), key=lambda x: x["date"]):
        d = _d(e["date"])
        bd = business_days(today, d)
        in_win = today <= d <= today + timedelta(days=window)
        if e.get("kind") == "earnings" and d >= today and bd <= 3:
            earnings_soon = True
        evs.append(dict(e, in_window=in_win, sessions=bd if d >= today else None))

    regime = mk.get("regime", "unknown")
    cat_grade = primary["grade"] if primary else "D"
    level, trace = conviction(cat_grade, m["fund_score"], S["total"], group, regime, earnings_soon, st.get("type"))
    m.update(size_r=SIZE[level], cat_score=primary["score"] if primary else None)

    R = dict(fund=FA, catalysts=cats, primary=primary, supply=S, peers=P, group=group, events=evs,
             regime=regime, earnings_soon=earnings_soon, conviction=level, trace=trace, horizon=HORIZON[level],
             window=window)
    chart = dict(series=FA["series"],
                 peers=[dict(t=r["ticker"], x=r.get("rev_yoy"), y=r.get("ev_sales"), s=r["subject"]) for r in P
                        if r.get("rev_yoy") is not None and r.get("ev_sales") is not None],
                 supply=[dict(name=r["name"], px=r["price_basis"], sh=r.get("shares"), gate=r.get("gate"))
                         for r in S["rows"] if r.get("price_basis")], price=price)
    return m, R, chart


if __name__ == "__main__":
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    m, R, _ = compute(case)
    p = R["primary"]
    print(f'fundamentales {m["fund_score"]:.0f} ({R["fund"]["score"]["label"]}) · banderas {m["flags_on"]}')
    print(f'catalizador principal {p["id"]}: {p["score"]} {p["grade"]} {p["verdict"]}')
    print(f'oferta {R["supply"]["total"]} ({R["supply"]["label"]}) · grupo {R["group"]} · régimen {R["regime"]}')
    print(f'convicción {R["conviction"]} ({m["size_r"]} R) · {R["trace"]}')
    print(f'EV/ventas {m["ev_sales"]} · DCF inverso {m["implied_g"]}')
