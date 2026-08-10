# CSS OWNERSHIP — V1.2.49

## Cascade chuẩn
`design_tokens.css` → `style.css` (legacy) → `components/buttons.css` → `button_sizes.css` → feature modules → page module.

## Chủ sở hữu
| Thành phần | Owner |
|---|---|
| Biến màu dùng chung | `static/css/core/design_tokens.css` |
| Màu/nền/viền/shadow `.btn` | `static/css/components/buttons.css` |
| Kích thước `.btn` | `static/css/button_sizes.css` |
| Room legacy/compat | `static/css/room_detail.css` |
| Room V2 hiện hành | `static/css/room_v2.css` |
| Parsec | `static/css/parsec_room.css` |
| Quick Match | `static/css/quick_match.css` |
| Profile | `static/css/profile_showcase.css` |
| Shop/Inventory | `static/css/shop_phase3.css` |
| Admin | `static/css/admin_dashboard.css` + module admin tương ứng |
| Legacy chung | `static/style.css` |

## Luật bắt buộc
1. `static/css/**` không dùng `!important`.
2. Không tạo thêm visual rule generic `.btn` ngoài `components/buttons.css`.
3. `button_sizes.css` chỉ điều khiển kích thước/khoảng cách.
4. Page module phải có scope riêng.
5. `style.css` là legacy compatibility; không append fix mới vào cuối file.
6. Chạy `python scripts/check_css_contract.py` trước khi đóng gói.
