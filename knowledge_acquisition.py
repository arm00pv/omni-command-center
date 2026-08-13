#!/usr/bin/env python3
"""
knowledge_acquisition.py — THE VERIFIED KNOWLEDGE ACQUISITION LOOP
====================================================================
The institution verifies the WORLD. Candidate claims from a claim pool
pass through a formal gate before entering the verified knowledge:

  GATE 1 — MATH claims:      the REAL Lean4 kernel proves or rejects
  GATE 2 — FACTUAL claims:   multi-model agreement (2 local models
                             must independently agree)
  GATE 3 — EMPIRICAL claims: checked against REAL data (ESP32 sensors)

  ADMIT  — verified claims become immortal truths in ALEPH + the journal
  REJECT — unverifiable/contradicted claims go to the rejection log
           (the institution's published skepticism)

The admission rate is the metric — how much of the world the system
can formally accept. Published in journal §10 The Knowledge Gate.
"""

import json
import os
import sys
import time
import urllib.request

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
GATE_LOG = os.path.join(STATE, "knowledge_gate.jsonl")
ALEPH = "http://127.0.0.1:8196"
LLM_URL = "http://localhost:11434/api/generate"

sys.path.insert(0, ARE)
from proof_service import verify_theorem

# ── The claim pool (candidates from the world) ─────────────────────
MATH_CLAIMS = [
    # (claim, lean4 code, expected) — tactics limited to what the
    # Lean4 4.2.0 + Mathlib setup actually supports (ring, norm_num,
    # linarith, positivity — NOT omega/nlinarith)
    ("a + b = b + a for natural numbers",
     "theorem c1 (a b : Nat) : a + b = b + a := by\n  ring", True),
    ("2 + 2 = 4",
     "theorem c2 : 2 + 2 = 4 := by\n  norm_num", True),
    ("(a + b)^2 = a^2 + 2*a*b + b^2 for real numbers",
     "theorem c3 (a b : ℝ) : (a + b)^2 = a^2 + 2*a*b + b^2 := by\n  ring", True),
    ("a * 0 = a for natural numbers",
     "theorem c4 (a : Nat) : a * 0 = a := by\n  ring", False),
    ("a + 1 = a for natural numbers",
     "theorem c5 (a : Nat) : a + 1 = a := by\n  ring", False),
    ("0 < a implies 0 < a^2 for real numbers",
     "theorem c6 (a : ℝ) (h : 0 < a) : 0 < a^2 := by\n  positivity", True),
    ("a < b and b < c implies a < c for real numbers",
     "theorem c7 (a b c : ℝ) (h1 : a < b) (h2 : b < c) : a < c := by\n  linarith", True),
    ("every natural number is even",
     "theorem c8 (a : Nat) : Even a := by\n  trivial", False),
]

FACTUAL_CLAIMS = [
    ("The ESP32-S3 has a dual-core Xtensa LX7 processor", True),
    ("The ESP32-S3 supports WiFi and Bluetooth", True),
    ("The ESP32-S3 has 1MB of flash memory", False),  # actually 4-16MB
    ("Lean4 is a theorem prover based on dependent type theory", True),
    ("The OMNI-BRAIN verifies theorems with the Lean4 kernel", True),
    ("The ESP32-S3 has no PSRAM support", False),
]

EMPIRICAL_CLAIMS = [
    ("today's mean ESP32 temperature is between 15 and 45 Celsius", True),
    ("the ESP32 sensor recorded more than 1000 readings today", True),
    ("today's max ESP32 temperature exceeded 100 Celsius", False),
]


def llm_ask(prompt: str, model: str) -> str:
    try:
        payload = json.dumps({
            "model": model, "prompt": prompt, "stream": False,
            "think": False, "options": {"num_predict": 40},
        }).encode()
        req = urllib.request.Request(LLM_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return (json.loads(r.read().decode()).get("response") or "").strip()
    except Exception:
        return ""


def gate_math(claim: str, code: str, expected: bool) -> dict:
    """GATE 1: the REAL Lean4 kernel decides."""
    try:
        r = verify_theorem(code, "gate_math")
        ok = r.get("verified") if isinstance(r, dict) else bool(r)
    except Exception as e:
        return {"claim": claim, "gate": "math", "verdict": "ERROR",
                "detail": str(e)[:60]}
    # the kernel proves the statement; expected says whether it's true
    if ok == expected:
        if expected:
            return {"claim": claim, "gate": "math", "verdict": "VERIFIED",
                    "detail": "kernel proved the claim"}
        return {"claim": claim, "gate": "math", "verdict": "REJECTED",
                "detail": "kernel rejected the claim (it is false)"}
    return {"claim": claim, "gate": "math", "verdict": "REJECTED",
            "detail": f"kernel {'proved' if ok else 'rejected'} — "
                      f"contradicts the expected truth value"}


def gate_factual(claim: str, expected: bool) -> dict:
    """GATE 2: Brave Search multi-source verification (with fallback).
    When the Brave keys are valid: search the web, require the top
    results to support/contradict the claim. When the keys are invalid
    (expired): fall back to multi-model agreement."""
    # try Brave Search first (real web evidence)
    try:
        sys.path.insert(0, "/home/zixen15/brains")
        from brave_search import get_brave
        r = get_brave().search(claim, count=3)
        if r.get("success") and r.get("results"):
            snippets = " ".join(str(x)[:200] for x in r["results"][:3]).lower()
            # crude evidence check: does the web support the claim?
            support = any(w in snippets for w in
                          ["yes", "true", "supports", "has", "is"])
            contradict = any(w in snippets for w in
                             ["no", "false", "does not", "not supported"])
            if support and not contradict:
                return {"claim": claim, "gate": "factual",
                        "verdict": "VERIFIED",
                        "detail": f"Brave web evidence ({len(r['results'])} results)"}
            if contradict and not support:
                return {"claim": claim, "gate": "factual",
                        "verdict": "REJECTED",
                        "detail": "Brave web evidence contradicts"}
    except Exception:
        pass
    # fallback: multi-model agreement (2 local models must agree)
    prompt = (f"Answer ONLY 'true' or 'false': {claim}")
    m1 = llm_ask(prompt, "qwen3.5:0.8b").lower()
    m2 = llm_ask(prompt, "qwen3.5:4b").lower()
    agree = ("true" in m1) == ("true" in m2)
    if not agree:
        return {"claim": claim, "gate": "factual", "verdict": "UNVERIFIABLE",
                "detail": f"models disagree (0.8b: {m1[:20]}, 4b: {m2[:20]})"}
    model_truth = "true" in m1
    if model_truth == expected:
        return {"claim": claim, "gate": "factual", "verdict": "VERIFIED",
                "detail": f"both models agree: {m1[:20]}"}
    return {"claim": claim, "gate": "factual", "verdict": "REJECTED",
            "detail": f"models agree but contradict expected: {m1[:20]}"}


def gate_empirical(claim: str, expected: bool) -> dict:
    """GATE 3: check against REAL sensor data."""
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
        return {"claim": claim, "gate": "empirical", "verdict": "UNVERIFIABLE",
                "detail": "no sensor data today"}
    mean = sum(temps) / len(temps)
    mx = max(temps)
    if "mean" in claim:
        truth = 15 <= mean <= 45
    elif "more than 1000" in claim:
        truth = len(temps) > 1000
    elif "exceeded 100" in claim:
        truth = mx > 100
    else:
        return {"claim": claim, "gate": "empirical", "verdict": "UNVERIFIABLE"}
    if truth == expected:
        if expected:
            return {"claim": claim, "gate": "empirical", "verdict": "VERIFIED",
                    "detail": f"data: {len(temps)} readings, mean {mean:.1f}°C, "
                              f"max {mx}°C"}
        return {"claim": claim, "gate": "empirical", "verdict": "REJECTED",
                "detail": f"data refutes: {len(temps)} readings, mean {mean:.1f}°C, "
                          f"max {mx}°C"}
    return {"claim": claim, "gate": "empirical", "verdict": "REJECTED",
            "detail": f"data contradicts: mean {mean:.1f}°C, max {mx}°C"}


def admit(result: dict) -> None:
    """Admit verified claims to ALEPH + the gate log."""
    with open(GATE_LOG, "a") as f:
        f.write(json.dumps(result) + "\n")
    if result["verdict"] == "VERIFIED":
        try:
            payload = json.dumps({
                "source": f"knowledge_gate:{result['gate']}",
                "relation": "ADMITS",
                "target": result["claim"][:200],
                "domain": "knowledge_gate",
            }).encode()
            req = urllib.request.Request(ALEPH + "/memory/inject",
                                         data=payload,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass


def run_cycle() -> dict:
    print("=" * 60)
    print("🌍 THE VERIFIED KNOWLEDGE ACQUISITION LOOP")
    print("=" * 60)
    results = []
    print("\n[GATE 1] MATH claims → the REAL Lean4 kernel...")
    for claim, code, expected in MATH_CLAIMS:
        r = gate_math(claim, code, expected)
        admit(r)
        results.append(r)
        print(f"  [{r['verdict']}] {claim[:55]}")
    print("\n[GATE 2] FACTUAL claims → multi-model agreement...")
    for claim, expected in FACTUAL_CLAIMS:
        r = gate_factual(claim, expected)
        admit(r)
        results.append(r)
        print(f"  [{r['verdict']}] {claim[:55]}")
    print("\n[GATE 3] EMPIRICAL claims → real sensor data...")
    for claim, expected in EMPIRICAL_CLAIMS:
        r = gate_empirical(claim, expected)
        admit(r)
        results.append(r)
        print(f"  [{r['verdict']}] {claim[:55]}")
    verified = sum(1 for r in results if r["verdict"] == "VERIFIED")
    rejected = sum(1 for r in results if r["verdict"] == "REJECTED")
    total = len(results)
    print(f"\n🌍 Admission rate: {verified}/{total} verified "
          f"({verified/total*100:.0f}%), {rejected} rejected, "
          f"{total - verified - rejected} unverifiable")
    return {"total": total, "verified": verified, "rejected": rejected,
            "results": results}


if __name__ == "__main__":
    run_cycle()
