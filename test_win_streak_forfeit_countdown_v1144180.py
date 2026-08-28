from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
RESULT = (ROOT / "modules" / "match_result_service.py").read_text(encoding="utf-8")
REBUILD = (ROOT / "modules" / "admin_ranking_rebuild.py").read_text(encoding="utf-8")
FORFEIT = (ROOT / "modules" / "room_rematch_routes.py").read_text(encoding="utf-8")
ROOM = (ROOT / "templates" / "partials" / "room_dynamic_state.html").read_text(encoding="utf-8")


def test_version_and_timeout_stay_60_seconds():
    assert 'APP_VERSION = "V1.4.7"' in APP
    assert 'RESULT_CONFIRM_TIMEOUT_SECONDS = 60' in APP


def test_draw_resets_live_and_rebuilt_win_streak():
    assert 'new_streak = current_streak + 1 if win else 0' in RESULT
    assert 'state["streak"] = 0' in REBUILD
    assert 'Hòa làm gián đoạn chuỗi thắng liên tiếp' in REBUILD


def test_forfeit_awards_statistical_win_without_rp():
    assert 'def _award_forfeit_win(winner_id)' in FORFEIT
    assert '"wins": wins' in FORFEIT
    assert '"streak": streak' in FORFEIT
    assert '"rank_points"' not in FORFEIT.split('def _award_forfeit_win', 1)[1].split('@app.route', 1)[0]
    assert '_award_forfeit_win(room.get("host_user_id"))' in FORFEIT
    assert '_award_forfeit_win(room.get("guest_user_id"))' in FORFEIT


def test_confirmation_countdown_is_visible():
    assert 'id="roomCountdown"' in ROOM
    assert 'Tự động xác nhận sau' in ROOM
    assert 'data-seconds="{{ room.timeout_seconds }}"' in ROOM
