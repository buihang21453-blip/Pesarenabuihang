from pathlib import Path
root = Path(__file__).parent
app = (root/'app.py').read_text(encoding='utf-8')
admin_room = (root/'modules/admin_data_routes.py').read_text(encoding='utf-8')
admin_match = (root/'modules/admin_match_routes.py').read_text(encoding='utf-8')
assert 'RESULT_CONFIRM_TIMEOUT_SECONDS = 12 * 60 * 60' in app
assert 'auto_confirm_expired_match_if_needed' in app
assert 'apply_match_result(dict(match))' in app
assert 'close_room_with_timeout_penalty' not in app[app.index('# Đã nhập tỷ số nhưng chưa xác nhận'):app.index('# Giao hữu hoặc phòng chưa bắt đầu')]
block = admin_room[admin_room.index('def admin_cancel_room'):admin_room.index('@app.route("/admin/invite')]
assert 'db.table("matches").update' not in block
assert 'không sửa trạng thái trận' in block
assert 'old_status == "disputed" and new_status == "confirmed"' in admin_match
print('7/7 checks passed')
