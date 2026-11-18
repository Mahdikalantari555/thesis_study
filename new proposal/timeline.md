# Research Timeline — New Proposal

**Topic:** Crop Stress Detection in Sugarcane Fields Using Satellite Image Time Series  
**Duration:** 18 weeks (4.5 months)

---

## Phase 1: Data Pipeline (Weeks 1–4)

| Week | Task | Deliverable |
|------|------|-------------|
| 1 | Download Landsat 7/8/9 L2 collection; verify coverage | Raw data inventory |
| 2 | Cloud masking (CFMASK); 16-day compositing | Clean composites |
| 3 | Gap-filling (STRFM); raw bands + LST + indices | Feature-ready dataset |
| 4 | Quality control; verify valid dates and temporal distribution | QC report |

## Phase 2: SSL Pre-training (Weeks 5–8)

| Week | Task | Deliverable |
|------|------|-------------|
| 5 | Implement CNN-Mamba architecture (reimplement from paper) | Model code |
| 6 | Barlow Twins pre-training on unlabeled archive | Pre-trained weights |
| 7 | Pilot: verify reconstruction + embedding quality | Pilot report |
| 8 | Hyperparameter tuning; augmentation selection | Tuned model |

## Phase 3: Fine-tuning + XAI (Weeks 9–14)

| Week | Task | Deliverable |
|------|------|-------------|
| 9 | Expert labeling campaign (50–100 fields) | Labeled dataset |
| 10 | Fine-tune on 4 stress classes | Trained classifier |
| 11 | Baseline comparison (RF/XGBoost on indices; 3D-CAE; LSTM/Transformer) | Baseline table |
| 12 | Temporal SHAP + Grad-CAM implementation | XAI outputs |
| 13 | Physiological validation of explanations | Validation report |
| 14 | Cross-year validation; uncertainty reporting | Final evaluation |

## Phase 4: Writing (Weeks 15–18)

| Week | Task | Deliverable |
|------|------|-------------|
| 15 | Draft proposal sections | Proposal v1 |
| 16 | Revise based on advisor feedback | Proposal v2 |
| 17 | Finalize proposal + references | Final proposal |
| 18 | Export to Word-ready format | Submission package |

---

## Key Milestones

- **Week 4:** Data pipeline complete and verified
- **Week 8:** SSL pre-training validated
- **Week 14:** Full evaluation complete
- **Week 18:** Proposal ready for submission
