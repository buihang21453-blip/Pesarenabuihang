from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "static" / "style.css"
ROOM = ROOT / "static" / "css" / "room_detail.css"
BASE = ROOT / "templates" / "base.html"

checks = []
style = STYLE.read_text(encoding="utf-8")
room = ROOM.read_text(encoding="utf-8")
base = BASE.read_text(encoding="utf-8")

checks.append(("room_detail.css tồn tại", ROOM.exists()))
checks.append(("room_detail.css chỉ được khai báo dưới endpoint room_detail", "request.endpoint == 'room_detail'" in base and "css/room_detail.css" in base))
checks.append(("style.css không còn khối Room redesign v1.10.0", "Room redesign v1.10.0" not in style))
checks.append(("Room redesign đã chuyển sang module Room", "Room redesign v1.10.0" in room))
checks.append(("Arena V1.13.7 đã chuyển sang module Room", "Collap_V1.13.7" in room))
checks.append(("Quick Match vẫn là module riêng", (ROOT / "static/css/quick_match.css").exists()))
checks.append(("Parsec vẫn là module riêng", (ROOT / "static/css/parsec_room.css").exists()))
checks.append(("Rank Mode vẫn là module riêng", (ROOT / "static/css/rank_mode_toggle.css").exists()))

bad = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + " - " + name)
print(f"\nKết quả: {len(checks)-len(bad)}/{len(checks)} PASS")
raise SystemExit(1 if bad else 0)
