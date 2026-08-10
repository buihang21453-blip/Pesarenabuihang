from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVICE = (ROOT / "modules" / "static_asset_service.py").read_text(encoding="utf-8")
ROOM = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
LIVE = (ROOT / "templates" / "_room_live_content.html").read_text(encoding="utf-8")
DYNAMIC = (ROOT / "templates" / "partials" / "room_dynamic_state.html").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")

def test_version_and_exact_v1340_room_paths():
    assert 'APP_VERSION = "V1.2.27"' in APP
    assert "v1.3.40/stadium-blue.webp" in ROOM
    assert "v1.3.40/stadium-red.webp" in ROOM
    assert "v1.3.40/room-texture-dark.webp" in ROOM
    assert "v1.3.40/pes-arena-room-logo.webp" in ROOM

def test_mode_logos_stay_on_confirmed_v1340_branch():
    for i in range(1, 7):
        assert f"v1.3.40/modes/{i}.webp" in ROOM
    assert "_confirmed_v1340_url" in SERVICE

def test_vs_filename_is_case_exact():
    combined = ROOM + LIVE + DYNAMIC
    assert "asset_url('VS.webp')" in combined
    assert "asset_url('vs.webp')" not in combined
