from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('growth_validation', ROOT / 'src/ssl_anomaly/eval/growth_validation.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_split_boundaries_and_spatial_exclusion():
    s = ['2020-01-01', '2021-12-01', '2022-01-01', '2024-01-01', '2024-01-01', '2021-01-01']
    e = ['2020-12-31', '2022-01-02', '2023-12-31', '2024-12-31', '2024-12-31', '2021-12-01']
    p = g.temporal_split(s, e, ['a', 'a', 'a', 'a', 'b', 'b'], holdout_fields=['b'])
    assert np.flatnonzero(p['train']).tolist() == [0]
    assert np.flatnonzero(p['validation']).tolist() == [2]
    assert np.flatnonzero(p['temporal_test']).tolist() == [3]
    assert np.flatnonzero(p['spatial_test']).tolist() == [4]
    assert np.flatnonzero(p['excluded']).tolist() == [1, 5]


@pytest.mark.parametrize('kind', ['sudden', 'gradual', 'delay', 'peak', 'recovery'])
def test_injection_is_paired_and_preserves_missing(kind):
    x = np.column_stack([np.linspace(.1, .9, 12), np.arange(12.)])
    x[5, 0] = np.nan
    orig = x.copy()
    y, mask = g.inject_growth(x, kind=kind, start=3, duration=6, magnitude=.1)
    np.testing.assert_equal(x, orig)
    assert mask.any() and not mask[5]
    np.testing.assert_equal(x[:, 1], y[:, 1])
    assert np.array_equal(mask, np.isfinite(x[:, 0]) & (x[:, 0] != y[:, 0]))


def test_calibration_and_events():
    threshold = g.calibrate([0, 1, 2, 3], .5)
    assert threshold == 1.5
    e = g.event_metrics([0, 1, 1, 0, 1, 1], [0, 0, 2, 0, 0, 0], threshold)
    assert e['delays'] == [1, None] and e['missed'] == 1
    m = g.point_metrics([0, 0, 1, 1], [0, 2, 1, 3], threshold)
    assert (m['tp'], m['fp'], m['fn'], m['tn']) == (1, 1, 1, 1)
    assert g.point_metrics([0, 0], [1, 2], 1)['roc_auc'] is None


def test_causal_windows_do_not_see_future():
    x = np.arange(12., dtype=float).reshape(1, 6, 2)
    model = g.WindowIsolationForest(window=3, seed=0).fit(x)
    a = model.score(x)
    y = x.copy(); y[:, 4:] += 1000
    np.testing.assert_allclose(a[:, :4], model.score(y)[:, :4])


def test_end_to_end(tmp_path):
    rng = np.random.default_rng(2)
    x = rng.uniform(.2, .8, (8, 9, 2))
    starts = np.array(['2019-01-01'] * 3 + ['2022-01-01'] * 2 + ['2024-01-01'] * 3)
    ends = np.array(['2019-10-01'] * 3 + ['2022-10-01'] * 2 + ['2024-10-01'] * 3)
    ids = np.array(['a', 'a', 'b', 'a', 'b', 'a', 'b', 'c'])
    source, output = tmp_path / 'cycles.npz', tmp_path / 'report.json'
    np.savez(source, X=x, start_dates=starts, end_dates=ends, field_ids=ids)
    subprocess.run([sys.executable, str(ROOT / 'scripts/validate_growth.py'), '--input', str(source),
                    '--output', str(output), '--band', '0', '--holdout-fields', 'c'], check=True)
    report = json.loads(output.read_text())
    assert report['split_counts']['spatial_test'] == 1
    assert report['models']['phase_mad']['scenarios']
    assert report['protocol']['test_used_for_calibration'] is False


def test_event_precision_and_cluster_ci():
    runs = g.event_overlap_counts([0, 1, 1, 0, 0, 0], [0, 2, 2, 0, 2, 0], 1)
    assert runs == {'predicted_runs': 2, 'matched_runs': 1, 'unmatched_runs': 1}
    assert g.field_bootstrap_ratio([1], [2]) is None
    ci = g.field_bootstrap_ratio([1, 0, 2], [2, 1, 2], seed=1, n_boot=100)
    assert 0 <= ci[0] <= ci[1] <= 1


@pytest.mark.parametrize('architecture', ['gru_ae', 'masked_transformer'])
def test_ssl_train_only_and_missing(architecture):
    pytest.importorskip('torch')
    p = ROOT / 'src/ssl_anomaly/eval/growth_ssl.py'
    spec = importlib.util.spec_from_file_location('growth_ssl', p)
    ssl = importlib.util.module_from_spec(spec); spec.loader.exec_module(ssl)
    x = np.array([[[.2], [.4], [np.nan], [.5]], [[.3], [.5], [.6], [.7]]])
    model = ssl.MaskedSSL(architecture, epochs=1, seed=3).fit(x)
    center = model.center.copy()
    y = x.copy(); y[0, 1, 0] = 10
    scores = model.score(y)
    np.testing.assert_equal(center, model.center)
    assert scores.shape == (2, 4) and np.isnan(scores[0, 2])
    assert np.isfinite(scores[0, 1]) and model.parameter_count > 0


def test_weather_evidence_reference_and_neighbors():
    pd = pytest.importorskip('pandas')
    spec = importlib.util.spec_from_file_location('growth_evidence', ROOT / 'scripts/analyze_growth_evidence.py')
    evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)
    events = pd.DataFrame({'event_id':['x','y'], 'field_id':['1','2'],
                           'start_date':['2024-01-02','2024-01-02'], 'end_date':['2024-01-03','2024-01-04']})
    weather = pd.DataFrame({'field_id':['1']*4, 'date':['2019-01-01','2020-01-01','2021-01-01','2024-01-02'],
                            'vpd':[1.,2.,3.,5.]})
    edges = pd.DataFrame({'field_id':['1'], 'neighbor_id':['2']})
    out = evidence.analyze(events, weather, reference_end='2021-12-31', variables=['vpd'], edges=edges)
    assert out['events'][0]['weather']['vpd']['mean_difference'] == 3
    assert out['events'][0]['neighbors_with_overlapping_events'] == 1
    assert out['events'][1]['weather']['vpd']['mean_difference'] is None
    with pytest.raises(ValueError):
        evidence.analyze(events, weather, reference_end='2024-01-02', variables=['vpd'])


def test_spatial_block_and_buffer_exclusion():
    layout = g.geographic_holdout(['a', 'b', 'c'], [10, 95, 110], [0, 0, 0],
                                   block_size=100, origin_x=0, origin_y=0,
                                   holdout_blocks=[(1, 0)], buffer=20)
    assert layout['holdout_fields'] == ['c'] and layout['excluded_fields'] == ['b']
    split = g.temporal_split(['2019-01-01','2019-01-01','2024-01-01'],
                             ['2019-02-01','2019-02-01','2024-02-01'], ['a','b','c'],
                             holdout_fields=layout['holdout_fields'], excluded_fields=layout['excluded_fields'])
    assert split['train'].tolist() == [True, False, False]
    assert split['spatial_test'].tolist() == [False, False, True]


def test_window_ocsvm_uses_only_past_and_train():
    x = np.arange(16., dtype=float).reshape(2, 4, 2)
    model = g.WindowOneClassSVM(window=2).fit(x)
    before = model.center.copy()
    s = model.score(x)
    y = x.copy(); y[:, 3] += 100
    np.testing.assert_equal(before, model.center)
    np.testing.assert_allclose(s[:, :3], model.score(y)[:, :3])


def test_cli_ssl_and_event_export(tmp_path):
    pytest.importorskip('torch')
    x = np.tile(np.linspace(.2, .8, 6)[None,:,None], (7,1,1))
    starts = np.array(['2019-01-01']*3+['2022-01-01']*2+['2024-01-01']*2)
    ends = np.array(['2019-10-01']*3+['2022-10-01']*2+['2024-10-01']*2)
    ids = np.array(['a','a','b','a','b','a','b'])
    dates = starts.astype('datetime64[D]')[:,None] + np.arange(6)[None,:].astype('timedelta64[D]') * 15
    inp, out, csv = tmp_path/'in.npz', tmp_path/'out.json', tmp_path/'events.csv'
    np.savez(inp, X=x, start_dates=starts, end_dates=ends, field_ids=ids, bin_dates=dates, bin_days=15)
    subprocess.run([sys.executable, str(ROOT/'scripts/validate_growth.py'), '--input', str(inp),
                    '--output', str(out), '--band', '0', '--models', 'gru_ae,masked_transformer',
                    '--epochs', '1', '--bootstrap', '10'], check=True)
    report = json.loads(out.read_text())
    assert set(report['models']) == {'gru_ae', 'masked_transformer'}
    assert report['models']['gru_ae']['parameter_count'] > 0
    subprocess.run([sys.executable, str(ROOT/'scripts/export_growth_events.py'), '--report', str(out),
                    '--model', 'gru_ae', '--subset', 'temporal_test', '--output', str(csv)], check=True)
    assert csv.read_text().startswith('event_id,field_id,start_date,end_date')


def test_field_specific_history_and_unseen_fallback():
    x = np.array([[[.1], [.2]], [[.2], [.3]], [[.8], [.9]], [[.9], [1.0]]])
    model = g.FieldPhaseMAD(shrinkage=0).fit(x, ['a','a','b','b'])
    seen = model.score(x[:1], ['a'])
    fallback = model.score(x[:1], ['new'])
    assert np.nanmean(seen) < np.nanmean(fallback)
    assert 'new' not in model.offsets


def test_test_data_never_changes_calibration(tmp_path):
    spec = importlib.util.spec_from_file_location('validate_growth', ROOT / 'scripts/validate_growth.py')
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    x = np.tile(np.arange(6., dtype=float)[None,:,None], (5,1,1))
    starts = np.array(['2019-01-01']*2 + ['2022-01-01']*2 + ['2024-01-01'])
    ends = np.array(['2019-03-01']*2 + ['2022-03-01']*2 + ['2024-03-01'])
    fields = np.array(['a','a','a','a','a'])
    kwargs = dict(band=0, holdouts=[], quantile=.95, train_end='2021-12-31',
                  val_end='2023-12-31', test_end='2026-12-31', seed=42,
                  models=('phase_mad',), bootstrap=5)
    a, b = tmp_path/'a.npz', tmp_path/'b.npz'
    np.savez(a, X=x, start_dates=starts, end_dates=ends, field_ids=fields)
    x[-1] += 10000
    np.savez(b, X=x, start_dates=starts, end_dates=ends, field_ids=fields)
    with np.load(a) as first, np.load(b) as second:
        r1 = runner.run(first, **kwargs); r2 = runner.run(second, **kwargs)
    assert r1['models']['phase_mad']['threshold'] == r2['models']['phase_mad']['threshold']


def test_affiliation_reference_and_missing():
    rows = g.affiliation_by_observed_segment([0,1,1,0,0,1], [0,2,2,0,np.nan,0], 1)
    assert len(rows) == 2
    assert rows[0]['precision'] == pytest.approx(1)
    assert rows[0]['recall'] == pytest.approx(1)
    assert rows[1]['precision'] is None
    assert rows[1]['recall'] == pytest.approx(0)


@pytest.mark.parametrize('architecture', ['gru_ae', 'masked_transformer'])
def test_causal_ssl_future_invariance(architecture):
    pytest.importorskip('torch')
    p = ROOT / 'src/ssl_anomaly/eval/growth_ssl.py'
    spec = importlib.util.spec_from_file_location('growth_ssl_causal', p)
    ssl = importlib.util.module_from_spec(spec); spec.loader.exec_module(ssl)
    x = np.arange(24., dtype=float).reshape(3,8,1) / 24
    model = ssl.MaskedSSL(architecture, epochs=2, seed=3, causal=True).fit(x)
    original = model.score(x)
    changed = x.copy(); changed[:,4:,:] += 1000
    np.testing.assert_allclose(original[:,:4], model.score(changed)[:,:4], atol=1e-6)


def test_online_binning_uses_only_prior_samples():
    pd = pytest.importorskip('pandas')
    spec = importlib.util.spec_from_file_location('growth_online', ROOT / 'scripts/prepare_online_growth.py')
    online = importlib.util.module_from_spec(spec); spec.loader.exec_module(online)
    anchors = pd.DataFrame({'field_id':['a'], 'start_date':['2020-01-01'], 'known_date':['2019-12-31']})
    obs = pd.DataFrame({'field_id':['a']*4, 'date':['2020-01-01','2020-01-02','2020-01-04','2020-01-06'],
                        'ndvi':[.1,.2,.3,.9]})
    d = online.prepare(obs, anchors, as_of='2020-01-06', bin_days=3, horizon_days=6)
    assert d['X'][0,:,0].tolist() == pytest.approx([.15,.6])
    obs.loc[3, 'ndvi'] = .1
    d2 = online.prepare(obs, anchors, as_of='2020-01-06', bin_days=3, horizon_days=6)
    assert d['X'][0,0,0] == d2['X'][0,0,0]
    anchors.loc[0, 'known_date'] = '2020-01-02'
    with pytest.raises(ValueError, match='available'):
        online.prepare(obs, anchors, as_of='2020-01-06', bin_days=3, horizon_days=6)


def test_causal_affiliation_and_feature_cli(tmp_path):
    pytest.importorskip('torch')
    rng = np.random.default_rng(7)
    x = rng.uniform(.2, .7, (6, 6, 2))
    starts = np.array(['2019-01-01']*2 + ['2022-01-01']*2 + ['2024-01-01']*2)
    ends = np.array(['2019-10-01']*2 + ['2022-10-01']*2 + ['2024-10-01']*2)
    path, out = tmp_path/'d.npz', tmp_path/'result.json'
    np.savez(path, X=x, start_dates=starts, end_dates=ends, field_ids=np.array(['a']*6))
    subprocess.run([sys.executable, str(ROOT/'scripts/validate_growth.py'), '--input', str(path),
                    '--output', str(out), '--band', '1', '--feature-bands', '1',
                    '--models', 'causal_gru', '--epochs', '1', '--affiliation', '--bootstrap', '5'], check=True)
    report = json.loads(out.read_text())
    assert report['protocol']['original_injection_band'] == 1
    model = report['models']['causal_gru']
    assert model['scoring_mode'] == 'causal_prefix'
    assert model['memory_profile']['sampled_peak_rss_bytes'] > 0
    assert model['scenarios'][0]['affiliation']['segments_with_truth'] > 0
