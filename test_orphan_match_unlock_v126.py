from pathlib import Path

APP = Path("app.py").read_text(encoding="utf-8")
FORFEIT = Path("modules/forfeit_history_service.py").read_text(encoding="utf-8")


def test_version_v126():
    assert 'APP_VERSION = "V1.3.14"' in APP


def test_orphan_match_does_not_block_new_room():
    assert "def match_blocks_new_room(match, linked_room=None):" in APP
    assert "return bool(linked_room and room_is_active(linked_room))" in APP
    assert "rooms_by_match = _room_by_match_id(rooms)" in APP
    assert "if match_blocks_new_room(match, linked_room):" in APP


def test_forfeit_clears_all_match_cache_layers():
    assert 'ttl_cache_delete("matches_raw")' in FORFEIT
