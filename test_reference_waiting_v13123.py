from pathlib import Path
import re

ROOT = Path(__file__).parent

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def test_version_and_authoritative_css():
    assert 'APP_VERSION = "1.3.123"' in read('app.py')
    room = read('templates/room_detail.html')
    assert '26-reference-layout-waiting-v123.css' in room
    assert '25-full-mockup-v122.css' not in room

def test_reference_shell_structure():
    room = read('templates/room_detail.html')
    assert 'class="room-reference-body"' in room
    assert 'class="room-reference-main"' in room
    assert 'room/_waiting_opponent_actions.html' in room
    # side rail must be outside the 3-card match shell so it can span actions + mode row
    shell_end = room.index('</div>{# /.room-arena-frame #}')
    rail_pos = room.index('room/_side_rail.html')
    assert rail_pos > shell_end

def test_waiting_opponent_has_no_host_club_and_true_empty_guest():
    host = read('templates/room/_host_card.html')
    guest = read('templates/room/_guest_card.html')
    assert "room.status == 'waiting_ready' and not room.has_guest" in host
    assert 'room-host-no-team' in host
    assert 'CLB sẽ được xác định sau khi có đối thủ' in host
    assert '{% if not room.has_guest %}' in guest
    assert 'room-empty-opponent' in guest
    assert 'Chưa có đối thủ' in guest

def test_waiting_actions_keep_real_routes():
    action = read('templates/room/_waiting_opponent_actions.html')
    for endpoint in ['players', 'quick_match_invite', 'room_leave']:
        assert f"url_for('{endpoint}'" in action
    center = read('templates/room/_center_stage.html')
    no_guest = center.split('{% else %}')[-1]
    assert 'room-center-vs-image' in no_guest

def test_polling_reuses_same_partials():
    live = read('templates/_room_live_content.html')
    assert 'id="roomLiveShell"' in live
    for partial in [
        'room/_host_card.html', 'room/_center_stage.html', 'room/_guest_card.html',
        'room/_waiting_opponent_actions.html', 'room/_bottom_modes_history.html', 'room/_side_rail.html'
    ]:
        assert partial in live

def test_mode_number_mapping_and_labels():
    center = read('templates/room/_center_stage.html')
    assert "'tactical_bo3':3" in center
    assert "'ban_pick_bo3':5" in center
    assert "'home_away':6" in center
    modes = read('templates/room/_bottom_modes_history.html')
    for text in ['Rank thường Random','Random 3 chọn 1','Đấu chiến thuật BO3','Cấm chọn CLB','Lượt đi - Lượt về']:
        assert text in modes

def test_reference_geometry_tokens_exist():
    css = read('static/css/room/26-reference-layout-waiting-v123.css')
    assert 'grid-template-columns:minmax(0,1fr) 374px' in css
    assert 'grid-template-rows:500px 58px 228px' in css
    assert 'height:500px' in css
    assert 'grid-template-columns:repeat(6,minmax(0,1fr))' in css
    assert 'height:806px' in css
