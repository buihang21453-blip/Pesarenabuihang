# PES Arena V1.6.91 — Guest Friendly Match

## Mục tiêu
Cho khách truy cập và người đã đăng nhập random đội giao hữu mà không tạo tải DB/Realtime không cần thiết.

## Kiến trúc
- GET `/friendly`: chỉ render trang tĩnh qua Flask một lần.
- Sau khi trang đã tải, chọn chế độ và `RANDOM LẠI` chạy hoàn toàn bằng JavaScript.
- Không có fetch/XHR/API call trong module random.
- Không Supabase DB, Realtime hay Storage cho thao tác random.
- Không logo CLB/ĐTQG.
- Không ghi History/BXH.

## Chế độ
- Ngoại Hạng Anh
- La Liga
- 5 Sao (pool S/S+ tĩnh của source PES Arena)
- 4 Sao (pool A/A+ tĩnh của source PES Arena)
- CLB 5★
- Quốc Gia 5★

## Database / SQL
Không thay đổi.
