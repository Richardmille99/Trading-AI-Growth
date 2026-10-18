"""Catalyst scoring engine — implements references/catalysts.md exactly.

score_catalyst(c, revenue_ttm) -> dict(score, grade, verdict, components, flags, caps, market)
Usage: python catalysts.py case.json
"""
import json, sys

BINDING = {"definitive": 20, "purchase_order": 20, "award_funded": 20, "option_exercise": 16,
           "award_unfunded": 12, "idiq_ceiling": 8, "loi": 5, "mou": 3, "partnership_undefined": 1, "none": 0}
SOFT = {"loi", "mou", "partnership_undefined", "none"}
HISTORY = {"converted": 10, "partial": 5, "unknown": 3, "not_converted": 0}
VERDICT = {"A": "real", "B": "real parcial", "C": "por confirmar", "D": "especulación"}
ORDER = "ABCD"


def grade_of(score):
    return "A" if score >= 75 else "B" if score >= 60 else "C" if score >= 40 else "D"


def cap(grade, maxg):
    return grade if ORDER.index(grade) >= ORDER.index(maxg) else maxg


def _materiality(c, revenue_ttm, flags):
    firm = c.get("value_firm")
    if not firm:
        if c.get("value_ceiling"):
            flags.append("TECHO ≠ INGRESO")
        return 0, None
    years = max(c.get("duration_years") or 1, 1)
    annual = firm / years
    if not revenue_ttm:
        return 8, None  # material in absolute terms but no base: mid score
    r = annual / revenue_ttm
    pts = 20 if r >= .25 else 14 if r >= .10 else 8 if r >= .03 else 3
    return pts, r


def score_contract(c, revenue_ttm):
    flags, caps = [], []
    ver = (5 if c.get("counterparty_named") else 0) + (10 if c.get("counterparty_confirms") else 0) \
        + (5 if c.get("filed_8k_101") else 0) + (5 if c.get("exhibit_attached") else 0)
    binding = c.get("binding", "none")
    bnd = BINDING.get(binding, 0)
    mat, ratio = _materiality(c, revenue_ttm, flags)
    eco = (6 if c.get("economics_disclosed") else 0) + (4 if c.get("recurring") else 0)
    hist = HISTORY.get(c.get("issuer_history", "unknown"), 3)
    if (c.get("pr_count_90d") or 0) >= 6:
        hist = max(0, hist - 3); flags.append("PR EN SERIE")
    jux = 15
    fa, disc = c.get("financing_after_days"), c.get("financing_discount_pct") or 0
    if fa is not None and fa <= 10:
        jux -= 15 if disc >= 10 else 10
        flags.append("PR→FINANCIACIÓN")
    if c.get("insider_selling_after"):
        jux -= 5; flags.append("VENTA DE INSIDERS")
    lk = c.get("lockup_within_days")
    if lk is not None and lk <= 30:
        jux -= 5; flags.append("LOCK-UP CERCA")
    if c.get("promo_language"):
        jux -= 3; flags.append("LENGUAJE PROMOCIONAL")
    jux = max(0, jux)
    comps = dict(verificable=ver, vinculante=bnd, materialidad=mat, economia=eco, historial=hist, juxtaposiciones=jux)
    score = sum(comps.values())
    g = grade_of(score)
    if binding in SOFT and not c.get("value_firm"):
        g = cap(g, "C"); caps.append("no vinculante y sin valor firme → máx. C")
    if fa is not None and fa <= 10 and disc >= 10:
        g = cap(g, "C"); caps.append("financiación con descuento ≤10 días → máx. C")
    if c.get("issuer_history") == "not_converted" and c.get("promo_language"):
        g = cap(g, "D"); caps.append("historial no convertido + lenguaje promocional → D")
    return score, g, comps, flags, caps, ratio


def score_earnings(c):
    flags = []
    gy = c.get("rev_growth_yoy")
    gro = 0 if gy is None else 25 if gy >= .40 else 18 if gy >= .25 else 10 if gy >= .15 else 3
    acc = 0
    if gy is not None and c.get("rev_growth_yoy_prev") is not None:
        d = (gy - c["rev_growth_yoy_prev"]) * 100
        acc = 20 if d >= 10 else 15 if d >= 3 else 8 if d > -3 else 0
        if d <= -3: flags.append("DESACELERA")
    rs, es = c.get("rev_surprise_pct"), c.get("eps_surprise_pct")
    sur = (0 if rs is None else 10 if rs >= 5 else 6 if rs >= 2 else 3 if rs > 0 else 0) + \
          (0 if es is None else 10 if es >= 10 else 5 if es > 0 else 0)
    gr, gc = c.get("guide_raise"), c.get("guide_change_pct")
    if gr is None:
        gui = 5
    elif gr:
        gui = 25 if (gc or 0) >= 5 else 18
    else:
        gui = 0 if (gc or 0) < 0 else 8
    if gc is not None and gc < 0: flags.append("BAJA LA GUÍA")
    gm = c.get("gm_change_bp")
    qual = 6 if gm is None else 10 if gm >= 100 else 6 if gm >= 0 else 2
    if c.get("nonrecurring_in_beat"):
        qual = max(0, qual - 10); flags.append("BEAT CON NO RECURRENTES")
    comps = dict(crecimiento=gro, aceleracion=acc, sorpresa=sur, guia=gui, calidad=qual)
    score = sum(comps.values())
    return score, grade_of(score), comps, flags, [], None


def score_financing(c):
    flags, s = [], 50
    ft = c.get("financing_type")
    p = c.get("price_vs_market_pct")
    if ft == "strategic" and (p or 0) >= 0:
        s += 35
    elif p is not None and p > 0:
        s += 15
    if p is not None and p <= -15:
        s -= 25
    elif p is not None and p <= -5:
        s -= 15
    if ft == "atm":
        s -= 10; flags.append("ATM")
    if c.get("warrants"):
        s -= 10; flags.append("WARRANTS")
    if ft == "convertible" and c.get("variable_price"):
        s -= 25; flags.append("CONVERTIBLE VARIABLE")
    s = max(0, min(100, s))
    return s, grade_of(s), dict(base=50, ajuste=s - 50), flags, [], None


def score_market(c):
    if all(c.get(k) is None for k in ("gap_pct", "rvol", "close_in_range", "day2_follow", "estimate_revisions")):
        return None
    s = 0
    if (c.get("gap_pct") or 0) >= 10: s += 20
    rv = c.get("rvol") or 0
    s += 25 if rv >= 5 else 15 if rv >= 3 else 0
    if (c.get("close_in_range") or 0) >= 2 / 3: s += 20
    if c.get("day2_follow"): s += 15
    if c.get("estimate_revisions") == "up": s += 20
    return s


def score_catalyst(c, revenue_ttm=None):
    t = c.get("type", "other")
    if t == "earnings":
        score, g, comps, flags, caps, ratio = score_earnings(c)
    elif t == "financing":
        score, g, comps, flags, caps, ratio = score_financing(c)
    elif t == "index_analyst":
        score, g, comps, flags, caps, ratio = 20, "D", {"no_cambia_negocio": 20}, ["SIN CAMBIO DE NEGOCIO"], [], None
    else:
        score, g, comps, flags, caps, ratio = score_contract(c, revenue_ttm)
    return dict(id=c.get("id"), type=t, score=score, grade=g, verdict=VERDICT[g], components=comps,
                flags=flags, caps=caps, materiality_ratio=ratio, market=score_market(c))


if __name__ == "__main__":
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    from fundamentals import ttm
    q = case.get("financials", {}).get("quarters", [])
    rev = ttm(q, len(q) - 1, "revenue") if q else None
    for c in case.get("catalysts", []):
        r = score_catalyst(c, rev)
        print(f'{r["id"]:<10} {r["type"]:<20} {r["score"]:>3} {r["grade"]} {r["verdict"]:<14} {r["flags"]} {r["caps"]}')
