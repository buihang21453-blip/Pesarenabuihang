"""GĐ2 countdown occupies the old media overlay without a second clock."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
ROOT = Path(__file__).resolve().parents[1]

def test_one_clock_in_media_and_no_old_ready_banner():
    media = (ROOT/'templates/tournament/cards/c1_media.html').read_text()
    header = (ROOT/'templates/tournament/cards/c1_header_nav.html').read_text()
    scripts = (ROOT/'templates/tournament/scripts/page_scripts.html').read_text()
    assert media.count('data-c1-gd2-clock') == 1
    assert 'tournament-progress-overlay c1-gd2-clock' in media
    assert 'data-c1-gd2-clock' not in header
    assert 'data-gd2-ceremony-card' not in media + scripts
    assert 'GĐ2 SẴN SÀNG MỞ' not in media + scripts
    assert 'data-start="{{ tournament.league_start_at or' in media
    assert 'data-end="{{ tournament.league_end_at or' in media

def test_clock_rendered_inside_banner_with_times():
    env=Environment(loader=FileSystemLoader(str(ROOT/'templates')))
    tmpl=env.get_template('tournament/cards/c1_media.html')
    data=dict(status='ongoing',club_draw_at=None,league_start_at='2026-09-18T12:00:00+07:00',league_end_at='2026-09-25T12:00:00+07:00',league_start_label='12:00 · 18/09/2026',league_end_label='12:00 · 25/09/2026')
    result=tmpl.render(tournament=data)
    assert result.count('data-c1-gd2-clock')==1
    assert '12:00 · 18/09/2026' in result and '12:00 · 25/09/2026' in result
    assert result.count('data-gd2-d>')==1
