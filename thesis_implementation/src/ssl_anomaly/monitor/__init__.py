"""Causal field monitoring (train-and-finalize-main-architecture).

Submodules:
- splits: locked train/dev/test/monitoring splits with manifest hashes
- inputs: mask-aware cycle tensors, train-only robust normalization, DOY channels
- perturbations: MAD-scaled anomaly injections for the dev metric
- models: causal scorers (masked transformer, GRU-AE, B1 PhaseZ)
- scoring: causal per-bin scores, alarm rule, FAR calibration
"""

from ssl_anomaly.monitor import inputs, models, perturbations, scoring, splits

__all__ = ["inputs", "models", "perturbations", "scoring", "splits"]
