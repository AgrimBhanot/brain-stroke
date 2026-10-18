# v2 Feature Handoff Decision

**Status:** Ready for independent review; not yet tagged `features-v2`
**Date:** 2026-10-18

## Final design decision

- **Primary graph representation:** G8f, the audited 8-channel core with `N_fixed=15`.
- **Secondary sensitivity representation:** G24f, the expanded 22-channel symmetric set with `N_fixed=6`.
- **Spectral tables:** `spectral_abs.csv` and `spectral_lesion.csv` remain registered feature alternatives.
- **Excluded subjects:** `sub-13` and `sub-40` are absent from both graph tables because they do not meet the relevant fixed-epoch minimum.
- **No representation is claimed to improve prediction before the registry run.**

## Why G8f is primary

G8f uses the established clean channel core and supports 15 fixed usable epochs. G24f retains more channels but the expanded screen reduces the feasible fixed count to 6, making it less stable and more vulnerable to sampling variability. G24f is therefore retained as a secondary sensitivity analysis rather than the primary result.

## Fixed graph contract

- Bands: delta 1-4 Hz, theta 4-8 Hz, alpha 8-13 Hz, beta 13-30 Hz.
- Artifact screen: 150 uV peak-to-peak on every configured channel.
- The artifact screen is applied to the actual sampling pool before cross-spectra and subsampling.
- Subsampling: 100 draws without replacement per subject, with seed `42 + zero-based subject index`.
- Aggregation: median adjacency across subsamples.
- Metrics: absolute efficiency asymmetry, absolute clustering asymmetry, mean homotopic wPLI, and aligned normalized Frobenius distance.

## QC limitations to report

- G8f retains residual epoch-count correlations for some features, including alpha Frobenius distance (approximately -0.36).
- G24f has stronger residual epoch-count correlations for several features.
- Several graph features have second-seed stability below 0.9, especially in G24f.
- No feature was tuned or removed using NIHSS or severity labels.
- These findings are limitations to report, not reasons to select a more favorable configuration.

## Handoff contents

- `features/v2/spectral_abs.csv`
- `features/v2/spectral_lesion.csv`
- `features/v2/graph_g8f.csv`
- `features/v2/graph_g24f.csv`
- `features/v2/subject_meta.csv`
- `features/v2/MANIFEST.json`
- All feature sidecars and graph configs
- `docs/FEATURE_QC_V2.md`
- `docs/GRAPH_DESIGN_LOCK.md`
- `docs/METADATA_AUDIT.md`

## Group B boundary

Group B may use the frozen schemas and sidecars to build the registry and evaluation harness. It must not alter feature values, channel sets, epoch counts, or registered feature definitions after registry freeze. Real-label evaluation remains prohibited until the independent review, human review, registry freeze, and `features-v2` tag are complete.
