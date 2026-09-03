from pathlib import Path

APP=Path("app.py").read_text()
TPL=Path("templates/tournaments.html").read_text()
ADMIN=Path("templates/admin.html").read_text()
ROUTES=Path("modules/tournament_routes.py").read_text()

def test_version():
    assert 'APP_VERSION = "V1.4.29"' in APP

def test_new_badge_and_card_layout():
    assert 'Huyhieu.webp' in TPL
    assert 'tournament-card-media' in TPL
    assert 'PES Arena Champions League' in TPL
    assert 'tournament-arena-badge' in TPL

def test_admin_image_controls():
    for key in ['hero_cup_width','hero_cup_right','hero_cup_bottom','arena_badge_width','arena_badge_x','arena_badge_y']:
        assert key in ADMIN
        assert key in ROUTES
    assert "admin_tournament_design" in ROUTES
