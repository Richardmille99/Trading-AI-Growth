"""Offline tests for casekit, new_case helpers, consensus, market breadth, regime with breadth, journal, site and profiles.
Run: python tests/test_tools.py   (from the skill folder)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
from test_prices import series  # noqa: E402


def _q(end, rev, gp):
    return dict(end=end, period=end[:7], revenue=rev, gross_profit=gp)


def test_casekit():
    from casekit import contract, earnings, growth_at, usd_m
    q = [_q("2025-03-31", 100, 40), _q("2025-06-30", 100, 40), _q("2025-09-30", 110, 44), _q("2025-12-31", 120, 48),
         _q("2026-03-31", 150, 75), _q("2026-06-30", 180, 99)]
    gy, gyp, bp = growth_at(q, "2026-06-30")
    assert abs(gy - .8) < 1e-9 and abs(gyp - .5) < 1e-9 and bp == 1500
    assert growth_at(q, "2025-06-30") == (None, None, None)
    rows = series([100.0] * 60)
    rows.append(dict(date="2099-01-02", open=110.0, high=115.0, low=108.0, close=114.0, adj_close=114.0, volume=3e6))
    c = earnings(dict(financials=dict(quarters=q)), rows, "q2", "2026-06-30", rows[-2]["date"], "amc", "R", ["8-K", "u"])
    assert c["sources"] == [["8-K", "u"]] and c["gap_pct"] == 10.0 and c["rvol"] == 3.0 and c["time_et"] == "after-hours"
    c2 = earnings(dict(financials=dict(quarters=q)), rows, "q2", "2026-06-30", "2099-02-01", "amc", "R", [["8-K", "u"]])
    assert "gap_pct" not in c2, "not traded yet → no reaction fields"
    k = contract("x", "2026-01-01", "h", [], binding="definitive", value_firm=1e8)
    assert k["binding"] == "definitive" and k["counterparty"] is None and k["type"] == "commercial_contract"
    assert usd_m(50_400_000) == "$50,4M" and usd_m(6.5e9) == "$6.500,0M"
    print("casekit ok")


def test_new_case_helpers():
    from new_case import last_earnings_8k, quarter_for
    idx = dict(filings=[dict(form="4", items=None), dict(form="8-K", items="5.02"), dict(form="8-K", items="2.02,9.01", filed="2026-08-05"),
                        dict(form="8-K", items="2.02", filed="2026-05-05")])
    assert last_earnings_8k(idx)["filed"] == "2026-08-05"
    from new_case import same_day_earnings_8ks
    idx["filings"].insert(0, dict(form="8-K", items="2.02,5.02,9.01", filed="2026-08-05"))
    assert len(same_day_earnings_8ks(idx, last_earnings_8k(idx))) == 2
    q = [_q("2026-03-31", 1, 1), _q("2026-06-30", 1, 1)]
    assert quarter_for(q, "2026-08-05")["end"] == "2026-06-30"
    assert quarter_for(q, "2026-06-30")["end"] == "2026-03-31", "a release on the quarter-end day reports the previous quarter"
    assert quarter_for(q, "2027-01-15") is None, "more than 100 days after the last quarter → companyfacts is behind"
    print("new_case helpers ok")


FINVIZ = """<table class="snapshot-table2"><tr>
<td class="snapshot-td2 cursor-pointer w-[7%]" align="left"><a>EPS next Q</a></td><td class="snapshot-td2 w-[8%]"><b>3.05</b></td>
<td class="snapshot-td2 cursor-pointer"><a>EPS/Sales Surpr.</a></td><td class="snapshot-td2"><b><span class="color-text is-positive">12.35%</span> <span>-1.20%</span></b></td>
<td class="snapshot-td2 cursor-pointer">Earnings</td><td class="snapshot-td2"><b><small>Dec 17 AMC</small></b></td>
</tr><tr><td class="snapshot-td2">Target Price</td><td class="snapshot-td2"><b>245.10</b></td>
<td class="snapshot-td2">Recom</td><td class="snapshot-td2"><b>1.45</b></td>
<td class="snapshot-td2">Short Float</td><td class="snapshot-td2"><b>2.31%</b></td>
<td class="snapshot-td2">Shs Float</td><td class="snapshot-td2"><b>1.11B</b></td></tr></table>"""


def test_consensus():
    from consensus import earnings_date, num, parse, snapshot
    s = snapshot(FINVIZ)
    assert s["EPS next Q"] == "3.05" and s["Earnings"] == "Dec 17 AMC" and s["EPS/Sales Surpr."] == "12.35% -1.20%"
    p = parse(s, "2026-10-18")
    assert p["eps_next_q"] == 3.05 and p["eps_surprise_pct"] == 12.35 and p["sales_surprise_pct"] == -1.2
    assert p["earnings_date"] == "2026-12-17" and p["earnings_session"] == "amc" and p["target_price"] == 245.1
    assert p["short_float_pct"] == 2.31 and p["eps_this_y"] is None and num(s["Shs Float"]) == 1.11e9
    assert earnings_date("Jan 28 BMO", "2026-12-20") == ("2027-01-28", "bmo"), "year closest to today"
    assert earnings_date("Oct 30", "2026-12-20") == ("2026-10-30", None)
    assert earnings_date("-", "2026-10-18") == (None, None)
    print("consensus ok")


def _members(n_up, n_down, days=70):
    """n_up members rising 1%/day; n_down members falling 1%/day with a −5% day near the end."""
    S = {}
    for i in range(n_up):
        S[f"U{i}"] = series([100 * 1.01 ** k for k in range(days)])
    for i in range(n_down):
        closes = [100 * 0.99 ** k for k in range(days)]
        closes[-2] = closes[-3] * 0.95
        closes[-1] = closes[-2] * 0.99
        S[f"D{i}"] = series(closes)
    return S


def test_breadth_and_regime():
    from market import breadth, state
    from prices import metrics, regime_proxy
    b = breadth(_members(8, 2), days=3)[-1]
    assert b["n"] == 10 and b["pct_above_sma50"] == 80.0 and b["down4_5d"] == 2 and b["up4_5d"] == 0
    assert b["ratio_10d"] == 0.0 and state(b) == "strong", "only 2 moves of ±4%: the ratio does not count"
    w = breadth(_members(3, 7), days=3)[-1]
    assert w["pct_above_sma50"] == 30.0 and state(w) == "weak"
    assert breadth(_members(5, 5), days=1)[-1]["state"] == "weak", "50% over SMA 50 but 0 up / 5 down moves"
    assert state(dict(pct_above_sma50=50, ratio_10d=1.0, up4_10d=3, down4_10d=3)) == "mixed"
    up = metrics(series([100 * 1.01 ** i for i in range(120)]))
    dn = metrics(series([100 * 0.99 ** i for i in range(120)]))
    M = {"QQQ": up, "IWM": up}
    assert regime_proxy(M)[0] == "risk_on" and "Sin amplitud" in regime_proxy(M)[1]
    assert regime_proxy(M, breadth=dict(state="weak", pct_above_sma50=35, evidence="x"))[0] == "neutral"
    assert regime_proxy({"QQQ": dn, "IWM": dn}, breadth=dict(state="strong", pct_above_sma50=70))[0] == "neutral"
    assert regime_proxy({"QQQ": up, "IWM": dn}, breadth=dict(state="weak", pct_above_sma50=25))[0] == "risk_off"
    assert regime_proxy({"QQQ": up, "IWM": dn}, breadth=dict(state="weak", pct_above_sma50=35))[0] == "neutral"
    assert regime_proxy({"QQQ": dn, "IWM": dn}, breadth=dict(state="mixed", pct_above_sma50=45))[0] == "risk_off"
    print("breadth + regime ok")


def test_journal_outcome():
    from journal import outcome
    closes = [100.0] * 10 + [101 + k for k in range(70)]
    rows = series(closes, rng=0.0)
    fecha = rows[9]["date"]
    o = outcome(rows, fecha, pivot=100.5, stop=95.5)
    # first session after `fecha` has open 100, high 101 ≥ 100.5 → entry 100.5, risk 5
    assert o["salida"].startswith("activada") and o["mfe_5d_R"] == round((105 - 100.5) / 5, 2) and o["mae_5d_R"] == 0.1
    assert o["cierre_20d_R"] == round((120 - 100.5) / 5, 2) and "mfe_60d_R" in o
    assert outcome(series([100.0] * 20, rng=0.0), rows[2]["date"], 110, 95) == dict(salida="no activada")
    assert outcome(rows, rows[-1]["date"], 200, 150) == {}, "no sessions yet"
    short = outcome(series([100.0] * 3 + [101.0] * 3, rng=0.0), series([100.0] * 3)[2]["date"], 100.5, 95.5)
    assert "mfe_5d_R" not in short and short["salida"].startswith("activada"), "window incomplete → left empty"
    print("journal ok")


def test_site_markdown():
    from sitepage import markdown
    h = markdown("# T\n\nUn **dato** con `code`.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n- uno\n- dos\n")
    assert "<h2>T</h2>" in h and "<b>dato</b>" in h and "<code>code</code>" in h
    assert "<th>a</th>" in h and "<td>2</td>" in h and "---" not in h and h.count("<li>") == 2
    print("site ok")


def test_validate_gap_quarter():
    from validate import validate
    case = json.load(open(os.path.join(HERE, "..", "examples", "EXMP_synthetic.json"), encoding="utf-8"))
    q = case["financials"]["quarters"]
    mid = dict(q[3], revenue=None, gross_profit=None)
    q[3] = mid
    errs, _ = validate(case)
    assert any("revenue vacío" in e for e in errs), "a silent hole is an error"
    mid.update(gap=True, gap_note="no publicado")
    errs, warns = validate(case)
    assert not any("revenue vacío" in e for e in errs) and any("sin datos publicados" in w for w in warns)
    q[-1] = dict(q[-1], revenue=None, gap=True, gap_note="x")
    assert any("revenue vacío" in e for e in validate(case)[0]), "the last quarter can never be a gap"
    print("validate gap ok")


def test_profiles():
    p = json.load(open(os.path.join(HERE, "..", "assets", "sector_profiles.json"), encoding="utf-8"))
    for k, v in p.items():
        if k.startswith("_"):
            continue
        assert abs(sum(v["weights"].values()) - 1) < 1e-9, k
        assert set(v["weights"]) == {"growth", "accel", "gross_margin", "rule40", "op_leverage", "quality"}, k
        assert 0 < v["fcf_target"] < 1 and ("gm_target" not in v or 0 < v["gm_target"] < 1), k
    assert p["semis_memory"]["gm_target"] == 0.40
    print("profiles ok")


if __name__ == "__main__":
    test_casekit(); test_new_case_helpers(); test_consensus(); test_breadth_and_regime(); test_journal_outcome()
    test_site_markdown(); test_validate_gap_quarter(); test_profiles()
