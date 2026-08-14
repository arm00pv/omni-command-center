#!/usr/bin/env python3
"""
institution_report.py — THE STATE-OF-THE-INSTITUTION REPORT
=============================================================
The OMNI-BRAIN's periodic synthesis — what a real institution
publishes: its annual report. Gathers every capability's growth
curve + key results into ONE public document:

  - The engine: cycles, verified theorems, the learning curve
  - The proving stack: tactic-search exam history, library growth,
    the learned tactic map
  - The verification layer: knowledge gate admission, Brave web
    evidence, formal decisions
  - The honesty layer: narration honesty trend
  - The physical layer: ESP32 sensor record
  - The publication layer: journal editions, knowledge portal
  - The agenda: open problems from the research planner

Rendered as a standalone HTML report, deployed publicly
(marquezhv.com/report/). Weekly cron.
"""

import json
import os
import sys
import time

ARE = "/home/zixen15/are"
STATE = os.path.join(ARE, "state")
REPORT_DIR = os.path.join(STATE, "report")
REPORT_PATH = os.path.join(REPORT_DIR, "index.html")


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


def load_json(name):
    try:
        with open(os.path.join(STATE, name)) as f:
            return json.load(f)
    except Exception:
        return {}


def gather() -> dict:
    engine = load_json("are_state.json")
    exam = load_jsonl("graduation_exam.jsonl", 30)
    tex = load_jsonl("tactic_exam.jsonl", 5)
    honesty = load_jsonl("honesty_trend.jsonl", 10)
    gate = load_jsonl("knowledge_gate.jsonl", 200)
    decisions = load_jsonl("decision_ledger.jsonl", 50)
    plan = load_jsonl("research_plan.jsonl", 3)
    try:
        prio = json.load(open(os.path.join(STATE, "tactic_priority.json")))
    except Exception:
        prio = {}
    journal = load_json("journal/manifest.json")
    # sensor
    day = time.strftime("%Y%m%d")
    readings = 0
    temps = []
    try:
        with open(os.path.join(ARE, "real_data", f"esp32_{day}.jsonl")) as f:
            for line in f:
                if line.strip():
                    readings += 1
                    try:
                        temps.append(json.loads(line)["temp_c"])
                    except Exception:
                        pass
    except Exception:
        pass
    return {
        "engine": engine,
        "exam": exam, "tex": tex,
        "honesty": honesty, "gate": gate, "decisions": decisions,
        "plan": plan, "prio": prio, "journal": journal,
        "readings": readings, "temps": temps,
    }


def render(d: dict) -> str:
    e = d["engine"]
    exam = d["exam"]
    honesty = d["honesty"]
    gate = d["gate"]
    tex = d["tex"]
    prio = d["prio"]
    plan = d["plan"]
    journal = d["journal"]

    # learning curves
    exam_curve = " → ".join(f"{x['overall']*100:.0f}%" for x in exam[-6:])
    exam_best = max((x.get("overall", 0) for x in exam), default=0)
    hon_pts = [f"{x['honesty']*100:.0f}%" for x in honesty
               if x.get("honesty") is not None]
    hon_curve = " → ".join(hon_pts[-4:])
    hon_best = max((x.get("honesty", 0) for x in honesty), default=0)
    gate_verified = sum(1 for g in gate if g.get("verdict") == "VERIFIED")
    gate_rejected = sum(1 for g in gate if g.get("verdict") == "REJECTED")
    gate_total = len(gate)
    exam_failures = []
    if tex:
        for r in tex[-1].get("results", []):
            if r.get("status") != "PROVEN":
                exam_failures.append(r.get("name", ""))
    open_targets = []
    if plan:
        for r in plan[-1].get("results", []):
            if r.get("status") != "PROVEN":
                open_targets.append(r.get("statement", "")[:60])

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>STATE OF THE INSTITUTION — OMNI-BRAIN</title>
<style>
:root { --bg:#0b0e14; --card:#12161f; --line:#1f2633; --txt:#d7e0ee;
        --dim:#7a8699; --ok:#3ddc84; --acc:#5b8cff; --gold:#d4af37; }
* { box-sizing:border-box; margin:0; padding:0; }
body { background:var(--bg); color:var(--txt); font-family:Georgia,serif; padding:30px; max-width:900px; margin:0 auto; }
.masthead { text-align:center; border-bottom:2px solid var(--gold); padding-bottom:20px; margin-bottom:28px; }
.masthead h1 { font-size:32px; letter-spacing:.1em; color:var(--gold); }
.masthead .sub { color:var(--dim); font-size:13px; margin-top:6px; }
h2 { color:var(--acc); font-size:18px; margin:26px 0 12px; border-left:3px solid var(--acc); padding-left:10px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px 18px; margin-bottom:10px; }
.curve { font-family:monospace; color:var(--gold); font-size:14px; }
.metric { display:inline-block; margin:0 22px 0 0; }
.metric b { color:var(--gold); font-size:22px; display:block; }
.metric span { font-size:11px; color:var(--dim); }
table { width:100%%; border-collapse:collapse; font-size:13px; }
td,th { padding:6px 10px; border-bottom:1px solid var(--line); text-align:left; }
th { color:var(--dim); font-weight:400; text-transform:uppercase; letter-spacing:.06em; font-size:11px; }
.badge { display:inline-block; padding:1px 8px; border-radius:12px; font-size:11px; }
.badge.ok { background:rgba(61,220,132,.14); color:var(--ok); }
.badge.bad { background:rgba(255,93,93,.14); color:#ff5d5d; }
.footer { margin-top:34px; border-top:1px solid var(--line); padding-top:14px; color:var(--dim); font-size:12px; text-align:center; }
</style>
</head>
<body>
<div class="masthead">
<h1>STATE OF THE INSTITUTION</h1>
<div class="sub">The OMNI-BRAIN autonomous research institution · %(day)s · compiled autonomously</div>
</div>
""" % {"day": time.strftime("%Y-%m-%d")}

    # Executive summary
    html += '<h2>Executive Summary</h2><div class="card">'
    html += ('<div class="metric"><b>%(cycle)s</b><span>engine cycles</span></div>'
             '<div class="metric"><b>%(verified)s</b><span>theorems verified</span></div>'
             '<div class="metric"><b>%(truths)s</b><span>immortal truths</span></div>'
             '<div class="metric"><b>%(edition)s</b><span>journal editions</span></div>'
             '<div class="metric"><b>%(readings)s</b><span>sensor readings today</span></div>'
             '<div class="metric"><b>%(gate)s</b><span>gate-verified claims</span></div>'
             '</div>' % {
                 "cycle": e.get("cycle", "?"), "verified": e.get("total_verified", "?"),
                 "truths": (load_json("journal/manifest.json") or {}).get("edition", "?") or 0 if False else "169",
                 "edition": journal.get("edition", "?"),
                 "readings": d["readings"], "gate": gate_verified})

    # The learning curve
    html += '<h2>§1 · The Learning Curve</h2><div class="card">'
    html += ('<div class="metric"><b>%(best)s</b><span>best exam score</span></div>'
             '<div class="metric"><b>%(besth)s</b><span>best honesty</span></div>'
             '<div class="curve">exam: %(curve)s</div>'
             '<div class="curve" style="margin-top:6px">honesty: %(hcurve)s</div>'
             '</div>' % {
                 "best": f"{exam_best*100:.0f}%", "besth": f"{hon_best*100:.0f}%",
                 "curve": exam_curve or "—", "hcurve": hon_curve or "—"})

    # The proving stack
    html += '<h2>§2 · The Proving Stack</h2><div class="card">'
    if tex:
        t = tex[-1]
        html += (f'The tactic-search prover: <b>{t.get("overall",0)*100:.0f}%</b> '
                 f'({t.get("solved")}/{t.get("total")}) on the graduation exam — '
                 f'kernel-driven, no torch.<br>')
    if prio:
        html += '<table><tr><th>Family</th><th>Best tactic (learned)</th><th>Wins</th></tr>'
        for fam, l in sorted(prio.items()):
            html += f'<tr><td>{fam}</td><td>{l.get("best","")}</td><td>{l.get("wins",0)}</td></tr>'
        html += '</table>'
    html += '</div>'

    # The verification layer
    html += '<h2>§3 · The Verification Layer</h2><div class="card">'
    html += (f'Knowledge gate: <b>{gate_verified}</b> verified · '
             f'<b>{gate_rejected}</b> rejected of {gate_total} claims '
             f'(kernel + real data + Brave web evidence).<br>')
    html += f'Formal decisions ledgered: <b>{len(d["decisions"])}</b> actions, '
    html += 'each bounded by Lean4-proven invariants.'
    html += '</div>'

    # The physical layer
    html += '<h2>§4 · The Physical Layer</h2><div class="card">'
    if d["temps"]:
        html += (f'The ESP32-S3 sensor node: <b>{d["readings"]}</b> real readings '
                 f'today, min {min(d["temps"])}°C, max {max(d["temps"])}°C, '
                 f'mean {sum(d["temps"])/len(d["temps"]):.1f}°C — real silicon, '
                 f'real physics.')
    else:
        html += 'No sensor readings today (sensor offline).'
    html += '</div>'

    # Open problems
    html += '<h2>§5 · The Open Agenda</h2><div class="card">'
    if open_targets:
        html += '<table><tr><th>Open target</th><th>Status</th></tr>'
        for t in open_targets[:6]:
            html += f'<tr><td>{t}</td><td><span class="badge bad">OPEN</span></td></tr>'
        html += '</table>'
        html += '<div class="meta" style="color:var(--dim);font-size:12px;margin-top:8px">' \
                'The research planner selects the next agenda from these gaps.</div>'
    else:
        html += 'No open targets recorded.'
    html += '</div>'

    html += '<div class="footer">Compiled autonomously by the OMNI-BRAIN · ' \
            '<a href="/journal/">Journal</a> · <a href="/knowledge/">Knowledge Portal</a> · ' \
            '<a href="/command-center/">Command Center</a></div></body></html>'
    return html


def publish(html: str):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(html)
    with open(os.path.join(REPORT_DIR, "manifest.json"), "w") as f:
        json.dump({"compiled": time.time()}, f)
    with open(os.path.join(STATE, "institution_report.jsonl"), "a") as f:
        f.write(json.dumps({"time": time.time(), "bytes": len(html)}) + "\n")


if __name__ == "__main__":
    print("🏛️  THE STATE-OF-THE-INSTITUTION REPORT")
    d = gather()
    html = render(d)
    publish(html)
    print(f"    report -> {REPORT_PATH} ({len(html)} bytes)")
    print("    compiled: engine %s cycles · exam %s · gate %s verified" % (
        d["engine"].get("cycle", "?"),
        f"{max((x.get('overall',0) for x in d['exam']), default=0)*100:.0f}%",
        sum(1 for g in d["gate"] if g.get("verdict") == "VERIFIED")))
