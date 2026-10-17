# Figshare Metadata Audit (v2 A0)

**Audit date:** 2026-10-17
**Status:** READY FOR A2

## Search result

The repository was searched recursively for `participants.tsv`, participant TSV files, and clinical TSV files.

- `data\raw\figshare\participants.tsv`

The raw participant table provides `ParalysisSide`, `StrokeLocation`, `Gender`, `Age`, `Duration`, and `Handedness`.
The companion metadata description is `data\raw\figshare\participants.json`. It defines `ParalysisSide` as the side of limb paralysis due to stroke.
The v2 rule maps paralysis side to contralateral lesion side. This mapping is recorded as provenance and is not inferred from NIHSS or severity.
Exact raw participant columns: `Participant_ID`, `Gender`, `Age`, `Duration`, `ParalysisSide`, `Handedness`, `IsFirstTime`, `StrokeLocation`, `NIHSS`, `MBI`, `mRS`.

## Counts

Mapped lesion-side counts: left=22, right=28, NA=0.
Severity cross-tab (descriptive only; not used for feature design):
- left: mild=14, moderate=8
- right: mild=19, moderate=9
- NA: mild=0, moderate=0

## Decision

Lesion alignment feasibility rule: at least 10 clear left and 10 clear right cases. Feasible=True.
A2/T3 may proceed only if the feasibility result is true. Subjects with non-lateral or missing paralysis side remain `NA`.

## Subject metadata scaffold

The scaffold contains 50 subjects copied from `features/figshare_features.csv` for handoff bookkeeping. `n_epochs_g8f` and `n_epochs_g24f` remain empty until the v2 graph pipeline runs.

## Next feasible work

A2 may proceed from this metadata audit. The label-blind A3 channel/epoch audit may also proceed now that processed epoch FIFs are available.
