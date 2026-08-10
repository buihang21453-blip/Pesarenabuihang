from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_version_and_neon_button_owner():
    assert 'APP_VERSION = "V1.2.46"' in read("app.py")
    css = read("static/css/room_v2.css")
    assert ".room-v2-shell .room-neon-btn{" in css
    assert "V1.2.43 - Cum nut chinh Neon can doi" not in css
    assert "3 nut dung cung mot ngon ngu thiet ke Neon" not in css
    assert "3 nut: cung nen, vien, bo goc" not in css

def test_room_buttons_use_isolated_neon_classes():
    html = read("templates/_room_live_content.html")
    assert "room-neon-gold" in html
    assert "room-neon-green" in html
    assert "room-neon-red" in html
    assert 'room-neon-label">Mời Đấu' in html
    assert 'room-neon-label">Sẵn Sàng' in html
    assert 'room-neon-label">Thoát Phòng' in html
