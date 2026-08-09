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
