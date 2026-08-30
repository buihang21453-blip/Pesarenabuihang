from pathlib import Path

HTML = Path('templates/tournaments.html').read_text()
APP = Path('app.py').read_text()


def test_version_and_tournament_assets():
    assert 'APP_VERSION = "V1.4.27"' in APP
    for asset in ('Nengiaidau.webp', 'Cupnen.webp', 'NenC1arena.webp', 'Huyhieu.webp'):
        assert f'/Giaidau/C1mua1/{asset}' in HTML
    assert 'is-c1-arena' in HTML
