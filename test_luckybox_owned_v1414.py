from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
RANK=(ROOT/'templates/ranking.html').read_text(encoding='utf-8')
BASE=(ROOT/'templates/base.html').read_text(encoding='utf-8')
LB=(ROOT/'templates/luckybox/index.html').read_text(encoding='utf-8')
SERVICE=(ROOT/'modules/luckybox/service.py').read_text(encoding='utf-8')
SEASON=(ROOT/'modules/season_routes.py').read_text(encoding='utf-8')
SQL=(ROOT/'docs/update_luckybox_owned_v1_4_14.sql').read_text(encoding='utf-8')
JS=(ROOT/'static/js/luckybox_user.js').read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "V1.4.19"' in APP

def test_podium_always_rendered_even_empty():
    assert '{% if players %}' not in RANK.split('ranking-showcase',1)[0][-80:]
    assert "players[0].display_name if players|length > 0 else '---'" in RANK
    assert "players[1].display_name if players|length > 1 else '---'" in RANK
    assert "players[2].display_name if players|length > 2 else '---'" in RANK

def test_owned_luckybox_visible_global_and_page():
    assert 'topbar-luckybox' in BASE
    assert 'current_user.lucky_box_balance' in BASE
    assert 'Lucky Box sở hữu' in LB
    assert 'data-lb3-owned-boxes' in LB

def test_owned_box_allows_open_without_zcoin():
    assert 'owned_boxes > 0 or balance >= price' in SERVICE
    assert 'data-owned-boxes' in LB
    assert 'Dùng 1 Lucky Box đang sở hữu' in JS

def test_season_rewards_grant_real_owned_boxes_idempotently():
    assert "db.rpc('adjust_lucky_box_balance'" in SEASON
    assert "season:{sn}:rank:{pos}:luckybox" in SEASON
    assert 'lucky_box_balance_transactions' in SQL
    assert 'idempotency_key text not null unique' in SQL

def test_sql_backfills_and_consumes_owned_box_first():
    assert 'add column lucky_box_balance' in SQL
    assert "where lower(coalesce(status,''))='granted'" in SQL
    assert 'open_lucky_box_paid_core' in SQL
    assert "payment_method='owned_lucky_box'" in SQL
    assert "set lucky_box_balance=v_ticket_before-1" in SQL
