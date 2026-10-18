"""Helpers to build and update case.json files (library; no CLI).

  load(univ_dir, t) / save(univ_dir, t, case)     cases/<T>.json
  link(cik, accession, doc, label)                 [label, EDGAR url]
  growth_at(quarters, end)                         (yoy, yoy_prev, gm_change_bp) for the quarter ending `end`
  earnings(case, rows, ...)                        earnings catalyst with the market reaction from prices.reaction
  contract(cid, date, headline, src, **kw)         contract/partnership catalyst with every checklist field defaulted
  insider_supply(insiders_json)                    supply[] row of kind 'insider' from insiders.py output
  skeleton(...)                                    Phase-1 case with default texts (used by new_case.py)
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prices import reaction  # noqa: E402

E = "https://www.sec.gov/Archives/edgar/data"


def case_path(univ_dir, t):
    return os.path.join(univ_dir, "cases", f"{t}.json")


def load(univ_dir, t):
    return json.load(open(case_path(univ_dir, t), encoding="utf-8"))


def save(univ_dir, t, case):
    os.makedirs(os.path.join(univ_dir, "cases"), exist_ok=True)
    json.dump(case, open(case_path(univ_dir, t), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def link(cik, acc, doc, label):
    return [label, f"{E}/{int(cik)}/{acc.replace('-', '')}/{doc}"]


def growth_at(q, end):
    """(yoy, yoy_prev, gm_change_bp) for the quarter ending `end`; None where the year-ago quarter is missing."""
    i = next(i for i, x in enumerate(q) if x["end"] == end)

    def g(j):
        return None if j < 4 or not q[j - 4].get("revenue") or q[j].get("revenue") is None else q[j]["revenue"] / q[j - 4]["revenue"] - 1

    def gm(j):
        return q[j]["gross_profit"] / q[j]["revenue"] if q[j].get("gross_profit") is not None and q[j].get("revenue") else None

    bp = None if i < 4 or gm(i) is None or gm(i - 4) is None else round((gm(i) - gm(i - 4)) * 1e4)
    return g(i), g(i - 1), bp


def earnings(case, rows, cid, qend, date, timing, headline, src, rev_surprise=None, eps_surprise=None, guide_raise=None,
             guide_change=None, nonrec=False, note="", growth=None):
    """Earnings catalyst (catalysts.md §2). `rows` = prices.read_csv(...); timing 'amc' | 'bmo'.
    The reaction fields stay out if the release has not traded yet."""
    gy, gyp, bp = growth or growth_at(case["financials"]["quarters"], qend)
    c = dict(id=cid, type="earnings", date=date, time_et="after-hours" if timing == "amc" else "premarket", headline=headline,
             sources=[src] if src and isinstance(src[0], str) else src, rev_growth_yoy=gy, rev_growth_yoy_prev=gyp,
             rev_surprise_pct=rev_surprise, eps_surprise_pct=eps_surprise, guide_raise=guide_raise, guide_change_pct=guide_change,
             gm_change_bp=bp, nonrecurring_in_beat=nonrec, note=note)
    rx = reaction(rows, date, timing) if rows else None
    if rx:
        c.update(rx)
    return c


def contract(cid, date, headline, src, **kw):
    base = dict(id=cid, type=kw.pop("type", "commercial_contract"), date=date, time_et=kw.pop("time_et", None), headline=headline,
                sources=src, counterparty=None, counterparty_named=False, counterparty_confirms=False, filed_8k_101=False,
                exhibit_attached=False, binding="none", value_firm=None, value_ceiling=None, duration_years=None,
                economics_disclosed=False, recurring=False, issuer_history="unknown", pr_count_90d=None, financing_after_days=None,
                financing_discount_pct=None, insider_selling_after=False, lockup_within_days=None, promo_language=False, note="")
    base.update(kw)
    return base


def usd_m(v):
    """Spanish format in millions: 1234567.0 → '$1,2M'; 50_400_000 → '$50,4M'; 6.5e9 → '$6.500,0M'."""
    return "$" + f"{v / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + "M"


def insider_supply(path, top=4, src_label="Forms 4 (EDGAR), insiders.json"):
    d = json.load(open(path, encoding="utf-8"))
    fl = [o for o in d["owners"] if o["flagged"]]
    tot = sum(o["sold_value"] for o in d["owners"])
    names = "; ".join(f'{o["name"]} ({o["role"][:30]}) {usd_m(o["sold_value"])}, máx. {o["max_quarter_pct"] * 100:.0f}% en {o["max_quarter"]}'
                      f'{", " + str(len(o["off_plan_sales"])) + " ventas sin 10b5-1" if o["off_plan_sales"] else ""}'
                      for o in fl[:top])
    return dict(id="insiders", kind="insider", name=f"Ventas de insiders 12 meses: {usd_m(tot)}; {len(fl)} marcados",
                shares=sum(o["sold"] for o in d["owners"]), capacity_usd=None, price_basis=None, gate="live", date=None,
                flagged=bool(fl), notes=(names + ". " if names else "") +
                "Compras en mercado abierto: " + f'{sum(o["bought"] for o in d["owners"]):,.0f}'.replace(",", ".") + " acciones.",
                src=[[src_label, ""]])


def skeleton(u, theme, group_label, report_date, fin, filings_index, earn_cat, events, descriptor, fin_note, exchange):
    """Phase-1 case: quarters, last earnings with its reaction, next earnings (estimated) and default texts."""
    last = filings_index["filings"][0] if filings_index.get("filings") else {}
    cik = u.get("cik") or filings_index.get("cik")
    return dict(
        schema_version="1.0",
        meta=dict(ticker=u["ticker"], issuer=u["issuer"], cik=f"{int(cik):010d}" if cik else None, exchange=exchange,
                  report_date=report_date, price_basis=None, profile=u["profile"], theme=theme, group=group_label,
                  subgroup=u.get("subgroup"), synthetic=False, primary_catalyst=earn_cat["id"] if earn_cat else None,
                  descriptor=descriptor, last_filing_seen=last.get("accession"), last_filing_seen_date=last.get("filed"),
                  phase="fundamentales"),
        market=dict(price=None, price_date=None, regime="unknown", regime_evidence=""),
        financials=dict(source=fin.get("source", "sec-xbrl-companyfacts"), shares_out=fin.get("shares_out"),
                        shares_out_date=fin.get("shares_out_date"),
                        shares_out_note=fin.get("shares_out_note", "dei:EntityCommonStockSharesOutstanding (portada del último 10-Q/10-K)"),
                        quarters=fin["quarters"]),
        manual=dict(kpis=[], nongaap_adj_pct=None, nongaap_recurring_items=None),
        catalysts=[earn_cat] if earn_cat else [],
        supply=[],
        supply_context=dict(float_shares=None, window_days=56, ep_recent_days=None, atm_used_last_q=False),
        peers=[],
        setup=dict(type=None, pivot=None, stop=None, notes=None),
        events=events,
        header=dict(verdict="Fase 1 (fundamentales): sin auditoría de catalizadores, oferta ni insiders. La convicción es provisional.",
                    setup="{m.adr_pct:n1}% de ADR; ver §8.", catalyst="Solo los últimos resultados; sin consenso ni sorpresa.",
                    quality="Nota de fundamentales {m.fund_score:sc}; {m.flags_on:int} banderas activas.",
                    supply="Fase 1: sin auditoría de oferta. [VERIFY: Fase 2]", group="Pares = resto del universo."),
        snapshot=[["Negocio", descriptor.split(".")[0]], ["Subgrupo · pureza", f'{group_label} · {u.get("purity", "n/d")}'],
                  ["Ingresos TTM", "{m.revenue_ttm:usdM} · {m.rev_ttm_yoy:pctf} interanual"],
                  ["Último trimestre", "{m.rev_q:usdM} · {m.rev_yoy:pctf} · aceleración {m.accel_pp:pp}"],
                  ["Margen bruto TTM", "{m.gm_ttm:pctf}"], ["Rule of 40", "{m.rule40:n1}"], ["Caja neta", "{m.net_cash:usdM}"],
                  ["Market cap / EV", "{m.mcap:usdM} / {m.ev:usdM}"]],
        text=dict(narrative_flags=[], catalyst_read="Fase 1: solo se registran los últimos resultados con su reacción de mercado. "
                  "La checklist completa de catalizadores queda para la Fase 2.", financials_note=fin_note, quality=[],
                  supply_read="Fase 1: oferta sin auditar. [VERIFY: recompras, shelf, convertibles, Forms 4/144, 13D/13G — Fase 2]",
                  valuation=[], group_read="", risks=[], plan=[], verdict=""),
        sources=list(earn_cat["sources"]) if earn_cat else [],
    )
