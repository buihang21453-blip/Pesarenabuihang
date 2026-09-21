"""Regression checks for the public C1 GĐ2 countdown (V1.6.49)."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]


def test_clock_reads_persisted_dates_and_shows_both_labels():
    env = Environment(loader=FileSystemLoader(str(ROOT / 'templates')))
    tmpl = env.from_string(env.loader.get_source(env, 'tournament/cards/c1_media.html')[0])
    tournament = dict(room_code='ABC', member_count=16, phase_name='GĐ2', stage1_start_label=None,
                      registration_open=False, status='ongoing', stage1_start_at=None, show_stage1_start_countdown=False,
                      league_start_at='2026-09-18T12:00:00+07:00', league_end_at='2026-09-25T12:00:00+07:00',
                      league_start_label='12:00 · 18/09/2026', league_end_label='12:00 · 25/09/2026')
    html = tmpl.render(tournament=tournament)
    assert 'data-start="2026-09-18T12:00:00+07:00"' in html
    assert 'data-end="2026-09-25T12:00:00+07:00"' in html
    assert 'Khởi tranh:' in html and 'Kết thúc:' in html
    assert 'tournament-progress-overlay c1-gd2-clock' in html
    assert all(f'data-gd2-{unit}' in html for unit in 'dhms')


def test_missing_end_is_not_silently_invented():
    text = (ROOT / 'modules/tournament_routes.py').read_text()
    template = (ROOT / 'templates/tournament/cards/c1_media.html').read_text()
    assert 'item["league_end_at"] = timing.get("league_end_at")' in text
    assert "tournament.league_end_label or 'Chưa thiết lập'" in template
    js = (ROOT / 'templates/tournament/scripts/page_scripts.html').read_text()
    assert "caption='Chưa thiết lập hạn kết thúc GĐ2'" in js
    assert "phase='upcoming';target=start" in js
    assert "phase='active';target=end" in js
    assert "phase='ended';target=end" in js
