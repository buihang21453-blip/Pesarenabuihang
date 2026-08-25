from pathlib import Path

ROOT = Path(__file__).parent
CSS = (ROOT / "static/style.css").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin.html").read_text(encoding="utf-8")


def test_three_requested_admin_tabs_exist():
    for tab in ("test-data", "system", "rp-tools"):
        assert f'data-admin-tab="{tab}"' in ADMIN
        assert f'data-admin-panel="{tab}"' in ADMIN


def test_requested_admin_areas_have_compact_scoped_buttons():
    assert 'data-admin-panel="test-data"] .btn' in CSS
    assert 'data-admin-panel="system"] .btn' in CSS
    assert 'data-admin-panel="rp-tools"] .btn' in CSS
    assert 'min-height:34px!important' in CSS
    assert 'width:auto!important' in CSS
    assert 'padding:7px 12px!important' in CSS


def test_test_import_primary_action_is_no_longer_full_width():
    assert 'data-admin-panel="test-data"] .admin-primary-action' in CSS
    assert 'width:auto!important' in CSS

if __name__ == "__main__":
    test_three_requested_admin_tabs_exist()
    test_requested_admin_areas_have_compact_scoped_buttons()
    test_test_import_primary_action_is_no_longer_full_width()
