# Immediate Operational Context

**Updated:** 2026-10-21. Read `EXECUTION_GUIDE_CURRENT.md` first, `PROGRESS.md` for status/results, `ANALYSIS_REGISTRY.md` for the frozen protocol and `Ledgers/` for technical/history detail.

## Completed state

- Agrim is the sole owner/reviewer. Group A finished and will not return. All approvals and authority granted on 2026-10-20 persist; no AI-model or other-group review dependency remains.
- Figshare: 50 IDs, 33 mild/17 moderate, no severe. T3 uses verified paralysis semantics with the prescribed contralateral lesion mapping (22 left/28 right), not imaging confirmation.
- Group A corrected artifact screening before sampling and regenerated/provenanced graph features. G8f is primary with 15 fixed epochs; G24f is secondary T6 with six fixed epochs and 22 channels. Both have 48 subjects after excluding sub-13/sub-40, both moderate.
- Retain 04/05, 11/15 and 47/49 as separate IDs. Similar/identical signals remain an unresolved dependence/CV/permutation limitation. Residual graph epoch bias/seed instability also remains.
- B1/B2/B3 are complete. Original moderate synthetic controls failed; the authorized Option 3 replacement passed (Gate A p=.005; Gate B 168/200=.84). Frozen validation evidence preserves the history.
- All **47 tests pass** (29.848 seconds), including seven descriptive-sensitivity and eight continuation tests. The frozen validation JSON keeps its freeze-time 32-test evidence; do not edit it to update the current count.

## Frozen artifacts and execution recovery

Approved digest: `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898` (42 artifacts). Both annotated tags `registry-v1` and `features-v2` point to freeze commit `42ff54d`. Single owner record: `docs/reviews/registry_review.json`. Separate sensitivity implementation: `f6fd0c3`; tested continuation adapter: `9c4d11b`.

The first run `primary_20261020` stopped after saving T1-T5. Its `run.json` has stale running status; preserve it as historical evidence. `src/continue_registry_v2.py` validated/reused all five saved test directories byte-for-byte and called the unchanged frozen runner for T6-T9 and full-family finalization. New run `primary_20261021_continued` is COMPLETE. Its `continuation.json` records source hashes and confirms every original file is unchanged. GPG keybox signing failed for the recovery commit; a command-local unsigned exception was used without changing Git settings or freeze tags.

## Results: completed and independently verified

- Primary: `results/v2/runs/primary_20261021_continued/registry_results.csv`. All nine decisions are `no_effect_detected`; every Holm p=1.000. T1-T6 predictive rhos: -.1414, -.2220, -.0322, -.2481, .1058, -.0615. T7-T9 associations: .0101, .1657, .2128.
- Every primary Ridge RMSE exceeds its matched dummy. No predictive model qualifies for promotion; no model was exported. No effect detected does not prove that all effects are absent.
- Sensitivities: `results/v2/sensitivities/robustness_20261021/sensitivity_results.csv`. All 19 descriptive analyses completed. Grouped G8f rho=.0994 versus primary .1058; all six grouped runs preserve pair isolation in both CV levels and have ten distinct outer partitions.
- All sensitivity RMSE values also exceed their dummy. Some MAE/AUC improve descriptively (G8f SVR rho=.2085, AUC=.6190); combined spectral/G8f Ridge rho=-.1721. No sensitivity inference or promotion is allowed.
- Figure: `results/v2/figures/primary_20261021_overview.png`.
- Independent verification covered all primary statistics/null p-values/intervals/Holm decisions, all sensitivity rhos, source hashes, OOF folds, group/class counts and seeded inner/outer split reconstruction. Primary/sensitivity CSV hashes are recorded in the technical ledger.
- **No jobs remain active. Do not launch another primary or sensitivity run.** The files are saved locally under Git-ignored `results/`; preserve them.

## Next 2-3 major steps

1. Use existing results, figure and ledgers for the final methods/results/limitations write-up. Preserve all registered findings and avoid repeated tuning.
2. Resolve a compatible externally labelled NIHSS cohort. UCLH's public participant TSV has no NIHSS column; different stroke subtype/healthy-control targets cannot substitute for severity.
3. Once a compatible clinical target is established, audit raw EEG/reference/duration and define a separate common montage before external validation. Pinned UCLH source lacks O1/O2 and high-passes at 2 Hz, conflicting with the Figshare 1-4 Hz delta input. See the existing UCLH docs; no raw BDF/common-montage implementation is present locally.

## Working rules

Keep IDs/metadata/NIHSS/severity/epoch counts out of X; fit preprocessing/tuning only inside training folds. Preserve legacy and frozen artifacts. Update progress, rewrite the technical ledger and append the timeline after changes. The frozen registry retains historical freeze-time status wording; live operational status is in the guide/progress/context.
