#!/usr/bin/env python3
"""
fact_verifier.py — THE FACT VERIFIER: the institution audits its own words
==========================================================================
The honest audit found that LLM narration (the captain's log, research
answers) garbles numbers ("ESP32 sensors read steady highs above $32").
This engine verifies every numeric claim the system writes against the
GROUND TRUTH state, and publishes an honesty score:

  1. EXTRACT  — every numeric claim + its context word from
                LLM-generated text (captain's log, research agent, ...)
  2. VERIFY   — compare each claim against the reference table built
                from the real state (engine, ALEPH, exam, portfolio,
                ESP32 stats, fitness)
  3. VERDICT  — VERIFIED (within tolerance) / CONTRADICTED / UNVERIFIABLE
  4. HONESTY  — verified / (verified + contradicted) → the institution's
                truthfulness score
  5. REMEMBER — contradictions are injected into ALEPH so the memory
                learns the narrator's failure modes; the score goes to
                the journal (§9 The Honesty Report)

The system measures its own honesty — and the score is real.
"""

import json
import os
import re
import sys
import time
import urllib.request

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
FACT_LOG = os.path.join(STATE, "fact_check.jsonl")
ALEPH = "http://127.0.0.1:8196"

# Which LLM-generated texts to audit
SOURCES = ["captains_log.jsonl", "research_agent.jsonl",
           "knowledge_decisions.jsonl"]


def build_reference() -> dict:
    """The ground-truth reference table from the real state."""
    ref = {}

    def jl(name, n=1):
        try:
            out = []
            with open(os.path.join(STATE, name)) as f:
                for line in f:
                    if line.strip():
                        out.append(json.loads(line))
            return out[-n:]
        except Exception:
            return []

    def js(name):
        try:
            with open(os.path.join(STATE, name)) as f:
                return json.load(f)
        except Exception:
            return {}

    # engine
    eng = js("are_state.json")
    ref["cycle"] = eng.get("cycle")
    ref["verified"] = eng.get("total_verified")
    ref["attempted"] = eng.get("total_attempted")
    # ALEPH
    try:
        req = urllib.request.Request(ALEPH + "/memory/stats")
        with urllib.request.urlopen(req, timeout=5) as r:
            st = json.loads(r.read().decode())
            ref["nodes"] = st.get("nodes")
            ref["edges"] = st.get("edges")
            ref["truths"] = st.get("verified")
    except Exception:
        pass
    # exam
    ex = jl("graduation_exam.jsonl")
    if ex:
        ref["exam_pct"] = round(ex[-1].get("overall", 0) * 100)
    # portfolio
    port = js("portfolio.json")
    ref["cash"] = port.get("cash")
    ref["capital"] = port.get("capital")
    # esp32 fitness + readings + last temp
    disc = jl("esp32_discovery.jsonl")
    if disc:
        ref["fitness"] = (disc[-1].get("result") or {}).get("fitness")
    day = time.strftime("%Y%m%d")
    try:
        with open(os.path.join(ARE, "real_data", f"esp32_{day}.jsonl")) as f:
            lines = [l for l in f if l.strip()]
            ref["readings"] = len(lines)
            try:
                ref["temp"] = json.loads(lines[-1])["temp_c"]
            except Exception:
                pass
    except Exception:
        pass
    # consolidation
    con = jl("memory_consolidation.jsonl")
    if con:
        ref["entries"] = con[-1].get("entries")
    return {k: v for k, v in ref.items() if v is not None}


# claim keyword → reference key (the semantic anchor for a number)
KEYWORDS = [
    (["temp", "°c", "celsius", "sensor", "silicon", "degree"], "temp"),
    (["fitness"], "fitness"),
    (["readings", "measurement", "sample"], "readings"),
    (["entries", "consolidat"], "entries"),
    (["capital", "portfolio", "10k", "10000"], "capital"),
    (["cash"], "cash"),
    (["cycle"], "cycle"),
    (["theorem", "verified", "proven"], "verified"),
    (["attempt"], "attempted"),
    (["node"], "nodes"),
    (["edge"], "edges"),
    (["truth"], "truths"),
    (["exam", "score", "percent", "%"], "exam_pct"),
]

TOLERANCE = 0.05  # ±5%


def extract_claims(text: str) -> list:
    """Pull (number, anchor-keyword) claims from text.
    The anchor is the NEAREST keyword to the number (before or after),
    not any keyword in a fixed window — this fixes mis-anchoring like
    '1725 theorems' being claimed as 'cycle' because 'cycle' appeared
    earlier in the sentence."""
    claims = []
    lower = text.lower()
    # normalize thousands separators: "10,000" -> "10000"
    text_norm = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    lower = text_norm.lower()
    for m in re.finditer(r"\d+(?:\.\d+)?(?:k)?", text_norm):
        val = float(m.group().rstrip("k")) * (1000 if m.group().endswith("k") else 1)
        num_pos = m.start()
        best, best_dist = None, 10 ** 9
        for kws, key in KEYWORDS:
            for kw in kws:
                for found in re.finditer(re.escape(kw), lower):
                    dist = abs(found.start() - num_pos)
                    if dist < best_dist:
                        best_dist, best = dist, key
        if best is not None:
            # context starting at a WORD boundary (no mid-word fragments)
            start = max(0, num_pos - 40)
            ctx = text[start:num_pos]
            if start > 0 and not ctx[0].isspace():
                sp = ctx.find(" ")
                if sp >= 0:
                    ctx = ctx[sp + 1:]
            claims.append({"value": val, "anchor": best,
                           "context": ctx[-40:].strip()})
    return claims


def verify_claims(text: str, ref: dict) -> list:
    results = []
    for c in extract_claims(text):
        truth = ref.get(c["anchor"])
        if truth is None:
            results.append({**c, "verdict": "UNVERIFIABLE"})
            continue
        if truth == 0:
            ok = abs(c["value"]) < 0.01
        else:
            ok = abs(c["value"] - truth) / abs(truth) <= TOLERANCE
        results.append({**c, "truth": truth,
                        "verdict": "VERIFIED" if ok else "CONTRADICTED"})
    return results


def audit_source(name: str, ref: dict) -> dict:
    """Audit one LLM-generated source file's latest text."""
    try:
        with open(os.path.join(STATE, name)) as f:
            lines = [l for l in f if l.strip()]
        if not lines:
            return {"source": name, "texts": 0}
        latest = json.loads(lines[-1])
        text = latest.get("text") or json.dumps(latest.get("brief", {}))
        claims = verify_claims(str(text), ref)
        return {"source": name, "texts": 1, "claims": claims,
                "verified": sum(1 for c in claims if c["verdict"] == "VERIFIED"),
                "contradicted": sum(1 for c in claims
                                    if c["verdict"] == "CONTRADICTED")}
    except Exception as e:
        return {"source": name, "error": str(e)[:60]}


def run_cycle() -> dict:
    print("=" * 60)
    print("🔍 THE FACT VERIFIER — the institution audits its own words")
    print("=" * 60)
    print("\n[1] BUILDING the ground-truth reference...")
    ref = build_reference()
    print(f"    {len(ref)} reference facts: {sorted(ref.keys())}")
    print("\n[2] AUDITING LLM-generated texts...")
    audits = []
    for src in SOURCES:
        a = audit_source(src, ref)
        audits.append(a)
        if "claims" in a:
            print(f"    {src}: {len(a['claims'])} claims, "
                  f"{a['verified']} verified, {a['contradicted']} contradicted")
            for c in a["claims"][:4]:
                print(f"      [{c['verdict']}] {c['value']} "
                      f"(truth {c.get('truth', '?')}) ctx='{c['context']}'")
        else:
            print(f"    {src}: {a.get('error', 'no text')}")
    print("\n[3] COMPUTING the honesty score...")
    verified = sum(a.get("verified", 0) for a in audits)
    contradicted = sum(a.get("contradicted", 0) for a in audits)
    total = verified + contradicted
    honesty = round(verified / total, 4) if total else None
    print(f"    {verified} verified / {contradicted} contradicted "
          f"→ honesty {honesty}")
    print("\n[4] REMEMBERING...")
    entry = {"time": time.time(), "honesty": honesty,
             "verified": verified, "contradicted": contradicted,
             "audits": audits}
    with open(FACT_LOG, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    # inject contradictions so the memory learns the narrator's failures
    for a in audits:
        for c in a.get("claims", []):
            if c["verdict"] == "CONTRADICTED":
                try:
                    payload = json.dumps({
                        "source": f"fact_verifier:{a['source']}",
                        "relation": "CONTRADICTS",
                        "target": f"claim {c['value']} vs truth {c.get('truth')}",
                        "domain": "self_audit",
                    }).encode()
                    req = urllib.request.Request(
                        ALEPH + "/memory/inject", data=payload,
                        headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=5)
                except Exception:
                    pass
    print(f"    fact_check.jsonl + ALEPH contradiction records")
    print(f"\n🔍 The institution's honesty score: {honesty}")
    return entry


if __name__ == "__main__":
    run_cycle()
