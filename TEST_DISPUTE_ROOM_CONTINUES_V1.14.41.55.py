from pathlib import Path
src = Path('modules/room_result_routes.py').read_text(encoding='utf-8')
assert '"status": "waiting_ready"' in src
assert '"match_id": None' in src
assert '.eq("status", "waiting_result_confirm")' in src
assert '"status": "disputed"' in src
assert 'room_dispute_release_room' in src
assert 'phòng đã trở về Chờ Sẵn Sàng' in src
print('6/6 checks passed')
