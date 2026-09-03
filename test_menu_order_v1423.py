from pathlib import Path
BASE=(Path(__file__).parent/'templates'/'base.html').read_text(encoding='utf-8')
APP=(Path(__file__).parent/'app.py').read_text(encoding='utf-8')
def test_v1423_version():
    assert 'APP_VERSION = "V1.4.29"' in APP
def test_room_before_tournament_menu():
    room = BASE.index('>🎮</span> Phòng đấu</a>')
    tournament = BASE.index('>🏟️</span> Giải đấu</a>')
    assert room < tournament
