from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASH = (ROOT / 'modules/admin_dashboard_routes.py').read_text(encoding='utf-8')
DATA = (ROOT / 'modules/admin_data_routes.py').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_admin_version_and_no_cleanup_n_plus_one():
    assert 'APP_VERSION = "1.3.33"' in APP
    assert 'cleanup_duplicate_waiting_rooms(uid)' not in DASH
    assert 'Không thực hiện thao tác ghi/xóa dữ liệu trong request mở tab Admin' in DASH


def test_report_uses_filtered_lean_queries():
    assert 'report_columns = "id,created_at,status,player1_id,player2_id,score1,score2,delta1,delta2,rp_details,note"' in DASH
    assert '.gte("created_at", start_dt.isoformat()).lt("created_at", end_dt.isoformat())' in DASH
    assert 'check_rank_mode_eligibility(mode_row.get("code"), user)' not in DASH
    assert 'rank_mode_unlock_map' in DASH


def test_cancel_room_is_error_safe():
    assert 'execute_query(update_query, "admin_cancel_room", attempts=2)' in DATA
    assert 'except Exception as exc:' in DATA
    assert 'Không thể hủy phòng lúc này' in DATA
    assert 'admin_cancel_room_invite' in DATA
