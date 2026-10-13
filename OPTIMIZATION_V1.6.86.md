# PES Arena V1.6.86 — Local-first Asset Dual Source

## Mục tiêu
- Asset hệ thống do `asset_url()` quản lý luôn thử GitHub/Vercel trước tại `/static/assets/...`.
- Nếu file ảnh chưa được đưa lên GitHub, trình duyệt tự đổi sang Supabase Storage.
- Cho phép di chuyển asset dần từng file mà website vẫn hoạt động.
- URL tuyệt đối lưu trong DB vẫn được giữ nguyên.

## Quy tắc nguồn
1. Primary: `/static/assets/<logical-path>` (GitHub -> Vercel CDN).
2. Fallback: Supabase Storage (`STATIC_ASSET_BASE_URL`, `SHOP_ASSET_BASE_URL`, `LUCKYBOX_ASSET_BASE_URL`).
3. Fallback chỉ chạy một lần cho mỗi thẻ IMG để tránh vòng lặp lỗi.
4. Login background có cả local + Supabase fallback ở CSS variable.

## Lưu ý chuyển tiếp
Một số background Tournament/C1 cũ vẫn được CSS tham chiếu bằng URL Supabase tuyệt đối. Chúng tiếp tục hoạt động bình thường và chưa bắt buộc phải copy trong đợt đầu. Cây `ASSET_TREE_V1.6.86.md` liệt kê riêng nhóm này để di chuyển sau.
