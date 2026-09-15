# PROJECT_MAP — PES Arena

**Baseline:** V1.5.80  
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

### 5.1 Backend C1 sau V1.5.80

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


### V1.5.80 – lưu ý dependency của `tournament_competition_parts`
Các partition vẫn giữ endpoint cũ nhưng có thể tham chiếu helper/hằng số ở partition khác như khi còn monolith.
`tournament_competition.register_routes()` vì vậy xây dựng namespace chung hoàn chỉnh và đồng bộ namespace này vào tất cả partition sau khi đăng ký.
Không được bỏ bước đồng bộ này khi thêm partition mới.


### V1.5.80 – Duyệt IP & Admin Notification
- `app.py`: `registration_or_latest_ip_conflicts()` đối chiếu IP đăng ký + IP gần nhất.
- `modules/auth_routes.py`: registration/login hold khi trùng IP; popup blocked account.
- `modules/admin_account_routes.py`: Admin gửi notification riêng theo tài khoản.
- `templates/register.html`: QR nhóm Zalo.
- `templates/login.html`: popup tài khoản cần kiểm tra + QR + tin nhắn Admin.
- `templates/admin.html`: form gửi Nhắc nhở / Xác minh / Cảnh cáo / Thông báo chung.
- Dùng `user_notifications` hiện có, không cần migration mới.
