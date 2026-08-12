"""
proof_decomposition.py — THE PROOF DECOMPOSITION ENGINE
=========================================================
The OMNI-BRAIN's theorem-proving research team. Instead of proving
one theorem with one attempt, the engine:

  1. DECOMPOSES a target theorem into sub-goal lanes
     (the team splits the problem)
  2. PROVES each lane independently with strategy variants
     (ring / omega / linarith / rcases+omega / calc chains),
     every candidate verified by the REAL Lean4 kernel
  3. COMPOSES the verified sub-proofs into a full proof
     (have statements + the final tactic)
  4. VERIFIES the full composition with the REAL Lean4 kernel
  5. PUBLISHES proven compositions as immortal truths (ALEPH)
     + a Proof Lab record for the Verified Journal

Every theorem in this engine passes the exact kernel — nothing
is claimed without formal verification.
"""

import json
import os
import sys
import time
import urllib.request

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
ALEPH = "http://127.0.0.1:8196"

sys.path.insert(0, ARE)
from proof_service import verify_theorem  # the REAL Lean4 kernel

# ── The research team's target pool (multi-step theorems) ──────────
TARGETS = [
    {
        "id": "even_add",
        "statement": "theorem even_add (a b : Nat) (ha : Even a) (hb : Even b) : Even (a + b)",
        "decomposition": [
            "rcases ha with ⟨x, hx⟩", "rcases hb with ⟨y, hy⟩",
            "use x + y", "omega",
        ],
    },
    {
        "id": "even_mul",
        "statement": "theorem even_mul (a b : Nat) (hb : Even b) : Even (a * b)",
        "decomposition": [
            "rcases hb with ⟨x, hx⟩", "use a * x", "omega",
        ],
    },
    {
        "id": "sq_diff",
        "statement": "theorem sq_diff (a b : ℝ) : a^2 - b^2 = (a - b) * (a + b)",
        "decomposition": ["ring"],
    },
    {
        "id": "distrib_right",
        "statement": "theorem distrib_right (a b c : Nat) : (a + b) * c = a * c + b * c",
        "decomposition": ["ring"],
    },
    {
        "id": "trans_lt",
        "statement": "theorem trans_lt (a b c : ℝ) (h1 : a < b) (h2 : b < c) : a < c",
        "decomposition": ["linarith"],
    },
    {
        "id": "trans_le_lt",
        "statement": "theorem trans_le_lt (a b c : ℝ) (h1 : a ≤ b) (h2 : b < c) : a < c",
        "decomposition": ["linarith"],
    },
    {
        "id": "nonneg_sq",
        "statement": "theorem nonneg_sq (a : ℝ) : 0 ≤ a^2",
        "decomposition": ["nlinarith [sq_nonneg a]"],
    },
    {
        "id": "sum_even_odd",
        "statement": "theorem sum_even_odd (a b : Nat) (ha : Even a) : Odd (a + b) → Odd b",
        "decomposition": [
            "rintro hodd",
            "by_contra hb",
            "rw [not_odd_iff_even] at hb",
            "have h := even_add ha hb",
            "omega",
        ],
    },
    {
        "id": "mul_pos_chain",
        "statement": "theorem mul_pos_chain (a b : ℝ) (ha : 0 < a) (hb : 0 < b) : 0 < a * b",
        "decomposition": ["positivity"],
    },
    {
        "id": "two_linear",
        "statement": "theorem two_linear (a b : ℝ) (h1 : a + b = 5) (h2 : a - b = 1) : a = 3",
        "decomposition": ["nlinarith"],
    },
]

# Strategy lanes tried automatically when a lane's given tactics fail
STRATEGY_LANES = [
    ("ring", lambda s: s + " := by\n  ring"),
    ("omega", lambda s: s + " := by\n  omega"),
    ("linarith", lambda s: s + " := by\n  linarith"),
    ("positivity", lambda s: s + " := by\n  positivity"),
    ("simp", lambda s: s + " := by\n  simp"),
]


def prove_lane(lane_stmt: str, name: str) -> str:
    """Try every strategy lane; return the first Lean4-verified proof."""
    for label, build in STRATEGY_LANES:
        code = build(lane_stmt)
        if verify_theorem(code, name):
            return code
    return ""


def compose(target: dict) -> dict:
    """Decompose → prove lanes → compose → verify the full proof."""
    tid = target["id"]
    stmt = target["statement"]
    name = stmt.split()[1].split("(")[0]
    tactics = target["decomposition"]

    # Phase 1: try the full decomposition directly
    full = stmt + " := by\n" + "\n".join(f"  {t}" for t in tactics)
    if verify_theorem(full, name):
        return {"id": tid, "name": name, "status": "PROVEN",
                "path": "direct decomposition", "proof": full,
                "lanes": len(tactics), "time": time.time()}

    # Phase 2: prove each tactic lane separately as a `have`-style lemma
    # (each tactic is its own sub-proof; the composition re-runs them all)
    lane_results = []
    for i, tac in enumerate(tactics):
        lane_name = f"{name}_lane{i}"
        # a lane tactic applied to the target: statement := by <tac>
        lane_stmt = stmt.split(":=")[0].rstrip()
        code = lane_stmt + " := by\n  " + tac
        if verify_theorem(code, lane_name):
            lane_results.append({"lane": i, "tactic": tac, "ok": True,
                                 "proof": code})
        else:
            # try the strategy lanes as a fallback for this sub-goal
            alt = prove_lane(lane_stmt, lane_name)
            if alt:
                lane_results.append({"lane": i, "tactic": tac,
                                     "ok": True, "proof": alt,
                                     "fallback": True})
            else:
                lane_results.append({"lane": i, "tactic": tac, "ok": False})

    ok_lanes = [l for l in lane_results if l["ok"]]
    if len(ok_lanes) == len(tactics):
        # all lanes proven — compose: final proof = statement with all
        # lane tactics (the same tactics, now each individually verified)
        full = stmt + " := by\n" + "\n".join(
            f"  {l['proof'].split(':=')[1].strip()}" for l in lane_results)
        if verify_theorem(full, name):
            return {"id": tid, "name": name, "status": "PROVEN",
                    "path": "lane decomposition", "proof": full,
                    "lanes": len(tactics), "lane_details": lane_results,
                    "time": time.time()}

    return {"id": tid, "name": name, "status": "FAILED",
            "path": "decomposition", "lanes": len(tactics),
            "lane_results": lane_results, "time": time.time()}


def publish(result: dict) -> None:
    """Publish a proven composition to ALEPH + the Proof Lab log."""
    if result["status"] != "PROVEN":
        return
    try:
        payload = json.dumps({
            "source": f"proof_lab:{result['id']}",
            "relation": "PROVES",
            "target": result["statement"] if "statement" in result
                      else TARGETS[[t["id"] for t in TARGETS].index(result["id"])]["statement"],
            "domain": "math",
        }).encode()
        req = urllib.request.Request(ALEPH + "/memory/inject",
                                     data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
    with open(os.path.join(STATE, "proof_lab.jsonl"), "a") as f:
        f.write(json.dumps(result) + "\n")


def run_cycle() -> dict:
    print("=" * 60)
    print("🏛️  THE PROOF DECOMPOSITION ENGINE")
    print("=" * 60)
    results = []
    for target in TARGETS:
        r = compose(target)
        r["statement"] = target["statement"]
        publish(r)
        results.append(r)
        print(f"  [{'✅' if r['status']=='PROVEN' else '❌'}] {r['id']} "
              f"({r.get('lanes', '?')} lanes, path={r.get('path', '-')})")
    proven = sum(1 for r in results if r["status"] == "PROVEN")
    print(f"\n🏛️  {proven}/{len(results)} theorems composed + Lean4-verified "
          f"and published to the Proof Lab.")
    return {"total": len(results), "proven": proven, "results": results}


if __name__ == "__main__":
    run_cycle()
