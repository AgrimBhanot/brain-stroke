# UCLH Stroke EIT Dataset Audit

**Updated:** 2026-10-20. **Status:** source-level audit completed; external NIHSS validation remains BLOCKED. No UCLH raw signal was downloaded or evaluated.

## Identity, licence and citation

The earlier document incorrectly called `10.5281/zenodo.836841` the whole dataset DOI. Zenodo's API resolves it to the healthy-volunteer archive's concept record.

| Content | Version-specific DOI | Concept DOI |
|---|---|---|
| Processing repository initial release | [10.5281/zenodo.1035910](https://zenodo.org/records/1035910) | 10.5281/zenodo.1035909 |
| Healthy-volunteer archives | [10.5281/zenodo.1199523](https://zenodo.org/records/1199523) | 10.5281/zenodo.836841 |
| Patient archives, part 1 | [10.5281/zenodo.1199529](https://zenodo.org/records/1199529) | 10.5281/zenodo.838175 |
| Patient archives, part 2 | [10.5281/zenodo.1199630](https://zenodo.org/records/1199630) | 10.5281/zenodo.838183 |
| Radiology | [10.5281/zenodo.1215676](https://zenodo.org/records/1215676) | 10.5281/zenodo.838704 |

All five version-specific records returned `cc-by-4.0` from the Zenodo API on 2026-10-20. Cite the actual archive used and: Goren, N., Avery, J., Dowrick, T., Mackle, E., Witkowska-Wrobel, A., Werring, D., & Holder, D. (2018). *Multi-frequency electrical impedance tomography and neuroimaging data in stroke patients*. Scientific Data, 5, 180112. [doi:10.1038/sdata.2018.112](https://doi.org/10.1038/sdata.2018.112).

The paper reports 23 patients and ten volunteers, including ten ischaemic, eight haemorrhagic and five other patient classifications. These are not verified usable EEG/NIHSS cohort counts. Repeated A/B visits are not independent people. MF acquisition spans approximately 20 minutes for three frames; TD spans 25 minutes for 60 frames. These are EIT durations. The described pre/post-injection EEG can last up to a minute on each side, but usable duration requires per-file verification. [Publication](https://www.nature.com/articles/sdata2018112)

## Pinned source evidence

Inspected [repository commit `52ad25a8cb8ecae867cd8fb9984b4fbe703585c4`](https://github.com/EIT-team/Stroke_EIT_Dataset/tree/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4), dated 2021-11-01. Remote raw bytes were read and SHA-256 hashed on 2026-10-20.

| Source path | SHA-256 |
|---|---|
| `resource/_channels.tsv` | `d85c470cb0c8b78beb452e2358ed2c5b1aca13f7bcffc6e9f9764d9605f5d792` |
| `resource/_electrodes.tsv` | `98062e641892c418439c493749da614da346eff40921d2b7fc7cea2cf41e7e69` |
| `resource/make_EEG_BIDS.m` | `5367a981b6048ad0f17df43a64913c407ee7fb31e05ac326cb995404ae4fffd2` |
| `src/Extract_EEG.m` | `130148b1e0c677f4743a00c271026a41743014b0b8f36b82304cca7d9f43d152` |
| `Patients/participants.tsv` | `bb60d5d12a1108f1a45dcd2de13e21dc63cdf2cf3917b7a1fa24f2247c12cfce` |

The [participant table](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/Patients/participants.tsv) has participant ID, age, sex and group columns, not NIHSS. The [patient README](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/Patients/readme.md) documents visits, diagnoses and exclusions. Neither subtype, lesion size nor healthy/patient status can substitute for the Figshare NIHSS target.

## EEG extraction implications

The pinned [Extract_EEG.m](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/52ad25a8cb8ecae867cd8fb9984b4fbe703585c4/src/Extract_EEG.m) uses header/trigger-derived boundaries, trims before/after injection, then applies second-order 2-200 Hz Butterworth filtering and a 49-51 Hz stop band with forward/backward filtering. It contains no explicit rereferencing operation. This verifies code behavior, not per-file duration, calibration or effective reference through all loader stages.

**Project implication:** this 2 Hz high-pass is not equivalent to the frozen 1-4 Hz delta-band input. A compatible raw-EEG workflow must explicitly define filtering/transient removal, units, trigger exclusion, reference and resampling. EIT impedance matrices are not EEG features.

## Remaining prerequisites

1. Establish a versioned, patient/visit-linked compatible clinical target. Public NIHSS availability is not established; without it, UCLH cannot validate NIHSS prediction. A different target needs a separate explicit protocol.
2. Acquire a scoped raw BDF sample and loader/trigger dependencies. Verify header channels/order, units, sampling rate, record duration, injection boundaries, effective reference and clean seconds/epochs. Eye condition remains unverified.
3. Define compatible preprocessing and a common montage before transfer. O1/O2 are absent; see [UCLH_MONTAGE.md](UCLH_MONTAGE.md). No local UCLH source/config implementation, `graph_common.json` or BDF file was found in the 2026-10-20 inventory.
4. Keep new common-montage artifacts separate from frozen Figshare feature/model contracts.

Group A's implementation claim remains user-reported. Unsupported 60-90-second EEG, eyes-open/closed-block and montage assertions have been removed, not accepted as facts. Source-level verification is not completed external validation.
