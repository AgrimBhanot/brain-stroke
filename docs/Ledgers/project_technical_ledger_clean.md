# Project Technical Ledger

**Current state updated:** 2026-10-21, interrupted primary recovery prepared; T1-T5 outputs verified and separate sensitivities implemented.

## Purpose and authority

This ledger is rewritten to describe current technical state; the timeline ledger preserves events. `EXECUTION_GUIDE_CURRENT.md` is authoritative, `AGENTS.md` gives repository rules, `docs/PROGRESS.md` gives status and `docs/CONTEXT.md` supplies the concise handoff. The original plan is archived at `docs/archive/PROJECT_EXECUTION_GUIDE_V1.md`. Group A's original assignment remains unchanged.

## Cohort, metadata and integrity

Figshare contains 50 subject IDs: 33 mild (NIHSS 1-4), 17 moderate (5-11), no severe. Labels and metadata are in `features/v2/subject_meta.csv` and never enter X. The authenticated participant TSV is version 5 asset 42345150; JSON asset 38516579 appears in versions 3-5 and matches the version 1 JSON checksum. All 50 version 1/version 5 paralysis sides agree. The dictionary defines limb paralysis side. The project's contralateral mapping gives 22 left and 28 right lesion sides, an alignment assumption rather than imaging confirmation. All 800 aligned AI values and three unchanged globals match the construction; T3 remains feasible. See `METADATA_AUDIT.md` for hashes and sources.

Explicitly authorized exclusion accounting found sub-13 NIHSS 9 and sub-40 NIHSS 6, both moderate. Each actual graph subset is 33 mild / 15 moderate (68.75%/31.25%), versus 66%/34% in the full cohort. The two feature documents now disclose the 2.75-percentage-point decrease in moderate prevalence. Eligibility and feature values were not changed.

`src/audit_recording_integrity_v2.py` with `configs/recording_integrity_v2.json` audited all 33 raw EDF signal channels and all 160,000 samples per channel at 500 Hz for pairs 04/05, 11/15 and 47/49. Reports: `docs/RECORDING_INTEGRITY_AUDIT_V2.md`/`.json`, including file/config/source hashes and per-channel statistics. All 32 named channels for 04/05 are exactly identical; the unnamed channel differs. Other pairs have only constant CPz exactly equal, with nonconstant named-channel correlations about .99937-.999997 and .99955-.999997 respectively. No complete EDF pair has equal file hashes or identical all-channel values.

Age and stroke location differ within all pairs; sex also differs for 04/05. Age/sex/location/duration/handedness for every paired ID agree between the source TSV and stored metadata. The discrepancy is therefore present in source metadata/signals, not a local transcription mismatch. The cause and participant identities remain unresolved. The user retains distinct IDs and subject-ID splits; this does not establish exchangeability and reviewers must assess the risk to CV and permutation inference. No pair outcomes were inspected in this integrity audit.

## Legacy and Group A feature state

Legacy spectral/graph sources, feature files and results remain frozen. Spectral classification was weak near the dummy baseline; v1 graph features had epoch-count dependence. The first registered original-label run is now in progress; results have not yet been interpreted.

- Absolute and lesion-aligned spectral tables: 50 subjects, 19 features plus ID.
- G8f: primary, eight core channels, N_fixed=15, 16 features.
- G24f: secondary registered T6 within the nine-test Holm family, 22 channels/11 pairs, N_fixed=6, 16 features.
- Both graph tables contain 48 subjects after excluding 13/40 under locked epoch requirements.
- Bands: delta 1-4, theta 4-8, alpha 8-13, beta 13-30 Hz.
- Graph metrics: absolute efficiency/clustering asymmetry, homotopic wPLI, normalized aligned Frobenius distance.
- Group A corrected the 150-microvolt screen to restrict the actual sampling pool before spectra/subsampling. Fixed-size sampling is without replacement, with 100 deterministic draws and median adjacency.
- Nine existing graph/lesion tests pass; residual epoch bias and second-seed instability remain reportable.
- Four provenance sidecars, feature manifest, changelog and handoff exist. All 19 original Group A byte hashes still match after this remediation. No full feature regeneration was repeated.

The user confirms the local processed epochs and the other computer's clean folder represent the same data. The generator still needs explicit local path mapping; the aggregate input hash does not provide individual cross-computer reconciliation.

### Primary execution interruption and recovery

On 2026-10-21, no Python registry process or previous tool session remains. `primary_20261020` contains complete T1-T5 files; T6-T9/family finalization are missing and its running metadata is stale. The original folder is preserved. All five saved tests pass exact contract/membership, target/class, OOF folds/coverage, dummy means, metrics, alpha-grid, permutation-tail/p-value and bootstrap checks. Their observed rhos are -.141440, -.222041, -.032221, -.248141 and .105778 respectively; raw p-values .545455, .809191, .310689, .902098 and .124875. No complete nine-test decision is available yet.

New `src/continue_registry_v2.py` and synthetic tests implement a recovery adapter without editing any frozen source. It validates original freeze identity, package versions, settings and input hashes, reuses the saved ordered prefix byte-for-byte, and invokes the frozen registry runner in a new directory to compute missing tests, apply the full nine-test correction and perform the original model-export rule. Original artifacts are hashed before/after and bound in `continuation.json`; functions are restored even on errors. An interrupted initial metadata snapshot stores LF-normalized legacy hashes alongside original-byte v2 manifest hashes, so comparisons honor the existing CRLF/LF contract. Content changes remain rejected. No subject, feature, threshold, seed, model or permutation count changed.

Recovery acceptance: all 47 tests pass in 29.848 seconds, including eight continuation tests. The unchanged 42-artifact snapshot passes self-check. The continuation will use `primary_20261021_continued`, preserving the original folder and reusing verified T1-T5.

## B1 specification and B2/B3 implementation

The primary model is standardized Ridge with a 20-alpha grid from .01 to 1000, selected by five inner shuffled KFold splits (seed 42), using scaling fitted inside each training fold. The efficient SVD path matches full-pipeline GridSearchCV. Outer CV is five folds by ten repeats, stratified by severity while predicting NIHSS. Pool OOF predictions within each repeat, then average ten Spearman correlations. Joint target/class permutations regenerate splits and refit the complete pipeline.

T1-T6 use upper-tail predictive inference; T7-T9 direct associations use two-sided inference. Use 1,000 permutations with plus-one/tie-inclusive correction and Holm over all nine tests. A signal requires adjusted p<.05 and rho>=.30 (absolute rho for T7-T9). The 2,000-draw subject bootstrap is descriptive/conditional on saved OOF predictions, with an explicit 1% invalid-draw rule. Undefined required statistics fail the family. No inference settings or memberships changed in this remediation.

Implementation includes `stats_utils.py`, `train_regression.py`, `run_registry.py`, `validate_registry_v2.py`, `write_registry_freeze_v2.py` and `freeze_io_v2.py`. Exact feature whitelists and memberships are in `configs/registry_v1.json`. All nine tests/failures, OOF folds/predictions/targets, alphas, nulls and metrics are retained in immutable run outputs. Whole-family failures withhold decisions and model export. Only qualifying predictive T1-T6 sets can promote a model. SVR/RF/combined sensitivities are implemented separately and cannot change the primary inference.

## Post-failure validation amendment and results

The independent review supplied by the user is preserved at `docs/reviews/independent_review_20261019.md`. It found no result-changing code defect and attributes the original moderate control's p=.011988 to a design-sensitivity/power mismatch. The user explicitly adopted Option 3. Registry section 12 recorded the amendment before new simulations; it preserves the failed reduced p=.010/full p=.011988 controls and the prior strong diagnostic.

Gate A: population Pearson r=.95, dataset seed 81000, 199 permutations, two outer repeats, strict p<.01. Result: OOF Spearman rho=.8299159664, p=.005, PASS.

Gate B: 200 independent r=.65 datasets, fixed seeds 83000-83199, 200 permutations and two repeats each, require 50-95% detection at raw p<.05. Result: 168/200 (84%), exact binomial 95% CI [78.1701%,88.7913%], PASS. No dataset failed or was omitted. All 201 p-values were independently recomputed from saved null statistics. These two-repeat uncorrected diagnostics do not estimate exact ten-repeat Holm power; the upper bound is an adopted operational criterion, not a theoretical power limit.

`docs/REGISTRY_VALIDATION_RESULTS.json` records `acceptance_passed: true`, all historical controls, the full report's hash and current 32/32 test outcome. The prior 100-null-dataset calibration remains 3% (passed), its file hash matches, and nine shuffled smoke analyses completed. The full Option 3 report is `results/v2/validation/power_diagnostic_option3_20261019.json`, SHA-256 `99793e1bf69909388dc6987488d1bea8f03ca33224e6c8a783a6b6c0178ff27c`; a JSONL checkpoint and all per-dataset nulls are retained.

## Freeze guards, manifests and remaining gates

The real runner checks `git status --porcelain` before reading labels and refuses unstaged/staged/unmerged/untracked changes in src/configs/tests. Only pure CRLF/LF changes verified against the index are exempt. Snapshot schema 2 uses UTF-8 text normalized solely from CRLF to LF; other whitespace, encoding and data changes fail. Both tag contents must match the same reviewed bindings.

Before documentation consolidation, the registry snapshot bound 43 artifacts with digest `da6d580818214c0a70bcd005483f101c645a97be9dac7381021194733d84f14e`. After consolidation it used 42 artifacts with digest `8d3f190541cc8edc2fea0b5eaa9d5f4884b635569aa1b621e53fc87fd2c6d9b1`. The one-owner review change then produced the current 42-artifact digest `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898`; self-check passes. It still binds the Group A feature manifest/all 19 records, implementation/tests, amendment, historical review source and integrity/class-disclosure evidence; original Group A raw byte hashes remain preserved as `source_sha256`.

All 32 tests passed after the single-review change in 22.515 seconds; the expanded suite now passes 39 tests in 26.493 seconds. Temporary synthetic Git repositories verify dirty unlisted code, staged/untracked changes, CRLF checkouts versus LF tags, stable snapshot reconstruction and content/data/owner-review tamper rejection. The actual workspace guard passed at the authorized primary-run start.

Older supplied reviews remain historical evidence for the positive-control amendment and earlier snapshots. They are not active freeze dependencies and cannot block ongoing coding.

Group A has finished and will no longer participate. Agrim is the sole project owner and the only required reviewer. R8 and registry section 13 now require one authoritative Agrim review of the exact final digest, explicitly acknowledging unresolved limitations. No AI-model, model-family, Group A or multi-review dependency remains. Review is requested only at a genuine freeze or result-changing amendment boundary.

`docs/reviews/registry_review.json` replaces the former model-family and human JSON pair. It has a minimal contract: status, reviewer, review date, artifact digest, scope and required limitation acknowledgements. `verify_freeze` reads only this one path, checks approved status/identity/date, matches its digest to the current artifact list and matches its tagged bytes. Approval, freeze commit, both tags and the execution-machine guard are now complete.

Agrim's 2026-10-20 instruction grants all outstanding approvals and authority to proceed. The single owner record now has approved status and review date 2026-10-20 for digest `57044770c2e18c0fb31929a569cbd8523946e955c06152304d3d758d3e07f898`, with the user's authorization source recorded. The scoped freeze commit/tags and one-shot primary run are authorized; the existing freeze guard must pass before the data loader runs. Statistical methods and feature content remain as reviewed.

Freeze commit `42ff54d` contains the scoped prior project work and owner approval. Both `registry-v1` and `features-v2` are annotated tags at this commit. The execution-machine guard passed on all 42 bound inputs. The first run is `results/v2/runs/primary_20261020`, launched through the frozen CLI with OPENBLAS_NUM_THREADS, MKL_NUM_THREADS and OMP_NUM_THREADS all set to one. It uses the full registered 1,000 permutations/test, five-fold/ten-repeat outer CV, five-fold inner selection and 2,000 bootstrap resamples. No inference settings were changed.

Primary source, tests, features and validation evidence have not been altered since freeze. The later sensitivity implementation uses separate new files outside the primary artifact list. The full suite and unchanged snapshot pass. Real evaluation is authorized by Agrim's instruction, not merely by synthetic acceptance.

## Separate descriptive sensitivity implementation

The sensitivity specification is now registry section 14 rather than a separate planning document. Preserve all primary subjects/features/targets and group 04/05, 11/15 and 47/49, leaving other IDs singleton: 47 groups for N=50 and 45 for N=48. Keep groups out of X and separate in both outer evaluation and inner alpha selection.

Installed scikit-learn 1.9.1 provides StratifiedGroupKFold but no RepeatedStratifiedGroupKFold. Registry section 14 specifies ten deterministic five-fold StratifiedGroupKFold repeats (seeds 42 through 51), five-fold inner StratifiedGroupKFold (seed 10042+5*r+f), the original alpha grid and fold-local scaling. Exact class balance is not guaranteed; keep fixed seeds, disclose class/group counts and duplicate split assignments, and fail rather than search seeds or change membership when required checks fail. These approved descriptive choices do not amend the primary method.

Compare grouped mean pooled-repeat OOF rho with the saved one-shot primary results, reporting signed/absolute delta and the absolute .05 descriptive flag outside Holm. No new p-values, model promotion, dependence-adjusted confidence intervals or significance claims are planned. Grouping addresses within-pair cross-fold contamination but does not resolve source identity, prove independence of other records, or validate the primary individual-level permutation exchangeability assumption. The numerical difference also reflects changed folds/training sets, not exclusively leakage bias.

`src/run_sensitivities_v2.py`, `configs/sensitivities_v2.json` and `tests/test_sensitivities_v2.py` implement all 19 descriptive analyses before primary outcomes are inspected: six grouped Ridge, six fixed RBF SVR, six fixed shallow random forest and one combined T2/T5 Ridge. They reuse strict frozen feature loading and prediction metrics. Alternative models require the same subjects and exact outer folds as their primary comparator; the combined table joins by subject ID and requires the 48-subject intersection. The grouped models use explicit Pipeline/GridSearchCV rather than changing the optimized primary engine.

Seven new synthetic tests passed, including a full 19-analysis synthetic invocation. Tests cover pair isolation at both CV levels, deterministic/complete OOF assignments, inner-fold scaling and manually checked alpha selection, unchanged matrix width (no IDs/groups added), strict ID/intersection and target consistency, matched alternative-model folds/dummy predictions, refusing an incomplete primary, preventing overwrites, preserving every primary file, and absence of inferential outputs/model promotion. The expanded full suite passes 39 tests; the 42-artifact snapshot remains unchanged.

The sensitivity runner requires a completed real primary run, the working freeze guard, matching primary digest/settings/feature hashes and a complete nine-test family. It records primary-run file hashes, its own source/config/test hashes, versions, timestamps, folds, class/group counts, OOF predictions and descriptive metrics in a separate immutable output directory. Real sensitivities have not yet run; the current primary process is left undisturbed.

## Documentation structure

Three overlapping live documents were removed after consolidation: `B2_B3_IMPLEMENTATION.md`, `FREEZE_READINESS_REVIEW.md` and `FREEZE_AND_SENSITIVITY_PLAN.md`. Current implementation state belongs here; current blockers/checklist belong in `PROGRESS.md`; statistical and sensitivity specifications belong in `ANALYSIS_REGISTRY.md`; historical events remain in the timeline. Distinct scientific audits/QC, Group A handoff/changelog, UCLH evidence, immutable review sources and machine-consumed JSON remain separate. New standalone planning documents should not be created unless they are required distinct artifacts.

## UCLH and reporting limitations

UCLH source audit on 2026-10-20 pinned upstream commit `52ad25a8cb8ecae867cd8fb9984b4fbe703585c4` and recorded SHA-256 hashes for channels, electrodes, BIDS generation, extraction code and participant TSV in the rewritten existing `UCLH_AUDIT.md`. Zenodo API checks establish `836841` as the healthy-volunteer concept DOI, `1199523` as its version-specific archive, patient archives `1199529`/`1199630`, radiology `1215676`, and processing-code release `1035910`; all checked version records return CC BY 4.0.

The independent source check confirms 32 EEG channels plus STATUS, 33 electrode entries including NFpz, 16384 Hz and common/CMS metadata. O1/O2 are absent; I1/O9 and I2/O10 cannot be substituted. Exact G8f overlap is three pairs (six channels), not the frozen eight-channel feature contract. The upstream extractor uses trigger-derived pre/post-injection portions with 2-200 Hz filtering and a 49-51 Hz stop band, and contains no explicit rereference; the 2 Hz high-pass is not equivalent to the project's 1-4 Hz delta input. The paper places CMS at NFpz and DRL at NFp2, describes about 20-minute MF/25-minute TD EIT recordings and up to a minute of EEG before/after injection, not a fixed usable-EEG duration. Unsupported old eye-block, normalized-coordinate and 60-90-second assertions were removed from both existing UCLH docs.

External NIHSS validation remains BLOCKED: the public participant TSV contains ID/age/sex/group but no NIHSS; compatible clinical-target availability, effective raw/output reference, eye condition and per-file clean epoch counts are not established. No UCLH source/config implementation, `graph_common.json` or raw BDF file was found locally. A separate clinical task cannot be substituted for NIHSS, nor can new common-montage features be inserted into the frozen Figshare model contract. No raw archive or EEG was downloaded/evaluated and no new planning document was added.

The study is pre-specified exploratory research. Small sample/no severe class, assumed lesion mapping, possible recording dependence, graph instability/residual bias and transfer mismatches remain. Report no effect detected when appropriate; neither synthetic validation nor the review establishes clinical utility or a predictive improvement.
