# Project Progress

The authoritative plan is [EXECUTION_GUIDE_CURRENT.md](../EXECUTION_GUIDE_CURRENT.md). [CONTEXT.md](CONTEXT.md) is the concise AI handoff. The ledgers preserve current technical detail and history.

## Status as of 2026-10-21

| Phase | Status | Evidence | Next action |
|---|---|---|---|
| Legacy baseline | DONE; frozen | Legacy spectral/graph tables and benchmark | Preserve only |
| A0-A2 metadata/spectral v2 | DONE | `METADATA_AUDIT.md`; 50-subject absolute/lesion tables; T3 feasible under documented contralateral assumption | Preserve provenance limitation |
| A3-A6 graph v2 | DONE WITH FLAGS | G8f N=15, G24f N=6; graph tables 48 x 17; screen fix, QC, sidecars and manifest | Report residual bias/instability |
| B1 registry | FROZEN | Commit `42ff54d`; annotated `registry-v1` and `features-v2`; 42 inputs verified | Preserve frozen scientific artifacts |
| B2-B3 engine/statistics | IMPLEMENTED; SYNTHETIC ACCEPTANCE PASSED | Gate A p=.005; Gate B 168/200 (84%); frozen 32-test evidence preserved; expanded suite 39/39 | Preserve implementation |
| Phase 6 freeze/evaluation | INTERRUPTED AFTER T5; CONTINUATION PREPARED | T1-T5 validated in `primary_20261020`; separate continuation adapter/tests | Reuse saved prefix and compute T6-T9 through the frozen runner |
| Registered descriptive robustness | IMPLEMENTED; 7 NEW TESTS PASS | Separate `run_sensitivities_v2.py`, config and tests; 19 analyses | Run after the primary family completes; no new inference or tuning |
| UCLH transfer | SOURCE AUDIT UPDATED; EXTERNAL VALIDATION BLOCKED | Pinned source, hashes and archive DOI/licences verified in existing audit/montage docs | Establish compatible clinical targets, raw EEG usability and common montage |

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
2. DONE: commit `42ff54d` and both annotated freeze tags created.
3. DONE: `verify_freeze()` passed against all 42 bound inputs on the execution machine.
4. IN PROGRESS: `primary_20261020` uses 1,000 permutations/test, five outer folds, ten repeats, nested Ridge and 2,000 bootstrap draws. Independently check the saved results after completion.

## Next major work

1. Complete the interrupted primary family in a new continuation directory and independently verify all nine tests.
2. Run and report the separately implemented grouped-split, SVR, RF and combined-feature descriptive sensitivities.
3. Complete UCLH prerequisite verification before any external validation.

## Latest verification

After simplifying review to one owner record, all 32 unit/integration tests passed in 22.515 seconds. On 2026-10-20 the same 42-artifact snapshot passed self-check and Agrim's approval was recorded. The first primary run is authorized; its execution and outcomes will be recorded below.

The expanded suite now passes 39 tests in 26.493 seconds, including seven synthetic sensitivity tests. These cover both CV levels' group isolation, exactly-once OOF coverage, deterministic splits, fold-local scaling/alpha selection, ID-based intersection, matching alternative-model folds, incomplete-primary refusal, no overwrites, no inference/model export, and preservation of primary artifacts. The same frozen snapshot still passes self-check; no primary methods or files were changed.

UCLH source audit on 2026-10-20 verified 32 EEG channels plus STATUS (33 electrode entries including NFpz), 16384 Hz metadata, common/CMS acquisition description, absent O1/O2, and trigger-delimited EEG extraction with a 2 Hz high-pass. Corrected the healthy-volunteer concept DOI versus patient/code archive identities. The published participant table has no NIHSS field; usable raw EEG duration, eye condition, effective reference and clinical-target compatibility remain unresolved. Existing UCLH docs were rewritten, removing unsupported specifications; no new planning documents or raw-data download.

- Registry invocation 2026-10-20T12:56:33.499416+00:00: START real run=primary_20261020; rerun_reason=None

On 2026-10-21, the old process/session is gone; T1-T5 have complete saved outputs and T6-T9 are absent. The old `run.json` still says running because finalization was interrupted. All five saved tests passed contract, target/class, OOF coverage/folds, dummy/metric, alpha, permutation and bootstrap checks. `continue_registry_v2.py` uses the frozen runner for the complete family, copies verified prefix files byte-for-byte into a new directory, and computes only missing tests. It preserves the original run and records interruption provenance. Windows initial legacy hashes are checked using the already-registered LF normalization. No inference or feature setting changed.

Recovery verification: 47/47 tests passed in 29.848 seconds, including eight continuation tests. The same 42-artifact snapshot passes self-check. Planned continuation ID: `primary_20261021_continued`, preserving `primary_20261020`.
