# PES Arena V1.6.78 — Usage Optimization

Bản này ưu tiên tối ưu an toàn, giữ nguyên nghiệp vụ và giao diện.

## Thay đổi chính
- Pending Invite: active 2.2s -> 6s; idle 8s -> 20s; hidden 10s -> 60s.
- Invite watchdog: 5s/15s threshold -> kiểm tra 15s, chỉ cứu poller sau 45s visible hoặc 90s hidden.
- Heartbeat: 60s -> 180s; hidden 180s -> 300s; activity throttle 30s -> 120s.
- Room Chat polling: 3s -> 6s; hidden vẫn dừng, fallback interval 60s.
- Room State: giãn polling có kiểm soát theo trạng thái, vẫn giữ cơ chế since + HTTP 204.
- Chat DB query: bỏ select(*) ở 2 hot path, chỉ lấy cột cần thiết.

## Chủ đích
Đây là bước tối ưu low-risk trước khi chuyển Chat/Invite/Room State sang Realtime. Polling fallback vẫn được giữ để tránh làm mất chức năng khi kết nối realtime chưa được triển khai hoặc bị gián đoạn.

## Không thay đổi
- Luật Room/Tournament/League/C1.
- Giao diện và luồng thao tác chính.
- Database schema.
- Cơ chế đăng nhập.
