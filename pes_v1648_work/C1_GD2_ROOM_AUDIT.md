# Audit phòng C1 GĐ2 – V1.6.41

Phạm vi: kiểm tra tĩnh source V1.6.40, sửa trong V1.6.41 và chạy regression mô phỏng. Chưa thử trực tiếp Supabase Production hay trình duyệt hai máy.

| Luồng | Phát hiện từ V1.6.40 | Xử lý trong V1.6.41 |
|---|---|---|
| Hai HLV đã vào, guest chưa Ready, lookup CLB trả rỗng/lỗi | Template ưu tiên `not tournament_fixed_clubs_ready` và bỏ hẳn form Ready | Nút Ready luôn hiện cho guest; service vẫn quyết định có thể bắt đầu không |
| Khách mới vào, chưa Ready | Badge ghi `Đã vào phòng · CLB theo HLV` với CSS `is-ready` | Badge dựa trên `guest_ready` thật |
| Ready thành công nhưng tự start lỗi | Guest chỉ thấy trạng thái chờ, host phải retry | Guest có thể retry nếu guest_ready; hoặc hủy ready, host vẫn có retry |
| CLB chưa được gán, hoặc trùng nhau | Service ngăn bắt đầu, không Random hay tiêu vé | Giữ kiểm tra backend; nút Ready không bị UI chặn bởi preview |
| GĐ2 chưa mở/trận không còn pending, sai đối thủ | Service từ chối bắt đầu | Giữ guard và thông báo lỗi |
| Hai request start đồng thời | Update room và fixture có điều kiện, rollback khi fixture transition thất bại | Giữ guard, chưa chuyển sang RPC atomic |
| Host nhập tỷ số; guest xác nhận | C1 result partial có route riêng và cập nhật BXH qua xác nhận | Giữ nguyên, test UI host/guest |
| Kick guest trong C1 | Nút Rank vẫn hiển thị dù backend cấm | Ẩn nút trên first render và polling |
| Bỏ cuộc trong trận C1 | Form Rank có cảnh báo -20 RP; route Rank không chặn C1 | Ẩn form Rank, chặn cả POST trực tiếp để không trừ RP/đổi metadata |
| Bị rớt kết nối lúc chờ | C1 room_leave riêng giữ metadata, không RP | Không đổi |

## Điểm cần theo dõi Production

- Nếu start từ Ready vẫn báo `Giai đoạn chưa mở` hoặc `Phòng chưa liên kết trận`, cần xem cụ thể stage, fixture, room metadata và server logs; không được tự sinh lịch hoặc sửa dữ liệu giải để vượt qua guard.
- Chuyển trạng thái `match_rooms` + `tournament_matches` hiện gồm hai câu lệnh DB riêng có rollback ứng dụng; muốn atomic hoàn toàn cần RPC SQL được thiết kế và test riêng.
- Luồng nhập tỷ số + xác nhận cũng có nhiều cập nhật DB riêng: theo dõi các trường hợp Vercel/Supabase mất kết nối ở giữa để thiết kế giao dịch một lần trong bản sau nếu cần.
- Không thay đổi luật xử lý bỏ cuộc C1: hiện chặn cơ chế bỏ cuộc Rank và hướng người chơi về quy trình Admin C1 thay vì tự động xử thắng/trừ RP.
