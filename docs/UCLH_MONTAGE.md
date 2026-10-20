> **Correction / review status (2026-10-17):** The author reports that the 33 entries comprise 32 EEG channels plus the additional NFpz electrode, with STATUS a separate trigger channel. O1/O2 are **not** present in the supplied 32-channel list: the occipital labels are I1/O9, I2/O10 and Oz. The prior O1/O2 assertions below are superseded. The repository's [BIDS generation code](https://github.com/EIT-team/Stroke_EIT_Dataset/blob/master/resource/make_EEG_BIDS.m) specifies 16384 Hz and a common reference and writes one fewer channel than electrodes. The user-provided list has not been independently checked against a raw header; the extracted segments' actual reference, usable duration and eye condition remain unverified. Do not treat I1/O9 and I2/O10 as interchangeable with O1/O2 without an explicit validated montage decision.

# UCLH Channel List and Recording Specifications

## 32-Electrode Montage (10-20 EEG System)

### Left Hemisphere Channels

| Electrode | Type | Region |
|-----------|------|--------|
| FP1 | Prefrontal | Anterior |
| F7 | Frontal | Lateral |
| F3 | Frontal | Medial |
| FC5 | Fronto-central | Lateral |
| FC1 | Fronto-central | Medial |
| T7 | Temporal | Lateral |
| C3 | Central | Medial |
| TP9 | Temporo-parietal | Lateral |
| CP5 | Centroparietal | Lateral |
| CP1 | Centroparietal | Medial |
| P7 | Parietal | Lateral |
| P3 | Parietal | Medial |
| PO3 | Parieto-occipital | Medial |
| I1/O9 | Occipital/Inion | Lateral |

### Right Hemisphere Channels

| Electrode | Type | Region |
|-----------|------|--------|
| FP2 | Prefrontal | Anterior |
| F8 | Frontal | Lateral |
| F4 | Frontal | Medial |
| FC6 | Fronto-central | Lateral |
| FC2 | Fronto-central | Medial |
| T8 | Temporal | Lateral |
| C4 | Central | Medial |
| TP10 | Temporo-parietal | Lateral |
| CP6 | Centroparietal | Lateral |
| CP2 | Centroparietal | Medial |
| P8 | Parietal | Lateral |
| P4 | Parietal | Medial |
| PO4 | Parieto-occipital | Medial |
| I2/O10 | Occipital/Inion | Lateral |

### Midline Channels

| Electrode | Type | Region |
|-----------|------|--------|
| NFpz | Frontal pole | Extra electrode entry; not in the reported 32 EEG-channel list |
| Fz | Frontal | Anterior |
| Cz | Central | Central |
| Pz | Parietal | Posterior |
| Oz | Occipital | Posterior |

### Status Channel

| Channel | Type | Purpose |
|---------|------|---------|
| STATUS | Digital trigger | Records EIT injection timing and other system triggers |

## Symmetric Left/Right Pairs (Common-Montage Comparison Set)

These are the clinically relevant symmetric pairs for comparison against Figshare montage definitions:

| Pair # | Left | Right | Region | Clinical Use |
|--------|------|-------|--------|--------------|
| 1 | F3 | F4 | Frontal | Speech, motor planning |
| 2 | C3 | C4 | Central | Sensorimotor cortex |
| 3 | P3 | P4 | Parietal | Spatial processing |
| 4 | O1 | O2 | Occipital | Absent from the reported UCLH channel list |

Note: FP1/FP2, FC1/FC2, CP1/CP2, and their lateral counterparts (FC5/FC6, CP5/CP6, etc.) are also available if required for extended comparisons.

## Recording Specifications

### Sampling and Frequency

| Parameter | Value |
|-----------|-------|
| Sampling Rate | 16384 Hz |
| EIT Frequency Range | 5 Hz – 2000 Hz (17 discrete frequencies) |
| Mains Frequency | 50 Hz |

### Acquisition Details

| Parameter | Value |
|-----------|-------|
| Current Injection Pattern | 31 pairs |
| Measurement Points per Frequency | 930 |
| Recording Duration per Run | 60–90 seconds |
| Frames per Recording | 3 |

### Reference Scheme

The BIDS-generation code describes channels with respect to a CMS common electrode and sets `EEGReference='common'`. The reference actually used in extracted EEG segments must be verified from the raw header and extraction code. Pairwise measurements used in EIT acquisition do not by themselves establish the EEG reference.

### Recording Condition

| Parameter | Value |
|-----------|------|
| State | Resting state |
| Eye Position | Eyes-open and eyes-closed blocks |
| Body Position | Supine |
| Environment | Acute hospital (HASU, UCLH) |
| Electrode Contact | EasyCap with Ag/AgCl electrodes |

### Recording Duration by Dataset Type

| Dataset Type | Identifier | Frequencies | Duration | Purpose |
|--------------|------------|-------------|----------|---------|
| Multi-Frequency | MF | 17 frequencies | ~60–90 sec per frame | Full spectrum imaging |
| Time Difference | TD | 3 frequencies | ~60–90 sec | Rapid time-series imaging |
| Z-Check | Z | Single frequency | ~30–60 sec | Contact impedance verification |

## Electrode Positioning Coordinates

All 33 electrodes (32 recording + 1 reference) have been co-registered to a standard head model (EasyCap placement on a normalized MRI template). Coordinate data (x, y, z) are available in:

- File: resource/_electrodes.tsv
- Format: Normalized Cartesian coordinates (0–1 scale)
- Material: Ag/AgCl
- Cap System: EasyCap

Example positions from the repo:
- C3: (0.179, 0.126, 0.169)
- C4: (0.074, 0.126, 0.169)
- Cz: (0.126, 0.126, 0.191)

## Comparison Against Figshare Common Montage

Current status: F3/F4, C3/C4 and P3/P4 appear in the reported channel list. O1/O2 do not; I1/O9 and I2/O10 are distinct labels and cannot be silently substituted.

Pending: Compare the corrected UCLH channel list against Group A's existing design lock and verify the extracted EEG channel names and order.

Process:
1. When A3 completes the Figshare montage audit, cross-reference those results against this list.
2. Identify any additional or non-standard pairs used in Figshare.
3. Verify the available common pairs in both datasets and resolve the missing O1/O2 pair before defining a feature contract.
4. Document any divergences or special handling in the final common-montage report.

## Notes for Group A

F3/F4, C3/C4 and P3/P4 are reported present; O1/O2 are absent from the reported UCLH list.  
✅ Electrode coordinates available: Normalized 3D positions for co-registration  
✅ Full 10-20 system implemented: Extended coverage beyond core pairs available if needed

To send to Group A immediately:
- Sampling rate: 16384 Hz
- EEG reference: BIDS code specifies common; verify extracted EEG reference.
- Channel list: See the symmetric pairs table above
- Mains: 50 Hz
- Recording duration: 60–90 seconds per run

---

Data Source:
- Channel metadata: resource/_channels.tsv, resource/_electrodes.tsv
- Acquisition settings: EITSETTINGS.json
- Reference system: BioSemi ActiveTwo with EasyCap EIT adapter

Last Updated: 2026-10-11
