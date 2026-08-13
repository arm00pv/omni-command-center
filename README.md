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

## Components (added)
- `verified_journal.py` — THE VERIFIED JOURNAL: publishes machine-proven
  science (Lean4 theorems, real-data laws, experiments, exam scoreboard,
  captain's log) to a public HTML journal daily (marquezhv.com/journal/).
- `hypothesis_experiments.py` — the hypothesis + experiment engine:
  tests physical/statistical hypotheses on real sensor data and logs
  PASS/FAIL outcomes for the journal.

## Components (added)
- `proof_decomposition.py` — THE PROOF DECOMPOSITION ENGINE: decomposes
  theorems into sub-goal lanes, proves each lane (ring/omega/linarith/
  rcases/positivity), composes + verifies with the REAL Lean4 kernel,
  publishes to the Proof Lab (journal §7).

## Components (added)
- `compounding_proofs.py` — THE COMPOUNDING THEOREM LIBRARY: generates
  harder theorems that reference the proven library (even of 3-sums via
  even_add, etc.), proves + verifies with the REAL Lean4 kernel — the
  library grows itself.
- `formal_decisions.py` — THE FORMALLY-GROUNDED DECISION CORE: verifies
  the policy invariant set (take-profit, stop-loss, cash non-negativity)
  with Lean4, checks every action against it, grounds in verified memory,
  and ledgers decisions (journal §8).
- `journal_selfcheck.py` — the automated daily journal accuracy gate.

## Components (added)
- `fact_verifier.py` — THE FACT VERIFIER: extracts numeric claims from
  LLM-generated text and verifies each against the ground-truth state —
  publishing the institution's honesty score (journal §9). Contradictions
  are injected into ALEPH so the memory learns its narrator's failures.

## Components (added)
- `grounded_narration.py` — THE GROUNDED NARRATOR: generates the captain's
  log from a verified fact sheet (use ONLY these numbers) — honesty rose
  from 0.5 (ungrounded) to 0.80 (grounded). The trend is published in
  journal §9.

## Components (added)
- `knowledge_acquisition.py` — THE VERIFIED KNOWLEDGE ACQUISITION LOOP:
  candidate claims pass a formal gate (GATE 1 math → Lean4 kernel,
  GATE 2 factual → Brave Search + multi-model, GATE 3 empirical → real
  sensor data). Verified claims become immortal truths; false claims are
  rejected. Journal §10 The Knowledge Gate.

## Components (added)
- `distributed_research.py` — THE DISTRIBUTED VERIFIED RESEARCH NETWORK:
  research campaigns dispatched to the RPi node (tailnet ollama) + the
  throne, every answer verified on the throne (Lean4 kernel for math,
  cross-model for facts). Journal §11.

## Components (added)
- `verified_knowledge.py` — THE VERIFIED KNOWLEDGE PORTAL: a public,
  searchable index of every verified entry (ALEPH truths, Proof Lab,
  Knowledge Gate, Distributed Network, Decision Ledger) with its
  verification path. Served at marquezhv.com/knowledge/.

## Components (added)
- `tactic_search.py` — THE TACTIC-SEARCH PROVER: kernel-driven proof
  search (NO torch — immune to RAM windows). Batched Lean4 verification
  solves the graduation exam at 19/20 (95%) in ~20s vs the ML prover's
  45%. The exam now falls back to it when the ML prover is down.
