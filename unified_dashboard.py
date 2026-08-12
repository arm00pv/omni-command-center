"""
unified_dashboard.py — THE GRAND UNIFIED DASHBOARD
===================================================
ONE live operational view of the entire OMNI-BRAIN:

  Sections (all LIVE, auto-refresh):
    1. Services      — every port probed (8181/8182/8189/8195/8196/8197/8765/9180)
                       + the ESP32 ingest daemon
    2. ALEPH         — graph nodes, edges, verified truths
    3. Engine        — cycles, verified theorems, attempted
    4. Exam          — graduation exam history + latest scores
    5. Trader        — portfolio, cash, positions
    6. ESP32         — live physical sensor (real MCU temperature)
    7. Discoveries   — esp32 fitness, autonomous discoveries, laws
    8. Predictions   — honest hit rate
    9. Self-healing  — recent recoveries
   10. Memory        — the consolidation digest (one view of all memory)
   11. Recent events — latest entries across the state files

Served on :8198 (self-healing guarded). API: /api/state (JSON).
"""

import json
import os
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ARE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(ARE_DIR, "state")
PORT = 8198

SERVICES = [
    ("8181", "OMNI-API (gallery+theology+esp32)"),
    ("8182", "OIF PubSub Bus"),
    ("8189", "Prover (fine-tuned Lean4)"),
    ("8195", "OMNI-API Service (proving product)"),
    ("8196", "ALEPH Universal Memory"),
    ("8197", "OMNI-Agent Platform"),
    ("8765", "WebSocket Server"),
    ("9180", "Verify API (Lean4)"),
]

EVENT_FILES = [
    "graduation_exam.jsonl", "autonomous_discovery.jsonl",
    "esp32_discovery.jsonl", "self_healing.jsonl",
    "knowledge_decisions.jsonl", "research_swarm.jsonl",
    "memory_agent_runtime.jsonl", "math_paper.jsonl",
    "prediction_validation.jsonl", "memory_consolidation.jsonl",
    "distributed_prover.jsonl", "trade_first_cycle.jsonl",
]


def port_up(port: str) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        r = s.connect_ex(("127.0.0.1", int(port)))
        s.close()
        return r == 0
    except Exception:
        return False


def load_jsonl(name: str, limit: int = 5):
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


def load_json(name: str):
    try:
        with open(os.path.join(STATE_DIR, name)) as f:
            return json.load(f)
    except Exception:
        return {}


def esp32_live():
    """Latest ESP32 sensor reading (serial + wifi both land in the daily log)."""
    import glob
    day = time.strftime("%Y%m%d")
    path = os.path.join(ARE_DIR, "real_data", f"esp32_{day}.jsonl")
    try:
        with open(path) as f:
            lines = [l for l in f if l.strip()]
        if lines:
            return json.loads(lines[-1])
    except Exception:
        pass
    return None


def prediction_hit_rate():
    """Honest hit rate from the prediction validation log."""
    recs = load_jsonl("prediction_validations.jsonl", 1000)
    if not recs:
        return None
    correct = sum(1 for r in recs if r.get("validated") is True)
    total = len(recs)
    return {"correct": correct, "total": total,
            "rate": round(correct / total, 3) if total else 0}


def gather_state() -> dict:
    state = {
        "time": time.time(),
        "services": [
            {"port": p, "name": n, "up": port_up(p)} for p, n in SERVICES
        ],
        "esp32_daemon": os.path.exists("/tmp/esp32_ingest.pid"),
        "aleph": load_json("memory_digest.json").get("aleph") or {},
        "engine": {
            "cycle": None, "verified": None, "attempted": None,
        },
        "exam": load_jsonl("graduation_exam.jsonl", 8),
        "trader": load_json("portfolio.json"),
        "esp32": esp32_live(),
        "discoveries": {
            "esp32": load_jsonl("esp32_discovery.jsonl", 3),
            "autonomous": load_jsonl("autonomous_discovery.jsonl", 3),
            "laws": load_jsonl("discovered_laws.jsonl", 3),
        },
        "predictions": prediction_hit_rate(),
        "self_healing": load_jsonl("self_healing.jsonl", 5),
        "memory_digest": load_json("memory_digest.json"),
        "events": {},
    }
    # Engine numbers
    are_state = load_json("are_state.json")
    state["engine"] = {
        "cycle": are_state.get("cycle"),
        "verified": are_state.get("total_verified"),
        "attempted": are_state.get("total_attempted"),
    }
    # Recent events across the state files
    for f in EVENT_FILES:
        recs = load_jsonl(f, 1)
        if recs:
            state["events"][f] = recs[-1]
    # Captain's log — the system's own narration
    logs = load_jsonl("captains_log.jsonl", 1)
    state["captains_log"] = logs[-1] if logs else None
    return state


HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🌌 OMNI-BRAIN — Grand Unified Dashboard</title>
<style>
:root { --bg:#0b0e14; --card:#12161f; --line:#1f2633; --txt:#d7e0ee;
        --dim:#7a8699; --ok:#3ddc84; --bad:#ff5d5d; --acc:#5b8cff; }
* { box-sizing:border-box; margin:0; padding:0; }
body { background:var(--bg); color:var(--txt); font-family:'Segoe UI',system-ui,sans-serif; padding:18px; }
h1 { font-size:20px; margin-bottom:4px; }
.sub { color:var(--dim); font-size:12px; margin-bottom:18px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; }
.card h2 { font-size:13px; color:var(--acc); text-transform:uppercase; letter-spacing:.08em; margin-bottom:10px; }
.row { display:flex; justify-content:space-between; padding:3px 0; font-size:13px; }
.row .k { color:var(--dim); }
.big { font-size:26px; font-weight:700; }
.ok { color:var(--ok); } .bad { color:var(--bad); }
.pill { display:inline-block; padding:2px 8px; border-radius:20px; font-size:11px; }
.pill.ok { background:rgba(61,220,132,.12); } .pill.bad { background:rgba(255,93,93,.12); }
pre { font-size:11px; color:var(--dim); white-space:pre-wrap; word-break:break-all; max-height:140px; overflow:auto; }
#stamp { color:var(--dim); font-size:11px; margin-top:14px; }
</style>
</head>
<body>
<h1>🌌 OMNI-BRAIN — Grand Unified Dashboard</h1>
<div class="sub">One live view of the whole organism · auto-refresh 10s</div>
<div class="grid" id="grid"></div>
<div id="stamp"></div>
<script>
async function refresh() {
  try {
    const r = await fetch('api/state');
    const s = await r.json();
    render(s);
  } catch(e) { document.getElementById('stamp').textContent = 'offline: ' + e; }
}
function esc(x){ return String(x==null?'':x).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function card(title, body){ return '<div class="card"><h2>'+title+'</h2>'+body+'</div>'; }
function render(s){
  let g = '';
  // 1. Services
  let svc = '';
  for (const v of s.services) {
    svc += '<div class="row"><span class="k">'+esc(v.name)+'</span>'+
           '<span class="pill '+(v.up?'ok':'bad')+'">'+(v.up?'UP':'DOWN')+'</span></div>';
  }
  svc += '<div class="row"><span class="k">ESP32 ingest daemon</span>'+
         '<span class="pill '+(s.esp32_daemon?'ok':'bad')+'">'+(s.esp32_daemon?'UP':'DOWN')+'</span></div>';
  g += card('Services', svc);
  // 2. ALEPH
  const a = s.aleph || {};
  g += card('ALEPH Graph', '<div class="row"><span class="k">nodes</span><span class="big">'+esc(a.nodes)+'</span></div>'+
    '<div class="row"><span class="k">edges</span><span class="big">'+esc(a.edges)+'</span></div>'+
    '<div class="row"><span class="k">verified truths</span><span class="big ok">'+esc(a.verified)+'</span></div>');
  // 3. Engine
  const e = s.engine || {};
  g += card('Engine', '<div class="row"><span class="k">cycles</span><span class="big">'+esc(e.cycle)+'</span></div>'+
    '<div class="row"><span class="k">verified theorems</span><span class="big ok">'+esc(e.verified)+'</span></div>'+
    '<div class="row"><span class="k">attempted</span><span>'+esc(e.attempted)+'</span></div>');
  // 4. Exam
  let ex = '';
  const hist = (s.exam||[]).map(x=>x.overall).join(' → ');
  if (s.exam && s.exam.length) {
    const last = s.exam[s.exam.length-1];
    ex = '<div class="row"><span class="k">latest</span><span class="big">'+(last.overall*100).toFixed(0)+'%</span></div>'+
         '<div class="row"><span class="k">tiers</span><span>'+Math.round(last.tier1*100)+' / '+Math.round(last.tier2*100)+' / '+Math.round(last.tier3*100)+'</span></div>'+
         '<div class="row"><span class="k">history</span><span>'+esc(hist)+'</span></div>';
  } else ex = '<div class="row"><span class="k">no exam yet</span></div>';
  g += card('Graduation Exam', ex);
  // 5. Trader
  const t = s.trader || {};
  let pos = '';
  for (const [k,v] of Object.entries(t.positions||{})) pos += '<div class="row"><span class="k">'+esc(k)+'</span><span>'+esc(v)+'</span></div>';
  g += card('Trader', '<div class="row"><span class="k">cash</span><span class="big">$'+esc(t.cash)+'</span></div>'+pos);
  // 6. ESP32
  const sp = s.esp32;
  g += card('ESP32 Sensor (real)', sp ?
    '<div class="row"><span class="k">temp</span><span class="big">'+esc(sp.temp_c)+'°C</span></div>'+
    '<div class="row"><span class="k">reading</span><span>#'+esc(sp.index)+'</span></div>'+
    '<div class="row"><span class="k">t</span><span>'+esc(sp.t_seconds)+'s</span></div>' :
    '<div class="row"><span class="k">no readings yet</span></div>');
  // 7. Discoveries
  let d = '';
  const d32 = (s.discoveries||{}).esp32||[];
  if (d32.length) { const r = d32[d32.length-1].result||{};
    d += '<div class="row"><span class="k">esp32 law fit</span><span class="ok">'+esc(r.fitness)+'</span></div>'; }
  const laws = (s.discoveries||{}).laws||[];
  if (laws.length) d += '<div class="row"><span class="k">laws</span><span>'+esc(laws.length)+'</span></div>';
  const auto = (s.discoveries||{}).autonomous||[];
  if (auto.length) d += '<div class="row"><span class="k">autonomous</span><span>'+esc(auto.length)+'</span></div>';
  g += card('Discoveries', d || '<div class="row"><span class="k">none yet</span></div>');
  // 8. Predictions
  const p = s.predictions;
  g += card('Predictions', p ?
    '<div class="row"><span class="k">hit rate</span><span class="big">'+(p.rate*100).toFixed(1)+'%</span></div>'+
    '<div class="row"><span class="k">correct/total</span><span>'+esc(p.correct)+'/'+esc(p.total)+'</span></div>' :
    '<div class="row"><span class="k">no validations yet</span></div>');
  // 9. Self-healing
  let h = '';
  for (const r of (s.self_healing||[]).slice(-3)) {
    h += '<div class="row"><span class="k">'+esc(new Date(r.time*1000).toLocaleTimeString())+'</span>'+
         '<span>'+(r.healthy||0)+'/'+(r.down?r.down.length:0)+'</span></div>';
  }
  g += card('Self-Healing', h || '<div class="row"><span class="k">no records</span></div>');
  // 10. Memory digest
  const md = s.memory_digest || {};
  g += card('Memory Consolidation', '<div class="row"><span class="k">state files</span><span>'+esc(md.state_files)+'</span></div>'+
    '<div class="row"><span class="k">total entries</span><span>'+esc(md.total_entries)+'</span></div>'+
    '<div class="row"><span class="k">day</span><span>'+esc(md.day)+'</span></div>');
  // 11. Recent events
  let ev = '';
  for (const [f, v] of Object.entries(s.events||{})) {
    ev += '<div class="row"><span class="k">'+esc(f.replace('.jsonl',''))+'</span></div>'+
          '<pre>'+esc(JSON.stringify(v).slice(0,160))+'</pre>';
  }
  g += card('Recent Events', ev);
  // 12. Captain's Log
  const cl = s.captains_log;
  g += card("📖 Captain's Log — "+esc(cl?cl.day:'pending'),
    cl ? '<pre style="color:var(--txt);max-height:220px">'+esc(cl.text)+'</pre>' :
         '<div class="row"><span class="k">daily narration runs at end of day</span></div>');
  document.getElementById('grid').innerHTML = g;
  document.getElementById('stamp').textContent = 'updated ' + new Date(s.time*1000).toLocaleTimeString();
}
setInterval(refresh, 10000);
refresh();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/api/state"):
            body = json.dumps(gather_state()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def main():
    print(f"[unified_dashboard] serving on :{PORT}", flush=True)
    while True:
        try:
            srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
            srv.serve_forever()
        except Exception as e:
            print(f"[unified_dashboard] crash {e} — restarting in 10s", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
