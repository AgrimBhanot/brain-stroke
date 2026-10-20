# Independent Review — Figshare v2 EEG Stroke-Severity Registry

**Reviewer:** Independent (automated, model-based)
**Date:** 2026-10-19
**Scope:** Full registry, feature handoff, statistical design, implementation, and freeze-readiness

---

## A. VERDICT

**Block** — with a focused remediation path (medium confidence)

1. The positive-control gate is legitimately failed (planted ρ=.65 → OOF ρ≈.33, p=.012 vs required <.01). This is a real design-sensitivity problem, not a code bug, and the current single-dataset gate cannot be expected to pass without either inflating the planted signal or reducing the threshold — both post-failure amendments.
2. The remedy is tractable: replace the single-dataset positive control with a pre-specified multi-simulation detection-rate gate and a separate correctness-only strong-signal check. This is Option (3) from Section C below. It can be done in ≤1 day and requires a documented amendment, config update, manifest regeneration, and re-review.
3. Everything else — nested scaling, permutation logic, Holm, freeze guards, feature engineering — is sound. Twenty unit tests pass. No code bugs found that would change a result.
4. The dependent-recordings limitation (pairs 4/5, 11/15, 47/49) is a genuine exchangeability threat to the permutation null but is a pre-existing cohort property that cannot be fixed without data. The disclosure is adequate; a grouped-split sensitivity is warranted.
5. The feature freeze is **Approve after fixes** (one item: missing class-balance count for excluded subjects).

---

## B. PREFLIGHT

All eight required files were located and read:

| File | Status |
|------|--------|
| [ANALYSIS_REGISTRY.md](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md) | ✅ Present, 132 lines |
| [registry_v1.json](file:///d:/brain-stroke/configs/registry_v1.json) | ✅ Present, 689 lines |
| [REGISTRY_VALIDATION_RESULTS.json](file:///d:/brain-stroke/docs/REGISTRY_VALIDATION_RESULTS.json) | ✅ Present, 71 lines |
| [stats_utils.py](file:///d:/brain-stroke/src/stats_utils.py) | ✅ Present, 88 lines |
| [train_regression.py](file:///d:/brain-stroke/src/train_regression.py) | ✅ Present, 177 lines |
| [run_registry.py](file:///d:/brain-stroke/src/run_registry.py) | ✅ Present, 219 lines |
| [validate_registry_v2.py](file:///d:/brain-stroke/src/validate_registry_v2.py) | ✅ Present, 75 lines |
| [test_registry_v2.py](file:///d:/brain-stroke/tests/test_registry_v2.py) | ✅ Present, 197 lines |

Optional context files [UCLH_AUDIT.md](file:///d:/brain-stroke/docs/UCLH_AUDIT.md) and [UCLH_MONTAGE.md](file:///d:/brain-stroke/docs/UCLH_MONTAGE.md) were also read.

**Unit tests:** All 20 tests pass (11 registry, 6 graph, 3 lesion) in 6.5 s.

Preflight: **PASS — review can proceed.**

---

## C. POSITIVE-CONTROL DECISION

### The observed problem

The planted signal has population Pearson r=.65 with one informative feature and 18 noise features. After nested 5×10 CV with Ridge over 20 alphas, the pooled OOF mean Spearman ρ attenuates to ≈.334 ([REGISTRY_VALIDATION_RESULTS.json:32](file:///d:/brain-stroke/docs/REGISTRY_VALIDATION_RESULTS.json#L32)). With 1000 permutations the corrected p=.01199 — just above the required p<.01 threshold.

The attenuation from .65 population to .33 OOF is expected: N=50, 19 features, 5-fold inner/outer nesting, Ridge regularization. This is not a code defect. The SVD path matches sklearn's GridSearchCV exactly ([test_registry_v2.py:72-78](file:///d:/brain-stroke/tests/test_registry_v2.py#L72-L78)). The strong diagnostic (population .95 → OOF .83, p=.005) confirms the pipeline detects strong signal. The null calibration (3% FPR at α=.05, 100 datasets) confirms calibration.

**Diagnosis:** The single-dataset p<.01 gate was set too strictly relative to the expected power of the pipeline at the chosen planted effect size. This is a design-sensitivity mismatch, not a bug.

### Options evaluated

#### Option 1: Keep the single-dataset rule, look for a code defect

I found no code defect. The SVD path is algebraically verified. The attenuation is explained by the estimation context. **Reject**: the gate will not pass without changing either the planted effect or the threshold, both of which are post-failure tuning.

#### Option 2: Detection rate over many pre-generated simulated datasets

Run S simulated datasets (each with the same planted .65 correlation), record the fraction that achieve p<.05 with 200 permutations. Require detection rate ≥70%. This measures pipeline power directly.

- **Pro:** Directly answers "can this pipeline detect a moderate effect?"; avoids single-dataset Monte Carlo noise.
- **Con:** Computationally expensive. At S=100 with B=200 permutations and 2 outer repeats, ≈20,000 Ridge evaluations. Took ≈45 min for the existing null calibration at similar scale. Runtime is acceptable.
- **Threshold justification:** 70% detection rate is a conventional power benchmark (Cohen, 1988). The planted .65 is above the approximate uncorrected detectable ρ≈.39 at N=50 (Fisher z, verified in [test_registry_v2.py:59](file:///d:/brain-stroke/tests/test_registry_v2.py#L59)), so 70% is a reasonable expectation if the pipeline is working.

#### Option 3 (RECOMMENDED): Correctness gate + descriptive power curve

Split the positive control into two separable requirements:

**Gate A — Strong-signal correctness check:** Plant population ρ=.95, require p<.01 with 199 permutations and 2 repeats. This already passes (OOF ρ=.83, p=.005; [REGISTRY_VALIDATION_RESULTS.json:58-67](file:///d:/brain-stroke/docs/REGISTRY_VALIDATION_RESULTS.json#L58-L67)). Purpose: verify that the pipeline can detect unambiguous signal. One dataset suffices because the effect is massive.

**Gate B — Multi-dataset detection rate at moderate signal:** Run S=200 simulated datasets at population ρ=.65, each with B=200 permutations and 2 outer repeats. Record the fraction with raw p<.05. Require detection rate ∈ [50%, 95%]. Purpose: confirm that the pipeline has non-trivial power at the expected moderate effect, without requiring near-certainty from a single draw.

- The [50%, 95%] range is justified because: (a) Fisher-z power at ρ=.65, N=50, α=.05 is roughly 99% for a simple Spearman test, but nested CV with 19 features and regularization can easily halve effective power; 50% is a generous lower bound. (b) >95% would mean the pipeline has more power than a simple correlation test, which is implausible.
- This is **not** a single-p-value threshold chosen to make the current data pass. It is a power diagnostic.
- Runtime: 200 × (200 perm × 2 rep × 5 outer × 5 inner) ≈ 2M Ridge fits. At ~1ms each, ~30–40 min with 4 workers. Acceptable.

**Why Option 3 over Option 2:** Option 3 separates *correctness* (Gate A: does the code work?) from *power* (Gate B: is the pipeline sensitive enough?). Option 2 conflates them. The current strong diagnostic already provides Gate A evidence; Gate B adds the power dimension that the single-dataset gate was trying to measure.

#### Option 4: Bayesian or analytic power calculation

Not recommended. The pipeline has nested CV, Ridge regularization, and 18 noise features; no closed-form power formula applies. Monte Carlo is the correct tool.

### Proposed thresholds summary

| Gate | Planted ρ | Simulations | Permutations/Repeats | Accept criterion | Justification |
|------|-----------|-------------|---------------------|-----------------|---------------|
| A (correctness) | 0.95 | 1 | 199 / 2 | p < 0.01 | Effect is massive; single dataset has >99.9% theoretical power |
| B (power diagnostic) | 0.65 | 200 | 200 / 2 | Detection rate ∈ [50%, 95%] | Cohen's 80% power convention as midpoint; generous bounds for nested CV pipeline |

### Amendment protocol

This is a **post-failure amendment**. It must be:

1. Documented as an explicit amendment in [ANALYSIS_REGISTRY.md](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md) §12 with a dated rationale paragraph explaining that the single-dataset .65 gate was underpowered for the nested pipeline, not that the pipeline was defective.
2. Recorded in [PROGRESS.md](file:///d:/brain-stroke/docs/PROGRESS.md) and the timeline ledger with the amendment date.
3. Implemented in [validate_registry_v2.py](file:///d:/brain-stroke/src/validate_registry_v2.py) as a new mode `"power_diagnostic"` with config in [registry_v1.json](file:///d:/brain-stroke/configs/registry_v1.json) under `validation.power_diagnostic`.
4. After the new validation passes, [REGISTRY_VALIDATION_RESULTS.json](file:///d:/brain-stroke/docs/REGISTRY_VALIDATION_RESULTS.json) must be regenerated with `acceptance_passed: true` and the new gate results.
5. The freeze manifest hashes, artifact digest, and any approval records become stale and must be regenerated.
6. The freeze snapshot in [REGISTRY_FREEZE_MANIFEST.json](file:///d:/brain-stroke/docs/REGISTRY_FREEZE_MANIFEST.json) must be regenerated to cover the changed files.
7. Both `registry-v1` and `features-v2` tags must be recreated after the manifest is final.

### Assessment of the attenuation

The attenuation from planted .65 to OOF .33 is roughly 50%, which is concerning but explainable:
- 19 features with only 1 informative → Ridge must regularize heavily, diluting signal.
- 5-fold inner/outer nesting with N=50 means train sizes of ~32 (outer) × ~26 (inner). Very small.
- The .30 decision threshold for real data is therefore near the upper end of what this pipeline can deliver at moderate effect sizes. This is a design limitation but not a flaw: the threshold was pre-specified. The registry already acknowledges that the minimum detectable ρ at Holm's strictest threshold is ~.48 ([ANALYSIS_REGISTRY.md:119](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md#L119)).

**Conclusion:** The decision threshold ρ≥.30 is not unreachable but the pipeline has limited power. This must be reported. It does not warrant changing .30 — that would be post-hoc threshold shopping.

---

## D. IMPLEMENTATION AUDIT

### D1. Nested scaler/alpha selection isolation

**Severity: OK**

[train_regression.py:26-47](file:///d:/brain-stroke/src/train_regression.py#L26-L47): The `fit_ridge` function fits a `StandardScaler` Pipeline inside each inner fold (line 34), transforms inner-train and inner-valid independently, computes SVD on the scaled inner-train, evaluates all alphas in one pass, selects the best alpha (line 44), then refits a full `Pipeline([StandardScaler(), Ridge()])` on the entire outer-train (line 45-46).

The unit test at [test_registry_v2.py:72-78](file:///d:/brain-stroke/tests/test_registry_v2.py#L72-L78) confirms selected alpha and predictions match `GridSearchCV(Pipeline(...))` exactly. The scaler never touches validation or test data before transform. **Sound.**

### D2. SVD path vs sklearn Pipeline equivalence

**Severity: OK**

The SVD path computes `coefficients = V^T (S / (S^2 + α)) U^T (y - ȳ)` for all alphas simultaneously (lines 39-41). This is algebraically identical to Ridge's closed-form solution on centered/scaled data. The test confirms numerical agreement to atol=1e-10. The re-centering at line 38 (`xmean = a.mean(axis=0)`) is correct because `StandardScaler` sets `mean_=0` only if `with_mean=True` (the default), and numerical residuals after scaling can be non-zero.

**One subtle point:** The SVD path computes `ymean = y[train].mean()` and uses it as the intercept, which matches `Ridge(fit_intercept=True)` on centered data. The final sklearn Pipeline also uses `fit_intercept=True` (default). **Consistent.**

### D3. Joint permutation of NIHSS and severity with split regeneration

**Severity: OK**

[train_regression.py:111-113](file:///d:/brain-stroke/src/train_regression.py#L111-L113): `y[permutation]` and `strata[permutation]` are passed to `cross_validated_predictions`, which calls `RepeatedStratifiedKFold.split(X, strata)` — so permuted strata generate new splits. The test at [test_registry_v2.py:88-94](file:///d:/brain-stroke/tests/test_registry_v2.py#L88-L94) explicitly verifies that (a) the first null statistic matches refitting with the expected permutation, and (b) using unpermuted strata produces different folds. **Correct.**

### D4. One-sided T1-T6 vs two-sided T7-T9 tails

**Severity: OK**

[train_regression.py:116](file:///d:/brain-stroke/src/train_regression.py#L116): `alternative = "greater" if kind == "ridge" else "two-sided"`. [stats_utils.py:23-26](file:///d:/brain-stroke/src/stats_utils.py#L23-L26): `greater` counts `null >= observed`; `two-sided` counts `|null| >= |observed|`. Matches registry §7 ([ANALYSIS_REGISTRY.md:83](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md#L83)). **Correct.**

### D5. The (1+k)/(B+1) correction

**Severity: OK**

[stats_utils.py:29](file:///d:/brain-stroke/src/stats_utils.py#L29): `(1 + exceed.sum()) / (len(null) + 1)`. This is the Davison-Hinkley finite-sample correction (1997). With B=1000, floor is 1/1001 ≈ .001. Ties counted as exceedances (lines 24, 26: `>=`). **Correct.**

### D6. Pooled-then-averaged ρ and tie handling

**Severity: OK**

[stats_utils.py:32-40](file:///d:/brain-stroke/src/stats_utils.py#L32-L40): Custom Spearman uses `scipy.stats.rankdata` (average ties, matching scipy's default). Pearson on ranks is computed manually. Test at [test_registry_v2.py:40-44](file:///d:/brain-stroke/tests/test_registry_v2.py#L40-L44) verifies agreement with `scipy.stats.spearmanr`. [stats_utils.py:43-52](file:///d:/brain-stroke/src/stats_utils.py#L43-L52): pools N predictions per repeat, computes ρ per repeat, averages. **Matches registry §6.**

**One edge case:** If a repeat has constant predictions (zero variance after ranking), `denominator` in line 39 is 0 and the function returns NaN. Line 50-51 then raises `ValueError`. This correctly treats undefined correlations as failures. **Correct.**

### D7. Holm adjustment

**Severity: OK**

[stats_utils.py:8-16](file:///d:/brain-stroke/src/stats_utils.py#L8-L16): Sort ascending, multiply by `(m - rank + 1)` via `np.arange(len(p), 0, -1)`, cumulative max, cap at 1, restore order. This is the standard Holm step-down procedure. Test at [test_registry_v2.py:28-31](file:///d:/brain-stroke/tests/test_registry_v2.py#L28-L31) verifies a hand example. **Correct.**

### D8. Bootstrap policy

**Severity: OK**

[stats_utils.py:55-81](file:///d:/brain-stroke/src/stats_utils.py#L55-L81): Fixed 2000 resamples, no redraws. Invalid resamples counted (line 76). If >1% invalid, CI unavailable (line 77). Percentile limits at 2.5th and 97.5th. The `pooled_oof_spearman` call inside the bootstrap (line 72) resamples whole subject rows (all 10 repeats together), matching the registry §8 specification for conditional bootstrap. **Correct.**

### D9. Failure accounting and placeholder p=1

**Severity: OK**

[run_registry.py:178-183](file:///d:/brain-stroke/src/run_registry.py#L178-L183): Failed tests catch exceptions (line 178), store the error string (line 179), and contribute `p_raw=1` (via `.get("p_raw", 1)` at line 183) to Holm. Holm-adjusted p is set to `None` for failed tests (line 185). Decision is `withheld_incomplete_family` for all tests if any failed (line 188). Model export is blocked (line 190: `not failed`). Test at [test_registry_v2.py:115-141](file:///d:/brain-stroke/tests/test_registry_v2.py#L115-L141) verifies this. **Correct.**

> [!IMPORTANT]
> **One issue (Low):** The placeholder p=1 for failed tests inflates surviving tests' Holm denominators, making the family *more* conservative. Since the decision is already `withheld_incomplete_family` when any test fails, this is inconsequential for the decision but is a defensible design choice. No fix needed.

### D10. Freeze guards

**Severity: Med — items below need attention before freeze**

[run_registry.py:55-106](file:///d:/brain-stroke/src/run_registry.py#L55-L106):

- **Tag verification** (line 58-59): checks `registry-v1` and `features-v2` exist as annotated tags. ✅
- **Manifest identity** (line 61-62): checks REGISTRY_FREEZE_MANIFEST.json matches the `registry-v1` tag byte-for-byte. ✅
- **Artifact hashes** (line 69-74): checks SHA-256 of each artifact against manifest AND against the tag's version. ✅
- **Feature manifest** (line 75-77): checks MANIFEST.json matches `features-v2` tag. ✅
- **Validation acceptance** (line 80-82): checks `acceptance_passed is True`. Currently false → runner refuses. ✅ (this is the blocking positive-control issue)
- **Approval records** (line 98-104): checks status, reviewer, reviewed_at, artifact_digest against the computed digest. ✅
- **Path traversal guard** (line 36-38): `safe_path` prevents escaping the repo root. ✅

**Finding D10a (Med):** The `verify_freeze` function does not check that the *working tree* is clean (no uncommitted changes outside the covered artifacts). A modified but unlisted file (e.g. a newly added sensitivity script) would not be caught. The runner does record `source_commit` (line 166), which partly mitigates this, but a dirty working tree means the commit hash doesn't fully represent the execution environment.

**Fix:** Add a `git status --porcelain` check at the start of `verify_freeze` and refuse if there are unstaged changes to any file under `src/`, `configs/`, or `tests/`.

**Finding D10b (Low):** The approval records are checked against the `artifact_digest` of the freeze manifest, but the freeze manifest does not include the feature manifest's own hash or the approval record files themselves. This creates a narrow window where an attacker could modify the approval JSON after tagging, but before verification. Mitigation: the tag comparison at line 103 (`path.read_bytes() != git_bytes(...)`) catches this. **No fix needed.**

### D11. Items outside the freeze snapshot

**Severity: Med**

The [REGISTRY_FREEZE_MANIFEST.json](file:///d:/brain-stroke/docs/REGISTRY_FREEZE_MANIFEST.json) lists 12 artifacts. These do NOT include:

- `src/validate_registry_v2.py` — covered in manifest line 28-30 ✅
- `tests/test_registry_v2.py` — covered in manifest line 35-37 ✅
- `src/write_registry_freeze_v2.py` — covered ✅

However, the feature MANIFEST.json's `implementation_sources` includes files not in the registry freeze manifest: `src/audit_graph_design_v2.py`, `src/qc_graph_features_v2.py`, `src/build_spectral_abs_v2.py`, `src/build_spectral_lesion_v2.py`, `src/write_v2_provenance.py`, `src/write_v2_manifest.py`. These are feature-build scripts, appropriately covered by the `features-v2` tag rather than the `registry-v1` tag.

**Finding D11a (Low):** The registry freeze manifest does not cover `features/v2/MANIFEST.json` or `features/v2/subject_meta.csv`. However, `verify_freeze` checks the feature manifest separately via the `features-v2` tag (lines 75-96). **Adequate but fragile** — if the feature tag is recreated independently, registry results could silently change.

### D12. Windows path and cross-computer reproducibility

**Severity: Low**

- All paths use `pathlib.Path`, which handles Windows separators. ✅
- Config and manifest paths are stored as POSIX-style strings (`features/v2/...`), which Path handles on both platforms. ✅
- `git show ref:path` uses forward-slash paths, which Git accepts on Windows. ✅
- `subprocess.check_output(["git", ...])` requires Git to be on PATH. Normal for development environments.
- The `core.autocrlf` setting in the freeze guard test is explicitly set to `false` (test line 153). **However,** the production `verify_freeze` does not control autocrlf. If a file is checked in with LF but checked out with CRLF due to `.gitattributes` or config, the byte comparison `path.read_bytes() != git_bytes(root, tag, path)` will fail because `git show` returns the blob content (LF), while the working copy may have CRLF.

**Finding D12a (Med):** The byte-exact comparison between working copy and `git show` is CRLF-sensitive. A `.gitattributes` with `* text=auto` would cause false failures on Windows. Verify that `.gitattributes` either normalizes to LF or is absent. If present, use `git show` on the normalized content or compare hashes of blob objects instead of raw bytes.

### D13. sklearn/numpy version sensitivity

**Severity: Low**

The runner records `numpy`, `scipy`, and `sklearn` versions in `run.json` (line 164). The pipeline uses only `StandardScaler` + `Ridge(solver='svd')`, which are numerically stable across sklearn versions. `np.linalg.svd` uses LAPACK, which is deterministic given the same BLAS. `rankdata` from scipy is stable.

**Potential issue:** `RepeatedStratifiedKFold` with `random_state=42` uses numpy's legacy `RandomState` (via sklearn), while permutations use `default_rng` (PCG64). These are different RNG families but both are seeded deterministically. Cross-version reproducibility depends on sklearn not changing its split algorithm, which has been stable since sklearn 0.22. **Acceptable risk.**

---

## E. DEPENDENT RECORDINGS

### The facts

Per [FREEZE_READINESS_REVIEW.md:15](file:///d:/brain-stroke/docs/FREEZE_READINESS_REVIEW.md#L15):
- **sub-04/sub-05:** Identical signal values across all 160,000 samples in 8 core channels.
- **sub-11/sub-15:** Channel-wise correlations 0.99967–0.99993.
- **sub-47/sub-49:** Channel-wise correlations 0.99955–0.99993.

All six subjects are retained by team decision ([ANALYSIS_REGISTRY.md:24](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md#L24)).

### Effect on CV leakage

When sub-04 and sub-05 appear in the same 5-fold split (one in train, one in test), the test prediction for the duplicate is based on training data that contains its exact signal twin. This is a form of data leakage — the model has "seen" the test subject. With 5-fold CV, P(same pair split across train/test in one fold) = 4/5 per pair per fold. Over 10 repeats, this occurs frequently.

For sub-11/15 and sub-47/49, the near-identical signals create the same problem at slightly lower severity.

**Impact on nominal performance:** OOF ρ is inflated because 6 of 50 subjects' held-out predictions benefit from quasi-duplicates in training. The inflation is bounded: even if all 6 subjects' predictions are perfect, they represent 12% of the sample. The bias is modest but non-zero.

**Impact on permutation null validity:** Permutation tests assume exchangeability of subjects. When two subjects share identical signals but different NIHSS scores, permuting their labels breaks the signal-label structure differently than permuting independent subjects. The null distribution becomes anti-conservative if duplicates happen to have different NIHSS (the model predicts the same score for both, so permuting one but not the other creates a detectable pattern), or conservative if they have the same NIHSS. **Without knowing the real NIHSS values of sub-04/05, 11/15, and 47/49, the direction of bias cannot be determined, and must not be determined before the real run.**

### Adequacy of disclosure

[ANALYSIS_REGISTRY.md:24](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md#L24) states: *"different IDs do not establish statistical independence, and similar signals can appear in both training and test folds. Nominal CV estimates and permutation p-values rely on subject exchangeability and must be interpreted with this limitation."*

This is **adequate but should be more specific.** It should quantify the expected fold-overlap probability (4/5 per pair per fold) and state that the direction of bias depends on whether paired subjects have similar or different NIHSS, which will be known only after the real run.

### Recommendation: grouped-split sensitivity analysis

**Yes, a pre-specified grouped-split sensitivity analysis outside Holm is warranted.** Specifically:

1. After the registered run, rerun T1-T6 (not T7-T9, which don't use CV) with a modified split that groups {4,5}, {11,15}, {47,49} into the same fold in every split. This ensures no pair is ever split across train and test.
2. Compare the grouped-split ρ with the ungrouped ρ. If the difference is >0.05, the leakage bias is material.
3. Report this as a pre-specified descriptive sensitivity, clearly outside Holm. It cannot rescue or invalidate a registered result.

This should be documented as a sensitivity analysis in the registry amendment and run automatically after the primary real run.

### Data-integrity checks on paired subjects

The following checks should be run (label-free) before freeze:

1. **Verify the identity claim for sub-04/sub-05:** Confirm that the 8 core channels (F3, C3, P3, O1, F4, C4, P4, O2) are bitwise identical sample-by-sample. If they are, check whether ALL channels (not just core) are identical. If yes, they are the same recording file with different subject IDs.
2. **Check metadata consistency:** Do 04/05 have the same age, sex, handedness, stroke location, duration? If so, they are almost certainly the same person. If not, investigate.
3. **For 11/15 and 47/49:** Check if the near-identity extends to non-core channels, and whether their metadata matches.
4. **Check with the Figshare dataset authors** whether these are known duplicates. The Figshare record should have a version history.

> [!WARNING]
> These checks are data-integrity investigations, not model-result-driven decisions. They should be done before freeze but do not depend on NIHSS values.

---

## F. FEATURE-SIDE INDEPENDENT REVIEW

### F1. Label-blind engineering

**Verdict: Sound.**

- [build_spectral_lesion_v2.py](file:///d:/brain-stroke/src/build_spectral_lesion_v2.py): Reads `lesion_side` from metadata (line 44); does not import `nihss_raw` or `severity_class`. The test at [test_lesion_align.py:61-64](file:///d:/brain-stroke/tests/test_lesion_align.py#L61-L64) explicitly checks source text. ✅
- [graph_features_v2.py](file:///d:/brain-stroke/src/graph_features_v2.py): No imports of metadata or labels. Operates on MNE Epochs objects and config dicts. ✅
- [run_graph_features_v2.py](file:///d:/brain-stroke/src/run_graph_features_v2.py): Writes epoch counts to `subject_meta.csv` (lines 83-92) but never reads NIHSS or severity. ✅
- [train_regression.py:134](file:///d:/brain-stroke/src/train_regression.py#L134): `BANNED_PARTS` tuple blocks `nihss`, `severity`, `subject`, `epoch`, etc. from entering X. ✅

**Approved:** `lesion_side` is the only clinical column used in feature engineering, and it is explicitly permitted by the registry.

### F2. Fixed-epoch subsampling and post-correction screen

[graph_features_v2.py:153-157](file:///d:/brain-stroke/src/graph_features_v2.py#L153-L157): `screen_epochs` is called inside `compute_graph_features` on the passed epochs. [run_graph_features_v2.py:48-55](file:///d:/brain-stroke/src/run_graph_features_v2.py#L48-L55): The runner calls `passing_epochs` (which calls `screen_epochs`) and passes the screened result to `compute_graph_features`. The calculator then screens again — this is redundant but harmless (idempotent: already-screened data passes the same screen). The test at [test_graph_features_v2.py:91-102](file:///d:/brain-stroke/tests/test_graph_features_v2.py#L91-L102) confirms that screening is applied before sampling. The FEATURE_CHANGELOG explicitly documents the fix. **Correct after the documented bug fix.**

### F3. wPLI vectorization and reference equivalence

[graph_features_v2.py:91-117](file:///d:/brain-stroke/src/graph_features_v2.py#L91-L117):

The implementation computes `imag(S_ij)` across epochs, then `|Σ imag| / Σ|imag|`, averaged over frequencies. This is the standard debiased wPLI formula (Vinck et al. 2011) **without the debiasing term**. Standard wPLI = `|E[imag(S)]| / E[|imag(S)|]`; debiased wPLI additionally subtracts sample-size-dependent bias. The implementation uses the non-debiased version.

The test at [test_graph_features_v2.py:61-75](file:///d:/brain-stroke/tests/test_graph_features_v2.py#L61-L75) verifies against a direct formula calculation but not against an external library (e.g., `mne.connectivity`). [FREEZE_READINESS_REVIEW.md:23](file:///d:/brain-stroke/docs/FREEZE_READINESS_REVIEW.md#L23) explicitly notes this gap.

**Finding F3a (Low):** The wPLI implementation is mathematically correct for non-debiased wPLI but has not been verified against an external library. At N_fixed=15 (G8f) or 6 (G24f) epochs, the debiasing correction would be non-trivial. The lack of debiasing is a design choice, not a bug, but should be disclosed. **No fix required; add a note to the final report.**

**Finding F3b (Low):** Line 114 averages wPLI across frequency bins: `np.mean(adjacency, axis=2)`. This gives equal weight to each FFT bin within the band. An alternative is to sum cross-spectra across frequencies before computing the ratio (the more common convention). The current implementation computes wPLI per-frequency and then averages. This is a valid but different estimator. **Disclose in the final report.**

### F4. Contralateral lesion mapping and sign rule

[build_spectral_lesion_v2.py:49](file:///d:/brain-stroke/src/build_spectral_lesion_v2.py#L49): `sign = 1.0 if lesion_side == "left" else -1.0`. Applied to all AI columns. The test at [test_lesion_align.py:46-59](file:///d:/brain-stroke/tests/test_lesion_align.py#L46-L59) verifies: left lesion → +AI, right lesion → −AI, global features unchanged. [METADATA_AUDIT.md:17-18](file:///d:/brain-stroke/docs/METADATA_AUDIT.md#L17-L18) confirms: max absolute difference 1.11e-16 across 800 values. **Correct.**

### F5. 48-subject graph subsets and excluded subjects

sub-13 and sub-40 are excluded because their screened epoch counts (4 and 9 for G8f core; 0 and 4 for G24f expanded) are below N_fixed=15 and N_fixed=6 respectively ([graph_design_audit_v2.json:200,227,252,279](file:///d:/brain-stroke/docs/graph_design_audit_v2.json#L200)).

**Finding F5a (Med):** The class labels (mild/moderate) of sub-13 and sub-40 are not reported in any feature-side document. The registry states 48 subjects for T5/T6 but does not disclose whether the exclusions are balanced across classes. Checking `subject_meta.csv`:

- sub-13: NIHSS and severity are in `subject_meta.csv` but I have not read those specific rows. However, looking at the metadata header, I can see it contains `nihss_raw` and `severity_class`.

**UNVERIFIED:** I did not read the specific NIHSS/severity values for sub-13 and sub-40 to avoid label-adjacent analysis. The feature handoff should state whether the exclusions change the class ratio (e.g., "both mild" or "one from each class"). If both are from the same class, the 48-subject subset has a different class balance than the 50-subject set, which affects stratification and power. **This must be checked and disclosed before freeze.**

### F6. Residual epoch-count correlations and seed instability (G24f N_fixed=6)

From [FEATURE_QC_V2.md](file:///d:/brain-stroke/docs/FEATURE_QC_V2.md):

**G8f:** Largest epoch-count correlation: `alpha_FrobeniusDist` at −0.359 (line 34). Most features are |r| < 0.25.

**G24f:** Several features have |r| > 0.4: `alpha_FrobeniusDist` −0.531, `alpha_ClustCoeff_absAI` −0.451, `alpha_MeanHomotopic` −0.417, `beta_FrobeniusDist` −0.412 (lines 102-107).

**Second-seed stability:**
- G8f: Lowest stability is `theta_ClustCoeff_absAI` at 0.722 (line 69). Most features are >0.85.
- G24f: Lowest is `theta_ClustCoeff_absAI` at 0.532 (line 138), and several are below 0.8.

**Assessment:** G24f's epoch-count correlations above 0.4 and seed stability below 0.6 are concerning. With N_fixed=6, the median over 100 subsamples is sensitive to individual epoch content. This was anticipated by designating G24f as secondary.

If epoch count is correlated with NIHSS (UNVERIFIED — this would be a label-driven check and must not be done before the real run), then the epoch-count correlation in features could create a confound pathway: NIHSS → epoch count → feature → prediction. The fixed-epoch design was intended to break this pathway, but N_fixed=6 is too small to fully decouple.

**Recommendation:** Report the epoch-count correlations and seed instability prominently. After the real run, compute the partial correlation of each feature with NIHSS after controlling for epoch count. This is a post-run diagnostic, not a pre-registered analysis.

### F7. Claims in V2_FEATURE_HANDOFF and FEATURE_CHANGELOG

- "G8f uses the established clean channel core and supports 15 fixed usable epochs." ✅ Verified from [graph_design_audit_v2.json:291](file:///d:/brain-stroke/docs/graph_design_audit_v2.json#L291).
- "G24f retains more channels but the expanded screen reduces the feasible fixed count to 6." ✅ Verified from [graph_design_audit_v2.json:292](file:///d:/brain-stroke/docs/graph_design_audit_v2.json#L292).
- "The artifact screen is applied to the actual sampling pool." ✅ Verified from code and test.
- "Both graph tables were regenerated after this correction." UNVERIFIED — I cannot verify that the current CSV hashes correspond to post-fix regeneration without running the pipeline. The MANIFEST hashes exist but were self-reported.
- "No feature was tuned or removed using NIHSS or severity labels." ✅ Verified from code inspection; no label access in any feature builder.
- "No real-label v2 evaluation has been performed." ✅ Consistent with all evidence.

### Feature Freeze Verdict

**Approve after fixes:**

1. **(MUST)** Disclose the class labels of sub-13 and sub-40 and report the resulting class balance for the 48-subject subset.
2. **(SHOULD)** Add a note to the final report that wPLI is non-debiased and frequency-averaged (not sum-then-ratio).

---

## G. STATISTICAL VALIDITY OF THE WHOLE DESIGN

### Single most likely way this analysis misleads

**Underpowered registry produces a universal null result that is mistakenly interpreted as evidence of no effect.** At N=50 with 17 moderate subjects and m=9 Holm corrections, the minimum detectable ρ at the strictest Holm threshold is ~0.48 (registry §11). The pipeline's nested CV further attenuates observed ρ by ~50% relative to population ρ (Section C). To detect a population ρ of 0.48, the pipeline would need to produce OOF ρ ≈ 0.24 — below the .30 decision threshold. **The design is essentially powered to detect only large effects (population ρ > ~0.60).** A null result therefore cannot rule out moderate effects and must not be reported as "no association between EEG features and NIHSS."

### Is m=9 with ρ≥.30 sensible at N=50?

**m=9 is aggressive but acceptable** given that the tests are pre-specified and the Holm procedure controls FWER. The ρ≥.30 floor is reasonable as a minimum clinically meaningful effect (corresponding to ~9% variance explained). At N=50, a simple Spearman test can detect ρ=.39 at 80% power uncorrected. With Holm's strictest multiplier (×9), the effective α for the smallest p is .0056, requiring ρ ≈ .48 for 80% power. **The T7-T9 direct correlations have the best chance of detection** because they avoid CV attenuation.

### Is T3 interpretable?

T3 uses lesion-aligned AI features with sign = +1 for left lesion, −1 for right. The alignment depends on the contralateral assumption (paralysis side → opposite lesion side). [METADATA_AUDIT.md:9](file:///d:/brain-stroke/docs/METADATA_AUDIT.md#L9) confirms this is a prescribed mapping, not imaging-verified for every subject. The mapping has 22 left and 28 right lesion sides.

**T3 is interpretable if the sign convention is correct for most subjects**, but a few misclassifications would dilute the signal without creating a systematic bias. The main risk is that posterior fossa strokes (e.g., sub-02, sub-03 with pons/cerebellum lesions) may not produce contralateral EEG asymmetry at all, making the alignment meaningless for those subjects. With N=50 and mixed lesion locations, T3 is at best a rough test of whether hemisphere-specific EEG markers track severity. **Report T3 with explicit caveats about the contralateral assumption and posterior fossa subjects.**

### Is the decision rule too strict or too loose?

**Too strict for the available power, which is by design.** The registry acknowledges this ([ANALYSIS_REGISTRY.md:119](file:///d:/brain-stroke/docs/ANALYSIS_REGISTRY.md#L119)). The rule was pre-specified and should not be changed. A positive result under this rule would be credible; a negative result is expected and uninformative about moderate effects.

### Claims the data can support

Regardless of outcome:
- **All pass:** "Exploratory evidence of EEG-NIHSS association in acute stroke; replication required. The effect withstood Holm correction over 9 tests at FWER=.05 with a minimum ρ=.30 floor."
- **Some pass:** Same, plus: "Cannot infer that passing feature sets are superior to failing ones from this analysis alone."
- **None pass:** "No evidence of a large EEG-NIHSS association was detected in this 50-patient exploratory analysis. The design had limited power to detect moderate effects (population ρ < .60). This does not exclude clinically meaningful associations."

---

## H. FUTURE DECISIONS AND PROJECT IMPROVEMENT

### Before freeze

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 1 | Implement and run the amended positive-control validation (Option 3, Section C) | MUST | M |
| 2 | Disclose class balance for sub-13/sub-40 exclusion in feature docs | MUST | S |
| 3 | Run data-integrity checks on pairs 4/5, 11/15, 47/49 (metadata comparison, full-channel identity) | MUST | S |
| 4 | Add CRLF-safety check or blob-hash comparison to `verify_freeze` | SHOULD | S |
| 5 | Document the grouped-split sensitivity analysis in the registry amendment | SHOULD | S |
| 6 | Add `git status --porcelain` dirty-tree check to `verify_freeze` | SHOULD | S |
| 7 | Regenerate freeze manifest, hashes, and artifact digest after all changes | MUST | S |
| 8 | Obtain and commit actual independent review approvals | MUST | S |
| 9 | Create `registry-v1` and `features-v2` tags | MUST | S |

### Between freeze and the real run

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 10 | Verify `.gitattributes` does not cause CRLF issues on the execution machine | MUST | S |
| 11 | Run `verify_freeze` on the actual execution machine and confirm it passes | MUST | S |
| 12 | Confirm sklearn/numpy/scipy versions match the development environment | SHOULD | S |

### After the real run

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 13 | Run the grouped-split sensitivity (pairs in same fold) for T1-T6 | SHOULD | M |
| 14 | Compute partial correlations of features with NIHSS controlling for epoch count | SHOULD | S |
| 15 | Run the pre-specified sensitivity models (SVR, RF, combined) descriptively | SHOULD | M |
| 16 | Prepare the final report with all required disclosures (Section G claims language) | MUST | M |

### Interpretation policy

**If ALL of T1-T9 fail:** Report as a pre-specified null result. Emphasize limited power. Do not interpret as "EEG cannot predict stroke severity." Do not run additional exploratory analyses to find a positive result.

**If exactly one passes:** Report the specific test and effect size. Note that with m=9, the expected number of false discoveries at FWER=.05 is ≤1 by Holm control, so a single detection is credible but fragile. Recommend external replication. If it is a T7-T9 association, no predictive model is promoted.

**If several pass:** Report all. Do not rank feature sets by p-value. If T1-T6 tests pass, export the qualified model(s). Note that multiple passing tests increase confidence but do not multiply the evidence (they may share signal through correlated features).

### UCLH Phase 9

**O1/O2 are absent from the UCLH montage** ([UCLH_MONTAGE.md:70](file:///d:/brain-stroke/docs/UCLH_MONTAGE.md#L70)). I1/O9 and I2/O10 are physically different electrode positions and must not be silently substituted. This means:

- T1/T2/T3/T7-T9 feature sets include O1O2 AI and pdBSI features that cannot be computed from UCLH data without dropping or substituting the O1/O2 pair.
- T4 legacy graph features include O1/O2 in the 8-channel core.
- T5/T6 graph features use O1/O2 in the G8f core and the G24f expanded set.

**Recommendation:** Phase 9 UCLH should be **descriptive only** (MUST). Pre-specify this now. Define a reduced 6-channel montage (F3/F4, C3/C4, P3/P4) for the UCLH comparison. Report the feature subset that can be computed and the subset that cannot. Do not apply the Figshare decision rule to UCLH data. The effective reference and eyes-open/closed conditions also remain unresolved ([UCLH_AUDIT.md:1](file:///d:/brain-stroke/docs/UCLH_AUDIT.md#L1), [UCLH_MONTAGE.md:95](file:///d:/brain-stroke/docs/UCLH_MONTAGE.md#L95)).

| # | UCLH Item | Priority | Effort |
|---|-----------|----------|--------|
| 17 | Pre-specify UCLH as descriptive-only in the registry or a separate UCLH protocol | MUST | S |
| 18 | Define the reduced montage (drop O1/O2 pair) and document which features are computable | MUST | S |
| 19 | Verify the UCLH EEG reference from raw headers | MUST | M |
| 20 | Resolve eyes-open/closed condition from the actual data segments | SHOULD | M |
| 21 | Do not substitute I1/O9 or I2/O10 for O1/O2 | MUST | S |

### Final report disclosures (MUST)

1. The dependent-recording pairs and their potential effect on CV and permutation validity.
2. The post-failure positive-control amendment and its justification.
3. The limited power at moderate effect sizes.
4. The contralateral assumption for T3 and posterior fossa cases.
5. G24f seed instability and epoch-count correlations.
6. wPLI is non-debiased and frequency-bin-averaged.
7. The frozen Phase 5 null result.
8. UCLH montage limitations.

### What would move the science forward

- **Replication on an independent dataset with imaging-verified lesion lateralization** (not the UCLH data, which has its own limitations). N≥100 with prospective NIHSS assessment would provide adequate power.
- **Dense-array EEG** (64+ channels) to test topographic features beyond the 10-20 system.
- **Longitudinal NIHSS** to separate acute from chronic severity.

### Process improvements

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 22 | Add a CI/CD pipeline that runs unit tests on every commit | NICE | M |
| 23 | Pin exact package versions in `requirements.txt` with hashes | SHOULD | S |
| 24 | Reduce the number of manual steps in the freeze process by scripting the manifest/digest/approval workflow | SHOULD | M |
| 25 | The project has too many documentation files with overlapping scope (PROGRESS, CONTEXT, two ledgers, FREEZE_READINESS, B2_B3_IMPLEMENTATION, ANALYSIS_REGISTRY). Consolidate after the run | NICE | L |

---

## I. THINGS I DID NOT ASK THAT YOU THINK I SHOULD KNOW

1. **The wPLI adjacency symmetrization at [graph_features_v2.py:115](file:///d:/brain-stroke/src/graph_features_v2.py#L115) uses `np.maximum(adjacency, adjacency.T)`.** This takes the element-wise maximum rather than averaging. For a symmetric input (cross-spectrum `S_ij * conj(S_ji)` = `conj(S_ji * conj(S_ij))`), the adjacency should be symmetric by construction, so this is a no-op in exact arithmetic. But numerical asymmetry from float accumulation means `max` vs `mean` could produce slightly different values. The effect is negligible but the choice should be documented.

2. **The `simulated()` function in [validate_registry_v2.py:23](file:///d:/brain-stroke/src/validate_registry_v2.py#L23) creates strata using a 66th-percentile split**: `strata = (y > np.quantile(y, 0.66)).astype(int)`, producing ~34% class-1 prevalence. The real data has 17/50 = 34% moderate subjects. This is a reasonable match, but the simulated strata are deterministic functions of y (the outcome), which means they perfectly predict the outcome's direction. In the real data, the NIHSS-to-severity mapping is not perfectly aligned (NIHSS 4 is mild, NIHSS 5 is moderate). This could make the simulated setting slightly easier than the real one for stratification purposes.

3. **The `load_analysis` function at [train_regression.py:169-170](file:///d:/brain-stroke/src/train_regression.py#L169-L170) checks for constant features** (`np.ptp(X, axis=0) == 0`). If a feature has near-zero but non-zero variance (e.g., all values within float precision of each other), it would pass this check but could cause numerical instability in Ridge. The `StandardScaler` would amplify the noise. This is unlikely given the QC checks but is a theoretical edge case.

4. **No test covers the `prediction_metrics` function** with a dummy regressor that predicts the training mean. If the training mean happens to equal the test target for some fold, `r2_score` returns 0 for that fold (correct), but if the dummy prediction is constant and the test targets are also constant (impossible with stratification), `roc_auc_score` would fail. The AUC call at [train_regression.py:91](file:///d:/brain-stroke/src/train_regression.py#L91) uses `strata` as the binary target, which is not constant within any fold (stratification ensures both classes are present). **Low risk but no explicit test.**

5. **The bootstrap CI for T7-T9 associations** ([train_regression.py:118](file:///d:/brain-stroke/src/train_regression.py#L118)) passes `X[:, 0]` (the single feature) as the `predictions` argument. `bootstrap_ci` then calls `pooled_oof_spearman(y[idx], X[idx, 0])`, which computes Spearman between resampled y and resampled X. This is a valid non-parametric bootstrap for Spearman ρ, but the function's docstring says "conditional on supplied predictions." For T7-T9, the "predictions" are not model outputs but raw features, so the CI captures sampling uncertainty rather than model uncertainty. This is correct for a direct correlation CI but the naming is potentially confusing.

---

## J. LIMITS OF THIS REVIEW

### What I could not verify

1. **Byte-level hash verification:** I did not recompute SHA-256 hashes of any file to confirm they match the manifest. I relied on the recorded values.
2. **Feature regeneration:** I did not run the feature extraction pipeline (requires EEG data files which were not loaded). The claims that current CSVs match post-bug-fix regeneration are UNVERIFIED.
3. **Cross-computer path equivalence:** The user-confirmed equivalence between `data/processed/figshare/sub-*-epo.fif` and `clean/sub-*-clean-epo.fif` is taken at face value.
4. **Real label values:** I did not inspect NIHSS values for sub-13/sub-40 or any other subject, as required by the review constraints.
5. **External wPLI validation:** The wPLI implementation was not compared against `mne-connectivity` or any other external library.
6. **CRLF behavior:** I did not check `.gitattributes` or test `verify_freeze` across platforms.
7. **Null calibration reproducibility:** I did not rerun the 100-dataset null calibration. The reported 3% FPR and KS statistic of 0.132 are taken from the recorded results.

### What I assumed

1. The 20 unit tests that passed are representative of the codebase's correctness. There may be untested paths (e.g., the real-mode model export path has only a mock test).
2. The Figshare metadata provenance chain (participants.json → subject_meta.csv) is correct as documented in METADATA_AUDIT.md.
3. The user's decision to retain dependent recordings is final and will not be reversed.

### What a second reviewer should check

1. **Hash verification:** Recompute all manifest hashes and confirm they match. This is the single most important mechanical check I could not perform.
2. **wPLI against MNE-connectivity:** Run the same data through `mne_connectivity.spectral_connectivity_epochs` with method='wpli' and compare.
3. **Class balance of excluded subjects:** Read the NIHSS values for sub-13 and sub-40 and report the 48-subject class split.
4. **CRLF test:** Run `verify_freeze` on a Windows machine with `core.autocrlf=true` and confirm it works.
5. **The smoke run output:** Inspect `results/v2/smoke/` to confirm all nine tests completed with plausible shuffled-label results.
