"""Phase 1 for a new ticker of a universe: data/<T>/ + cases/<T>.json, validated.

Usage:
  python new_case.py --universe memoria/universe.json --ticker MU --ua "$SEC_USER_AGENT" [--date AAAA-MM-DD] [--force]
       [--earn-date AAAA-MM-DD --earn-timing amc|bmo --earn-url URL]     (override / foreign issuers)

Steps (each one skipped if its file already exists, unless --force):
  1. CIK from universe.json or SEC company_tickers.json (written back to universe.json).
  2. data/<T>/filings.json  (edgar.py: index with acceptance time and session).
  3. data/<T>/quarters.json (xbrl.py + inline-XBRL fallback for 10-Q/10-K not yet in companyfacts).
     Foreign issuers (filer 20-F/6-K) have no quarterly XBRL: load quarters.json by hand first (CLAUDE.md).
  4. data/<T>/prices.csv    (prices.py download, 2 years).
  5. Earnings catalyst: latest 8-K with Item 2.02 (its EX-99.1 as source, session from the acceptance time) matched
     to the last quarter, with the market reaction. Next earnings = that date + 91 days, marked [VERIFY].
  6. Default Phase-1 texts; validate.py must pass. universe.json status → 'fundamentales'.
Nothing here reads consensus, guidance or KPIs: those stay for the analyst (Phase 1 manual pass and Phase 2).
"""
import argparse, json, os, sys, time, urllib.request
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import casekit, edgar, prices, xbrl  # noqa: E402
from validate import validate  # noqa: E402

E = "https://www.sec.gov/Archives/edgar/data"


def _json(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def lookup_cik(ticker, ua):
    for row in _json("https://www.sec.gov/files/company_tickers.json", ua).values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"])
    return None


def last_earnings_8k(index):
    """Newest 8-K (or 8-K/A) carrying Item 2.02."""
    return next((r for r in index["filings"] if r["form"] in ("8-K", "8-K/A") and "2.02" in (r.get("items") or "")), None)


def same_day_earnings_8ks(index, first):
    """Every 8-K with Item 2.02 filed the same day as `first` (a company may file the results and, say, a CFO change apart)."""
    return [r for r in index["filings"] if r["form"] in ("8-K", "8-K/A") and "2.02" in (r.get("items") or "")
            and r["filed"] == first["filed"]]


def exhibit_991(cik, filings, ua):
    """[label, url] of the press-release exhibit: the largest '99' exhibit among `filings` (the results release is
    longer than a same-day announcement); falls back to the first filing's primary document."""
    best = None
    for f in filings:
        acc = f["accession"].replace("-", "")
        try:
            items = _json(f"{E}/{int(cik)}/{acc}/index.json", ua)["directory"]["item"]
        except Exception:  # noqa: BLE001 — the index is a convenience; the 8-K itself is a valid source
            continue
        for i in items:
            n = i["name"]
            if n.lower().endswith((".htm", ".html")) and "99" in n and n != f.get("primary_doc"):
                size = int(i.get("size") or 0)
                if best is None or size > best[0]:
                    best = (size, f, f"{E}/{int(cik)}/{acc}/{n}")
        time.sleep(.2)
    if best:
        return [f'EX-99.1 8-K {best[1]["filed"]}', best[2]]
    return [f'8-K {filings[0]["filed"]} (Item 2.02)', filings[0]["url"]]


def quarter_for(quarters, day):
    """Last quarter that ended before `day` and at most 100 days earlier."""
    d = date.fromisoformat(day)
    cand = [q for q in quarters if date.fromisoformat(q["end"]) < d <= date.fromisoformat(q["end"]) + timedelta(days=100)]
    return cand[-1] if cand else None


def build(uni_path, t, ua, today, force=False, earn=None, log=print):
    root = os.path.dirname(os.path.abspath(uni_path))
    uni = json.load(open(uni_path, encoding="utf-8"))
    u = next(x for x in uni["tickers"] if x["ticker"] == t)
    d = os.path.join(root, "data", t)
    os.makedirs(d, exist_ok=True)
    foreign = "20-F" in (u.get("filer") or "") or "6-K" in (u.get("filer") or "")

    if not u.get("cik"):
        u["cik"] = lookup_cik(t, ua)
        if not u["cik"]:
            raise SystemExit(f"{t}: no está en company_tickers.json; añade 'cik' a universe.json")
        json.dump(uni, open(uni_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cik = int(u["cik"])

    fpath = os.path.join(d, "filings.json")
    if force or not os.path.exists(fpath):
        idx = edgar.filings(cik, ua)
        json.dump(idx, open(fpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log(f"{t}: {len(idx['filings'])} filings ({idx['name']})")
    idx = json.load(open(fpath, encoding="utf-8"))

    qpath = os.path.join(d, "quarters.json")
    if foreign and not os.path.exists(qpath):
        raise SystemExit(f"{t}: emisor extranjero sin trimestres en XBRL; carga {qpath} a mano desde los 6-K (CLAUDE.md)")
    if not foreign and (force or not os.path.exists(qpath)):
        facts = xbrl.fetch(cik, ua)
        added = xbrl.supplement(facts, idx, ua, log=log)
        res = xbrl.quarters_from_facts(facts, 12, inline_ends=set(added))
        json.dump(res, open(qpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log(f"{t}: {len(res['quarters'])} trimestres (último {res['quarters'][-1]['end']})")
    fin = json.load(open(qpath, encoding="utf-8"))

    ppath = os.path.join(d, "prices.csv")
    if force or not os.path.exists(ppath):
        src, rows = prices.download(t)
        prices.write_csv(ppath, rows)
        log(f"{t}: {len(rows)} sesiones de precio ({src})")
    rows = prices.read_csv(ppath)

    earn_cat, events, q = None, [], fin["quarters"]
    if earn:
        e_date, e_timing, e_src = earn["date"], earn["timing"], [earn.get("label") or f"Resultados {earn['date']}", earn.get("url", "")]
    else:
        f8 = None if foreign else last_earnings_8k(idx)
        e_date, e_timing, e_src = (f8["filed"], f8.get("session") or "amc", exhibit_991(cik, same_day_earnings_8ks(idx, f8), ua)) if f8 else (None, None, None)
        if f8 and f8.get("session") == "intraday":
            e_timing = "amc"  # released during the session: the reaction is the next session's
    lastq = quarter_for(q, e_date) if e_date else None
    if lastq:
        gy, _, _ = casekit.growth_at(q, lastq["end"])
        head = f"Resultados {lastq['period']}: ingresos {casekit.usd_m(lastq['revenue'])}" + (
            f" ({gy * 100:+.0f}% interanual)" if gy is not None else "")
        earn_cat = casekit.earnings(dict(financials=fin), rows, f"q_{lastq['end'][:7].replace('-', '')}", lastq["end"], e_date, e_timing,
                                    head, e_src, note="Fase 1: sin consenso, guía ni sorpresa. [VERIFY: consenso (finviz o búsqueda web) y guía del PR]")
        nxt = (date.fromisoformat(e_date) + timedelta(days=91)).isoformat()
        events.append(dict(date=nxt, kind="earnings", text=f"Próximos resultados [VERIFY: fecha estimada = últimos resultados ({e_date}) + 91 días]",
                           src=[]))
    elif e_date:
        log(f"{t}: AVISO resultados del {e_date} sin trimestre que case (¿companyfacts atrasado?)")

    group = uni.get("subgroups", {}).get(u.get("subgroup"), u.get("subgroup") or "")
    descriptor = (u.get("descriptor") or u.get("notes") or u["issuer"]).rstrip(".") + \
        ". Ingresos {m.revenue_ttm:usdM} TTM; último trimestre {m.rev_yoy:pctf} interanual."
    src_note = "Trimestres de XBRL (companyfacts" + (", con el último leído del documento" if any(x.get("src") for x in q) else "") + \
        ")." if not foreign else "Emisor extranjero: trimestres cargados a mano desde los 6-K (ver notas.md)."
    exch = u.get("exchange") or ", ".join(idx.get("exchanges") or []) or "n/d"
    case = casekit.skeleton(u, uni.get("theme", uni.get("name", "")), group, today, fin, idx, earn_cat, events, descriptor,
                            src_note + " [VERIFY: contrastar el último trimestre con el EX-99.1]", exch)
    cpath = casekit.case_path(root, t)
    if os.path.exists(cpath) and not force:
        raise SystemExit(f"{t}: {cpath} ya existe (usa --force para rehacerlo; en modo actualización no se rehace nada)")
    errs, warns = validate(case)
    for w in warns:
        log(f"  AVISO: {w}")
    if errs:
        raise SystemExit(f"{t}: validate.py → {errs} (caso no guardado)")
    casekit.save(root, t, case)
    u["status"] = "fundamentales"
    json.dump(uni, open(uni_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    notes = os.path.join(d, "notas.md")
    fresh = not os.path.exists(notes) or os.path.getsize(notes) == 0
    with open(notes, "a", encoding="utf-8") as fh:
        if fresh:
            fh.write(f"# {t} · notas\n\n")
        fh.write(f"- {today} · Fase 1 automática (new_case.py): {len(q)} trimestres, último {q[-1]['end']}; "
                 f"resultados {e_date or 'n/d'} ({e_timing or '—'}).\n")
    log(f"{t}: caso creado → {cpath} (validate OK)")
    time.sleep(.2)
    return case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--ticker", required=True, nargs="+")
    ap.add_argument("--ua", default=os.environ.get("SEC_USER_AGENT"))
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--earn-date")
    ap.add_argument("--earn-timing", choices=("amc", "bmo"))
    ap.add_argument("--earn-url")
    a = ap.parse_args()
    if not a.ua or "@" not in a.ua:
        ap.error("SEC exige User-Agent con nombre y email: --ua o $SEC_USER_AGENT")
    earn = dict(date=a.earn_date, timing=a.earn_timing or "amc", url=a.earn_url or "") if a.earn_date else None
    for t in a.ticker:
        build(a.universe, t, a.ua, a.date, a.force, earn)


if __name__ == "__main__":
    main()
