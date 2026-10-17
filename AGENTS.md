# Agent Rules

## Authority and starting point

- Read `EXECUTION_GUIDE_CURRENT.md` first. It is the authoritative operational guide.
- Use `docs/PROGRESS.md` for the active status and next subphase.
- Use `docs/Ledgers/` for historical and technical context.
- `PROJECT_EXECUTION_GUIDE.md` is the original reference plan and is stale for current v2 work.
- `docs/PHASE5_CONTEXT.md` is missing; do not recreate or rely on it.

## Project contract

- The current Figshare task is binary: `0=mild` and `1=moderate`. There are 0 severe subjects.
- Legacy v1 feature files and results are frozen reference artifacts. Do not overwrite them for v2.
- v2 feature CSVs contain only `subject_id` and feature columns. Labels and metadata belong in `features/v2/subject_meta.csv`.
- Feature-building code must not read `nihss_raw` or `severity_class`. Only the explicitly approved lesion-alignment step may read verified `lesion_side`.
- Never put NIHSS, severity, subject IDs, or epoch-count columns into a model matrix.

## Leakage and evaluation

- All scaling and feature selection must be inside sklearn pipelines.
- Legacy model evaluation uses `RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)` and reports macro-F1, balanced accuracy, and binary ROC-AUC with a majority-class dummy baseline.
- Do not perform repeated label-driven tuning on the small cohort.
- Real-label v2 evaluation is allowed only through the frozen registry described in `EXECUTION_GUIDE_CURRENT.md`.

## v2 workflow rules

- v2 is new-files-only: use `src/*_v2.py`, `features/v2/`, `configs/`, `tests/`, `results/v2/`, and new docs.
- Every v2 constant belongs in a JSON config; record hashes, seeds, channels, bands, and output schemas.
- Use fixed-size epoch sampling without replacement and deterministic seeds.
- Keep engineering label-blind. Report technical failures rather than tuning them away.
- Do not claim v2 is complete until tests, QC, metadata provenance, review, manifest, and freeze tag are complete.

## Change and logging rules

- Before editing, identify the active subphase and its acceptance check.
- After each subphase, update `docs/PROGRESS.md` and relevant ledgers.
- If a required input is missing or semantics are uncertain, mark the subphase `BLOCKED` and record the exact reason.
- Do not commit or create branches unless explicitly requested.
# Agent Rules (All AI Tools Read This First)

- **Project Context:** EEG asymmetry -> stroke severity. Read `docs/PHASE5_CONTEXT.md` and `PROJECT_EXECUTION_GUIDE.md` before performing any task.
- **Task Goal:** Binary classification (`0=mild`, `1=moderate`). The severe class has 0 samples on Figshare.
- **Feature Matrix ($X$):** Use exactly the 19 engineered features. NEVER include NIHSS scores, severity labels, subject IDs, or epoch count columns in $X$.
- **Pipeline Integrity:** All scaling (`StandardScaler`) and feature selection (`SelectKBest`) MUST live inside a `sklearn.pipeline.Pipeline` to guarantee zero data leakage across CV folds.
- **Cross-Validation:** Use `RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)`.
- **Metrics:** `f1_macro`, `balanced_accuracy`, `roc_auc` (binary mode). Always benchmark against `DummyClassifier(strategy='most_frequent')`.
- **Model Constraints:** Classical ML only (SVM, RF, KNN). No deep learning. No heavy hyperparameter tuning. Skip SHAP for distance-based models (use RF/permutation importances only).
- **Scope Limit:** Do NOT modify Phase 0–4 files in `src/` or `features/` unless explicitly instructed.
- **Logging Rule:** Maintain running technical and timeline logs in `docs/Ledgers/` and update operational handoff context in `docs/PHASE5_CONTEXT.md`.