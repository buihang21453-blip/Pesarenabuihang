# CHẾ ĐỘ FIX NHANH PES ARENA

> **Quy tắc cấp dự án:** `AGENTS.md` tự phân loại mọi yêu cầu thành FIX NHANH / NÂNG CẤP MODULE / AUDIT TOÀN HỆ THỐNG. File này chỉ mô tả chi tiết chế độ FIX NHANH.

> Dùng nguyên prompt này cho các lần sửa lỗi nhỏ / nâng cấp có phạm vi rõ ràng.

```text
CHẾ ĐỘ FIX NHANH PES ARENA

Chỉ xử lý đúng lỗi tôi mô tả.

Xác định luồng Frontend → Backend → Database.
Chỉ đọc file liên quan.
Không audit toàn bộ dự án.
Không refactor file không liên quan.
Không thay đổi giao diện nếu tôi không yêu cầu.
Kiểm tra CSS chỉ khi lỗi liên quan hiển thị.
Giữ tương thích với hệ thống hiện tại.
Sau khi sửa, kiểm tra import/syntax và dependency liên quan.
Chỉ đóng gói những file đã thay đổi.
Ghi Log.md: file, chức năng, thay đổi.

Lỗi/Yêu cầu:
[Điền lỗi hoặc yêu cầu tại đây]
```

## Cách dùng nhanh

1. Gửi prompt trên.
2. Điền một lỗi/yêu cầu duy nhất.
3. Nếu có log, gửi thêm `request_id`, endpoint hoặc đoạn lỗi gần nhất.
4. Nếu biết module, ghi tên module; nếu không biết, tra `PROJECT_MAP.md`.

## Quy tắc phạm vi

- Không biến FIX NHANH thành audit toàn dự án.
- Không dọn CSS khi lỗi là backend.
- Không refactor route/module khác chỉ vì “tiện tay”.
- Nếu phát hiện lỗi ngoài phạm vi, ghi chú riêng; không tự sửa nếu nó không chặn yêu cầu hiện tại.
