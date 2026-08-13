#!/usr/bin/env python3
"""
grounded_narration.py — THE GROUNDED NARRATOR
==============================================
The Fact Verifier proved the narrator hallucinates (honesty 0.5).
This engine makes the narrator HONEST by construction:

  1. FACT SHEET — build a numbered list of ONLY verified facts
     (engine, ALEPH, exam, portfolio, ESP32, fitness — all from
     the ground-truth state)
  2. GROUNDED PROMPT — the LLM is told: use EXACTLY these values,
     never invent a number, self-check before writing
  3. NARRATE — generate the captain's log with the grounded prompt
  4. AUDIT — run the Fact Verifier on the output (the same engine
     that caught the hallucinations)
  5. TREND — the honesty score is tracked over time; the journal
     shows the improvement (ungrounded 0.5 → grounded target 1.0)

The institution learns to tell the truth — measurably.
"""

import json
import os
import sys
import time
import urllib.request

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
TREND = os.path.join(STATE, "honesty_trend.jsonl")
LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen3.5:4b"   # slightly stronger than the 0.8b narrator

sys.path.insert(0, ARE)
from fact_verifier import build_reference, verify_claims


def fact_sheet(ref: dict) -> str:
    """A numbered, unambiguous fact sheet from the verified reference."""
    lines = []
    labels = {
        "cycle": "engine cycles", "verified": "theorems verified",
        "attempted": "theorems attempted", "nodes": "ALEPH nodes",
        "edges": "ALEPH edges", "truths": "immortal truths",
        "exam_pct": "graduation exam score (percent)",
        "cash": "portfolio cash (USD)", "capital": "portfolio capital (USD)",
        "fitness": "ESP32 law fitness", "readings": "ESP32 readings today",
        "temp": "latest ESP32 temperature (Celsius)",
        "entries": "consolidated memory entries",
    }
    for i, (k, v) in enumerate(ref.items(), 1):
        label = labels.get(k, k)
        lines.append(f"{i}. {label} = {v}")
    return "\n".join(lines)


def grounded_prompt(sheet: str) -> str:
    return (
        "You are the captain's log of the OMNI-BRAIN, an autonomous "
        "research institution. Write TODAY'S LOG ENTRY (3-5 sentences, "
        "confident, precise, slightly poetic).\n\n"
        "STRICT RULES:\n"
        "- Use ONLY the numbers from the FACT SHEET below. Never invent, "
        "round, or estimate a number.\n"
        "- Every number you write MUST appear verbatim in the fact sheet.\n"
        "- Before writing, self-check: does every number in your draft "
        "appear in the fact sheet? If not, fix it.\n"
        "- No units confusion: temperatures are Celsius, money is USD.\n\n"
        "FACT SHEET (the ONLY numbers you may use):\n" + sheet
    )


def narrate(sheet: str) -> str:
    try:
        payload = json.dumps({
            "model": LLM_MODEL, "prompt": grounded_prompt(sheet),
            "stream": False, "think": False,
            "options": {"temperature": 0.5, "num_predict": 300},
        }).encode()
        req = urllib.request.Request(LLM_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            text = (json.loads(r.read().decode()).get("response") or "").strip()
        if len(text) > 40:
            return text
    except Exception as e:
        print(f"[grounded] LLM unavailable ({e})", flush=True)
    return ""


def audit(text: str, ref: dict) -> dict:
    claims = verify_claims(text, ref)
    verified = sum(1 for c in claims if c["verdict"] == "VERIFIED")
    contradicted = sum(1 for c in claims if c["verdict"] == "CONTRADICTED")
    total = verified + contradicted
    return {"claims": claims, "verified": verified,
            "contradicted": contradicted,
            "honesty": round(verified / total, 4) if total else None}


def run_cycle() -> dict:
    print("=" * 60)
    print("🎙️  THE GROUNDED NARRATOR — the institution learns to tell the truth")
    print("=" * 60)
    print("\n[1] BUILDING the verified fact sheet...")
    ref = build_reference()
    sheet = fact_sheet(ref)
    print(f"    {len(ref)} verified facts:\n{sheet[:300]}...")
    print("\n[2] NARRATING with the grounded prompt...")
    text = narrate(sheet)
    if not text:
        print("    LLM unavailable — using the previous log")
        return {"status": "llm_unavailable"}
    print(f"    {text[:160]}...")
    print("\n[3] AUDITING against the SNAPSHOT fact sheet "
          "(the ground truth at narration time)...")
    # audit against the SNAPSHOT reference the narrator was grounded on —
    # live metrics (readings/temp/entries) move every second, so a fresh
    # reference would falsely flag correct numbers as stale
    result = audit(text, ref)
    print(f"    {result['verified']} verified / {result['contradicted']} "
          f"contradicted → honesty {result['honesty']}")
    for c in result["claims"][:6]:
        print(f"      [{c['verdict']}] {c['value']} "
              f"(truth {c.get('truth', '?')})")
    print("\n[4] RECORDING the trend...")
    entry = {"time": time.time(), "mode": "grounded", "text": text,
             "snapshot_ref": ref,
             **{k: v for k, v in result.items() if k != "claims"}}
    with open(TREND, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    # also write the grounded log as the captain's log (replaces the old)
    with open(os.path.join(STATE, "captains_log.jsonl"), "a") as f:
        f.write(json.dumps({"time": time.time(),
                            "day": time.strftime("%Y-%m-%d"),
                            "text": text, "grounded": True}) + "\n")
    print(f"    honesty_trend.jsonl + captains_log.jsonl (grounded)")
    print(f"\n🎙️  Grounded honesty: {result['honesty']} "
          f"(baseline ungrounded: 0.5)")
    return entry


if __name__ == "__main__":
    run_cycle()
