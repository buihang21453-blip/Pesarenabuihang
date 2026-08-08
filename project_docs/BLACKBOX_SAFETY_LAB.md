# PES Arena V1.3.54 — Black Box Safety Lab

## Mục tiêu
Cho phép Admin tự kiểm tra Black Box mà không phải thao tác gameplay bằng tay và không tạo dữ liệu trận/RP giả.

## Cách dùng
1. Deploy V1.3.54.
2. Vào Admin → `🛡 Black Box`.
3. Bấm `▶ Chạy kiểm tra tự động`.
4. Xem PASS / WARNING / FAIL / NOT TESTED.
5. Có thể bấm `⬇ Xuất báo cáo JSON` để gửi phân tích.

## Các nhóm tự động
- Source isolation: so hash 14 module gameplay quan trọng với baseline an toàn hiện tại V1.3.69.
- Kill Switch: kiểm tra cấu hình server/client và khi OFF thì frontend không load `blackbox.js`.
- Crash test: ép lớp lưu Black Box ném exception trong bộ nhớ, xác nhận exception không bubble ra gameplay.
- Storage probe: read-only tới `blackbox_incidents`.
- Browser micro benchmark: đo chi phí xử lý telemetry cục bộ.
- UI/CSS overlap scan: quét các phần tử tương tác đang render và cảnh báo giao nhau đáng kể.
- Navigation timing: ghi nhận DOMContentLoaded trên thiết bị đang chạy.

## Điều cố ý KHÔNG giả lập trên production
Luồng hai người: Invite → Ready → Random → Result → Confirm → RP. Safety Lab báo `NOT TESTED` thay vì tạo dữ liệu giả hoặc báo PASS không có bằng chứng.

## Kill Switch
- `BLACKBOX_ENABLED=false`: backend không lưu Black Box.
- `BLACKBOX_CLIENT_ENABLED=false`: template không nạp config/script Black Box ở trình duyệt.
- Khi client OFF: không listener, không timer, không wrap fetch, không telemetry request từ Black Box.
