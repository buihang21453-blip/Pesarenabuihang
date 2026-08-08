from pathlib import Path

html = Path('templates/room_detail.html').read_text(encoding='utf-8')
css = Path('static/css/arena_room_v2.css').read_text(encoding='utf-8')

required_routes = [
    'room_guest_ready', 'room_guest_unready', 'room_leave',
    'room_guest_forfeit', 'room_host_forfeit', 'room_submit_result'
]
for route in required_routes:
    assert route in html, route
for label in ['Sẵn Sàng', 'Thoát Phòng', 'Gửi Kết Quả']:
    assert label in html, label
assert 'V1.3.19 — keep state-dependent room actions visible' in css
assert '.room-center-stage-plain > .room-center-score-panel' in css
assert 'position: absolute;' in css
print('room action visibility v1.3.19: OK')
