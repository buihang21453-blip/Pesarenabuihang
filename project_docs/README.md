# PES Arena — Tài liệu giữ lại

Thư mục này chứa **chỉ các tài liệu/SQL còn cần cho vận hành, khôi phục hoặc sửa dự án**.

## Tài liệu vận hành

- `FIX_NHANH_PES_ARENA.md` — quy trình FIX NHANH chi tiết.
- `LOGGING_GUIDE.md` — cấu trúc log/runtime và cách lần lỗi.
- `BLACKBOX_SAFETY_LAB.md` — cách dùng Black Box Safety Lab.

## SQL

Tất cả SQL cần giữ được gom tại `project_docs/sql/`.

- `20260808_blackbox.sql` — schema Black Box; chỉ chạy khi chủ dự án chủ động cho phép thay đổi Supabase production.
- Các file `PES_ARENA_*.sql` — schema/update cốt lõi còn được template/test tham chiếu.
- Các file `update_*.sql` — migration lịch sử duy nhất cần giữ để khôi phục/đối chiếu schema.

## File cố ý giữ ở root

- `AGENTS.md` — phải ở root để phiên/chat mới đọc quy tắc dự án trước khi sửa.
- `PROJECT_MAP.md` — bản đồ module/file.
- `Log.md` — lịch sử phiên bản.

Không đưa ba file trên vào thư mục này vì chúng là entrypoint vận hành của dự án.
