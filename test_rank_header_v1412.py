from pathlib import Path

ROOT = Path(__file__).resolve().parent
RANKING = (ROOT / "templates" / "ranking.html").read_text(encoding="utf-8")
PUBLIC = (ROOT / "templates" / "public_ranking.html").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")

def test_version():
    assert 'APP_VERSION = "V1.4.22"' in APP

def test_ranking_header_order():
    for src in (RANKING, PUBLIC):
        assert src.index('PES eFOOTBALL 2026') < src.index('TOP 100 BẢNG XẾP HẠNG')
        assert src.index('TOP 100 BẢNG XẾP HẠNG') < src.index('ranking-showcase')
        assert 'SEASON {{ season.season_number }}' in src
        assert 'ranking-season-strip ranking-season-switcher' not in src
