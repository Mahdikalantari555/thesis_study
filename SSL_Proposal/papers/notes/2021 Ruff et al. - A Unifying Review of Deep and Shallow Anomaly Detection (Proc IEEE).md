# 2021 Ruff et al. — A Unifying Review of Deep and Shallow Anomaly Detection

## Full citation
Ruff, L.; Kauffmann, J.R.; Vandermeulen, R.A.; Montavon, G.; Samek, W.; Kloft, M.; Dietterich, T.G.; Müller, K.-R. "A Unifying Review of Deep and Shallow Anomaly Detection." *Proceedings of the IEEE*, Vol. 109, No. 5, May 2021, pp. 756–795. DOI: 10.1109/JPROC.2021.3052449.

## Problem & setting
- Review/tutorial paper (not a single experiment): organizes the entire anomaly detection (AD) field — classic "shallow" methods (PCA, OC-SVM, SVDD, KDE, k-NN, LOF, isolation forest) and deep methods (AEs, deep one-class classification, deep generative models, self-supervised AD) — into one framework of components: **feature map φ, model/loss, regularization, inference mode**.
- Motivating setting: mostly **unsupervised AD** where labeled anomalies are absent/insufficient; anomalies diverse and rare; normality concept must be learned from (possibly contaminated) unlabeled data.

## Method (taxonomy and precise objectives)
- Formalizes AD as **density level-set estimation**: A = {x | p+(x) ≤ τ}; concentration (cluster) assumption: normal data concentrates in a bounded high-density region, anomalies do not.
- Anomaly taxonomy: point, contextual/conditional, group/collective, plus the deep-learning-relevant split of **low-level sensory vs. high-level semantic anomalies** — semantic anomalies can be closer to normal data in raw pixel space than normal-class variants are to each other, so detecting them requires semantic feature representations.
- **Deep SVDD objective** (one-class deep classification): min over ω, c of (1/n) Σᵢ ‖φω(xᵢ) − c‖² (+R); collapse prevention via reconstruction terms, architectural constraints (no unbounded/biased activations, no pooling), frozen embeddings, auxiliary negatives, or variance penalties.
- **Self-supervised AD** reviewed: train multiclass classifiers on pseudo-labels from geometric transformations (rotations/flips/translations; GOAD uses random affine transformations); anomaly score from softmax prediction uncertainty (near-uniform ⇒ anomaly). Also notes contrastive self-supervision as promising for AD.
- Deep generative models (VAE, flows, GANs) reviewed; flags the **Nalisnick et al. "typical set" failure**: DGM likelihoods biased toward low-level background statistics, can assign higher likelihood to OOD samples — a key caution for reconstruction/density-based AD.
- Empirical assessment (MNIST/CIFAR-style k-classes-out benchmarks, tables with AUROC) enriched with explainability (layer-wise relevance propagation-style relevance maps) so one can see *why* a point is anomalous.

## Data & labels
- Benchmark-style experiments on image AD benchmarks (MNIST, Fashion-MNIST, CIFAR-10, GTSRB); toy 2-D examples (moons); n unlabelled training samples, labels only used for evaluation and (in DSAD) a few labeled anomalies.

## Results (key empirical findings)
- Deep one-class (DOCC/Deep SVDD) beats shallow baselines on complex image benchmarks; on simple structured data shallow methods remain competitive.
- Self-supervised (geometric transformation) AD shows "significant performance improvements" on k-classes-out benchmarks over vanilla Deep SVDD.
- XAI-based relevance analysis shows deep detectors often latch onto background/low-level statistics — motivating explicit explainability checks before deployment.

## What transfers to our thesis
- Frame label-free sugarcane stress detection as **one-class / level-set estimation on SSL-learned embeddings of Landsat time series**, not as supervised classification — the concentration assumption maps to "healthy fields concentrate, stress is diverse."
- The **contextual/group anomaly taxonomy** fits our problem: stress is a *contextual* anomaly (a parcel anomalous for its date, soil, and phenological stage) and often a *collective* anomaly (a sub-series), so the detector should be conditioned on context (season, crop stage) rather than use global thresholds.
- **Low-level vs. semantic anomaly distinction** is a design warning: pixel/reconstruction-based detectors on Landsat tiles may only catch low-level anomalies (clouds, missing data) while water/salinity stress is semantic — argues for SSL representations (masked temporal modeling, contrastive) + one-class head, as in Deep SAD/DOCC lineage.
- Softmax-uncertainty / transformation-classification AD (rotation prediction) could be a cheap pretext on 16-day NDVI/LST stacks; but their caveat that self-supervision may learn mainly low-level statistics supports pairing it with temporal pretext tasks.
- Deep SVDD's collapse-avoidance tricks (no biased activations/pooling, whiten the embedding) are directly reusable for a lightweight per-field stress scorer.

## Limitations / caveats
- 2021 review: predates masked-image-modeling AD, modern foundation-model era, and satellite time-series SSL; benchmarks are natural images, not remote sensing.
- Authors' own bias acknowledged (Deep SVDD lineage).
- Does not address nonstationarity of "normal" across years/sensors beyond discussion — a core issue for cross-year Landsat models.

## Key numbers to quote in lit review
- Published in Proc. IEEE vol. 109, no. 5 (2021); DOI 10.1109/JPROC.2021.3052449 — the standard citation for unifying shallow+deep AD.
- Self-supervised geometric-transformation AD gives "significant performance improvements" over vanilla Deep SVDD on k-classes-out image benchmarks (e.g., MNIST-family AUROC gains reported in their Table 3).
- DGM likelihood failure: models trained on Fashion-MNIST systematically assign *higher* likelihood to MNIST digits (Nalisnick et al.) — caution against pure-likelihood AD.
- Anomaly score hierarchy: point vs. contextual vs. collective anomalies — the formal vocabulary for stress-as-contextual-anomaly framing.
