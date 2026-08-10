# V1.2.51 — Audit CSS cụm nút trung tâm + 7 logo chế độ

## 1. Thứ tự CSS thực tế trên trang Room

1. `css/core/design_tokens.css` — token toàn hệ thống.
2. `style.css` — legacy toàn dự án.
3. `css/components/buttons.css` — skin `.btn` dùng chung.
4. `css/button_sizes.css` — kích thước `.btn` dùng chung.
5. `css/room_detail.css` — legacy riêng trang Room.
6. `css/rank_mode_toggle.css` — chọn chế độ Rank cũ.
7. `css/parsec_room.css` — Parsec.
8. `css/quick_match.css` — hành vi/trạng thái Quick Match.
9. `css/room_v2.css` — layout Room V2 hiện hành.
10. `css/room/buttons.css` — skin cụm nút trung tâm.
11. `css/room/mode_cards.css` — kích thước ảnh 7 mode.

`room_detail.html` nạp 3 file cuối bằng `page_styles`, vì vậy chúng là lớp trang cuối cùng.

## 2. Module có thể tác động cụm nút trung tâm

| Module | Tác động trước V1.2.51 | Trạng thái V1.2.51 |
|---|---|---|
| `style.css` | `.btn`, `.btn.green/.red/.gold` legacy | Không còn match với neon trung tâm vì đã bỏ class `.btn` khỏi các nút neon |
| `components/buttons.css` | gradient/màu `.btn` toàn hệ thống | Không còn match với neon trung tâm |
| `button_sizes.css` | min-height/padding/font `.btn` | Không còn match với neon trung tâm |
| `room_detail.css` | nhiều đời `.room-center-primary-actions`, `.room-center-action-btn`, `.room-action-zone` | Chỉ còn vai trò legacy/layout nền; skin neon không lấy màu/nền từ đây |
| `quick_match.css` | skin gradient Quick Match + pulse filter | Skin cũ đã dùng `:not(.room-neon-btn)`; pulse cũ cũng không tác động neon |
| `room_v2.css` | vị trí, độ rộng, chiều cao responsive cụm trung tâm | HỢP LỆ: owner layout/kích thước, không owner màu/nền/viền neon |
| `room/buttons.css` | màu/nền/viền/glow/radius/icon | HỢP LỆ: owner duy nhất của skin Neon Gaming |
| JS `quick_match.js` | đổi text/trạng thái/class khi tìm | HỢP LỆ: chức năng, không đặt CSS inline |

## 3. Những lệnh hợp lệ cho cụm nút

### `room_v2.css` — được phép
- `width`, `max-width`, `margin`
- `display`, `grid-template-columns`, `gap`
- `height`, `min-height`, `font-size` responsive theo biến Admin
- vị trí và bố cục cụm nút

### `room/buttons.css` — được phép
- `background`
- `border`, `border-radius`
- `box-shadow`, `text-shadow`
- `color`
- trạng thái `hover/active/focus/disabled`
- màu icon
- căn nội dung bên trong nút

### Không được phép ở module khác
- đặt lại `background`, `border-color`, `box-shadow`, `border-radius` cho `.room-neon-btn`
- thêm `!important`
- thêm gradient/3D/translate/scale vào nút neon
- dùng `.btn.green/.red/.gold` cho nút neon trung tâm

## 4. Module có thể tác động 7 logo chế độ

| Module | Tác động | Trạng thái V1.2.51 |
|---|---|---|
| `room_v2.css` | card, grid, chiều cao card, tên/status | HỢP LỆ; không trực tiếp size/scale ảnh V2 |
| `room/mode_cards.css` | width/height/object-fit/transform của ảnh | OWNER DUY NHẤT |
| `room_detail.css` | có rule cũ cho `.room-mode-card img`, class khác | Không match `.room-v2-mode-card > img` |
| `admin/room-ui-designer.css` | preview Admin `.rui-mode-icon` | Chỉ Preview, không tác động Room thật |
| inline `--rui-mode-scale`, `--rui-mode-logo-size` | cấu hình cũ | Không được dùng để scale riêng 7 ảnh Room thật |

Kích thước Room thật hiện ép chung: desktop `64x64`, <=1250px `56x56`, <=700px `48x48`.

Nếu 7 hình vẫn nhìn to/nhỏ khác nhau dù CSS box bằng nhau, nguyên nhân là khoảng trống trong suốt nằm *bên trong file WebP*. Khi đó cách đúng là chuẩn hóa canvas/transparent padding của bộ asset; không thêm `scale(.7)`, `scale(1.2)` riêng cho từng logo.

## 5. Skin Neon Gaming đã chốt

- Nền tối bán trong suốt: `rgba(3,10,16,.82)`.
- Viền neon 1px.
- Bo góc 8px.
- Glow nhẹ, không gradient mạnh.
- Không translate/scale/3D.
- Chữ trắng.
- Icon nhận màu cùng viền và ép ưu tiên dạng symbol text.
- Tìm nhanh/Sẵn sàng: xanh lá.
- Mời đấu/Đá tiếp: vàng.
- Thoát/Bỏ cuộc: đỏ.
- Hủy: xám xanh.

## 6. Quy tắc nâng cấp tiếp theo

Muốn đổi **màu/phong cách** 3 nút: chỉ sửa `static/css/room/buttons.css`.

Muốn đổi **kích thước/vị trí** 3 nút: sửa layout tại `static/css/room_v2.css` hoặc cấu hình Admin tương ứng.

Muốn đổi **kích thước chung 7 logo**: chỉ sửa `--room-mode-logo-fixed-size` trong `static/css/room/mode_cards.css`.
