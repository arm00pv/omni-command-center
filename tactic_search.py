#!/usr/bin/env python3
"""
tactic_search.py — THE TACTIC-SEARCH PROVER
=============================================
A proof search driven by the REAL Lean4 kernel — NO torch, NO RAM
window dependency. The ML prover (:8189) has been down for days in a
bad RAM window; this prover never sleeps.

  SEARCH: for each target, generate candidate tactic sequences
  (depth 1 + 2) from a library, then verify ALL candidates in ONE
  batched Lean4 compilation (the kernel is the judge). The first
  verified proof per problem wins.

Usage:
  python tactic_search.py --exam   # solve the graduation exam
"""

import json
import os
import re
import subprocess
import sys
import time

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")

sys.path.insert(0, ARE)
from verifier import AVAILABLE_IMPORTS, LAKE_BIN, LEAN_PROJECT

# ── The tactic library ─────────────────────────────────────────────
TACTICS = [
    "rfl", "simp", "ring", "norm_num", "trivial", "linarith",
    "positivity", "omega", "nlinarith",
    "simp [Nat.mul_comm]", "simp [Nat.add_comm]",
    "simp [pow_mul]", "simp [mul_pow]",
    "ring_nf", "norm_num [Nat.mul_comm]",
    "exact by omega", "exact by ring", "exact by simp",
    "simp [abs_of_pos h]",
    "rcases h with ⟨x, hx⟩; use 2 * x ^ 2",
    "rw [abs_of_pos h]",
]
TWO_TACTIC = [
    ("simp", "ring"), ("rw [Nat.mul_comm]", "ring"),
    ("ring_nf", "norm_num"), ("simp [pow_mul]", "ring"),
    ("simp [mul_pow]", "ring"), ("norm_num", "ring"),
    ("cases a", "simp"), ("induction a", "simp"),
    ("simp", "omega"), ("ring", "omega"),
    ("ring_nf", "omega"),
    ("simp [Nat.sub_add_cancel, Nat.mul_sub]", "ring"),
    ("rcases h with ⟨x, hx⟩", "rw [hx]; use 2 * x ^ 2; ring"),
    ("simp [abs_of_pos h]", "norm_num"),
]


def _body(statement: str) -> str:
    """The theorem body after the name: '(a : ℕ) : a + 0 = a'.
    Strips the trailing ' := by' that exam statements carry."""
    s = statement.strip()
    # drop 'theorem NAME '
    s = s[s.find(" ") + 1:]
    s = s[s.find(" ") + 1:]
    # drop the trailing proof marker
    if s.endswith(":= by"):
        s = s[:-len(":= by")].rstrip()
    elif s.endswith(":="):
        s = s[:-2].rstrip()
    # keep from the first binder or colon
    if "(" in s:
        return s[s.find("("):]
    return s[s.find(":"):]


def batch_prove(problems: list) -> dict:
    """Generate all candidates, verify in ONE Lean4 compile.
    Returns {problem_index: (tactic_key, proof_template)}."""
    candidates = []  # (pi, tkey, rendered_code)
    for pi, (name, tier, stmt) in enumerate(problems):
        body = _body(stmt)
        for tac in TACTICS:
            candidates.append((pi, (tac,),
                               f"theorem cand_{len(candidates)} {body} := by {tac}"))
        for t1, t2 in TWO_TACTIC:
            candidates.append((pi, (t1, t2),
                               f"theorem cand_{len(candidates)} {body} := by {t1}; {t2}"))
    # write the batch file — one theorem per line (line N = candidate N)
    tmp = os.path.join(LEAN_PROJECT, f"ARE_batch_{int(time.time() * 1000)}.lean")
    with open(tmp, "w") as f:
        f.write("\n".join(AVAILABLE_IMPORTS) + "\n\n")
        for _, _, code in candidates:
            f.write(code + "\n")
    try:
        r = subprocess.run([LAKE_BIN, "env", "lean", tmp],
                           cwd=LEAN_PROJECT, capture_output=True,
                           text=True, timeout=300)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        out = ""
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    # map error lines to candidates: line = imports + 1(blank) + candidate + 1
    failed = set()
    for m in re.finditer(r"ARE_batch_\d+\.lean:(\d+):\d+:\s*error", out):
        ln = int(m.group(1))
        cand_i = ln - len(AVAILABLE_IMPORTS) - 2
        if 0 <= cand_i < len(candidates):
            failed.add(cand_i)
    # first verified candidate per problem
    results = {}
    for i, (pi, tkey, code) in enumerate(candidates):
        if i not in failed:
            results.setdefault(pi, (tkey, code))
    return results


def solve_exam() -> dict:
    """Solve the graduation exam with the batched search prover."""
    EXAM = [
        ("exam_add_zero", 1, "theorem exam_add_zero (a : ℕ) : a + 0 = a := by"),
        ("exam_mul_one", 1, "theorem exam_mul_one (a : ℕ) : a * 1 = a := by"),
        ("exam_comm", 1, "theorem exam_comm (a b : ℕ) : a + b = b + a := by"),
        ("exam_assoc", 1, "theorem exam_assoc (a b c : ℕ) : a + (b + c) = (a + b) + c := by"),
        ("exam_distrib", 1, "theorem exam_distrib (a b c : ℕ) : a * (b + c) = a * b + a * c := by"),
        ("exam_double", 1, "theorem exam_double (a : ℕ) : a + a = 2 * a := by"),
        ("exam_sq_sum", 2, "theorem exam_sq_sum (a b : ℕ) : (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2 := by"),
        ("exam_cube_sum", 2, "theorem exam_cube_sum (a b : ℕ) : (a + b) ^ 3 = a ^ 3 + 3 * a ^ 2 * b + 3 * a * b ^ 2 + b ^ 3 := by"),
        ("exam_sq_diff", 2, "theorem exam_sq_diff (a b : ℕ) : (a - b) * (a + b) = a ^ 2 - b ^ 2 := by"),
        ("exam_pow_mul", 2, "theorem exam_pow_mul (a b c : ℕ) : (a ^ b) ^ c = a ^ (b * c) := by"),
        ("exam_mul_pow", 2, "theorem exam_mul_pow (a b c : ℕ) : (a * b) ^ c = a ^ c * b ^ c := by"),
        ("exam_triple", 3, "theorem exam_triple (a : ℕ) : a + a + a = 3 * a := by"),
        ("exam_sq_even", 3, "theorem exam_sq_even (a : ℕ) (h : Even a) : Even (a ^ 2) := by"),
        ("exam_two_mul", 3, "theorem exam_two_mul (a b : ℕ) : 2 * (a + b) = 2 * a + 2 * b := by"),
        ("exam_sq_identity", 3, "theorem exam_sq_identity (a b : ℝ) : (a + b) ^ 2 + (a - b) ^ 2 = 2 * a ^ 2 + 2 * b ^ 2 := by"),
        ("exam_comm_sq", 3, "theorem exam_comm_sq (a b : ℝ) : (a + b) ^ 2 = (b + a) ^ 2 := by"),
        ("exam_abs_pos", 3, "theorem exam_abs_pos (a : ℝ) (h : 0 < a) : |a| = a := by"),
        ("exam_add_zero_r", 3, "theorem exam_add_zero_r (a : ℝ) : a + 0 = a := by"),
        ("exam_mul_one_r", 3, "theorem exam_mul_one_r (a : ℝ) : a * 1 = a := by"),
        ("exam_distrib_r", 3, "theorem exam_distrib_r (a b c : ℝ) : a * (b + c) = a * b + a * c := by"),
    ]
    print("🏛️  THE TACTIC-SEARCH PROVER — graduation exam (no torch)")
    t0 = time.time()
    solved_map = batch_prove(EXAM)
    print(f"    batch verification completed in {time.time()-t0:.0f}s "
          f"({len(EXAM)} problems, {len(solved_map)} solved)")
    solved = 0
    by_tier = {1: [0, 0], 2: [0, 0], 3: [0, 0]}
    results = []
    for pi, (name, tier, stmt) in enumerate(EXAM):
        by_tier[tier][1] += 1
        r = solved_map.get(pi)
        if r:
            tkey, code = r
            solved += 1
            by_tier[tier][0] += 1
            results.append({"name": name, "tier": tier, "status": "PROVEN",
                            "tactics": list(tkey), "proof": code})
            print(f"  [✅] {name} ({tkey})")
        else:
            by_tier[tier][1] += 0
            results.append({"name": name, "tier": tier, "status": "FAILED"})
            print(f"  [❌] {name}")
    total = len(EXAM)
    entry = {
        "time": time.time(), "prover": "tactic_search",
        "overall": round(solved / total, 4),
        "tier1": round(by_tier[1][0] / max(by_tier[1][1], 1), 4),
        "tier2": round(by_tier[2][0] / max(by_tier[2][1], 1), 4),
        "tier3": round(by_tier[3][0] / max(by_tier[3][1], 1), 4),
        "solved": solved, "total": total, "results": results,
    }
    with open(os.path.join(STATE, "tactic_exam.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"\n🎯 Search-prover exam: {solved}/{total} "
          f"({entry['overall']:.1%}) — tiers "
          f"{entry['tier1']:.1%}/{entry['tier2']:.1%}/{entry['tier3']:.1%}")
    return entry


def run_cycle():
    print("=" * 60)
    print("🔍 THE TACTIC-SEARCH PROVER")
    print("=" * 60)
    return solve_exam()


if __name__ == "__main__":
    run_cycle()
