from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_profile_identity_release_has_moved_forward():
    app = read("app.py")
    assert 'APP_VERSION = "V1.4.8"' in app


def test_profile_identity_remains_scoped_and_complete():
    template = read("templates/profile.html")
    css = read("static/css/profile_showcase.css")
    for token in (
        "profile-v2-lol-layout",
        "profile-v2-lol-identity",
        "profile-v2-lol-avatar",
        "profile-v2-lol-name-row",
        "profile-v2-lol-showcase",
        "profile-v2-lol-mastery-row",
        "profile-v2-lol-rank",
        "PES ARENA PROFILE",
    ):
        assert token in template or token in css
    assert "object-fit:contain" in css
    assert "Scoped to .profile-v2-page" in css


def test_profile_identity_keeps_existing_profile_features():
    template = read("templates/profile.html")
    for token in (
        'data-profile-tab="overview"',
        'data-profile-tab="achievements"',
        'data-profile-tab="matches"',
        'data-profile-tab="settings"',
        "Quản lý trang bị",
        "Cửa hàng",
        "data-profile-share",
        "update_parsec_id",
        "update_display_name",
        "update_profile_avatar",
        "change_password",
    ):
        assert token in template
