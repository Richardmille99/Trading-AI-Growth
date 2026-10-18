"""EDGAR filing index for a CIK (submissions API) → data/<T>/filings.json.

Usage:
  python edgar.py --cik 1835632 --ua "Nombre email" --out semis/data/MRVL/filings.json [--since 2024-01-01]
  python edgar.py --file filings.json --after <accession>     (update mode: filings newer than last_filing_seen)

Each row: form, filed, report_date, accession, primary_doc, items (8-K items), url (primary document),
accepted_et (acceptance time in New York, AAAA-MM-DDTHH:MM) and session ('bmo' before 9:30, 'intraday', 'amc' from 16:00).
"""
import argparse, json, sys, time, urllib.request
from datetime import datetime, timedelta


def _get(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or i == 3:
                raise
            time.sleep(2 ** i)


def _nth_sunday(year, month, n):
    d = datetime(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def to_new_york(utc_iso):
    """EDGAR acceptanceDateTime (UTC, '...Z') → New York local time, US DST rules (no tzdata needed)."""
    if not utc_iso:
        return None
    u = datetime.strptime(utc_iso[:19], "%Y-%m-%dT%H:%M:%S")
    start = _nth_sunday(u.year, 3, 2) + timedelta(hours=7)   # 2:00 EST = 7:00 UTC
    end = _nth_sunday(u.year, 11, 1) + timedelta(hours=6)    # 2:00 EDT = 6:00 UTC
    return u - timedelta(hours=4 if start <= u < end else 5)


def session_of(et):
    if et is None:
        return None
    hm = et.hour * 60 + et.minute
    return "bmo" if hm < 9 * 60 + 30 else "amc" if hm >= 16 * 60 else "intraday"


def _rows(block, cik):
    keys = ("form", "filingDate", "reportDate", "accessionNumber", "primaryDocument", "items", "acceptanceDateTime")
    cols = [block.get(k, [None] * len(block.get("form", []))) for k in keys]
    for form, filed, rep, acc, doc, items, accepted in zip(*cols):
        et = to_new_york(accepted)
        yield dict(form=form, filed=filed, report_date=rep or None, accession=acc, primary_doc=doc, items=items or None,
                   url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}" if doc else None,
                   accepted_et=et.strftime("%Y-%m-%dT%H:%M") if et else None, session=session_of(et))


def filings(cik, ua, since="2023-01-01"):
    base = _get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", ua)
    rows = list(_rows(base["filings"]["recent"], cik))
    for f in base["filings"].get("files", []):
        if f.get("filingTo", "9999") >= since:
            rows += list(_rows(_get(f"https://data.sec.gov/submissions/{f['name']}", ua), cik))
    rows = sorted({r["accession"]: r for r in rows if r["filed"] >= since}.values(), key=lambda r: r["filed"], reverse=True)
    return dict(cik=int(cik), name=base.get("name"), tickers=base.get("tickers"), fiscal_year_end=base.get("fiscalYearEnd"),
                exchanges=base.get("exchanges"), sic=base.get("sic"), sic_description=base.get("sicDescription"), filings=rows)


def after(index, accession):
    """Filings filed after the one with `accession` (newest first)."""
    fs = index["filings"]
    seen = next((r["filed"] for r in fs if r["accession"] == accession), None)
    if seen is None:
        return fs
    return [r for r in fs if r["filed"] > seen or (r["filed"] == seen and r["accession"] > accession)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cik")
    ap.add_argument("--ua")
    ap.add_argument("--out")
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--file")
    ap.add_argument("--after")
    a = ap.parse_args()
    if a.file:
        idx = json.load(open(a.file, encoding="utf-8"))
        for r in (after(idx, a.after) if a.after else idx["filings"]):
            print(f'{r["filed"]} {r["form"]:<8} {r["accession"]} {r["items"] or ""} {r["url"] or ""}')
        return
    if not (a.cik and a.ua):
        ap.error("--cik y --ua, o --file")
    idx = filings(a.cik, a.ua, a.since)
    txt = json.dumps(idx, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
        print(f"wrote {a.out}: {len(idx['filings'])} filings ({idx['name']})")
    else:
        print(txt)


if __name__ == "__main__":
    sys.exit(main())
