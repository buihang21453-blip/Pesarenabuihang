from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_version_v144():
    assert 'APP_VERSION = "V1.4.4"' in APP


def test_invite_page_uses_same_invisible_visibility_policy_as_players_page():
    assert 'invisible_ids = get_invisible_player_ids()' in APP
    assert 'all_players = filter_players_for_viewer(list_players(), user, invisible_ids)' in APP
    assert 'if str(player.get("id")) != str(user.get("id")) and player.get("is_online")' in APP


def test_invisible_viewer_can_see_all_players_in_visibility_helper():
    assert 'if viewer_id and viewer_id in ids:' in APP
    assert 'return True' in APP[APP.index('if viewer_id and viewer_id in ids:'):APP.index('def filter_players_for_viewer')]

if __name__ == "__main__":
    test_version_v144()
    test_invite_page_uses_same_invisible_visibility_policy_as_players_page()
    test_invisible_viewer_can_see_all_players_in_visibility_helper()
