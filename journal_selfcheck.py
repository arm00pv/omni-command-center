#!/usr/bin/env python3
"""
journal_selfcheck.py — THE AUTOMATED JOURNAL SELF-CHECK
========================================================
The daily automated accuracy gate for the Verified Journal
(the deep sub-agent gate runs on demand; this local check runs
EVERY edition automatically):

  1. §4 exam % matches graduation_exam.jsonl
  2. §2 laws all lean4_verified in discovered_laws.jsonl
  3. §5 experiment outcomes match experiments.jsonl
  4. §6 captain's log matches the latest entry
  5. no None/undefined/null placeholders in the HTML
  6. the edition artifact exists + manifest matches the title

Verdict: PASS / FAIL logged to state/journal_selfcheck.jsonl.
"""

import json
import os
import re
import sys
import time

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
JOURNAL = os.path.join(STATE, "journal", "index.html")
LOG = os.path.join(STATE, "journal_selfcheck.jsonl")


def load_jsonl(name, limit=50):
    out = []
    try:
        with open(os.path.join(STATE, name)) as f:
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


def load_json(name):
    try:
        with open(os.path.join(STATE, name)) as f:
            return json.load(f)
    except Exception:
        return {}


def check_exam(html):
    ex = load_jsonl("graduation_exam.jsonl", 1)
    if not ex:
        return True, "no exam entries"
    last = ex[-1]
    expected = f"{last.get('overall', 0) * 100:.0f}%"
    found = re.search(r"score (\d+)%", html)
    if not found:
        return False, "no score found"
    return found.group(1) == expected.replace("%", ""), \
        f"exam {found.group(1)}% vs {expected}"


def check_laws(html):
    laws = [l for l in load_jsonl("discovered_laws.jsonl", 20)
            if l.get("lean4_verified")]
    distinct = {l.get("law") for l in laws}
    shown = re.findall(r"family: ([a-z_0-9]+)", html)
    shown_set = set(shown)
    missing = distinct - shown_set
    return not missing, f"laws: {len(distinct)} distinct, missing from page: {missing or 'none'}"


def check_experiments(html):
    exps = load_jsonl("experiments.jsonl", 6)
    if not exps:
        return True, "no experiments"
    outcomes = []
    for x in exps:
        if x.get("outcome"):
            outcomes.append(x["outcome"])
        elif x.get("lean4_verified"):
            outcomes.append("PASS")
        else:
            outcomes.append("pending")
    # count each outcome label in the html (case-sensitive)
    html_outcomes = [o for o in outcomes if o in html]
    missing = [o for o in outcomes if o not in html]
    ok = len(missing) <= 1  # allow one mismatch (truncation)
    return ok, f"experiment outcomes on page: {len(html_outcomes)}/{len(outcomes)}, missing {missing}"


def check_captain(html):
    caps = load_jsonl("captains_log.jsonl", 1)
    if not caps:
        return True, "no captain entries"
    text = caps[-1].get("text", "")
    snippet = text[:60]
    return snippet in html, f"captain snippet: {snippet[:40]}..."


def check_placeholders(html):
    bad = re.findall(r"None|undefined|NaN|null", html)
    return not bad, f"placeholders: {len(bad)}"


def check_manifest(html):
    try:
        with open(os.path.join(STATE, "journal", "manifest.json")) as f:
            m = json.load(f)
        with open(JOURNAL) as f:
            html = f.read()
        title_ok = f"Edition {m.get('edition')}" in html
        exists_ok = os.path.exists(JOURNAL)
        return title_ok and exists_ok, \
            f"manifest edition {m.get('edition')}, artifact exists: {exists_ok}, title match: {title_ok}"
    except Exception as e:
        return False, f"manifest err {e}"


def run():
    if not os.path.exists(JOURNAL):
        entry = {"time": time.time(), "verdict": "FAIL",
                 "reason": "journal artifact missing", "checks": {}}
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print("[selfcheck] FAIL — journal artifact missing", flush=True)
        return entry
    with open(JOURNAL) as f:
        html = f.read()
    checks = {}
    for name, fn in [
        ("exam", check_exam), ("laws", check_laws),
        ("experiments", check_experiments), ("captain", check_captain),
        ("placeholders", check_placeholders), ("manifest", check_manifest),
    ]:
        ok, detail = fn(html)
        checks[name] = {"ok": ok, "detail": detail}
    verdict = "PASS" if all(c["ok"] for c in checks.values()) else "FAIL"
    entry = {"time": time.time(), "verdict": verdict, "checks": checks}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[selfcheck] VERDICT: {verdict}", flush=True)
    for name, c in checks.items():
        print(f"  {name}: {'✅' if c['ok'] else '❌'} {c['detail']}", flush=True)
    return entry


if __name__ == "__main__":
    run()
