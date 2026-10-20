# Project Progress

The authoritative plan is [EXECUTION_GUIDE_CURRENT.md](../EXECUTION_GUIDE_CURRENT.md). [CONTEXT.md](CONTEXT.md) is the concise AI handoff. The ledgers preserve current technical detail and history.

## Status as of 2026-10-20

| Phase | Status | Evidence | Next action |
|---|---|---|---|
| Legacy baseline | DONE; frozen | Legacy spectral/graph tables and benchmark | Preserve only |
| A0-A2 metadata/spectral v2 | DONE | `METADATA_AUDIT.md`; 50-subject absolute/lesion tables; T3 feasible under documented contralateral assumption | Preserve provenance limitation |
| A3-A6 graph v2 | DONE WITH FLAGS | G8f N=15, G24f N=6; graph tables 48 x 17; screen fix, QC, sidecars and manifest | Report residual bias/instability |
| B1 registry | OWNER APPROVED; FREEZE IN PROGRESS | Current 42-artifact digest approved on 2026-10-20 | Commit/tag and verify frozen content |
| B2-B3 engine/statistics | IMPLEMENTED; SYNTHETIC ACCEPTANCE PASSED | Gate A p=.005; Gate B 168/200 (84%); current 32/32 tests pass; validation JSON | Preserve implementation |
| Phase 6 freeze/evaluation | AUTHORIZED; IN PROGRESS | Owner approval covers the current snapshot and continuation through the primary run | Verify tags/guard and execute T1-T9 once |
| UCLH transfer | PARTIAL HANDOFF; VALIDATION NOT STARTED | UCLH audit/montage documents | Verify acquisition/reference/duration/common montage after Figshare freeze |

## Fixed decisions and limitations

- Current cohort: 33 mild, 17 moderate, no severe subjects. Do not build a three-class model.
- Retain subjects 04/05, 11/15 and 47/49 as distinct IDs. Their identical/highly similar signals remain a dependence and CV/permutation limitation. The full audit is in `RECORDING_INTEGRITY_AUDIT_V2.md`/`.json`.
- Both graph exclusions, sub-13 and sub-40, are moderate; graph subsets contain 33 mild and 15 moderate.
- G8f is primary. G24f is registered secondary T6 inside the nine-test Holm family.
- Original moderate positive controls failed and remain recorded. The user-authorized Option 3 replacement passed; `REGISTRY_VALIDATION_RESULTS.json` has `acceptance_passed: true`.
- Group A completed its work and will not return. Agrim is the sole project owner and the only required reviewer. AI-model, model-family and multi-group review dependencies have been removed.
- One active record, `reviews/registry_review.json`, binds the latest owner decision to the final digest. Earlier supplied reviews are historical evidence only and never block ordinary development.
- Agrim's 2026-10-20 instruction grants the outstanding approvals and authority to continue. Owner approval, scoped freeze commit/tags and the registered primary run are authorized. Scientific settings and all nine tests remain fixed.

## Documentation structure after cleanup

- `ANALYSIS_REGISTRY.md`: scientific protocol, amendments, freeze criteria and grouped-split sensitivity.
- `PROGRESS.md`: only current status, blockers and next actions.
- `CONTEXT.md`: concise handoff for a new AI session.
- `FEATURE_QC_V2.md`, `METADATA_AUDIT.md`, `GRAPH_DESIGN_LOCK.md`, and recording-integrity audit: distinct scientific evidence.
- `V2_FEATURE_HANDOFF.md` and `FEATURE_CHANGELOG.md`: completed Group A handoff/provenance.
- `UCLH_AUDIT.md` and `UCLH_MONTAGE.md`: future external-validation evidence.
- `reviews/`: one active machine-readable owner-review record plus historical supplied review evidence.
- `Ledgers/`: current technical state and append-only history.
- JSON manifests/results/audits remain because code or reproducibility checks consume their structured fields.

Redundant `B2_B3_IMPLEMENTATION.md`, `FREEZE_READINESS_REVIEW.md`, and `FREEZE_AND_SENSITIVITY_PLAN.md` were removed after their unique current content was consolidated into the registry, this status board and the ledgers.

## Freeze checklist

1. DONE: owner approved digest `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898` on 2026-10-20; snapshot self-check passes.
2. Commit the reviewed project changes and create the authorized `registry-v1` and `features-v2` tags.
3. Verify the tagged freeze with `verify_freeze()`.
4. Execute the authorized one-shot T1-T9 primary evaluation and independently check its saved results.

## Next major work

1. Complete the refreshed freeze described above.
2. Run and report the one-shot registered T1-T9 evaluation without tuning or selective omission.
3. Implement the separately registered grouped-split and other descriptive sensitivities, then complete UCLH prerequisite verification before external validation.

## Latest verification

After simplifying review to one owner record, all 32 unit/integration tests passed in 22.515 seconds. On 2026-10-20 the same 42-artifact snapshot passed self-check and Agrim's approval was recorded. The first primary run is authorized; its execution and outcomes will be recorded below.
