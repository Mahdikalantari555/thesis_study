"""Incremental/continual training placeholder (task 9.1, design D9).

Each completed season, the frozen monitor model would be fine-tuned on newly
finished cycles so it keeps learning the current "normal". Anomalies must not
be learned as normal: before fine-tuning, the top-scoring fraction of the new
cycles is trimmed from the set (or weighted down), and the trimmed identities
stay available for the future active-learning loop in which farmers report
where and when stress actually happened (see ``docs/vision.md``).

Status in this change: interface stub ONLY. No implementation, no tests
beyond the stub's existence. Not called anywhere.
"""

from __future__ import annotations

from pathlib import Path


def fine_tune(
    checkpoint: str | Path,
    new_cycles,  # masked cycle batch of newly finished cycles (type defined with the implementation)
    *,
    trim_top_frac: float = 0.1,
):
    """Fine-tune a frozen monitor checkpoint on newly completed cycles.

    Parameters
    ----------
    checkpoint:
        Path to ``checkpoints/<id>_main.pt`` (loaded with its sidecar).
    new_cycles:
        Masked cycle tensors of cycles that finished since the last update.
    trim_top_frac:
        Fraction of highest-scoring new cycles to EXCLUDE from the fine-tuning
        set so suspected anomalies are not learned as normal.

    Raises
    ------
    NotImplementedError
        Always, until the incremental-training change. See ``docs/vision.md``
        (incremental training + active learning from farmer reports).
    """
    raise NotImplementedError(
        "Incremental fine-tuning is a placeholder in this change "
        "(train-and-finalize-main-architecture, design D9). "
        "See docs/vision.md for the planned incremental-training and "
        "active-learning design; implement in a dedicated openspec change."
    )
