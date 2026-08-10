# Hướng dẫn chuyển PES Arena sang Supabase project mới

> Mục tiêu: chuyển Database/Auth sang project mới, giữ nguyên dữ liệu người chơi; Storage cũ được tải về `static/` để Vercel phục vụ các asset giao diện. Không xóa project cũ trước khi kiểm tra xong.

## A. Chuẩn bị project Supabase mới

1. Tạo **project mới** trong tài khoản Supabase mới.
2. Nên chọn region gần người dùng (ví dụ Singapore nếu phù hợp).
3. Ghi lại:
   - `NEW_PROJECT_URL`
   - `NEW_SERVICE_ROLE_KEY` / secret key chỉ dùng ở backend
   - Database password
   - Session Pooler connection string trong nút **Connect**.
4. Không đưa service-role/secret key vào HTML/JS phía trình duyệt.

## B. Cách chuyển Database + Auth an toàn

### Cách 1 — nếu Supabase Dashboard cho phép “Restore to a new project”

Đây là cách ưu tiên nếu project/gói của bạn có tính năng này. Nó copy schema, dữ liệu, indexes, roles và Auth users. Storage files, Edge Functions, API/Auth settings, Realtime settings vẫn phải cấu hình lại thủ công.

### Cách 2 — dump/restore bằng Supabase CLI

Cài Docker Desktop, Supabase CLI và PostgreSQL/psql trước. Sau đó lấy **connection string project cũ** và **project mới** từ nút Connect.

Chạy ở thư mục tạm trên máy Windows:

```bat
supabase db dump --db-url "OLD_CONNECTION_STRING" -f roles.sql --role-only
supabase db dump --db-url "OLD_CONNECTION_STRING" -f schema.sql
supabase db dump --db-url "OLD_CONNECTION_STRING" -f data.sql --use-copy --data-only -x "storage.buckets_vectors" -x "storage.vector_indexes"
```

Sau đó restore sang project mới theo đúng hướng dẫn CLI hiện tại của Supabase. Nên dùng Session Pooler connection string mặc định nếu mạng không hỗ trợ IPv6.

**Lưu ý:** project cũ đang bị `exceed_egress_quota`. Nếu Supabase chặn cả kết nối database/backup, bạn cần khôi phục quyền truy cập (nâng gói/bỏ spend cap hoặc dùng backup có sẵn) trước khi dump được.

## C. Auth người chơi

Full database migration có thể chuyển các bảng trong schema `auth`, gồm user và password hash, nên người chơi không phải tạo lại mật khẩu. Tuy nhiên project mới có JWT secret khác thì token đăng nhập cũ không còn hợp lệ; người chơi chỉ cần đăng nhập lại. Không cần cố giữ token cũ trừ khi thật sự cần.

Sau migration, kiểm tra ít nhất:

```sql
select count(*) from auth.users;
select count(*) from public.users;
select count(*) from public.matches;
select count(*) from public.match_rooms;
```

So sánh số dòng với project cũ/backup.

## D. Storage / ảnh giao diện

V1.2.20 chuyển sang mô hình **Vercel-first**.

1. Khi Storage cũ truy cập lại được, tại thư mục project chạy:

```bat
python tools\migrate_supabase_assets_to_vercel_static.py --static-base "OLD_STATIC_ASSET_BASE_URL" --shop-base "OLD_SHOP_ASSET_BASE_URL" --luckybox-base "OLD_LUCKYBOX_ASSET_BASE_URL"
```

2. Chờ kết quả 100% asset hợp lệ.
3. Deploy project có các file mới trong `static/` lên Vercel.
4. Trên Vercel đặt:

```text
STATIC_ASSET_MODE=auto
```

5. Khi kiểm tra toàn bộ ảnh đều chạy từ `/static/...`, có thể chuyển thành:

```text
STATIC_ASSET_MODE=local
```

6. Khi đã dùng local hoàn toàn, có thể xóa `STATIC_ASSET_BASE_URL`, `SHOP_ASSET_BASE_URL`, `LUCKYBOX_ASSET_BASE_URL` khỏi Vercel để project không còn tải asset UI từ Supabase cũ.

## E. Đổi biến môi trường Vercel sang Supabase mới

Trong **Vercel > Project > Settings > Environment Variables**, thay:

```text
SUPABASE_URL=https://NEW_PROJECT_REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<secret/service-role của project mới>
```

Giữ nguyên `FLASK_SECRET_KEY` hiện tại để session Flask không bị đổi không cần thiết.

Sau khi sửa Environment Variables, Redeploy Production.

## F. Những thứ phải kiểm tra/cấu hình lại ở project mới

- Auth URL / Site URL / Redirect URLs.
- Email provider/template nếu có tùy chỉnh.
- Realtime publications/settings cần thiết.
- Database extensions/settings đặc biệt.
- Edge Functions nếu dự án có dùng.
- Storage buckets/policies nếu vẫn giữ một số loại file động trên Supabase mới.
- RLS/policies và quyền Data API.

## G. Checklist test trước khi bỏ project cũ

- [ ] Login tài khoản cũ được.
- [ ] RP người chơi đúng.
- [ ] BXH đúng.
- [ ] Tạo phòng được.
- [ ] Mời đấu được.
- [ ] Gửi kết quả + xác nhận được.
- [ ] RP cập nhật đúng một lần.
- [ ] Lịch sử trận còn đủ.
- [ ] Admin mở được từng tab.
- [ ] Avatar/logo/ảnh giao diện hiển thị đủ.
- [ ] Lucky Box/Shop hiển thị ảnh đầy đủ nếu đang dùng.
- [ ] Không còn request asset UI tới domain Supabase cũ trong DevTools > Network.

Chỉ sau khi toàn bộ checklist đạt mới cân nhắc xóa/tạm dừng project Supabase cũ.
