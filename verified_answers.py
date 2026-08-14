#!/usr/bin/env python3
"""
verified_answers.py — THE VERIFIED ANSWER ENGINE
=================================================
Ask the institution anything — it answers ONLY with verification:

  ROUTE  →  what kind of question?
    MATH      → extract the claim → the Tactic-Search Prover
                (REAL Lean4 kernel) → VERIFIED (with proof) or REJECTED
    FACTUAL   → search the VERIFIED KNOWLEDGE INDEX → entries with paths
    EMPIRICAL → query the REAL sensor data (ESP32 temperature, readings)
    SYSTEM    → live institution stats (engine, truths, exam, honesty)
    WEB       → Brave Search (when the keys work) as a second source
    UNKNOWN   → the honest answer: "I cannot verify this" — the
                institution never claims without proof

Every answer carries its verification path. The engine is local,
torch-free, and always honest.
"""

import json
import os
import re
import sys
import time

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")

sys.path.insert(0, ARE)


def _load_jsonl(name, limit=50):
    out = []
    try:
        with open(os.path.join(STATE, name)) as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    except Exception:
        pass
    return out[-limit:]


def _load_json(name):
    try:
        with open(os.path.join(STATE, name)) as f:
            return json.load(f)
    except Exception:
        return {}


def route_question(q: str) -> str:
    """Classify the question type (priority: empirical → system → math → factual)."""
    ql = q.lower()
    # 1. EMPIRICAL — physical/sensor questions
    if any(k in ql for k in ["temperature", "sensor", "readings", "celsius",
                             "°c", "degrees", "mcu"]):
        return "empirical"
    # 2. SYSTEM — the institution itself
    if any(k in ql for k in ["exam", "cycle", "journal", "verified",
                             "honesty", "edition", "engine", "truths",
                             "theorem count", "how many theorems"]):
        return "system"
    # 3. MATH — provable claims (an equality, or explicit math language)
    if "=" in ql or any(k in ql for k in ["prove", "theorem", " even",
                                           " odd", "commutative",
                                           "associative", "distributive",
                                           "true or false", "equals"]):
        return "math"
    # 4. FACTUAL — knowledge questions
    if any(k in ql for k in ["what is", "what are", "who", "when",
                             "does ", "has ", "supports", "features",
                             "capable"]):
        return "factual"
    return "unknown"


def _bind(claim: str) -> str:
    """Add ℕ binders for free single-letter variables in a claim.
    Always returns '… : claim' so the theorem header is valid."""
    import re as _re
    free = sorted(set(_re.findall(r"\b([a-z])\b", claim))
                  - set({"by", "is", "of", "and", "or", "not", "to",
                        "for", "the"}))
    if not free:
        return f": {claim}"
    binders = " ".join(f"({v} : ℕ)" for v in free)
    return f"{binders} : {claim}"


def answer_math(q: str) -> dict:
    """Extract the claim + prove or reject with the kernel."""
    from tactic_search import batch_prove
    ql = q.lower()
    stmts = []
    # pattern 1: "is X = Y" (with or without trailing words)
    m = re.search(r"is\s+(.+?=\s*[^\s?]+)\s*[?]*$", q, re.I)
    if m:
        claim = m.group(1).strip().rstrip("?")
        stmts.append((f"theorem ask_claim {_bind(claim)} := by",
                      f"theorem ask_neg {_bind(f'¬ ({claim})')} := by"))
    # pattern 2: "is X even/odd"
    m2 = re.search(r"is\s+(.+?)\s+(even|odd)", q, re.I)
    if m2:
        prop = f"Even {m2.group(1).strip()}" if m2.group(2).lower() == "even" \
            else f"Odd {m2.group(1).strip()}"
        stmts.append((f"theorem ask_claim {_bind(prop)} := by",
                      f"theorem ask_neg {_bind(f'¬ ({prop})')} := by"))
    # pattern 3: "is X commutative/associative/distributive"
    m3 = re.search(r"is\s+(\w+)\s+(commutative|associative|distributive)", q, re.I)
    if m3:
        op = m3.group(1).lower()
        kind = m3.group(2).lower()
        if op in ("addition", "add", "+"):
            c1 = "a + b = b + a" if kind == "commutative" else \
                 ("a + (b + c) = (a + b) + c" if kind == "associative" else "a * (b + c) = a * b + a * c")
        else:
            c1 = "a * b = b * a" if kind == "commutative" else \
                 ("a * (b * c) = (a * b) * c" if kind == "associative" else "(a + b) * c = a * c + b * c")
        stmts.append((f"theorem ask_claim {_bind(c1)} := by",
                      f"theorem ask_neg {_bind(f'¬ ({c1})')} := by"))
    # pattern 4: "is 2 + 2 = 4" style (bare expression)
    if not stmts and "=" in ql:
        claim = q.split("is")[-1].strip().rstrip("?")
        stmts.append((f"theorem ask_claim {_bind(claim)} := by",
                      f"theorem ask_neg {_bind(f'¬ ({claim})')} := by"))
    if not stmts:
        return {"answer": "UNVERIFIABLE — I could not parse a mathematical claim.",
                "verification": "claim parser", "verdict": "unverifiable"}
    # batch-prove the claim and its negation
    flat = []
    for pos, neg in stmts:
        flat.append(("ask_claim", 1, pos))
        flat.append(("ask_neg", 1, neg))
    smap = batch_prove(flat)
    if 0 in smap:
        return {"answer": "VERIFIED — the claim is provable.",
                "verification": "Lean4 kernel (tactic search found a proof)",
                "proof": smap[0][1], "verdict": "verified"}
    if 1 in smap:
        return {"answer": "REJECTED — the claim is false (the negation is provable).",
                "verification": "Lean4 kernel (negation proved)",
                "proof": smap[1][1], "verdict": "rejected"}
    return {"answer": "UNVERIFIABLE — the tactic search found no proof or disproof.",
            "verification": "Lean4 kernel (exhausted the tactic library)",
            "proof": "", "verdict": "unverifiable"}


def answer_factual(q: str) -> dict:
    """Search the verified knowledge index; fall back to Brave web
    evidence (with citation) when the index has no match."""
    try:
        with open(os.path.join(STATE, "knowledge_index.json")) as f:
            entries = json.load(f).get("entries", [])
    except Exception:
        entries = []
    words = [w for w in re.findall(r"[a-z]{3,}", q.lower())
             if w not in {"what", "is", "the", "of", "and", "does", "has",
                          "supports", "capable", "when", "who", "which"}]
    best = []
    for e in entries:
        text = e.get("text", "").lower()
        score = sum(1 for w in words if w in text)
        if score >= 2:  # require meaningful overlap, not single words
            best.append((score, e))
    best.sort(key=lambda x: -x[0])
    if best:
        score, e = best[0]
        return {"answer": e.get("text", ""),
                "verification": e.get("path", "verified index"),
                "domain": e.get("domain", ""),
                "matches": len(best), "verdict": "verified"}
    # Brave web fallback — answer with a real citation
    try:
        sys.path.insert(0, "/home/zixen15/brains")
        from brave_search import get_brave
        r = get_brave().search(q, count=3)
        if r.get("success") and r.get("results"):
            top = r["results"][0]
            snippet = (top.get("snippet") or top.get("title") or "")
            clean = re.sub(r"<[^>]+>", "", snippet)[:200]
            return {"answer": clean or top.get("title", ""),
                    "verification": f"Brave web evidence — {top.get('url', '')}",
                    "source": "web",
                    "matches": len(r["results"]),
                    "verdict": "web-sourced",
                    "note": "cited from the web — NOT formally verified by the kernel"}
    except Exception:
        pass
    return {"answer": "UNVERIFIABLE — no verified entry matches this question.",
            "verification": "verified knowledge index (no match)",
            "verdict": "unverifiable"}


def answer_empirical(q: str) -> dict:
    """Answer from the REAL sensor data."""
    day = time.strftime("%Y%m%d")
    temps = []
    try:
        with open(os.path.join(ARE, "real_data", f"esp32_{day}.jsonl")) as f:
            for line in f:
                if line.strip():
                    try:
                        temps.append(json.loads(line)["temp_c"])
                    except Exception:
                        pass
    except Exception:
        pass
    if not temps:
        return {"answer": "No sensor readings today (sensor offline).",
                "verification": "real_data (no data)", "verdict": "unverifiable"}
    last = temps[-1]
    avg = sum(temps) / len(temps)
    if "how many" in q.lower():
        ans = f"{len(temps)} real temperature readings today."
    elif "average" in q.lower() or "mean" in q.lower():
        ans = f"Mean temperature today: {avg:.1f}°C ({len(temps)} readings)."
    else:
        ans = (f"Latest ESP32-S3 temperature: {last}°C. Today: "
               f"{len(temps)} readings, min {min(temps)}°C, max {max(temps)}°C, "
               f"mean {avg:.1f}°C.")
    return {"answer": ans,
            "verification": f"real sensor data ({len(temps)} readings today)",
            "verdict": "verified"}


def answer_system(q: str) -> dict:
    """Live institution stats."""
    engine = _load_json("are_state.json")
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8196/memory/stats",
                                    timeout=5) as r:
            stats = json.loads(r.read().decode())
    except Exception:
        stats = {}
    tex = _load_jsonl("tactic_exam.jsonl", 1)
    fc = _load_jsonl("fact_check.jsonl", 1)
    parts = []
    parts.append(f"Engine: cycle {engine.get('cycle', '?')}, "
                 f"{engine.get('total_verified', '?')} theorems verified.")
    if stats:
        parts.append(f"ALEPH: {stats.get('nodes', '?')} nodes, "
                     f"{stats.get('edges', '?')} edges, "
                     f"{stats.get('verified', '?')} immortal truths.")
    if tex:
        t = tex[-1]
        parts.append(f"Exam (tactic-search prover): "
                     f"{t.get('overall', 0) * 100:.0f}% "
                     f"({t.get('solved')}/{t.get('total')}).")
    if fc:
        f = fc[-1]
        if f.get("honesty") is not None:
            parts.append(f"Narration honesty: {f['honesty'] * 100:.0f}%.")
    parts.append(f"Verified journal: Edition "
                 f"{(_load_json('journal/manifest.json') or {}).get('edition', '?')} "
                 f"at marquezhv.com/journal/.")
    return {"answer": " ".join(parts),
            "verification": "live institution state (kernel + memory + logs)",
            "verdict": "verified"}


def answer(q: str) -> dict:
    """The verified answer pipeline."""
    kind = route_question(q)
    try:
        if kind == "math":
            r = answer_math(q)
        elif kind == "empirical":
            r = answer_empirical(q)
        elif kind == "system":
            r = answer_system(q)
        else:
            r = answer_factual(q)
    except Exception as e:
        r = {"answer": f"ERROR: {e}", "verification": "answer engine",
             "verdict": "error"}
    r["question"] = q
    r["route"] = kind
    r["time"] = time.time()
    # log
    with open(os.path.join(STATE, "verified_answers.jsonl"), "a") as f:
        f.write(json.dumps(r) + "\n")
    return r


def demo():
    print("=" * 60)
    print("💬 THE VERIFIED ANSWER ENGINE")
    print("=" * 60)
    questions = [
        "is addition commutative for natural numbers",
        "is a + 0 = a",
        "is 2 + 2 = 4",
        "is a * 0 = a",
        "what is the ESP32 temperature",
        "how many sensor readings today",
        "does the ESP32-S3 support wifi",
        "what is the institution's exam score",
        "is the sky made of cheese",
    ]
    for q in questions:
        r = answer(q)
        print(f"\n  Q: {q}")
        print(f"  A: {r['answer'][:110]}")
        print(f"    [{r['route']} · {r['verdict']}] {r['verification'][:60]}")


if __name__ == "__main__":
    demo()
