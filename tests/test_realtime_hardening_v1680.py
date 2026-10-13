from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read(path): return (ROOT / path).read_text(encoding='utf-8')

def test_version_and_realtime_allowlists():
    assert 'APP_VERSION = "V1.6.80"' in read('app.py')
    server = read('modules/realtime_events.py')
    js = read('static/js/pes_realtime.js')
    for event in ['INVITE_CHANGED','MATCH_FOUND','ROOM_ASSIGNED','CHAT_CHANGED','PLAYER_READY','ROOM_CHANGED']:
        assert event in server
        assert event in js

def test_realtime_is_signal_only_and_resyncs():
    server = read('modules/realtime_events.py')
    js = read('static/js/pes_realtime.js')
    room = read('templates/room_detail.html')
    assert 'json.dumps({"changed": True}' in server
    assert 'pes:realtime-resync' in js
    assert 'isRoomConnected' in room
    assert '__RESYNC__' in room
