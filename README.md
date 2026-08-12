# OMNI-COMMAND-CENTER

The operational brain of an autonomous research institution — one live
view, one consolidated memory, and a self-narration.

## Components
- `unified_dashboard.py` — Grand Unified Dashboard (:8198): live services
  probe, ALEPH graph stats, engine cycles, exam history, trader, ESP32
  real sensor, discoveries, predictions, self-healing, memory digest,
  recent events + the Captain's Log card. Single-page HTML + `/api/state`.
- `memory_consolidation.py` — consolidates the system's fragmented state
  files into the universal memory (ALEPH) + one digest
  (`memory_digest.json`).
- `captains_log.py` — daily LLM-written narrative of the day's activity
  (local qwen3.5:0.8b, `"think": false`), stored in ALEPH.

## Run
```bash
python unified_dashboard.py        # :8198
python memory_consolidation.py     # daily
python captains_log.py             # daily (end of day)
```
All three are self-healing guarded (restart on failure) + cron'd.
