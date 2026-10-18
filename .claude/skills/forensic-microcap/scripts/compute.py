"""Forensic micro-cap engine: deterministic metrics from a case JSON.

Usage:  python compute.py case.json            -> prints metrics
        from compute import compute; m, chart = compute(case)

Every number the report prints should come from here or from the case file,
never from mental arithmetic. Supply models:
  fixed            shares_max (and shares_min for a band) regardless of price
  shelf_ib5        Form F-3 I.B.5 baby shelf: 1/3 public float valued at max(p, 60-day high), in shares at p
  dollars_discount dollars / (discount * max(p, floor)), capped by cap_price and max_shares (ELOC, floor notes)
  cashless_bs      Black-Scholes cashless warrant (underlying = strike, r = 0): warrants * BS / max(p, floor)
"""
import json, math, statistics as st, sys
from datetime import date


def _d(s):
    y, m, dd = map(int, s.split("-"))
    return date(y, m, dd)


def bs_call_at_strike(k, vol, term):
    """BS call with S = K, r = 0: K * (2N(d1) - 1), d1 = vol*sqrt(T)/2."""
    d1 = vol * math.sqrt(term) / 2
    n = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    return k * (2 * n - 1)


def shares_at(inst, p, case, band="max"):
    sup = inst.get("supply", {"model": "fixed"})
    model = sup.get("model", "fixed")
    if model == "fixed":
        if band == "min" and "shares_min" in inst:
            return inst["shares_min"]
        return inst.get("shares_max", 0)
    if model == "shelf_ib5":
        non = sup.get("non_affiliates", case["shares"]["non_affiliates"])
        h = sup.get("high60", case["market"]["high60"])
        return non * max(p, h) / 3 / p
    if model == "dollars_discount":
        paid = sup["discount"] * max(p, sup.get("floor", 0))
        if sup.get("cap_price"):
            paid = min(paid, sup["cap_price"])
        sh = sup["dollars"] / paid
        if sup.get("max_shares"):
            sh = min(sh, sup["max_shares"])
        return sh
    if model == "cashless_bs":
        k = sup["strike"]
        if p >= k:
            return sup["warrants"] * (p - k) / p
        bsv = bs_call_at_strike(k, sup.get("vol", 1.75), sup.get("term", 5))
        return sup["warrants"] * bsv / max(p, sup.get("floor", 0))
    raise ValueError(f"unknown supply model {model}")


def compute(case):
    mk, sh, fin = case["market"], case["shares"], case["financials"]
    P = mk["prev_close"]
    os_ = sh["os_primary"]
    non = sh["non_affiliates"]
    B = (sh.get("class_b") or {}).get("shares", 0)
    vpsB = (sh.get("class_b") or {}).get("votes_per_share", 1)
    m = {}
    m.update(prev_close=P, prev_close_date=mk["prev_close_date"], change_pct=mk.get("change_pct"),
             volume=mk.get("volume"), high60=mk.get("high60"), os=os_, non_aff=non,
             affiliates=os_ - non, classB=B, report_date=case["meta"]["report_date"])
    cum = 1
    for s in sh.get("splits", []):
        cum *= s["ratio"]
    m["cum_split"] = cum
    m["raw_equiv"] = os_ * cum
    m["mcap_A"] = os_ * P
    m["mcap_AB"] = (os_ + B) * P
    m["voteshare_B"] = 100 * B * vpsB / (B * vpsB + os_) if B else 0
    if sh.get("authorized_A"):
        m["headroom_A"] = sh["authorized_A"] - os_
        m["headroom_x"] = m["headroom_A"] / os_
    if sh.get("reference_os"):
        m["growth_ref"] = m["growth_ref_x"] = os_ / sh["reference_os"]["shares"]
    if sh.get("ipo_os"):
        m["growth_ipo"] = os_ / sh["ipo_os"]
    if sh.get("os_at_financials"):
        m["since_fin"] = os_ - sh["os_at_financials"]
        m["since_fin_pct"] = 100 * m["since_fin"] / sh["os_at_financials"]

    # volume
    vols = [r[2] for r in mk.get("daily", [])]
    if vols:
        m["adv_mean"] = st.mean(vols)
        m["adv_median"] = st.median(vols)
        big = max(mk["daily"], key=lambda r: r[2])
        m["largest_vol"], m["largest_date"] = big[2], big[0]
        m["largest_turnover"] = big[2] / non

    # instruments
    live_lo = live_hi = gated = fd_add = 0
    for i in case.get("instruments", []):
        iid = i["id"]
        hi = shares_at(i, P, case, "max")
        lo = shares_at(i, P, case, "min")
        m[f"{iid}_max"], m[f"{iid}_min"], m[f"{iid}_now"] = hi, lo, hi
        m[f"{iid}_pct_os"] = 100 * hi / os_
        m[f"{iid}_pct_float"] = 100 * hi / non
        if i.get("basis"):
            m[f"{iid}_pnl"] = 100 * (P / i["basis"] - 1)
        if i.get("discount"):
            m[f"{iid}_px"] = i["discount"] * P
            m[f"{iid}_proceeds"] = hi * i["discount"] * P
        if i["gate"] == "live":
            live_lo += lo; live_hi += hi
        elif i.get("supply", {}).get("model") != "shelf_ib5":
            gated += hi
        if i.get("fd"):
            fd_add += hi
    m.update(printable_lo=live_lo, printable_hi=live_hi, gated_total=gated,
             gated_xfloat=gated / non, fd=os_ + fd_add)
    m["fd_xos"], m["fd_xfloat"] = m["fd"] / os_, m["fd"] / non
    for k in ("lo", "hi"):
        v = m[f"printable_{k}"]
        m[f"printable_{k}_xos"] = v / os_
        m[f"printable_{k}_xfloat"] = v / non
        if vols:
            m[f"printable_{k}_xadv"] = v / m["adv_median"]

    # shelf (I.B.5) if present
    h60 = mk.get("high60", P)
    m["shelf_cap_now"] = non * P / 3
    m["shelf_cap_high"] = non * max(P, h60) / 3
    m["shelf_sh_now"] = non * max(P, h60) / 3 / P
    m["shelf_sh_floor"] = non / 3
    m["ib1_px"] = 75_000_000 / non

    # cash
    m["cash"] = fin["cash"]; m["equity"] = fin["equity"]
    m["cash_ps"] = fin["cash"] / os_
    burn_cash = -fin["opcf"]["value"] / fin["opcf"]["months"]
    pw = fin["pre_wc_burn"]
    burn_pre = (pw["loss"] - pw["noncash"]) / pw["months"]
    months = (_d(case["meta"]["report_date"]) - _d(fin["as_of"])).days / 30.44
    m.update(burn_cash=burn_cash, burn_prewc=burn_pre, months_elapsed=months,
             cash_pf_hi=fin["cash"] - months * min(burn_cash, burn_pre),
             cash_pf_lo=fin["cash"] - months * max(burn_cash, burn_pre),
             runway_lo=fin["cash"] / max(burn_cash, burn_pre),
             runway_hi=fin["cash"] / min(burn_cash, burn_pre))
    if fin.get("big_asset"):
        v = fin["big_asset"]["value"]
        m["big_asset"] = v
        m["big_asset_pct_eq"] = 100 * v / fin["equity"]
        m["big_asset_pct_assets"] = 100 * v / fin["total_assets"]
    m["book_ps"] = fin["equity"] / os_
    m["adj_equity"] = fin["equity"] - sum(a["value"] for a in fin.get("equity_adjustments", []))
    m["adj_book_ps"] = m["adj_equity"] / os_
    m["cash_like"] = sum(a["value"] for a in fin.get("cash_like", []))
    m["cash_like_ps"] = m["cash_like"] / os_

    # compliance
    ci = case.get("compliance_inputs", {})
    bid = ci.get("bid_min", 1.0)
    m["bid_cushion"] = 100 * (1 - bid / P)
    m["mvphs"] = non * P
    m["mvphs_line"] = ci.get("mvphs_min", 1_000_000) / non
    if ci.get("mvls_rule_line"):
        m["mvls_line"] = ci["mvls_rule_line"] / os_

    # chart data
    c = case.get("chart", {})
    pmin, pmax = c.get("pmin", P / 3), c.get("pmax", P * 12)
    n = 80
    prices = [10 ** (math.log10(pmin) + (math.log10(pmax) - math.log10(pmin)) * j / (n - 1)) for j in range(n)]
    layers = [dict(id=i["id"], name=i.get("short", i["name"]), gate=i["gate"],
                   values=[round(shares_at(i, p, case, "max")) for p in prices],
                   band_min=(i.get("shares_min") if i["gate"] == "live" else None))
              for i in case.get("instruments", []) if i.get("chart", True)]
    fd_stack = [dict(name="O/S", value=os_)] + [
        dict(name=i.get("short", i["name"]), id=i["id"], value=round(shares_at(i, P, case, "max")))
        for i in case.get("instruments", []) if i.get("fd")]
    chart = dict(prices=prices, layers=layers, ymax=c.get("ymax"), marks=c.get("price_marks", []),
                 ladder=sh.get("ladder", []), fd_stack=fd_stack, pmin=pmin, pmax=pmax)
    return m, chart


if __name__ == "__main__":
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    m, _ = compute(case)
    for k, v in m.items():
        print(f"{k} = {v}")
