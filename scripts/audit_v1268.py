from pathlib import Path
import ast, compileall, sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def check(name, ok, details=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{(': ' + details) if details else ''}")
    return bool(ok)


def main():
    results = []
    results.append(check("Compile toàn bộ Python", compileall.compile_dir(ROOT, quiet=1)))
    for rel in [
        "app.py",
        "modules/room_access_routes.py",
        "modules/room_result_routes.py",
        "modules/room_rematch_routes.py",
        "modules/room_team_routes.py",
        "modules/match_result_service.py",
    ]:
        try:
            ast.parse(read(rel))
            results.append(check(f"AST {rel}", True))
        except SyntaxError as exc:
            results.append(check(f"AST {rel}", False, str(exc)))

    app = read("app.py")
    result_routes = read("modules/room_result_routes.py")
    result_service = read("modules/match_result_service.py")
    access = read("modules/room_access_routes.py")
    rematch = read("modules/room_rematch_routes.py")
    full = read("templates/room_detail.html")
    live = read("templates/_room_live_content.html")
    css = read("static/css/room_v2.css")

    confirm_block = result_routes.split("def room_confirm_result", 1)[1].split("def room_dispute_result", 1)[0]
    exit_block = result_routes.split("def room_post_result_exit", 1)[1].split("def room_confirm_result", 1)[0]
    leave_block = access.split("def room_leave", 1)[1]

    results += [
        check("Version V1.2.68", 'APP_VERSION = "V1.2.68"' in app),
        check("Xác nhận kết thúc ở confirmed", '"status": "confirmed"' in confirm_block),
        check("Không còn mã CONFIRM trong route xác nhận", '_result_error_id("CONFIRM")' not in confirm_block),
        check("Thoát sau kết quả không tính/lưu RP", "apply_match_result" not in exit_block),
        check("Có snapshot người chơi trước khi ghi RP", "_result_player_snapshot" in result_service),
        check("Có rollback cả hai người chơi", "_restore_result_player_snapshot(snapshot1)" in result_service and "_restore_result_player_snapshot(snapshot2)" in result_service),
        check("Rời phòng sau kết quả luôn về sảnh an toàn", '{"waiting_result_confirm", "disputed", "confirmed"}' in leave_block),
        check("Rematch chỉ dùng sau confirmed", 'room["status"] != "confirmed"' in rematch),
        check("Full template có nút Sẵn Sàng", "room_guest_ready" in full and "room-ready-actions" in full),
        check("Live polling có nút Sẵn Sàng", "room_guest_ready" in live and "room-ready-actions" in live),
        check("CSS cuối cùng không ghim absolute nút Ready", "V1.2.68 — READY ACTIONS FINAL LAYOUT" in css and "position:relative !important" in css),
        check("CSS Ready luôn visible", "visibility:visible !important" in css and "opacity:1 !important" in css),
    ]
    passed = sum(results)
    print(f"\nKẾT QUẢ: {passed}/{len(results)} kiểm tra PASS")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
