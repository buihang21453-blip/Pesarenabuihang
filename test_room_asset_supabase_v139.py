from pathlib import Path

ROOT = Path(__file__).parent

def test_room_assets_are_remote_only():
    assert not (ROOT / "UPLOAD_SUPABASE").exists()
    assert not (ROOT / "static" / "assets" / "room_v2").exists()

def test_room_asset_helper_has_verified_supabase_default():
    text = (ROOT / "modules" / "static_asset_service.py").read_text(encoding="utf-8")
    assert "DEFAULT_ROOM_ASSET_BASE_URL" in text
    assert "pes-assets/room-assets/v1.3.18" in text
    assert "def room_asset_url" in text

def test_room_template_uses_helper():
    text = (ROOT / "templates" / "room_detail.html").read_text(encoding="utf-8")
    assert "room_asset(" in text
