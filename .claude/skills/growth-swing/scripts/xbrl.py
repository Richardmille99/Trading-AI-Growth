"""SEC XBRL companyfacts → discrete quarters for fundamentals.py.

Usage:
  python xbrl.py --cik 1234567 --ua "Nombre email@dominio" [--out quarters.json] [--n 12]
  python xbrl.py --file companyfacts.json [--out quarters.json]

Flows: direct ~3-month facts are used when present; otherwise each quarter is the difference of
consecutive cumulative facts that share a fiscal-year start (6M−3M, 9M−6M, FY−9M). This derives Q4
and discretises year-to-date cash-flow lines. Balances: instant facts at the quarter end.
Average diluted shares are not additive: only direct quarterly facts are used (Q4 stays null unless
reported). Output quarters are ordered oldest → newest and carry `src` with the tag used.

companyfacts can lag a new 10-Q/10-K by weeks. With --filings data/<T>/filings.json, every 10-Q/10-K whose period
ends after the last quarter in companyfacts is read directly (inline XBRL of its primary document, facts without
dimensions only) and merged before computing the quarters; the quarter's `src` says so.
"""
import argparse, html as _html, json, re, sys, time, urllib.request
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
    "basic_shares": ("avg", ["WeightedAverageNumberOfSharesOutstandingBasic"]),
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


def _same_vintage(xs, ps):
    """Par (acumulado largo, acumulado corto) presentado más cerca en el tiempo, con el largo después del corto.
    Restar versiones distintas da basura: un 10-K que reexpresa el año sin un negocio vendido menos los 9 meses
    originales (APP 2023, ingresos −$488M), o un 10-Q posterior que etiqueta mal el año (FIX 2025, −$4.624M)."""
    return min(((x, p) for x in xs for p in ps),
               key=lambda xp: (xp[0].get("filed", "") < xp[1].get("filed", ""),
                               abs((_d(xp[0].get("filed") or xp[0]["end"]) - _d(xp[1].get("filed") or xp[1]["end"])).days)))


def discrete_flows(entries):
    """{end: value} for ~quarterly periods, using direct facts and cumulative differences."""
    entries = [e for e in entries if e.get("start")]
    out = {}
    for e in _dedupe(entries):
        if 80 <= _days(e) <= 100:
            out[e["end"]] = e["val"]
    vers = {}
    for e in entries:
        if _days(e) >= 80:
            vers.setdefault(e["start"], {}).setdefault(e["end"], []).append(e)
    for start, by_end in vers.items():
        ends = sorted(by_end)
        for prev, end in zip(ends, ends[1:]):
            if end not in out and 80 <= (_d(end) - _d(prev)).days <= 100:
                x, p = _same_vintage(by_end[end], by_end[prev])
                out[end] = x["val"] - p["val"]
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


def quarters_from_facts(facts, n=12, inline_ends=()):
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
        if q["revenue"] is not None and q["revenue"] < 0:
            # Ni emparejando versiones cuadra (APLD reexpresó el año en el mismo 10-K): mejor un hueco que una cifra imposible.
            q["revenue"] = q["gross_profit"] = None
            q["gap"] = True
            q["gap_note"] = "el trimestre derivado (año − 9 meses) da ingresos negativos: reexpresión entre filings; ver el 10-K"
        if end in inline_ends:
            q["src"] = "XBRL incrustado del 10-Q/10-K (companyfacts aún no lo incluía)"
        quarters.append(q)
    dei = facts.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
    shares_out = max(dei, key=lambda e: (e["end"], e.get("filed", ""))) if dei else None
    return dict(quarters=quarters, shares_out=shares_out and shares_out["val"],
                shares_out_date=shares_out and shares_out["end"], tags=src, source="sec-xbrl-companyfacts",
                entity=facts.get("entityName"), cik=facts.get("cik"))


# ---------- inline XBRL fallback (filings not yet in companyfacts) ----------
_CTX = re.compile(r"<(?:\w+:)?context\b[^>]*\bid=\"([^\"]+)\"[^>]*>(.*?)</(?:\w+:)?context>", re.S | re.I)
_FACT = re.compile(r"<ix:nonFraction\b([^>]*)>(.*?)</ix:nonFraction>", re.S | re.I)
_ATTR = re.compile(r'([\w:]+)="([^"]*)"')


def _tagval(block, name):
    m = re.search(rf"<(?:\w+:)?{name}>\s*([^<\s]+)\s*</(?:\w+:)?{name}>", block, re.I)
    return m.group(1) if m else None


def facts_from_ixbrl(doc, filed, form):
    """companyfacts-shaped dict from an inline-XBRL document. Dimensional contexts (segments) are skipped."""
    ctx = {}
    for cid, body in _CTX.findall(doc):
        if re.search(r"<(?:\w+:)?segment\b", body, re.I):
            continue
        inst = _tagval(body, "instant")
        ctx[cid] = dict(end=inst) if inst else dict(start=_tagval(body, "startDate"), end=_tagval(body, "endDate"))
    out = {"facts": {}}
    seen = set()
    for attrs, inner in _FACT.findall(doc):
        a = dict(_ATTR.findall(attrs))
        c = ctx.get(a.get("contextRef"))
        if not c or not c.get("end") or ":" not in a.get("name", ""):
            continue
        txt = _html.unescape(re.sub(r"<[^>]+>", "", inner)).strip().replace(",", "").replace(" ", "").strip("()")
        if "fixed-zero" in a.get("format", "") or txt in ("", "—", "-", "–"):
            val = 0.0
        else:
            try:
                val = float(txt)
            except ValueError:
                continue
        val *= 10 ** int(a.get("scale", "0") or 0)
        if a.get("sign") == "-":
            val = -val
        prefix, local = a["name"].split(":", 1)
        ns = {"us-gaap": "us-gaap", "dei": "dei", "ifrs-full": "ifrs-full"}.get(prefix)
        if not ns:
            continue
        u = (a.get("unitRef") or "").lower()
        unit = "USD/shares" if "usd" in u and "share" in u else "USD" if "usd" in u else "shares" if "share" in u else u
        key = (ns, local, c.get("start"), c["end"], unit)
        if key in seen:
            continue
        seen.add(key)
        e = dict(c, val=int(val) if val == int(val) else val, filed=filed, form=form, src="inline-xbrl")
        out["facts"].setdefault(ns, {}).setdefault(local, {"units": {}})["units"].setdefault(unit, []).append(e)
    return out


def merge_facts(base, extra):
    for ns, tags in extra.get("facts", {}).items():
        for tag, node in tags.items():
            dst = base.setdefault("facts", {}).setdefault(ns, {}).setdefault(tag, {"units": {}})["units"]
            for unit, es in node["units"].items():
                dst.setdefault(unit, []).extend(es)
    return base


def supplement(facts, index, ua, log=print):
    """Merge inline XBRL of 10-Q/10-K filings whose period ends after the last revenue quarter in companyfacts."""
    _, rev = pick(facts, "flow", CONCEPTS["revenue"][1])
    last = max(rev) if rev else "0000"
    added = []
    for r in sorted(index["filings"], key=lambda x: x["filed"]):
        if r["form"] in ("10-Q", "10-K", "10-Q/A", "10-K/A") and (r.get("report_date") or "") > last and r.get("url"):
            req = urllib.request.Request(r["url"], headers={"User-Agent": ua, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                doc = resp.read().decode("utf-8", "replace")
            merge_facts(facts, facts_from_ixbrl(doc, r["filed"], r["form"]))
            added.append(r["report_date"])
            log(f"  + {r['form']} {r['report_date']} leído del XBRL del documento (companyfacts aún no lo tenía)")
            time.sleep(.25)
    return added


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
    ap.add_argument("--filings", help="data/<T>/filings.json: lee del documento los 10-Q/10-K que companyfacts aún no tiene")
    a = ap.parse_args()
    if a.file:
        facts = json.load(open(a.file, encoding="utf-8"))
    elif a.cik and a.ua:
        facts = fetch(a.cik, a.ua)
    else:
        ap.error("--file o --cik con --ua")
    added = supplement(facts, json.load(open(a.filings, encoding="utf-8")), a.ua) if a.filings and a.ua else []
    res = quarters_from_facts(facts, a.n, inline_ends=set(added))
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
        print(f"wrote {a.out}: {len(res['quarters'])} trimestres; etiquetas: {res['tags']}")
    else:
        print(txt)


if __name__ == "__main__":
    sys.exit(main())
