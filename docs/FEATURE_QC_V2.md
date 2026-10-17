# v2 Graph Feature QC

All checks below are label-free.

## g8f

- Rows: 48; features: 16.
- Finite values: True.
- Banned label/count column names: none.
- Constant features: none.

### Feature ranges

- `g8f_alpha_ClustCoeff_absAI`: min=0.000141762, max=0.155324
- `g8f_alpha_FrobeniusDist`: min=0.0242602, max=0.211901
- `g8f_alpha_GlobalEff_absAI`: min=0.000211714, max=0.133991
- `g8f_alpha_MeanHomotopic`: min=0.283466, max=0.412856
- `g8f_beta_ClustCoeff_absAI`: min=0.000651039, max=0.0714665
- `g8f_beta_FrobeniusDist`: min=0.0105658, max=0.113897
- `g8f_beta_GlobalEff_absAI`: min=0.000641991, max=0.062792
- `g8f_beta_MeanHomotopic`: min=0.282442, max=0.34757
- `g8f_delta_ClustCoeff_absAI`: min=0.000913633, max=0.188661
- `g8f_delta_FrobeniusDist`: min=0.0385722, max=0.212639
- `g8f_delta_GlobalEff_absAI`: min=0.000662256, max=0.17429
- `g8f_delta_MeanHomotopic`: min=0.26837, max=0.444593
- `g8f_theta_ClustCoeff_absAI`: min=0.000173179, max=0.279371
- `g8f_theta_FrobeniusDist`: min=0.0275, max=0.232422
- `g8f_theta_GlobalEff_absAI`: min=9.94847e-05, max=0.126793
- `g8f_theta_MeanHomotopic`: min=0.275474, max=0.433335

### Epoch-count bias

- `g8f_alpha_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=-0.212877
- `g8f_alpha_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.359296
- `g8f_alpha_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.255843
- `g8f_alpha_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.303608
- `g8f_beta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=-0.110149
- `g8f_beta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.14229
- `g8f_beta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=0.123932
- `g8f_beta_MeanHomotopic` vs `n_epochs_all`: Spearman r=0.0603756
- `g8f_delta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=-0.0884988
- `g8f_delta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.070308
- `g8f_delta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.044082
- `g8f_delta_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.104179
- `g8f_theta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=-0.141286
- `g8f_theta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.208636
- `g8f_theta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.273755
- `g8f_theta_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.175379

### Collinearity

- Pairs with |r| > 0.95: none

### Second-seed stability

- Alternate seed base: 1042.
- `g8f_alpha_ClustCoeff_absAI` between seed runs: Spearman r=0.774859
- `g8f_alpha_FrobeniusDist` between seed runs: Spearman r=0.972102
- `g8f_alpha_GlobalEff_absAI` between seed runs: Spearman r=0.892749
- `g8f_alpha_MeanHomotopic` between seed runs: Spearman r=0.979483
- `g8f_beta_ClustCoeff_absAI` between seed runs: Spearman r=0.794073
- `g8f_beta_FrobeniusDist` between seed runs: Spearman r=0.886018
- `g8f_beta_GlobalEff_absAI` between seed runs: Spearman r=0.910334
- `g8f_beta_MeanHomotopic` between seed runs: Spearman r=0.92944
- `g8f_delta_ClustCoeff_absAI` between seed runs: Spearman r=0.848784
- `g8f_delta_FrobeniusDist` between seed runs: Spearman r=0.87614
- `g8f_delta_GlobalEff_absAI` between seed runs: Spearman r=0.827508
- `g8f_delta_MeanHomotopic` between seed runs: Spearman r=0.965371
- `g8f_theta_ClustCoeff_absAI` between seed runs: Spearman r=0.721884
- `g8f_theta_FrobeniusDist` between seed runs: Spearman r=0.918693
- `g8f_theta_GlobalEff_absAI` between seed runs: Spearman r=0.910877
- `g8f_theta_MeanHomotopic` between seed runs: Spearman r=0.948545

## g24f

- Rows: 48; features: 16.
- Finite values: True.
- Banned label/count column names: none.
- Constant features: none.

### Feature ranges

- `g24f_alpha_ClustCoeff_absAI`: min=0.000107173, max=0.0764353
- `g24f_alpha_FrobeniusDist`: min=0.018048, max=0.0669434
- `g24f_alpha_GlobalEff_absAI`: min=4.82045e-05, max=0.0603336
- `g24f_alpha_MeanHomotopic`: min=0.454903, max=0.54895
- `g24f_beta_ClustCoeff_absAI`: min=0.000349047, max=0.06518
- `g24f_beta_FrobeniusDist`: min=0.0100485, max=0.0421252
- `g24f_beta_GlobalEff_absAI`: min=8.13198e-05, max=0.0354054
- `g24f_beta_MeanHomotopic`: min=0.452749, max=0.49209
- `g24f_delta_ClustCoeff_absAI`: min=0.00276983, max=0.135403
- `g24f_delta_FrobeniusDist`: min=0.0205191, max=0.106713
- `g24f_delta_GlobalEff_absAI`: min=0.000313787, max=0.0522364
- `g24f_delta_MeanHomotopic`: min=0.453795, max=0.545288
- `g24f_theta_ClustCoeff_absAI`: min=0.000880918, max=0.163183
- `g24f_theta_FrobeniusDist`: min=0.0187242, max=0.0733456
- `g24f_theta_GlobalEff_absAI`: min=0.000753174, max=0.0325522
- `g24f_theta_MeanHomotopic`: min=0.444204, max=0.539777

### Epoch-count bias

- `g24f_alpha_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=-0.209697
- `g24f_alpha_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.438365
- `g24f_alpha_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.0603756
- `g24f_alpha_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.402765
- `g24f_beta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=0.0880524
- `g24f_beta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.120249
- `g24f_beta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.0075888
- `g24f_beta_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.0400644
- `g24f_delta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=0.0177444
- `g24f_delta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.156575
- `g24f_delta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=0.183973
- `g24f_delta_MeanHomotopic` vs `n_epochs_all`: Spearman r=0.0249426
- `g24f_theta_ClustCoeff_absAI` vs `n_epochs_all`: Spearman r=0.163271
- `g24f_theta_FrobeniusDist` vs `n_epochs_all`: Spearman r=-0.409237
- `g24f_theta_GlobalEff_absAI` vs `n_epochs_all`: Spearman r=-0.173092
- `g24f_theta_MeanHomotopic` vs `n_epochs_all`: Spearman r=-0.32325

### Collinearity

- Pairs with |r| > 0.95: none

### Second-seed stability

- Alternate seed base: 1042.
- `g24f_alpha_ClustCoeff_absAI` between seed runs: Spearman r=0.693552
- `g24f_alpha_FrobeniusDist` between seed runs: Spearman r=0.827073
- `g24f_alpha_GlobalEff_absAI` between seed runs: Spearman r=0.646548
- `g24f_alpha_MeanHomotopic` between seed runs: Spearman r=0.889275
- `g24f_beta_ClustCoeff_absAI` between seed runs: Spearman r=0.752388
- `g24f_beta_FrobeniusDist` between seed runs: Spearman r=0.899262
- `g24f_beta_GlobalEff_absAI` between seed runs: Spearman r=0.655124
- `g24f_beta_MeanHomotopic` between seed runs: Spearman r=0.895462
- `g24f_delta_ClustCoeff_absAI` between seed runs: Spearman r=0.648285
- `g24f_delta_FrobeniusDist` between seed runs: Spearman r=0.850304
- `g24f_delta_GlobalEff_absAI` between seed runs: Spearman r=0.754451
- `g24f_delta_MeanHomotopic` between seed runs: Spearman r=0.924446
- `g24f_theta_ClustCoeff_absAI` between seed runs: Spearman r=0.563938
- `g24f_theta_FrobeniusDist` between seed runs: Spearman r=0.835215
- `g24f_theta_GlobalEff_absAI` between seed runs: Spearman r=0.715154
- `g24f_theta_MeanHomotopic` between seed runs: Spearman r=0.820343
<!-- End of label-free QC report. -->

