from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_v145_invite_surfaces_force_refresh_invisible_setting():
    assert 'APP_VERSION = "V1.4.15"' in APP
    assert 'def invite_visible_players' in APP
    assert 'get_invisible_player_ids(force=force_invisible_refresh)' in APP
    assert 'invite_visible_players(current_user(), include_admin=True, force_invisible_refresh=True)' in APP
    assert 'invite_visible_players(user, include_admin=False, force_invisible_refresh=True)' in APP


def test_invisible_viewer_bypasses_player_filter():
    assert 'if viewer_id and viewer_id in ids:\n        return list(players or [])' in APP

if __name__ == "__main__":
    test_v145_invite_surfaces_force_refresh_invisible_setting()
    test_invisible_viewer_bypasses_player_filter()
