from pathlib import Path


def test_quick_match_requires_explicit_online_flag():
    source = Path("app.py").read_text(encoding="utf-8")
    assert 'opponent.get("is_online") is not True' in source
    assert 'quick_match_live_players' in source


def test_status_endpoint_also_rejects_offline_opponent():
    source = Path("app.py").read_text(encoding="utf-8")
    assert 'opponent.get("is_online") is not False' in source
    assert 'quick_match_cancel_offline_opponent' in source
