from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_profile_empty_banner_clean_release():
    assert 'APP_VERSION = "V1.4.17"' in read("app.py")


def test_profile_without_banner_has_no_center_placeholder_words():
    template = read("templates/profile.html")
    empty_banner = '<div class="profile-v2-default-banner" aria-hidden="true"></div>'
    assert empty_banner in template
    assert '<span class="profile-v2-default-mark">PES ARENA</span>' not in template
    assert '<strong>BẢN LĨNH SÂN CỎ</strong>' not in template
    assert '<small>HỒ SƠ CẦU THỦ</small>' not in template


def test_empty_banner_caption_and_player_identity_are_preserved():
    template = read("templates/profile.html")
    assert "'TRANG CÁ NHÂN'" in template
    assert "'Chưa trang bị banner'" in template
    assert 'class="profile-v2-lol-identity"' in template
    assert 'class="profile-v2-lol-showcase"' in template


def test_empty_banner_placeholder_hide_rule_is_profile_scoped():
    css = read("static/css/profile_showcase.css")
    assert ".profile-v2-hero.has-default-banner .profile-v2-default-mark" in css
    assert ".profile-v2-hero.has-default-banner .profile-v2-default-banner>strong" in css
    assert "display:none!important" in css
