## V1.6.62 — Top 3 reroll Pot 3 / giữ CLB hiện tại

- `modules/tournament_competition_parts/rewards.py`: khóa pool reroll vào Pot 3; thêm action chốt giữ CLB không tiêu vé.
- `modules/tournament_routes.py`: public payload thêm trạng thái `club_finalized` / `ticket_waived`.
- `templates/tournament/components/knockout_dashboard.html`: thêm nút giữ CLB và trạng thái đã chốt.
- `templates/tournament/styles.html`: style cho nhóm action vé.
- `tests/test_c1_top3_reroll_pot3_keepclub_v1662.py`: regression tests.

## V1.6.61 — Champion Cup tối giản

- `templates/tournament/components/knockout_dashboard.html`: bỏ lớp glow của Cup.
- `templates/tournament/styles.html`: bỏ background/border/box-shadow của toàn bộ champion card, chỉ giữ Cup và chữ.
- `app.py`: bump version `V1.6.61`.

## V1.6.60 — Admin Random hộ Top 3 visibility fix

- `templates/tournament/components/knockout_dashboard.html`: nhận diện đầy đủ Admin/Owner bằng `role` và `admin_level`, ưu tiên nút Random hộ.
- `templates/tournament/styles.html`: thêm nhãn Chế độ Admin và trạng thái vé đã dùng.
- `tests/test_c1_knockout_admin_reroll_v1658.py`: thêm kiểm thử Owner/Admin phụ.
- `app.py`: bump version `V1.6.60`.

## V1.6.59 — Bracket Knockout đẹp hơn

- `templates/tournament/components/knockout_dashboard.html`: làm mới layout bracket, thêm cột cúp nhà vô địch và nhãn cặp đấu.
- `templates/tournament/styles.html`: bổ sung CSS cho sơ đồ Knockout kiểu bracket và thẻ cúp vô địch.
- `modules/tournament_routes.py`: mở rộng dữ liệu public Knockout để trả thêm `champion_name` cho giao diện.
- `app.py`: bump version lên `V1.6.59`.

## V1.6.58 — Admin proxy Random CLB Top 3

- `modules/tournament_competition_parts/rewards.py`: gom logic dùng vé Top 3 vào helper dùng chung, thêm route Admin quay hộ và ghi actor/notification.
- `templates/tournament/components/knockout_dashboard.html`: hiển thị nút **Admin Random hộ** cho Admin trên từng vé còn hiệu lực.
- `tests/test_c1_knockout_admin_reroll_v1658.py`: kiểm tra route và quyền hiển thị nút Admin.
- `app.py`: nâng version lên V1.6.58.

## V1.6.57 — Knockout Dashboard

- `modules/tournament_routes.py`: dựng payload Knockout công khai, ghép cặp theo aggregate_group, trạng thái/tổng tỷ số, trận tiếp theo của HLV và trạng thái vé Top 3.
- `templates/tournament/components/knockout_dashboard.html`: bảng theo dõi Tứ kết/Bán kết/Chung kết trên `/tournaments`.
- `templates/tournament/cards/champions_league.html`: đưa Knockout Dashboard vào màn hình chính giải C1.
- `templates/tournament/styles.html`: CSS responsive cho bracket, trận tiếp theo và vé Top 3.
- `modules/tournament_competition_parts/rewards.py`: bracket đã sinh vẫn cho dùng vé; khóa reroll khi HLV đã bắt đầu Knockout.
- `tests/test_c1_knockout_dashboard_v1657.py`: kiểm thử giao diện bracket/trận tiếp theo và guard vé.
- `app.py`: nâng `APP_VERSION` lên V1.6.57.

## V1.6.56 — C1 fixed-match state recovery

- `modules/c1_fixed_match_service.py`: phục hồi room `waiting_ready` khi fixture đã `playing`; xử lý race condition trước rollback.
- `modules/room_team_routes.py`: guest Ready tự bắt đầu cho cả `league` và `knockout`.
- `tests/test_c1_gd2_fixed_match.py`: thêm kiểm thử fixture playing/room waiting và Knockout.
- `app.py`: nâng version lên V1.6.56.

## V1.6.55 — Chuẩn hóa trạng thái phòng Rank trống

- `modules/legacy_room_activity_service.py`: mở rộng nhận diện solo room và tự sửa status Rank trống bị stale.
- `modules/legacy_match_service.py`: activity map không còn gắn nhãn `Đang thi đấu` cho phòng chỉ còn chủ và không có match.
- `tests/test_rank_solo_room_status_v1655.py`: hồi quy trạng thái hiển thị và luồng mời.

## V1.6.54 — Invite/Matchmaking isolation Rank ↔ C1

- `modules/legacy_room_activity_service.py`: snapshot phòng lấy thêm loại phòng, tách `c1_room_*` và `normal_room_*`, ưu tiên C1 khi có dữ liệu active trùng.
- `modules/invite_routes.py`: chặn gửi/nhận/Tìm Nhanh Rank khi có C1 active và ẩn popup Rank trong C1.
- `tests/test_rank_invite_c1_isolation_v1654.py`: kiểm thử hồi quy cho các điểm cách ly C1.
- Không có SQL mới.

## V1.6.53 — Tô xanh hai phía khi trùng availability

- `modules/tournament_routes.py`: dựng riêng `lobby_opponent_slot_set` từ các đối thủ GĐ2 đang hiển thị và đánh dấu overlap cho `mine_availability_days`.
- `templates/tournament/tabs/lobby.html`: thêm class `is-overlap` cho khung giờ của chính HLV khi trùng.
- `tests/test_c1_lobby_gd2_visibility.py`: kiểm thử khung giờ của tôi và đối thủ cùng nhận trạng thái overlap.
- `app.py`: bump version V1.6.53.

## V1.6.52 — Hiển thị availability C1

- `modules/tournament_routes.py`: thêm `mine_availability_days` từ dữ liệu slot đã lưu.
- `templates/tournament/tabs/lobby.html`: “LỊCH CỦA TÔI” hiển thị trực tiếp slot đã lưu, không phụ thuộc danh sách checkbox giờ tròn.
- `tests/test_c1_lobby_gd2_visibility.py`: thêm hồi quy cho giờ linh hoạt 19:30.

## V1.6.51 — Chat Phòng nổi bật hơn

- `templates/room_detail.html`: Chat Phòng mở mặc định, thêm badge chưa đọc, nhận diện tin mới của đối thủ, trạng thái MỚI và logic mở/thu nhỏ.
- `static/style.css`: badge đỏ, pulse nút Chat Phòng, flash khung chat và highlight tin nhắn mới.
- `tests/test_room_chat_attention_v1651.py`: kiểm tra mặc định mở và các hook UI tin chưa đọc.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ version V1.6.51.
- Không đổi DB/API; không cần SQL.

## V1.6.50 — Vị trí đồng hồ GĐ2

- `templates/tournament/cards/c1_media.html`: nhúng đồng hồ vào đúng vị trí overlay trên ảnh giải C1.
- `templates/tournament/cards/c1_header_nav.html`: bỏ đồng hồ ở dưới header, giữ menu giải.
- `templates/tournament/scripts/page_scripts.html`: đồng hồ duy nhất cập nhật trạng thái và đếm ngược; bỏ script lễ bốc thăm cũ ở khung đã thay.
- `templates/tournament/styles.html`: đồng hồ vừa khung overlay desktop/mobile.
- `tests/test_c1_gd2_clock_v1649.py`, `tests/test_c1_gd2_clock_location_v1650.py`: kiểm tra nội dung và vị trí đồng hồ.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ V1.6.50. Không có SQL mới.

## V1.6.49 — Đồng hồ GĐ2 C1

- `modules/tournament_routes.py`: thêm nhãn giờ khởi tranh/hạn kết thúc GĐ2 theo Asia/Ho_Chi_Minh từ competition_timing.
- `templates/tournament/cards/c1_header_nav.html`: hiển thị khung giờ và đồng hồ GĐ2 dưới thông tin giải.
- `templates/tournament/scripts/page_scripts.html`: đếm ngược phía trình duyệt theo thời gian ISO được server cung cấp, xử lý thiếu hạn và hết giờ.
- `templates/tournament/styles.html`: định dạng responsive của đồng hồ.
- `tests/test_c1_gd2_clock_v1649.py`: kiểm tra template, kịch bản đồng hồ, không ảnh hưởng dữ liệu.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ phiên bản V1.6.49.
- Không cần SQL mới.

## V1.6.48 — Chống trùng CLB xuyên đối thủ (Rank)

- `app.py`: phiên bản `V1.6.48`; `_recent_rank_team_names` lấy trực tiếp 5 trận Rank có CLB đã cấp của từng HLV trong `matches`, bao gồm Random Selection Match.
- `modules/legacy_team_random_service.py`: `_pick_rank_team` loại cứng danh sách 5 trận; `smart_random_team_pair` và `build_friendly_random3_state` áp dụng cùng quy tắc; giữ phân bố Tier và không trùng 2 phía/6 lựa chọn.
- `tests/test_rank_random_no_repeat_v1648.py`: kiểm thử lịch sử nhiều đối thủ, hai vị trí chủ/khách, lựa chọn ba đội, thiếu pool và lỗi truy vấn.
- Không thay đổi route, form, `tournament_matches`, schema, SQL hoặc nghiệp vụ C1.

## V1.6.47 — Header Phòng đấu

- `templates/room_detail.html`: bỏ thẻ img logo tại topbar, đặt 3 mode buttons ở grid column giữa với hai cột hai bên có kích thước bằng nhau; responsive có hàng thứ hai.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: version V1.6.47.
- `tests/test_room_mode_header_v1647.py`: xác nhận logo không xuất hiện trong header, thứ tự vùng, CSS center và breakpoint.
- Không thay đổi nghiệp vụ, Supabase/API/DB.

## V1.6.46 — Thanh mode trong topbar

- `templates/room_detail.html`: tái bố trí HTML thanh mode vào `.room-stage-topbar` và CSS grid responsive; JS điều khiển mode giữ nguyên.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ version V1.6.46.
- `tests/test_room_mode_header_v1646.py`: kiểm tra vị trí nav trong topbar, thứ tự 3 tab và CSS responsive. Không thêm endpoint, bảng hay SQL.

## V1.6.45 — Giao diện thanh chế độ gọn

- `templates/room_detail.html`: loại phần diễn giải và hero banner theo mode; CSS nút chế độ chiều cao nhỏ, tối đa 670px, responsive. Giữ nguyên liên kết route và JS đổi mode.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ version.
- Không sửa dịch vụ giải đấu, API hay DB.

## V1.6.44 — Phòng đấu đa chức năng

- `templates/room_detail.html`: thêm thanh chọn chế độ phía trên, hero theo chế độ và CSS/JS đổi layout trong cùng một giao diện.
- `app.py`: bump `APP_VERSION` lên `V1.6.44`.
- `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ nhãn version hiển thị.
- Không thêm route, không thay đổi database hay API; tận dụng luồng Phòng đấu thường và Phòng đấu C1 hiện có.

## V1.6.43 — Bộ giới hạn RP Rank

- `modules/rank_daily_policy.py`: quy tắc thuần Python xác định giới hạn 10/180 ngày thường, 20/250 cuối tuần và tách RP cơ bản/thưởng chuỗi.
- `modules/daily_rank_limit_service.py`: thống kê lượt và RP cơ bản đã nhận; ghi cấu hình giới hạn; zero loss khi đạt trần.
- `modules/match_result_service.py`: xác nhận trận, trần RP cơ bản, thưởng chuỗi ngoài trần, thông báo đạt trần.
- `modules/admin_ranking_rebuild.py`, `modules/ranking_rebuild_service.py`: áp dụng cùng quy tắc cho Admin phát lại lịch sử; giữ cột created_at gốc.
- `modules/weekly_rp_rewards_service.py`: thưởng tuần ngoài trần; bỏ các trận đã đánh dấu vượt hạn lượt ngày.
- `app.py`, `modules/room_rematch_routes.py`, `modules/legacy_room_service.py`: bảo vệ RP khi bỏ cuộc sau giới hạn, cập nhật thông báo đúng số RP bị trừ.
- `modules/admin_system_routes.py`, `templates/admin.html`, `templates/guide.html`: cập nhật hiển thị và nội dung công khai.
- `modules/rp_formula.py`: bump formula version, giữ nguyên seed RP hiện tại.
- `tests/test_rank_daily_policy_v1643.py`: kiểm thử mốc tuần, cap/bonus, zero-loss và Admin replay.

## V1.6.42

- `templates/register.html`: CSS thẻ nhóm Zalo nằm trong `page_styles`; giới hạn kích thước QR và căn giữa trên mobile/desktop.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ nhãn version.
- Không đổi route, model, database, logic C1, Rank hoặc tài khoản.

## V1.6.41

- `templates/partials/c1_fixed_waiting_controls.html`: nút Sẵn sàng độc lập với preview CLB, cho khách thử lại/hủy khi start lỗi.
- `templates/room_detail.html`, `templates/_room_live_content.html`: sửa badge readiness, ẩn kick/forfeit Rank C1.
- `modules/room_rematch_routes.py`: chặn thao tác bỏ cuộc Rank lên C1 tại backend.
- `modules/tournament_competition_parts/rooms.py`: cho phép guest đã ready gọi lại start an toàn (service xác thực trận và CLB).
- `static/style.css`: CSS nút Ready C1 và hướng dẫn trạng thái.
- `tests/test_c1_gd2_fixed_match.py`: kiểm thử trường hợp lookup CLB thất bại.
- `C1_GD2_ROOM_AUDIT.md`: ma trận luồng lỗi/biện pháp và các rủi ro DB cần theo dõi.

## V1.6.40 — Luồng Phòng đấu C1 GĐ2

- `modules/c1_fixed_match_service.py`: khởi chạy trận GĐ2/KO bằng CLB gắn với 2 HLV, kiểm tra lịch và trạng thái, rollback khi lỗi.
- `modules/room_team_routes.py`: khách Sẵn sàng tự khởi động GĐ2 qua service.
- `modules/tournament_competition_parts/rooms.py`: host retry dùng cùng service; chỉ đồng bộ CLB cho phòng chưa bắt đầu.
- `modules/room_access_routes.py`: giữ metadata C1 khi truy vấn phụ lỗi.
- `templates/partials/c1_fixed_waiting_controls.html`: điều khiển GĐ2 dùng chung ở cả hai đường render.
- `templates/room_detail.html` và `templates/_room_live_content.html`: include điều khiển chung.
- `templates/partials/tournament_room_result.html`: biểu mẫu GĐ1 tái sử dụng cho GĐ2 và cảnh báo khi thiếu trận liên kết.

## V1.6.39 — Admin template scope hotfix

- `templates/admin.html`: định nghĩa `ops` ở scope cha để được chia sẻ giữa `admin_parts/c1_console.html` và khối Test Mode kế tiếp.
- `templates/admin_parts/`: giữ toàn bộ cấu trúc module V1.6.37; không dùng `admin_legacy_recovery.html`.
- `tests/test_admin_template_scope.py`: kiểm thử Jinja include scope và bản render Admin mô phỏng.
- `app.py`, `templates/admin_parts/c1_gd2_clubs.html`: đồng bộ version.

## V1.6.37 — Sắp xếp Admin
- `templates/admin.html`: giữ lõi người dùng, Rank, kinh tế, hệ thống và include các module mới.
- `templates/admin_parts/function_menu.html`: menu theo 7 nhóm chức năng.
- `templates/admin_parts/c1_console.html`: wrapper Admin giải C1.
- `templates/admin_parts/c1_stage_header.html`: trạng thái giai đoạn từ `ops.stages`.
- `templates/admin_parts/c1_stage1.html`, `c1_gd2_clubs.html`, `c1_gd2_matches.html`, `c1_knockout.html`: giao diện giai đoạn tách file.
- `templates/admin_parts/feature_review.html`: Owner đánh dấu rà soát chức năng.
- `static/js/admin_dashboard.js`: điều hướng menu và quyết định rà soát trình duyệt.
- `static/css/admin_dashboard.css`: nhóm menu, trạng thái giai đoạn, khu rà soát.
- `ADMIN_FEATURE_AUDIT.md`: các tính năng trùng/ít dùng và ranh giới không xóa.

## V1.6.36
- `templates/guide.html`: hướng dẫn chung phòng đấu, cơ chế RP công khai và Zcoin; có liên kết Phần thưởng/Ví/Cửa hàng.
- `app.py`: nâng APP_VERSION. Không sửa DB/API/route/service.

## V1.6.35
- `modules/admin_system_routes.py`: save/import/export RANK_CLUB_TIER_WEIGHTS.
- `modules/admin_dashboard_routes.py`: tải tỷ lệ Rank cho giao diện.
- `templates/admin.html`: module chỉnh và Import Tier CLB Rank.
- `modules/admin_account_routes.py`: sửa route gửi thông báo Admin.
- `modules/legacy_team_random_service.py`: kiểm tra tỷ lệ nguyên chính xác.

## V1.6.34

- `templates/tournament/admin_lobby.html`: hai chế độ loại trừ nhau, nút chọn ở đầu trang; tổng quan 16 HLV mặc định.
- `modules/tournament_routes.py`: `admin_tournament_lobby` nhận query `view=all|perspective` và chỉ dùng lịch cá nhân để tính trùng ở Góc nhìn HLV.
- `templates/tournament/styles.html`, `templates/tournament/tabs/lobby.html`: màu xanh dương cho lịch cá nhân, xanh lá chỉ cho giờ đối thủ trùng chính xác.
- `app.py`, `templates/admin.html`: đồng bộ version.

## V1.6.33

- `modules/tournament_routes.py`: `_landing_hub_payload` truy vấn lịch rảnh theo lô; đọc riêng bốn trận GĐ2 của HLV; `admin_tournament_lobby` nạp lịch toàn bộ HLV.
- `templates/tournament/tabs/lobby.html`: Lịch của tôi + giờ rảnh bốn đối thủ theo ba ngày; bỏ Host; hiện lỗi tải dữ liệu.
- `templates/tournament/admin_lobby.html`: tổng quan giờ rảnh toàn bộ HLV và bộ chọn Góc nhìn HLV.
- `templates/tournament/styles.html`: sửa ranh giới thẻ style và bổ sung cảnh báo lịch rảnh.
- `app.py`, `templates/admin.html`: phiên bản V1.6.33.

## V1.6.32

- `templates/tournament/tabs/lobby.html`: thêm khối Lịch của tôi (3 ngày) từ `hub.days` và `hub.mine_set` phía trên 4 thẻ đối thủ.
- `templates/tournament/styles.html`: bổ sung style lịch cá nhân 3 cột và tiêu đề phân tách.
- `modules/tournament_routes.py`: không thay đổi; tái sử dụng dữ liệu lịch hiện có.
- `app.py`, `templates/admin.html`: đồng bộ version.

## V1.6.31

- `templates/tournament/tabs/lobby.html`: Sảnh chờ chỉ xem đối thủ, logo, Tier, Pot, 3 ngày giờ rảnh và Host rảnh; loại bỏ phòng, trạng thái trận và tạo trận.
- `modules/tournament_routes.py`: thêm `availability_days` vào từng `league_opponents` từ dữ liệu lịch đã đọc; không phát sinh query mới.
- `templates/tournament/styles.html`: CSS Sảnh chờ compact mới.
- `templates/tournament/admin_lobby.html`: Admin tái sử dụng Sảnh chờ mới, bỏ bảng lịch trùng lặp.
- `app.py`, `templates/admin.html`: đồng bộ V1.6.31.

## V1.6.30

- `templates/tournament/admin_league_opponent_wall.html`: đổi từ card lớn thành ma trận 16×4 compact one-screen.
- `templates/tournament/admin_league_opponent_board.html`: đổi nhãn nút mở bảng tổng quan.
- `app.py`, `templates/admin.html`: đồng bộ V1.6.30.

## V1.6.29

- `modules/tournament_routes.py`: thêm route Admin `admin_tournament_league_opponent_wall`.
- `templates/tournament/admin_league_opponent_wall.html`: trang riêng hiển thị toàn bộ HLV và 4 đối thủ GĐ2 trên 1 màn hình.
- `templates/tournament/admin_league_opponent_board.html`: thêm nút mở bảng mới.
- `templates/tournament/admin_lobby.html`: thêm lối tắt sang bảng mới.
- `templates/admin.html`: đồng bộ nhãn version V1.6.29.
- `app.py`: nâng `APP_VERSION` lên V1.6.29.

## V1.6.28
- modules/tournament_routes.py: GET admin_tournament_lobby, kiểm tra admin và membership trước khi đọc góc nhìn HLV.
- templates/tournament/admin_lobby.html: giao diện Sảnh chờ của Admin, selector HLV, lịch rảnh chỉ xem.
- templates/tournament/tabs/lobby.html: shared lobby với cờ admin_preview để vô hiệu hóa hành động của người chơi.
- templates/admin.html và templates/tournament/cards/c1_header_nav.html: link Sảnh chờ Admin.

## V1.6.27
- modules/tournament_competition_parts/core.py: _admin_payload thêm league_opponent_board từ trận league lưu và phân bổ CLB hiện tại.
- templates/admin.html: nhúng bảng đối thủ độc lập trong tab GĐ2.
- templates/tournament/admin_league_opponent_board.html: 4 thẻ đối thủ / HLV; chọn HLV, xem tất cả, làm mới CLB.
- app.py: APP_VERSION V1.6.27.

## V1.6.26
- modules/tournament_competition_parts/core.py: _host_ready_rows bỏ opt-in; nguồn API Host live và trang chi tiết.
- modules/tournament_routes.py: payload /tournaments tính Host từ online + không trong phòng.
- modules/tournament_competition_parts/scheduling.py: POST host-ready cũ tương thích và không còn ghi setting.
- templates/tournament/tabs/lobby.html: bỏ form bật/tắt chế độ rảnh.
- templates/admin.html: cập nhật hướng dẫn và trạng thái trống, polling 15 giây giữ nguyên.
- app.py: APP_VERSION V1.6.26.

## V1.6.25
- modules/tournament_routes.py: BXH public points, stage1_points, league_points tính từ tournament_matches completed của hai giai đoạn.
- modules/tournament_competition_parts/core.py: _combined_ranking cộng và trả về chi tiết điểm từng giai đoạn.
- templates/tournament/tabs/ranking.html, templates/tournament_detail.html: hiển thị hai cột điểm theo giai đoạn + tổng C1.
- templates/room_detail.html, templates/_room_live_content.html, templates/c1_rooms.html: hướng dẫn giao diện C1 GĐ2 trên đúng phòng đấu C1.
- app.py, templates/admin.html: đồng bộ version. DB không thay đổi, không tạo route mới.

## V1.6.24
- modules/tournament_competition_parts/rooms.py: endpoint start-fixed-match, khóa CLB lúc bắt đầu.
- modules/room_access_routes.py: làm mới CLB trước trận cho full view và polling.
- templates/room_detail.html, templates/_room_live_content.html: giao diện GĐ2 không Random CLB.

## V1.6.23
- modules/tournament_routes.py: tải bốn đối thủ đã công bố và thông tin CLB/Tier hiện thời, host rảnh theo opt-in.
- modules/tournament_competition_parts/core.py: host opt-in và chế độ mở giải giữ vé.
- modules/tournament_competition_parts/league.py: Admin mở GĐ2 không đóng vé.
- templates/tournament/tabs/lobby.html, styles.html: thẻ đối thủ và bật rảnh.
- templates/admin.html: danh sách Host rảnh real-time, nút mở giải bảo lưu vé.
- SQL_V1.6.23_KEEP_TICKETS_AFTER_LEAGUE_START.sql: thay thế RPC để vé vẫn đổi CLB khi GĐ2 đã mở nhưng chưa hết hạn.

## V1.6.22 — BXH C1

- modules/tournament_routes.py: kết hợp hàng BXH với tournament_members theo user_id; ánh xạ fixed_club_name → Pot thông qua C1_CLUB_POT_BY_NAME.
- templates/tournament/tabs/ranking.html: BXH công khai có Tier HLV, CLB hiện tại, Pot CLB; giữ chi tiết Admin.
- templates/tournament/styles.html: huy hiệu Tier/Pot và khung bảng cuộn ngang trên màn nhỏ.
- app.py, templates/admin.html: đồng bộ version.
- DB/API: chỉ đọc tournament_members, không đổi schema, route hoặc tính điểm.

## V1.6.21 — Phòng đấu và C1

- modules/legacy_room_service.py: bảo vệ phòng tournament khỏi đóng / xóa note / trừ RP theo quy tắc Rank khi host offline hoặc timeout generic.
- modules/room_access_routes.py: phân loại Giao hữu khi vào link/rời phòng, chặn kick Rank phá metadata C1.
- modules/room_team_routes.py: guest-ready Giao hữu không kiểm tra giới hạn Rank; ready C1 cập nhật có điều kiện status và guest_user_id.
- modules/tournament_competition_parts/rooms.py: nhận lời mời C1 với điều kiện guest còn trống, chống ghi đè và nhận lặp.
- templates/room_detail.html: ẩn kick theo Rank tại phòng C1.
- app.py, templates/admin.html: version.

## V1.6.20
# V1.6.20 — Vé CLB: SQL migration đổi thứ tự ghi

- SQL_V1.6.20_FIX_ATOMIC_CLUB_REROLL_ORDER.sql: CREATE OR REPLACE RPC c1_use_early_club_reroll_ticket; nhả CLB cũ trước khi gán CLB mới trong transaction để đáp ứng unique(tournament_id,selected_by).
- modules/tournament_competition_parts/league.py: giữ nguyên 2 route HLV/Admin gọi chung RPC; không sửa backend ở version này.
- app.py, templates/admin.html: đồng bộ version V1.6.20.

## V1.6.19
# V1.6.19 — Chẩn đoán Random vé

- modules/tournament_competition_parts/league.py: route HLV/Admin gọi atomic RPC; log SQLSTATE phân loại lỗi.
- SQL_V1.6.19_DIAGNOSE_REROLL_READ_ONLY.sql: kiểm tra RPC, quyền, draft, thời hạn, số lượng CLB và vé; không sửa dữ liệu.

## V1.6.18
# V1.6.18 — Atomic GĐ1 ticket reroll

- modules/tournament_competition_parts/league.py: hai route HLV/Admin cùng gọi RPC c1_use_early_club_reroll_ticket.
- SQL_V1.6.18_ATOMIC_REWARD_CLUB_REROLL.sql: transaction khóa tournament, validate Tier/Pot, chọn CLB, chuyển sở hữu, trừ 1 vé, ghi lịch sử và nhả CLB cũ.
- tests/test_admin_proxy_reroll_guard.py: kiểm thử mô phỏng hai route, lỗi/missing SQL, không retry.

## V1.6.17
# V1.6.17 — Chặn lỗi Admin quay hộ vé CLB

- modules/tournament_competition_parts/league.py: route admin_tournament_reward_reroll_for không đọc DB ngoài guarded flow; _reroll_early_ticket_for gắn operation id/step cho chẩn đoán và rollback có điều kiện.
- app.py: APP_VERSION = V1.6.17.
- tests/test_admin_proxy_reroll_guard.py: bộ 7 smoke test mock route/Admin và luồng đổi CLB; không ghi Supabase thật.

## V1.6.16
# V1.6.16 — Fix route dùng vé Random CLB

- modules/tournament_competition_parts/league.py: hàm `_reroll_early_ticket_for` dùng chung cho HLV và Admin, xử lý lỗi thao tác ghi và trả về trang hợp lệ.
- `_save_reward_draft`: trả về kết quả Supabase để caller kiểm tra thành công.
- app.py và templates/admin.html: đồng bộ version.
- Không thay đổi schema/SQL, route URLs hoặc template form action.

## V1.6.15
# Admin quay hộ vé CLB GĐ1

- modules/tournament_competition_parts/league.py: `_reroll_early_ticket_for` dùng chung cho HLV và route `admin_tournament_reward_reroll_for` (admin-only).
- templates/admin.html: cột Quay hộ trong bảng 16 HLV.
- templates/tournament/draw_admin_preview.html: điều khiển quay hộ trên màn điều hành lễ.
- Data: `tournament_settings.club_draft_v2.entries`, `history`; không sửa `tournament_matches` hoặc schema.

## V1.6.14
# V1.6.14 — Vé Random lại CLB / UX HLV

- app.py: nâng APP_VERSION lên V1.6.14.
- templates/tournament/cards/c1_actions.html: làm mới khu hiển thị vé Random lại CLB cho HLV.
- templates/tournament/styles.html: thêm style thẻ vé, popup xác nhận và overlay loading.
- templates/tournament/scripts/page_scripts.html: thêm countdown hạn vé, confirm modal và loading state trước khi submit.
- Đưa chế độ tập dượt vào Công cụ quản trị phụ; màn hình chính không nhắc tới giả lập. Chế độ tập dượt vẫn hoạt động khi Admin chủ động chọn.
- Giảm lớp phủ trên nền sân vận động; hiển thị crowd overlay ở chân trang.
- Khung ánh sáng phủ sân khấu; bục ở lớp đáy, không che nội dung.
- Thẻ bí ẩn giữ nguyên tỉ lệ ảnh; chỉ hiện khung reveal khi có logo được công bố, không chồng 2 dấu hỏi.
- Hai nút RANDOM CLB / Bốc tiếp căn giữa dưới thẻ và bốn đối thủ.
- Không thay đổi route backend, random, dữ liệu Supabase, lịch, vé hay chính sách mở giải.
- URL Storage chưa kiểm chứng được từ môi trường làm việc; cần kiểm tra trực quan trình duyệt sau deploy.

### V1.6.9 – Chuẩn hóa logo GĐ2 từ CSV
- `modules/tournament_club_logos.py`: alias LOSC Lille/Calcio Como, fallback URL Porto/Leipzig sau clubs_import/teams; PSV dùng psv.png trong import.
- `templates/tournament/draw_admin_preview.html`: báo nguồn fallback cho Admin. Không có mutation DB/Storage.

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


### V1.6.3 — Admin Preview Lễ bốc thăm GĐ2
- `modules/tournament_competition_parts/admin.py`: route GET `admin_tournament_draw_preview`, chỉ Admin, chỉ đọc dữ liệu hiện tại của giải.
- `templates/tournament/draw_admin_preview.html`: sân khấu preview gồm 2 phần Random CLB / Random đối thủ.
- `static/css/tournament_draw_preview.css`: layout stadium/dashboard responsive dành riêng cho preview.
- `static/js/tournament_draw_preview.js`: chuyển phase, fullscreen và countdown theo giờ Việt Nam.
- `templates/admin.html`: nút mở preview tại đầu tab `GĐ2 · Pot / CLB / Lịch`.
- Preview không gọi API POST và không có nút thay đổi dữ liệu; mọi thao tác vận hành thật vẫn thực hiện tại Admin GĐ2.


### V1.6.4 — Admin Control Lễ bốc thăm GĐ2
- `modules/tournament_competition_parts/admin.py`: dựng payload dữ liệu thật và payload rehearsal in-memory.
- `modules/tournament_competition_parts/league.py`: route thao tác live, trả về màn hình điều hành và route thu hồi đối thủ GĐ2.
- `templates/tournament/draw_admin_preview.html`: giao diện điều hành thật + giả lập.
- `static/js/tournament_draw_preview.js`: chuyển mode Live/Simulation, chạy giả lập toàn bộ lễ.
- `static/css/tournament_draw_preview.css`: style bảng điều khiển live/simulation.
Luồng rollback trước GĐ2: Thu hồi đối thủ → Thu hồi CLB. Simulation không ghi dữ liệu.

### V1.6.5 – Lượt bốc thăm một nút
- `league.py`: route `clubs/draw-next` tự cấu hình 16→1 và RPC một CLB; `league-draw/next` khởi động tự động, công bố 4 đối thủ/HLV theo 1→16 và kiểm tra 32 trận.
- `admin.py`: dữ liệu người tiếp theo, chỉ trả đối thủ đã tiết lộ trong HTML.
- `draw_admin_preview.html`, `tournament_draw_preview.js`: một nút/HLV, đồng bộ giả lập.

### V1.6.6 – Sân khấu và tài nguyên hình ảnh lễ bốc thăm
- `modules/tournament_competition_parts/admin.py`: nạp avatar từ `_all_members`/`users.avatar_url`, logo từ danh mục `teams.logo_url` hiện hữu; xác định CLB vừa bốc từ lịch sử `BASE_SINGLE_RANDOM` đã ghi; chỉ dữ liệu HLV active và đối thủ đã công bố trong HTML.
- `templates/tournament/draw_admin_preview.html`: một nút chính trong mỗi sân khấu; công cụ quản trị chuyển vào `<details>`; avatar HLV/opponent có fallback và logo chỉ hiện tại kết quả công bố CLB.
- `static/js/tournament_draw_preview.js`: render avatar an toàn bằng DOM, logo theo kết quả; giả lập CLB thứ tự 16→1.
- `static/css/tournament_draw_preview.css`: layout gọn, responsive, avatar và logo. Không migration.

### V1.6.7 – Một nút điều khiển trên mỗi phần
- `templates/tournament/draw_admin_preview.html`: di chuyển form POST Random CLB / Bốc tiếp ra thanh điều khiển phía trên sân khấu, xóa nút trùng trong sân khấu; vẫn dùng endpoint cũ.
- `static/css/tournament_draw_preview.css`: định dạng thanh điều khiển; responsive.
- `static/js/tournament_draw_preview.js`: không đổi; tiếp tục dùng `data-live-action` / `data-sim-next` để chỉ hiển thị nút đúng chế độ.

### V1.6.8 – Logo CLB lễ bốc thăm
- `modules/tournament_club_logos.py`: ánh xạ tên 24 CLB, đọc clubs_import trước rồi teams; URL công khai hợp lệ; báo cáo thiếu logo/bản ghi read-only.
- `modules/tournament_competition_parts/admin.py`: truyền logo + trạng thái đồng bộ cho màn hình Lễ bốc thăm.
- `templates/tournament/draw_admin_preview.html`, `static/css/tournament_draw_preview.css`: trạng thái đồng bộ trong Công cụ quản trị phụ; logo trên sân khấu dùng nguồn trên.
- `clubs_import` chỉ đọc. Không migration, không ghi Storage; 3 CLB chưa có bản ghi do chủ dự án bổ sung sau.

### V1.6.10 – GD2 ceremony assets / layout
- `modules/tournament_draw_assets.py`: danh mục 8 URL WebP trên Supabase, tham chiếu cho bảo trì.
- `templates/tournament/draw_admin_preview.html`: hai nút live/simulation đặt trong khung `.draw-center-stage`, mỗi pha một nút hiện ra.
- `static/css/tournament_draw_preview.css`: nền sân vận động, crowd, đèn, frame, card và fallback khi ảnh không tải. Spritesheet chưa cắt icon.
- Không thay `league.py`, RPC/DB, logic vé hoặc lịch.


### V1.6.11 – Secret fixture / centered ceremony action
- `league.py`: lịch GĐ2 sinh từ Tier trước lễ CLB; không phụ thuộc fixed_club.
- `core.py`: ẩn league matches với HLV cho tới khi chính HLV đó được công bố hoặc GĐ2 mở.
- `draw_admin_preview.html` + CSS: mô tả luồng mới và căn giữa tuyệt đối nút hành động sân khấu.
