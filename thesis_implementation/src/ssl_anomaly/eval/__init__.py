"""Evaluation: CV splits, synthetic injection, cloud robustness, lead time, validation gate, probing, contamination."""

from __future__ import annotations

from .cloud_robustness import (
    COMPLETENESS_LEVELS,
    evaluate_e_align_three_metrics,
    evaluate_e_norm_trimming_stability,
    run_cloud_completeness_benchmark,
    subsample_cloud_completeness,
)
from .contamination import (
    CONTAMINATION_RATES,
    analyze_false_alarm_confounders,
    run_contamination_sweep,
)
from .cv import (
    cluster_field_ci,
    compare_detectors_wilcoxon_holm,
    generate_splits_dict,
    save_splits_json,
    simulate_490_field_archive,
)
from .data_scarcity import (
    DEFAULT_FEW_SHOT_FRACTIONS,
    DEFAULT_FRACTIONS,
    alignment_uniformity,
    effective_rank,
    embedding_quality_report,
    few_shot_probe,
    learning_curve,
    mean_cosine_similarity,
    summarize_train_val_history,
    tsne_projection,
)
from .early_detection import (
    EIGENCL_REFERENCE_LEAD_DAYS,
    run_loyo_early_detection,
    simulate_progressive_onset_archive,
)
from .probing import (
    extract_frozen_embeddings,
    probe_binary_target,
    probe_continuous_targets,
    run_rq7_probing_suite,
)
from .real_archive import (
    add_source_argument,
    build_provenance,
    get_archive_provenance,
    load_real490_archive,
    require_real_archive,
    resolve_archive,
    simulated_output_path,
)
from .stats import (
    bootstrap_ci,
    holm_correction,
    paired_wilcoxon,
    spearman_correlation,
)
from .synthetic import (
    InjectionConfig,
    inject_anomaly,
    synthetic_benchmark,
)
from .validation_gate import (
    build_expert_event_review_packet,
    evaluate_stress_validation_gate,
)

__all__ = [
    "COMPLETENESS_LEVELS",
    "CONTAMINATION_RATES",
    "DEFAULT_FEW_SHOT_FRACTIONS",
    "DEFAULT_FRACTIONS",
    "EIGENCL_REFERENCE_LEAD_DAYS",
    "InjectionConfig",
    "add_source_argument",
    "alignment_uniformity",
    "analyze_false_alarm_confounders",
    "bootstrap_ci",
    "build_expert_event_review_packet",
    "build_provenance",
    "cluster_field_ci",
    "compare_detectors_wilcoxon_holm",
    "effective_rank",
    "embedding_quality_report",
    "evaluate_e_align_three_metrics",
    "evaluate_e_norm_trimming_stability",
    "evaluate_stress_validation_gate",
    "extract_frozen_embeddings",
    "few_shot_probe",
    "generate_splits_dict",
    "get_archive_provenance",
    "holm_correction",
    "inject_anomaly",
    "learning_curve",
    "load_real490_archive",
    "mean_cosine_similarity",
    "paired_wilcoxon",
    "probe_binary_target",
    "probe_continuous_targets",
    "require_real_archive",
    "resolve_archive",
    "run_cloud_completeness_benchmark",
    "run_contamination_sweep",
    "run_loyo_early_detection",
    "run_rq7_probing_suite",
    "save_splits_json",
    "simulate_490_field_archive",
    "simulate_progressive_onset_archive",
    "simulated_output_path",
    "spearman_correlation",
    "subsample_cloud_completeness",
    "summarize_train_val_history",
    "synthetic_benchmark",
    "tsne_projection",
]
