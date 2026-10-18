"""Offline tests for scripts/insiders.py on synthetic EDGAR XML (no network).
Run: python tests/test_insiders.py   (from the skill folder)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from insiders import parse_144, parse_13, parse_form4, summarize_form4  # noqa: E402


def f4(owner, rows, plan_box="0", footnote=""):
    tx = "".join(f"""<nonDerivativeTransaction><transactionDate><value>{d}</value></transactionDate>
      <transactionCoding><transactionCode>{c}</transactionCode></transactionCoding>
      <transactionAmounts><transactionShares><value>{s}</value></transactionShares>
      <transactionPricePerShare><value>{p}</value>{'<footnoteId id="F1"/>' if footnote else ''}</transactionPricePerShare>
      <transactionAcquiredDisposedCode><value>{'D' if c in 'SF' else 'A'}</value></transactionAcquiredDisposedCode></transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>{a}</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
      <ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
      </nonDerivativeTransaction>""" for d, c, s, p, a in rows)
    fn = f'<footnotes><footnote id="F1">{footnote}</footnote></footnotes>' if footnote else ""
    return f"""<?xml version="1.0"?><ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>{owner}</rptOwnerName>
      </reportingOwnerId><reportingOwnerRelationship><isDirector>0</isDirector><isOfficer>1</isOfficer>
      <officerTitle>CFO</officerTitle></reportingOwnerRelationship></reportingOwner><aff10b5One>{plan_box}</aff10b5One>
      <nonDerivativeTable>{tx}</nonDerivativeTable>{fn}</ownershipDocument>"""


def doc(xml, acc):
    d = parse_form4(xml)
    d.update(accession=acc, filed="2026-09-01")
    return d


def test_form4():
    plan = doc(f4("Ann", [("2026-08-01", "S", 1000, 50, 99000)], plan_box="1"), "a1")
    assert plan["transactions"][0]["plan"]
    off = doc(f4("Bob", [("2026-08-01", "S", 5000, 50, 20000), ("2026-08-02", "F", 300, 50, 19700)]), "b1")
    foot = doc(f4("Cid", [("2026-08-01", "S", 100, 50, 10000)], footnote="Sold under a Rule 10b5-1 trading plan adopted on May 1"), "c1")
    buy = doc(f4("Dee", [("2026-08-01", "P", 2000, 40, 12000)], plan_box="0"), "d1")
    rows = {r["name"]: r for r in summarize_form4([plan, off, foot, buy])}
    assert not rows["Ann"]["flagged"] and rows["Ann"]["max_quarter_pct"] < .02
    assert rows["Bob"]["flagged"] and rows["Bob"]["off_plan_sales"] and abs(rows["Bob"]["max_quarter_pct"] - 5000 / 24700) < 1e-4
    assert rows["Bob"]["tax_withheld"] == 300, "F is counted apart, never as a sale"
    assert not rows["Cid"]["flagged"], "10b5-1 footnote counts as plan"
    assert rows["Dee"]["bought"] == 2000 and not rows["Dee"]["flagged"]
    big = doc(f4("Eve", [("2026-08-01", "S", 3000, 50, 10000)], plan_box="1"), "e1")
    assert summarize_form4([big])[0]["flagged"], "under plan but 23% of the position in a quarter"
    trust = f4("Fay", [("2026-08-01", "S", 1000, 50, 0)]).replace("</nonDerivativeTable>",
        "<nonDerivativeHolding><securityTitle><value>Common Stock</value></securityTitle><postTransactionAmounts>"
        "<sharesOwnedFollowingTransaction><value>99000</value></sharesOwnedFollowingTransaction></postTransactionAmounts>"
        "<ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>"
        "</nonDerivativeHolding></nonDerivativeTable>")
    r = summarize_form4([doc(trust, "f1")])[0]
    assert abs(r["max_quarter_pct"] - 0.01) < 1e-4, "a trust emptied, but the direct holding remains"
    print("form 4 ok")


def test_144_and_13():
    x144 = """<?xml version="1.0"?><ns2:edgarSubmission xmlns:ns2="http://www.sec.gov/edgar/ownership"><ns2:formData>
      <ns2:issuerInfo><ns2:nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>Kim</ns2:nameOfPersonForWhoseAccountTheSecuritiesAreToBeSold>
      <ns2:relationshipsToIssuer><ns2:relationshipToIssuer>Officer</ns2:relationshipToIssuer></ns2:relationshipsToIssuer></ns2:issuerInfo>
      <ns2:securitiesInformation><ns2:noOfUnitsSold>1500</ns2:noOfUnitsSold><ns2:aggregateMarketValue>75000</ns2:aggregateMarketValue>
      <ns2:noOfUnitsOutstanding>9000000</ns2:noOfUnitsOutstanding><ns2:approxSaleDate>08/17/2026</ns2:approxSaleDate>
      </ns2:securitiesInformation></ns2:formData></ns2:edgarSubmission>"""
    r = parse_144(x144)
    assert r["person"] == "Kim" and r["shares"] == 1500 and r["approx_date"] == "08/17/2026" and not r["plan_10b5_1"]
    x13 = """<?xml version="1.0"?><edgarSubmission xmlns="http://www.sec.gov/edgar/schedule13g"><formData><coverPageHeader>
      <eventDateRequiresFilingThisStatement>06/30/2026</eventDateRequiresFilingThisStatement></coverPageHeader>
      <coverPageHeaderReportingPersonDetails><reportingPersonName>BIG FUND</reportingPersonName>
      <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>4325471.00</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
      <classPercent>4.8</classPercent></coverPageHeaderReportingPersonDetails></formData></edgarSubmission>"""
    r = parse_13(x13)
    assert r["persons"][0] == dict(name="BIG FUND", shares=4325471.0, pct=4.8) and r["event_date"] == "06/30/2026"
    print("144 + 13G ok")


if __name__ == "__main__":
    test_form4(); test_144_and_13()
