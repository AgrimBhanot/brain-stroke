# Paired-recording integrity audit

**Date:** 2026-10-19. **Scope:** the user-authorized label-blind investigation of sub-04/05, sub-11/15 and sub-47/49. The separate sub-13/40 class disclosure is in `FEATURE_QC_V2.md`.

## Method and reproducibility

Run `python -B src/audit_recording_integrity_v2.py` using `configs/recording_integrity_v2.json`. The script reads only participant ID, age, sex, stroke location, onset duration and handedness from the source participant TSV and stored subject metadata. It does not load either clinical outcome column into the audit frames. Raw-file SHA-256 values, metadata hashes, software version, source/config hashes and every channel comparison are saved in `RECORDING_INTEGRITY_AUDIT_V2.json`.

All six raw EDFs have the same 33 channel names/order, 160,000 samples per channel and a sampling rate of 500 Hz. MNE-decoded values were compared at every sample on every recorded channel, with no tolerance, filtering, resampling, time-shift search or channel exclusion. Whole-file checksums were compared separately. The 33 channels consist of 30 scalp labels, HEOL, HEOR and one empty channel label; the unnamed channel's role was not inferred. CPz is constant in the compared records, so its correlation is undefined and is reported as null rather than as evidence of similarity.

## Signal findings

| Pair | Exactly equal channels | All 33 channels equal? | Whole-file SHA-256 equal? |
|---|---|---|---|
| sub-04 / sub-05 | All 32 named channels; only the unnamed channel differs | No | No |
| sub-11 / sub-15 | CPz only; other channels differ sample by sample | No | No |
| sub-47 / sub-49 | CPz only; other channels differ sample by sample | No | No |

The prior eight-core-channel identity for sub-04/05 is confirmed and extends to every named scalp/EOG signal. A difference in the unnamed channel and different file hashes do not remove the concern about identical named EEG signals. The other pairs retain very high named-channel correlations but are not exactly identical recordings. Per-channel correlations, equality counts and maximum absolute differences are in the JSON evidence.

## Non-outcome metadata findings

| Pair | Ages | Sex | Stroke locations | Other differences |
|---|---|---|---|---|
| 04 / 05 | 56 / 44 | male / female | Left frontal parietal cortex, Left centrum semiovale / Left pons | Duration 14 / 4; both right-handed |
| 11 / 15 | 31 / 63 | both male | Right paraventricular / Right fronto-parietal temporo-occipital lobe, Right inner watershed | Duration 7 / 1; right / left handedness |
| 47 / 49 | 40 / 52 | both male | Right medulla oblongata / Right basal ganglia | Duration 4 / 3; both right-handed |

All five audited metadata fields for all six IDs match the source TSV and stored `subject_meta.csv` after whitespace/case normalization. Thus the within-pair disagreements are present in the source metadata; they are not a local subject-meta transcription discrepancy. Source duration units are not newly inferred here.

## Interpretation and handoff

The checks are complete, but they do not resolve the origin of identical/near-identical signals under differing demographic/clinical records or establish participant identity. Retain the user's existing separate-ID/subject-split decision and disclose the potential dependence in both CV and permutation inference. Reviewers must explicitly assess this strengthened evidence before sign-off. Source-author clarification is a possible follow-up; no external contact or cohort change was made in this task.
