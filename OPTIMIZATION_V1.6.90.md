# PES Arena V1.6.90 — Admin Lazy Data Loading Phase 1

## Vấn đề
Trước V1.6.90, một lần mở `/admin` có thể tải cả dữ liệu của các tab đang ẩn: báo cáo trận, phòng hủy, audit log, migration probes và cấu hình hệ thống. Điều này làm phát sinh query Supabase dù Admin chưa mở chức năng đó.

## Giải pháp
Admin dùng tham số `tab` để server biết dataset nào thực sự cần. Các dataset nặng/ít dùng được tải theo nhu cầu. Dashboard cơ bản vẫn giữ dữ liệu cần cho metric và quản trị nhanh để tránh thay đổi hành vi.

| Dataset | V1.6.89 | V1.6.90 |
|---|---|---|
| Match report | Mỗi lần `/admin` | Chỉ `tab=match-report` |
| Cancelled rooms (limit 300) | Mỗi lần `/admin` | Chỉ `tab=rooms` |
| Audit logs | Owner mỗi lần `/admin` | Chỉ `tab=logs` |
| Migration probes | Mỗi lần/cache | Chỉ `tab=database` + cache |
| System/maintenance config | Mỗi lần `/admin` | Chỉ `tab=system` |
| Rank tier config | Mỗi lần `/admin` | `system` / `season` |

## Tác động
- Giảm DB reads không cần thiết khi Admin chỉ xem Tổng quan hoặc một tab cụ thể.
- Giảm thời gian xử lý Function và lượng dữ liệu Supabase -> Vercel.
- Không có SQL migration mới.

## Lưu ý
Đây là Phase 1 an toàn. Users/matches/active rooms cơ bản vẫn được tải để giữ các metric và chức năng Tổng quan. Phase tiếp theo chỉ nên tách chúng thành endpoint/lazy fragment sau khi đo usage thực tế.
