"""
memory_consolidation.py — THE MEMORY CONSOLIDATION LOOP
========================================================
The OMNI-BRAIN's fragmented state files (60+ jsonl silos) are
consolidated into the universal memory (ALEPH) + a single digest.

  The loop:
    1. SCAN   — every state/*.jsonl + key .json files
    2. EXTRACT — per-file summary (count, latest, key metrics)
    3. CONSOLIDATE — deduplicated facts -> ALEPH universal memory
    4. PROMOTE — verified facts (Lean4 truths, exam, discoveries)
    5. DIGEST — one consolidated memory digest (state/memory_digest.json)
    6. FEED — the digest is available to every agent (memory-first runtime)

Run daily (cron) + wired into next_level.py.
"""

import glob
import json
import os
import sys
import time
import urllib.request
from typing import Dict, List

ARE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(ARE_DIR, "state")
ALEPH_URL = "http://127.0.0.1:8196"
LOG_PATH = os.path.join(STATE_DIR, "memory_consolidation.jsonl")
DIGEST_PATH = os.path.join(STATE_DIR, "memory_digest.json")

# Files whose content is a single JSON object (not jsonl)
JSON_FILES = [
    "are_state.json", "portfolio.json", "heartbeat.json",
    "last_retrain_count.json", "fresh_position_prices.json",
    "self_model.json", "curriculum.json", "agent_team.json",
    "autonomous_discoveries.json", "distributed_network.json",
]

# Key metrics to extract from specific files (promoted facts)
PROMOTED = {
    "graduation_exam.jsonl": ("exam", "overall"),
    "validated_predictions.jsonl": ("prediction", "validated"),
    "autonomous_discovery.jsonl": ("discovery", "success"),
    "esp32_discovery.jsonl": ("esp32_discovery", "result"),
    "math_paper.jsonl": ("math_paper", "verified"),
    "knowledge_decisions.jsonl": ("decision", "outcome"),
    "research_swarm.jsonl": ("swarm", "status"),
    "memory_agent_runtime.jsonl": ("agent_runtime", "action"),
    "self_healing.jsonl": ("self_healing", "healed"),
}


def _aleph(path: str, payload: Dict, timeout: float = 4.0) -> Dict:
    """Call the ALEPH universal memory service."""
    try:
        req = urllib.request.Request(
            ALEPH_URL + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}


def _aleph_stats() -> Dict:
    try:
        req = urllib.request.Request(ALEPH_URL + "/memory/stats")
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}


def scan_state_files() -> List[Dict]:
    """Scan every state file and produce a per-file summary."""
    summaries = []
    for path in sorted(glob.glob(os.path.join(STATE_DIR, "*.jsonl"))):
        name = os.path.basename(path)
        count = 0
        latest = None
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    count += 1
                    try:
                        latest = json.loads(line)
                    except Exception:
                        pass
        except Exception:
            pass
        summaries.append({
            "file": name, "count": count, "latest": latest,
            "size": os.path.getsize(path) if os.path.exists(path) else 0,
        })
    for name in JSON_FILES:
        path = os.path.join(STATE_DIR, name)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                summaries.append({
                    "file": name, "count": 1, "latest": data,
                    "size": os.path.getsize(path),
                })
            except Exception:
                pass
    return summaries


def extract_metrics(summaries: List[Dict]) -> Dict:
    """Pull the headline numbers from the summaries."""
    metrics = {}
    for s in summaries:
        name = s["file"]
        latest = s.get("latest") or {}
        if name == "are_state.json":
            metrics["engine_cycle"] = latest.get("cycle")
            metrics["engine_verified"] = latest.get("total_verified")
            metrics["engine_attempted"] = latest.get("total_attempted")
        elif name == "portfolio.json":
            metrics["portfolio_cash"] = latest.get("cash")
            metrics["portfolio_positions"] = latest.get("positions")
        elif name == "graduation_exam.jsonl":
            metrics["exam_overall"] = latest.get("overall")
            metrics["exam_tier1"] = latest.get("tier1")
            metrics["exam_tier2"] = latest.get("tier2")
            metrics["exam_tier3"] = latest.get("tier3")
        elif name == "esp32_discovery.jsonl":
            r = (latest.get("result") or {})
            metrics["esp32_fitness"] = r.get("fitness")
        elif name == "self_healing.jsonl":
            metrics["healing_healthy"] = latest.get("healthy")
    return {k: v for k, v in metrics.items() if v is not None}


def consolidate_to_aleph(summaries: List[Dict], metrics: Dict) -> Dict:
    """Inject the consolidated facts into ALEPH (deduplicated)."""
    day = time.strftime("%Y-%m-%d")
    results = {"injected": 0, "errors": 0}
    budget = time.time() + 200   # hard time budget for the whole pass
    # 1. Per-file state summaries (daily-hashed target -> one node per day)
    for s in summaries:
        if time.time() > budget:
            print(f"    [budget] stopping after {results['injected']} injects",
                  flush=True)
            break
        latest = s.get("latest")
        if not latest:
            continue
        # Compact the latest entry to a small string
        try:
            compact = json.dumps(latest, default=str)[:200]
        except Exception:
            compact = str(latest)[:200]
        r = _aleph("/memory/inject", {
            "source": f"consolidation:{s['file']}",
            "relation": f"state_summary:{day}",
            "target": f"{s['count']} entries | {compact}",
            "domain": "memory_consolidation",
        })
        if r.get("ok"):
            results["injected"] += 1
        else:
            results["errors"] += 1
    # 2. Promoted headline metrics (wired in — the PROMOTED map drives this)
    for name, (kind, field) in PROMOTED.items():
        if time.time() > budget:
            break
        latest = next((s.get("latest") or {} for s in summaries
                       if s["file"] == name), None)
        if not latest:
            continue
        val = latest.get(field) or latest
        try:
            val_str = str(val)[:160]
        except Exception:
            val_str = ""
        r = _aleph("/memory/inject", {
            "source": f"promoted:{name}",
            "relation": f"fact:{kind}:{field}",
            "target": val_str,
            "domain": "memory_consolidation",
        })
        if r.get("ok"):
            results["injected"] += 1
        else:
            results["errors"] += 1
    return results


def build_digest(summaries: List[Dict], metrics: Dict, aleph_stats: Dict) -> Dict:
    """The single consolidated memory digest."""
    return {
        "time": time.time(),
        "day": time.strftime("%Y-%m-%d"),
        "state_files": len(summaries),
        "total_entries": sum(s["count"] for s in summaries),
        "metrics": metrics,
        "aleph": aleph_stats,
        "files": [
            {"file": s["file"], "count": s["count"], "size": s["size"]}
            for s in summaries
        ],
    }


def run_cycle() -> Dict:
    print("=" * 60)
    print("🧠 MEMORY CONSOLIDATION LOOP")
    print("=" * 60)
    print("\n[1] SCANNING state files...")
    summaries = scan_state_files()
    print(f"    {len(summaries)} files, "
          f"{sum(s['count'] for s in summaries)} total entries")
    print("\n[2] EXTRACTING headline metrics...")
    metrics = extract_metrics(summaries)
    print(f"    {json.dumps(metrics, default=str)[:200]}")
    print("\n[3] CONSOLIDATING into ALEPH...")
    results = consolidate_to_aleph(summaries, metrics)
    print(f"    injected {results['injected']}, errors {results['errors']}")
    print("\n[4] ALEPH stats...")
    aleph_stats = _aleph_stats()
    print(f"    {json.dumps(aleph_stats)[:150]}")
    print("\n[5] BUILDING the digest...")
    digest = build_digest(summaries, metrics, aleph_stats)
    try:
        with open(DIGEST_PATH, "w") as f:
            json.dump(digest, f, indent=2, default=str)
        print(f"    digest -> {DIGEST_PATH}")
    except Exception as e:
        print(f"    digest write failed: {e}")
    # Log the cycle
    entry = {
        "time": time.time(),
        "files": len(summaries),
        "entries": sum(s["count"] for s in summaries),
        "injected": results["injected"],
        "metrics": metrics,
    }
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"    log write failed: {e}")
    print("\n🎯 Memory consolidated — every agent now sees ONE digest")
    return entry


if __name__ == "__main__":
    run_cycle()
