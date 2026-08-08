# PES ARENA — AI WORKFLOW RULES

> **BẮT BUỘC ĐỌC FILE NÀY TRƯỚC KHI SỬA DỰ ÁN.**
> File này là quy tắc làm việc cấp dự án và được dùng cho cả các đoạn chat/phiên làm việc mới.

## 0. Quy tắc khởi động

Khi người dùng yêu cầu sửa, nâng cấp, kiểm tra hoặc audit PES Arena:

1. Đọc yêu cầu đầu tiên của người dùng trong phiên hiện tại.
2. Đọc `AGENTS.md` này.
3. Đọc `PROJECT_MAP.md` để xác định module/file sở hữu luồng.
4. **Tự động phân loại yêu cầu** vào đúng 1 trong 3 chế độ bên dưới.
5. Không bắt người dùng phải tự ghi tên chế độ nếu nội dung yêu cầu đã đủ rõ.
6. Nếu yêu cầu thay đổi giữa phiên, được phép chuyển chế độ tương ứng với yêu cầu mới.

---

# 1. FIX NHANH

## Khi nào tự chọn

Chọn **FIX NHANH** khi người dùng báo một lỗi cụ thể hoặc một hành vi đang sai, ví dụ:

- Internal Server Error / 500.
- Một nút không hoạt động.
- Người online nhưng không nhận được lời mời.
- Sai hiển thị một khu vực.
- Một API/route bị lỗi.
- Một chức năng vừa sửa bị regression.

## Luồng xử lý bắt buộc

1. Xác định đúng luồng: **Frontend → Backend → Database/Supabase**.
2. Đọc **chỉ các file liên quan** theo `PROJECT_MAP.md`.
3. Kiểm tra log/request ID nếu có.
4. Xác định nguyên nhân gốc trước khi sửa.
5. Sửa tối thiểu đúng lỗi.
6. Không audit toàn bộ dự án.
7. Không refactor file/module không liên quan.
8. Không đổi UI nếu người dùng không yêu cầu.
9. Chỉ kiểm tra CSS khi lỗi liên quan hiển thị/style/layout.
10. Giữ compatibility với hệ thống hiện tại.
11. Sau khi sửa: kiểm tra import/syntax/dependency và regression test đúng module.
12. Không xoá template/partial/module chỉ vì grep không thấy tham chiếu trực tiếp; phải kiểm tra include động, import động, runtime dependency và regression test.
13. Ghi `Log.md`: nguyên nhân, file, chức năng, thay đổi, test.

### Mẫu tư duy phạm vi

`Lỗi cụ thể → module sở hữu → frontend liên quan → backend liên quan → DB nếu có → fix → test module`

---

# 2. NÂNG CẤP MODULE

## Khi nào tự chọn

Chọn **NÂNG CẤP MODULE** khi người dùng yêu cầu:

- Thêm tính năng mới.
- Thay đổi logic của một module.
- Thêm chế độ Rank.
- Nâng cấp Invite/Quick Match/Room/Admin/Profile/Shop/Zcoin...
- Thiết kế lại một phần giao diện có phạm vi rõ ràng.
- Tách/refactor một module cụ thể.

## Luồng xử lý bắt buộc

1. Xác định module sở hữu bằng `PROJECT_MAP.md`.
2. Vẽ/hiểu luồng hiện tại: **Frontend → Route/API → Service → Repository/DB**.
3. Xác định dependency với module khác trước khi chỉnh.
4. Chỉ mở rộng phạm vi khi thật sự cần cho tính năng.
5. Giữ API/public binding cũ nếu có thể để tránh regression.
6. Nếu thay DB/Supabase, kiểm tra schema/RLS/storage liên quan.
7. Nếu thay UI, kiểm tra CSS conflict đúng phạm vi module.
8. Chạy test module + dependency gần nhất.
9. Nếu phát hiện lỗi ngoài phạm vi nhưng không chặn nâng cấp: ghi chú, không tự sửa lan rộng.
10. Ghi `Log.md` và cập nhật `PROJECT_MAP.md` nếu cấu trúc/module/file ownership thay đổi.

### Mẫu tư duy phạm vi

`Yêu cầu mới → module → luồng hiện tại → thiết kế thay đổi → triển khai → compatibility → regression test`

---

# 3. AUDIT TOÀN HỆ THỐNG

## Khi nào tự chọn

Chọn **AUDIT TOÀN HỆ THỐNG** khi người dùng yêu cầu rõ ràng các nội dung như:

- Kiểm duyệt toàn bộ website/dự án.
- Rà tất cả module/luồng.
- Kiểm tra frontend + backend + database + admin.
- Tối ưu toàn hệ thống.
- Tìm lỗi chồng chéo/thiếu module/thiếu dữ liệu trên toàn dự án.
- Kiểm tra cấu trúc dự án tổng thể.

## Luồng xử lý bắt buộc

Audit theo lớp, không sửa ngẫu nhiên:

1. Bootstrap / cấu trúc project.
2. Frontend templates/JS.
3. CSS và conflict/cascade.
4. Backend route/API.
5. Service/repository.
6. Supabase schema/data/storage/RLS khi liên quan.
7. Room / Rank / Invite / Presence / Match / RP.
8. Admin.
9. Economy/Profile/Shop/Zcoin.
10. Polling/cache/performance/logging.
11. Security/permissions/runtime dependency.
12. Test/regression/dead code.

Sau audit phải phân loại phát hiện theo mức độ và chỉ sửa theo phạm vi người dùng yêu cầu.

---

# 4. Quy tắc tự chuyển chế độ

- Đang **NÂNG CẤP MODULE**, người dùng báo bản vừa làm bị lỗi 500 → lượt đó chuyển sang **FIX NHANH**.
- Đang **FIX NHANH**, người dùng yêu cầu “kiểm tra luôn toàn bộ hệ thống” → chuyển sang **AUDIT TOÀN HỆ THỐNG**.
- Người dùng yêu cầu thêm một tính năng mới sau khi fix xong → chuyển sang **NÂNG CẤP MODULE**.

Không giữ cứng chế độ của lượt trước nếu yêu cầu mới đã thay đổi bản chất công việc.

---

# 5. Quy tắc an toàn chung của PES Arena

- Không sửa lan sang module khác chỉ vì “tiện tay”.
- Không xoá file/template/module vì chỉ thấy không có static reference.
- Không thay đổi gameplay/RP nếu yêu cầu không liên quan.
- Không thay giao diện nếu yêu cầu chỉ là backend.
- Không tạo polling mới nếu có thể dùng event/state hiện tại.
- Không tăng tải Supabase/Vercel không cần thiết.
- Static asset đã có trên Supabase thì ưu tiên remote asset; không giữ bản local trùng lặp, nhưng chỉ xoá sau khi xác minh runtime reference.
- Khi refactor `app.py`, giữ compatibility binding cho route/test legacy nếu chưa di chuyển toàn bộ dependency.
- Nếu test cũ rõ ràng stale so với kiến trúc hiện tại, ghi rõ; không phá code production chỉ để làm test lịch sử pass.
- ZIP phát hành không bọc thêm thư mục cha.

---

# 6. Tài liệu bắt buộc liên quan

- `AGENTS.md` — quy tắc chọn chế độ làm việc (file này).
- `PROJECT_MAP.md` — lỗi/module → file cần đọc.
- `project_docs/README.md` — danh mục tài liệu/SQL bắt buộc giữ lại.
- `project_docs/FIX_NHANH_PES_ARENA.md` — prompt chi tiết cho FIX NHANH.
- `project_docs/LOGGING_GUIDE.md` — chuẩn log/runtime.
- `Log.md` — lịch sử thay đổi phiên bản.

## Quy tắc ưu tiên

Nếu tài liệu cũ mâu thuẫn với `AGENTS.md`, ưu tiên `AGENTS.md` cho **quy trình làm việc**; ưu tiên code/schema hiện tại cho **hành vi runtime thực tế**.
