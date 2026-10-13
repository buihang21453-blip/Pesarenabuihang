# PES Arena V1.6.99 — Friendly Admin Analytics

## Phạm vi
- Theo dõi duy nhất trang `/friendly` bằng Vercel Web Analytics.
- Admin Overview hiển thị đúng 2 chỉ số: **Người truy cập** và **Lượt mở trang**.
- Không tạo bảng Supabase, không ghi lượt truy cập vào DB.
- Vercel Analytics API chỉ được gọi ở server Admin, cache 5 phút; lỗi API không làm sập Admin.

## Cấu hình Vercel bắt buộc
1. Vercel Dashboard → Project → Analytics → Enable Web Analytics, sau đó redeploy.
2. Tạo Vercel Access Token và thêm Environment Variable `VERCEL_ANALYTICS_TOKEN`.
3. `VERCEL_PROJECT_ID` được hỗ trợ trực tiếp; nếu môi trường không có, đặt thủ công project ID.
4. Nếu project thuộc Team, đặt `VERCEL_TEAM_ID`.

Token chỉ nằm server-side, tuyệt đối không đưa vào HTML/JavaScript.
