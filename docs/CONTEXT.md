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

Phase 6: documentation consolidation and review-mechanism simplification are complete. All 32 tests passed in 22.515 seconds. The regenerated 42-artifact snapshot passed its self-check; digest `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898`.

The freeze mechanism requires only Agrim's latest owner review. `reviews/registry_review.json` now approves the current digest, following Agrim's 2026-10-20 instruction granting all outstanding approvals and authority to continue. Earlier supplied reviews are historical evidence only.

The approved snapshot was committed at `42ff54d`, both annotated freeze tags were created, and `verify_freeze()` passed for all 42 inputs. The first run `primary_20261020` is in progress under the full registered settings. Do not restart it or change frozen artifacts. Agrim authorized continued work; do not ask again for approvals already provided.

## Required behavior

- Never modify legacy v1 artifacts for v2 or put IDs, NIHSS, severity, metadata or epoch counts in X.
- All preprocessing/tuning stays within training folds. Feature engineering remains label-blind.
- Preserve and report every registered test/failure; do not tune after observing labels.
- Update `PROGRESS.md`, rewrite the technical ledger and append the timeline after changes.
- Stop and record uncertainty rather than guessing.

## Next three milestones

1. Complete and verify the current one-shot T1-T9 run.
2. Execute and report the already implemented descriptive sensitivities in separate outputs; preserve the frozen primary artifacts and all primary decisions.
3. Resolve UCLH reference/duration/common-montage prerequisites before external validation.
