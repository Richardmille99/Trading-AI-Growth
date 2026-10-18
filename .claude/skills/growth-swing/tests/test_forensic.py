"""Offline test for scripts/forensic.py on a synthetic companyfacts fixture.
Run: python tests/test_forensic.py   (from the skill folder)
"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from forensic import analyze  # noqa: E402


def test_analyze():
    inst = lambda end, val, filed: dict(end=end, val=val, filed=filed, form="10-Q")
    facts = {"facts": {"us-gaap": {
        "Goodwill": {"units": {"USD": [inst("2026-03-31", 100, "2026-05-01"), inst("2026-06-30", 120, "2026-08-01")]}},
        "IntangibleAssetsNetExcludingGoodwill": {"units": {"USD": [inst("2026-06-30", 30, "2026-08-01")]}},
        "StockholdersEquity": {"units": {"USD": [inst("2026-06-30", 300, "2026-08-01")]}},
        "Assets": {"units": {"USD": [inst("2026-06-30", 1000, "2026-08-01")]}},
        "GoodwillImpairmentLoss": {"units": {"USD": [dict(start="2025-04-01", end="2025-06-30", val=42, filed="2025-08-01")]}}},
        "dei": {"EntityPublicFloat": {"units": {"USD": [dict(end="2026-01-30", val=2.0e9, filed="2026-03-01", form="10-K")]}}}}}
    filings = {"filings": [dict(filed="2026-02-10", form="8-K", items="5.02,9.01", accession="a", url="u"),
                           dict(filed="2026-02-11", form="8-K", items="2.02,9.01", accession="b", url="u"),
                           dict(filed="2023-01-01", form="8-K", items="4.01", accession="c", url="u")]}
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
        fh.write("date,open,high,low,close,adj_close,volume\n2026-01-29,1,1,1,40,40,1\n2026-01-30,1,1,1,50,50,1\n")
    r = analyze(facts, filings, fh.name, "2024-10-01")
    os.unlink(fh.name)
    assert r["balance"]["goodwill"]["val"] == 120 and abs(r["goodwill_intang_to_equity"] - 0.5) < 1e-9
    assert r["public_float"]["float_shares"] == 40_000_000 and r["public_float"]["close_date"] == "2026-01-30"
    assert [g["items"] for g in r["governance"]] == [["5.02"]], "only governance items, only since the cut-off"
    assert r["impairments"][0]["val"] == 42
    print("forensic ok")


if __name__ == "__main__":
    test_analyze()
