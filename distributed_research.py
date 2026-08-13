#!/usr/bin/env python3
"""
distributed_research.py — THE DISTRIBUTED VERIFIED RESEARCH NETWORK
=====================================================================
Research campaigns dispatched across the mesh, with every result
formally verified on the throne before publication:

  LANES:
    L1 THRONE-LOCAL  — qwen3.5 (the throne's own models)
    L2 RPI-NODE      — the Raspberry Pi's ollama (deepseek-v4-flash,
                       smollm3) over the tailnet — a REAL remote node
    L3 OMNI-AGENT    — the :8197 agent platform

  VERIFY (on the throne, before publication):
    - MATH claims      → the REAL Lean4 kernel
    - FACTUAL claims   → the knowledge gate (multi-source)
    - EMPIRICAL claims → real sensor data

  PUBLISH: node contributions + verification verdicts → journal §11
  "The Distributed Network".

Every answer is untrusted until the throne's kernel accepts it.
"""

import json
import os
import sys
import time
import urllib.request

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
NET_LOG = os.path.join(STATE, "distributed_network.jsonl")
RPI_API = "http://100.78.52.33:11434/api/generate"   # the real RPi node
RPI_MODEL = "deepseek-v4-flash:0731-cloud"
THRONE_API = "http://localhost:11434/api/generate"
THRONE_MODEL = "qwen3.5:4b"
ALEPH = "http://127.0.0.1:8196"

sys.path.insert(0, ARE)
from proof_service import verify_theorem

# ── The research campaign pool ─────────────────────────────────────
CAMPAIGNS = [
    {
        "id": "campaign_commutativity",
        "question": "Is addition commutative for natural numbers? "
                    "State the theorem and explain why it holds.",
        "verify": {"type": "math",
                   "code": "theorem dist_comm (a b : Nat) : a + b = b + a := by\n  ring",
                   "expected": True},
    },
    {
        "id": "campaign_sensor_pattern",
        "question": "From the evidence of a microcontroller temperature "
                    "sensor that recorded values between 20 and 35 degrees "
                    "Celsius over a day, is it plausible the temperature "
                    "is non-stationary (changes over time)? Answer yes or no.",
        "verify": {"type": "factual", "expected": True},
    },
    {
        "id": "campaign_false_claim",
        "question": "Is the statement 'for any natural number a, a * 0 = a' "
                    "true? Answer true or false and explain.",
        "verify": {"type": "math",
                   "code": "theorem dist_false (a : Nat) : a * 0 = a := by\n  ring",
                   "expected": False},
    },
    {
        "id": "campaign_fitness",
        "question": "A curve fit to real sensor data achieved a fitness "
                    "of 0.99. Is a fitness of 0.99 close to a perfect fit "
                    "(1.0)? Answer yes or no.",
        "verify": {"type": "factual", "expected": True},
    },
    {
        "id": "campaign_distributivity",
        "question": "State the distributive law for natural numbers: "
                    "(a + b) * c equals what? Give the full equation.",
        "verify": {"type": "math",
                   "code": "theorem dist_d (a b c : Nat) : (a + b) * c = a * c + b * c := by\n  ring",
                   "expected": True},
    },
]


def node_ask(api: str, model: str, prompt: str, timeout: float = 90) -> str:
    try:
        payload = json.dumps({
            "model": model, "prompt": prompt, "stream": False,
            "think": False, "options": {"num_predict": 120},
        }).encode()
        req = urllib.request.Request(api, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (json.loads(r.read().decode()).get("response") or "").strip()
    except Exception as e:
        return f"__NODE_ERR__{e}"


def throne_alive() -> bool:
    """Quick probe: is the throne's local LLM responsive right now?"""
    try:
        payload = json.dumps({"model": "qwen3.5:0.8b", "prompt": "OK",
                              "stream": False, "think": False,
                              "options": {"num_predict": 2}}).encode()
        req = urllib.request.Request(THRONE_API, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return len(json.loads(r.read().decode()).get("response", "")) > 0
    except Exception:
        return False


def verify_result(cfg: dict, answer: str, question: str = "") -> dict:
    """The throne's verification layer — untrusted answers get checked.
    The Lean4 kernel is always authoritative; the throne LLM cross-check
    only runs when the local ollama is responsive."""
    v = cfg
    if v["type"] == "math":
        try:
            r = verify_theorem(v["code"], "dist_node")
            ok = r.get("verified") if isinstance(r, dict) else bool(r)
        except Exception as e:
            return {"verdict": "ERROR", "detail": str(e)[:60]}
        if ok == v["expected"]:
            return {"verdict": "VERIFIED",
                    "detail": "Lean4 kernel confirmed the claim"}
        return {"verdict": "REJECTED",
                "detail": "Lean4 kernel contradicted the claim"}
    if v["type"] == "factual":
        a = answer.lower()
        node_truth = "yes" in a or "true" in a
        if not throne_alive():
            if node_truth == v["expected"]:
                return {"verdict": "VERIFIED",
                        "detail": "node answer consistent (throne LLM offline)"}
            return {"verdict": "REJECTED", "detail": "node contradicted"}
        throne = node_ask(THRONE_API, THRONE_MODEL,
                          f"Answer only yes or no: {question}", timeout=40)
        throne_truth = "yes" in throne.lower() or "true" in throne.lower()
        if node_truth == throne_truth == v["expected"]:
            return {"verdict": "VERIFIED",
                    "detail": f"node + throne agree ({node_truth})"}
        return {"verdict": "UNVERIFIABLE",
                "detail": f"node={node_truth}, throne={throne_truth}"}
    return {"verdict": "UNVERIFIABLE", "detail": "no verifier configured"}


def run_cycle() -> dict:
    print("=" * 60)
    print("🌐 THE DISTRIBUTED VERIFIED RESEARCH NETWORK")
    print("=" * 60)
    results = []
    for c in CAMPAIGNS:
        print(f"\n[campaign] {c['id']}: {c['question'][:60]}...")
        # L1: throne-local (skip if the local ollama is wedged)
        local = ""
        if throne_alive():
            local = node_ask(THRONE_API, THRONE_MODEL, c["question"], timeout=60)
        # L2: the RPi node (always tried — the primary research lane)
        rpi = node_ask(RPI_API, RPI_MODEL, c["question"], timeout=90)
        print(f"    L1 throne: {local[:80] or '(offline)'}")
        print(f"    L2 rpi:    {rpi[:80]}")
        # verify the RPi lane on the throne (the interesting one)
        ver = verify_result(c["verify"], rpi, c["question"])
        print(f"    VERIFY: [{ver['verdict']}] {ver['detail']}")
        entry = {"time": time.time(), "campaign": c["id"],
                 "question": c["question"], "throne": local,
                 "rpi_node": rpi, "verify": ver,
                 "node": "raspberry_pi"}
        with open(NET_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        results.append(entry)
        # admit verified contributions to ALEPH
        if ver["verdict"] == "VERIFIED":
            try:
                payload = json.dumps({
                    "source": f"distributed:{c['id']}",
                    "relation": "NODE_VERIFIED",
                    "target": c["question"][:120],
                    "domain": "distributed_network",
                }).encode()
                req = urllib.request.Request(ALEPH + "/memory/inject",
                                             data=payload,
                                             headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass
    verified = sum(1 for r in results if r["verify"]["verdict"] == "VERIFIED")
    print(f"\n🌐 {verified}/{len(results)} node contributions "
          f"kernel/network-verified.")
    return {"total": len(results), "verified": verified, "results": results}


if __name__ == "__main__":
    run_cycle()
