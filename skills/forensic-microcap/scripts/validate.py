"""Validate a case JSON before rendering.

Usage: python validate.py case.json
Checks required blocks, instrument fields, row widths, grade levels, and that every
{m.key} referenced in text exists in compute.py's output. Exit code 1 on errors.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute import compute  # noqa: E402

REQUIRED = {
    "meta": ["ticker", "issuer", "cik", "exchange", "report_date", "price_basis", "descriptor"],
    "market": ["prev_close", "prev_close_date", "high60", "daily"],
    "shares": ["os_primary", "non_affiliates", "splits", "ladder"],
    "financials": ["as_of", "cash", "equity", "total_assets", "opcf", "pre_wc_burn"],
    "header": ["mixed", "live", "gated", "actors", "changes"],
    "grades": ["overhead", "dilution", "frequency", "offering", "cash", "compliance"],
    "read": ["ceo_headline", "ceo", "ladder", "verdict"],
}
LISTS = {"snapshot": 2, "registrations": 5, "facilities": 5, "offerings": 8, "timeline": 3,
         "compliance": 6, "ownership": 5, "catalysts": 2, "sources": 2}
TEXTS = ["grades_note", "alert", "os_caption", "supply_caption", "capital_intro", "warrants_text",
         "convertibles_text", "legal_text"]
LIST_TEXTS = ["cash_text", "governance_text", "today_text"]


def walk(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def main(path):
    case = json.load(open(path, encoding="utf-8"))
    err, warn = [], []
    for blk, keys in REQUIRED.items():
        if blk not in case:
            err.append(f"falta bloque {blk}"); continue
        for k in keys:
            if k not in case[blk]:
                err.append(f"falta {blk}.{k}")
    for k, width in LISTS.items():
        rows = case.get(k)
        if not rows:
            err.append(f"falta lista {k}"); continue
        for i, r in enumerate(rows):
            if len(r) != width:
                err.append(f"{k}[{i}] tiene {len(r)} columnas, se esperaban {width}")
    for k in TEXTS + LIST_TEXTS:
        if k not in case:
            warn.append(f"sin texto {k}")
    for g, v in case.get("grades", {}).items():
        if v.get("level") not in ("Alto", "Medio", "Bajo"):
            err.append(f"grades.{g}.level inválido: {v.get('level')}")
    ids = set()
    for i in case.get("instruments", []):
        for k in ("id", "name", "gate", "gate_label", "arming"):
            if k not in i:
                err.append(f"instrumento sin {k}: {i.get('id')}")
        if i.get("id") in ids:
            err.append(f"id duplicado {i['id']}")
        ids.add(i.get("id"))
        if i.get("gate") not in ("live", "gated", "price", "issued"):
            err.append(f"gate inválido en {i.get('id')}")
        model = i.get("supply", {}).get("model", "fixed")
        if model == "fixed" and "shares_max" not in i:
            err.append(f"{i.get('id')}: modelo fixed sin shares_max")
    if len(case.get("market", {}).get("daily", [])) < 20:
        warn.append("menos de 20 sesiones en market.daily")
    if not err:
        m, _ = compute(case)
        refs = set(re.findall(r"\{m\.([A-Za-z0-9_]+)", " ".join(walk(case))))
        for r in sorted(refs - set(m)):
            err.append(f"métrica citada que no existe: {r}")
        nver = sum(s.count("[VERIFY") for s in walk(case))
        print(f"métricas: {len(m)} · citadas: {len(refs)} · VERIFY: {nver}")
    for w in warn:
        print("AVISO", w)
    for e in err:
        print("ERROR", e)
    print("OK" if not err else f"{len(err)} errores")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
