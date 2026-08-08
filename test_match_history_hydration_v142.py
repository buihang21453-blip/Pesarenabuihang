from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
MATCHES = Path('templates/matches.html').read_text(encoding='utf-8')
PROFILE = Path('templates/profile.html').read_text(encoding='utf-8')
CSS = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in Path('static/css').rglob('*.css'))


def test_version_and_hydration_guard_present():
    assert 'APP_VERSION = "1.3.42"' in APP
    assert 'def hydrate_match_player_fields(match):' in APP
    assert 'hydrate_match_player_fields(item)' in APP
    assert 'player.get("display_name") or player.get("username") or "Unknown"' in APP


def test_targeted_read_model_is_kept():
    assert 'load_user_matches(user.get("id"), limit=30)' in APP
    assert 'load_user_matches' in Path('modules/profile/service.py').read_text(encoding='utf-8')


def test_history_templates_render_hydrated_fields():
    assert '{{ m.left_player_name }}' in MATCHES
    assert '{{ m.right_player_name }}' in MATCHES
    assert '{{ m.left_player_name }}' in PROFILE
    assert '{{ m.right_player_name }}' in PROFILE


def test_css_does_not_inject_none_text():
    assert 'content:"None"' not in CSS
    assert "content:'None'" not in CSS
