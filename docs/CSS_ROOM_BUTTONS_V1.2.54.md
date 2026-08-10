# CSS ownership - cum nut trung tam V1.2.54

## Owner
- `static/css/room/buttons.css`: background, border, glow, radius, mau chu/icon, hover/active/focus/disabled.
- `static/css/room_v2.css`: vi tri, flex/grid, width/height responsive cua cum action.
- `static/css/quick_match.css`: trang thai/behavior Quick Match cu; cac selector skin cu bat buoc `:not(.room-neon-btn)`.
- `static/css/room_detail.css`: legacy; cac rule `.room-center-action-btn` cu da duoc tach khoi `.room-neon-btn` o cac diem xung dot kich thuoc.

## Quy tac
1. Khong them mau/gradient/border/shadow cho `.room-neon-btn` ngoai `room/buttons.css`.
2. Khong dung `!important` de thang cascade.
3. Khong sua vi tri cum nut trong file skin.
4. Muon doi mau: sua bien `--room-neon-color` va `--room-neon-rgb` cua tung variant.
