# PES Arena V1.6.93 — Friendly Random Anti-Repeat

## Mục tiêu
Ngăn đội vừa xuất hiện bị random lặp lại trong 5 lượt gần nhất ở chế độ Giao hữu công khai.

## Quy tắc
- Lưu tối đa 5 hành động random gần nhất trong bộ nhớ trình duyệt.
- Random cả hai đội: ưu tiên loại toàn bộ đội đã xuất hiện trong 5 lượt gần nhất.
- Random riêng: áp dụng cùng lịch sử và luôn loại đội đang đứng ở phía đối diện.
- Đổi chế độ: reset lịch sử.
- Pool không đủ lớn: bỏ dần lượt cũ nhất cho tới khi đủ ứng viên; bảo đảm không treo UI.
- Hai phía không bao giờ nhận cùng một đội.

## Tài nguyên
100% client-side. Không thêm DB read/write, Supabase Realtime, Supabase Storage hay Vercel Function invocation cho thao tác random.

## File thay đổi
- `app.py`: V1.6.93
- `static/js/friendly_public.js`: anti-repeat 5 lượt
- `CHANGELOG.md`
- `OPTIMIZATION_V1.6.93.md`
