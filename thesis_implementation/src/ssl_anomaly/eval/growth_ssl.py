"""Matched-input retrospective SSL adapters for the growth validation benchmark.

Freshly trained masked reconstruction; these are not existing checkpoints. Each score
masks the scored time bin, but uses other bins from the full cycle (non-causal).
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import torch

# Make src/ importable when this module is loaded by path (e.g. in tests).
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _model_class(filename, name):
    import importlib
    mod_name = f"ssl_anomaly.models.{filename.removesuffix('.py')}"
    mod = importlib.import_module(mod_name)
    return getattr(mod, name)


class MaskedSSL:
    def __init__(self, architecture, *, epochs=15, seed=42, mask_fraction=.25, batch_size=32, causal=False, train_enabled=True):
        valid_archs = ('gru_ae', 'masked_transformer', 'sts_net', 'tiny_cnn_mamba', 'time2agri', 'jepa')
        if architecture not in valid_archs:
            raise ValueError(f'unsupported architecture {architecture}; expected {valid_archs}')
        if epochs < 1 or batch_size < 1 or not 0 < mask_fraction <= 1:
            raise ValueError('invalid training parameters')
        self.architecture, self.epochs, self.seed = architecture, epochs, seed
        self.mask_fraction, self.batch_size = mask_fraction, batch_size
        self.causal = bool(causal)
        self.train_enabled = bool(train_enabled)

    def _tokens(self, X):
        x = np.asarray(X, dtype=np.float32)
        if x.ndim != 3 or x.shape[1:] != self.shape:
            raise ValueError('model input shape differs from training')
        observed = np.isfinite(x)
        z = np.where(observed, (x - self.center) / self.scale, 0).astype(np.float32)
        # GRU receives explicit missing/target mask; fixed phase is an exogenous index.
        phase = np.broadcast_to(np.linspace(0, 1, x.shape[1], dtype=np.float32)[None,:,None],
                                (len(x), x.shape[1], 1))
        tokens = np.concatenate([z, observed.astype(np.float32), phase], axis=2)
        return torch.from_numpy(tokens), torch.from_numpy(observed)

    def fit(self, X):
        x = np.asarray(X, dtype=np.float32)
        if x.ndim != 3 or len(x) == 0 or not np.isfinite(x).any():
            raise ValueError('training requires observed 3D data')
        x = x[np.isfinite(x).any(axis=(1, 2))]
        self.shape = x.shape[1:]
        self.n_bands = x.shape[2]
        with np.errstate(all='ignore'):
            self.center = np.nanmedian(x, axis=(0, 1))
            self.scale = 1.4826 * np.nanmedian(np.abs(x-self.center), axis=(0,1))
        self.center = np.where(np.isfinite(self.center), self.center, 0)
        self.scale = np.where(np.isfinite(self.scale) & (self.scale > .02), self.scale, .02)
        torch.manual_seed(self.seed)
        torch.set_num_threads(1)
        d_in = 2*self.n_bands + 1
        if self.architecture == 'gru_ae':
            cls = _model_class('gru_ae.py', 'GRUAutoencoder')
            self.model = cls(d_in=d_in, d_model=32, n_layers=1, dropout=0)
        elif self.architecture == 'sts_net':
            cls = _model_class('sts_net.py', 'STSNetAutoencoder')
            self.model = cls(d_in=d_in, d_model=32, latent_dim=16)
        elif self.architecture == 'tiny_cnn_mamba':
            cls = _model_class('cnn_mamba.py', 'TinyCNNMamba')
            self.model = cls(d_in=d_in, d_model=32, d_state=8, n_layers=2, latent_dim=16)
        elif self.architecture == 'time2agri':
            cls = _model_class('pretexts.py', 'PretextTransformer')
            self.model = cls(d_in=d_in, n_bands=self.n_bands, d_model=32, n_heads=4, n_layers=2,
                             d_ff=64, dropout=.1, max_len=max(128, self.shape[0]), arm='masked_recon')
        elif self.architecture == 'jepa':
            from ssl_anomaly.models.jepa import JEPAModel
            self.model = JEPAModel(d_in=d_in, d_model=32, n_heads=4, n_layers=2, d_ff=64, max_len=max(128, self.shape[0]))
        else:
            cls = _model_class('masked_tf.py', 'MaskedTransformer')
            self.model = cls(d_in=d_in, d_model=32, n_heads=4, n_layers=2,
                             d_ff=64, dropout=.1, max_len=max(128, self.shape[0]))
        self.model.train()
        opt = torch.optim.AdamW(self.model.parameters(), lr=.001)
        tok, obs = self._tokens(x)
        rng = np.random.default_rng(self.seed)
        for _ in range(self.epochs if self.train_enabled else 0):
            for indices in np.array_split(rng.permutation(len(x)), max(1, int(np.ceil(len(x)/self.batch_size)))):
                original = tok[indices]
                observed = obs[indices]
                masks = torch.from_numpy(rng.random(original.shape[:2]) < self.mask_fraction)
                masks &= observed.any(dim=2)
                lengths = None
                pad = ~observed.any(dim=2)
                if self.causal:
                    # One observed cutoff per cycle; never train using future tokens.
                    masks[:] = False
                    cutoffs = []
                    for row in range(len(original)):
                        possible = torch.nonzero(observed[row].any(dim=1)).flatten().numpy()
                        cutoff = int(rng.choice(possible)) if len(possible) else 0
                        cutoffs.append(cutoff)
                        if len(possible):
                            masks[row, cutoff] = True
                    lengths = torch.tensor(cutoffs, dtype=torch.long) + 1
                    future = torch.arange(original.shape[1])[None, :] >= lengths[:, None]
                    pad = pad | future
                if not masks.any():
                    continue
                inputs = original.clone()
                inputs[:, :, :2*self.n_bands][masks] = 0
                if self.causal:
                    inputs[future] = 0
                if self.architecture in ('masked_transformer', 'jepa'):
                    recon, _ = self.model(inputs, mask=masks, key_padding_mask=pad)
                elif self.architecture in ('sts_net', 'tiny_cnn_mamba'):
                    recon, _ = self.model(inputs)
                elif self.architecture == 'time2agri':
                    h, _ = self.model.encode_sequence(inputs, mask=masks, key_padding_mask=pad)
                    recon = self.model.task_head(h)
                else:
                    recon, _ = self.model(inputs, lengths=lengths)
                target_mask = observed & masks.unsqueeze(-1)
                loss = ((recon[:, :, :self.n_bands] - original[:, :, :self.n_bands])**2)[target_mask].mean()
                if self.architecture == 'jepa':
                    # Latent prediction against the EMA target encoder (JEPA objective).
                    loss = loss + self.model.latent_prediction_loss(inputs, masks, pad, target=original)
                opt.zero_grad(); loss.backward(); opt.step()
        self.model.eval()
        return self

    def score(self, X):
        tok, obs = self._tokens(X)
        n, k, _ = tok.shape
        result = np.full((n, k), np.nan)
        # Bounded batches of leave-one-time-bin-out masked predictions.
        pairs = np.argwhere(obs.any(dim=2).numpy())
        with torch.no_grad():
            for indices in np.array_split(pairs, max(1, int(np.ceil(len(pairs)/self.batch_size)))):
                if len(indices) == 0:
                    continue
                rows, cols = indices[:,0], indices[:,1]
                inputs = tok[rows].clone()
                mask = torch.zeros((len(rows), k), dtype=torch.bool)
                mask[torch.arange(len(rows)), cols] = True
                inputs[torch.arange(len(rows)), cols, :2*self.n_bands] = 0
                pad = ~obs[rows].any(dim=2)
                lengths = None
                if self.causal:
                    lengths = torch.as_tensor(cols + 1, dtype=torch.long)
                    future = torch.arange(k)[None, :] >= lengths[:, None]
                    inputs[future] = 0
                    pad = pad | future
                if self.architecture in ('masked_transformer', 'jepa'):
                    recon, _ = self.model(inputs, mask=mask, key_padding_mask=pad)
                elif self.architecture in ('sts_net', 'tiny_cnn_mamba'):
                    recon, _ = self.model(inputs)
                elif self.architecture == 'time2agri':
                    h, _ = self.model.encode_sequence(inputs, mask=mask, key_padding_mask=pad)
                    recon = self.model.task_head(h)
                else:
                    recon, _ = self.model(inputs, lengths=lengths)
                prediction = recon[torch.arange(len(rows)), cols, :self.n_bands]
                target = tok[rows, cols, :self.n_bands]
                valid = obs[rows, cols]
                err = ((prediction-target)**2 * valid).sum(dim=1)/valid.sum(dim=1)
                result[rows, cols] = err.numpy()
        return result

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.model.parameters())
