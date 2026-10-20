> **Review status: PARTIAL / UNVERIFIED (2026-10-17).** The author corrected the montage: 32 EEG channels plus STATUS and 33 electrode entries including NFpz; the claimed O1/O2 channels are absent from the supplied list. The [BIDS generation code](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/master/resource/make_EEG_BIDS.m) states 16384 Hz and a common reference; the effective reference and usable segment duration still require raw-header and extraction-code verification. The [dataset repository](https://github.com/EIT-team/Stroke_EIT_Dataset) describes EEG extraction from intervals before and after EIT injection. The handoff and Group A's implementation are user-reported; the implementation has not been verified here. EIT reference/duration claims below must not be taken as verified EEG specifications.

# UCLH Stroke EIT Dataset Audit

## Dataset Identity

| Field | Value |
|-------|-------|
| Repository | EIT-team/Stroke_EIT_Dataset |
| Primary DOI | 10.5281/zenodo.836841 |
| Zenodo Record | https://zenodo.org/record/836841 |
| GitHub Repository | https://github.com/EIT-team/Stroke_EIT_Dataset |
| License | CC BY 4.0 (Creative Commons Attribution 4.0 International) |

## Full Citation

James Avery, Nir Goren, Eleanor Mackle, Thomas Dowrick, Anna Witkowska-Wrobel, and David Holder. (2017). The UCLH Stroke EIT Dataset. Zenodo. https://doi.org/10.5281/zenodo.836841

## Associated Publication

Goren, N., Avery, J., Dowrick, T., Mackle, E., Witkowska-Wrobel, A., Werring, D., & Holder, D. (2018). Multi-frequency electrical impedance tomography and neuroimaging data in stroke patients. Scientific Data, 5, 180112. https://doi.org/10.1038/sdata.2018.112

## License Details

The dataset is distributed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. This permits:
- Redistribution and reuse of the dataset
- Commercial and non-commercial use
- Adaptation and modification

Required attribution: credit must be given to the creators (Avery, Goren, Mackle, Dowrick, Witkowska-Wrobel, Holder).

## Dataset Composition

### Data Types
- Raw BioSemi BDF (.bdf) recordings
- Processed MATLAB (.mat) files
- JSON format data
- Anonymised CT/MRI radiology reports and scans

### Population
- 23 acute stroke patients
- 10 healthy volunteers (controls)

### Clinical Context
- Collected in collaboration with the Hyper Acute Stroke Unit (HASU) at University College London Hospital (UCLH)
- Stroke patient data includes neuroimaging and radiological assessments

### EIT System
- Hardware: UCL ScouseTom System (32-electrode scalp montage)
- Electrode Arrangement: 10-20 EEG system positions
- Injection Protocol: 31-pair current injection protocol
- Measurement Points: 930 measurements per frequency (31 injections × 30 voltage measurements per injection)

### Acquisition Parameters
- Frequencies: 17 discrete frequencies: 5, 10, 20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1350, 1700, 2000 Hz
- Sampling Rate: 16384 Hz (digitization of electrode signals)
- Mains Frequency: 50 Hz (UK environment)
- Recording Duration: Approximately 60–90 seconds per EIT acquisition run
- Reference Scheme: Differential pairwise voltage recordings using the standard EIT injection protocol

### Recording Conditions
- State: Resting state; eyes-open and eyes-closed states
- Body Position: Supine (recumbent, on back)
- Clinical Setting: Acute hospital environment (HASU at UCLH)

## Data Structure

### Zenodo Archive Parts
The raw dataset is distributed across multiple Zenodo records due to size constraints (~150 GB total):

| Content | DOI | Zenodo Record | Notes |
|---------|-----|---------------|-------|
| Subject data | 10.5281/zenodo.1199523 | 1199523 | Healthy volunteers |
| Patient data (Part 1) | 10.5281/zenodo.1199529 | 1199529 | Stroke patients |
| Patient data (Part 2) | 10.5281/zenodo.1199630 | 1199630 | Stroke patients |
| Radiology data | 10.5281/zenodo.1215676 | 1215676 | CT/MRI scans & reports |

### Repository Structure

```text
Stroke_EIT_Dataset/
├── UCL_Stroke_EIT_Dataset.mat         # Processed MATLAB dataset
├── EITDATA.json                       # Processed data in JSON format
├── EITSETTINGS.json                   # Acquisition settings
├── Subjects/                          # Healthy volunteer raw data
├── Patients/                          # Stroke patient raw data
├── Anonymised_Radiology/              # CT/MRI scans and reports
├── resource/                          # Processing scripts and reference data
└── docs/                              # Documentation
```
