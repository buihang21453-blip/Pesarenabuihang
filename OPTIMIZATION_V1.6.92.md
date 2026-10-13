# PES Arena V1.6.92 — Friendly Match UI Redesign

## Phạm vi
Chỉ nâng cấp giao diện và thao tác trang `/friendly`.

## Thay đổi
- `templates/friendly_public.html`: bố cục mới theo phong cách PES Arena/stadium.
- `static/css/friendly_public.css`: UI desktop/mobile mới.
- `static/js/friendly_public.js`: hỗ trợ random riêng đội 1/đội 2 và random cả hai.
- `app.py`: version V1.6.92.

## Usage
Không thêm request khi random. Dataset vẫn nằm trong JavaScript và chạy tại browser; không query Supabase, không Realtime, không ghi DB.
