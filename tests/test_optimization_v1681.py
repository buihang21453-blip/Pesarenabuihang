from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read(rel): return (ROOT / rel).read_text(encoding='utf-8')

def test_tournament_host_ready_realtime_and_sparse_fallback():
    js = read('static/js/pes_realtime.js')
    page = read('templates/tournament/scripts/page_scripts.html')
    events = read('modules/realtime_events.py')
    assert 'TOURNAMENT_CHANGED' in js and 'subscribeTournament' in js
    assert '"tournament": {"TOURNAMENT_CHANGED"' in events
    assert '90000' in page
    assert 'setInterval(refreshAll,15000)' not in page

def test_global_chat_realtime_signal():
    service = read('modules/legacy_chat_service.py')
    base = read('templates/base.html')
    assert 'GLOBAL_CHAT_CHANGED' in service
    assert 'pes:realtime-global-event' in base
    assert '? 180000 : 45000' in base

def test_ranking_hot_query_not_select_star():
    ranking = read('modules/ranking_routes.py')
    assert 'select("user_id,rank_points,wins,draws,losses,total_matches,recent_form,final_rank,username,display_name")' in ranking
