from pathlib import Path

APP = Path('app.py').read_text(encoding='utf-8')
REPO = Path('modules/core/match_repository.py').read_text(encoding='utf-8')
FORFEIT = Path('modules/forfeit_history_service.py').read_text(encoding='utf-8')
PROFILE = Path('modules/profile/service.py').read_text(encoding='utf-8')
HISTORY = Path('modules/match_history_routes.py').read_text(encoding='utf-8')


def test_release_version_and_match_repo_refresh_after_services():
    assert 'APP_VERSION = "1.3.73"' in APP
    assert '_core_match_repository.configure(globals())' in APP
    service_pos = APP.index('for _service_module in (')
    refresh_pos = APP.index('_core_match_repository.configure(globals())', service_pos)
    routes_pos = APP.index('from modules.match_history_routes import register_routes')
    assert service_pos < refresh_pos < routes_pos


def test_forfeit_helpers_are_exported_for_match_repository():
    for name in ('is_forfeit_match', 'forfeit_loser_id', 'forfeit_display_note'):
        assert f'"{name}"' in FORFEIT
        assert f'{name}(' in REPO


def test_history_and_profile_share_decorated_match_path():
    assert 'decorate_match_for_view(match, history_viewer_id)' in HISTORY
    assert 'decorate_match_for_view(match, user_id)' in PROFILE
    assert 'decorate_match_for_view(match, viewer_id)' in PROFILE
