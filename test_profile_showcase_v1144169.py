from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_profile_v2_release_version():
    assert 'APP_VERSION = "V1.4.21"' in read("app.py")


def test_profile_v2_isolated_assets_and_complete_banner():
    template = read("templates/profile.html")
    css = read("static/css/profile_showcase.css")
    assert 'class="profile-v2-page"' in template
    assert 'class="profile-v2-banner-image"' in template
    assert 'src="{{ equipped_banner.image_url }}"' in template
    assert "object-fit:contain" in css
    assert ".profile-v2-page" in css
    assert "--profile-banner-image" in template
    assert "css/profile_showcase.css" in template
    assert "js/profile_showcase.js" in template
    assert template.count("static_asset(") >= 3


def test_profile_v2_has_showcase_tabs_and_owner_controls():
    template = read("templates/profile.html")
    script = read("static/js/profile_showcase.js")
    for token in (
        'data-profile-tab="overview"',
        'data-profile-tab="achievements"',
        'data-profile-tab="matches"',
        'data-profile-tab="settings"',
        'data-profile-panel="overview"',
        "BỘ SƯU TẬP ĐANG TRANG BỊ",
        "HÀNH TRÌNH XẾP HẠNG",
        "Quản lý trang bị",
        "Cửa hàng",
        "data-profile-share",
        "update_parsec_id",
        "update_display_name",
        "update_profile_avatar",
        "change_password",
    ):
        assert token in template
    assert "activateTab" in script
    assert "navigator.clipboard" in script
    assert "Đã sao chép liên kết" in script


def test_profile_v2_does_not_touch_other_page_selectors():
    css = read("static/css/profile_showcase.css")
    assert "Scoped to .profile-v2-page" in css
    assert ".profile-v2-page .history-card" in css
    assert ".profile-v2-page .achievement-card" in css
