# PES Arena CSS Ownership — V1.2.14

Mục tiêu: mỗi khu vực giao diện có một nơi quản lý chính để tránh CSS ở trang này đè sang trang khác.

| Khu vực | File quản lý chính | Phạm vi |
|---|---|---|
| Nền tảng, layout chung, nút dùng chung | `static/style.css` | Toàn hệ thống |
| Phòng đấu | `static/css/room_detail.css` | Chỉ `room_detail` |
| Quick Match | `static/css/quick_match.css` | Chỉ `room_detail` |
| Parsec | `static/css/parsec_room.css` | Room/Profile theo class riêng |
| Chế độ Rank | `static/css/rank_mode_toggle.css` | Room/Admin theo class riêng |
| Admin Dashboard | `static/css/admin_dashboard.css` | Admin |
| Admin thưởng tuần | `static/css/admin_weekly_rewards.css` | Admin, đã scope `body[data-page="admin"]` |
| Hồ sơ Showcase | `static/css/profile_showcase.css` | `.profile-v2-page` |
| Shop | `static/css/shop_phase3.css` | Các trang Shop/Inventory/Profile/Admin Shop |
| Lucky Box người chơi | `static/css/luckybox_user.css` | Các trang Lucky Box |
| Lucky Box Admin | `static/css/luckybox_admin.css` | Admin Lucky Box |
| Zcoin | `static/css/zcoin.css` | Thành phần Zcoin/topbar dùng chung |
| Zcoin Rewards | `static/css/zcoin_rewards.css` | Trang rewards |

## Quy tắc từ V1.2.14

1. CSS mới của phòng đấu phải sửa trong `static/css/room_detail.css` hoặc đúng module con, không thêm lại vào `style.css`.
2. Không dùng selector chung như `.btn`, `.panel`, `button`, `input` trong module nếu có thể dùng class riêng của module.
3. Module tải sau chỉ được ghi đè trong phạm vi class của module đó.
4. Không dùng `!important` để giải quyết xung đột trừ khi cần giữ tương thích với CSS legacy và phải ghi chú lý do.
5. Dọn CSS và thay thiết kế giao diện là hai công việc riêng; V1.2.14 chỉ dọn/cô lập, không cố tình đổi thiết kế.
6. Khi thêm module mới, ưu tiên tải CSS theo `request.endpoint` thay vì nạp toàn hệ thống.
