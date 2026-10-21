# UCLH Channel List and Recording Specifications

**Updated:** 2026-10-20. Source list independently verified; raw-header/usable-EEG audit pending. Pinned commit and byte hashes are in [UCLH_AUDIT.md](UCLH_AUDIT.md).

## Recorded channels versus electrodes

Sources: [channels](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/resource/_channels.tsv) and [electrodes](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/resource/_electrodes.tsv).

| Set | Names in source spelling | Count |
|---|---|---:|
| Left EEG | FP1, F7, F3, FC5, FC1, T7, C3, TP9, CP5, CP1, P7, P3, PO3, I1/O9 | 14 |
| Right EEG | FP2, F8, F4, FC6, FC2, T8, C4, TP10, CP6, CP2, P8, P4, PO4, I2/O10 | 14 |
| Midline EEG | Fz, CZ, Pz, Oz | 4 |
| Trigger | STATUS | 1 |
| Extra electrode entry, not a sampled EEG channel | NFpz | 1 |

Thus channels.tsv contains 32 EEG/EIT rows plus STATUS; electrodes.tsv contains 33 entries including NFpz. Preserve source spelling/order in provenance and document any CZ-to-Cz normalization. STATUS must not enter X.

Exact source EEG order:

```text
FP2 FP1 F8 F4 Fz F3 F7 FC6 FC2 FC1 FC5 T8 C4 CZ C3 T7
TP10 CP6 CP2 CP1 CP5 TP9 P4 Pz P3 P8 PO4 PO3 P7 I2/O10 I1/O9 Oz
```

O1/O2 are absent. I1/O9 and I2/O10 are distinct labels, not authorized replacements.

## Comparison with the actual Figshare configs

| Contract | Exact matching pairs | Missing / unresolved |
|---|---|---|
| G8f, four pairs | F3/F4, C3/C4, P3/P4 | O1/O2 absent |
| G24f, eleven pairs | F3/F4, F7/F8, C3/C4, P3/P4 | FC3/FC4, FT7/FT8, CP3/CP4, TP7/TP8, O1/O2 lack exact matches |
| G24f temporal labels | T3/T4 and T5/T6 do not appear literally | T7/T8 and P7/P8 are candidate nomenclature mappings; validate/document geometry and mapping before use |

Local sources: `configs/graph_g8f.json` and `configs/graph_g24f.json`. G24f actually contains 22 channels/11 pairs despite its historical name.

Three shared core pairs establish a six-channel intersection, not compatibility with the existing eight-channel graph model. Changing nodes changes feature meaning. Common-montage features/refitting need a separate explicit contract; do not fill missing electrodes or rename distinct locations to make a frozen model load.

## Recording specifications

| Field | Source-level evidence | Still required |
|---|---|---|
| Sampling | 16384 Hz in channel rows/BIDS code | Verify raw header and extraction output |
| Hardware | BioSemi ActiveTwo, EasyCap | Confirm calibration/units and selected channels |
| Mains | 50 Hz; extractor uses a 49-51 Hz stop band | Record applied preprocessing |
| Reference | BIDS code describes CMS/common | Check loader/output reference and any project rereferencing |
| State | BIDS task is rest | Eye condition and usable resting intervals unverified |
| Duration | Trigger-delimited pre/post-injection EEG | Measure clean seconds/epochs; no blanket 60-90-second assumption |
| Extraction | 2-200 Hz bandpass plus notch | Not equivalent to Figshare's 1-4 Hz delta-band input |

Sources: [BIDS-generation code](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/resource/make_EEG_BIDS.m), [EEG extractor](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/src/Extract_EEG.m).

The publication locates CMS at NFpz and the additional driven-right-leg electrode at NFp2. The TSV is not a complete count of acquisition hardware contacts. It provides nominal Cartesian positions; the unsupported assertion of normalized 0-1 coordinates is withdrawn. [Publication](https://www.nature.com/articles/sdata2018112)

## Operational handoff

Agrim owns further work; no response from Group A is required. Source-level channel/reference metadata are established, but common-montage implementation, compatible clinical targets and raw-EEG QC remain prerequisites. External validation has not run.
