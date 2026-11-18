#!/usr/bin/env python3
"""Run a forward-only paired injection benchmark from a prepared cycle NPZ.

See docs/growth_validation.md for the input contract and limitations.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import time
import threading
from pathlib import Path
import warnings
import numpy as np
import sys

# Ensure src is on sys.path
_src_dir = Path(__file__).resolve().parents[1] / 'src'
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Load the lightweight module directly; avoid importing all optional SSL dependencies.
path = Path(__file__).resolve().parents[1] / 'src/ssl_anomaly/eval/growth_validation.py'
spec = importlib.util.spec_from_file_location('growth_validation', path)
gv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gv)


def run(data, *, band, holdouts, quantile, train_end, val_end, test_end, seed,
        models=('phase_mad', 'window_iforest'), epochs=15, bootstrap=500, excluded_fields=(), spatial_layout=None, affiliation=False, feature_bands=None):
    if bootstrap < 1:
        raise ValueError('bootstrap replicates must be positive')
    required = {'X', 'start_dates', 'end_dates', 'field_ids'}
    if not required.issubset(data.files):
        raise ValueError(f'missing NPZ arrays: {sorted(required - set(data.files))}')
    X = np.asarray(data['X'], dtype=float)
    if X.ndim != 3 or not 0 <= band < X.shape[2]:
        raise ValueError('X must be (cycles, bins, bands) with valid --band')
    original_band = band
    if feature_bands is not None:
        if (not feature_bands or len(set(feature_bands)) != len(feature_bands)
                or any(i < 0 or i >= X.shape[2] for i in feature_bands) or band not in feature_bands):
            raise ValueError('feature-bands must be unique valid indices containing the injected band')
        X = X[:, :, feature_bands]
        band = feature_bands.index(band)
    split = gv.temporal_split(data['start_dates'], data['end_dates'], data['field_ids'],
                              train_end=train_end, val_end=val_end, test_end=test_end,
                              holdout_fields=holdouts, excluded_fields=excluded_fields)
    if any(len(m) != len(X) for m in split.values()):
        raise ValueError('metadata length must equal number of cycles')
    if not split['train'].any() or not split['validation'].any():
        raise ValueError('need complete training and validation cycles')
    if not (split['temporal_test'].any() or split['spatial_test'].any()):
        raise ValueError('need at least one complete test cycle')
    ids = np.asarray(data['field_ids']).astype(str)
    bin_dates = np.asarray(data['bin_dates'], dtype='datetime64[D]') if 'bin_dates' in data.files else None
    if bin_dates is not None and (bin_dates.shape != X.shape[:2] or np.isnat(bin_dates).any()
                                  or np.any(bin_dates[:, 1:] < bin_dates[:, :-1])):
        raise ValueError('bin_dates must be valid, ordered and match (cycles,bins)')
    bin_days = int(data['bin_days']) if 'bin_days' in data.files else 1
    if bin_days < 1:
        raise ValueError('bin_days must be positive')
    result = {'protocol': {'train_end': train_end, 'validation_end': val_end, 'test_end': test_end,
                           'holdout_fields': holdouts, 'excluded_fields': list(excluded_fields),
                           'spatial_layout': spatial_layout, 'seed': seed, 'band': band,
                           'original_injection_band': original_band, 'feature_bands': feature_bands,
                           'threshold_quantile': quantile, 'test_used_for_calibration': False,
                           'label_source': 'injection_only_not_real_stress',
                           'score_direction': 'larger_is_more_anomalous'},
              'split_counts': {key: int(v.sum()) for key, v in split.items()}, 'models': {}}
    # Fixed grid is declared before scoring, not tuned against test.
    scenarios = [(kind, depth, phase, duration) for kind in ('sudden', 'gradual', 'delay', 'peak', 'recovery')
                 for depth in (0.05, 0.1, 0.2) for phase in ('early', 'mid', 'late') for duration in (3, 6)]
    model_map = {'phase_mad': lambda: gv.PhaseMAD(),
                 'field_phase_mad': lambda: gv.FieldPhaseMAD(),
                 'window_iforest': lambda: gv.WindowIsolationForest(seed=seed),
                 'window_ocsvm': lambda: gv.WindowOneClassSVM()}
    if any(name in ('gru_ae', 'masked_transformer', 'jepa', 'causal_gru', 'causal_transformer', 'causal_jepa', 'random_gru_ae', 'random_masked_transformer') for name in models):
        ssl_path = path.with_name('growth_ssl.py')
        ssl_spec = importlib.util.spec_from_file_location('growth_ssl', ssl_path)
        ssl = importlib.util.module_from_spec(ssl_spec)
        ssl_spec.loader.exec_module(ssl)
        for name in ('gru_ae', 'masked_transformer', 'jepa', 'sts_net', 'tiny_cnn_mamba', 'time2agri'):
            model_map[name] = lambda name=name: ssl.MaskedSSL(name, epochs=epochs, seed=seed)
        model_map['random_gru_ae'] = lambda: ssl.MaskedSSL('gru_ae', epochs=epochs, seed=seed, train_enabled=False)
        model_map['random_masked_transformer'] = lambda: ssl.MaskedSSL('masked_transformer', epochs=epochs, seed=seed, train_enabled=False)
        model_map['causal_gru'] = lambda: ssl.MaskedSSL('gru_ae', epochs=epochs, seed=seed, causal=True)
        model_map['causal_transformer'] = lambda: ssl.MaskedSSL('masked_transformer', epochs=epochs, seed=seed, causal=True)
        model_map['causal_sts_net'] = lambda: ssl.MaskedSSL('sts_net', epochs=epochs, seed=seed, causal=True)
        model_map['causal_cnn_mamba'] = lambda: ssl.MaskedSSL('tiny_cnn_mamba', epochs=epochs, seed=seed, causal=True)
        model_map['causal_time2agri'] = lambda: ssl.MaskedSSL('time2agri', epochs=epochs, seed=seed, causal=True)
        model_map['causal_jepa'] = lambda: ssl.MaskedSSL('jepa', epochs=epochs, seed=seed, causal=True)
    if not models or len(set(models)) != len(models) or any(name not in model_map for name in models):
        raise ValueError('unknown, empty or duplicate models')
    result['protocol']['models'] = list(models)
    result['protocol']['ssl_epochs'] = epochs
    result['protocol']['bootstrap_replicates'] = bootstrap
    result['protocol']['affiliation_enabled'] = affiliation
    for model_name in models:
        model = model_map[model_name]()
        import psutil
        process = psutil.Process()
        initial_rss = process.memory_info().rss
        rss_samples = [initial_rss]
        stop_sampling = threading.Event()
        def sample_memory():
            while not stop_sampling.wait(.01):
                rss_samples.append(process.memory_info().rss)
        monitor = threading.Thread(target=sample_memory, daemon=True)
        monitor.start()
        field_aware = model_name == 'field_phase_mad'
        def score(arr, field_ids):
            return model.score(arr, field_ids) if field_aware else model.score(arr)
        try:
            started = time.perf_counter()
            if field_aware:
                model.fit(X[split['train']], ids[split['train']])
            else:
                model.fit(X[split['train']])
            train_seconds = time.perf_counter() - started
            started = time.perf_counter()
            val_scores = score(X[split['validation']], ids[split['validation']])
            inference_seconds = time.perf_counter() - started
            rss_samples.append(process.memory_info().rss)
        finally:
            stop_sampling.set()
            monitor.join()
        threshold = gv.calibrate(val_scores, quantile)
        out = {'threshold': threshold, 'scenarios': [], 'train_seconds': train_seconds,
               'validation_inference_seconds_per_cycle': inference_seconds / int(split['validation'].sum()),
               'parameter_count': getattr(model, 'parameter_count', None),
               'memory_profile': {'initial_rss_bytes': initial_rss, 'sampled_peak_rss_bytes': max(rss_samples),
                                  'sampled_peak_increase_bytes': max(rss_samples)-initial_rss,
                                  'sample_interval_seconds': .01, 'scope': 'process_during_fit_and_validation_score'},
               'scoring_mode': 'causal_prefix' if model_name.startswith('causal_') else 'retrospective_or_window'}
        for subset in ('temporal_test', 'spatial_test'):
            selected = np.flatnonzero(split[subset])
            if not len(selected):
                continue
            original = X[selected]
            original_scores = score(original, ids[selected])
            finite_original = np.isfinite(original_scores)
            out[subset + '_original_events'] = []
            for j, idx in enumerate(selected):
                flags = finite_original[j] & (original_scores[j] > threshold)
                begins = np.flatnonzero(flags & ~np.r_[False, flags[:-1]])
                ends = np.flatnonzero(flags & ~np.r_[flags[1:], False])
                for a, b in zip(begins, ends):
                    event = {'event_id': f'{model_name}:{subset}:{idx}:{a}', 'field_id': ids[idx],
                             'cycle_index': int(idx), 'first_bin': int(a), 'last_bin': int(b),
                             'start_date': None, 'end_date': None}
                    if bin_dates is not None:
                        start = max(bin_dates[idx, a], np.datetime64(data['start_dates'][idx], 'D'))
                        end = min(bin_dates[idx, b] + np.timedelta64(bin_days-1, 'D'),
                                  np.datetime64(data['end_dates'][idx], 'D'))
                        if end >= start:
                            event['start_date'], event['end_date'] = str(start), str(end)
                    out[subset + '_original_events'].append(event)
            out[subset + '_original_alert_fraction'] = (float(np.mean(original_scores[finite_original] > threshold))
                                                          if finite_original.any() else None)
            for kind, depth, phase, dur in scenarios:
                k = X.shape[1]
                start = {'early': 0, 'mid': k // 3, 'late': 2 * k // 3}[phase]
                altered = []; masks = []
                for cyc in original:
                    modified, mask = gv.inject_growth(cyc, kind=kind, start=start, duration=dur,
                                                      magnitude=depth, band=band)
                    altered.append(modified); masks.append(mask)
                modified_scores = score(np.stack(altered), ids[selected])
                masks = np.stack(masks)
                eligible = masks.any(axis=1)
                if not eligible.any():
                    continue
                # Compare only modified bins and their exact originals, avoiding label
                # ambiguity outside injections and excluding untouched cycles.
                paired = masks & np.isfinite(original_scores) & np.isfinite(modified_scores)
                if not paired.any():
                    continue
                s0, s1 = original_scores[paired], modified_scores[paired]
                labels = np.r_[np.zeros(len(s0), bool), np.ones(len(s1), bool)]
                metrics = gv.point_metrics(labels, np.r_[s0, s1], threshold)
                events = [gv.event_metrics(m, s, threshold) for m, s in zip(masks, modified_scores)]
                detected = sum(e['detected'] for e in events)
                n_events = sum(e['events'] for e in events)
                delays = [d for e in events for d in e['delays'] if d is not None]
                per_field = {}
                for fid in np.unique(ids[selected]):
                    ii = ids[selected] == fid
                    ev = [events[j] for j in np.flatnonzero(ii)]
                    per_field[fid] = {'events': sum(x['events'] for x in ev),
                                      'detected': sum(x['detected'] for x in ev)}
                overlaps = [gv.event_overlap_counts(m, s, threshold) for m, s in zip(masks, modified_scores)]
                predicted = sum(e['predicted_runs'] for e in overlaps)
                matched = sum(e['matched_runs'] for e in overlaps)
                ci = gv.field_bootstrap_ratio([v['detected'] for v in per_field.values()],
                                               [v['events'] for v in per_field.values()],
                                               seed=seed, n_boot=bootstrap)
                aff = None
                if affiliation:
                    segments = [seg for m, s in zip(masks, modified_scores)
                                for seg in gv.affiliation_by_observed_segment(m, s, threshold)]
                    precisions = [seg['precision'] for seg in segments if seg['precision'] is not None]
                    recalls = [seg['recall'] for seg in segments if seg['recall'] is not None]
                    aff = {'segments_with_truth': len(segments),
                           'precision_mean': float(np.mean(precisions)) if precisions else None,
                           'recall_mean': float(np.mean(recalls)) if recalls else None,
                           'aggregation': 'unweighted_mean_over_finite_observation_segments'}
                out['scenarios'].append({'subset': subset, 'kind': kind, 'magnitude': depth,
                    'phase': phase, 'duration_bins': dur, 'eligible_cycles': int(eligible.sum()),
                    'paired_bins': int(paired.sum()), 'mean_paired_score_change': float(np.mean(s1-s0)),
                    'point_metrics': metrics, 'affiliation': aff, 'events': n_events, 'detected_events': detected,
                    'missed_events': n_events-detected,
                    'event_recall': detected/n_events if n_events else None,
                    'event_recall_field_bootstrap_ci95': ci,
                    'predicted_runs': predicted, 'matched_predicted_runs': matched,
                    'synthetic_event_precision': matched/predicted if predicted else None,
                    'mean_delay_detected_bins': float(np.mean(delays)) if delays else None,
                    'per_field_events': per_field})
        result['models'][model_name] = out
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--band', required=True, type=int, help='zero-based NDVI/EVI column in X')
    ap.add_argument('--holdout-fields', default='', help='comma-separated field IDs chosen before evaluation')
    ap.add_argument('--spatial-layout', type=Path, help='predeclared geographic layout JSON')
    ap.add_argument('--train-end', default='2021-12-31')
    ap.add_argument('--val-end', default='2023-12-31')
    ap.add_argument('--test-end', default='2026-12-31')
    ap.add_argument('--quantile', type=float, default=0.95)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--models', default='phase_mad,window_iforest',
                    help='comma-separated: phase_mad,field_phase_mad,window_iforest,window_ocsvm,gru_ae,masked_transformer,jepa,causal_jepa')
    ap.add_argument('--feature-bands', help='comma-separated input columns; must include --band')
    ap.add_argument('--affiliation', action='store_true', help='compute affiliation metrics per observed segment')
    ap.add_argument('--epochs', type=int, default=15, help='fresh SSL training epochs')
    ap.add_argument('--bootstrap', type=int, default=500, help='field bootstrap replicates')
    args = ap.parse_args()
    layout = json.loads(args.spatial_layout.read_text()) if args.spatial_layout else None
    if layout and args.holdout_fields:
        ap.error('use either --spatial-layout or --holdout-fields')
    holdouts = layout['holdout_fields'] if layout else [x for x in args.holdout_fields.split(',') if x]
    excluded = layout['excluded_fields'] if layout else []
    with np.load(args.input, allow_pickle=False) as data, warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='All-NaN slice encountered', category=RuntimeWarning)
        result = run(data, band=args.band, holdouts=holdouts,
                     quantile=args.quantile, train_end=args.train_end, val_end=args.val_end,
                     test_end=args.test_end, seed=args.seed, models=args.models.split(','),
                     epochs=args.epochs, bootstrap=args.bootstrap, excluded_fields=excluded, spatial_layout=layout,
                     affiliation=args.affiliation,
                     feature_bands=[int(x) for x in args.feature_bands.split(',')] if args.feature_bands else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f'Wrote {args.output}; split counts: {result["split_counts"]}')


if __name__ == '__main__':
    main()
