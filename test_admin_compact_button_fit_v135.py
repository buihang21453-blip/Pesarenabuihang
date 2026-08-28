from pathlib import Path

ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CSS = (ROOT / "static/style.css").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")


def test_version_is_v135():
    assert 'APP_VERSION = "V1.4.12"' in APP


def test_admin_target_sections_use_content_sized_buttons():
    marker = "PES Arena V1.3.6 — Admin action buttons hug their text"
    assert marker in CSS
    block = CSS[CSS.index(marker):]
    assert 'width:fit-content!important' in block
    assert 'height:fit-content!important' in block
    assert 'block-size:fit-content!important' in block
    assert 'align-self:center!important' in block
    assert 'justify-self:start!important' in block


def test_rank_limit_button_remains_simple_submit_button():
    assert '<button class="btn" type="submit">Lưu giới hạn Rank</button>' in ADMIN
    assert 'class="system-toggle-grid"' in ADMIN
