# PES Arena — FEATURE → FILE MAP

**Version:** V1.6.75  
**Mục đích:** Tra nhanh “muốn sửa chức năng X thì phải mở file nào”, giảm việc phải đọc lại toàn bộ dự án và giảm rủi ro sửa lan sang module không liên quan.

> Đây là tài liệu bảo trì cấp root. Khi thêm feature mới, đổi file phụ trách hoặc tách/gộp module, phải cập nhật file này cùng `PROJECT_MAP.md` và `CHANGELOG.md`.

---

## 1. Quy tắc sử dụng Feature → File Map

1. Xác định **Feature** cần sửa.
2. Mở **Primary files** trước.
3. Chỉ mở **Dependencies / Related files** khi thay đổi chạm tới dữ liệu, quyền, route hoặc luồng liên kết.
4. Chạy **Regression tests** tương ứng trước khi bàn giao.
5. Nếu feature đổi phạm vi/file phụ trách, cập nhật lại map này.
6. UI không được xem là lớp bảo mật. Mọi quyền quan trọng phải có guard ở backend/service.
7. Với C1/KO, luôn kiểm tra cả ba lớp: **payload → room route → fixed-match service** nếu thay đổi quyền vào trận.

### Layer dùng trong tài liệu

| Layer | Ý nghĩa |
|---|---|
| `Entry/App` | Khởi tạo app, đăng ký module, version, context toàn cục |
| `Route` | HTTP endpoint / điều phối request |
| `Service` | Logic nghiệp vụ |
| `Repository/Data` | Đọc/ghi dữ liệu |
| `UI` | Jinja template / giao diện |
| `Style/JS` | CSS / JavaScript phía client |
| `Test` | Regression / unit test |
| `Docs` | Tài liệu kiến trúc / changelog / audit |

---

# 2. CORE / APP / SYSTEM

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| App bootstrap + version | `app.py` | Entry/App | Khởi tạo Flask, đăng ký route/module, `APP_VERSION`, context chung | Hầu hết module | Import/compile app; kiểm tra version UI |
| Feature flags / system state | `modules/system_feature_service.py` | Service | Trạng thái feature hệ thống | `modules/admin_system_routes.py` | Luồng bật/tắt feature liên quan |
| Cache helpers | `modules/cache_utils.py` | Service | Hỗ trợ cache | Các route/service sử dụng cache | Import/compile |
| Static asset lookup | `modules/static_asset_service.py` | Service | Resolve asset tĩnh | Templates | Kiểm tra fallback asset |
| Date/time chuẩn | `modules/datetime_utils.py` | Service | Chuẩn hóa thời gian | C1, Rank, lịch sử | Test các luồng có mốc giờ |
| Maintenance / system admin | `modules/admin_system_routes.py`, `templates/admin.html` | Route/UI | Điều hành hệ thống | `modules/system_feature_service.py` | Admin access + render |

---

# 3. AUTH / ACCOUNT / SESSION / PROFILE

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Đăng nhập / đăng ký / đổi mật khẩu | `modules/auth_routes.py`, `templates/login.html`, `templates/register.html`, `templates/change_password.html` | Route/UI | Luồng tài khoản | Session, player data | Login/register/logout |
| Quên mật khẩu | `modules/auth_routes.py`, `templates/forgot_password.html` | Route/UI | Khôi phục mật khẩu | Account data | Request/reset flow |
| Session presence | `modules/session_presence_routes.py`, `modules/session_runtime_service.py` | Route/Service | Theo dõi session/online runtime | Room/invite | Presence khi vào/ra phòng |
| Hồ sơ người chơi | `modules/profile/routes.py`, `modules/profile/service.py`, `modules/profile/repository.py`, `templates/profile.html` | Route/Service/Data/UI | Profile HLV | Inventory/equipment/history | Render + update profile |
| Trang bị hồ sơ | `modules/profile/equipment_service.py` | Service | Trang bị vật phẩm/profile | Inventory | Equip/unequip |
| Admin tài khoản | `modules/admin_account_routes.py`, `modules/admin_player_routes.py`, `templates/players.html` | Route/UI | Quản lý tài khoản/HLV | Player data | Admin permission |

---

# 4. RANK / BXH / RP

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| BXH Rank | `modules/ranking_routes.py`, `modules/legacy_ranking_service.py`, `templates/ranking.html`, `templates/public_ranking.html` | Route/Service/UI | Hiển thị BXH | RP engine/season | BXH public + login |
| Công thức RP | `modules/rp_engine.py`, `modules/rp_formula.py` | Service | Tính RP | Match result, rebuild | RP win/draw/loss |
| Chính sách giới hạn ngày | `modules/rank_daily_policy.py`, `modules/daily_rank_limit_service.py` | Service | Trần trận/RP ngày | `modules/match_result_service.py` | `tests/test_rank_daily_policy_v1643.py` |
| Chống farm cùng đối thủ | `modules/repeat_opponent_rp_service.py` | Service | Giảm/khóa RP khi gặp lặp | Match result | Test RP gặp lặp |
| Chuỗi thắng | `modules/win_streaks.py` | Service | Bonus streak | Match result | Mốc 3W/5W/10W/... |
| Thưởng hoạt động tuần | `modules/weekly_rp_rewards_service.py` | Service | Thưởng tuần | Rank policy | Weekly reward flow |
| Trừ RP không hoạt động | `modules/inactivity_rp_service.py` | Service | Inactivity RP | Ranking | Scheduled/manual check |
| Lock/rebuild BXH | `modules/ranking_lock_service.py`, `modules/ranking_rebuild_service.py`, `modules/admin_ranking_rebuild.py` | Service | Khóa / dựng lại BXH | Match history | Replay dữ liệu + policy |
| Rank random CLB không lặp 5 trận | `modules/legacy_team_random_service.py` | Service | Loại CLB đã dùng gần đây | Match history | `tests/test_rank_random_no_repeat_v1648.py` |
| Bật/tắt Rank mode | `modules/rank_mode_toggle/service.py` | Service | Điều khiển trạng thái Rank | Rooms/UI | Toggle mode |

---

# 5. ROOM / MATCH / MATCHMAKING / CHAT

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Danh sách / tạo / vào phòng | `modules/room_access_routes.py`, `modules/room_api_routes.py`, `modules/legacy_room_service.py`, `templates/rooms.html`, `templates/room_detail.html` | Route/Service/UI | Vòng đời phòng cơ bản | Presence/invite/match | Create/join/leave |
| Activity/status phòng | `modules/legacy_room_activity_service.py` | Service | Xác định trạng thái phòng | Invite/Rank/C1 | `tests/test_rank_solo_room_status_v1655.py` |
| Lời mời phòng | `modules/invite_routes.py`, `templates/invites.html` | Route/UI | Gửi/nhận invite | Room activity, C1 isolation | `tests/test_rank_invite_c1_isolation_v1654.py` |
| Tìm nhanh | `modules/quick_match/service.py` | Service | Matchmaking nhanh | Invite/room | Rank/C1 isolation |
| Chọn đội / Ready | `modules/room_team_routes.py`, `templates/partials/room_ready_controls.html`, `templates/partials/c1_fixed_waiting_controls.html` | Route/UI | Chọn đội và trạng thái sẵn sàng | Team random, C1 fixed match | `tests/test_c1_gd2_fixed_match.py` |
| Rematch / forfeit room | `modules/room_rematch_routes.py`, `modules/forfeit_history_service.py` | Route/Service | Đá tiếp/bỏ cuộc | Match result/RP | Rank vs C1 guards |
| Nhập/xác nhận kết quả | `modules/room_result_routes.py`, `modules/match_result_service.py`, `templates/submit_result.html`, `templates/confirm_result.html` | Route/Service/UI | Kết quả + RP | Rank policy/history | Win/draw/loss + confirm |
| Match history | `modules/match_history_routes.py`, `modules/legacy_match_service.py`, `templates/matches.html` | Route/Service/UI | Lịch sử trận | Player/room | History render |
| Chat phòng | `modules/chat_routes.py`, `modules/legacy_chat_service.py`, `templates/chat.html`, `templates/room_detail.html`, `static/style.css` | Route/Service/UI/Style | Chat + unread attention | Room permission | `tests/test_room_chat_attention_v1651.py` |
| Thanh mode RANK/C1/MINI CUP | `templates/room_detail.html`, `templates/partials/room_mode_selector_strip.html`, `templates/partials/room_mode_center_display.html`, `static/style.css` | UI/Style | Chọn/hiển thị mode | Room state | `tests/test_room_mode_header_v1646.py`, `test_room_mode_header_v1647.py` |
| Parsec room panel | `modules/parsec_room/routes.py`, `modules/parsec_room/service.py`, `templates/partials/parsec_room_panel.html` | Route/Service/UI | Thông tin/luồng Parsec trong phòng | Room | Panel + permission |

---

# 6. C1 TOURNAMENT — CORE / PUBLIC UI

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Tournament routes/public payload | `modules/tournament_routes.py` | Route | Payload trang giải, tab, lobby, KO | Tournament competition | C1 pages render |
| Competition facade | `modules/tournament_competition.py` | Service | Điểm vào logic C1 | `tournament_competition_parts/*` | Import + main C1 flows |
| Competition core helpers | `modules/tournament_competition_parts/core.py` | Service | Helper/data chung | Supabase/tournament settings | Test feature liên quan |
| Admin C1 | `modules/tournament_competition_parts/admin.py`, `templates/admin_parts/c1_console.html` | Route/Service/UI | Điều hành C1 | Core/stage modules | Admin role + actions |
| GĐ1 league logic | `modules/tournament_competition_parts/league.py`, `templates/admin_parts/c1_stage1.html` | Service/UI | Logic giai đoạn 1 | Scheduling/result | Stage1 flow |
| GĐ2 draw | `modules/tournament_competition_parts/league_draw.py`, `templates/admin_parts/c1_gd2_clubs.html` | Service/UI | Bốc CLB/đối thủ GĐ2 | Tier→Pot, club pool | Draw/reroll tests |
| Scheduling | `modules/tournament_competition_parts/scheduling.py`, `templates/admin_parts/c1_gd2_matches.html` | Service/UI | Sinh/điều hành lịch | Members/matches | 32-match invariants |
| Tournament rooms | `modules/tournament_competition_parts/rooms.py`, `templates/c1_rooms.html` | Route/Service/UI | Tạo/vào/mời phòng C1 | Fixed match service | Fixed match tests |
| Rewards/KO actions | `modules/tournament_competition_parts/rewards.py` | Route/Service | Thưởng, vé, reroll, KO admin actions | Core/members/settings | Top3 + KO tests |
| Tournament test support | `modules/tournament_competition_parts/test_support.py`, `modules/tournament_test_mode.py` | Service | Test mode C1 | Tournament data | Test-center smoke |
| Public C1 main card | `templates/tournament/cards/champions_league.html`, `templates/tournaments.html` | UI | Tổng hợp màn hình C1 | Tabs/components | Render desktop/mobile |
| C1 header/navigation | `templates/tournament/cards/c1_header_nav.html`, `templates/tournament/cards/c1_actions.html` | UI | Điều hướng/action C1 | Tournament routes | Link/action visibility |
| C1 shared styling/scripts | `templates/tournament/styles.html`, `templates/tournament/scripts/page_scripts.html`, `templates/tournament/scripts/legacy_tail_scripts.html` | UI/Style/JS | CSS/JS toàn trang C1 | Các component | Browser smoke |

---

# 7. C1 AVAILABILITY / SẢNH CHỜ / LỊCH

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Gate bắt buộc lịch rảnh | `modules/tournament_routes.py`, `templates/tournament/components/availability_gate.html` | Route/UI | Chặn/nhắc điền lịch | Tournament member availability | C1 gate |
| Lịch của tôi | `modules/tournament_routes.py`, `templates/tournament/tabs/lobby.html` | Route/UI | Hiển thị slot đã lưu | Availability data | `tests/test_c1_lobby_gd2_visibility.py` |
| Lịch rảnh 4 đối thủ GĐ2 | `modules/tournament_routes.py`, `templates/tournament/tabs/lobby.html` | Route/UI | HLV chỉ thấy đối thủ GĐ2 | Scheduling | Lobby visibility test |
| Highlight giờ trùng | `modules/tournament_routes.py`, `templates/tournament/tabs/lobby.html` | Route/UI | Tô xanh hai phía khi overlap | Availability slots | Lobby overlap test |
| Admin Lobby toàn bộ HLV | `templates/tournament/admin_lobby.html`, `modules/tournament_routes.py` | UI/Route | Góc nhìn Admin + HLV | Availability | Admin render |
| Board/Wall đối thủ | `templates/tournament/admin_league_opponent_board.html`, `templates/tournament/admin_league_opponent_wall.html` | UI | Tổng hợp đối thủ/lịch | GĐ2 schedule | Render check |

---

# 8. C1 CLUB / TIER / POT / TOP-3 TICKET

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Logo CLB | `modules/tournament_club_logos.py`, `modules/tournament_routes.py` | Service/Route | Map logo CLB | KO/Lobby UI | Fallback logo |
| Assets lễ bốc thăm | `modules/tournament_draw_assets.py` | Service | Asset draw | C1 draw UI | Missing asset fallback |
| Tier HLV → Pot CLB | `modules/tournament_competition_parts/league_draw.py`, `modules/tournament_competition_parts/rewards.py` | Service | Mapping Tier1→Pot3, Tier2→Pot2, Tier3→Pot1 | Member pot_no/club pools | `tests/test_c1_top3_reroll_tier_mapping_v1663.py` |
| Top 3 Random CLB | `modules/tournament_competition_parts/rewards.py`, `modules/tournament_routes.py`, `templates/tournament/components/knockout_dashboard.html` | Route/Service/UI | Vé random trước KO | Tier/Pot + KO started guard | Top3 test group |
| Admin Random hộ | `modules/tournament_competition_parts/rewards.py`, `templates/tournament/components/knockout_dashboard.html` | Route/UI | Admin dùng vé của HLV | Permission + ticket history | `tests/test_c1_knockout_admin_reroll_v1658.py` |
| Admin giữ CLB hộ | `modules/tournament_competition_parts/rewards.py`, `templates/tournament/components/knockout_dashboard.html` | Route/UI | Chốt CLB không tiêu vé | KO started guard | `tests/test_c1_top3_admin_keep_club_v1665.py` |
| Undo reroll | `modules/tournament_competition_parts/rewards.py`, `modules/tournament_routes.py` | Route/Service | Hoàn tác lượt reroll hợp lệ | Ticket history/club availability | `tests/test_c1_top3_admin_undo_reroll_v1664.py` |
| Admin-only ticket controls | `modules/tournament_competition_parts/rewards.py`, `templates/tournament/components/knockout_dashboard.html` | Route/UI | HLV chỉ xem, Admin thao tác | Admin role | `tests/test_c1_admin_only_ticket_controls_v1668.py` |

---

# 9. C1 KNOCKOUT — BRACKET / ADMIN UNLOCK / FIXED MATCH

## 9.1 Feature map chi tiết

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Public KO payload | `modules/tournament_routes.py` | Route | Ghép bracket, trạng thái, next match, Tier/CLB/logo | Core/rewards | KO dashboard tests |
| Poster/bracket KO | `templates/tournament/components/knockout_dashboard.html`, `templates/tournament/styles.html` | UI/Style | Tứ kết/Bán kết/Chung kết/Cup | Public KO payload | `test_c1_knockout_dashboard_v1657.py`, tier/club tests |
| Champion display | `templates/tournament/components/knockout_dashboard.html`, `modules/tournament_routes.py` | UI/Route | Nhà vô địch | KO flow | `tests/test_knockout_champion_cup_v1661.py` *(legacy assertions cần đối chiếu khi UI đổi)* |
| Fixed-match C1 | `modules/c1_fixed_match_service.py`, `modules/room_team_routes.py`, `templates/partials/c1_fixed_waiting_controls.html` | Service/Route/UI | Ready/start/snapshot CLB | Tournament fixture + room | `tests/test_c1_gd2_fixed_match.py` |
| Đọc trạng thái lock/unlock | `modules/tournament_competition_parts/core.py` | Service | `_knockout_unlock_state`, `_knockout_pair_is_unlocked` | `tournament_settings` | Unlock tests |
| Admin mở/khóa cặp KO | `modules/tournament_competition_parts/rewards.py`, `templates/admin_parts/c1_knockout.html` | Route/Service/UI | Mở/khóa bất kỳ aggregate pair ở Tứ kết, Bán kết hoặc Chung kết; không ép thứ tự | Core/settings | `tests/test_c1_knockout_admin_unlock_v1673.py`, `tests/test_c1_knockout_unlock_all_rounds_v1675.py` |
| Mặc định khóa cặp mới | `modules/tournament_competition_parts/rewards.py` | Service | Tứ kết/Bán kết/CK mới sinh = locked | Bracket generation | Unlock tests |
| Chặn tạo/vào/mời phòng KO khóa | `modules/tournament_competition_parts/rooms.py` | Route/Service | Backend guard | Core unlock helper | Unlock + fixed-match tests |
| Chặn start KO khóa | `modules/c1_fixed_match_service.py` | Service | Guard cuối trước `playing` | Fixture + unlock helper | Fixed-match tests |
| HLV thấy “Chờ BTC mở trận” | `modules/tournament_routes.py`, `templates/tournament/components/knockout_dashboard.html` | Route/UI | `can_enter` + status label | Unlock state | Unlock UI test |
| Admin KO control panel | `templates/admin_parts/c1_knockout.html`, `modules/tournament_competition_parts/core.py` | UI/Service | Danh sách cặp + trạng thái + action | Rewards routes | Admin render test |

## 9.2 Luồng quyền KO bắt buộc giữ đồng bộ

```text
Admin UI
  ↓
rewards.py  ── ghi tournament_settings: knockout_match_unlocks_v1
  ↓
core.py     ── helper đọc / xác minh cặp
  ├── tournament_routes.py ── public status + can_enter
  ├── rooms.py             ── chặn create/join/invite/accept
  └── c1_fixed_match_service.py ── chặn start trước playing
```

**Khi sửa cơ chế mở/khóa KO, không được chỉ sửa một nhánh trong sơ đồ trên.**

---

# 10. ECONOMY / ZCOIN / SHOP / INVENTORY / REWARDS

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| ZCoin | `modules/zcoin/service.py`, `modules/zcoin/routes.py`, `modules/zcoin/admin.py`, `templates/zcoin/wallet.html` | Service/Route/UI | Ví/giao dịch ZCoin | Rewards/shop | Wallet flow |
| Legacy ZCoin compatibility | `modules/zcoin_service.py`, `modules/zcoin_routes.py`, `templates/zcoin_wallet.html` | Service/Route/UI | Luồng tương thích cũ | New ZCoin module | Smoke legacy routes |
| Shop | `modules/shop/catalog.py`, `modules/shop/service.py`, `modules/shop/repository.py`, `modules/shop/routes.py`, `templates/shop.html` | Data/Service/Route/UI | Mua hàng | ZCoin/inventory | Purchase flow |
| Admin Shop | `modules/admin_shop/*`, `templates/admin_shop/index.html` | Data/Service/Route/UI | Quản trị shop | Shop/inventory | Admin CRUD |
| Inventory | `modules/inventory/repository.py`, `modules/inventory/service.py`, `modules/inventory/routes.py`, `templates/inventory.html` | Data/Service/Route/UI | Kho vật phẩm | Shop/profile | Add/use/equip |
| Lucky Box | `modules/luckybox/*`, `templates/luckybox/*`, `templates/admin_luckybox/*` | Data/Service/Route/UI | Mở box/lịch sử/admin | Inventory/ZCoin | Open/history/admin |
| Gift Codes | `modules/gift_codes/*` | Data/Service/Route | Mã quà | Economy/inventory | Redeem once/permission |
| Daily check-in | `modules/daily_checkin/*` | Data/Service/Route | Điểm danh | Rewards/ZCoin | Daily idempotency |
| Admin economy | `modules/admin_economy/*`, `templates/admin_economy/index.html` | Data/Service/Route/UI | Điều hành kinh tế | ZCoin/rewards | Admin permission/audit |
| Rewards page | `templates/rewards/index.html` | UI | Hiển thị thưởng | Economy | Render |

---

# 11. NOTIFICATION / ANNOUNCEMENT / DASHBOARD

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Notification | `modules/notification_routes.py`, `modules/notification_service.py`, `templates/notifications.html` | Route/Service/UI | Thông báo người dùng | C1/economy/match | Read/unread/send |
| Announcement | `modules/announcement_routes.py` | Route | Thông báo hệ thống | Dashboard/base | Render/permission |
| Dashboard | `modules/dashboard_routes.py`, `templates/dashboard.html` | Route/UI | Trang chính | Ranking/notifications | Render |

---

# 12. SEASON / DATA / ADMIN MATCH

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Season | `modules/season_routes.py`, `modules/season_service.py` | Route/Service | Quản lý mùa | Ranking/matches | Season switch |
| Admin match management | `modules/admin_match_routes.py`, `modules/admin_match_service.py`, `templates/partials/admin_match_row.html` | Route/Service/UI | Quản lý trận | Match history/result | Admin edit/delete |
| Data admin/backup | `modules/admin_data_routes.py`, `templates/backup_preview.html` | Route/UI | Backup/data ops | Database | Permission + preview |
| Data cleanup | `modules/data_cleanup_service.py` | Service | Dọn dữ liệu | DB tables | Dry/safe cleanup |
| Admin dashboard | `modules/admin_dashboard_routes.py`, `templates/admin.html` | Route/UI | Trang quản trị tổng | Admin modules | Admin access |

---

# 13. TEST MODE / AUDIT / DOCUMENTATION

| Feature | Primary files | Layer | Responsibility | Dependencies / Related | Regression / kiểm tra |
|---|---|---|---|---|---|
| Tournament test center | `templates/tournament_test_center.html`, `templates/tournament_test_mode.html`, `templates/tournament_test_public.html`, `modules/tournament_test_mode.py` | UI/Service | Môi trường test C1 | Tournament modules | Smoke test |
| Admin feature review | `templates/admin_parts/feature_review.html` | UI | Kiểm tra feature Admin | Admin routes | Render |
| C1 room audit | `C1_GD2_ROOM_AUDIT.md` | Docs | Audit luồng C1 fixed room | C1 service/routes | Cập nhật khi room flow đổi |
| Admin feature audit | `ADMIN_FEATURE_AUDIT.md` | Docs | Audit chức năng Admin | Admin modules | Cập nhật khi Admin thay đổi lớn |
| Project structure map | `PROJECT_MAP.md` | Docs | Lịch sử/điểm chạm cấu trúc theo version | Changelog | Update mỗi version |
| Feature → File Map | `FEATURE_FILE_MAP.md` | Docs | Tra feature → file | Toàn project | Update khi ownership đổi |
| Project rules | `PROJECT_RULES.md` | Docs | Invariants/quy tắc không được phá | Toàn project | Review trước thay đổi lớn |
| Change history | `CHANGELOG.md` | Docs | Nhật ký thay đổi | Release notes | Update mỗi version |

---

# 14. QUICK LOOKUP — “MUỐN SỬA X THÌ MỞ FILE NÀO?”

| Muốn sửa | Mở trước | Chỉ mở thêm khi cần |
|---|---|---|
| Giao diện KO HLV | `templates/tournament/components/knockout_dashboard.html`, `templates/tournament/styles.html` | `modules/tournament_routes.py` nếu thiếu/thay dữ liệu |
| Nút Admin mở/khóa KO | `templates/admin_parts/c1_knockout.html`, `modules/tournament_competition_parts/rewards.py` | `modules/tournament_competition_parts/core.py` nếu đổi state model |
| Quyền vào trận KO | `modules/tournament_competition_parts/rooms.py`, `modules/c1_fixed_match_service.py`, `modules/tournament_competition_parts/core.py` | `modules/tournament_routes.py` để đồng bộ UI |
| Logic sinh/đẩy bracket | `modules/tournament_competition_parts/rewards.py`, `modules/tournament_competition_parts/core.py` | `modules/tournament_routes.py`, KO template |
| Tier/Pot/Random CLB C1 | `modules/tournament_competition_parts/league_draw.py`, `modules/tournament_competition_parts/rewards.py` | `modules/tournament_routes.py`, Admin/KO templates |
| Sảnh chờ/lịch rảnh C1 | `modules/tournament_routes.py`, `templates/tournament/tabs/lobby.html` | `modules/tournament_competition_parts/scheduling.py` nếu đổi đối thủ/lịch |
| Phòng C1 GĐ2/KO | `modules/tournament_competition_parts/rooms.py`, `modules/c1_fixed_match_service.py`, `modules/room_team_routes.py` | `templates/room_detail.html`, waiting controls |
| Giao diện phòng đấu | `templates/room_detail.html`, `static/style.css`, các `templates/partials/room_*` | Room routes nếu đổi hành vi |
| Invite Rank/Tìm nhanh | `modules/invite_routes.py`, `modules/legacy_room_activity_service.py`, `modules/quick_match/service.py` | C1 room guard nếu liên quan cách ly |
| RP Rank | `modules/rp_engine.py`, `modules/rp_formula.py`, `modules/match_result_service.py` | daily/repeat/streak services |
| Trần trận/RP ngày | `modules/rank_daily_policy.py`, `modules/daily_rank_limit_service.py` | `modules/match_result_service.py`, rebuild/weekly reward |
| Random CLB Rank | `modules/legacy_team_random_service.py` | Match history service |
| Chat phòng | `modules/chat_routes.py`, `modules/legacy_chat_service.py`, `templates/room_detail.html`, `static/style.css` | None nếu chỉ UI |
| Shop/ZCoin | `modules/shop/*`, `modules/zcoin/*` | inventory/profile nếu vật phẩm |
| Lucky Box | `modules/luckybox/*` | inventory/economy nếu phần thưởng |
| Admin chung | `templates/admin.html`, module `admin_*_routes.py` tương ứng | Service/repository của feature |

---

# 15. REGRESSION GROUPS GỢI Ý

## KO / C1 fixed match

```bash
pytest -q \
  tests/test_c1_knockout_admin_unlock_v1673.py \
  tests/test_c1_gd2_fixed_match.py \
  tests/test_c1_knockout_dashboard_v1657.py \
  tests/test_c1_knockout_tier_club_v1666.py
```

## Top-3 ticket / Tier-Pot

```bash
pytest -q \
  tests/test_c1_top3_reroll_pot3_keepclub_v1662.py \
  tests/test_c1_top3_reroll_tier_mapping_v1663.py \
  tests/test_c1_top3_admin_undo_reroll_v1664.py \
  tests/test_c1_top3_admin_keep_club_v1665.py \
  tests/test_c1_knockout_admin_reroll_v1658.py \
  tests/test_c1_admin_only_ticket_controls_v1668.py
```

## C1 Lobby

```bash
pytest -q tests/test_c1_lobby_gd2_visibility.py
```

## Rank policy

```bash
pytest -q \
  tests/test_rank_daily_policy_v1643.py \
  tests/test_rank_random_no_repeat_v1648.py \
  tests/test_rank_invite_c1_isolation_v1654.py \
  tests/test_rank_solo_room_status_v1655.py
```

## Room UI / Chat

```bash
pytest -q \
  tests/test_room_chat_attention_v1651.py \
  tests/test_room_mode_header_v1646.py \
  tests/test_room_mode_header_v1647.py
```

> Nếu test legacy đang assert class/markup đã bị loại bỏ ở version UI mới, phải xác minh lỗi có tồn tại trên baseline trước khi coi là regression.

---

# 16. FILE OWNERSHIP / CHANGE SAFETY

### Mức A — Có thể sửa khá độc lập
- CSS/markup thuần: template + style tương ứng.
- Text/label/spacing/icon hiển thị.
- Docs.

### Mức B — Phải kiểm tra payload + UI
- `modules/tournament_routes.py`
- `modules/ranking_routes.py`
- Dashboard/profile routes.

### Mức C — Phải regression nhiều lớp
- `modules/tournament_competition_parts/rewards.py`
- `modules/tournament_competition_parts/rooms.py`
- `modules/c1_fixed_match_service.py`
- `modules/match_result_service.py`
- `modules/rp_engine.py`
- Economy transaction services.

### Mức D — Core / toàn hệ thống
- `app.py`
- Auth/session.
- Database/data cleanup/rebuild.
- Các thay đổi schema SQL.

---

# 17. QUY TẮC CẬP NHẬT MAP

Khi một phiên bản mới có thay đổi source:

- **Feature mới:** thêm một dòng vào section đúng domain.
- **Feature chuyển file:** sửa Primary files và dependency.
- **Tách module:** ghi file facade + file mới phụ trách thực tế.
- **Đổi quyền:** cập nhật cả UI và backend guard.
- **Đổi DB/schema:** thêm SQL/migration vào dependency và release notes.
- **Thêm regression test:** cập nhật cột test + Regression Groups.
- **Feature bị loại bỏ:** không xóa lịch sử khỏi `CHANGELOG.md`; trong map hiện tại thì xóa/đánh dấu deprecated để tránh ChatGPT sửa nhầm code chết.

---

# 18. NGUỒN SỰ THẬT KHI CÓ XUNG ĐỘT

Ưu tiên theo thứ tự:

1. **Source code hiện tại** — hành vi thực tế.
2. **`PROJECT_RULES.md`** — invariants/quy tắc bắt buộc.
3. **`FEATURE_FILE_MAP.md`** — ownership/điểm chạm feature.
4. **`PROJECT_MAP.md`** — lịch sử cấu trúc theo version.
5. **`CHANGELOG.md` / Release Notes** — lịch sử thay đổi.

Nếu map khác source, **không đoán**: kiểm tra source rồi cập nhật map.

---

**Maintained from V1.6.74 · current V1.6.75.**
