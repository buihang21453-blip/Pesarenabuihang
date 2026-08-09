from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_invite_presence_modules_exist():
    assert (ROOT / "modules/invites/service.py").exists()
    assert (ROOT / "modules/presence/service.py").exists()


def test_result_flow_finishes_confirmed():
    text = (ROOT / "modules/room_result_routes.py").read_text(encoding="utf-8")
    assert '"status": "confirmed"' in text
    assert "confirm_result_finish_room" in text


def test_rp_rollback_snapshot_exists():
    text = (ROOT / "modules/match_result_service.py").read_text(encoding="utf-8")
    assert "_restore_player_snapshot" in text
    assert "player1_applied" in text and "player2_applied" in text


def test_app_version():
    assert 'APP_VERSION = "V1.2.11"' in (ROOT / "app.py").read_text(encoding="utf-8")
