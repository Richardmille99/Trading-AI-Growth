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
    assert conviction("A", 80, 70, "leader", "risk_on", False, "ep")[0] == "Alta"
    assert conviction("A", 80, 70, "unknown", "risk_on", False, "ep")[0] == "Media"
    assert conviction("A", 80, 70, "leader", "risk_off", False, "ep")[0] == "Baja"
    assert conviction("A", 80, 30, "leader", "risk_on", False, "ep")[0] == "Descartar"
    assert conviction("B", 80, 70, "leader", "risk_on", True, "vcp")[0] == "Descartar"
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


def test_example():
    case = json.load(open(os.path.join(HERE, "..", "examples", "EXMP_synthetic.json"), encoding="utf-8"))
    m, R, _ = compute(case)
    assert R["primary"]["grade"] == "A" and R["supply"]["total"] == 55 and R["group"] == "leader"
    assert R["conviction"] == "Media" and round(m["fund_score"]) == 83
    print("example ok")


if __name__ == "__main__":
    test_xbrl(); test_catalysts(); test_dcf_and_conviction(); test_dilution_and_runway_rules(); test_example()
