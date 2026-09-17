### V1.6.0 – Lịch GĐ2 đủ ba Tier
- `modules/tournament_competition_parts/league_draw.py`: thuật toán sinh 4 lượt từ mẫu đồ thị hợp lệ, hoán vị ngẫu nhiên trong Tier; `validate_four_match_draw()` kiểm tra 16 HLV 5–6–5, 32 trận, 4 đối thủ khác nhau, đủ 3 Tier trong cả 4 trận.
- `modules/tournament_competition_parts/league.py`: route POST `/admin/tournaments/<tournament_id>/league/generate` dùng thuật toán mới, xác thực trước ghi DB; route `/league/start` kiểm tra lịch đã lưu có đủ 3 Tier.
- `templates/admin.html`: mô tả luật cập nhật; `core.py` metadata luật; `app.py` version V1.6.0. Không migration.


### V1.5.99
- V1.5.99: modules/tournament_competition_parts/admin.py thêm route admin_tournament_gd2_draw_time lưu competition_timing.club_draw_at (giữ nguyên các khóa thời gian khác); core.py truyền mốc về admin; tournament_routes.py gắn mốc vào card; c1_media.html thay overlay GĐ1 bằng countdown GĐ2; page_scripts.html hiển thị ngày giờ Việt Nam và trạng thái khi hết giờ. Không có migration mới.


### V1.5.86: league.py xử lý start_now; rooms.py chặn stage và nạp CLB cố định khi vào phòng theo trận; templates/admin.html có nút bắt đầu ngay. Các luồng tự động GĐ1 chưa hoàn thiện.
# PROJECT_MAP — PES Arena

**Baseline:** V1.5.84  
**Stack:** Flask + Jinja2 + Supabase + vanilla CSS/JavaScript  
**Entry point:** `app.py`  

> Mục tiêu của file này là giúp xác định nhanh: yêu cầu thuộc module nào, file nào, dữ liệu nào và vùng nào có nguy cơ bị ảnh hưởng trước khi sửa.

## 1. Kiến trúc tổng thể

```text
Browser
  ↓ Flask routes
app.py (bootstrap, config, shared helpers, dependency wiring)
  ├─ modules/*_routes.py            route theo miền nghiệp vụ
  ├─ modules/<feature>/routes.py    feature package
  ├─ modules/*_service.py           nghiệp vụ dùng chung
  ├─ modules/<feature>/service.py   service theo feature
  ├─ modules/<feature>/repository.py truy cập dữ liệu
  ↓
Supabase (PostgreSQL + Storage/RPC)

Render UI
  routes → templates/*.html / templates/** → static/css + static/js
```

`app.py` vẫn là composition root lớn: khai báo cấu hình, helper legacy, cấu hình service rồi đăng ký các route module bằng `register_routes(globals())`. Vì vậy khi tách module tiếp phải bảo toàn dependency được truyền từ `app.py`.

## 2. Thư mục gốc

| File/thư mục | Vai trò | Lưu ý khi sửa |
|---|---|---|
| `app.py` | Khởi tạo Flask, Supabase, hằng số, helper dùng chung, cấu hình service, đăng ký route | `APP_VERSION` phải tăng và đồng bộ mỗi release |
| `modules/` | Backend chia theo miền nghiệp vụ | Ưu tiên sửa đúng module, tránh đưa logic mới ngược lại `app.py` |
| `templates/` | Jinja UI | Giữ `id/class/data-*`, endpoint và biến Jinja khi refactor |
| `static/` | CSS, JS, SVG | `style.css` là CSS legacy/global; feature mới nên ưu tiên file riêng |
| `SQL_CU/` | Migration/SQL lịch sử | Không chạy/sửa SQL nếu yêu cầu không cần schema/data migration |
| `SQL_V1.4.65_MIGRATION_TRACKER.sql` | Theo dõi migration cũ | Chỉ đụng khi có migration tương ứng |
| `teams_data.py` | Dữ liệu/logic hỗ trợ đội bóng | Có liên quan random/team nếu được import |
| `requirements.txt` | Python dependencies | Thêm package phải đánh giá Vercel/deploy |
| `vercel.json` | Cấu hình deploy Vercel | Không đổi cho sửa UI/nghiệp vụ thông thường |
| `.env.example` | Mẫu biến môi trường | Không chứa secret thật |
| `PROJECT_MAP.md` | Bản đồ source | Cập nhật khi đổi cấu trúc/module/luồng |
| `PROJECT_RULES.md` | Quy tắc dự án | Bắt buộc tuân theo mỗi lần sửa |
| `CHANGELOG.md` | Lịch sử version | Cập nhật cùng mỗi release |

## 3. Backend — tài khoản, phiên và giao tiếp

| Module | Trách nhiệm chính |
|---|---|
| `auth_routes.py` | Login, register, logout, quên/đổi mật khẩu |
| `session_presence_routes.py` | Heartbeat, online/offline, timeout/presence API |
| `session_runtime_service.py` | Quyết định idle logout; bảo vệ phiên khi đang ở phòng |
| `dashboard_routes.py` | Dashboard/người chơi |
| `profile/` | Profile, avatar, display name; equipment/badge/name style |
| `notification_routes.py` + `notification_service.py` | Chuông/thông báo người dùng và tạo notification |
| `announcement_routes.py` | Thông báo hệ thống/Admin |
| `chat_routes.py` + `legacy_chat_service.py` | Chat global/phòng; room chat RAM/TTL |
| `invite_routes.py` | Lời mời trận, Quick Match và các điều kiện tìm đối thủ |
| `quick_match/service.py` | Xếp ưu tiên ứng viên Quick Match |
| `parsec_room/` | Parsec ID/link và context phòng |

## 4. Backend — phòng đấu, trận và BXH

| Module | Trách nhiệm chính | Tác động điển hình |
|---|---|---|
| `room_access_routes.py` | Vào/tạo/xem phòng, quyền truy cập | `room_detail.html`, room state |
| `room_api_routes.py` | API state/polling phòng | `pes_polling.js`, live room UI |
| `room_team_routes.py` | Ready, chọn/random đội, thao tác đội | Room state + team data |
| `room_result_routes.py` | Gửi/xác nhận/tranh chấp kết quả | matches, match_rooms, BXH |
| `room_rematch_routes.py` | Rematch/đá tiếp, gồm nhánh C1 | Cẩn thận state machine C1 |
| `match_history_routes.py` | Lịch sử trận | templates lịch sử/profile |
| `match_result_service.py` | Áp/reverse kết quả, đồng bộ room sau sửa Admin | RP/stats/match |
| `legacy_match_service.py` | Đọc/decorate match/dispute legacy | Nhiều route cũ phụ thuộc |
| `legacy_room_service.py` | Đọc/expire/timeout room | Không đổi trạng thái tùy tiện khi render |
| `legacy_room_activity_service.py` | Active room, cooldown, H2H | Invite/room/dashboard |
| `legacy_team_random_service.py` | Pool/random/team overall | Rank/Friendly/C1 team flow |
| `ranking_routes.py` | Trang BXH/public BXH | `ranking.html`, `public_ranking.html` |
| `legacy_ranking_service.py` | Rank ranges/tier/difficulty | RP và UI rank |
| `rp_engine.py`, `rp_formula.py` | Công thức RP | Thay đổi là phạm vi rủi ro cao |
| `repeat_opponent_rp_service.py` | Điều chỉnh RP gặp lại đối thủ | Match result |
| `daily_rank_limit_service.py` | Giới hạn số trận Rank/ngày | Rank flow |
| `inactivity_rp_service.py` | Phạt RP không hoạt động | Ranking/season |
| `ranking_lock_service.py` | Lock rebuild BXH đa instance | Admin rebuild |
| `ranking_rebuild_service.py`, `admin_ranking_rebuild.py` | Phát lại/rebuild BXH | Rủi ro dữ liệu cao |
| `forfeit_history_service.py` | Ghi lịch sử xử thua | Match/room stats |
| `win_streaks.py` | Chuỗi thắng/badge/event | Room/ranking UI |

## 5. Backend — Giải đấu C1

### V1.6.1 — Điều hành Lễ bốc thăm GĐ2
- `modules/tournament_competition_parts/core.py`: `_reward_ticket_phase_status`, `_close_reward_ticket_phase`, `_league_launch_readiness`, `_open_league_stage`, `_sync_competition_deadlines`; quản lý hạn vé và điều kiện mở GĐ2.
- `modules/tournament_competition_parts/admin.py`: POST `/admin/tournaments/<id>/gd2/draw-time`; lưu 3 mốc `club_draw_at`, `gd2_reward_ticket_deadline_at`, `league_start_at`.
- `modules/tournament_competition_parts/league.py`: Random CLB/vé thưởng, POST `/tournaments/<id>/club-draft/finalize`, gate sinh lịch, lễ công bố đối thủ Tier 1→2→3, Admin mở GĐ2.
- `modules/tournament_competition_parts/league_draw.py`: thuật toán 32 trận V1.6 giữ nguyên; 4 trận/HLV, đủ 3 Tier, không trùng.
- `modules/tournament_routes.py`: đưa mốc lễ/hạn vé/mở GĐ2 vào public tournament hub/card.
- `templates/admin.html`: khối kịch bản 5 bước + điều khiển 3 mốc + điều hành CLB/đối thủ.
- `templates/tournament/cards/c1_actions.html`: HLV dùng vé và `Chốt CLB cuối cùng`.
- `templates/tournament/cards/c1_media.html` + `templates/tournament/scripts/page_scripts.html`: countdown chuyển pha Lễ bốc thăm → Vé thưởng → Mở GĐ2.
- Dữ liệu: không schema mới; dùng `tournament_settings.setting_key=competition_timing`, `club_draft_v2`, `league_draw_v2`, `deadline_sync`.

**Luồng chuẩn V1.6.1:** 16 CLB gốc → pha vé thưởng đóng (3 HLV chốt hoặc hết hạn) → sinh 32 trận → công bố Tier 1→2→3 → mở GĐ2 theo lịch / tự mở sớm khi đủ điều kiện / Admin mở ngay.

Đây là miền nghiệp vụ lớn nhất hiện tại.

| Module | Vai trò |
|---|---|
| `tournament_routes.py` | Hub `/tournaments`, đăng ký/rút, hồ sơ HLV, admin registration/finance/access; dựng `landing_hub` và dữ liệu render |
| `tournament_competition.py` | **Composition root C1**: giữ API `register_routes(context)`, hằng số chung và đăng ký các partition theo thứ tự phụ thuộc; không còn chứa nghiệp vụ 4k+ dòng. |
| `tournament_test_mode.py` | Sandbox/Test C1, tạo player test, seed/generate stage, simulate/report/reset |
| `tournament_competition_parts/core.py` | Helper lõi: members/matches/ranking/progress/availability payload/countdown/KO helper/payload Admin + context processor. |
| `tournament_competition_parts/admin.py` | Route Admin nền tảng: test accounts, member/stage/match result, Pot. |
| `tournament_competition_parts/test_support.py` | 2 tài khoản test, Admin switch, ranking test, lịch sử random GĐ1, pool CLB test. |
| `tournament_competition_parts/rooms.py` | Phòng C1: open/invite/accept/enter/next-match/random CLB/result/confirm/dispute + nhánh test room. |
| `tournament_competition_parts/league.py` | Chọn CLB, sinh lịch GĐ2, timing/start, draft/random/reveal League Phase. |
| `tournament_competition_parts/scheduling.py` | Availability, Host đang rảnh API/toggle, đặt/accept/reject lịch, host admin, gia hạn GĐ1. |
| `tournament_competition_parts/rewards.py` | Kết thúc GĐ1/GĐ2, vé reroll Top 3, sinh/điều hành Knockout, thưởng hoàn thành sớm, reward admin. |
| `templates/tournaments.html` | **Orchestrator 32 dòng** của hub giải sau V1.5.76 |
| `templates/tournament_detail.html` | Template legacy/chi tiết; GET detail hiện chủ yếu tương thích/redirect theo lịch sử V1.5.54 |
| `templates/c1_rooms.html` | Trang/phần phòng C1 legacy/trung gian còn được giữ cho tương thích |

### 5.1 Backend C1 sau V1.5.84

```text
modules/
├─ tournament_competition.py          # composition root, ~80 dòng
└─ tournament_competition_parts/
   ├─ core.py                         # helper lõi + payload/ranking/context
   ├─ admin.py                        # route Admin cơ bản
   ├─ test_support.py                 # 2 TK test + Admin switch + test helpers
   ├─ rooms.py                        # vòng đời phòng C1 + result
   ├─ league.py                       # club/draw/Stage 2
   ├─ scheduling.py                   # availability/schedule/Host live
   └─ rewards.py                      # finish/reward/KO/reroll
```

**Thứ tự đăng ký bắt buộc:** `core → admin → test_support → rooms → league → scheduling → rewards`. `tournament_competition.py` gom helper được export từ partition trước và truyền sang partition sau để giữ nguyên dependency/endpoint mà không đưa logic trở lại `app.py`.

### 5.2 Cấu trúc `templates/tournament/` sau V1.5.76

```text
tournament/
├─ styles.html
├─ tournament_list.html
├─ components/
│  ├─ hero.html
│  ├─ filterbar.html
│  ├─ closed.html
│  ├─ database_not_ready.html
│  └─ availability_gate.html       # popup/gate lịch bắt buộc
├─ cards/
│  ├─ champions_league.html        # card C1 điều phối
│  ├─ c1_media.html                # ảnh/tiến trình/countdown
│  ├─ c1_header_nav.html           # 4 menu nhanh
│  ├─ c1_actions.html
│  ├─ c1_registration.html
│  └─ generic.html
├─ tabs/
│  ├─ ranking.html                 # 📊 BXH
│  ├─ schedule.html                # 📅 Lịch của tôi
│  └─ lobby.html                   # 🏟️ Sảnh chờ / Host đang rảnh
└─ scripts/
   ├─ page_scripts.html
   └─ legacy_tail_scripts.html
```

### 5.3 Map yêu cầu C1 → file ưu tiên

| Yêu cầu | File đầu tiên cần kiểm tra |
|---|---|
| Tiến trình GĐ1/countdown/thưởng | `cards/c1_media.html`, `tournament_routes.py` |
| 4 menu BXH/Lịch/Sảnh/C1 | `cards/c1_header_nav.html` |
| BXH giải | `tabs/ranking.html`, `tournament_competition_parts/core.py` |
| Lịch của tôi/đối thủ/giờ rảnh | `tabs/schedule.html`, `components/availability_gate.html`, `tournament_competition_parts/scheduling.py` |
| Sảnh chờ/Host đang rảnh | `tabs/lobby.html`, `tournament_competition_parts/scheduling.py` + `core.py` |
| Đăng ký giải/Host/khu vực | `cards/c1_registration.html`, `tournament_routes.py` |
| Phòng đấu C1 | `tournament_competition_parts/rooms.py` + room modules + `room_detail.html` partials |
| Test C1 | `tournament_test_mode.py` + `tournament_test_*.html` |

### 5.4 Luồng C1 quan trọng

```text
/tournaments
  → tournament_routes.py dựng tournament + landing_hub
  → tournaments.html include các partial
  → HLV khai báo availability nếu gate yêu cầu
  → Sảnh chờ đọc Host online/live
  → Phòng đấu C1 mở/tái sử dụng match_room
  → room modules xử lý ready/random/result
  → tournament_competition_parts/* cập nhật tournament_match/stage/ranking
```

**Quy tắc state:** không được tạo side effect DB chỉ vì render GET nếu không có chủ đích nghiệp vụ rõ ràng. Luồng C1 từng có nhiều lỗi do state `confirmed/waiting_ready` và chuyển trận; mọi sửa phần này phải test cả Host và Guest.

## 6. Kinh tế, vật phẩm và phần thưởng

| Package/module | Trách nhiệm |
|---|---|
| `zcoin/` | Route/service ZCoin hiện hành |
| `zcoin_routes.py`, `zcoin_service.py` | Bản legacy/tương thích; không xóa nếu chưa kiểm tra import/route |
| `shop/` | Catalog, mua item, repository/service |
| `inventory/` | Kho đồ/equip |
| `luckybox/` | Lucky Box user/admin, reward/rate/audit |
| `gift_codes/` | Gift code tạo/đổi/nhận |
| `daily_checkin/` | Điểm danh hằng ngày |
| `weekly_rp_rewards_service.py` | Thưởng RP tuần |
| `admin_shop/` | Quản trị shop |
| `admin_economy/` | Tổng quan/điều chỉnh kinh tế Admin |

## 7. Admin

| Module | Vai trò |
|---|---|
| `admin_dashboard_routes.py` | Dashboard Admin |
| `admin_account_routes.py` | Duyệt/ban/quyền/tài khoản test/reset password |
| `admin_player_routes.py` | Sửa player, presence/invisibility, reset/delete |
| `admin_match_routes.py` + `admin_match_service.py` | Sửa/xóa/xử lý match |
| `admin_system_routes.py` | Thiết lập hệ thống và công cụ Admin |
| `admin_data_routes.py` | Backup/export/data utilities |
| `season_routes.py` + `season_service.py` | Mùa giải, snapshot, reward config |

## 8. Frontend

### Template chính
`base.html` là layout chung. Các trang lớn gồm `dashboard.html`, `ranking.html`, `players.html`, `profile.html`, `room_detail.html`, `tournaments.html`, `admin.html`, `shop.html`, `inventory.html`, `notifications.html`.

`room_detail.html` vẫn rất lớn; UI động được tách một phần sang `partials/room_*`. Đây là ứng viên refactor tiếp theo nhưng chỉ làm theo đợt nhỏ.

### Static
- `static/style.css`: style global/legacy.
- CSS feature riêng: Admin, Lucky Box, Parsec, Profile, Quick Match, Rank mode, Shop, streak, ZCoin.
- JS feature riêng: polling phòng, session timeout, Quick Match, shop, profile, streak, ZCoin, admin preview.
- CSS/JS của `/tournaments` hiện vẫn nằm trong partial `templates/tournament/styles.html` và scripts partial; có thể tách sang static ở một version refactor riêng sau khi test ổn định.

## 9. Database/Supabase — bảng được source tham chiếu trực tiếp

Nhóm tài khoản/hệ thống: `users`, `user_devices`, `system_settings`, `registration_invite_codes`, `password_reset_requests`, `admin_activity_logs`, `admin_announcements`, `user_notifications`.

Nhóm trận/phòng: `match_rooms`, `matches`, `match_invites`, `match_disputes`, `chat_messages`, `teams`.

Nhóm Rank/mùa: `rank_seasons`, `rank_season_snapshots`, `rank_season_rewards`, `season_player_stats`, `weekly_rp_rewards`, `user_achievements`.

Nhóm giải đấu: `tournaments`, `tournament_stages`, `tournament_members`, `tournament_registrations`, `tournament_matches`, `tournament_hosts`, `tournament_clubs`, `tournament_availability_slots`, `tournament_schedule_requests`, `tournament_settings`, `tournament_reward_rules`, `tournament_reward_grants`, `tournament_fee_unmatched`.

Nhóm kinh tế: `zcoin_transactions`, `shop_items`, `shop_purchases`, `user_inventory`, `user_equipment`, `daily_checkins`, `gift_codes`, các bảng `lucky_box_*`.

`schema_migrations` theo dõi migration. Danh sách trên được lấy từ lời gọi `.table(...)` trong source; RPC/view được gọi động có thể không xuất hiện trong danh sách này.

## 10. Điểm rủi ro / nợ kỹ thuật hiện tại

1. `tournament_competition.py` khoảng **4.3k dòng / 66 route** — quá lớn; nên tách theo `schedule`, `lobby/presence`, `room`, `ranking/stages`, `rewards/clubs`, nhưng phải làm từng đợt.
2. `app.py` khoảng **2.8k dòng** — vẫn chứa nhiều helper/service legacy ngoài bootstrap.
3. `room_detail.html` khoảng **100 KB** — đã có partial nhưng vẫn cần refactor dần.
4. Có cặp `zcoin/` và `zcoin_routes.py`/`zcoin_service.py`; coi bản root là legacy cho tới khi xác minh không còn dependency.
5. Nhiều module dùng `configure(globals())` / `register_routes(globals())`; dependency coupling cao, không đổi signature hàng loạt.
6. Release notes lịch sử không liên tục; `CHANGELOG.md` chỉ ghi những version có file chứng cứ trong source.

## 11. Quy trình xác định phạm vi trước khi sửa

```text
Yêu cầu
→ xác định miền nghiệp vụ
→ PROJECT_MAP tìm module/template
→ grep route/endpoint/id/data-hook liên quan
→ xác định bảng DB + state liên quan
→ liệt kê ảnh hưởng chéo
→ sửa phạm vi nhỏ nhất
→ test 2 TK test + Admin nếu liên quan giải/tài khoản
→ tăng version + CHANGELOG/PROJECT_MAP nếu cần
→ kiểm tra + dọn ZIP
```


### V1.5.84 – lưu ý dependency của `tournament_competition_parts`
Các partition vẫn giữ endpoint cũ nhưng có thể tham chiếu helper/hằng số ở partition khác như khi còn monolith.
`tournament_competition.register_routes()` vì vậy xây dựng namespace chung hoàn chỉnh và đồng bộ namespace này vào tất cả partition sau khi đăng ký.
Không được bỏ bước đồng bộ này khi thêm partition mới.


### V1.5.84 – Duyệt IP & Admin Notification
- `app.py`: `registration_or_latest_ip_conflicts()` đối chiếu IP đăng ký + IP gần nhất.
- `modules/auth_routes.py`: registration/login hold khi trùng IP; popup blocked account.
- `modules/admin_account_routes.py`: Admin gửi notification riêng theo tài khoản.
- `templates/register.html`: QR nhóm Zalo.
- `templates/login.html`: popup tài khoản cần kiểm tra + QR + tin nhắn Admin.
- `templates/admin.html`: form gửi Nhắc nhở / Xác minh / Cảnh cáo / Thông báo chung.
- Dùng `user_notifications` hiện có, không cần migration mới.


### V1.5.84 – Thay HLV giữa giải
- Backend: `modules/tournament_competition_parts/admin.py` → `admin_tournament_member_replace`.
- UI Admin: `templates/admin.html` → nút `🔄 Thay HLV` trong danh sách HLV giải.
- Cơ chế: chuyển ownership của suất qua `tournament_members`, `tournament_registrations`, `tournament_matches`, `tournament_clubs`, reward markers và các setting/draft có user id.
- Audit: snapshot trước khi chuyển được append vào `tournament_settings` với key `replacement_history`.
- Lịch rảnh (`tournament_availability_slots`) của HLV mới luôn được xóa để bắt buộc khai báo lại.

### V1.5.84 – Responsive room / sidebar
- `static/style.css`: CSS scoped desktop `.player-sidebar` và `#roomLiveShell`, viewport height <=1000px.

### V1.5.84
- `static/style.css`: CSS compact `.room-layout-v137 .room-stage-topbar` cho Rank/C1, không đổi HTML/JS.


V1.5.84: Bản bảo vệ dữ liệu GĐ2, chưa hoàn thành toàn bộ yêu cầu; không triển khai lên giải thật trước kiểm thử end-to-end.

### V1.5.85 GĐ2
- `modules/tournament_competition_parts/league.py`: endpoint `admin_tournament_league_start` kiểm tra điều kiện và mở GĐ2 thủ công.
- `modules/tournament_competition_parts/core.py`: deadline không tự mở GĐ2.
- `modules/tournament_competition_parts/rewards.py`: chặn kết thúc khi còn trận thiếu.
- `templates/admin.html`: điều hướng GĐ1/GĐ2/KO, nút mở GĐ2.

V1.5.87: rooms.py c1_room_open/c1_room_accept fixed club for free rooms during league/KO; remaining auto stage flow pending.

V1.5.87 bổ sung: rewards.py chứa _auto_finish_stage1, _grant_stage1_early_rewards; rooms.py gọi tự kết thúc sau xác nhận kết quả.

- V1.5.87: `rewards.py` xử lý khôi phục tự kết thúc GĐ1/Pot; `templates/admin.html` điều hướng tab GĐ1/GĐ2/KO.

V1.5.88: `rewards.py` route `admin_tournament_stage1_finish` ghi GĐ2 `pending` trước GĐ1 `completed`, cùng migration `SQL_V1.5.88_STAGE_STATUS_PENDING.sql` cập nhật CHECK `tournament_stages.status`. Nếu thiếu migration sẽ log lỗi và flash, không trả trang 500.

V1.5.89: Vé thưởng sớm GĐ1 thuộc `modules/tournament_competition_parts/league.py` (routes random/accept/reward-reroll và bảo lưu state), `core.py` (không auto-expire cho Top 1–3). `modules/tournament_routes.py` cung cấp `landing_hub.early_reward_entry` cho `templates/tournament/cards/c1_actions.html`; Admin theo dõi tại `templates/admin.html`. Lưu tại `tournament_settings.club_draft_v2` không thay schema.

V1.5.90: Admin `POST /admin/tournaments/<id>/clubs/rerandom-by-tier` tại `modules/tournament_competition_parts/league.py`, nút UI `templates/admin.html`, rule Pot trong `modules/tournament_competition.py`. DB RPC `public.c1_admin_rerandom_tier_clubs` tại SQL_V1.5.90_ADMIN_RERANDOM_TIER_POT.sql thực hiện một transaction thay 16 `tournament_members.fixed_club_*`/`tournament_clubs.selected_by`, bảo toàn vé và lịch sử trong `tournament_settings.club_draft_v2`; không chạm thưởng ZCoin/Lucky Box. Chặn GĐ2 sai mapping và giới hạn reroll vé trong Pot tương ứng.

### V1.5.91 – Tab điều hành và thu hồi CLB
- `templates/admin.html`: tab GD1/GD2/KO chờ DOMContentLoaded; GD2 gồm nút thu hồi 16 CLB.
- `modules/tournament_competition_parts/league.py`: route POST `/admin/tournaments/<tournament_id>/clubs/revoke-all` (admin only) gọi RPC.
- `SQL_V1.5.91_ADMIN_REVOKE_CLUBS.sql`: RPC atomic giải phóng `tournament_clubs.selected_by/selected_at`, `tournament_members.fixed_club_id/fixed_club_name`, cập nhật JSON `tournament_settings.club_draft_v2`; giữ vé/lịch sử và các bảng khác.
- Ảnh hưởng: giao diện Admin tab, lựa chọn CLB / Random lại; không sửa kết quả, BXH, điểm thưởng, lịch thi đấu.

### V1.5.92 – Quy tắc mở vé sau phân CLB gốc
- `modules/tournament_competition_parts/league.py`: `_early_reward_ticket_phase_open()` xác minh trạng thái cấp CLB gốc cho 16 thành viên và Tier/Pot, chặn ba route vé khi chưa đủ; bảo vệ admin khỏi thay CLB đã dùng vé.
- `modules/tournament_competition_parts/core.py`: `_club_draft_admin_rows` trả `tier_hlv` từ `tournament_members.pot_no`; phân biệt `club_pot` suy từ tên CLB.
- `modules/tournament_routes.py`: chuyển `club_draft` vào dữ liệu card giải ở `/tournaments` để hiển thị cổng khóa vé.
- `templates/admin.html`, `templates/tournament_detail.html`, `templates/tournament/cards/c1_actions.html`: cột Tier HLV; luồng chờ phân CLB gốc rồi mới mở vé thưởng sớm.
- Dữ liệu: đọc `tournament_settings.club_draft_v2`, `tournament_members`, không thay schema; SQL V1.5.90/91 tiếp tục dùng cho nút Admin.

### V1.5.93 – Điều hướng Admin theo hash
- `templates/admin.html`: thanh điều hướng giai đoạn đặt trên đầu tab Điều hành giải đấu, liên kết trực tiếp tới `#c1-admin-gd1`, `#c1-admin-gd2`, `#c1-admin-ko`; script chọn panel theo hash hoặc session.
- `static/js/admin_dashboard.js`: ba hash trên kích hoạt tab cha `tournaments` thay vì rơi về `overview`. Không tác động route hay database.

### V1.5.94 – Admin GĐ2: Random lại / Thu hồi phản hồi tại chỗ
- `templates/admin.html`: hai POST `data-c1-club-admin-action` không dùng confirm; fetch và trạng thái lỗi nội tuyến, chỉ reload sau JSON `ok`.
- `modules/tournament_competition_parts/league.py`: hai route POST trả JSON cho XHR, fallback redirect `#c1-admin-gd2`, vẫn gọi RPC V1.5.90/91 để ghi giao dịch nguyên tử.
- `app.py`: đồng bộ version; bảng `tournament_members`, `tournament_clubs`, `tournament_settings` không đổi schema.

### V1.5.96 – Điều hành Random CLB GĐ2
- `templates/admin.html`: khối thống nhất Random toàn bộ / cấu hình thứ tự 1→16 hoặc 16→1 / chọn Admin hoặc HLV bấm / thu hồi / bảng theo hạng BXH GĐ1.
- `modules/tournament_competition_parts/league.py`: POST `admin_tournament_configure_base_draft`, `admin_tournament_random_one_base_club`, `tournament_random_my_base_club`; kiểm soát quyền, mode, lượt và thông báo kết quả; bảo vệ khi batch trùng phiên tuần tự.
- `modules/tournament_competition_parts/core.py`: trả `base_draft_config`, `base_draft_next` và hạng `seed_no` cho Admin/trang giải.
- `modules/tournament_routes.py`, `templates/tournament/cards/c1_actions.html`, `templates/tournament_detail.html`: hiện nút tự Random duy nhất cho HLV đúng lượt khi Admin chọn mode player.
- `SQL_V1.5.96_SEQUENTIAL_CLUB_DRAFT.sql`: RPC service-role `c1_allocate_one_base_club(uuid,uuid,text)` lock trên giải; phân CLB gốc một HLV trong một transaction; kết thúc 16 lượt mới bật vé thưởng. Setting mode `club_base_draft_v1`; trạng thái đã có `club_draft_v2`. Không có bảng mới.

### V1.5.97 – Chẩn đoán thu hồi CLB
- `modules/tournament_competition_parts/league.py` → `admin_tournament_revoke_clubs`: phân loại lỗi RPC theo mã PostgREST/SQLSTATE, thông báo an toàn trong GĐ2; log server chứa chi tiết.
- `SQL_V1.5.97_DIAGNOSE_REVOKE_READ_ONLY.sql`: kiểm tra dữ liệu/cấu hình bằng SELECT; không phải migration, không tự thu hồi.

### V1.5.98 – Sửa đếm thành viên của RPC thu hồi/Random
- SQL_V1.5.98_FIX_ACTIVE_16_REVOKE_RERANDOM.sql thay thế RPC V1.5.90 và V1.5.91 để đếm 16 HLV active thay vì 17 bản ghi gồm 1 inactive; ID trong `all_order` vẫn được kiểm tra thuộc active.
- Nút Admin tại `modules/tournament_competition_parts/league.py` và UI `templates/admin.html` giữ nguyên; không thay thưởng, vé, lịch, KO và BXH.
### V1.6.2 — Lịch đối thủ cố định, vé thưởng đổi CLB độc lập
- `modules/tournament_competition_parts/league.py`: sau khi đủ 16 CLB gốc hợp lệ, cho phép sinh 32 trận và bắt đầu công bố đối thủ ngay; không chờ pha vé đóng. Route reroll vé thưởng chỉ cập nhật CLB, không thay đổi lịch.
- `modules/tournament_competition_parts/core.py`: mở GĐ2 vẫn kiểm tra pha vé đã đóng, 32 trận hợp lệ và lễ công bố hoàn tất.
- `templates/admin.html`: luồng hiển thị 16 CLB gốc → sinh/công bố đối thủ cố định → vé thưởng tiếp tục đổi CLB đến deadline → mở GĐ2.

**Luồng chuẩn V1.6.2:** 16 CLB gốc → sinh 32 trận cố định → công bố Tier 1→2→3 (có thể song song thời gian dùng vé) → 3 HLV tiếp tục reroll CLB nếu còn vé → khi pha vé đóng và các điều kiện lịch/công bố đạt thì mở GĐ2.

