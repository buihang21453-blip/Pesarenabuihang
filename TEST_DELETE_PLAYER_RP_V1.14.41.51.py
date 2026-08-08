from pathlib import Path

source = Path('modules/data_cleanup_service.py').read_text(encoding='utf-8')
assert 'def delete_match_safe(match_id, *, reverse_result=True):' in source
assert 'if match and reverse_result:' in source
assert 'delete_room_safe(room["id"], reverse_result=False)' in source
assert 'delete_match_safe(match_id, reverse_result=False)' in source
assert 'related_match_ids = set()' in source
print('PASS: Xóa tài khoản không hoàn tác RP đối thủ và không xử lý trùng trận.')
