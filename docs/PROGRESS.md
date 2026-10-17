# Project Progress

The active plan and phase definitions are in [EXECUTION_GUIDE_CURRENT.md](../EXECUTION_GUIDE_CURRENT.md). Historical detail remains in the technical and timeline ledgers.

## Status as of 2026-10-17

| Phase | Subphase | Status | Outputs / evidence | Next action |
|---|---|---|---|---|
| Legacy | Figshare preprocessing and spectral feature extraction | DONE | `features/figshare_features.csv`, `features/figshare_patient_features.csv` | Preserve as v1 reference |
| Legacy | Spectral modeling benchmark | DONE | `src/train_models.py`; weak, unstable near-baseline result recorded in ledgers | Do not tune repeatedly |
| Legacy | v1 graph feature extraction | DONE | `src/graph_features.py`, `features/figshare_graph_features.csv`, `features/figshare_combined_features.csv` | Treat as biased baseline |
| Legacy | v1 graph audit | DONE | Epoch-count dependence identified, especially for `MeanHomotopic` | Correct with fixed-epoch v2 design |
| V2 | Phase 0: handoff reconciliation | DONE | `EXECUTION_GUIDE_CURRENT.md`; operational docs corrected | Follow current guide |
| V2 | Phase 1 / A0: metadata audit | DONE | `docs/METADATA_AUDIT.md` and `features/v2/subject_meta.csv`; 22 left and 28 right mapped lesion cases | A2/T3 is feasible |
| V2 | Phase 2 / A1: absolute spectral table | DONE | `features/v2/spectral_abs.csv` and `.meta.json`; shape 50×20, finite and label-free | Preserve output; continue to A3 when inputs exist |
| V2 | Phase 2 / A2: lesion-aligned spectral table | DONE | `features/v2/spectral_lesion.csv` and `.meta.json`; 50×20; 3 acceptance tests pass | Preserve output; lesion mapping is provenance-bound |
| V2 | Phase 3 / A3: channel and epoch design lock | DONE | `docs/GRAPH_DESIGN_LOCK.md`, audit JSON, and both configs; G8f N=15, G24f N=6 | Implement v2 graph library |
| V2 | Phase 4 / A4: graph v2 library and tests | DONE | `src/graph_features_v2.py`; 5 synthetic tests pass | Preserve implementation; no v1 edits |
| V2 | Phase 5 / A5-A6: generation and QC | DONE WITH FLAGS | `graph_g8f.csv`, `graph_g24f.csv`, sidecars, and `docs/FEATURE_QC_V2.md`; both tables 48×17 and label-free | Report residual bias/instability; do not tune against labels |
| V2 | Phase 6 / A7: freeze and registry handoff | BLOCKED | Depends on v2 outputs, reviews, and Group B registry | Freeze only after prerequisites |
| V2 | Phase 7: UCLH transfer and reporting | NOT STARTED | UCLH validation not complete | Defer until Figshare v2 is frozen |

## Open issues

- `participants.tsv` is missing from the current repository; lesion alignment is blocked until metadata semantics are verified.
- `docs/PHASE5_CONTEXT.md` is missing; `EXECUTION_GUIDE_CURRENT.md` is the replacement authority.
- The original `PROJECT_EXECUTION_GUIDE.md` is retained as historical reference and is not the current v2 execution plan.
- No v2 result may be described as an improvement before the fixed-epoch comparison is run under the frozen evaluation protocol.
# Project Progress Reference

> [!NOTE]
> **Notice on Progress Tracking:** Progress logging has been consolidated into the authoritative project ledgers.
> - **Operational Handoff & Immediate Context:** See [`docs/PHASE5_CONTEXT.md`](file:///d:/brain-stroke/docs/PHASE5_CONTEXT.md)
> - **Complete Technical State & Architecture:** See [`docs/Ledgers/project_technical_ledger_clean.md`](file:///d:/brain-stroke/docs/Ledgers/project_technical_ledger_clean.md)
> - **Chronological Milestones & Execution History:** See [`docs/Ledgers/project_timeline_ledger_clean.md`](file:///d:/brain-stroke/docs/Ledgers/project_timeline_ledger_clean.md)

---

## Current Status Summary
- **Current Milestone:** Phase 3b (Graph / Connectivity Branch) & Phase 5 Feature Ablation.
- **Latest Completed Step:** `src/graph_features.py` implemented (wPLI/multitaper graph features).
- **Next Pending Action:** Execute `src/graph_features.py` and run 3-way feature family ablation study.