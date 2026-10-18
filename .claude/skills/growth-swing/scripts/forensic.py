"""Large-company forensic data from EDGAR: balance-sheet quality, public float and governance events.

Usage:
  python forensic.py --cik 1288469 --ua "Nombre email" --filings data/<T>/filings.json [--prices data/<T>/prices.csv] --out data/<T>/forensic.json

- goodwill, intangibles and equity at the latest balance date (us-gaap or ifrs-full), (goodwill + intangibles) ÷ equity
- dei:EntityPublicFloat (10-K cover: non-affiliate market value at the end of Q2) → float shares = value ÷ close that day
  (needs prices.csv covering that date; otherwise null)
- 8-K items 4.01 (auditor change), 4.02 (non-reliance / restatement), 5.02 (officer or director change), NT 10-K/10-Q
"""
import argparse, csv, json, sys, urllib.request

TAGS = {
    "goodwill": ["Goodwill", "ifrs:Goodwill"],
    "intangibles": ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet", "ifrs:IntangibleAssetsOtherThanGoodwill"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "ifrs:Equity"],
    "total_assets": ["Assets", "ifrs:Assets"],
    "impairment": ["GoodwillImpairmentLoss", "ImpairmentOfIntangibleAssetsExcludingGoodwill", "GoodwillAndIntangibleAssetImpairment"],
}


def _units(facts, tag):
    ns, t = ("ifrs-full", tag[5:]) if tag.startswith("ifrs:") else ("us-gaap", tag)
    node = facts.get("facts", {}).get(ns, {}).get(t)
    if not node:
        return []
    u = node.get("units", {})
    return u.get("USD") or next(iter(u.values()), [])


def latest_instant(facts, tags):
    best = None
    for tag in tags:
        for e in _units(facts, tag):
            if e.get("start"):
                continue
            if best is None or (e["end"], e.get("filed", "")) > (best["end"], best.get("filed", "")):
                best = dict(e, tag=tag)
    return best


def flows_since(facts, tags, since):
    out = []
    for tag in tags:
        for e in _units(facts, tag):
            if e.get("start") and e["end"] >= since and e.get("val"):
                out.append(dict(tag=tag, start=e["start"], end=e["end"], val=e["val"], form=e.get("form")))
    return sorted({(x["tag"], x["start"], x["end"]): x for x in out}.values(), key=lambda x: x["end"])


def public_float(facts):
    es = facts.get("facts", {}).get("dei", {}).get("EntityPublicFloat", {}).get("units", {}).get("USD", [])
    return max(es, key=lambda e: (e["end"], e.get("filed", ""))) if es else None


def close_on(prices_csv, day):
    if not prices_csv:
        return None
    try:
        rows = list(csv.DictReader(open(prices_csv, encoding="utf-8")))
    except OSError:
        return None
    on = [r for r in rows if r["date"] <= day]
    if not on or (rows and rows[0]["date"] > day):
        return None
    return dict(date=on[-1]["date"], close=float(on[-1]["close"]))


def governance(filings, since):
    ev = []
    for r in filings["filings"]:
        if r["filed"] < since:
            continue
        items = r.get("items") or ""
        hit = [i for i in ("4.01", "4.02", "5.02") if i in items.split(",")]
        if r["form"].startswith("NT "):
            hit.append(r["form"])
        if hit:
            ev.append(dict(filed=r["filed"], form=r["form"], items=hit, accession=r["accession"], url=r["url"]))
    return ev


def fetch(cik, ua):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def analyze(facts, filings, prices_csv, since):
    bs = {k: latest_instant(facts, v) for k, v in TAGS.items() if k != "impairment"}
    val = {k: (b["val"] if b else None) for k, b in bs.items()}
    gi = (val["goodwill"] or 0) + (val["intangibles"] or 0)
    pf = public_float(facts)
    px = close_on(prices_csv, pf["end"]) if pf else None
    return dict(
        balance={k: (dict(val=b["val"], end=b["end"], tag=b["tag"], form=b.get("form")) if b else None) for k, b in bs.items()},
        goodwill_intang_to_equity=gi / val["equity"] if val["equity"] else None,
        goodwill_intang_to_assets=gi / val["total_assets"] if val["total_assets"] else None,
        impairments=flows_since(facts, TAGS["impairment"], since),
        public_float=None if not pf else dict(usd=pf["val"], date=pf["end"], filed=pf.get("filed"), form=pf.get("form"),
                                               close=px and px["close"], close_date=px and px["date"],
                                               float_shares=round(pf["val"] / px["close"]) if px else None),
        governance=governance(filings, since))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cik", required=True)
    ap.add_argument("--ua", required=True)
    ap.add_argument("--filings", required=True)
    ap.add_argument("--prices")
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="2024-10-01")
    a = ap.parse_args()
    res = analyze(fetch(a.cik, a.ua), json.load(open(a.filings, encoding="utf-8")), a.prices, a.since)
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    b = res["balance"]
    f = lambda k: "n/d" if not b[k] else f'{b[k]["val"] / 1e6:,.1f}M ({b[k]["end"]})'
    print(f'goodwill {f("goodwill")} · intangibles {f("intangibles")} · patrimonio {f("equity")} · '
          f'(GW+int)/patrimonio {res["goodwill_intang_to_equity"] and round(res["goodwill_intang_to_equity"], 2)}')
    print(f'float público {res["public_float"]}')
    print(f'deterioros desde {a.since}: {[(x["end"], round(x["val"] / 1e6, 1)) for x in res["impairments"]]}')
    for g in res["governance"]:
        print(f'  {g["filed"]} {g["form"]} {g["items"]} {g["url"]}')


if __name__ == "__main__":
    sys.exit(main())
