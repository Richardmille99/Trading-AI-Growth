"""Offline tests: XBRL discretisation on a synthetic companyfacts fixture + scoring rules.
Run: python tests/test_engines.py   (from the skill folder)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from xbrl import quarters_from_facts  # noqa: E402
from catalysts import score_catalyst  # noqa: E402
from fundamentals import reverse_dcf, dcf_value  # noqa: E402
from compute import compute, conviction  # noqa: E402


def fact(start, end, val, filed, form="10-Q"):
    d = {"end": end, "val": val, "filed": filed, "form": form}
    if start:
        d["start"] = start
    return d


def fixture():
    """FY = calendar year. Revenue: direct quarters Q1–Q3 + annual (Q4 must be derived).
    CFO: year-to-date only (all quarters must be discretised). Old revenue on a legacy tag."""
    rev = [  # 2025: Q1 100, Q2 120, Q3 130, FY 500 → Q4 150
        fact("2025-01-01", "2025-03-31", 100, "2025-05-01"),
        fact("2025-04-01", "2025-06-30", 120, "2025-08-01"),
        fact("2025-01-01", "2025-06-30", 220, "2025-08-01"),
        fact("2025-07-01", "2025-09-30", 130, "2025-11-01"),
        fact("2025-01-01", "2025-09-30", 350, "2025-11-01"),
        fact("2025-01-01", "2025-12-31", 500, "2026-02-20", "10-K"),
        fact("2026-01-01", "2026-03-31", 140, "2026-05-01"),
        fact("2025-01-01", "2025-03-31", 99, "2025-04-15"),  # older, superseded value
    ]
    legacy = [fact("2024-10-01", "2024-12-31", 90, "2025-02-20", "10-K")]
    cfo = [
        fact("2025-01-01", "2025-03-31", -10, "2025-05-01"),
        fact("2025-01-01", "2025-06-30", -5, "2025-08-01"),
        fact("2025-01-01", "2025-09-30", 10, "2025-11-01"),
        fact("2025-01-01", "2025-12-31", 40, "2026-02-20", "10-K"),
        fact("2026-01-01", "2026-03-31", 12, "2026-05-01"),
    ]
    cash = [fact(None, e, v, f) for e, v, f in [("2025-03-31", 50, "2025-05-01"), ("2025-12-31", 70, "2026-02-20"),
                                                ("2026-03-31", 65, "2026-05-01")]]
    return {"cik": 1, "entityName": "Fixture Co (synthetic)", "facts": {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": rev}},
            "Revenues": {"units": {"USD": legacy}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": cfo}},
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": cash}},
        },
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            fact(None, "2026-04-25", 1000, "2026-05-01"), fact(None, "2026-02-10", 990, "2026-02-20")]}}}}}


def test_xbrl():
    r = quarters_from_facts(fixture(), n=12)
    q = {x["end"]: x for x in r["quarters"]}
    assert q["2025-12-31"]["revenue"] == 150, "Q4 = FY − 9M"
    assert q["2025-03-31"]["revenue"] == 100, "latest filed wins"
    assert q["2024-12-31"]["revenue"] == 90, "legacy tag fills older gap"
    assert [q[e]["cfo"] for e in ("2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31")] == [-10, 5, 15, 30, 12]
    assert q["2025-12-31"]["cash"] == 70 and q["2025-06-30"]["cash"] is None
    assert r["shares_out"] == 1000 and r["tags"]["revenue"].startswith("RevenueFromContract")
    print("xbrl ok")


def test_xbrl_q4_same_vintage():
    """Q4 = año − 9 meses solo con datos de la misma versión (casos reales de FIX, APP y APLD)."""
    rev = [  # FIX 2025: un 10-Q de 2026 etiqueta mal el año con el valor del 1T; el 10-K manda.
        fact("2025-01-01", "2025-03-31", 1831, "2025-04-24"),
        fact("2025-01-01", "2025-06-30", 4005, "2025-07-24"),
        fact("2025-01-01", "2025-09-30", 6456, "2025-10-23"),
        fact("2025-01-01", "2025-12-31", 9102, "2026-02-19", "10-K"),
        fact("2025-01-01", "2025-12-31", 1831, "2026-04-23"),
        # APP 2023: un 10-K de 2026 reexpresa el año sin el negocio vendido; los 9 meses son los originales.
        fact("2023-01-01", "2023-09-30", 2330, "2023-11-08"),
        fact("2023-01-01", "2023-12-31", 3283, "2024-02-26", "10-K"),
        fact("2023-01-01", "2023-12-31", 1842, "2026-02-19", "10-K"),
        # APLD FY25: el propio 10-K ya reexpresa; ninguna versión cuadra → hueco, no ingresos negativos.
        fact("2024-06-01", "2025-02-28", 178, "2025-04-14"),
        fact("2024-06-01", "2025-05-31", 144, "2025-07-30", "10-K"),
    ]
    f = {"cik": 1, "facts": {"us-gaap": {"Revenues": {"units": {"USD": rev}}}}}
    q = {x["end"]: x for x in quarters_from_facts(f, n=20)["quarters"]}
    assert q["2025-12-31"]["revenue"] == 9102 - 6456, "FIX: el 10-K, no el 10-Q mal etiquetado"
    assert q["2023-12-31"]["revenue"] == 3283 - 2330, "APP: año y 9 meses de la misma versión"
    assert q["2025-05-31"]["revenue"] is None and q["2025-05-31"]["gap"] and q["2025-05-31"]["gap_note"]
    print("xbrl Q4 misma versión ok")


def test_catalysts():
    base = dict(type="gov_contract", counterparty_named=True, counterparty_confirms=True, filed_8k_101=True,
                exhibit_attached=True, binding="award_funded", value_firm=50e6, duration_years=1,
                economics_disclosed=True, recurring=True, issuer_history="converted", pr_count_90d=2)
    r = score_catalyst(base, 100e6)
    assert r["score"] == 100 and r["grade"] == "A"
    r = score_catalyst(dict(base, financing_after_days=2, financing_discount_pct=15), 100e6)
    assert r["score"] == 85 and r["grade"] == "C" and "PR→FINANCIACIÓN" in r["flags"]
    r = score_catalyst(dict(base, binding="idiq_ceiling", value_firm=None, value_ceiling=1e9), 100e6)
    assert r["components"]["materialidad"] == 0 and "TECHO ≠ INGRESO" in r["flags"]
    r = score_catalyst(dict(base, binding="mou", value_firm=None), 100e6)
    assert r["grade"] in ("C", "D") and r["caps"]
    r = score_catalyst(dict(base, issuer_history="not_converted", promo_language=True), 100e6)
    assert r["grade"] == "D"
    r = score_catalyst(dict(type="financing", financing_type="strategic", price_vs_market_pct=5), None)
    assert r["score"] == 85
    print("catalysts ok")


def test_dcf_and_conviction():
    v = dcf_value(.25, 100, .05, .2)
    g = reverse_dcf(v, 100, .05, .2)
    assert abs(g - .25) < 1e-6
    assert conviction("A", 80, 70, "leader", False, "ep")[0] == "Alta"
    assert conviction("A", 80, 70, "unknown", False, "ep")[0] == "Media"
    assert conviction("C", 50, 55, "weak", False, "ep")[0] == "Media"
    assert conviction("D", 80, 70, "leader", False, "ep")[0] == "Baja"
    assert conviction("A", 80, 30, "leader", False, "ep")[0] == "Descartar"
    assert conviction("B", 80, 70, "leader", True, "vcp")[0] == "Descartar"
    print("dcf + conviction ok")


def _quarters(**over):
    base = dict(revenue=100.0, gross_profit=50.0, op_income=10.0, net_income=10.0, cfo=20.0, capex=5.0, capitalized_sw=None,
                sbc=1.0, diluted_shares=100.0, basic_shares=100.0, ar=None, deferred_rev=None, rpo=None, inventory=None,
                cash=100.0, debt=0.0, total_assets=500.0)
    q = [dict(base, period=f"q{i}", end=f"2025-{i + 1:02d}-28") for i in range(9)]
    for i, kv in over.items():
        q[int(i[1:])].update(kv)
    return q


def test_dilution_and_runway_rules():
    from fundamentals import metrics
    # year-ago loss: diluted (=basic under GAAP) 90 vs diluted 110 would read +22%; basic 98 → 100 is +2%
    m = metrics(_quarters(q4=dict(net_income=-5.0, diluted_shares=90.0, basic_shares=98.0)))
    assert m["dil_basis"] == "basic" and abs(m["dil_yoy"] - (100 / 98 - 1)) < 1e-9
    m = metrics(_quarters(q4=dict(net_income=-5.0, basic_shares=None)))
    assert m["dil_yoy"] is None, "loss and no basic shares → n/d, never the biased diluted figure"
    m = metrics(_quarters(q4=dict(diluted_shares=90.0)))
    assert m["dil_basis"] == "diluted" and abs(m["dil_yoy"] - (100 / 90 - 1)) < 1e-9
    both = metrics(_quarters(q4=dict(net_income=-5.0, diluted_shares=90.0, basic_shares=None), q8=dict(net_income=-1.0, basic_shares=None)))
    assert both["dil_basis"] == "diluted" and abs(both["dil_yoy"] - (100 / 90 - 1)) < 1e-9, "two losses: diluted = basic in both"
    # positive CFO, capex-driven negative FCF, net debt: runway on gross cash (100 / (40/12) = 30 months)
    capex_heavy = {f"q{i}": dict(capex=30.0, debt=300.0) for i in range(5, 9)}
    m = metrics(_quarters(**capex_heavy))
    assert m["fcf_ttm"] == -40 and abs(m["runway_m"] - 30) < 1e-9
    # negative CFO: net cash (negative → 0 months)
    burn = {f"q{i}": dict(cfo=-10.0, capex=0.0, debt=300.0) for i in range(5, 9)}
    assert metrics(_quarters(**burn))["runway_m"] == 0
    print("dilution + runway rules ok")


def test_peer_gm_relative_to_profile():
    from compute import peers_table
    foundry = dict(ticker="F", rev_yoy=.2, accel_pp=0, gm=.27, gm_rel=.27 - .25, rule40=20, ev_sales=5, rs_3m=50)
    fabless = [dict(ticker=f"P{i}", rev_yoy=.2, accel_pp=0, gm=.55, gm_rel=.55 - .60, rule40=20, ev_sales=5, rs_3m=50)
               for i in range(3)]
    rows, _ = peers_table(foundry, fabless)
    s = next(r for r in rows if r["subject"])
    assert s["gm_basis"] == "gm_rel" and s["pct"]["gm"] == 100, "above its own target beats peers below theirs"
    raw = [{k: v for k, v in p.items() if k != "gm_rel"} for p in fabless]
    rows, _ = peers_table({k: v for k, v in foundry.items() if k != "gm_rel"}, raw)
    s = next(r for r in rows if r["subject"])
    assert s["gm_basis"] == "gm" and s["pct"]["gm"] == 0, "without gm_rel, absolute margin"
    print("peer gm relative ok")


def test_example():
    case = json.load(open(os.path.join(HERE, "..", "examples", "EXMP_synthetic.json"), encoding="utf-8"))
    m, R, _ = compute(case)
    assert R["primary"]["grade"] == "A" and R["supply"]["total"] == 55 and R["group"] == "leader"
    assert R["conviction"] == "Media" and round(m["fund_score"]) == 83
    print("example ok")


IXBRL = """<html><body><xbrli:context id="Q"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity>
<xbrli:period><xbrli:startDate>2026-04-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="QSEG"><xbrli:entity><xbrli:identifier>1</xbrli:identifier><xbrli:segment><xbrldi:explicitMember dimension="x">y</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
<xbrli:period><xbrli:startDate>2026-04-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="I"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<ix:nonFraction name="us-gaap:Revenues" contextRef="Q" unitRef="usd" scale="6" decimals="-5">1,234.5</ix:nonFraction>
<ix:nonFraction name="us-gaap:Revenues" contextRef="QSEG" unitRef="usd" scale="6">999</ix:nonFraction>
<ix:nonFraction name="us-gaap:NetIncomeLoss" contextRef="Q" unitRef="usd" scale="6" sign="-">(<span>12</span>)</ix:nonFraction>
<ix:nonFraction name="us-gaap:InventoryNet" contextRef="I" unitRef="usd" scale="3" format="ixt:fixed-zero">—</ix:nonFraction>
<ix:nonFraction name="us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding" contextRef="Q" unitRef="shares" scale="6">50.5</ix:nonFraction>
</body></html>"""


def test_ixbrl_fallback():
    from xbrl import facts_from_ixbrl, merge_facts
    base = {"facts": {"us-gaap": {"Revenues": {"units": {"USD": [fact("2026-01-01", "2026-03-31", 1.1e9, "2026-05-01")]}}}}}
    extra = facts_from_ixbrl(IXBRL, "2026-08-01", "10-Q")
    rev = extra["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    assert len(rev) == 1 and rev[0]["val"] == 1234.5e6, "segment context must be skipped, scale applied"
    assert extra["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"][0]["val"] == -12e6, "sign=- negates"
    assert extra["facts"]["us-gaap"]["InventoryNet"]["units"]["USD"][0]["val"] == 0, "fixed-zero"
    merge_facts(base, extra)
    res = quarters_from_facts(base, inline_ends={"2026-06-30"})
    q = res["quarters"][-1]
    assert q["end"] == "2026-06-30" and q["revenue"] == 1234.5e6 and q["diluted_shares"] == 50.5e6 and "src" in q
    assert "src" not in res["quarters"][0]
    print("ixbrl fallback ok")


def test_edgar_session():
    from edgar import to_new_york, session_of
    et = to_new_york("2026-10-01T00:02:00.000Z")
    assert et.strftime("%Y-%m-%d %H:%M") == "2026-09-30 20:02" and session_of(et) == "amc"
    w = to_new_york("2026-12-02T12:00:00.000Z")
    assert w.hour == 7 and session_of(w) == "bmo", "EST in winter"
    assert session_of(to_new_york("2026-07-01T15:00:00.000Z")) == "intraday"
    print("edgar session ok")


if __name__ == "__main__":
    test_xbrl(); test_xbrl_q4_same_vintage(); test_catalysts(); test_dcf_and_conviction(); test_dilution_and_runway_rules(); test_peer_gm_relative_to_profile(); test_example(); test_ixbrl_fallback(); test_edgar_session()
