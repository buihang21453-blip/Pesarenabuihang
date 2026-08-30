from pathlib import Path
ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
WEEKLY = (ROOT / "static" / "css" / "admin_weekly_rewards.css").read_text(encoding="utf-8")

def test_version_and_content_fingerprint_pipeline():
    assert 'APP_VERSION = "V1.4.27"' in APP
    assert "def static_asset(filename):" in APP
    assert "hashlib.sha256" in APP
    assert "static_asset('style.css')" in BASE

def test_weekly_css_is_scoped_and_not_duplicated():
    assert 'body[data-page="admin"] .weekly-rp-two-column' in WEEKLY
    assert "!important" not in WEEKLY
    assert "Weekly RP: inline critical CSS" not in ADMIN
    assert "admin_weekly_rewards.css" in BASE
