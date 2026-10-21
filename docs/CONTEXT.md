# Immediate Operational Context

Use [EXECUTION_GUIDE_CURRENT.md](../EXECUTION_GUIDE_CURRENT.md) as operational authority, [PROGRESS.md](PROGRESS.md) for current status, [ANALYSIS_REGISTRY.md](ANALYSIS_REGISTRY.md) for the frozen scientific plan, and `Ledgers/` for technical/history detail.

## Current state

- Group A completed A0-A6 and is no longer participating. Agrim is the sole project owner and human reviewer from now on.
- Figshare has 50 subjects: 33 mild, 17 moderate, no severe. T3 is feasible under the documented contralateral lesion-side assumption, not imaging confirmation.
- G8f is primary (`N_fixed=15`); G24f is registered secondary T6 (`N_fixed=6`). Both graph tables have 48 subjects after label-blind exclusion of sub-13 and sub-40, both moderate.
- Group A fixed artifact screening before sampling and regenerated/provenanced graph outputs. Residual epoch-count correlation and seed instability must be reported.
- Retain 04/05, 11/15 and 47/49 as distinct subjects. Their identical/highly similar EEG remains an unresolved dependence limitation. All named channels are identical for 04/05; demographics/location differ.
- B1 and the B2/B3 engine are implemented. Option 3 synthetic validation passed: Gate A p=.005; Gate B 168/200 (84%, exact 95% CI 78.17-88.79%). Original failures remain preserved; the last complete suite had 32 passing tests.
- The registry includes T1-T9, nine-test Holm correction, nested standardized Ridge, exact tails/seeds/failure rules, and a separate descriptive grouped-split sensitivity for T1-T6.
- The separate sensitivity runner/config/tests are implemented: six grouped Ridge, six fixed SVR, six fixed random forest, and one combined absolute-spectral/G8f Ridge. All 39 tests pass (seven new); real sensitivity execution waits for the primary run to complete.

## Active subphase

Phase 6: interrupted primary recovery; separate descriptive sensitivities implemented. The expanded suite passes 47 tests in 29.848 seconds (eight new continuation tests). The unchanged 42-artifact snapshot passes self-check; digest `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898`. Continuation ID: `primary_20261021_continued`.

The freeze mechanism requires only Agrim's latest owner review. `reviews/registry_review.json` now approves the current digest, following Agrim's 2026-10-20 instruction granting all outstanding approvals and authority to continue. Earlier supplied reviews are historical evidence only.

The approved snapshot was committed at `42ff54d`; both annotated freeze tags exist and all 42 inputs still verify. On resuming 2026-10-21, the old process/session is gone: `primary_20261020` has validated T1-T5, but no T6-T9 or final family table. Its running status is stale. A new `src/continue_registry_v2.py` adapter reuses complete saved tests byte-for-byte and calls the frozen runner for missing computations/family finalization. Use a new run directory, preserve the interrupted one, and record the interruption reason; do not restart the full analysis or alter scientific settings. Agrim's approvals persist.

## Required behavior

- Never modify legacy v1 artifacts for v2 or put IDs, NIHSS, severity, metadata or epoch counts in X.
- All preprocessing/tuning stays within training folds. Feature engineering remains label-blind.
- Preserve and report every registered test/failure; do not tune after observing labels.
- Update `PROGRESS.md`, rewrite the technical ledger and append the timeline after changes.
- Stop and record uncertainty rather than guessing.

## Next three milestones

1. Complete and verify the interrupted primary family using the tested continuation adapter; T1-T5 already have verified results.
2. Execute and report the already implemented descriptive sensitivities in separate outputs; preserve the frozen primary artifacts and all primary decisions.
3. Resolve UCLH reference/duration/common-montage prerequisites before external validation.

UCLH source/DOI audit is now pinned to upstream commit `52ad25a8cb8ecae867cd8fb9984b4fbe703585c4`. The source has no O1/O2, and its EEG extractor high-passes at 2 Hz (not equivalent to the frozen 1-4 Hz delta input). The public participant TSV does not contain NIHSS. No UCLH raw files/common-montage implementation were found locally; external NIHSS validation remains blocked on target availability and raw preprocessing/montage compatibility. See the two existing UCLH docs for hashes and corrected source references.
