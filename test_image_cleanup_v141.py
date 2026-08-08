from pathlib import Path
ROOT = Path(__file__).parent

def test_old_local_mode_logos_removed():
    assert not (ROOT / "static/assets/room_v2/modes").exists()
    assert not (ROOT / "static/assets/room_v2/emblems").exists()

def test_old_upload_mode_logos_removed():
    base = ROOT / "UPLOAD_SUPABASE/UPLOAD_VAO_BUCKET_pes-assets/room-assets/v1.3.18"
    assert not (base / "modes").exists()
    assert not (base / "emblems").exists()

def test_unused_trophies_removed():
    for name in ("trophy_gold.svg", "trophy_silver.svg", "trophy_bronze.svg"):
        assert not (ROOT / "static" / name).exists()

def test_v140_mode_upload_folder_stays_empty():
    p = ROOT / "pes-assets/room-assets/v1.3.40/modes"
    assert p.is_dir()
    assert list(p.iterdir()) == []

def test_mode_helper_points_only_to_supabase_v140():
    text=(ROOT / "modules/static_asset_service.py").read_text(encoding="utf-8")
    assert "pes-assets/room-assets/v1.3.40/modes" in text
    assert "assets/room_v2/modes/{filename}" not in text
