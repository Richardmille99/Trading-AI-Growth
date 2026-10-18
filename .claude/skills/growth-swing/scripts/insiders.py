"""Insider and holder activity from EDGAR XML: Forms 4, 144 and Schedules 13D/13G (references/dilution_supply.md §2).

Usage:
  python insiders.py --filings data/<T>/filings.json --ua "Nombre email" --out data/<T>/insiders.json [--days 365] [--asof AAAA-MM-DD]

Form 4  — open-market sales (code S) and purchases (P) per owner and calendar quarter. A sale is flagged when it is not
          under a 10b5-1 plan (aff10b5One = 0 and no footnote citing 10b5-1) or when the owner sold > 10% of the position
          in a quarter: sold ÷ (sold + total position, all accounts, after the owner's last sale of that quarter). Tax withholding (F),
          option exercises (M), grants (A) and gifts (G) are counted apart and never flagged.
Form 144 — notices of proposed sales (shares, value, approximate date).
13D/13G — reporting person, shares, % of class, event date (XML schedules only, i.e. since Dec-2024).
"""
import argparse, json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, timedelta


def _strip_ns(root):
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def _t(el, path, default=None):
    x = el.find(path)
    if x is None:
        return default
    v = x.find("value")
    txt = (v.text if v is not None else x.text)
    return txt.strip() if txt and txt.strip() else default


def _f(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse_form4(xml):
    root = _strip_ns(ET.fromstring(xml))
    owners = [dict(name=_t(o, "reportingOwnerId/rptOwnerName"),
                   director=_t(o, "reportingOwnerRelationship/isDirector") in ("1", "true"),
                   officer=_t(o, "reportingOwnerRelationship/isOfficer") in ("1", "true"),
                   ten_pct=_t(o, "reportingOwnerRelationship/isTenPercentOwner") in ("1", "true"),
                   title=_t(o, "reportingOwnerRelationship/officerTitle"))
              for o in root.findall("reportingOwner")]
    plan_box = _t(root, "aff10b5One") in ("1", "true")
    notes = {fn.get("id"): (fn.text or "") for fn in root.iter("footnote")}
    plan_note = any(re.search(r"10b5-?1", n, re.I) for n in notes.values())
    tx = []
    for t in root.iter("nonDerivativeTransaction"):
        ids = {fid.get("id") for fid in t.iter("footnoteId")}
        tx.append(dict(date=_t(t, "transactionDate"), code=_t(t, "transactionCoding/transactionCode"),
                       shares=_f(_t(t, "transactionAmounts/transactionShares")),
                       price=_f(_t(t, "transactionAmounts/transactionPricePerShare")),
                       ad=_t(t, "transactionAmounts/transactionAcquiredDisposedCode"),
                       after=_f(_t(t, "postTransactionAmounts/sharesOwnedFollowingTransaction")),
                       nature=_t(t, "ownershipNature/directOrIndirectOwnership"),
                       plan=plan_box or any(re.search(r"10b5-?1", notes.get(i, ""), re.I) for i in ids) or (plan_note and not ids)))
    # total position after the filing: last balance of every account (direct, each trust/entity), including
    # accounts listed only as holdings; a sale from one trust does not empty the owner's position
    acct = {}
    for el in root.iter():
        if el.tag in ("nonDerivativeTransaction", "nonDerivativeHolding"):
            after = _f(_t(el, "postTransactionAmounts/sharesOwnedFollowingTransaction"))
            if after is None:
                continue
            nat = el.find("ownershipNature/natureOfOwnership")
            key = (_t(el, "securityTitle"), _t(el, "ownershipNature/directOrIndirectOwnership"),
                   (_t(el, "ownershipNature/natureOfOwnership") or "") + ",".join(f.get("id") for f in (nat.iter("footnoteId") if nat is not None else [])))
            acct[key] = after
    return dict(owners=owners, plan_box=plan_box, transactions=tx, total_after=sum(acct.values()) if acct else None)


def parse_144(xml):
    root = _strip_ns(ET.fromstring(xml))
    raw = xml if isinstance(xml, str) else xml.decode("utf-8", "replace")
    return dict(person=_t(root, ".//nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold"),
                relationship=_t(root, ".//relationshipToIssuer"),
                shares=_f(_t(root, ".//securitiesInformation/noOfUnitsSold")),
                value=_f(_t(root, ".//securitiesInformation/aggregateMarketValue")),
                outstanding=_f(_t(root, ".//securitiesInformation/noOfUnitsOutstanding")),
                approx_date=_t(root, ".//securitiesInformation/approxSaleDate"),
                plan_10b5_1=bool(re.search(r"10b5-?1", raw, re.I)))


def parse_13(xml):
    root = _strip_ns(ET.fromstring(xml))
    people = []
    for p in root.iter("coverPageHeaderReportingPersonDetails"):
        people.append(dict(name=_t(p, "reportingPersonName"),
                           shares=_f(_t(p, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares") or _t(p, "aggregateAmountOwned")),
                           pct=_f(_t(p, "classPercent") or _t(p, "percentOfClass"))))
    if not people:  # 13D layout
        for p in root.iter("reportingPersons"):
            for q in p:
                people.append(dict(name=_t(q, "reportingPersonName"), shares=_f(_t(q, "aggregateAmountOwned")),
                                   pct=_f(_t(q, "percentOfClass"))))
    return dict(event_date=_t(root, ".//eventDateRequiresFilingThisStatement") or _t(root, ".//dateOfEvent"), persons=people)


def quarter(d):
    return f"{d[:4]}-T{(int(d[5:7]) - 1) // 3 + 1}"


def summarize_form4(docs):
    """docs: list of parsed Form 4 dicts (with 'accession', 'filed'). Returns per-owner rows with flags."""
    by = defaultdict(lambda: dict(sold=0.0, value=0.0, bought=0.0, bought_value=0.0, tax=0.0, exercised=0.0,
                                  quarters=defaultdict(lambda: dict(sold=0.0, last_after=None, last_date="")),
                                  off_plan=[], role="", accessions=set()))
    for d in docs:
        o = d["owners"][0] if d["owners"] else dict(name="?")
        role = ", ".join(x for x, ok in (("consejero", o.get("director")), (o.get("title") or "directivo", o.get("officer")),
                                         ("≥10%", o.get("ten_pct"))) if ok)
        r = by[o["name"]]
        r["role"] = r["role"] or role
        for t in d["transactions"]:
            if not t["shares"] or not t["date"]:
                continue
            if t["code"] == "S":
                r["sold"] += t["shares"]
                r["value"] += t["shares"] * (t["price"] or 0)
                q = r["quarters"][quarter(t["date"])]
                q["sold"] += t["shares"]
                remaining = d.get("total_after") if d.get("total_after") is not None else t["after"]
                if t["date"] >= q["last_date"] and remaining is not None:
                    q["last_date"], q["last_after"] = t["date"], remaining
                if not t["plan"]:
                    r["off_plan"].append(dict(date=t["date"], shares=t["shares"], price=t["price"], accession=d["accession"]))
                r["accessions"].add(d["accession"])
            elif t["code"] == "P":
                r["bought"] += t["shares"]
                r["bought_value"] += t["shares"] * (t["price"] or 0)
                r["accessions"].add(d["accession"])
            elif t["code"] == "F":
                r["tax"] += t["shares"]
            elif t["code"] == "M":
                r["exercised"] += t["shares"]
    rows = []
    for name, r in by.items():
        qmax = None
        for qk, q in r["quarters"].items():
            if q["last_after"] is not None and q["sold"]:
                pct = q["sold"] / (q["sold"] + q["last_after"])
                if qmax is None or pct > qmax[1]:
                    qmax = (qk, pct)
        flagged = bool(r["off_plan"]) or (qmax is not None and qmax[1] > .10)
        if not (r["sold"] or r["bought"]):
            continue
        rows.append(dict(name=name, role=r["role"], sold=r["sold"], sold_value=round(r["value"]), bought=r["bought"],
                         bought_value=round(r["bought_value"]), tax_withheld=r["tax"], exercised=r["exercised"],
                         max_quarter_pct=None if qmax is None else round(qmax[1], 4), max_quarter=None if qmax is None else qmax[0],
                         off_plan_sales=r["off_plan"], flagged=flagged, accessions=sorted(r["accessions"])))
    return sorted(rows, key=lambda x: -x["sold_value"])


def fetch(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or i == 3:
                raise
            time.sleep(2 ** i)


def raw_url(cik, row):
    doc = row["primary_doc"].split("/")[-1]  # drop the xsl rendering folder → raw XML
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{row['accession'].replace('-', '')}/{doc}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filings", required=True)
    ap.add_argument("--ua", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--asof", default=date.today().isoformat())
    a = ap.parse_args()
    idx = json.load(open(a.filings, encoding="utf-8"))
    since = (date.fromisoformat(a.asof) - timedelta(days=a.days)).isoformat()
    rows = [r for r in idx["filings"] if r["filed"] >= since and r["filed"] <= a.asof]
    f4, f144, f13, errors = [], [], [], []
    for r in rows:
        kind = "4" if r["form"] in ("4", "4/A") else "144" if r["form"] in ("144", "144/A") else \
            "13" if r["form"].startswith(("SCHEDULE 13", "SC 13")) else None
        if not kind or not (r["primary_doc"] or "").endswith(".xml"):
            continue
        try:
            xml = fetch(raw_url(idx["cik"], r), a.ua)
            if kind == "4":
                d = parse_form4(xml)
            elif kind == "144":
                d = parse_144(xml)
            else:
                d = parse_13(xml)
            d.update(accession=r["accession"], filed=r["filed"], form=r["form"])
            (f4 if kind == "4" else f144 if kind == "144" else f13).append(d)
        except Exception as e:  # malformed or legacy document: keep going, report it
            errors.append(dict(accession=r["accession"], form=r["form"], error=str(e)[:200]))
        time.sleep(.22)
    owners = summarize_form4(f4)
    holders = {}
    for d in sorted(f13, key=lambda x: x["filed"]):
        for p in d["persons"]:
            holders[p["name"]] = dict(p, filed=d["filed"], form=d["form"], event_date=d["event_date"], accession=d["accession"])
    out = dict(asof=a.asof, since=since, cik=idx["cik"], form4_count=len(f4), form144_count=len(f144), schedule13_count=len(f13),
               owners=owners, form144=sorted(f144, key=lambda x: x["filed"], reverse=True),
               holders=sorted(holders.values(), key=lambda x: -(x.get("pct") or 0)), errors=errors)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Forms 4: {len(f4)} · 144: {len(f144)} · 13D/G: {len(f13)} · errores: {len(errors)}")
    for o in owners[:12]:
        print(f'  {o["name"][:32]:<32} {o["role"][:28]:<28} vende {o["sold"]:>12,.0f} (${o["sold_value"]:>13,.0f}) '
              f'compra {o["bought"]:>9,.0f} máx/trim {o["max_quarter_pct"]} {"MARCADA" if o["flagged"] else ""} fuera de plan {len(o["off_plan_sales"])}')
    for h in out["holders"][:8]:
        print(f'  13D/G {h["name"][:40]:<40} {h.get("pct")}% {h.get("shares")} ({h["filed"]})')


if __name__ == "__main__":
    sys.exit(main())
