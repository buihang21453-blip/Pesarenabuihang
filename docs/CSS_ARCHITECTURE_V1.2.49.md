# V1.2.49 — Kiến trúc CSS & kiểm soát cascade

## 1. Mục tiêu

- Chấm dứt việc đổi màu nút ở một chỗ nhưng bị CSS cũ đè ở chỗ khác.
- Có thứ tự nạp CSS cố định và có chủ sở hữu rõ ràng cho từng nhóm giao diện.
- CSS module không dùng `!important`.
- Tách **màu/nền/viền/shadow** của nút khỏi **kích thước** của nút.
- Giữ nguyên HTML/JS/API/core/DB; nâng cấp này chỉ tổ chức lại CSS và quy tắc cascade.

## 2. Thứ tự CSS chuẩn

| Thứ tự | Lớp | File/nhóm | Quyền sở hữu |
|---:|---|---|---|
| 1 | Design tokens | `css/core/design_tokens.css` | Biến màu, radius, transition |
| 2 | Legacy foundation | `style.css` | Layout/nền tảng cũ; không được thêm override nút mới |
| 3 | Shared component | `css/components/buttons.css` | Màu/nền/viền/shadow của `.btn` dùng chung |
| 4 | Shared sizing | `css/button_sizes.css` | Height/padding/font-size/gap của nút dùng chung |
| 5 | Feature modules | `zcoin.css`, `parsec_room.css`, `quick_match.css`, ... | Chỉ giao diện tính năng của chính module |
| 6 | Page module | `room_v2.css`, `profile_showcase.css`, `admin_dashboard.css`, ... | Quyền ưu tiên cuối trong trang tương ứng |

`templates/base.html` hiện nạp đúng thứ tự trên. `page_styles` vẫn nằm sau cùng để trang riêng có thể tự sở hữu giao diện của nó mà không cần `!important`.

## 3. Quy tắc `!important`

### Trước V1.2.49
- Toàn dự án: **1.653 khai báo `!important`**.
- Riêng `room_v2.css`: **280**.
- `room_detail.css`: **161**.
- Admin Room UI Designer: **110**.
- Profile: **62**.

### Sau V1.2.49
- Mọi file dưới `static/css/**`: **0 khai báo `!important`**.
- `style.css` legacy còn **899** khai báo. Đây là nợ kỹ thuật cũ, nhưng đã bị cô lập phía trước module mới trong thứ tự tải.
- Không được thêm `!important` mới vào module. Script `scripts/check_css_contract.py` sẽ báo FAIL nếu vi phạm.

> Lưu ý: `style.css` chưa được xóa hàng loạt `!important` vì đây là file lịch sử 3.000+ dòng, chứa nhiều giao diện cũ. Xóa đồng loạt có thể làm lệch BXH/Admin/Login. V1.2.49 cô lập nó trước; các đợt sau có thể tách dần theo trang.

## 4. Hệ thống nút sau khi phân luồng

| Nhóm nút | Khu vực | File sở hữu màu | File sở hữu kích thước | Màu chính |
|---|---|---|---|---|
| `.btn` mặc định | Toàn hệ thống | `components/buttons.css` | `button_sizes.css` | Vàng |
| `.btn.green` | Xác nhận/Lưu/Tìm nhanh ngoài Room | `components/buttons.css` | `button_sizes.css` | Xanh lá |
| `.btn.red` | Xóa/Từ chối/Bỏ cuộc ngoài Room | `components/buttons.css` | `button_sizes.css` | Đỏ |
| `.btn.gray` | Hủy/Phụ | `components/buttons.css` | `button_sizes.css` | Xám xanh |
| `.btn.blue` | Hành động phụ màu xanh | `components/buttons.css` | `button_sizes.css` | Xanh dương |
| `.room-neon-btn` | Phòng đấu | `room_v2.css` | `room_v2.css` | Neon vàng/xanh/đỏ/xanh dương/xám |
| `.parsec-action-btn` | Parsec | `parsec_room.css` | `parsec_room.css` | Theo Parsec |
| `.game-notice-button` | Quick Match | `quick_match.css` | `quick_match.css` | Theo Quick Match |
| Preview Room Admin | Admin UI Designer | `admin/room-ui-designer.css` | cùng file | Theo preview |
| Lucky Box | Lucky Box | `luckybox_user.css` / `luckybox_admin.css` | cùng file | Theo Lucky Box |

### Muốn đổi màu nút toàn hệ thống
Chỉ sửa biến trong `static/css/core/design_tokens.css`.

Ví dụ:
- Xanh lá: `--ui-action-green`, `--ui-action-green-hover`, `--ui-action-green-border`.
- Đỏ: `--ui-action-red`, `--ui-action-red-hover`, `--ui-action-red-border`.
- Vàng: `--ui-action-gold`, `--ui-action-gold-hover`, `--ui-action-gold-border`.

Không cần tìm hàng chục rule `.btn.green` trong `style.css` nữa.

## 5. Module theo khu vực

| Khu vực | CSS module | Phạm vi |
|---|---|---|
| Nền tảng/legacy | `style.css` | Shell, bảng, form, layout cũ |
| Token màu | `css/core/design_tokens.css` | Chỉ biến CSS |
| Nút dùng chung | `css/components/buttons.css` | Chỉ visual `.btn` |
| Kích thước nút | `css/button_sizes.css` | Chỉ size/spacing |
| Room legacy | `css/room_detail.css` | Luồng room cũ/compatibility |
| Room V2 | `css/room_v2.css` | Giao diện Room hiện hành; tải sau cùng |
| Parsec Room | `css/parsec_room.css` | Panel Parsec |
| Quick Match | `css/quick_match.css` | Tìm nhanh/thông báo game |
| Rank mode | `css/rank_mode_toggle.css` | Công tắc/chọn mode |
| Profile | `css/profile_showcase.css` | Hồ sơ người chơi |
| Shop | `css/shop_phase3.css` | Cửa hàng/kho đồ |
| Lucky Box User | `css/luckybox_user.css` | Người dùng Lucky Box |
| Lucky Box Admin | `css/luckybox_admin.css` | Quản trị Lucky Box |
| Zcoin | `css/zcoin.css` | Topbar + ví Zcoin |
| Zcoin reward | `css/zcoin_rewards.css` | Phần thưởng Zcoin |
| Admin dashboard | `css/admin_dashboard.css` | Dashboard admin |
| Admin weekly | `css/admin_weekly_rewards.css` | Thưởng tuần |
| Admin Room UI | `css/admin/room-ui-designer.css` | Preview/slider chỉnh Room |
| Streak animation | `css/streak_animation.css` | Animation chuỗi thắng |

## 6. Các dạng chồng chéo đã phát hiện

1. `.btn`, `.btn.green`, `.btn.red`, `.btn.gray` từng được khai báo lại ở nhiều version trong `style.css`.
2. Có block cũ biến **`.btn.green` thành màu vàng**, nên yêu cầu đổi xanh thường bị đè.
3. Light theme có một bộ override nút riêng với `!important`.
4. `room_v2.css` từng dùng `!important` gần như toàn bộ `.room-neon-btn` để thắng CSS cũ.
5. Admin Room UI Designer, Parsec, Profile, Quick Match cũng dùng `!important` để tự bảo vệ.
6. `room_detail.css` và `room_v2.css` cùng tồn tại trên Room; V1.2.49 xác định rõ **room_v2 tải sau và là owner cuối của giao diện Room V2**.

Các block màu `.btn` trùng có quyền ưu tiên cao trong `style.css` đã được loại khỏi luồng active và chuyển quyền sở hữu sang `components/buttons.css`.

## 7. Quy tắc phát triển từ V1.2.49

- Không thêm CSS mới vào cuối `style.css` chỉ để sửa một trang.
- Không dùng `!important` trong module.
- Không sửa màu `.btn` trong file trang.
- Trang/tính năng đặc thù phải có class scope riêng, ví dụ `.room-v2-shell ...`, `.profile-v2-...`, `.parsec-room-panel ...`.
- Nếu cần đổi size nút dùng chung: `button_sizes.css`.
- Nếu cần đổi màu nút dùng chung: `design_tokens.css` hoặc `components/buttons.css`.
- Nếu cần đổi Neon Room: `room_v2.css`.
- Khi thêm CSS mới, chạy `python scripts/check_css_contract.py`.

## 8. Kết quả kiểm tra

- CSS parse error: **0**.
- Module `!important`: **0**.
- Contract checker: **PASS**.
- Jinja syntax: kiểm tra toàn bộ template.
- Python compile: kiểm tra `app.py` và modules.
