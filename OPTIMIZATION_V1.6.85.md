# PES Arena V1.6.85 — Asset Cache Ready

## Mục tiêu
Chuẩn bị source để các ảnh hệ thống cố định khi được đặt trong Vercel static có thể cache dài trên trình duyệt.

## Thay đổi
- APP_VERSION -> V1.6.85.
- Static raster/SVG/GIF/ICO trên Vercel: Cache-Control `public, max-age=31536000, immutable`.
- `static/ranks/*` cũng dùng cache 1 năm + immutable.
- Không thay đổi avatar/user upload.
- Không tự sao chép asset từ Supabase vì source V1.6.84 bàn giao không chứa các file ảnh gốc.

## Cách chuyển asset hệ thống sang Vercel
1. Giữ các ảnh hệ thống trong repository GitHub dưới `static/` đúng đường dẫn mà `asset_url()` đang dùng.
2. Bỏ/để trống `STATIC_ASSET_BASE_URL` trên Vercel để asset chung dùng `/static/...`.
3. Shop/LuckyBox hiện vẫn có base URL Supabase riêng; chỉ chuyển khi đã đưa đủ file tương ứng vào repo và thay cấu hình.
4. Với file thay đổi nội dung, đổi filename/version/hash hoặc cập nhật URL để tránh cache immutable giữ bản cũ.

## Lưu ý
Bản ZIP này cố ý không chứa raster assets nặng theo quy ước dự án. Vì vậy không được xóa thư mục ảnh đang có trong GitHub khi chép source ZIP lên repository.
