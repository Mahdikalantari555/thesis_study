from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

from ssl_anomaly.config import SSLCfg, default_config
from ssl_anomaly.export import export_release, load_release
from ssl_anomaly.models.gru_ae import GRUAutoencoder
from ssl_anomaly.train.data import CycleRecord, cycle_collate
from ssl_anomaly.train.lit_module import SSLLitModule

SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_gru_ae_lit_module_train_embed_reconstruct_and_export(tmp_path):
    """Test GRU-AE end-to-end through SSLLitModule, gradient descent on masked targets, and SafeTensors export."""
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    d_in = 10
    # Create structured sinusoidal cycles so GRU-AE genuinely reduces masked loss
    recs = []
    for i in range(8):
        T = 20 + (i % 4) * 2
        t = np.linspace(0, np.pi, T, dtype=np.float32)
        tok = np.stack([np.sin(t + 0.2 * b) for b in range(d_in)], axis=-1).astype(np.float32)
        tok += rng.normal(0, 0.03, size=tok.shape).astype(np.float32)
        recs.append(CycleRecord(field_id=i + 1, cycle_id=0, stratum="all", tokens=tok))

    batch = cycle_collate(recs, mask_ratio=0.25, mask_block_max=2, seed=7)
    cfg = SSLCfg(model="gru_ae", lr=3e-3, trim_loss_frac=0.0)
    lit = SSLLitModule(d_in=d_in, cfg=cfg)
    assert isinstance(lit.model, GRUAutoencoder)

    init_loss = float(lit._compute_loss(batch).detach())
    opt = torch.optim.AdamW(lit.parameters(), lr=5e-3)
    for _ in range(25):
        loss = lit.training_step(batch, 0)
        opt.zero_grad()
        loss.backward()
        opt.step()
    final_loss = float(lit._compute_loss(batch).detach())
    assert final_loss < init_loss * 0.6

    emb = lit.embed(batch["tokens"], lengths=batch["lengths"])
    recon = lit.reconstruct(batch["tokens"], lengths=batch["lengths"])
    assert emb.shape == (8, cfg.gru_ae.d_model)
    assert recon.shape == batch["tokens"].shape

    rel_dir = export_release(
        lit,
        model_config={
            "model": "gru_ae",
            "d_in": d_in,
            "gru_ae": {
                "d_model": cfg.gru_ae.d_model,
                "n_layers": cfg.gru_ae.n_layers,
                "dropout": cfg.gru_ae.dropout,
                "bidirectional_enc": cfg.gru_ae.bidirectional_enc,
            },
        },
        norm_stats={"d_feature": d_in},
        out_dir=tmp_path / "gru_ae_rel",
        seed=42,
    )
    loaded, _, _ = load_release(
        lambda mc: GRUAutoencoder(d_in=mc["d_in"], **mc["gru_ae"]),
        rel_dir,
    )
    lit.eval()
    with torch.no_grad():
        r1, e1 = lit.model(batch["tokens"], lengths=batch["lengths"])
        r2, e2 = loaded(batch["tokens"], lengths=batch["lengths"])
    assert torch.allclose(r1, r2, atol=1e-6)
    assert torch.allclose(e1, e2, atol=1e-6)


def test_train_ssl_cli_overrides_select_gru_ae_or_transformer():
    from train_ssl import apply_cli_overrides

    cfg_gru = apply_cli_overrides(default_config(), ["model=gru_ae", "profile=laptop", "max_epochs=5", "seed=99"])
    assert cfg_gru.ssl.model == "gru_ae"
    assert cfg_gru.ssl.max_epochs == 5
    assert cfg_gru.train.seed == 99

    cfg_tf = apply_cli_overrides(default_config(), ["--model", "transformer", "--max-epochs", "12"])
    assert cfg_tf.ssl.model == "transformer"
    assert cfg_tf.ssl.max_epochs == 12
