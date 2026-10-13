from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_version_1683(): assert 'APP_VERSION = "V1.6.83"' in read('app.py')
def test_players_rpc_and_fallback():
    s=read('modules/dashboard_routes.py'); assert 'db_page_service.players_page' in s and 'invite_visible_players' in s and 'page_size = 30' in s
def test_bxh_rpc_and_historical_fallback():
    s=read('modules/ranking_routes.py'); assert 'db_page_service.leaderboard_page' in s and 'if not viewing_historical_season' in s and 'rank_season_snapshots' in s
def test_rpc_backend_only():
    s=read('SQL_CU/SQL_V1.6.83_PLAYERS_BXH_RPC.sql').lower(); assert 'revoke all on function public.pes_players_page' in s and 'to service_role' in s
def test_pagination_templates():
    assert 'total_pages' in read('templates/players.html'); assert 'total_pages' in read('templates/ranking.html')
def test_assets_not_bundled_as_raster_files():
    static=ROOT/'static'; assert not list(static.rglob('*.webp')) and not list(static.rglob('*.png')) and not list(static.rglob('*.jpg'))
