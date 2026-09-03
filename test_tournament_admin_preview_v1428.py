from pathlib import Path

ADMIN = Path('templates/admin.html').read_text(encoding='utf-8')
JS = Path('static/js/tournament_admin_preview.js').read_text(encoding='utf-8')
CSS = Path('static/css/admin_dashboard.css').read_text(encoding='utf-8')
APP = Path('app.py').read_text(encoding='utf-8')

def test_version_v1428():
    assert 'APP_VERSION = "V1.4.29"' in APP

def test_only_foreground_assets_have_controls():
    assert 'Ảnh Cúp Giải đấu' in ADMIN
    assert 'Ảnh Huy hiệu C1' in ADMIN
    assert 'name="hero_cup_width"' in ADMIN
    assert 'name="arena_badge_width"' in ADMIN
    assert 'name="hero_banner_width"' not in ADMIN
    assert 'name="arena_banner_width"' not in ADMIN

def test_live_preview_exists():
    assert 'Preview trực quan' in ADMIN
    assert 'preview-hero-cup' in ADMIN
    assert 'preview-arena-badge' in ADMIN
    assert 'Nengiaidau.webp' in CSS
    assert 'NenC1arena.webp' in CSS
    assert 'tournament_admin_preview.js' in ADMIN
    assert "addEventListener('input',update)" in JS
