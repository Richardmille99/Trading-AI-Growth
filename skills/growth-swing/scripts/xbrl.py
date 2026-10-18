"""SEC XBRL companyfacts → discrete quarters for fundamentals.py.

Usage:
  python xbrl.py --cik 1234567 --ua "Nombre email@dominio" [--out quarters.json] [--n 12]
  python xbrl.py --file companyfacts.json [--out quarters.json]

Flows: direct ~3-month facts are used when present; otherwise each quarter is the difference of
consecutive cumulative facts that share a fiscal-year start (6M−3M, 9M−6M, FY−9M). This derives Q4
and discretises year-to-date cash-flow lines. Balances: instant facts at the quarter end.
Average diluted shares are not additive: only direct quarterly facts are used (Q4 stays null unless
reported). Output quarters are ordered oldest → newest and carry `src` with the tag used.
"""
import argparse, json, sys, urllib.request
from datetime import date

CONCEPTS = {
    "revenue": ("flow", ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
                         "RevenueFromContractWithCustomerIncludingAssessedTax", "ifrs:Revenue"]),
    "gross_profit": ("flow", ["GrossProfit", "ifrs:GrossProfit"]),
    "cost_of_revenue": ("flow", ["CostOfRevenue", "CostOfGoodsAndServicesSold", "ifrs:CostOfSales"]),
    "op_income": ("flow", ["OperatingIncomeLoss", "ifrs:ProfitLossFromOperatingActivities"]),
    "net_income": ("flow", ["NetIncomeLoss", "ifrs:ProfitLoss"]),
    "cfo": ("flow", ["NetCashProvidedByUsedInOperatingActivities", "ifrs:CashFlowsFromUsedInOperatingActivities"]),
    "capex": ("flow", ["PaymentsToAcquirePropertyPlantAndEquipment", "ifrs:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"]),
    "capitalized_sw": ("flow", ["PaymentsToDevelopSoftware", "CapitalizedComputerSoftwareAdditions"]),
    "sbc": ("flow", ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]),
    "diluted_shares": ("avg", ["WeightedAverageNumberOfDilutedSharesOutstanding"]),
    "ar": ("inst", ["AccountsReceivableNetCurrent", "ifrs:CurrentTradeReceivables"]),
    "deferred_rev": ("inst", ["ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent"]),
    "rpo": ("inst", ["RevenueRemainingPerformanceObligation"]),
    "inventory": ("inst", ["InventoryNet", "ifrs:Inventories"]),
    "cash": ("inst", ["CashAndCashEquivalentsAtCarryingValue", "ifrs:CashAndCashEquivalents"]),
    "st_investments": ("inst", ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]),
    "debt": ("inst", ["LongTermDebt", "ConvertibleNotesPayable", "LongTermDebtNoncurrent"]),
    "debt_current": ("inst", ["LongTermDebtCurrent"]),
    "total_assets": ("inst", ["Assets", "ifrs:Assets"]),
}


def _d(s):
    return date.fromisoformat(s)


def _days(e):
    return (_d(e["end"]) - _d(e["start"])).days


def _units(facts, tag):
    ns, t = ("ifrs-full", tag[5:]) if tag.startswith("ifrs:") else ("us-gaap", tag)
    node = facts.get("facts", {}).get(ns, {}).get(t)
    if not node:
        return []
    units = node.get("units", {})
    for u in ("USD", "shares", "USD/shares"):
        if u in units:
            return units[u]
    return next(iter(units.values()), [])


def _dedupe(entries):
    """Keep the latest-filed value per (start, end)."""
    best = {}
    for e in entries:
        k = (e.get("start"), e["end"])
        if k not in best or e.get("filed", "") > best[k].get("filed", ""):
            best[k] = e
    return list(best.values())


def discrete_flows(entries):
    """{end: value} for ~quarterly periods, using direct facts and cumulative differences."""
    entries = _dedupe([e for e in entries if e.get("start")])
    out = {}
    for e in entries:
        if 80 <= _days(e) <= 100:
            out[e["end"]] = e["val"]
    by_start = {}
    for e in entries:
        by_start.setdefault(e["start"], []).append(e)
    for start, es in by_start.items():
        es = sorted(es, key=lambda x: x["end"])
        cum = [x for x in es if _days(x) >= 80]
        prev = None
        for x in cum:
            if prev is not None:
                span = (_d(x["end"]) - _d(prev["end"])).days
                if 80 <= span <= 100 and x["end"] not in out:
                    out[x["end"]] = x["val"] - prev["val"]
            prev = x
    return out


def direct_avg(entries):
    entries = _dedupe([e for e in entries if e.get("start")])
    return {e["end"]: e["val"] for e in entries if 80 <= _days(e) <= 100}


def instants(entries):
    best = {}
    for e in entries:
        if e.get("start"):
            continue
        if e["end"] not in best or e.get("filed", "") > best[e["end"]].get("filed", ""):
            best[e["end"]] = e
    return {k: v["val"] for k, v in best.items()}


def pick(facts, kind, tags):
    """Primary tag = the one reaching the most recent period; older gaps are filled from the other
    tags (companies switch tags, e.g. Revenues → RevenueFromContractWithCustomer…). Returns (tag, {end: val})."""
    found = []
    for tag in tags:
        es = _units(facts, tag)
        if not es:
            continue
        ser = discrete_flows(es) if kind == "flow" else direct_avg(es) if kind == "avg" else instants(es)
        if ser:
            found.append((tag, ser))
    if not found:
        return None, {}
    found.sort(key=lambda t: max(t[1]), reverse=True)
    tag, merged = found[0][0], dict(found[0][1])
    for _, ser in found[1:]:
        for k, v in ser.items():
            merged.setdefault(k, v)
    return tag, merged


def _label(end):
    d = _d(end)
    mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][d.month - 1]
    return f"{mes}-{d.year % 100:02d}"


def quarters_from_facts(facts, n=12):
    series, src = {}, {}
    for k, (kind, tags) in CONCEPTS.items():
        tag, ser = pick(facts, kind, tags)
        series[k], src[k] = ser, tag
    ends = sorted(series["revenue"])[-n:]
    quarters = []
    for end in ends:
        q = {"period": _label(end), "end": end}
        for k in CONCEPTS:
            q[k] = series[k].get(end)
        if q["gross_profit"] is None and q["revenue"] is not None and q["cost_of_revenue"] is not None:
            q["gross_profit"] = q["revenue"] - q["cost_of_revenue"]
        if q["cash"] is not None and q["st_investments"] is not None:
            q["cash"] += q["st_investments"]
        if q["debt"] is not None and src["debt"] == "LongTermDebtNoncurrent" and q["debt_current"]:
            q["debt"] += q["debt_current"]
        for k in ("cost_of_revenue", "st_investments", "debt_current"):
            q.pop(k)
        quarters.append(q)
    dei = facts.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
    shares_out = max(dei, key=lambda e: (e["end"], e.get("filed", ""))) if dei else None
    return dict(quarters=quarters, shares_out=shares_out and shares_out["val"],
                shares_out_date=shares_out and shares_out["end"], tags=src, source="sec-xbrl-companyfacts",
                entity=facts.get("entityName"), cik=facts.get("cik"))


def fetch(cik, ua):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cik")
    ap.add_argument("--ua", help='SEC requires "Nombre email"')
    ap.add_argument("--file")
    ap.add_argument("--out")
    ap.add_argument("--n", type=int, default=12)
    a = ap.parse_args()
    if a.file:
        facts = json.load(open(a.file, encoding="utf-8"))
    elif a.cik and a.ua:
        facts = fetch(a.cik, a.ua)
    else:
        ap.error("--file o --cik con --ua")
    res = quarters_from_facts(facts, a.n)
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
        print(f"wrote {a.out}: {len(res['quarters'])} trimestres; etiquetas: {res['tags']}")
    else:
        print(txt)


if __name__ == "__main__":
    sys.exit(main())
