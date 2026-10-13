# PES Arena V1.6.101 — Admin Lazy Loading Phase 2 + Analytics 403 Scope Fix

## Admin
- `/admin?tab=overview` không còn tải/decorate toàn bộ Users, Devices/IP, Matches, Rooms, Invites, Password Reset.
- 4 thẻ Tổng quan dùng truy vấn `COUNT exact` nhẹ.
- Dữ liệu chi tiết chỉ tải khi mở đúng tab: Users / Matches / Rooms / Passwords / System / Database / Logs.
- Overview bỏ bảng người dùng/IP/Admin nặng; thay bằng shortcut sang tab chức năng.

## Vercel Web Analytics
- Giữ endpoint chính thức `GET /v1/query/web-analytics/visits/count` và filter `requestPath eq '/friendly'`.
- Với 403, thử scope cấu hình theo Team ID/slug; nếu phù hợp, thử chế độ personal (không gửi team scope).
- Nếu mọi scope đều 403, báo rõ Access Token phải được tạo với Scope đúng team sở hữu project.
- Không log/hiển thị token.

## Không thay đổi
- Gameplay, Friendly random, Realtime, BXH/RPC, DB schema.
- Không có SQL migration mới.
