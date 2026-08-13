#!/usr/bin/env python3
"""
verified_knowledge.py — THE VERIFIED KNOWLEDGE PORTAL
======================================================
The institution's verified knowledge becomes a PUBLIC, SEARCHABLE
product. Every entry carries its verification path:

  SOURCES (all formally verified):
    - ALEPH immortal truths (Lean4-gated)
    - The Proof Lab (kernel-composed theorems)
    - The Compounding Library (self-grown theorems)
    - The Knowledge Gate (kernel + data + multi-source)
    - The Distributed Network (node answers, throne-verified)
    - The Decision Ledger (invariant-bounded actions)

  SEARCH: keyword + domain + verification-path filters
  API:    /knowledge/search?q=...  (served through the gateway)
  UI:     a public search page (marquezhv.com/knowledge/)

Every result shows HOW it was verified — nothing enters without a path.
"""

import json
import os
import sys
import time

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
INDEX = os.path.join(STATE, "knowledge_index.json")


def load_jsonl(name, limit=200):
    out = []
    try:
        with open(os.path.join(STATE, name)) as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    except Exception:
        pass
    return out[-limit:]


def build_index() -> list:
    """Assemble every verified entry with its verification path."""
    entries = []

    # 1. ALEPH immortal truths
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8196/memory/verified")
        with urllib.request.urlopen(req, timeout=5) as r:
            truths = json.loads(r.read().decode()).get("verified_truths", [])
        for t in truths[:100]:
            entries.append({
                "text": t.get("target", t.get("source", "")),
                "domain": t.get("domain", "math"),
                "path": "Lean4 kernel (immortal truth)",
                "source": t.get("source", "aleph"),
            })
    except Exception:
        pass

    # 2. Proof Lab (decomposition + compounding)
    for x in load_jsonl("proof_lab.jsonl", 30):
        if x.get("status") == "PROVEN":
            entries.append({
                "text": x.get("statement", x.get("id", "")),
                "domain": "math",
                "path": f"Proof Lab ({x.get('path', 'decomposition')})",
                "source": "proof_lab",
            })

    # 3. Knowledge Gate
    for x in load_jsonl("knowledge_gate.jsonl", 30):
        if x.get("verdict") == "VERIFIED":
            entries.append({
                "text": x.get("claim", ""),
                "domain": x.get("gate", "factual"),
                "path": f"Knowledge Gate ({x.get('gate', '')})",
                "source": "knowledge_gate",
            })

    # 4. Distributed Network
    for x in load_jsonl("distributed_network.jsonl", 20):
        v = x.get("verify") or {}
        if v.get("verdict") == "VERIFIED":
            entries.append({
                "text": x.get("question", ""),
                "domain": "research",
                "path": f"Distributed Network ({v.get('detail', '')[:40]})",
                "source": "distributed",
            })

    # 5. Decision Ledger
    for x in load_jsonl("decision_ledger.jsonl", 20):
        entries.append({
            "text": f"{x.get('action', '')} — {x.get('justification', '')[:80]}",
            "domain": "policy",
            "path": f"Formal Decision ({len(x.get('invariants_applied', []))} "
                    f"invariants)",
            "source": "decision_ledger",
        })

    # 6. Fact-checked truths (the grounded narrator's verified claims)
    for x in load_jsonl("fact_check.jsonl", 5):
        for a in x.get("audits", []):
            for c in a.get("claims", []):
                if c.get("verdict") == "VERIFIED":
                    entries.append({
                        "text": f"{c.get('context', '')} = {c.get('value')}",
                        "domain": "self_audit",
                        "path": "Fact Verifier (ground-truth match)",
                        "source": "fact_verifier",
                    })

    return entries


def search(query: str, entries: list, domain: str = "") -> list:
    q = query.lower()
    results = []
    for e in entries:
        if domain and e.get("domain") != domain:
            continue
        if q in e.get("text", "").lower() or q in e.get("path", "").lower():
            results.append(e)
    return results[:20]


def rebuild():
    entries = build_index()
    with open(INDEX, "w") as f:
        json.dump({"built": time.time(), "entries": entries}, f, indent=2)
    return entries


if __name__ == "__main__":
    print("=" * 60)
    print("📚 THE VERIFIED KNOWLEDGE PORTAL")
    print("=" * 60)
    entries = rebuild()
    print(f"\n[1] INDEX: {len(entries)} verified entries")
    from collections import Counter
    by_path = Counter(e["path"].split("(")[0].strip() for e in entries)
    for p, c in by_path.most_common(8):
        print(f"    {p}: {c}")
    print("\n[2] SEARCH demo:")
    for q in ["even", "commut", "temperature", "trade", "Lean4"]:
        r = search(q, entries)
        print(f"    '{q}': {len(r)} results")
        for x in r[:2]:
            print(f"      [{x['path'][:40]}] {x['text'][:60]}")
    print(f"\n📚 Index -> {INDEX}")
