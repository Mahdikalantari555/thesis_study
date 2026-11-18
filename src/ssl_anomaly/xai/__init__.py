"""RQ6 (Gap G6): Physiology-Validated Temporal XAI for Self-Supervised Crop Anomaly Detection."""

from .attribution import (
    SUGARCANE_STAGE_BINS,
    aggregate_to_sugarcane_stages,
    differentiable_cycle_score,
    integrated_gradients_attribution,
    temporal_grad_cam_attribution,
    temporal_shap_attribution,
    window_occlusion_attribution,
)
from .faithfulness import (
    deletion_insertion_auc,
    physiology_sign_concordance,
    weight_randomization_sanity_check,
)

__all__ = [
    "SUGARCANE_STAGE_BINS",
    "aggregate_to_sugarcane_stages",
    "deletion_insertion_auc",
    "differentiable_cycle_score",
    "integrated_gradients_attribution",
    "physiology_sign_concordance",
    "temporal_grad_cam_attribution",
    "temporal_shap_attribution",
    "weight_randomization_sanity_check",
    "window_occlusion_attribution",
]
