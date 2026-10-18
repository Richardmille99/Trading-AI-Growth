"""Offline tests for scripts/prices.py on synthetic CSVs (no network).
Run: python tests/test_prices.py   (from the skill folder)
"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from prices import (reaction, adr_pct, candidates, cooled_leader, ema, metrics, percentile, read_csv, regime_proxy,  # noqa: E402
                    rs_table, write_csv)


def series(closes, rng=0.02, vol=1e6, start=(2025, 1, 1)):
    """Synthetic sessions: high/low = close ± rng/2, open = previous close."""
    from datetime import date, timedelta
    d, out, prev = date(*start), [], closes[0]
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        out.append(dict(date=d.isoformat(), open=prev, high=c * (1 + rng / 2), low=c * (1 - rng / 2), close=c, adj_close=c,
                        volume=vol))
        prev, d = c, d + timedelta(days=1)
    return out


def test_indicators_and_csv():
    rows = series([100.0] * 300)
    m = metrics(rows)
    assert abs(m["ema10"] - 100) < 1e-9 and abs(m["sma200"] - 100) < 1e-9
    assert abs(adr_pct(rows) - (1.01 / 0.99 - 1) * 100) < 1e-9
    assert m["ret"]["12m"] == 0 and m["ema_stack"] is False  # flat: 10 > 20 > 50 does not hold
    assert ema([1, 2, 3], 5) is None
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "X", "prices.csv")
        write_csv(p, rows)
        back = read_csv(p)
        assert len(back) == 300 and back[-1]["close"] == 100.0
    up = metrics(series([100 * 1.01 ** i for i in range(300)]))
    assert up["ema_stack"] is True and abs(up["ret"]["1m"] - (1.01 ** 21 - 1)) < 1e-9
    print("indicators + csv ok")


def test_rs_percentile():
    assert percentile(5, [1, 2, 3, 4]) == 100 and percentile(1, [1, 2, 3, 4]) == 12.5 and percentile(None, [1]) is None
    M = {t: dict(ret={"1m": r, "3m": r, "6m": r, "12m": r}) for t, r in (("A", .1), ("B", .2), ("C", .3))}
    RS = rs_table(M)
    assert RS["C"]["1m"] == 100 and RS["A"]["1m"] == 0 and RS["B"]["3m"] == 50
    print("rs ok")


def _m(r12, r1, r3, dd, vs200):
    return dict(ret={"1m": r1, "3m": r3, "6m": 0, "12m": r12}, dd_52w=dd, vs_sma200=vs200)


def test_cooled_leader():
    M = {"L": _m(1.5, -.1, -.2, -.30, .02), "B": _m(.1, .1, .1, -.05, .2), "C": _m(.2, .2, .2, -.05, .2),
         "D": _m(.3, .3, .3, -.05, .2)}
    RS = rs_table(M)
    U = list(M)
    assert cooled_leader("L", M, RS, U, (0.0, 60)) == "cooled_leader"
    assert cooled_leader("L", M, RS, U, (-8.0, 60)) == "cooled_leader_broken", "deceleration > 3 pp breaks it"
    assert cooled_leader("L", M, RS, U, (0.0, 40)) == "cooled_leader_broken", "fund score < 45 breaks it"
    assert cooled_leader("L", M, RS, U, None) is None, "no case yet → not evaluated"
    M["L"]["dd_52w"] = -.60
    assert cooled_leader("L", M, RS, U, (0.0, 60)) is None, "drawdown beyond 50% is not 'cooled'"
    M["L"]["dd_52w"], M["L"]["vs_sma200"] = -.30, -.15
    assert cooled_leader("L", M, RS, U, (0.0, 60)) is None, "more than 10% below the 200-day"
    assert cooled_leader("B", M, RS, U, (0.0, 60)) is None
    print("cooled leader ok")


def test_candidates_and_regime():
    rows = series([100.0] * 100)
    last = rows[-1]
    rows.append(dict(date="2099-01-01", open=112.0, high=118.0, low=110.0, close=116.0, adj_close=116.0, volume=5e6))
    c = candidates(rows, metrics(rows))
    ep = [x for x in c if x["type"] == "ep"]
    assert ep and ep[0]["pivot"] == 118.0 and ep[0]["stop"] == 110.0, c
    assert not [x for x in candidates(series([100.0] * 100), metrics(series([100.0] * 100))) if x["type"] == "ep"]
    assert last["close"] == 100.0
    up = metrics(series([100 * 1.01 ** i for i in range(120)]))
    dn = metrics(series([100 * 0.99 ** i for i in range(120)]))
    assert regime_proxy({"QQQ": up, "IWM": up})[0] == "risk_on"
    assert regime_proxy({"QQQ": dn, "IWM": dn})[0] == "risk_off"
    assert regime_proxy({"QQQ": up, "IWM": dn})[0] == "neutral"
    assert regime_proxy({"QQQ": up})[0] == "unknown"
    rx = reaction(rows, rows[-2]["date"], "amc")
    assert rx["gap_pct"] == 12.0 and rx["rvol"] == 5.0 and rx["reaction_date"] == "2099-01-01" and rx["day2_follow"] is None
    assert reaction(rows, "2099-01-02", "amc") is None, "not traded yet"
    print("candidates + regime + reaction ok")


if __name__ == "__main__":
    test_indicators_and_csv(); test_rs_percentile(); test_cooled_leader(); test_candidates_and_regime()
