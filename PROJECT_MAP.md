> **V1.3.79 Emergency Safety Rule:** Không prune/xóa CSS legacy hoặc compatibility Python chỉ dựa trên static grep. Mọi cleanup giao diện phải có visual regression thực tế Host/Guest/Profile/History/Players trước khi phát hành.

# PES ARENA — PROJECT MAP

> **BẮT BUỘC:** trước khi dùng file map này, đọc `AGENTS.md` ở thư mục gốc để tự chọn chế độ **FIX NHANH / NÂNG CẤP MODULE / AUDIT TOÀN HỆ THỐNG**.
> Mục đích: tra nhanh **lỗi nào → đọc file nào**, tránh phải quét toàn bộ dự án mỗi lần sửa.
> Cập nhật: V1.3.78 — 08/08/2026 (Asia/Bangkok)

## 1. Quy tắc FIX NHANH

Khi xử lý lỗi, đọc theo thứ tự:

1. `PROJECT_MAP.md` → xác định module sở hữu.
2. File Frontend liên quan → HTML/JS/CSS đúng phạm vi.
3. File Backend route/service/repository tương ứng.
4. Bảng Supabase/chức năng DB nếu luồng có ghi/đọc dữ liệu.
5. `logs/pes_arena.log` hoặc Vercel log → lọc theo `request_id`.
6. Chạy test đúng module trước; chỉ chạy full test khi thay đổi dependency chung.

Không sửa module khác nếu chưa chứng minh dependency liên quan.

---

## 2. Bootstrap / App core

| Khu vực | File chính | Trách nhiệm |
|---|---|---|
| Flask bootstrap | `app.py` | tạo Flask app, env, request hooks, các route legacy chưa tách |
| Date/time | `modules/datetime_utils.py` | UTC/VN datetime helpers |
| Cache | `modules/cache_utils.py` | request cache + TTL cache |
| Logging | `modules/observability/app_logging.py` | request ID, request timing, exception, JSONL log |
| System settings | `modules/core/system_settings_runtime.py` | feature toggle, Quick Match config, repeat-opponent config, maintenance |
| Dispute evidence | `modules/core/dispute_evidence.py` | validate/resize/upload/sign URL ảnh tranh chấp |
| Static assets | `modules/static_asset_service.py` | URL asset Supabase/static |
| Session runtime | `modules/session_runtime_service.py` | idle timeout / session guard |
| System feature service | `modules/system_feature_service.py` | post-login/dashboard behavior |

### Core compatibility modules

`app.py` vẫn bind public function từ `modules/core/*` vào `globals()` để route cũ không bị vỡ import.

| Module | Trách nhiệm |
|---|---|
| `modules/core/achievements.py` | thành tích người chơi |
| `modules/core/rank_team_service.py` | rank range, team pool, Smart Random |
| `modules/core/room_runtime.py` | room timeout/read model/enrichment |
| `modules/core/user_repository.py` | user/device/admin reads |
| `modules/core/match_repository.py` | match/dispute/invite reads |
| `modules/core/social_runtime.py` | announcement/chat/streak data |
| `modules/core/matchmaking_runtime.py` | active room/match/busy snapshot |

---

## 3. Phòng đấu

### Frontend

| Thành phần | File |
|---|---|
| Orchestrator | `templates/room_detail.html` |
| Topbar | `templates/room/_topbar.html` |
| Chủ phòng | `templates/room/_host_card.html` |
| Trung tâm trận đấu | `templates/room/_center_stage.html` |
| Đối thủ | `templates/room/_guest_card.html` |
| Parsec/chat rail | `templates/room/_side_rail.html` |
| Mode + lịch sử | `templates/room/_bottom_modes_history.html` |
| Extra controls | `templates/room/_extra_controls.html` |
| Runtime/polling | `templates/room/scripts/_room_runtime.html` |
| Chat | `templates/room/scripts/_room_chat.html` |
| Dialog | `templates/room/scripts/_room_dialogs.html` |
| CSS room | `static/css/room/` |
| Khung gốc Room + biến nền tảng + responsive root | `static/css/room/00-room-core.css` |
| Logo chế độ + 6 thẻ chế độ | `static/css/room/13-mode-stability.css` |
| Bố cục khung phòng + Chủ phòng/Đối thủ + topbar/chia sẻ + logo PES ARENA + tiêu đề chọn CLB | `static/css/room/14-shell-player-stability.css` |
| Nút/trạng thái hành động trong phòng | `static/css/room/15-room-actions-stability.css` |
| Rail thông tin + Parsec + lịch sử phòng | `static/css/room/16-side-rail-history-stability.css` |
| Khu vực giữa phòng / VS / tỷ số / HUD trạng thái | `static/css/room/17-center-match-stability.css` |
| Chế độ đang chơi + trạng thái sẵn sàng/mở khóa | `static/css/room/18-active-mode-status-stability.css` |

### Backend

| Luồng | File |
|---|---|
| Vào/thoát/ready/kick phòng | `modules/room_access_routes.py` |
| Chọn/quay CLB | `modules/room_team_routes.py` |
| Kết quả/xác nhận/tranh chấp | `modules/room_result_routes.py` + `modules/match_result_service.py` |
| Đá tiếp/rematch | `modules/room_rematch_routes.py` |
| State/timeout/read model | `modules/core/room_runtime.py` + route state còn trong `app.py` |
| Lịch sử trận | `modules/match_history_routes.py` |
| Ảnh bằng chứng | `modules/core/dispute_evidence.py` |

---

## 4. Rank / RP / chế độ thi đấu

| Chức năng | File chính |
|---|---|
| Công thức RP | `modules/rp_formula.py` |
| Engine tính delta | `modules/rp_engine.py` |
| Daily Rank limit | `modules/daily_rank_limit_service.py` |
| Repeat opponent factor | `modules/repeat_opponent_rp_service.py` |
| Inactivity RP | `modules/inactivity_rp_service.py` |
| Weekly reward | `modules/weekly_rp_rewards_service.py` |
| Catalog mode | `modules/rank_modes/catalog.py` |
| Unlock / điều kiện mode | `modules/rank_modes/service.py` |
| Bật/tắt mode | `modules/rank_mode_toggle/service.py` |
| Series orchestrator | `modules/rank_series/service.py` |
| Series DB | `modules/rank_series/repository.py` |
| Series routes | `modules/rank_series/routes.py` |
| Lượt đi/về | `modules/rank_series/modes/home_away.py` |
| BO3 | `modules/rank_series/modes/bo3.py` |
| Tactical BO3 | `modules/rank_series/modes/tactical_bo3.py` |
| Ban/Pick BO3 | `modules/rank_series/modes/ban_pick_bo3.py` |

---

## 5. Invite / Presence / Quick Match

> **V1.3.61: chưa di chuyển route legacy khỏi `app.py`** vì nhiều regression test đang kiểm tra source trực tiếp.

| Luồng | File |
|---|---|
| Gửi/nhận/cancel invite | route legacy trong `app.py` + `modules/invites/service.py` |
| Online/offline | `modules/presence/service.py` + heartbeat route trong `app.py` |
| Quick Match priority | `modules/quick_match/service.py` + route legacy trong `app.py` |
| Busy/active match | `modules/core/matchmaking_runtime.py` |
| Quick Match config | `modules/core/system_settings_runtime.py` |

Khi sửa Invite/Quick Match: **không chuyển route sang file khác trong cùng bản fix**, trừ khi cập nhật toàn bộ source-based regression test cùng lúc.

---

## 6. Người dùng / Profile / Auth

| Chức năng | File |
|---|---|
| Login/register/password/logout | route legacy trong `app.py` |
| User repository | `modules/core/user_repository.py` |
| Profile routes | `modules/profile/routes.py` |
| Profile service | `modules/profile/service.py` |
| Profile repository | `modules/profile/repository.py` |
| Equipment/badge | `modules/profile/equipment_service.py` |

---

## 7. Admin

| Tab/luồng | File |
|---|---|
| Dashboard | `modules/admin_dashboard_routes.py` |
| System | `modules/admin_system_routes.py` |
| Thiết kế phòng đấu / Room UI Designer | `modules/admin_room_ui/` + `templates/admin/tabs/room-ui.html` + `static/css/admin/room-ui-designer.css` + `static/js/admin/room-ui-designer.js` |
| Account | `modules/admin_account_routes.py` |
| Match | `modules/admin_match_routes.py` |
| Player | `modules/admin_player_routes.py` |
| Data | `modules/admin_data_routes.py` |
| Economy | `modules/admin_economy/` |
| Shop | `modules/admin_shop/` |
| Ranking rebuild | `modules/admin_ranking_rebuild.py` + `modules/ranking_rebuild_service.py` |
| System settings runtime | `modules/core/system_settings_runtime.py` |

---

## 8. Economy / Shop

| Chức năng | File |
|---|---|
| Zcoin | `modules/zcoin/` |
| Daily Check-in | `modules/daily_checkin/` |
| Gift Codes | `modules/gift_codes/` |
| Shop | `modules/shop/` |
| Inventory | `modules/inventory/` |
| Lucky Box | `modules/luckybox/` |

---

## 9. Parsec

| Chức năng | File |
|---|---|
| Routes | `modules/parsec_room/routes.py` |
| Service | `modules/parsec_room/service.py` |
| UI | `templates/room/_side_rail.html` và partial liên quan |

---

## 10. CSS / Assets

| Khu vực | File |
|---|---|
| Compatibility CSS entry | `static/style.css` |
| Legacy CSS đã prune | `static/css/legacy/` — chỉ giữ selector còn tồn tại trong runtime source |
| Room CSS | `static/css/room/` |
| Room UI Designer runtime | `modules/admin_room_ui/` lưu `room_ui_designer_config` trong `system_settings`; CSS variables được truyền tại `templates/room_detail.html` |
| Admin CSS | `static/css/admin/` nếu có |
| Asset helper | `modules/static_asset_service.py` |
| Supabase manifest | `SUPABASE_ASSET_MANIFEST.csv` |

**Quy tắc:** lỗi logic không sửa CSS. Lỗi hiển thị mới kiểm tra cascade/scoped selector.

---

### Chính sách ảnh từ V1.3.62

- Ảnh UI dùng chung: Supabase `pes-assets/v1/` — không giữ bản local trùng lặp.
- Ảnh Shop: Supabase `pes-assets/v1.14.41/shop/`.
- Lucky Box: Supabase `pes-assets/v1.14.41/luckybox/`.
- Room: Supabase `pes-assets/room-assets/v1.3.18/`.
- Logo 6 chế độ Rank: Supabase `pes-assets/room-assets/v1.3.40/modes/`.
- Logo CLB/giải: bucket `team-logos`.
- `modules/static_asset_service.py` là nguồn duy nhất tạo URL ảnh giao diện.
- Không tạo lại `UPLOAD_SUPABASE/` trong ZIP Production sau khi asset đã được xác minh trên Storage.
- Không xóa template/partial/module trong quá trình dọn asset chỉ vì không thấy tham chiếu trực tiếp; phải coi regression test và include động là dependency.

## 11. Database / Supabase

| Nhóm | Nơi kiểm tra |
|---|---|
| SQL migration mới | `migrations/` |
| SQL/docs lịch sử | `docs/*.sql` |
| Query runtime | repository/service của module sở hữu |
| Retry/query logging | `execute_query()` trong `app.py` + observability |

Không chạy SQL thay đổi dữ liệu thật trong test nếu chưa có guard/test DB rõ ràng.

---

## 12. Logging / Debug

| File | Mục đích |
|---|---|
| `Log.md` | changelog phiên bản, không phải runtime log |
| `logs/pes_arena.log` | runtime JSONL local khi bật |
| `project_docs/LOGGING_GUIDE.md` | quy trình debug chuẩn |
| `modules/observability/app_logging.py` | logger implementation |

### Chuỗi debug chuẩn

`UI action → endpoint → request_id → service/repository → Supabase → response → UI render`

---

## 13. Test strategy

1. Test file/module đang sửa.
2. Test dependency trực tiếp.
3. `python -m py_compile` cho Python đã đổi.
4. Test source/boundary nếu có move module.
5. Full `pytest` cuối cùng; nếu baseline đã lỗi thì ghi rõ **baseline lỗi nào / lỗi mới nào**.

### Ghi chú test lịch sử

- Một số source-test cũ vẫn đọc cấu trúc `room_detail.html` monolith; không phá kiến trúc module hiện tại chỉ để làm test lịch sử pass.
- SQL lịch sử còn cần để test/khôi phục đã được gom tại `project_docs/sql/` từ V1.3.69.
## 14. Tài liệu / SQL giữ lại

- `AGENTS.md`, `PROJECT_MAP.md`, `Log.md`: giữ ở root vì là entrypoint vận hành.
- `project_docs/`: toàn bộ tài liệu vận hành còn cần.
- `project_docs/sql/`: toàn bộ SQL duy nhất còn cần cho khôi phục/schema/test; không giữ bản trùng ở root hoặc `docs/`.
- Các audit/version-note `.md` cũ đã loại khỏi bản phát hành từ V1.3.69.

## Black Box V1.3.68
- Runtime/service: `modules/blackbox/`
- Browser Safety Lab: `static/js/blackbox_safety_lab.js`
- Storage schema: `project_docs/sql/20260808_blackbox.sql`
- Hai bảng `blackbox_events` và `blackbox_incidents` là server-only; production phải chạy migration trước khi Storage check có thể PASS.



## V1.3.74 — Room action visibility
- V1.3.110: quyền quản lý nút phòng đấu đã chuyển sang `static/css/room/15-room-actions-stability.css`; `08-action-layout-guard.css` chỉ còn phần legacy chưa chuyển.
- Nút theo trạng thái render ở `templates/room/_center_stage.html`; bản polling tương ứng ở `templates/_room_live_content.html`.
- Nút host đưa khách khỏi phòng ở `templates/room/_guest_card.html`.


## V1.3.76 — Room pre-start hierarchy + Invite response

- Invite accept/reject visual module: `static/css/invite_center.css`; dynamic markup: `static/js/invite_center.js`; server markup: `templates/base.html`, `templates/invites.html`.
- Room waiting/Series orchestration: readiness state belongs to player card; center stage no longer renders duplicate fake disabled status buttons.
- V1.3.110: phần hiển thị pre-start/action đã được gom về `static/css/room/15-room-actions-stability.css`; `10-prestart-flow.css` chỉ giữ phần legacy chưa chuyển. Host start control uses a dedicated lane above the bottom action dock; guest Ready state uses only a compact flow line when waiting for Host.
- Applies to `home_away`, `bo3`, `tactical_bo3`, `ban_pick_bo3` as well as single-match modes.

## V1.3.77 — Global Gaming Neon 3D Buttons
- `static/css/gaming_neon_buttons.css`: lớp visual cuối cho nút giao diện người chơi.
- `templates/base.html`: gắn `data-ui-scope=player/admin` và nạp Gaming Neon CSS sau page CSS.
- Quy tắc: không áp dụng cho Admin và mọi control trong khu Parsec; không sửa logic/ID/route/kích thước layout.


## V1.3.78 — Dead-code cleanup
- `static/css/legacy/`: loại selector có class/ID không còn tồn tại trong templates/JS/Python runtime; không prune selector động/không chắc chắn.
- Đã bỏ `static/css/admin.css` vì không được load ở runtime.
- Đã bỏ compatibility Python cũ `modules/zcoin_service.py` và `modules/zcoin_routes.py`; runtime dùng `modules/zcoin/`.

## V1.3.80 — Button CSS final cascade

- `static/css/gaming_neon_buttons.css` là lớp visual cuối cho nút phía người chơi.
- Semantic màu được ghi bằng giá trị `background/border/box-shadow` cụ thể để thắng các legacy `!important` có specificity cao.
- Room có cascade guard riêng; Admin và Parsec vẫn loại trừ.
- Khi sửa màu nút sau V1.3.80, ưu tiên chỉnh file này thay vì thêm một lớp `!important` mới trong Room legacy.



## V1.3.81 — Quy tắc scope Gaming Neon

- `static/css/gaming_neon_buttons.css` KHÔNG được target bare `button` toàn cục.
- Chỉ action button có class rõ (`.btn`, `.arena-btn`, CTA chuyên dụng) mới nhận Gaming Neon.
- Các component dùng thẻ `button` nhưng là card/tab/selector (đặc biệt `room-master-mode-card`, `room-mode-select-btn`, `series-club-btn`) phải giữ CSS component riêng.
- Admin và Parsec tiếp tục nằm ngoài Gaming Neon scope.


## V1.3.82 — Gaming Neon button theme
- `modules/core/system_settings_runtime.py`: đọc cấu hình màu semantic từ `system_settings` key `gaming_neon_button_theme`.
- `modules/admin_system_routes.py`: Admin lưu bộ màu tại `/admin/system/button-theme`.
- `templates/admin/tabs/system.html`: bảng chọn màu cho Mời đấu, Tìm nhanh, success, danger, primary, secondary, default, Random3/Lucky Box.
- `templates/base.html`: truyền semantic palette xuống player UI bằng CSS variables; Admin/Parsec không nhận skin.
- `static/css/gaming_neon_buttons.css`: Gaming Neon 3D dùng màu semantic do Admin cấu hình.
- `.gaming-invite-action`: mọi nút Mời đấu phải dùng role `invite` (mặc định vàng).
- `.gaming-quick-action`: nút Tìm nhanh dùng role `quick` (mặc định xanh lá).

## V1.3.84 Room template safety
- Pre-start action markup phải được cập nhật đồng thời ở `templates/room/_center_stage.html` và `templates/_room_live_content.html`.
- Sau mọi thay đổi Jinja Room, bắt buộc parse toàn bộ `templates/**/*.html` trước khi đóng ZIP.
