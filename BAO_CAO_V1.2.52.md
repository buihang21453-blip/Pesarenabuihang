# V1.2.52 — Cân đối chiều rộng nút Tìm Nhanh

## Nguyên nhân
Rule cuối trong `room_v2.css` cho `.room-quick-match-row` dùng cùng chiều rộng tối đa 290px với cụm hai nút bên dưới; sau đó nút con `width:100%`, khiến Tìm Nhanh kéo dài gần bằng tổng hai nút.

## Sửa
- `.room-center-primary-actions`: vẫn tối đa 290px.
- `.room-quick-match-row`: tách riêng, `width: clamp(132px, 44%, 145px)` và `max-width:145px`.
- Nút Tìm Nhanh vẫn `width:100%`, nhưng chỉ fill hàng compact 132–145px.
- Không thay đổi màu, glow, bo góc, icon, vị trí dọc hay logic.

## Kết quả mong muốn
Tìm Nhanh nằm giữa, có chiều rộng gần bằng một nút Mời Đấu/Thoát Phòng thay vì dài bằng cả cụm hai nút.
