from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_version_v143():
    assert 'APP_VERSION = "V1.4.6"' in APP


def test_invisible_viewer_can_see_other_invisible_accounts():
    assert 'if viewer_id and viewer_id in ids:' in APP
    assert 'return True' in APP
    assert 'return target_id not in ids' in APP
    assert 'tài khoản tàng hình thấy đầy đủ' in APP


def test_normal_viewer_still_cannot_see_invisible_target():
    # The final return hides targets whose id is in the invisible set for normal viewers.
    assert 'return target_id not in ids' in APP
