# Figshare v2 Analysis Registry

**Status: Statistical specification finalized; Option 3 post-failure amendment validated on 2026-10-19. Fresh review of amended artifacts, human sign-off and freeze pending. No real-label evaluation authorized.**

**Draft date:** 2026-10-17

**Owner:** Group B

**Authority:** `EXECUTION_GUIDE_CURRENT.md` and explicit team decisions recorded below.

**Study description:** Pre-specified exploratory analysis. The completed legacy binary-classification results remain frozen.

## 1. Purpose and hypotheses

Evaluate whether fixed spectral and graph feature sets predict raw NIHSS severity, and whether the three global spectral features correlate with NIHSS. The cohort contains no severe subjects; findings cannot support a three-class severity claim.

For T1–T6, the prediction hypothesis is positive association between pooled out-of-fold predicted NIHSS and observed NIHSS. No particular multivariable coefficient sign is specified. For T7–T9, higher NIHSS is expected to accompany higher pdBSI, DAR and DTABR respectively; both observed directions will be reported.

Feature definitions, channels, artifact rules, sampling counts and seeds must be fixed using engineering evidence before labels are evaluated. No feature set, subject exclusion or statistical procedure may be selected because it improves a real-label result.

## 2. Cohort and explicit team decisions

- Retain the dataset's 50 subject identities: 33 mild (NIHSS 1–4) and 17 moderate (NIHSS 5–11). The primary regression target is `nihss_raw`; `severity_class` is used only for stratification and descriptive binary AUC.
- On 2026-10-17 the user decided to treat subjects 4/5, 11/15 and 47/49 as different subjects and retain them. The primary split unit remains subject ID, with no similarity grouping or exclusion. Their previously observed signal identity/similarity must be disclosed: different IDs do not establish statistical independence, and similar signals can appear in both training and test folds. Nominal CV estimates and permutation p-values rely on subject exchangeability and must be interpreted with this limitation. This decision does not establish that the signals are independent.
- The user confirmed that `data/processed/figshare/sub-*-epo.fif` and the separately stored `clean/sub-*-clean-epo.fif` files refer to the same processed data on different computers. Treat this as a user-confirmed location equivalence, not a new preprocessing change. Record actual paths and source hashes at freeze.
- T3 is included: the source semantics and side mapping passed the feasibility rule (22 left and 28 right mapped lesion sides). Alignment uses the prescribed contralateral mapping from paralysis side; it does not represent imaging verification of every lesion hemisphere. See `METADATA_AUDIT.md`.
- T5/T6 contain 48 subjects, excluding `sub-13` and `sub-40` under the locked epoch eligibility rules. The screen/sampling correction is implemented; nine tests and all 19 manifest checks pass locally (2026-10-19). Independent reviews and remaining freeze gates are pending. The user authorized the recommended classification on 2026-10-19: G24f is a secondary registered analysis, T6, inside the nine-test Holm family. It is not an unregistered sensitivity analysis.

## 3. Registered test family

| ID | Analysis | Input table / columns | Expected N | Number of features |
|---|---|---|---:|---:|
| T1 | Ridge prediction of NIHSS: signed spectral baseline | `features/figshare_features.csv`: 16 `all_AI_{band}_{pair}` plus `all_pdBSI`, `all_DAR`, `all_DTABR` | 50 | 19 |
| T2 | Ridge prediction: absolute spectral | `features/v2/spectral_abs.csv`, sidecar feature list | 50 | 19 |
| T3 | Ridge prediction: lesion-aligned spectral | `features/v2/spectral_lesion.csv`, sidecar feature list | 50 | 19 |
| T4 | Ridge prediction: legacy graph baseline | `features/figshare_graph_features.csv`, explicit frozen 16-feature list | 50 | 16 |
| T5 | Ridge prediction: primary fixed-epoch core graph | `features/v2/graph_g8f.csv`, sidecar feature list | 48 | 16 |
| T6 | Ridge prediction: secondary expanded fixed-epoch graph | `features/v2/graph_g24f.csv`, sidecar feature list | 48 | 16 |
| T7 | Direct Spearman association with NIHSS | T1 source: `all_pdBSI` | 50 | 1 |
| T8 | Direct Spearman association with NIHSS | T1 source: `all_DAR` | 50 | 1 |
| T9 | Direct Spearman association with NIHSS | T1 source: `all_DTABR` | 50 | 1 |

Bands: delta, theta, alpha, beta. Spectral pairs: F3F4, C3C4, P3P4, O1O2. The exact legacy T1/T4 feature lists must be stored in a new evaluation config/contract without editing legacy artifacts. Do not discover model columns by broadly dropping metadata or selecting every numeric column.

The primary multiplicity family is **m=9**, including T3. Do not reduce m because a result fails, is negative or encounters an execution error. Any label-blind eligibility change before freeze requires a documented amendment here, in the config and in `PROGRESS.md`.

## 4. Data validation and leakage safeguards

Load feature columns in the exact order given by their sidecar or the explicit legacy contract. Join with `features/v2/subject_meta.csv` one-to-one on `subject_id`. Assert unique IDs, the expected subject membership and N, finite numeric features and target, valid severity values and no missing join records. A different N is a failure requiring investigation, not permission to silently continue with fewer rows.

IDs, NIHSS, severity, lesion/paralysis side, age, sex, onset/duration, epoch counts and other metadata never enter X. No imputation or data-driven column removal is planned. Report constants or unexpected schema changes as engineering failures before freeze. No global scaling or selection is permitted; there is no `SelectKBest` in the primary model.

For every analysis subset, generate splits and permutations within that subset. Report N, class counts and excluded IDs for every test. Do not impose the 48-subject graph intersection on the 50-subject spectral tests. Comparisons across tests with different subjects are descriptive.

## 5. Primary model and nested alpha selection

The only inferential model family is Ridge regression with intercept. Alpha grid: `numpy.logspace(-2, 3, 20)`. The intended model is standardized features followed by Ridge, with alpha chosen using only each outer training set.

**Final statistical specification:** use the selection rule of `GridSearchCV(Pipeline(StandardScaler(), Ridge(solver='svd')), alpha_grid, cv=KFold(5, shuffle=True, random_state=42), scoring='neg_mean_squared_error', refit=True)`. Fit this entire search on each outer training set. The scaler is refitted within every inner training fold and the selected pipeline is refitted on the full outer training set before predicting the held-out outer fold. Alpha ties choose the first alpha in ascending grid order.

The Group B guide names `Pipeline(StandardScaler(), RidgeCV(...))`. Fitting the scaler outside RidgeCV's internal splits would let inner-validation features influence scaling. The proposed implementation preserves the intended alpha grid and Ridge model while nesting scaling correctly. This clarification is adopted before label evaluation. `fit_ridge` computes the same inner validation MSE path using one SVD per inner fold for all alphas, then refits a sklearn StandardScaler/Ridge Pipeline. Each inner scaler is fitted in its own preprocessing Pipeline on inner-training data only. A synthetic equivalence test compares selected alpha and predictions with full-pipeline GridSearchCV; independent review remains required.

## 6. Outer CV and observed statistics (T1–T6)

Outer CV is `RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)`, stratified using `severity_class` while fitting raw `nihss_raw`. Sort each subset by `subject_id` before splitting. Use identical outer folds across feature sets with identical subjects and strata. Each subject receives exactly one held-out prediction per repeat.

For repeat r, pool the five held-out folds into one prediction vector for all subjects in that subset and calculate `rho_r = Spearman(y, prediction_r)`. The primary statistic is the arithmetic mean of the ten repeat-level rhos. Do not average fold-level correlations or treat the ten predictions of one subject as ten independent observations.

Also report, for each repeat and their arithmetic means, RMSE, MAE, R², and ROC-AUC using predicted NIHSS as the continuous score for mild=0 versus moderate=1. Compute these metrics on the pooled held-out predictions of each repeat. AUC is a descriptive bridge to the frozen binary analysis, not another inferential test.

Fit `DummyRegressor(strategy='mean')` within each outer training fold and score it on the matching held-out fold. Report its pooled repeat-level RMSE, MAE and R², their means, and Ridge-minus-dummy differences. R² uses its usual definition on the pooled repeat; do not replace its denominator with the dummy's errors without separately naming that measure.

If a statistic is undefined, preserve the failure and diagnose it. Do not silently convert undefined correlations to zero or discard folds/repeats/permutations.

## 7. Permutation inference

Use 1,000 permutations per test and the finite-sample correction `(1 + exceedances)/(1000 + 1)` with ties counted as exceedances.

For T1–T6, permute the (`nihss_raw`, `severity_class`) pairs jointly across subjects within the analysis subset. Keep X fixed. Regenerate the outer stratified splits from the permuted severity classes using seed 42; refit the complete nested model, including alpha selection and scaling, in every outer training fold. Recalculate the mean repeat-level pooled rho. Do not reuse the observed folds or selected alphas for the null run.

For T7–T9, compute Spearman between the single fixed feature and NIHSS. Permute NIHSS across subjects and recompute rho. No scaling, regression or CV is used for these three tests.

**Final tail clarification:** the Group B guide says tests are two-sided but gives an upper-tail prediction p-value formula. Adopt the following explicit distinction: T1–T6 use the specified upper-tail statistic (`null_mean_rho >= observed_mean_rho`), because only positive predictive rho qualifies as signal. T7–T9 use two-sided permutation inference (`abs(null_rho) >= abs(observed_rho)`), while reporting the signed rho and the expected positive direction. T1–T6 are one-sided prediction tests; T7–T9 are two-sided association tests. This distinction is finalized before real-label evaluation.

Use `numpy.random.default_rng` and record seeds in the evaluation config. Fixed permutation seeds: `42000 + test_number`; fixed bootstrap seeds: `52000 + test_number`. These choices are recorded in `configs/registry_v1.json`. Split seeds remain 42. No optional stopping or adaptive increase in permutation count is planned.

## 8. Bootstrap intervals

T7–T9: 2,000 paired subject bootstrap resamples with replacement; percentile 95% CI (2.5th and 97.5th percentiles) for signed Spearman rho.

T1–T6: descriptive 95% percentile intervals from 2,000 paired subject resamples of the saved N-by-10 out-of-fold prediction matrix and its target vector. Resample each subject's entire ten-repeat prediction row together and recompute the mean repeat-level pooled rho. These intervals condition on the fitted CV predictions and do not capture full model-refitting uncertainty. They do not determine significance or replace permutation inference. This procedure specifies the requested predictive CI output; only the permutation test and Holm rule determine significance.

Draw exactly 2,000 resamples with no redraws. Count every undefined resample. If at most 1% are undefined, calculate percentile limits from the finite draws and report the invalid count; otherwise report the CI unavailable. Unavailable descriptive CIs do not change p-values or the decision rule. Undefined observed or permutation statistics fail the test and withhold family-level decisions until fixed. A percentile interval is not guaranteed to contain the point estimate; tests do not impose that incorrect requirement.

## 9. Multiplicity and decision rule

Apply Holm adjustment jointly to the nine raw permutation p-values at familywise alpha 0.05. Sort p-values ascending, multiply ranked p by `m - rank + 1`, take the cumulative maximum, cap at 1, and restore original test order.

- T1–T6 qualify as signal only if Holm-adjusted p < 0.05 **and mean pooled out-of-fold rho >= 0.30**.
- T7–T9 qualify only if Holm-adjusted p < 0.05 **and abs(rho) >= 0.30**. Report whether the direction agrees with the hypothesis.
- Preserve test failures in the results table with a reason. A failed required test blocks a complete inferential report until a documented fix/rerun; do not shrink m or silently omit it.

Report every registered test, including negative and nonsignificant findings. Use “no effect detected” when the rule is not met. Do not infer a difference between feature sets merely because one passes and another fails.

## 10. Sensitivity analyses and model promotion

Outside the nine-test Holm family, report only descriptive sensitivity results for RBF SVR (`C=1`, `epsilon=0.1`, `gamma='scale'`), RandomForestRegressor (`max_depth=3`, `n_estimators=300`, `random_state=42`), and combined absolute spectral plus G8f features (Ridge on their subject intersection). Use the same outer evaluation scheme and pipeline scaling where relevant. The intended estimator settings and model versions must be recorded with any sensitivity invocation. Sensitivities are specified for later descriptive reporting and are not executed by the primary registry runner. Sensitivities cannot rescue a failed registered test and have no significance claims. No further model or feature search is planned.

Only a T1–T6 feature set meeting the decision rule may be refitted using the same training procedure on its full analysis subset and saved to `results/v2/models/` with its feature contract and provenance. A T7–T9 association alone does not promote a predictive model. If none of T1–T6 qualifies, save no predictive model for promotion to Phase 9.

## 11. Outputs and run protocol

Implemented engine: `src/train_regression.py`; statistics: `src/stats_utils.py`; sole real-label entry point: `src/run_registry.py`. Until freeze, tests use simulated or shuffled labels only. Real-label associations, including T7–T9, may not be computed as plumbing checks.

Before the run, the harness must verify `registry-v1` and `features-v2`, registry/config identity against frozen content, input SHA-256 hashes against `features/v2/MANIFEST.json`, exact feature contracts, and subset membership. Tag existence alone is insufficient if working files differ from the frozen artifacts. Reject uncommitted or untracked changes under `src/`, `configs/`, and `tests/`, including staged changes; only verified CRLF/LF differences against the index are exempt. Snapshot schema 2 hashes UTF-8 content with CRLF converted to LF only; whitespace, encoding, values and all other content remain exact. It binds the feature manifest and all its artifacts to the registry, retaining Group A's original byte hashes as `source_sha256`. Tagged registry and feature contents must match the same bindings. Record package versions, source commit, timestamps, config hashes and all input hashes. Use a new run directory and fail on accidental overwrite. The one latest owner-review record must match the registry artifact digest and be committed in the registry tag. The runner refuses a pending, absent or stale owner review.

Required outputs include `results/v2/registry_results.csv` (ID, N/class counts, rho/CI, raw p, Holm p, RMSE/MAE/R², dummy comparison, descriptive AUC, decision and failure reason), per-test `.npy` null distributions, repeat/fold membership and out-of-fold predictions, selected alphas, and resolved JSON configs. Direct-association tests have model-only metric fields marked not applicable. Log each real-label invocation and any bug-driven rerun in `docs/PROGRESS.md`; preserve earlier runs and explain differences. After freeze, added analyses belong in a clearly separate post-registry section and cannot alter registered claims.

At N=50, the guide's approximate minimum detectable rank correlation at 80% power is 0.39 uncorrected and about 0.48 at Holm's strictest threshold, before CV attenuation. These are rough planning figures based on independent observations; they are not a power calculation for this exact nested pipeline and may be optimistic given the signal-similarity finding. N=48 graph subsets also have less nominal power. A null result does not rule out smaller effects.

## 12. Post-Failure Positive-Control Amendment (Option 3)

**Date:** 2026-10-19. **Authorization:** the user adopted Option 3 of the supplied independent review, preserved at `docs/reviews/independent_review_20261019.md`. This amendment is recorded before the new simulations and before any real-label v2 evaluation.

The original fixed moderate-signal simulation (population Pearson correlation 0.65; seed 81000) failed its single-dataset p<0.01 gate: full nested five-fold/ten-repeat Ridge evaluation returned mean pooled OOF Spearman rho=0.333647 and p=0.011988 (approximately 0.012). The independent review attributes this to a design-sensitivity/power mismatch at N=50 with 19 features, not a code defect; it found no result-changing defect and confirmed the SVD/GridSearchCV equivalence test. This is the review's supported diagnosis, not proof that every possible defect is absent. The original reduced/full failed controls and the subsequent strong-signal diagnostic remain in the evidence history.

Replace only the positive-control acceptance rule with these two gates:

| Gate | Data-generating population Pearson correlation | Datasets | Permutations per dataset | Outer repeats | Acceptance |
|---|---:|---:|---:|---:|---|
| A: correctness check | 0.95 | 1 | 199 | 2 | raw upper-tail permutation p < 0.01 |
| B: power diagnostic | 0.65 | 200 | 200 | 2 | fraction with raw p < 0.05 is in [0.50, 0.95], inclusive |

Both gates use the existing nested five-outer/five-inner-fold Ridge procedure and its fixed 20-alpha grid. Every simulation has 50 independent Gaussian subjects, 19 features with only feature 0 informative, unit-variance target construction, and severity-like strata at the target's 0.66 quantile. Gate A retains dataset seed 81000 and permutation test number 1. Gate B fixes dataset seeds 83000 through 83199 and uses each dataset seed as its permutation test number. Seed bases for permutations/bootstrap remain 42000/52000. Gate A uses 100 descriptive bootstrap draws and Gate B 10; these intervals do not determine acceptance. Four workers each limit numerical-library threads to one. No early stopping, seed replacement, failed-dataset omission, or threshold adjustment is allowed.

The power diagnostic uses two outer repeats for computation, as specified by the review; it does not estimate exact power for the ten-repeat registered analysis. Its raw-p detection rate is also not Holm-adjusted registry power. The [50%, 95%] bounds are the explicitly adopted operational diagnostic, not theoretical limits on achievable power: a rate above 95% would fail this agreed diagnostic but would not by itself prove leakage or invalid inference. Report the numerator, denominator, every dataset result and a binomial uncertainty interval.

Overall validation acceptance requires both gates, the existing passed null calibration, current unit tests and the completed shuffled smoke checks. A failed or incomplete gate leaves acceptance false. Real-analysis settings, the nine-test Holm family, rho threshold, cohort membership and feature definitions are unchanged. Historical reviews preserve the amendment rationale; only Agrim's latest owner review of the final digest is required before explicit tag authorization.

**Recorded outcome:** Gate A passed with OOF rho=0.829916 and p=.005. Gate B completed all 200 fixed datasets with 168 detections (84%; exact binomial 95% CI 78.17-88.79%), passing the adopted range. All 201 permutation p-values were independently recomputed from saved null statistics. Current unit/integration tests: 32 passed; prior null calibration and nine shuffled smoke analyses remain passed. `docs/REGISTRY_VALIDATION_RESULTS.json` now records `acceptance_passed: true` while preserving the original failures. The full report and its hash are linked there. This is synthetic acceptance only; owner review and tags are still required.

## 13. Review and freeze acceptance

Statistical choices are settled and the primary engine is implemented; B1 freeze is not complete. Before `registry-v1`:

1. Complete and review the documented synthetic validation, including positive control, null calibration and shuffled smoke runs. Preserve failures and do not tune seeds or methods to force acceptance.
2. Review the corrected graph implementation, regenerated tables and provenance; retain secondary registered T6 and verify final membership and hashes.
3. Obtain Agrim's single authoritative owner review. It must cover the limitation from retaining similar recordings as separate split units and approve the exact final artifact digest. No AI-model or additional group approval is required.
4. Verify `configs/registry_v1.json`, its explicit legacy feature contracts, and `docs/REGISTRY_FREEZE_MANIFEST.json`. Update the registry artifact digest after any reviewed changes; the latest owner review must cover that exact digest. The feature manifest/changelog already exist and require review.
5. Obtain explicit authorization for commit/tag operations; this draft does not create tags. Complete the required freeze tags before the one-shot run.

Neither this registry nor the technical checks establish a v2 predictive improvement. The user authorized updating both ledgers on 2026-10-19; the technical ledger reflects current state and the timeline preserves the accumulated work.

## 14. Registered-results grouped-split sensitivity

This is a descriptive sensitivity for T1-T6 only, executed separately after the authorized one-shot primary run. It does not alter T1-T9, enter the nine-test Holm family, produce significance claims, promote a model, rescue a failed test, or invalidate a registered numerical decision. It may limit interpretation of a positive primary result.

Group `sub-04/sub-05`, `sub-11/sub-15`, and `sub-47/sub-49`; assign every other subject a unique singleton group. Preserve the exact primary subject and feature lists: T1-T4 have 50 subjects/47 groups and T5-T6 have 48 subjects/45 groups. Groups are split metadata only and never enter X. Do not infer further groups, drop pair members, merge labels, or change membership based on outcomes.

Use an explicit ten-repeat loop over `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42+r)` for outer repeat `r=0,...,9`. Within outer fold `f`, select the unchanged Ridge alpha grid using five-fold `StratifiedGroupKFold` on the outer-training subjects with seed `10042 + 5*r + f`. Fit StandardScaler only on each inner-training fold and refit the selected scaler/Ridge pipeline on the outer-training data. Scikit-learn has no `RepeatedStratifiedGroupKFold`; `GroupKFold` is not stratified. StratifiedGroupKFold approximates class balance subject to group constraints and does not guarantee exact balance.

Require zero train/test group overlap at both CV levels, exactly-once OOF coverage per outer repeat, finite predictions, unchanged ID/feature contracts, and saved fold class/group counts. Keep fixed seeds even if repeats produce duplicate assignments. Do not rejection-sample splits. Report failure rather than alter seeds, groups or membership if valid folds/statistics cannot be produced. A one-class fold makes its fold-level AUC unavailable; it must not be fabricated or silently discarded.

For each T1-T6, compare the saved primary mean pooled-repeat OOF Spearman rho with the grouped result. Report both rho values, signed `delta = primary - grouped`, absolute delta, and a descriptive `abs(delta) > 0.05` materiality flag, plus the same saved-repeat RMSE, MAE, R-squared and training-mean dummy comparisons. The threshold is a reporting convention, not a significance test. The delta reflects both grouping and changed fold/training composition; it is not an isolated estimate of leakage bias.

No new permutation p-values, Holm decisions, confidence intervals or dependence-adjusted inference are planned. Grouping prevents the three known pairs from crossing folds but does not establish participant identity, independence of other recordings, or validity of individual-level permutation exchangeability.

Implement this later in separate v2 source/config/test files without changing the frozen primary engine. Its JSON config must contain all groups, seeds and constants. Synthetic tests must cover pair isolation at both CV levels, deterministic splits, OOF coverage, fold-local scaling, absence of IDs/groups/targets from X, strict schema/membership failures, and preservation of primary artifacts. Bind sensitivity provenance to the primary-run identity. Review implementation before real-data execution; any outcome-informed change is post hoc.
