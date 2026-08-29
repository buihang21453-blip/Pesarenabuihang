from pathlib import Path
ROOT=Path(__file__).parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
ROUTES=(ROOT/'modules/season_routes.py').read_text(encoding='utf-8')

def test_version_v1411():
    assert 'APP_VERSION = "V1.4.19"' in APP

def test_historical_stats_are_rebuilt_from_matches():
    assert 'def _build_season_stats_map' in APP
    assert 'reconstructed_stats = _build_season_stats_map' in APP
    assert 'base["recent_form"]' in APP
    assert 'base["record_text"]' in APP

def test_future_snapshot_keeps_full_stats():
    assert '_build_season_stats_map(matches, season)' in ROUTES
    assert '"wins": int(stats.get' in ROUTES
    assert '"recent_form": list(stats.get' in ROUTES
