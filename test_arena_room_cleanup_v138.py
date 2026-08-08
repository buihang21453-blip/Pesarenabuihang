from pathlib import Path

ROOT = Path(__file__).resolve().parent
html = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
css = (ROOT / "static/css/arena_room_v2.css").read_text(encoding="utf-8")

assert "room-center-primary-actions-three" in html
assert "room-quick-match-row" not in html
assert ":has(.room-quick-match-row)" not in css
assert not (ROOT / "static/css/room_master.css").exists()
assert not (ROOT / "static/icons/rank_modes").exists()
assert not (ROOT / "static/assets/room_v2/source_user_logo").exists()
assert not (ROOT / "static/assets/room_v2").exists()
service = (ROOT / "modules/static_asset_service.py").read_text(encoding="utf-8")
assert "room-assets/v1.3.18" in service
assert "room-assets/v1.3.40/modes" in service
print("V1.3.62 room UI remote asset cleanup: PASS")
