from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_required_root_operational_docs_remain_visible():
    for name in ("AGENTS.md", "PROJECT_MAP.md", "Log.md"):
        assert (ROOT / name).exists()


def test_operational_docs_are_centralized():
    base = ROOT / "project_docs"
    assert (base / "README.md").exists()
    assert (base / "FIX_NHANH_PES_ARENA.md").exists()
    assert (base / "LOGGING_GUIDE.md").exists()
    assert (base / "BLACKBOX_SAFETY_LAB.md").exists()


def test_sql_is_centralized_without_root_duplicates():
    sql_dir = ROOT / "project_docs" / "sql"
    assert (sql_dir / "20260808_blackbox.sql").exists()
    assert not list(ROOT.glob("*.sql"))
    assert not list((ROOT / "docs").glob("*.sql"))
    assert not (ROOT / "migrations").exists()


def test_no_local_image_assets_remain():
    exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico"}
    images = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    assert images == []
