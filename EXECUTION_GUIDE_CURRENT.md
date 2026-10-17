# Current Execution Guide

**Project:** EEG-based stroke-severity analysis from interhemispheric EEG asymmetry
**Status date:** 2026-10-17
**Authority:** This is the current operational guide. It reconciles the original phase plan, the completed legacy work, and the proposed Group A v2 feature track.

## 1. How agents must use this guide

1. Read this file and `AGENTS.md` before acting.
2. Confirm the current phase and required outputs exist before starting the next subphase.
3. Do only the active subphase unless this guide explicitly permits a dependency task.
4. Do not infer completion from prose. Verify files, shapes, finite values, tests, and logs on disk.
5. After each completed subphase, update `docs/PROGRESS.md` with the status, date, outputs, validation, and open issues.
6. Do not overwrite legacy v1 files or results while building v2.
7. If a required input is missing or a rule is ambiguous, mark the subphase `BLOCKED` and record the exact blocker. Do not silently improvise.

The historical ledgers preserve what happened. This guide and `docs/PROGRESS.md` describe what agents should do next.

## 2. Research scope and fixed facts

### 2.1 Goal

Evaluate whether EEG spectral asymmetry and graph/connectivity features contain useful information about stroke severity. The available Figshare cohort supports only binary classification:

- `mild`: NIHSS 1-4, 33 subjects
- `moderate`: NIHSS 5-11, 17 subjects
- `severe`: 0 subjects

The project cannot support a three-class severity conclusion with this cohort.

### 2.2 Legacy v1 state: complete and frozen

The original pipeline produced patient-level Figshare features and a baseline model. These files are reference inputs and must not be rewritten:

- `features/figshare_features.csv`: 50 subjects, labeled spectral table
- `features/figshare_patient_features.csv`: patient-level spectral table before final labels
- `features/figshare_graph_features.csv`: 50 subjects plus 16 v1 graph features
- `features/figshare_combined_features.csv`: legacy spectral-plus-graph table
- `src/train_models.py`: legacy modeling harness
- `src/graph_features.py`: legacy wPLI graph extractor

The legacy spectral benchmark was weak and unstable, close to the dummy baseline. The legacy graph features also showed epoch-count dependence, especially in `MeanHomotopic`. These are reasons for the v2 audit; they are not evidence that v2 will improve performance.

### 2.3 v2 objective

Build and validate new feature tables without using their relationship to labels during feature engineering:

- sign-invariant spectral asymmetry;
- lesion-aligned spectral asymmetry, only if lesion semantics are verified;
- fixed-epoch graph features on the clean 8-channel core;
- fixed-epoch graph features on an audited symmetric expanded channel set;
- label-free quality, bias, stability, and collinearity checks;
- frozen tables and a manifest for Group B evaluation.

The v2 work is **pre-specified exploratory analysis**, not a claim of improved prediction.

## 3. Non-negotiable agent rules

### R1: Prevent label leakage

Feature-building code must not read `nihss_raw` or `severity_class`. The only permitted clinical metadata access in Group A is `lesion_side` in the lesion-alignment step, and only after its semantics are verified. Feature engineering must not select channels, epochs, constants, or methods because of label associations.

### R2: Keep labels out of v2 feature files

Every v2 feature CSV contains `subject_id` and feature columns only. Labels and metadata belong in `features/v2/subject_meta.csv`. Sidecars must list the exact columns.

### R3: Preserve v1

Do not edit Phase 0-4 source files, legacy feature CSVs, or legacy result artifacts for v2. New implementation files use new names such as `src/*_v2.py`.

### R4: Use fixed, auditable configurations

All constants affecting v2 output belong in JSON config files saved under `configs/`. Record the config hash, source commit, date, channel list, band definitions, `N_fixed`, subsample count, and seeds in sidecars.

### R5: No unregistered label evaluation

Before any real-label v2 evaluation, Group B must freeze `docs/ANALYSIS_REGISTRY.md` and tag the registry. Real-label evaluation runs only through the registry harness. Tests may use synthetic or shuffled labels.

### R6: Statistical discipline

Do not tune repeatedly against the same labels. Report all registered tests, including failures, with the planned multiple-testing correction. Use the language `no effect detected`, not `no effect`.

### R7: Keep graph methods reproducible

Use fixed-size epoch sampling without replacement, deterministic per-subject seeds, a documented node order, explicit left/right pair mapping, and deterministic feature names.

### R8: Review before freeze

v2 implementation requires a code review by a different model family and a human reviewer from the other group before tables are frozen.

### R9: Escalate blockers

Missing metadata, uncertain lesion semantics, insufficient epochs, channel-quality failures, or library-equivalence failures are blockers to the affected subphase. Record them in `docs/PROGRESS.md` and stop that path.

## 4. Data and feature contract

Use the fixed bands:

- delta: 1-4 Hz
- theta: 4-8 Hz
- alpha: 8-13 Hz
- beta: 13-30 Hz

Legacy spectral AI is:

`AI = (P_left - P_right) / (P_left + P_right)`

The clean core graph channels are ordered:

`F3, C3, P3, O1, F4, C4, P4, O2`

The legacy spectral feature set contains exactly 19 `all_*` features: 16 AI features plus `all_pdBSI`, `all_DAR`, and `all_DTABR`. Subject IDs, NIHSS, severity, and epoch counts never enter a model matrix.

The planned v2 graph feature set has four metrics per band:

- `GlobalEff_absAI`
- `ClustCoeff_absAI`
- `MeanHomotopic`
- `FrobeniusDist`

## 5. Phase and subphase plan

### Phase 0: Reconcile and freeze the baseline

**Status: DONE for legacy work; v2 handoff reconciliation active.**

- **0.1** Verify the four legacy feature CSVs exist and have 50 subjects.
- **0.2** Confirm the legacy spectral benchmark and known graph epoch-count bias from the ledgers.
- **0.3** Keep `PROJECT_EXECUTION_GUIDE.md` as historical reference only.

Gate: legacy inputs exist; v1 files are treated as immutable.

### Phase 1: A0 metadata audit

**Status: DONE.**

- **1.1** Search repository and available data for `participants.tsv` and related metadata.
- **1.2** Record exact columns and source semantics for paralysis/hemiplegia side, lesion side, stroke location, age, sex, handedness, and onset.
- **1.3** Never infer lesion side from an undefined column. If only paralysis side is documented, explicitly map it as contralateral; otherwise mark semantics `UNVERIFIED`.
- **1.4** Create `docs/METADATA_AUDIT.md` and `features/v2/subject_meta.csv` with provenance and unresolved values.
- **1.5** Decide whether lesion alignment is feasible: verified semantics plus at least 10 clear left and 10 clear right lesion subjects. If not, mark T3 dropped and continue without lesion alignment.

Gate: metadata provenance is documented; 22 left and 28 right lesion-side cases meet the A2 feasibility rule.

### Phase 2: A1 absolute spectral table

**Status: DONE.**

- **2.1** Create `features/v2/spectral_abs.csv` from the 16 existing `all_AI_*` columns using absolute values.
- **2.2** Preserve the three global spectral features.
- **2.3** Create a sidecar with columns, definitions, source, hash, and the pdBSI redundancy check.
- **2.4** Validate 50 rows, 20 columns including `subject_id`, finite values, and no label columns.

Gate: acceptance checks passed; v1 files unchanged. The sidecar records a maximum mean(|AI|)-pdBSI difference of approximately 0.1124, so pdBSI is not treated as identical to the mean of the 16 subject-level absolute AIs.

### Phase 3: A3 channel, epoch, and design audit

**Status: DONE with provisional technical lock.**

- **3.1** Inspect epoch headers and channel names without reading clinical labels.
- **3.2** Calculate clean epoch counts, sampling rate, actual epoch window, per-channel 150 uV rejection rates, and losses under the expanded screen.
- **3.3** Reproduce the legacy graph epoch-count correlation as a label-free technical audit.
- **3.4** Select `N_fixed` using the guide rule: use the minimum if at least 15; otherwise choose the largest feasible value that excludes at most two subjects.
- **3.5** Select symmetric expanded pairs only when channel rejection rates are at or below 25%; retain the 8-channel core for G8f.
- **3.6** Write `docs/GRAPH_DESIGN_LOCK.md`, `configs/graph_g8f.json`, and `configs/graph_g24f.json`.

Gate: passed. G8f is primary with N_fixed=15; G24f is secondary with N_fixed=6 after the label-blind channel screen. Reopen the lock if implementation reveals a reproducibility or library-equivalence failure.

### Phase 4: A4 v2 graph library and tests

**Status: DONE for synthetic/unit validation.**

- **4.1** Create `src/graph_features_v2.py`; do not modify `src/graph_features.py`.
- **4.2** Cache per-epoch cross-spectra, calculate vectorized wPLI on sampled epochs, and aggregate median adjacency across subsamples.
- **4.3** Implement weighted global efficiency, Onnela clustering, homotopic connectivity, and aligned Frobenius distance.
- **4.4** Implement deterministic seed handling and explicit pair mapping.
- **4.5** Create `tests/test_graph_features_v2.py` using synthetic data only.
- **4.6** Verify symmetry, left/right invariance, reproducibility, `N_fixed` dependence, graph metric values, and wPLI equivalence or document a measured tolerance.

Gate: passed. Five synthetic graph tests pass; no label or clinical metadata access is used by the graph library.

### Phase 5: A5 generation and A6 quality control

**Status: DONE with reported QC flags.**

- **5.1** Generate `features/v2/graph_g8f.csv` and `graph_g24f.csv` with sidecars.
- **5.2** Add `n_epochs_g8f` and `n_epochs_g24f` to `subject_meta.csv`.
- **5.3** Log exclusions, runtime, and exact configs.
- **5.4** Write `docs/FEATURE_QC_V2.md` covering finite values, constants, ranges, epoch bias, second-seed stability, collinearity, and absence of labels.

Gate: passed. Both tables are finite and label-free; residual epoch-bias correlations and seed-instability failures are documented in `docs/FEATURE_QC_V2.md` and must not be tuned against labels.

### Phase 6: Registry, freeze, and handoff

**Status: BLOCKED until Phases 1-5 and Group B registry work are ready.**

- **6.1** Group B freezes `docs/ANALYSIS_REGISTRY.md` before real-label evaluation.
- **6.2** Write `features/v2/MANIFEST.json` and `docs/FEATURE_CHANGELOG.md`.
- **6.3** Complete independent model-family and human review.
- **6.4** Tag frozen tables `features-v2`; record hashes and handoff message.
- **6.5** Run the registry once, report all registered tests, and keep sensitivity analyses outside the registered claims.

Gate: frozen, hashed, reviewed outputs and a reproducible registry run.

### Phase 7: UCLH transfer and reporting

**Status: NOT STARTED.**

- **7.1** Verify UCLH acquisition, preprocessing, clinical labels, and montage.
- **7.2** Build only a documented common-montage feature set.
- **7.3** Perform external validation only after Figshare v2 is frozen.
- **7.4** Report limitations: small sample, no severe class, task/rest mismatch, reference differences, missing or uncertain metadata, and any remaining epoch bias.

## 6. Required v2 outputs

Expected outputs, in order:

- `docs/METADATA_AUDIT.md`
- `features/v2/subject_meta.csv`
- `features/v2/spectral_abs.csv` and sidecar
- `docs/GRAPH_DESIGN_LOCK.md`
- `configs/graph_g8f.json`, `configs/graph_g24f.json`
- `src/graph_features_v2.py`
- `tests/test_graph_features_v2.py`
- `features/v2/graph_g8f.csv`, `features/v2/graph_g24f.csv` and sidecars
- `docs/FEATURE_QC_V2.md`
- `features/v2/MANIFEST.json`
- `docs/FEATURE_CHANGELOG.md`
- `docs/ANALYSIS_REGISTRY.md` and registry results owned by Group B

## 7. Current blockers and decisions

- `participants.tsv` and verified lesion-side semantics are not currently present in the repository. A0 must search for them before A2.
- `docs/PHASE5_CONTEXT.md` is referenced by older files but is missing. This guide replaces it as the operational authority.
- The v2 guide supplied by the team is a proposal, not completed implementation. No v2 output may be described as finished.
- The legacy graph CSVs exist, but their epoch-count bias means they are a baseline, not the corrected graph solution.
- No severe-class model should be built from the current Figshare cohort.

## 8. Definition of done

The v2 track is complete only when the required outputs exist, acceptance checks and tests pass, all exclusions and unresolved metadata are documented, labels are absent from feature CSVs, configs and hashes are recorded, reviews are complete, `features-v2` is tagged, and `docs/PROGRESS.md` records the final handoff.
