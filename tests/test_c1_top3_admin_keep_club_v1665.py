from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_admin_keep_button_is_visible_only_in_admin_branch():
    html=(ROOT/'templates/tournament/components/knockout_dashboard.html').read_text(encoding='utf-8')
    assert 'admin_tournament_league_top3_keep_club_for' in html
    assert '✅ Admin chọn giữ {{ t.club }} · Không dùng vé' in html
    assert "ko_viewer_is_admin and t.remaining|int > 0" in html

def test_admin_keep_route_uses_same_keep_helper_without_ticket_spend():
    src=(ROOT/'modules/tournament_competition_parts/rewards.py').read_text(encoding='utf-8')
    assert "@app.post('/admin/tournaments/<tournament_id>/league-top3/keep-club-for')" in src
    assert 'return _league_top3_keep_current_club(tournament_id,uid,admin_actor=admin_uid)' in src
    section=src[src.index('def _league_top3_keep_current_club'):src.index('def _admin_undo_league_top3_reroll')]
    assert 'ticket_spent":False' in section
    assert 'actor_role="admin" if admin_actor else "player"' in section
