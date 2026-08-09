# PROJECT MAP - PES Arena V1.2.10

## Lõi hệ thống đã module hóa

| Nhóm | File | Vai trò |
|---|---|---|
| Thành tích | `modules/core/achievements.py` | achievement/progress |
| Rank + CLB | `modules/core/rank_team_service.py` | rank, random đội, tier |
| Runtime phòng | `modules/core/room_runtime.py` | đọc phòng, timeout, enrich |
| Người dùng | `modules/core/user_repository.py` | user/player/device/admin reads |
| Trận đấu | `modules/core/match_repository.py` | match/dispute/invite reads |
| Social | `modules/core/social_runtime.py` | chat/announcement/streak |
| Matchmaking | `modules/core/matchmaking_runtime.py` | busy/active room/match |

## Luồng trận đấu

Nguồn quy tắc trạng thái: `modules/room_flow_service.py`.

`waiting_ready -> playing -> waiting_result_confirm -> confirmed -> waiting_ready (Đá tiếp)`

Giao hữu: `waiting_ready -> friendly_playing -> waiting_ready`.

## Route phòng đấu

| Chức năng | File |
|---|---|
| Vào/xem/rời/kick | `modules/room_access_routes.py` |
| Ready/chọn mode/quay CLB/start | `modules/room_team_routes.py` |
| Gửi/xác nhận/tranh chấp kết quả | `modules/room_result_routes.py` |
| Bỏ cuộc/Đá tiếp | `modules/room_rematch_routes.py` |

## Nguyên tắc nâng cấp

- Không thêm logic phòng mới trực tiếp vào `app.py`.
- Quy tắc trạng thái mới phải thêm vào `room_flow_service.py`.
- DB update theo chức năng nằm trong route/service tương ứng.
- Giữ endpoint cũ để không phá Front-end hiện tại.

## V1.2.11 — Mời đấu / Online / Kết quả an toàn
- `modules/invites/service.py`: quy tắc gửi và nhận lời mời dùng chung.
- `modules/presence/service.py`: nguồn quyết định Online thống nhất.
- `modules/match_result_service.py`: claim + snapshot + rollback khi xác nhận RP lỗi.
- `modules/room_result_routes.py`: xác nhận kết thúc ở `confirmed`.
- `modules/room_rematch_routes.py`: Đá tiếp cần cả hai đồng ý, có kiểm tra ghi trạng thái.


### V1.2.12 event flow
- `modules/room_flow_service.py`: nguồn chuẩn cho action + event + transition của phòng.
- `modules/room_result_routes.py`: submit/confirm/dispute; confirm luôn vào `confirmed`.
- `modules/core/room_runtime.py`: timeout/repair, không reset bỏ qua bước Confirmed.
- `modules/core/match_repository.py`: auto-confirm đồng bộ Room sang Confirmed.
- `modules/room_rematch_routes.py`: hai bên đồng ý Đá tiếp rồi mới `confirmed -> waiting_ready`.

## V1.2.13 — Read Model / Hiệu năng
- `modules/read_model_service.py`: truy vấn đọc chuyên biệt, cache ngắn, lịch sử người dùng/H2H/phong độ/báo cáo.
- `modules/core/match_repository.py`: `list_matches(status=None, limit=None)` lọc trực tiếp tại Supabase.
- `modules/profile/service.py`: Hồ sơ chỉ đọc dữ liệu đúng người/cặp người chơi.
- `modules/admin_dashboard_routes.py`: ưu tiên Read Model và truy vấn giới hạn.
- `project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql`: migration tùy chọn cho các bảng cache/precompute.


## V1.2.15 - Layout phòng đấu
- `templates/room_detail.html`: shell đầy đủ, badge trạng thái và layout phòng chính.
- `templates/_room_live_content.html`: fragment trạng thái động; phải giữ đồng bộ với layout chính khi sửa nội dung trung tâm.
- `static/css/room_detail.css`: owner của `room-layout-v1215` và toàn bộ geometry theo trạng thái.
- Quy tắc: không tạo layout HTML riêng cho từng trạng thái; chỉ thay nội dung trong cột trung tâm.


### Admin Room UI Designer (V1.2.16)
- `modules/admin_room_ui/service.py`: đọc/lưu/chuẩn hóa cấu hình.
- `modules/admin_room_ui/routes.py`: route Save/Reset + context template.
- `templates/admin/tabs/room-ui.html`: tab thiết kế và Preview.
- `static/js/admin/room-ui-designer.js`: cập nhật Preview + kéo X/Y.
- `static/css/admin/room-ui-designer.css`: giao diện Designer.
- `static/css/room_detail.css`: lớp áp dụng biến UI vào phòng thật.
