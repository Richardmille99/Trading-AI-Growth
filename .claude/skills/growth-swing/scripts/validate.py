"""Validate a growth-swing case JSON before rendering.

Usage: python validate.py case.json
Exit 1 with a list of errors; warnings never block.
"""
import json, os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TYPES = {"gov_contract", "commercial_contract", "partnership", "product", "financing", "earnings", "mna", "index_analyst", "other"}
BINDING = {"definitive", "purchase_order", "award_funded", "award_unfunded", "idiq_ceiling", "option_exercise", "loi", "mou",
           "partnership_undefined", "none"}
HISTORY = {"converted", "partial", "not_converted", "unknown"}
FIN = {"atm", "registered_direct", "underwritten", "convertible", "pipe", "strategic", "debt"}
KINDS = {"atm", "shelf", "secondary", "convertible", "warrants", "lockup", "insider", "sbc", "pipe_resale"}
GATES = {"live", "gated", "dated"}
SETUPS = {"ep", "breakout_flag", "vcp", "momentum_burst", "wedge_pop", "ema_crossback", "base_n_break", "exhaustion_watch"}
REGIMES = {"risk_on", "neutral", "risk_off", "unknown"}


def validate(case):
    E, W = [], []
    profiles = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sector_profiles.json"), encoding="utf-8"))
    meta = case.get("meta", {})
    for k in ("ticker", "issuer", "exchange", "report_date", "profile"):
        if not meta.get(k):
            E.append(f"meta.{k} falta")
    if meta.get("profile") and meta["profile"] not in profiles:
        E.append(f"meta.profile '{meta['profile']}' no existe en sector_profiles.json")
    try:
        date.fromisoformat(meta.get("report_date", ""))
    except ValueError:
        E.append("meta.report_date no es AAAA-MM-DD")
    mk = case.get("market", {})
    if mk.get("regime", "unknown") not in REGIMES:
        E.append(f"market.regime inválido: {mk.get('regime')}")
    if mk.get("price") is None:
        W.append("market.price vacío: valoración, oferta a precio actual y DCF inverso saldrán n/d")

    q = case.get("financials", {}).get("quarters", [])
    if len(q) < 5:
        E.append(f"financials.quarters: {len(q)} trimestres; mínimo 5 para interanual (8 para TTM interanual)")
    elif len(q) < 8:
        W.append("menos de 8 trimestres: TTM interanual, Rule of 40 y accruals saldrán n/d")
    ends = [x.get("end") for x in q]
    if ends != sorted(ends):
        E.append("financials.quarters no está ordenado de antiguo a reciente")
    for i, x in enumerate(q):
        if x.get("revenue") is None:
            if x.get("gap") and x.get("gap_note") and 0 < i < len(q) - 1:
                W.append(f"trimestre {x.get('period')}: sin datos publicados ({x['gap_note']}); TTM y métricas que lo usan saldrán n/d")
            else:
                E.append(f"trimestre {x.get('period')}: revenue vacío" + (" (un hueco con gap: true solo vale entre trimestres con datos)" if x.get("gap") else ""))
    if not case.get("financials", {}).get("shares_out"):
        W.append("financials.shares_out vacío: sin market cap")

    ids = set()
    for c in case.get("catalysts", []):
        cid = c.get("id")
        if not cid or not re.fullmatch(r"[A-Za-z0-9_]+", cid):
            E.append(f"catalizador sin id válido: {c.get('headline')}")
        if cid in ids:
            E.append(f"id de catalizador duplicado: {cid}")
        ids.add(cid)
        if c.get("type") not in TYPES:
            E.append(f"{cid}: type inválido {c.get('type')}")
        if not c.get("date"):
            E.append(f"{cid}: date falta")
        if not c.get("sources"):
            W.append(f"{cid}: sin fuentes")
        if c.get("type") in ("gov_contract", "commercial_contract", "partnership", "product", "mna", "other"):
            if c.get("binding", "none") not in BINDING:
                E.append(f"{cid}: binding inválido {c.get('binding')}")
            if c.get("issuer_history", "unknown") not in HISTORY:
                E.append(f"{cid}: issuer_history inválido")
            if c.get("binding") == "idiq_ceiling" and c.get("value_firm") and c.get("value_firm") == c.get("value_ceiling"):
                W.append(f"{cid}: IDIQ con value_firm = techo; ¿es realmente valor obligado?")
        if c.get("type") == "financing" and c.get("financing_type") not in FIN:
            E.append(f"{cid}: financing_type inválido")
    pc = meta.get("primary_catalyst")
    if pc and pc not in ids:
        E.append(f"meta.primary_catalyst '{pc}' no está en catalysts")

    for s in case.get("supply", []):
        if s.get("kind") not in KINDS:
            E.append(f"supply {s.get('id')}: kind inválido {s.get('kind')}")
        if s.get("gate") not in GATES:
            E.append(f"supply {s.get('id')}: gate inválido {s.get('gate')}")
        if s.get("kind") == "lockup" and not s.get("date"):
            E.append(f"supply {s.get('id')}: lock-up sin fecha")
        if s.get("kind") == "atm" and s.get("capacity_usd") is None:
            W.append(f"supply {s.get('id')}: ATM sin capacity_usd (se trata como agotado)")
    if not case.get("supply_context", {}).get("float_shares"):
        W.append("supply_context.float_shares vacío: % del float y lock-ups saldrán n/d")

    st = case.get("setup", {})
    if st.get("type") and st["type"] not in SETUPS:
        E.append(f"setup.type inválido {st['type']}")
    if st.get("pivot") and st.get("stop") and st["stop"] >= st["pivot"]:
        E.append("setup.stop ≥ pivot")
    if len(case.get("peers", [])) < 3:
        W.append("menos de 3 pares: la posición en el grupo será 'unknown'")
    if st.get("rs_3m") is None:
        W.append("setup.rs_3m vacío: la posición en el grupo será 'unknown'")
    for e in case.get("events", []):
        try:
            date.fromisoformat(e.get("date", ""))
        except ValueError:
            E.append(f"evento con fecha inválida: {e}")

    # every {m.key} referenced must exist after compute
    if not E:
        from compute import compute
        m, _, _ = compute(case)
        refs = set(re.findall(r"\{m\.([A-Za-z0-9_]+)", json.dumps(case, ensure_ascii=False)))
        miss = sorted(refs - set(m))
        if miss:
            E.append(f"métricas referenciadas que no existen: {miss}")
        nulls = sorted(k for k in refs & set(m) if m[k] is None)
        if nulls:
            W.append(f"métricas referenciadas que salen n/d: {nulls}")
    return E, W


def main():
    case = json.load(open(sys.argv[1], encoding="utf-8"))
    E, W = validate(case)
    for w in W:
        print("AVISO:", w)
    for e in E:
        print("ERROR:", e)
    print("OK" if not E else f"{len(E)} errores")
    sys.exit(1 if E else 0)


if __name__ == "__main__":
    main()
