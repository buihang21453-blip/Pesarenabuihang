# PES Arena V1.6.100 — Friendly Analytics API Diagnostics Fix

## Mục tiêu
Sửa trường hợp Vercel Dashboard đã có dữ liệu `/friendly` nhưng Admin chỉ báo chung chung “Chưa có dữ liệu”.

## Thay đổi
- Giữ endpoint chính thức: `GET /v1/query/web-analytics/visits/count`.
- Filter: `requestPath eq '/friendly'`.
- Đọc `data.visitors` và `data.pageviews`.
- Phân loại lỗi HTTP/API an toàn, không hiển thị token.
- Team scope linh hoạt: `VERCEL_TEAM_ID=team_...` hoặc `VERCEL_TEAM_SLUG`; slug nhập nhầm vào `VERCEL_TEAM_ID` cũng được nhận diện.
- Cache thành công 300 giây; lỗi 60 giây.

## SQL / Supabase
Không có thay đổi SQL. Không tạo bảng, không ghi Supabase.
