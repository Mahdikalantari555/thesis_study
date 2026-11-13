"""PyTorch Dataset and collate for SSL cycle training."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch.utils.data import Dataset

from ..models.tokenizer import CycleTokenizer, mask_tokens


@dataclass
class CycleRecord:
    field_id: int
    cycle_id: int
    stratum: str
    tokens: np.ndarray  # (T, d_feat)
    is_validation: bool = False


class CycleDataset(Dataset):
    """Dataset of padded token arrays.

    Each item is a CycleRecord; masking happens in collate so the same record
    yields different masks per epoch (augmentation effect).
    """

    def __init__(self, records: list[CycleRecord]) -> None:
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> CycleRecord:
        return self.records[idx]


def cycle_collate(
    batch: list[CycleRecord],
    *,
    mask_ratio: float = 0.25,
    mask_block_max: int = 3,
    mask_block_p: float = 0.3,
    seed: int | None = None,
) -> dict:
    """Collate records into padded batches, applying random+block masking.

    Returns dict with:
        tokens : (B, T_max, d)  — masked tokens
        mask   : (B, T_max) bool — True where masked (loss target)
        lengths: (B,)
        pamask : (B, T_max) bool — True where padding (key_padding_mask)
        original: (B, T_max, d)
        field_ids, cycle_ids, strata
    """
    rng = np.random.default_rng(seed)
    d = batch[0].tokens.shape[1]
    lengths = np.array([r.tokens.shape[0] for r in batch], dtype=np.int64)
    T_max = int(lengths.max())
    B = len(batch)

    tokens = np.zeros((B, T_max, d), dtype=np.float32)
    original = np.zeros((B, T_max, d), dtype=np.float32)
    mask = np.zeros((B, T_max), dtype=bool)
    pamask = np.ones((B, T_max), dtype=bool)  # True = pad
    field_ids = []
    cycle_ids = []
    strata = []
    val_flags = []
    for i, r in enumerate(batch):
        t = r.tokens
        T_i = t.shape[0]
        tokens[i, :T_i] = t
        original[i, :T_i] = t
        pamask[i, :T_i] = False
        masked_tok, m = mask_tokens(
            t, mask_ratio=mask_ratio, block_max=mask_block_max, block_p=mask_block_p,
            rng=rng,
        )
        tokens[i, :T_i] = masked_tok
        mask[i, :T_i] = m
        field_ids.append(r.field_id)
        cycle_ids.append(r.cycle_id)
        strata.append(r.stratum)
        val_flags.append(r.is_validation)
    return {
        "tokens": torch.from_numpy(tokens),
        "mask": torch.from_numpy(mask),
        "lengths": torch.from_numpy(lengths),
        "pamask": torch.from_numpy(pamask),
        "original": torch.from_numpy(original),
        "field_ids": torch.tensor(field_ids, dtype=torch.long),
        "cycle_ids": torch.tensor(cycle_ids, dtype=torch.long),
        "strata": strata,
        "is_validation": torch.tensor(val_flags, dtype=torch.bool),
    }


def prepare_cycle_arrays(
    field_cycles: dict[int, list[dict]],
    tokenizer: CycleTokenizer,
    validation_fields: set[int] | None = None,
) -> list[CycleRecord]:
    """Tokenize every cycle and return a flat list of CycleRecord.

    ``field_cycles[fid]`` is a list of dicts with keys
    (bands, times, dsh, valid_frac, sensor, ratoon_no, stratum, cycle_id).
    """
    validation_fields = validation_fields or set()
    records: list[CycleRecord] = []
    for fid, cycles in field_cycles.items():
        for c in cycles:
            if c.get("censored", False):
                continue
            tok = tokenizer.tokenize(
                bands=c["bands"],
                times=c["times"],
                dsh=c["dsh"],
                valid_frac=c.get("valid_frac"),
                sensor=c.get("sensor"),
                ratoon_no=int(c.get("ratoon_no", 0)),
                weather=c.get("weather"),
                doy=c.get("doy"),
            )
            records.append(
                CycleRecord(
                    field_id=int(fid),
                    cycle_id=int(c.get("cycle_id", len(records))),
                    stratum=str(c.get("stratum", "all")),
                    tokens=tok,
                    is_validation=int(fid) in validation_fields,
                )
            )
    return records
