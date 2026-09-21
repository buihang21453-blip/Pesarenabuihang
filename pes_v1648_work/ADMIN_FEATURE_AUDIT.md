# Rà soát Admin — V1.6.37

## Phạm vi & cách hiểu
Đây là rà soát cấu trúc source và giao diện, KHÔNG phải đo thống kê sử dụng Production. Không thể kết luận route ít người bấm là không còn dùng khi thiếu log truy cập và yêu cầu chủ dự án.

## Điều hướng mới
Tổng quan; Người dùng; Rank & Phòng đấu; Giải đấu C1; Kinh tế & Thưởng; Hệ thống; Công cụ nâng cao. Mọi panel/endpoint gốc vẫn giữ nguyên.

## C1
Thanh tiến trình lấy status trực tiếp `tournament_stages`: `completed`/`open`/`pending`/không xác định. Mặc định mở giai đoạn `open` theo ưu tiên KO > GĐ2 > GĐ1; khi không có open thì chọn giai đoạn tiếp theo sau giai đoạn completed. GĐ2 luôn gom hai panel Pot/CLB và trận đấu trong cùng tab. Khối HLV và cấu hình ít dùng mặc định đóng; dữ liệu và thao tác bên trong vẫn còn.

## Hạng mục trùng hoặc ít dùng được đưa vào giao diện rà soát Owner
| ID | Nhận xét | Hành vi được phép trong V1.6.37 |
|---|---|---|
| c1-flow-summary | Sơ đồ 4 ô giới thiệu chức năng trùng thanh điều hướng | Ẩn ở trình duyệt hoặc đề xuất xóa |
| league-ranking-copy | BXH tổng lặp trong GĐ2 | Ẩn ở trình duyệt hoặc đề xuất xóa; BXH chính không đổi |
| c1-registration | Khối đăng ký/HLV chứa quản lý tiền, trận, không tương đương tab Người dùng | Thu gọn, chỉ đề xuất xem xét, không cho ẩn/xóa tự động |
| match-report | Báo cáo chi tiết có thể bổ trợ danh sách trận | Chỉ đánh dấu rà soát |
| rp-tools | Backup/Restore RP có nguy cơ mất dữ liệu nếu xóa | Giữ, chỉ đánh dấu rà soát |
| tournament-test | Kiểm thử có cách ly dữ liệu thật | Giữ, chỉ đánh dấu rà soát |
| database | SQL tracker là công cụ phục hồi | Giữ, chỉ đánh dấu rà soát |

Các quyết định lưu bằng localStorage ở trình duyệt Owner; nút xuất JSON dùng để phê duyệt trong đợt sau. Không xóa route, Python, SQL, DB, chức năng hoặc phân quyền.

## Luồng bị ảnh hưởng cần kiểm thử Production
- Menu tab và deep-link hash `#tournaments`, `#c1-admin-gd2`; các form tự điền `_admin_tab`.
- Hiển thị các giai đoạn theo trạng thái thực của Supabase; nếu không có status thì phải ghi “Chưa xác định”.
- HLV/Test Mode/Rank/Zcoin/SQL tracker/Lucky Box được giữ nguyên.
- Kiểm tra thủ công việc không xuất hiện/ẩn sai giai đoạn và việc lưu tuỳ chọn trên trình duyệt khi deploy.
