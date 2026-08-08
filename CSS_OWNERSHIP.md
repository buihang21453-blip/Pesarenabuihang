# PES Arena Room CSS Ownership — V1.3.110

Mục tiêu: mỗi khu vực của phòng đấu chỉ có một nơi chính quản lý. Không thêm CSS vá ở file khác nếu khu vực đã có owner.

| Khu vực | File quản lý chính |
|---|---|
| Khung gốc `.arena-room-v2`, biến màu nền tảng, nền/viền tổng | `00-room-core.css` |
| Logo + 6 chế độ | `13-mode-stability.css` |
| Khung phòng, topbar, Chủ phòng/Đối thủ, logo CLB | `14-shell-player-stability.css` |
| Nút và hành động phòng | `15-room-actions-stability.css` |
| Cột thông tin, Parsec, lịch sử phòng | `16-side-rail-history-stability.css` |
| Khu vực giữa trận, VS, đồng hồ, tỷ số/kết quả | `17-center-match-stability.css` |
| Chế độ đang chơi + trạng thái sẵn sàng | `18-active-mode-status-stability.css` |

## Quy tắc nâng cấp từ V1.3.110

1. Sửa đúng file owner của khu vực.
2. Không tạo selector trùng ở module Room khác.
3. Nếu cần thay owner: đưa CSS mới vào owner mới → kiểm tra → gỡ CSS cũ → kiểm tra lại.
4. Không dùng file `11-index-layout-reconnect.css` hoặc `12-mockup-layout-lock.css` để vá giao diện mới. Hai file này chỉ giữ phần legacy chưa chuyển.
5. `!important` chỉ giữ khi đang cần để bảo toàn giao diện; không dùng như cách mặc định để thắng CSS khác.
6. Thay đổi giao diện mới phải tách khỏi đợt dọn CSS.

## V1.3.122 room presentation authority
- `static/css/room/25-full-mockup-v122.css` is the only loaded layout/presentation owner for `room_detail.html`.
- Functional/base owners still loaded: `00`, `02`, `04`, `05`, `07`, `09`, `10`.
- Old layout/bridge modules `01`, `03`, `06`, `08`, `11`–`24` are intentionally not loaded by `room_detail.html`.
- Do not add a new bridge layer over `25`; edit `25` or replace it intentionally.


## V1.3.123 room reference shell authority
- `26-reference-layout-waiting-v123.css` sở hữu bố cục room mới và trạng thái đầu tiên `waiting_ready` khi chưa có đối thủ.
- Không tải `25-full-mockup-v122.css` trong `room_detail.html`.
- CSS chức năng cũ vẫn được giữ để bảo toàn form/state; file 26 được nạp cuối và sở hữu presentation/layout.
