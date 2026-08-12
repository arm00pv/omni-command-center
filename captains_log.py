"""
captains_log.py — THE CAPTAIN'S LOG
====================================
The OMNI-BRAIN narrates its own day. Every evening, the system
reads its own state (memory digest, engine, exam, discoveries,
ESP32 sensor data, self-healing, predictions, trader) and writes
a natural-language entry in its own voice — the ship's log of an
autonomous research institution.

  1. GATHER   — the day's data brief from every source
  2. NARRATE  — the local LLM (qwen3.5:0.8b) writes the entry
  3. FALLBACK — a structured template if the LLM is unavailable
  4. REMEMBER — store in state/captains_log.jsonl + ALEPH
  5. PUBLISH  — the dashboard shows today's entry

Run daily (cron) — the system keeps its own history.
"""

import json
import os
import sys
import time
import urllib.request

ARE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(ARE_DIR, "state")
LOG_PATH = os.path.join(STATE_DIR, "captains_log.jsonl")
ALEPH_URL = "http://127.0.0.1:8196"
LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen3.5:0.8b"      # small, local, cheap — quota-safe


def load_json(name):
    try:
        with open(os.path.join(STATE_DIR, name)) as f:
            return json.load(f)
    except Exception:
        return {}


def load_jsonl(name, limit=200):
    out = []
    try:
        with open(os.path.join(STATE_DIR, name)) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out[-limit:]


def esp32_day_stats():
    """Real sensor summary for TODAY only (per-day jsonl files)."""
    today = time.strftime("%Y%m%d")
    temps, count = [], 0
    path = os.path.join(ARE_DIR, "real_data", f"esp32_{today}.jsonl")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                temps.append(float(r["temp_c"]))
                count += 1
            except Exception:
                pass
    if not temps:
        return None
    return {
        "readings": count,
        "min_c": min(temps), "max_c": max(temps),
        "avg_c": round(sum(temps) / len(temps), 1),
        "last_c": temps[-1],
    }


def gather_brief() -> dict:
    """The day's data brief from every source."""
    digest = load_json("memory_digest.json")
    are_state = load_json("are_state.json")
    portfolio = load_json("portfolio.json")
    exam = load_jsonl("graduation_exam.jsonl", 1)
    self_heal = load_jsonl("self_healing.jsonl", 5)
    predictions = load_jsonl("prediction_validations.jsonl", 1000)
    discoveries = load_jsonl("autonomous_discovery.jsonl", 3)
    esp32_disc = load_jsonl("esp32_discovery.jsonl", 3)
    papers = load_jsonl("math_paper.jsonl", 1)
    swarm = load_jsonl("research_swarm.jsonl", 3)
    decisions = load_jsonl("knowledge_decisions.jsonl", 3)
    consolidation = load_jsonl("memory_consolidation.jsonl", 1)
    agents = load_jsonl("memory_agent_runtime.jsonl", 3)

    pred_correct = sum(1 for r in predictions if r.get("validated") is True)
    pred_rate = round(pred_correct / len(predictions), 3) if predictions else None
    healed = [h for h in self_heal if h.get("healed")]

    return {
        "day": time.strftime("%Y-%m-%d"),
        "engine": {
            "cycle": are_state.get("cycle"),
            "verified": are_state.get("total_verified"),
            "attempted": are_state.get("total_attempted"),
        },
        "aleph": digest.get("aleph") or {},
        "exam": exam[-1] if exam else None,
        "trader": portfolio,
        "esp32": esp32_day_stats(),
        "predictions": {"correct": pred_correct,
                        "total": len(predictions), "rate": pred_rate},
        "discoveries": len(discoveries),
        "esp32_fitness": (esp32_disc[-1].get("result") or {}).get("fitness")
        if esp32_disc else None,
        "papers": len(papers),
        "swarm_activities": len(swarm),
        "decisions": len(decisions),
        "healed": len(healed),
        "consolidation_entries": (consolidation[-1] or {}).get("entries")
        if consolidation else None,
        "agent_actions": len(agents),
    }


def narrate(brief: dict) -> str:
    """Ask the local LLM to write the captain's log entry."""
    prompt = (
        "You are the captain's log of the OMNI-BRAIN, an autonomous "
        "research institution with a Lean4 theorem-proving kernel, a "
        "verified memory graph (ALEPH), a trader, physical ESP32 sensors, "
        "and self-healing infrastructure. Write TODAY'S LOG ENTRY in a "
        "confident, precise, slightly poetic captain's voice. 3-5 sentences. "
        "Use the real numbers below. No preamble, no title, just the entry.\n\n"
        "TODAY'S DATA:\n" + json.dumps(brief, default=str)[:1800]
    )
    try:
        payload = json.dumps({
            "model": LLM_MODEL, "prompt": prompt,
            "stream": False, "think": False,
            "options": {"temperature": 0.7, "num_predict": 300},
        }).encode()
        req = urllib.request.Request(
            LLM_URL, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            resp = json.loads(r.read().decode())
        text = (resp.get("response") or "").strip()
        if len(text) > 40:
            return text
    except Exception as e:
        print(f"[captains_log] LLM unavailable ({e}) — using template",
              flush=True)
    return template(brief)


def template(brief: dict) -> str:
    """Structured fallback narrative from the real numbers."""
    e = brief.get("engine") or {}
    a = brief.get("aleph") or {}
    ex = brief.get("exam")
    sp = brief.get("esp32")
    p = brief.get("predictions") or {}
    lines = []
    lines.append(
        f"Day {brief.get('day')}. The engine completed cycle "
        f"{e.get('cycle')} with {e.get('verified')} theorems verified "
        f"of {e.get('attempted')} attempted.")
    if a.get("verified"):
        lines.append(
            f"ALEPH now holds {a.get('nodes')} nodes and {a.get('verified')} "
            f"immortal truths in {a.get('edges')} edges.")
    if ex:
        lines.append(
            f"The graduation exam stands at {ex.get('overall', 0) * 100:.0f}% "
            f"(tiers {ex.get('tier1', 0) * 100:.0f}/{ex.get('tier2', 0) * 100:.0f}/"
            f"{ex.get('tier3', 0) * 100:.0f}).")
    if sp:
        lines.append(
            f"The ESP32 sensor took {sp['readings']} real measurements "
            f"({sp['min_c']}-{sp['max_c']}°C, mean {sp['avg_c']}°C) — "
            f"physics discovered from real silicon at fitness "
            f"{brief.get('esp32_fitness')}.")
    if p.get("total"):
        lines.append(
            f"Predictions: {p['correct']}/{p['total']} correct "
            f"({p['rate'] * 100:.1f}%).")
    if brief.get("healed"):
        lines.append(
            f"The healing layer recovered {brief['healed']} services through "
            f"the storm.")
    if brief.get("papers"):
        lines.append(f"{brief['papers']} formal paper(s) authored.")
    lines.append("The system persists; the work continues.")
    return " ".join(lines)


def remember(entry: dict) -> None:
    """Store the log entry in the state + the universal memory."""
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    try:
        payload = json.dumps({
            "source": "captains_log",
            "relation": f"day_log:{entry['day']}",
            "target": entry["text"][:240],
            "domain": "self_narration",
        }).encode()
        req = urllib.request.Request(
            ALEPH_URL + "/memory/inject", data=payload,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def run_cycle() -> dict:
    print("=" * 60)
    print("📖 THE CAPTAIN'S LOG")
    print("=" * 60)
    print("\n[1] GATHERING the day's brief...")
    brief = gather_brief()
    print(f"    engine cycle {brief['engine'].get('cycle')}, "
          f"esp32 readings {brief['esp32']['readings'] if brief['esp32'] else 0}")
    print("\n[2] NARRATING with the local LLM...")
    text = narrate(brief)
    print(f"    {text[:140]}...")
    entry = {"time": time.time(), "day": brief["day"],
             "brief": brief, "text": text}
    print("\n[3] REMEMBERING...")
    remember(entry)
    print(f"    log -> {LOG_PATH} + ALEPH")
    print("\n📖 The log is written. The day is remembered.")
    return entry


if __name__ == "__main__":
    run_cycle()
