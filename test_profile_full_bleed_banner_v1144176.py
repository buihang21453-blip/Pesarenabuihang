from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_profile_full_bleed_banner_release():
    assert 'APP_VERSION = "V1.4.4"' in read("app.py")


def test_equipped_banner_covers_the_complete_profile_hero():
    css = read("static/css/profile_showcase.css")
    assert ".profile-v2-hero.has-banner .profile-v2-banner-stage" in css
    assert "background-image:var(--profile-banner-image)" in css
    assert "background-size:cover" in css
    assert "background-position:center center" in css


def test_full_bleed_mode_keeps_existing_banner_markup_and_accessibility():
    template = read("templates/profile.html")
    css = read("static/css/profile_showcase.css")
    assert "--profile-banner-image:url(" in template
    assert 'class="profile-v2-banner-image"' in template
    assert ".profile-v2-hero.has-banner .profile-v2-banner-image" in css
    assert "opacity:0" in css


def test_full_bleed_banner_change_remains_profile_scoped():
    css = read("static/css/profile_showcase.css")
    assert "Scoped to .profile-v2-page" in css
    assert ".profile-v2-hero.has-banner" in css
