"""Fundamentals engine — implements references/fundamentals.md §2–§6.

analyze(quarters, profile, profiles, manual) -> dict with metrics, flags, score, series
reverse_dcf(ev, rev_ttm, fcf_margin_now, fcf_target) -> implied 5-year growth or None

Quarters: list ordered oldest → newest, discrete (not YTD) flows, balances at period end.
"""

FLOW = ("revenue", "gross_profit", "op_income", "net_income", "cfo", "capex", "capitalized_sw", "sbc")


def _g(q, i, k):
    if i < 0 or i >= len(q):
        return None
    return q[i].get(k)


def yoy(q, i, k):
    a, b = _g(q, i, k), _g(q, i - 4, k)
    if a is None or b is None or b <= 0:
        return None
    return a / b - 1


def ttm(q, i, k):
    if i < 3:
        return None
    vals = [_g(q, j, k) for j in range(i - 3, i + 1)]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def ratio(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def fcf_q(q, i):
    cfo, capex = _g(q, i, "cfo"), _g(q, i, "capex")
    if cfo is None or capex is None:
        return None
    return cfo - capex - (_g(q, i, "capitalized_sw") or 0)


def fcf_ttm(q, i):
    if i < 3:
        return None
    v = [fcf_q(q, j) for j in range(i - 3, i + 1)]
    return None if any(x is None for x in v) else sum(v)


def _ttm_growth(q, i, k):
    a, b = ttm(q, i, k), ttm(q, i - 4, k)
    if a is None or b is None or b <= 0:
        return None
    return a / b - 1


def metrics(q):
    i = len(q) - 1
    m = {}
    m["period"] = q[i].get("period")
    m["rev_q"] = _g(q, i, "revenue")
    m["rev_yoy"] = yoy(q, i, "revenue")
    m["rev_yoy_prev"] = yoy(q, i - 1, "revenue")
    m["accel_pp"] = None if m["rev_yoy"] is None or m["rev_yoy_prev"] is None else (m["rev_yoy"] - m["rev_yoy_prev"]) * 100
    m["gp_yoy"] = yoy(q, i, "gross_profit")
    eps = [ratio(_g(q, j, "net_income"), _g(q, j, "diluted_shares")) for j in range(len(q))]
    m["eps_q"] = eps[i]
    m["eps_yoy"] = None if i < 4 or eps[i] is None or eps[i - 4] is None or eps[i - 4] <= 0 else eps[i] / eps[i - 4] - 1
    m["gm_q"] = ratio(_g(q, i, "gross_profit"), m["rev_q"])
    m["opm_q"] = ratio(_g(q, i, "op_income"), m["rev_q"])
    m["fcf_q"] = fcf_q(q, i)
    m["fcfm_q"] = ratio(m["fcf_q"], m["rev_q"])
    for k in FLOW:
        m[k + "_ttm"] = ttm(q, i, k)
    m["rev_ttm_prev"] = ttm(q, i - 4, "revenue")
    m["rev_ttm_yoy"] = _ttm_growth(q, i, "revenue")
    m["gm_ttm"] = ratio(m["gross_profit_ttm"], m["revenue_ttm"])
    m["opm_ttm"] = ratio(m["op_income_ttm"], m["revenue_ttm"])
    m["fcf_ttm"] = fcf_ttm(q, i)
    m["fcfm_ttm"] = ratio(m["fcf_ttm"], m["revenue_ttm"])
    m["rule40"] = None if m["rev_ttm_yoy"] is None or m["fcfm_ttm"] is None else (m["rev_ttm_yoy"] + m["fcfm_ttm"]) * 100
    m["sbc_pct"] = ratio(m["sbc_ttm"], m["revenue_ttm"])
    m["dil_yoy"] = yoy(q, i, "diluted_shares")
    m["dso"] = None if ratio(_g(q, i, "ar"), m["rev_q"]) is None else _g(q, i, "ar") / m["rev_q"] * 91
    ar4, rev4 = _g(q, i - 4, "ar"), _g(q, i - 4, "revenue")
    m["dso_prev"] = None if ar4 is None or not rev4 else ar4 / rev4 * 91
    m["dso_chg"] = None if m["dso"] is None or not m["dso_prev"] else m["dso"] / m["dso_prev"] - 1
    m["ar_yoy"] = yoy(q, i, "ar")
    m["inv_yoy"] = yoy(q, i, "inventory")
    m["def_yoy"] = yoy(q, i, "deferred_rev")
    m["rpo_yoy"] = yoy(q, i, "rpo")
    ta, ta4 = _g(q, i, "total_assets"), _g(q, i - 4, "total_assets")
    avg_ta = (ta + ta4) / 2 if ta and ta4 else ta
    m["accruals"] = None if m["net_income_ttm"] is None or m["cfo_ttm"] is None or not avg_ta else (m["net_income_ttm"] - m["cfo_ttm"]) / avg_ta
    op_prev = ttm(q, i - 4, "op_income")
    d_rev = None if m["revenue_ttm"] is None or m["rev_ttm_prev"] is None else m["revenue_ttm"] - m["rev_ttm_prev"]
    m["incr_margin"] = None if d_rev in (None, 0) or op_prev is None or m["op_income_ttm"] is None or d_rev <= 0 else (m["op_income_ttm"] - op_prev) / d_rev
    m["cash"], m["debt"] = _g(q, i, "cash"), _g(q, i, "debt") or 0
    m["net_cash"] = None if m["cash"] is None else m["cash"] - m["debt"]
    if m["fcf_ttm"] is not None and m["fcf_ttm"] < 0 and m["net_cash"] is not None:
        m["runway_m"] = max(0.0, m["net_cash"]) / (-m["fcf_ttm"] / 12)
    else:
        m["runway_m"] = None  # FCF ≥ 0 or unknown: no runway constraint
    opex_ttm = None if m["gross_profit_ttm"] is None or m["op_income_ttm"] is None else m["gross_profit_ttm"] - m["op_income_ttm"]
    m["capsw_opex"] = ratio(m["capitalized_sw_ttm"], opex_ttm)
    m["capsw_yoy"] = _ttm_growth(q, i, "capitalized_sw")
    return m


def _pp(a, b):
    return None if a is None or b is None else (a - b) * 100


def quality_flags(m, profile_cfg, manual):
    extra = set(profile_cfg.get("extra_flags", []))
    out = []

    def add(name, on, value, rule, scope=True):
        if scope:
            out.append(dict(name=name, on=on, value=value, rule=rule))

    d = _pp(m["ar_yoy"], m["rev_yoy"])
    add("COBROS > VENTAS", None if d is None else d > 20, d, "Δ cobros − Δ ingresos > 20 pp")
    on = None if m["dso_chg"] is None or m["accel_pp"] is None else (m["dso_chg"] > .15 and m["accel_pp"] < 0)
    add("DSO AL ALZA", on, m["dso_chg"], "DSO +15% interanual con crecimiento que desacelera")
    base = m["rpo_yoy"] if m["rpo_yoy"] is not None else m["def_yoy"]
    d = _pp(base, m["rev_yoy"])
    add("DIFERIDOS SE FRENAN", None if d is None else d < -15, d, "Δ diferidos/RPO < Δ ingresos − 15 pp",
        "DIFERIDOS SE FRENAN" in extra)
    on = None if m["net_income_ttm"] is None or m["cfo_ttm"] is None else (m["net_income_ttm"] > 0 and m["cfo_ttm"] < 0)
    add("BENEFICIO SIN CAJA", on, m["cfo_ttm"], "Beneficio neto TTM > 0 y CFO TTM < 0")
    add("ACCRUALS ALTOS", None if m["accruals"] is None else m["accruals"] > .10, m["accruals"], "Accruals de Sloan > 10%")
    add("SBC PESADA", None if m["sbc_pct"] is None else m["sbc_pct"] > .20, m["sbc_pct"], "SBC > 20% de ingresos TTM")
    add("DILUCIÓN", None if m["dil_yoy"] is None else m["dil_yoy"] > .05, m["dil_yoy"], "Acciones diluidas +5% interanual")
    d = _pp(m["inv_yoy"], m["rev_yoy"])
    add("INVENTARIO > VENTAS", None if d is None else d > 25, d, "Δ inventario − Δ ingresos > 25 pp",
        "INVENTARIO > VENTAS" in extra)
    on = None
    if m["capsw_opex"] is not None:
        on = m["capsw_opex"] > .10 or (m["capsw_yoy"] is not None and m["rev_ttm_yoy"] is not None
                                       and m["rev_ttm_yoy"] > 0 and m["capsw_yoy"] > 2 * m["rev_ttm_yoy"])
    add("CAPITALIZACIÓN", on, m["capsw_opex"], "Software capitalizado > 10% del opex o creciendo > 2× ingresos",
        "CAPITALIZACIÓN" in extra)
    ng = manual.get("nongaap_adj_pct")
    on = None if ng is None and manual.get("nongaap_recurring_items") is None else \
        bool((ng or 0) > .30 or manual.get("nongaap_recurring_items"))
    add("NON-GAAP AGRESIVO", on, ng, "(manual) ajustes > 30% de ingresos o no recurrentes repetidos")
    on = None if m["fcf_ttm"] is None else (m["fcf_ttm"] < 0 and (m["runway_m"] or 0) < 12)
    add("RUNWAY CORTO", on, m["runway_m"], "FCF negativo y caja neta < 12 meses de consumo")
    return out


# ---------- score (§6) ----------
def _sc_growth(g):
    if g is None: return None
    g *= 100
    return 100 if g >= 50 else 80 if g >= 30 else 60 if g >= 20 else 35 if g >= 10 else 15 if g >= 0 else 0


def _sc_accel(d):
    if d is None: return None
    return 100 if d >= 10 else 75 if d >= 3 else 50 if d > -3 else 25 if d > -10 else 0


def _sc_gm(gm, target):
    if gm is None: return None
    gap = (gm - target) * 100
    return 100 if gap >= 0 else 70 if gap >= -10 else 40 if gap >= -20 else 15


def _sc_r40(r):
    if r is None: return None
    return 100 if r >= 60 else 80 if r >= 40 else 55 if r >= 25 else 30 if r >= 10 else 10


def _sc_oplev(im, m):
    if im is None:
        return None if m["rev_ttm_prev"] is None else 30
    return 100 if im >= .30 else 70 if im >= .10 else 45 if im >= 0 else 15


def score(m, flags, profile_cfg):
    comps = dict(growth=_sc_growth(m["rev_yoy"]), accel=_sc_accel(m["accel_pp"]),
                 gross_margin=_sc_gm(m["gm_ttm"] if m["gm_ttm"] is not None else m["gm_q"], profile_cfg["gm_target"]),
                 rule40=_sc_r40(m["rule40"]), op_leverage=_sc_oplev(m["incr_margin"], m),
                 quality=max(0, 100 - 15 * sum(1 for f in flags if f["on"])))
    w = profile_cfg["weights"]
    avail = {k: v for k, v in comps.items() if v is not None}
    wsum = sum(w[k] for k in avail)
    total = None if wsum == 0 else sum(avail[k] * w[k] for k in avail) / wsum
    missing = [k for k, v in comps.items() if v is None]
    label = None if total is None else "fuerte" if total >= 65 else "aceptable" if total >= 45 else "débil"
    return dict(total=total, label=label, components=comps, weights=w, missing=missing)


def series(q):
    out = []
    for i in range(len(q)):
        g = yoy(q, i, "revenue")
        if g is None:
            continue
        gp = yoy(q, i - 1, "revenue")
        out.append(dict(period=q[i].get("period"), rev=q[i].get("revenue"), yoy=g,
                        accel=None if gp is None else (g - gp) * 100,
                        gm=ratio(q[i].get("gross_profit"), q[i].get("revenue"))))
    return out


def analyze(quarters, profile, profiles, manual=None):
    cfg = profiles.get(profile) or profiles["generic"]
    m = metrics(quarters)
    fl = quality_flags(m, cfg, manual or {})
    return dict(metrics=m, flags=fl, score=score(m, fl, cfg), series=series(quarters), profile=cfg)


# ---------- reverse DCF (§4) ----------
def dcf_value(g, rev0, m0, mt, r=.10, gt=.03):
    pv, rev, fcf = 0.0, rev0, 0.0
    for y in range(1, 11):
        if y <= 5:
            gy, margin = g, m0 + (mt - m0) * y / 5
        else:
            gy, margin = g + (gt - g) * (y - 5) / 5, mt
        rev *= 1 + gy
        fcf = rev * margin
        pv += fcf / (1 + r) ** y
    return pv + fcf * (1 + gt) / (r - gt) / (1 + r) ** 10


def reverse_dcf(ev, rev_ttm, m0, mt, r=.10, gt=.03, lo=-0.5, hi=3.0):
    if not ev or ev <= 0 or not rev_ttm or rev_ttm <= 0 or m0 is None:
        return None
    f = lambda g: dcf_value(g, rev_ttm, m0, mt, r, gt) - ev
    flo, fhi = f(lo), f(hi)
    if flo > 0 or fhi < 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
