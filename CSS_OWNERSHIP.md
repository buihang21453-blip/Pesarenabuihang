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
