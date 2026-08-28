from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_profile_arena_overview_release():
    assert 'APP_VERSION = "V1.4.16"' in read("app.py")


def test_arena_overview_composition_is_present():
    template = read("templates/profile.html")
    css = read("static/css/profile_showcase.css")
    required = (
        "profile-v2-lol-layout",
        "profile-v2-lol-identity",
        "profile-v2-lol-name-block",
        "profile-v2-lol-showcase",
        "profile-v2-lol-honor",
        "profile-v2-lol-mastery-row",
        "profile-v2-lol-mastery-node",
        "profile-v2-lol-rank-crest",
        "profile-v2-lol-actions",
    )
    for token in required:
        assert token in template
        assert token in css


def test_arena_overview_uses_existing_player_data_only():
    template = read("templates/profile.html")
    for token in (
        "player.display_name",
        "player.username",
        "player.rank_points",
        "player.rank_info",
        "player.position",
        "player.streak",
        "player.featured_achievement",
        "equipped_badge",
        "equipped_frame",
        "equipped_banner",
    ):
        assert token in template


def test_arena_overview_keeps_banner_uncropped():
    css = read("static/css/profile_showcase.css")
    assert ".profile-v2-banner-image" in css
    assert "object-fit:contain" in css
