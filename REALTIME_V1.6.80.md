# PES Arena V1.6.80 — Realtime Production Hardening

## Mục tiêu
V1.6.80 không thay luật chơi hay giao diện. Realtime chỉ là tín hiệu "có thay đổi"; Flask API + Supabase Database vẫn là nguồn dữ liệu chuẩn.

## Gia cố chính
- Chỉ chấp nhận event đã định nghĩa: Invite/Match/Room/Chat/Ready.
- Broadcast không mang dữ liệu game/người dùng; payload bị ép thành `{changed:true}`.
- Topic user/room tiếp tục là HMAC khó đoán.
- Khi Realtime reconnect, browser tự resync Invite/Active Room/Room State/Chat.
- Khi trình duyệt có mạng lại hoặc quay lại tab, browser tự resync.
- Room polling chỉ giãn chu kỳ khi chính room-channel đã SUBSCRIBED; nếu room-channel lỗi thì tự dùng polling nhanh dự phòng.
- Presence reconnect chỉ ghi heartbeat tối đa 1 lần/5 phút ở client.
- Event lạ/giả chỉ bị bỏ qua; event hợp lệ cũng chỉ đánh thức API, không tự sửa state game.

## Fallback
- Invite: Realtime OK ~60s kiểm tra dự phòng; Realtime lỗi 15–30s tùy hoạt động.
- Room state: Realtime OK 30s; room-channel lỗi quay lại chu kỳ state cũ 4–18s tùy trạng thái.
- Room chat: Realtime OK 60s; room-channel lỗi 6s.

## Biến môi trường
Cần `SUPABASE_URL` và một trong `SUPABASE_PUBLISHABLE_KEY` hoặc `SUPABASE_ANON_KEY` cho browser.
Backend broadcast dùng `SUPABASE_SECRET_KEY` hoặc `SUPABASE_SERVICE_ROLE_KEY`.
Không bao giờ đưa secret/service-role key xuống browser.
