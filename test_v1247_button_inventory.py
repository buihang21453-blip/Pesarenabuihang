from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def test_version_and_size_owner():
    assert 'APP_VERSION = "V1.2.47"' in read('app.py')
    base = read('templates/base.html')
    assert "css/button_sizes.css" in base
    sizes = read('static/css/button_sizes.css')
    assert 'min-height:40px' in sizes
    assert 'min-height:32px' in sizes
    assert 'min-height:44px' in sizes

def test_room_initial_and_live_use_same_neon_buttons():
    initial = read('templates/room_detail.html')
    live = read('templates/_room_live_content.html')
    for token in ['room-neon-gold', 'room-neon-green', 'room-neon-red', 'room-neon-gray']:
        assert token in initial
        assert token in live
    assert 'room-neon-label">Mời Đấu' in initial
    assert 'room-neon-label">Mời Đấu' in live
    assert 'room-neon-label">Thoát Phòng' in initial
    assert 'room-neon-label">Thoát Phòng' in live
