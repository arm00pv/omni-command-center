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

## Components (added)
- `verified_answers.py` — THE VERIFIED ANSWER ENGINE: ask the institution
  anything — math claims get kernel-verified proofs, factual questions hit
  the verified index, empirical questions read the real sensors, unknown
  questions get the honest "unverifiable" answer. Served at
  marquezhv.com/knowledge/ (Ask box).

## Components (added)
- `research_planner.py` — THE SELF-DIRECTED RESEARCH PLANNER: analyzes the
  system's gaps (exam failures, unverified claims), plans the next target
  set, executes it with the kernel (8/14 gap closure — the Nat-subtraction
  family filled), and publishes the agenda (journal §13).

## Upgrade
- `verified_answers.py` — WEB-GROUNDED answers: when the local verified
  index has no match, the engine searches Brave and answers with a real
  citation, honestly labeled "web-sourced — NOT formally verified"
  ("what is the capital of France" → "Paris …" via Wikipedia).

## Components (added)
- `tactic_learner.py` — THE TACTIC LEARNER: computes family-aware tactic
  success from real kernel outcomes (ring = the exam workhorse, 13 wins)
  and produces the priority map the search prover consumes — the proving
  strategy learns from its own results. Journal §14.

## Components (added)
- `institution_report.py` — THE STATE-OF-THE-INSTITUTION REPORT: the
  institution's public annual report — learning curves (exam 40%→75%,
  honesty 31%→80%), the proving stack, the verification layer, the
  physical layer, the open agenda. Served at marquezhv.com/report/.
  Weekly cron.

## Components (added)
- `knowledge_trader.py` — THE KNOWLEDGE-DRIVEN TRADER: trading signals from
  the verified knowledge (trend laws on real price histories), risk from
  the Lean4-proven invariants, and an HONEST walk-forward backtest (SPY
  +15%, Sharpe 1.00; cardano −64.8% — the truth). Journal §15.

## Components (added)
- `conjecture_mine.py` — THE CONJECTURE MINE: discovers NOVEL theorems by
  structurally generalizing the verified corpus (Nat→ℝ, 2→3 variables,
  add→mul swaps) — 8 NEW truths struck, 6 rejected by the kernel
  (including the false conjectures correctly refuted). Journal §16.
