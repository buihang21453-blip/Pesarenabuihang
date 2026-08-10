# Log

## V1.2.47 - Kiem ke va can doi toan bo nut bam
- Quet 44 template: 242 the button + 63 anchor dang button = 305 vi tri clickable.
- Dong bo Neon Gaming giua `room_detail.html` (render dau) va `_room_live_content.html` (polling) de khong doi style sau khi cap nhat.
- Tao `static/css/button_sizes.css` lam owner kich thuoc nut dung chung; khong quan ly mau/gradient/neon.
- Chot size: nut thuong 40px, small 32px, CTA/auth 44px, filter 38px, admin action 38px, admin tab 40px, invite-mini 34px.
- Bo kich thuoc khoi block `.btn` nen dau `style.css` de tranh 2 noi cung so huu kich thuoc co ban.
- Giu style rieng theo module: Room Neon, Parsec compact, Profile, Lucky Box, Admin Designer.
- Khong doi route, JS, Supabase, RP hay logic phong dau.
- Kem `BAO_CAO_NUT_BAM_V1.2.47.md`.

## V1.2.46 - Thay cum nut Neon Gaming, don CSS cu
- Thay giao dien nut trung tam phong dau sang Neon Gaming: nen toi, vien neon mong, glow nhe, chu trang.
- Mau chuc nang: Moi dau vang, San sang/Tim nhanh xanh la, Thoat phong do, nut phu xam/xanh.
- Them icon rieng cho Moi dau, San sang, Thoat phong; giu nguyen route/form/logic cu.
- Xoa cac block CSS nut trung tam bi lap o V1.2.43, V1.2.44, V1.2.45.
- Gom quyen so huu style vao mot selector rieng `.room-neon-btn`, tranh de `.btn` global de len.
- Khong thay doi luong backend, Supabase, RP, room state hay JavaScript.
- Don thu muc `__pycache__` khoi goi ban giao.


## V1.2.45 - Can giua PES ARENA, dong bo 3 nut, Preview trung tam day du
- Can logo PES ARENA theo chinh thanh PHONG DAU (topbar position: relative), chi scale to/nho.
- Ep Tìm nhanh / Mời đấu / Thoát phòng dùng cùng nền Neon tối, cùng chiều cao/font/bo góc; chỉ khác màu viền và glow khi click.
- Tăng vùng an toàn của cụm 7 chế độ, tách title/card/status để không cắt mép dưới.
- Preview Admin mô phỏng đầy đủ khu trung tâm: title, logo chế độ, trạng thái lựa chọn, VS thật, đủ 3 nút và trạng thái phòng.
- Preview 7 chế độ có chiều cao an toàn và không cắt thanh trạng thái.
# V1.2.44 - Thu gon chu PHONG DAU, can giua logo PES ARENA, dong bo 3 nut

- Khong cho `brand_scale` lam phong to chu PHONG DAU nua.
- Logo `pes-arena-room-logo.webp` luon can chinh giua header; Admin chi dieu chinh kich thuoc.
- Cho phep scale logo tu 0.50 -> 2.00, mac dinh 1.00.
- Dong bo Tìm Nhanh / Mời Đấu / Thoát Phòng: cung nen toi Neon, cung chieu cao, bo goc, font; an icon tia set o Tìm Nhanh.
- Mau vien van giu theo chuc nang; chi phat glow khi nhan.
- Preview Admin dung logo anh that va phan anh style nut moi.
- Khong doi Core/API/RP/matchmaking/gameplay.

# V1.2.43 - Thiet ke phong Preview phai + dieu khien tinh gon + nut Neon

- Admin -> Thiet ke phong: dieu chinh ben trai, Preview co dinh ben phai va auto-fit toan bo.
- Bo cac dieu chinh: Logo PES ARENA - Y, Ca hai khung - Y, Ca cot phai - Y.
- Cot phai cho phep giam nho hon (min 0.42fr).
- Trung tam Preview phan anh truc tiep logo mode, VS, kich thuoc/gap/width cua 3 nut.
- Do trong suot gom thanh 1 thanh chung cho toan bo Room UI.
- Cum nut chinh dong nhat kich thuoc, phong cach Neon; binh thuong khong glow, khi click (:active) moi phat sang.
- Khong thay doi Core/API/RP/matchmaking/gameplay.

# V1.2.42 - Preview toan bo trong Thiet ke phong

- Admin → Thiết kế phòng: ghim Preview ở phía trên khi cuộn chỉnh thông số.
- Preview tự co theo cả chiều rộng và chiều cao màn hình, luôn hiển thị toàn bộ Header + 4 cột + 7 chế độ.
- Không còn thanh cuộn ngang trong Preview desktop; kích thước khung Preview được tính lại khi kéo slider, đổi tab, đổi trạng thái hoặc resize trình duyệt.
- Mobile không dùng sticky để tránh chiếm toàn màn hình.
- Không thay đổi Core/API/RP/gameplay.

## V1.2.41 - Can chinh Room UI theo 8 khu vuc feedback
- Thu gon thanh PHONG DAU va nut Chia se phong; tang logo PES ARENA tren topbar.
- Bo vach mo o hai panel nguoi choi, thay bang huong dan CLB theo mode: CHON 1 CLB / CHON 1 TRONG 3 CLB.
- Tang logo che do dang chon, lam nen khu mode trung tam thoang hon, rut gon thanh trang thai.
- Dong bo chieu cao/font/cum rong 3 nut trung tam de khong con nut lech kich thuoc.
- Parsec hien tron noi dung, khong con scrollbar rieng; lich su moi duoc cuon khi dai.
- Dong bo mat bang quang hoc logo 7 che do, nen card mo hon, status ngan gon va tang chieu cao cum de khong bi cat.
- Khong thay doi Core/API/RP/matchmaking/gameplay.

## V1.2.40 - Nang cap dieu khien kich thuoc Room UI

- Them dieu chinh chieu cao thanh PHONG DAU.
- Nut Chia se phong bo icon, them dieu chinh rong/cao/co chu.
- Cum trung tam: them kich thuoc px logo che do dang chon va co chu 3 nut; 3 nut dung chung chieu cao.
- Cot phai: them Size Font chung.
- 7 che do: them chieu cao ca cum; giu trang thai luon nam gon trong card.
- Chuan hoa khung logo 7 che do; asset 7.webp duoc can quang hoc nho hon de khong to hon 6 logo con lai.
- Khong thay doi Core/API/RP/matchmaking/gameplay.


## V1.2.39 - Nang cap Thiet ke phong Pro
- Khoa doi xung hai cot Chu phong/Doi thu: dung chung `player_width`, khong con chinh X rieng.
- Bo tab Vi tri X/Y; chi giu cac dieu chinh Y that su can thiet.
- Them dieu khien nang cao cho nguoi choi: avatar, ten, logo CLB, khu CLB.
- Them dieu khien nang cao cho Trung tam: khoang cach doc, padding, chieu cao nut, khoang cach nut, do rong cum nut.
- Sua CSS de Tim nhanh / Moi dau / Thoat phong khong bi cat o cuoi khung Trung tam.
- Them `mode_logo_size` theo px; mac dinh 82px de 7 logo che do hien lon va ro hon.
- Them dieu khien ty le doc cot phai: Parsec / Lich su phong / Doi dau 2 nguoi.
- Preview Admin co mo phong day du nut Trung tam va khoa truc X de khong chay lung tung.
- Khong thay doi core/API/RP/matchmaking/gameplay.
# V1.2.35 — 2026-08-10 16:05 (+07:00)

- Thêm card UI **Random Selection Match** dùng logo Supabase `v1.3.40/modes/7.webp`.
- Vị trí hiển thị: thứ 3, ngay sau `Random 3 chọn 1` và trước `Lượt đi - lượt về`.
- Chế độ mới **khóa giao diện**, không thêm core/module/API/RP/route/database logic.
- Đổi tên hiển thị chế độ 1 từ `Rank thường Random` / `Rank thường` thành **Random** trong Room UI; backend identifier `smart_random` giữ nguyên.
- Dải chế độ chuyển từ 6 thành 7 cột và thu nhẹ kích thước card/logo để giữ mục tiêu xem Room trong một màn hình desktop.
- Preview Admin Room UI cập nhật đủ thứ tự 1, 2, 7, 3, 4, 5, 6.

# V1.2.33 - Thu gon 6 che do va dua lich su phong xuong duoi Parsec

- Dải 6 chế độ chỉ chiếm đúng chiều rộng từ Chủ phòng → Trung tâm → hết khung Đối thủ; không kéo sang cột thông tin bên phải.
- Trên màn hình hẹp, dải chế độ tự full width để không vỡ bố cục.
- Lịch sử phòng luôn nằm ngay dưới Kết nối Parsec trong cột phải.
- Đổi tiêu đề thành `LỊCH SỬ PHÒNG`; khi chưa có trận vẫn giữ khung và hiển thị trạng thái trống.
- Đồng bộ trạng thái lịch sử trong `_room_live_content.html`.
- Chỉ sửa Room UI/HTML/CSS; không đổi Core, API, RP, matchmaking hay 4 chế độ đang khóa.

# V1.2.32 - Test logo du an rieng voi logo phong dau
- Ngay: 2026-08-10 15:42 (Asia/Bangkok)
- Khoi phuc test 2 logo du an: `v1.3.40/pes-arena-logo.webp` (co nen) va `v1.3.40/pes-arena-logoknen.webp` (khong nen).
- Logo PES ARENA ben trong phong dau van co dinh `v1.3.40/pes-arena-room-logo.webp`, khong bi thay doi boi bo test.
- Giu test 2 nen trung tam: `center-stadium.webp` va `center-stadium2.webp`.
- Lua chon logo du an luu localStorage cua Admin va duoc ap dung lai o sidebar khi chuyen trang; khong ghi DB, khong goi API, khong thay core/RP/matchmaking.

# V1.2.31 - Tra lai logo rieng trong phong dau

- Khôi phục logo trong Room về đúng asset: `v1.3.40/pes-arena-room-logo.webp`.
- `pes-arena-logo.webp` và `pes-arena-logoknen.webp` được xác định là logo dự án, không còn dùng để thay logo PES ARENA bên trong phòng đấu.
- Bảng test trong Room chỉ còn test 2 ảnh nền giữa `center-stadium.webp` / `center-stadium2.webp`.
- Không thay đổi Core/API/RP/DB/matchmaking hay 4 chế độ đang khóa.

# V1.2.27 - Sua dung duong dan Room V2 Supabase v1.3.40

- Xac nhan 6 logo che do chi lay tu `pes-assets/v1.3.40/modes/1.webp` -> `6.webp`.
- Asset Room V2 `pes-arena-room-logo.webp`, `stadium-blue.webp`, `stadium-red.webp`, `room-texture-dark.webp` chi lay tu `pes-assets/v1.3.40/`.
- Sua ten file VS dung chinh xac chu hoa: `pes-assets/v1.3.40/VS.webp`.
- Cac asset v1.3.40 bo qua `STATIC_ASSET_MODE=local` de khong bi roi ve `/static/...` hoac ghep nham vao `v1.14.41`.
- Khong thay doi Core/API/RP/DB hay logic cua 4 che do dang khoa.

# V1.2.26 - Sua duong dan anh Supabase bi 404

- Sửa `modules/static_asset_service.py`: khi Vercel chưa có `STATIC_ASSET_BASE_URL`, `SHOP_ASSET_BASE_URL` hoặc `LUCKYBOX_ASSET_BASE_URL`, hệ thống tự suy ra URL public từ `SUPABASE_URL`.
- Logo 6 chế độ `v1.3.40/modes/1.webp` -> `6.webp` được nối thẳng vào root bucket `pes-assets`, không còn bị ghép nhầm dưới `v1.14.41`.
- Ảnh vật phẩm Lucky Box `luckybox/exclusive/...` fallback đúng về `pes-assets/v1.14.41/luckybox/...`.
- Ảnh Shop `shop/...` fallback đúng về `pes-assets/v1.14.41/shop/...`.
- Không thay đổi module/core/API/RP của các chế độ thi đấu. Không thay dữ liệu shop/luckybox. Chỉ sửa bộ phân giải đường dẫn ảnh.

# V1.2.24 - Giao dien phong 6 logo 4 che do khoa

- Dựng lớp giao diện Room V2 riêng bằng `static/css/room_v2.css`, scope trong `.room-v2-shell` để tránh đè CSS trang khác.
- Giữ nguyên core hiện tại của Rank thường Random và Random 3 chọn 1.
- Thêm dải 6 logo chế độ bằng đường dẫn ảnh Supabase đã tham khảo từ V1.4.6: `v1.3.40/modes/1.webp` -> `6.webp`.
- Chỉ 2 chế độ hiện tại có form chọn mode cũ; 4 chế độ Lượt đi/về, BO3, Chiến thuật BO3, Cấm chọn BO3 chỉ là card giao diện khóa, không form, không route, không API, không RP, không core.
- Thêm logo PES ARENA và share icon bằng đường dẫn ảnh hiện có qua `asset_url`.
- Giữ nguyên ảnh VS và toàn bộ luồng room/result/rematch/Parsec hiện tại.

## V1.2.6 — 05/08/2026 00:47 (GMT+7)
- Sửa lỗi tài khoản vẫn bị báo còn trận chưa hoàn tất dù phòng đã bị đóng hoặc không còn tồn tại.
- Chỉ khóa tạo phòng khi bản ghi trận còn liên kết với một phòng đang hoạt động.
- Bỏ qua các trận mồ côi có trạng thái `playing`/`waiting_confirm` nhưng phòng đã `cancelled` hoặc đã mất.
- Đồng bộ xóa cache trận sau khi ghi nhận bỏ cuộc do chủ phòng Offline.
- File sửa: `app.py`, `modules/forfeit_history_service.py`.

## V1.2.5 — 05/08/2026 00:43 (GMT+7)
- Admin hiển thị riêng các phòng đã tự đóng do chủ phòng Offline.
- Phòng đã đóng không còn khóa người chơi nhưng vẫn lưu để Admin xem chủ, khách, đội, lý do và chi tiết phòng.
- Bổ sung đầy đủ trạng thái phòng đang hoạt động trong tab quản trị.
- File sửa: `app.py`, `modules/admin_dashboard_routes.py`, `templates/admin.html`.

## V1.14.41.58 — 2026-08-02 07:45 (Asia/Bangkok)

- Thêm thưởng RP hoạt động tuần theo số trận và số đối thủ khác nhau.
- Mỗi mốc chỉ nhận một lần/tuần bằng bảng `weekly_rp_rewards`.
- Mốc thưởng cộng dồn: 10 trận +20; 5 đối thủ +30; 10 đối thủ +50; 20 đối thủ +50 RP.
- Chỉ trận confirmed được xét thưởng; tranh chấp chỉ được xét sau khi Admin xác nhận.
- Thêm SQL `docs/update_weekly_rp_rewards_v1_14_41_58.sql`.

## V1.14.41.57 — 2026-08-02 07:17 (Asia/Bangkok)

- Đổi thời gian chờ xác nhận kết quả Rank từ 12 giờ xuống 1 phút.
- Hết 1 phút không xác nhận hoặc tranh chấp, hệ thống tự xác nhận và cộng/trừ RP.
- Luồng phòng và luồng kết quả tiếp tục độc lập: hủy phòng không hủy kết quả đang chờ.
- Trận có tranh chấp không tự xác nhận, chờ Admin xử lý.

## V1.14.41.53 — Bảo vệ Hủy/Xóa phòng Admin — 02/08/2026 01:47 (Asia/Bangkok)
- Khách đã Sẵn sàng vẫn có thể bị chủ phòng đưa ra nếu phòng chưa tạo trận (`waiting_ready`, không có `match_id`); không ảnh hưởng RP.
- Admin Hủy phòng giữ lịch sử phòng/trận, hoàn tác RP trước khi cập nhật trạng thái và hủy lời mời liên kết.
- Admin chỉ được xóa vật lý phòng chờ chưa có trận; phòng có trận bắt buộc dùng Hủy.
- File: `app.py`, `modules/admin_data_routes.py`, `templates/admin.html`.

## V1.14.41.39 — 31/07/2026 11:25 (Asia/Bangkok)


## V1.14.41.51 — Sửa xóa tài khoản làm tụt RP — 02/08/2026 01:32 (Asia/Bangkok)

- Sửa `modules/data_cleanup_service.py`: xóa tài khoản không còn hoàn tác RP/thống kê của các đối thủ từng thi đấu.
- Chặn xử lý trùng một trận khi trận vừa nằm trong phòng vừa nằm trong danh sách trận cache.
- Giữ nguyên hành vi hoàn tác RP khi Admin chủ động xóa phòng/trận riêng lẻ.
- Thêm kiểm tra nguồn `TEST_DELETE_PLAYER_RP_V1.14.41.51.py`.

- Sửa lỗi số phiên bản trên giao diện bị giữ ở `V1.14.41.36`.
- Nguyên nhân: các bản 37 và 38 không cập nhật hằng số `APP_VERSION` trong `app.py`.
- Cập nhật `APP_VERSION` thành `V1.14.41.39`.

## V1.14.41.40
- Rà soát request/polling, dữ liệu trùng và file tải thừa.
- Chỉ tải zcoin_rewards CSS/JS tại endpoint tương ứng.
- Room state dừng khi tab ẩn; pending invite dùng chu kỳ 2,2s/8s.
- Xóa module/template Zcoin cũ không còn dùng.
- Bỏ reload bảo trì 30 giây bị trùng.


## V1.14.41.50 — Tối ưu ảnh — 02/08/2026 01:28 (Asia/Bangkok)
- Rà soát toàn bộ ảnh trong dự án.
- Xóa ảnh local đã có trong `SUPABASE_ASSET_MANIFEST.csv`.
- Xóa PNG cũ/trùng WebP và ảnh kiểm thử không dùng.
- Sửa `static/style.css` để nền đăng nhập chỉ lấy qua `asset_url()`/Supabase.
- Thêm `IMAGE_OPTIMIZATION_V1.14.41.50.md`.


## V1.14.41.52 — Xóa mềm tài khoản và bảo vệ thao tác kích khách — 02/08/2026 01:43 (Asia/Bangkok)

- Đổi xóa tài khoản sang xóa mềm: giữ nguyên dòng `users`, toàn bộ `matches`, phòng đã có `match_id`, tỷ số và RP lịch sử.
- Vô hiệu hóa đăng nhập bằng `account_status=banned`, đặt mật khẩu ngẫu nhiên và trạng thái Offline.
- Chỉ dọn phòng chờ chưa có trận, thiết bị đăng nhập và lời mời chưa hoàn tất.
- Sửa nút Admin thành “Xóa mềm” và cảnh báo rõ lịch sử/RP được giữ nguyên.
- Rà cơ chế chủ phòng kích khách: chỉ cho phép trước khi bắt đầu; chặn thêm khi đã có `match_id`.
- Khi kích khách, đóng lời mời liên kết để không còn trạng thái lời mời treo; không xóa trận và không thay đổi RP.

## V1.14.41.54 — 02/08/2026 01:53 (Asia/Bangkok)
- Bỏ hoàn toàn chức năng Admin xóa phòng; giao diện chỉ còn nút **Hủy phòng**.
- Hủy phòng chỉ giải phóng người chơi để tạo phòng mới, không hoàn tác hoặc thay đổi RP.
- Hỗ trợ phòng một người, chưa có trận, đang chơi, đã có kết quả, chờ xác nhận, tranh chấp và có báo cáo.
- Giữ nguyên lịch sử, tỷ số, delta RP, báo cáo và bằng chứng tranh chấp.
- Trận chưa hoàn tất chuyển `cancelled` để không khóa người chơi; trận đã `confirmed` giữ nguyên.
- File: `app.py`, `modules/admin_data_routes.py`, `templates/admin.html`.

## V1.14.41.55 - 02/08/2026
- Tách trạng thái tranh chấp khỏi trạng thái phòng.
- Trận bị tranh chấp vẫn lưu và chưa tính RP; phòng lập tức trở lại Chờ Sẵn Sàng.
- Người chơi có thể tiếp tục thi đấu trong cùng phòng mà không chờ Admin xử lý tranh chấp cũ.
- File: `modules/room_result_routes.py`, `app.py`.


## V1.14.41.56 — 2026-08-02 07:12 (Asia/Bangkok)
- Tách hủy phòng khỏi xử lý kết quả.
- Tự xác nhận trận chờ sau 12 giờ, không phạt người quên xác nhận.
- Khóa xác nhận trực tiếp trận disputed.

## V1.14.41.59 — 02/08/2026 08:08 (UTC+7)
- Điều chỉnh mốc thưởng tuần mặc định thành 20 + 30 + 50 + 20 = tối đa 120 RP.
- Bổ sung cấu hình thưởng tuần trong Admin > Hệ thống.
- File sửa: `modules/weekly_rp_rewards_service.py`, `modules/admin_system_routes.py`, `templates/admin.html`, `app.py`.

## V1.14.41.60 - 2026-08-02
- Sửa animation Win Streak và SHUTDOWN không xuất hiện khi trận được tự xác nhận sau 1 phút.
- File: app.py, UPDATE_MANIFEST_V1.14.41.60.md.

## V1.14.41.62 — 02/08/2026 09:24 (Asia/Bangkok)
- Sửa Remember this account: dùng phiên đăng nhập 30 ngày và Password Manager của trình duyệt.
- Tài khoản Admin tạo/import được dùng mật khẩu 1 ký tự.
- Tài khoản Admin tạo/import bỏ giới hạn thiết bị và cảnh báo trùng IP, nhưng vẫn tính RP bình thường.
- File: `app.py`, `modules/admin_account_routes.py`, `templates/admin.html`, `templates/login.html`.

## V1.14.41.65 — 2026-08-02 18:19 (Asia/Bangkok)
- Hoàn thiện bảo vệ phiên: truy vấn trực tiếp phòng theo user và trạng thái cần bảo vệ, không phụ thuộc cache `list_rooms()`.
- Đồng nhất trạng thái `playing`, `friendly_playing`, `waiting_result_confirm`, `waiting_confirm`, `disputed`.
- Không đăng xuất khi một phía vừa mất kết nối nhưng phòng vẫn cần hoàn tất.
- Admin hiển thị trạng thái tải `user_devices`, số bản ghi, số tài khoản có IP, số nhóm trùng và nút tải lại.
- Đổi nhãn Remember thành “Ghi nhớ đăng nhập trên thiết bị này”; làm rõ mật khẩu do trình duyệt lưu.
- Cập nhật kiểm thử: 94/94 đạt.
- File chính: `app.py`, `modules/session_runtime_service.py`, `modules/admin_dashboard_routes.py`, `templates/admin.html`, `templates/login.html`.

## V1.14.41.66 — 2026-08-02 19:30 (Asia/Bangkok)

- Sửa lỗi khách đã vào phòng nhưng phía chủ phòng không nhìn thấy.
- Bổ sung `host_user_id` và `guest_user_id` vào khóa trạng thái phòng để API phát hiện thay đổi thành viên và frontend tự tải lại phần phòng đấu.
- Không tạo thêm polling hoặc request nền.
- File: `app.py`, `test_room_guest_visibility_v1144166.py`, các test phiên bản, `UPDATE_MANIFEST_V1.14.41.66.md`.

## V1.14.41.67 — 02/08/2026 22:16 (GMT+7)

- Kiểm tra giới hạn trận Rank theo ngày Việt Nam: Thứ Hai–Thứ Sáu 10 trận, Thứ Bảy–Chủ Nhật 15 trận; đổi mốc chính xác lúc 00:00 GMT+7.
- Sửa `active_room_for_user()` truy vấn nhầm bảng `rooms`; nay truy vấn trực tiếp `match_rooms`.
- Bổ sung `waiting_ready` vào nhóm phòng active để người đang có phòng chờ không thể tạo thêm phòng mới.
- Chống double-click và request đồng thời trên nhiều Vercel instance: sau khi tạo phòng sẽ đối chiếu lại và chỉ giữ một phòng hợp lệ.
- Tự dọn các phòng `waiting_ready` trùng, chỉ xóa phòng chưa có `match_id`; không ảnh hưởng trận đang đá, kết quả, RP hoặc tranh chấp.
- Khi Admin mở trang quản trị, hệ thống tự dọn các phòng chờ trùng cũ và tải lại danh sách.
- Hủy lời mời pending gắn với phòng trùng đã bị xóa để tránh trạng thái lời mời treo.
- Kiểm tra tự động: 101/101 test đạt.

### File thay đổi
- `app.py`
- `modules/admin_dashboard_routes.py`
- `test_v1144167_room_daily_limit.py`
- `Log.md`


## V1.14.41.68 — 02/08/2026 23:35 (GMT+7)
- Sửa công thức thưởng chuỗi: chỉ RP thắng cơ bản chịu hệ số gặp lại và hệ số chủ phòng.
- Thưởng chuỗi được cộng nguyên vẹn.
- Đồng bộ luồng xác nhận trận và tính lại BXH Admin.
- Thêm test riêng cho thắng lần 3 cùng đối thủ khi chạm chuỗi 10.

## V1.14.41.73–77 — Profile V2
- Làm mới trang hồ sơ theo bố cục Champion Showcase / Arena Overview.
- Banner phủ khung, có lớp gradient; avatar, RP, Rank, huy hiệu và hành trình Rank rõ hơn.
- Hồ sơ chưa trang bị banner không còn hiện cụm chữ lớn mặc định.
- Không thay đổi SQL hoặc logic thi đấu.

## V1.14.41.78 — Room Session Guard
- Bảo vệ phòng đang thi đấu tối đa 4 giờ khi người chơi chuyển sang PES/Parsec.
- Request trang/API phòng được tính là hoạt động trước bộ lọc idle.
- Tab nền tiếp tục đồng bộ phiên; người ngoài phòng vẫn timeout sau 60 phút.

## V1.14.41.79 — Result Confirmation Reliability
- Sửa lỗi `NameError: get_win_streak_bonus is not defined` khi khách xác nhận tỷ số.
- `match_result_service.py` import trực tiếp `random` và `get_win_streak_bonus`.
- Giữ nguyên công thức RP, giới hạn ngày, hệ số gặp lại và session guard V1.14.41.78.

## V1.14.41.79 Clean — 04/08/2026 01:42 (Asia/Bangkok)
- Xóa toàn bộ Markdown thừa, chỉ giữ `Log.md`.
- Xóa cache Python/Pytest và các manifest TXT cũ.
- Xóa ảnh local đã có trong `SUPABASE_ASSET_MANIFEST.csv` cùng PNG/test image trùng hoặc không dùng.
- ZIP không bọc thư mục cha; yêu cầu cấu hình `STATIC_ASSET_BASE_URL` và `SHOP_ASSET_BASE_URL` trên Vercel.


## V1.14.41.80 — 04/08/2026 01:55 (GMT+7)
- Hòa đặt chuỗi thắng về 0; đồng bộ cả luồng xác nhận trực tiếp và tính lại BXH Admin.
- Đối thủ bỏ cuộc: người còn lại được +1 trận thắng và +1 chuỗi thắng, nhưng +0 RP.
- Giữ tự động xác nhận sau 60 giây và hiển thị đồng hồ đếm ngược ngay dưới tỷ số.
- File sửa: `app.py`, `modules/match_result_service.py`, `modules/admin_ranking_rebuild.py`, `modules/room_rematch_routes.py`, 3 template phòng, `static/style.css`.


## V1.2.0 — 04/08/2026 02:00 (GMT+7)

- Nâng phiên bản chính lên V1.2.0.
- Kiểm tra và gia cố toàn bộ luồng nhập/xác nhận tỷ số.
- Không cho polling thay khung phòng khi chủ phòng đang nhập tỷ số.
- Kiểm tra tỷ số 0–99 ở cả trình duyệt và máy chủ; không tự đổi ô trống thành 0.
- Giữ bản nháp tỷ số khi lỗi mạng.
- Chống trạng thái dở dang khi match đã lưu nhưng phòng chưa đổi trạng thái; tự hoàn tác an toàn.
- Mỗi lỗi lưu/xác nhận có mã riêng SCORE/CONFIRM/ROOM để tra log.
- Phân biệt rõ trường hợp RP đã ghi nhận nhưng phòng chưa làm mới.
- Lỗi phụ của animation chuỗi thắng không còn chặn xác nhận kết quả.

## V1.2.1 — 04/08/2026 02:26 (GMT+7)
- Tự động tạo fingerprint theo nội dung cho CSS/JS, không còn phụ thuộc hoàn toàn vào việc đổi phiên bản để phá cache.
- Tách CSS Thưởng RP tuần thành module riêng, giới hạn phạm vi trong trang Admin và loại bỏ CSS trùng/inline của module này.
- Thêm công cụ `scripts/bump_version.py` và `scripts/check_ui_assets.py` để kiểm tra trước khi đóng gói.
## V1.2.4
- Khi chủ phòng đóng tab/trình duyệt trong trạng thái đang thi đấu, hệ thống xác nhận Offline qua presence rồi tự đóng phòng.
- Chủ phòng bị tính bỏ trận, trừ 20 RP, cộng 1 trận thua và reset chuỗi thắng.
- Khách không thay đổi RP, thống kê hoặc chuỗi; được giải phóng để tạo phòng mới.
- Giữ nguyên quyền Admin hủy phòng mà không phạt thêm người chơi.


## V1.2.7 - Fix lời mời không hiển thị
- Lời mời được kiểm tra trên mọi trang đã đăng nhập, kể cả Lịch sử và Hướng dẫn.
- Tab nền vẫn kiểm tra lời mời theo chu kỳ 10 giây.
- API đọc tối đa 20 lời mời pending để không bỏ sót lời mời hợp lệ cũ hơn.
- Lỗi truy vấn API không còn bị hiểu nhầm là không có lời mời.
- Đồng bộ cache lời mời sau khi gửi.

## V1.2.9
- Sửa lỗi người nhận đang ở trang phòng một mình không thấy lời mời.
- Polling và watchdog lời mời tiếp tục chạy trên trang `/room/...`.
- Không thay đổi điều kiện backend: phòng đủ hai người hoặc đã thi đấu vẫn không nhận lời mời mới.
- Kiểm tra hồi quy toàn bộ: 166/166 test đạt.


## V1.2.10 - Chuan hoa luong tran va module hoa du an

- Chuẩn hóa state flow dùng chung: waiting_ready -> playing -> waiting_result_confirm -> confirmed -> rematch.
- Thêm `modules/room_flow_service.py` làm nguồn quy tắc trạng thái duy nhất.
- Route Ready/Start/Gửi KQ/Xác nhận/Tranh chấp/Đá tiếp dùng guard chung trước khi xử lý.
- Tách 7 nhóm helper lớn khỏi `app.py` sang `modules/core/` nhưng giữ nguyên logic V1.2.9.
- Thêm `PROJECT_MAP.md` để xác định file chịu trách nhiệm từng chức năng.
- Giữ nguyên endpoint, template, schema DB và giao diện V1.2.9.


## V1.2.11 — Moi dau Online + Gui/Xac nhan ket qua an toan
- Tach quy tac Invite va Presence thanh module doc lap.
- Gui moi dung chung `send_invite_blocker`; nhan moi dung `accept_invite_blocker`.
- Nhan loi moi claim `accepted` truoc khi dong phong cu; rollback ve `pending` neu chuyen phong loi.
- Presence dung 1 quy tac timeout duy nhat cho Players/Invite/Quick Match.
- `apply_match_result` co snapshot nguoi choi va rollback RP/thong ke neu loi giua chung.
- Xac nhan ket qua chot phong o `confirmed`, giu ty so/CLB/match_id de quyet dinh Da tiep/Roi phong.
- Auto-confirm 60 giay cung chot `confirmed`, khong tu dong xoa ket qua.
- Da tiep doi xung: ca hai nguoi deu phai dong y; update co dieu kien va kiem tra ket qua ghi.
- Khong doi schema Supabase, khong thay giao dien.


## V1.2.12 - Chuan hoa luong su kien + Confirmed -> Da tiep
- Chuẩn hóa state machine theo sự kiện trong `modules/room_flow_service.py`.
- Sửa lỗi `room_runtime.py` tự reset `waiting_result_confirm -> waiting_ready` khi Match đã confirmed.
- Mọi xác nhận thủ công/tự động đều kết thúc ở `room.status = confirmed`.
- Giữ nguyên tỷ số, CLB và `match_id` ở màn hình Confirmed.
- Bổ sung tự repair Room nếu Match đã confirmed nhưng cập nhật Room thất bại/race.
- Đá tiếp: người thứ nhất chỉ đánh dấu đồng ý; người thứ hai mới reset về `waiting_ready`.
- Không đổi schema Supabase, không thêm Series/BlackBox/UI V1.4.5.

## V1.2.13 — 09/08/2026 — Tối ưu đọc dữ liệu + Hiệu năng

### Nội dung nâng cấp
- Thêm `modules/read_model_service.py` làm lớp đọc dữ liệu chuyên biệt cho Dashboard, BXH, Hồ sơ và báo cáo Admin.
- Dashboard không còn tải toàn bộ lịch sử trận; chỉ lấy tối đa 30 trận liên quan đúng người đang đăng nhập.
- Hồ sơ người chơi không còn quét toàn bộ bảng `matches`; chỉ lấy tối đa 50 trận của người đó và H2H theo đúng cặp người chơi.
- BXH ưu tiên `player_recent_form_cache` để lấy 5 trận phong độ gần nhất; nếu Supabase chưa có Read Model thì tự fallback sang cách cũ.
- `list_matches(status=..., limit=...)` được đẩy bộ lọc xuống Supabase thay vì tải toàn bộ rồi lọc bằng Python.
- Admin ưu tiên báo cáo Read Model. Khi Read Model có sẵn, bảng Admin chỉ tải 80 trận gần nhất; các nhóm disputed/playing được SELECT riêng theo trạng thái.
- Thêm TTL RAM ngắn 10–30 giây cho các truy vấn đọc lặp lại trên warm instance Vercel.
- Thêm migration tùy chọn `project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql`. Không chạy migration vẫn hoạt động nhờ fallback.

### An toàn / tương thích
- Không thay đổi schema bắt buộc.
- Không thay đổi luồng trận đấu, RP, xác nhận, mời đấu hoặc giao diện.
- Không bắt buộc chạy SQL để deploy phiên bản này.

### Kiểm tra
- AST: 154 file Python, 0 lỗi.
- Test V1.2.13 Read Model/Performance: 7/7 PASS.

## V1.2.14 — 09/08/2026 — Dọn và cô lập CSS giảm đè giao diện

### Mục tiêu
- Tách CSS phòng đấu ra khỏi `static/style.css` chung.
- Chỉ tải CSS phòng đấu tại endpoint `room_detail`.
- Giữ nguyên logic/backend và không chủ động thay đổi thiết kế giao diện.
- Thiết lập quy tắc ownership để các nâng cấp sau sửa đúng file.

### Thay đổi
- Tạo `static/css/room_detail.css` làm owner chính của CSS phòng đấu legacy.
- `templates/base.html` chỉ nạp `room_detail.css` khi `request.endpoint == 'room_detail'`.
- Giảm `static/style.css` từ khoảng 293.6 KB xuống 202.4 KB.
- Di chuyển khoảng 91.3 KB CSS Room ra module riêng.
- Số chuỗi selector `.room...` trong CSS toàn cục giảm từ 1.046 xuống 142 (~86%).
- Giữ `quick_match.css`, `parsec_room.css`, `rank_mode_toggle.css` là các module riêng và tải sau CSS nền tảng.
- Thêm `CSS_OWNERSHIP.md` và `scripts/audit_css_ownership.py`.

### Không thay đổi
- Không đổi HTML phòng đấu.
- Không đổi luồng trận đấu, RP, Invite/Presence, Confirmed/Đá tiếp.
- Không đổi Supabase schema.

### Kiểm tra V1.2.14
- CSS `static/style.css`: parse PASS.
- CSS `static/css/room_detail.css`: parse PASS.
- Audit CSS ownership: 8/8 PASS.
- Test CSS isolation + Read Model V1.2.13: 12/12 PASS.
- AST toàn bộ Python: 156 file, 0 lỗi.


## V1.2.15 — 09/08/2026 — Tối ưu Layout và đồng bộ thiết kế trạng thái

### Mục tiêu
- Giữ một layout phòng đấu duy nhất cho toàn bộ vòng đời trận đấu.
- Đồng bộ vị trí Chủ phòng / Trung tâm / Đối thủ / Thông tin, tránh nhảy bố cục khi đổi trạng thái.
- Không thay đổi endpoint, RP, Invite/Presence hay state machine backend.

### Thay đổi
- Thêm lớp layout `room-layout-v1215` và các state class: `waiting-opponent`, `waiting-ready`, `playing`, `waiting-confirm`, `confirmed`, `disputed`.
- Thêm badge trạng thái ở topbar để người chơi biết đang ở bước nào của phòng.
- Chuẩn hóa chiều cao hai thẻ người chơi, cột trung tâm và kích thước vùng hành động.
- Đồng bộ `waiting_result_confirm` và `confirmed` dùng cùng khung tỷ số trung tâm.
- Ở Confirmed, giữ nguyên tỷ số và chỉ chuyển nhóm nút thành `Đá Tiếp / Thoát Phòng`; bỏ hiển thị summary tỷ số lặp phía dưới.
- Đồng bộ template đầy đủ `room_detail.html` và fragment `_room_live_content.html` để AJAX refresh không đổi layout.
- Responsive tiếp tục giữ cùng thứ tự nội dung trên tablet/mobile.

### Kiểm tra
- Jinja parse: PASS cho `room_detail.html` và `_room_live_content.html`.
- Python AST: 156 file, 0 lỗi.
- Test V1.2.15 Layout Sync: 4/4 PASS.
- Test Confirmed flow V1.2.12: PASS.
- CSS isolation V1.2.14: các kiểm tra cấu trúc chính PASS.


## V1.2.16 - Thiet ke giao dien phong trong Admin
- Thêm module `modules/admin_room_ui`.
- Thêm tab Admin có preview trực tiếp, kéo X/Y, scale các vùng.
- Cấu hình lưu vào `system_settings` key `room_ui_designer_config`.
- Áp dụng cùng một cấu hình cho toàn bộ state layout phòng V1.2.15.
- Không thay đổi logic trận đấu.

## V1.2.17 - Sua loi Vercel FUNCTION_INVOCATION_FAILED
- Ngay: 2026-08-09
- Sua loi khoi dong Vercel: `NameError: list_user_devices is not defined` tai app.py.
- Nguyen nhan: sau module hoa, dong khoi tao `list_user_devices.last_status` van nam o vi tri cu, truoc khi `modules/core/user_repository.py` duoc bind vao globals.
- Xu ly: chuyen khoi tao `last_status` xuong sau buoc bind Core modules va bao ve bang `hasattr`.
- Them `test_startup_name_order_v1217.py` de bat loi top-level dung ten truoc khi dinh nghia/bind.
- Khong thay doi luong tran, RP, giao dien phong hay Admin Designer.

## V1.2.18 - Toi uu Admin tai theo tab + phan trang
- Ngay: 2026-08-10 09:01 (Asia/Bangkok)
- `/admin` mặc định không còn tải toàn bộ Users, user_devices, Matches, Audit Log, Dispute và báo cáo trận.
- Dữ liệu nặng chỉ tải khi mở đúng tab bằng `?tab=...`.
- Tab Users phân trang 50 tài khoản/trang; chỉ tab này mới đọc `user_devices` để đối chiếu IP.
- Tab Matches phân trang 50 trận/trang.
- Tab Logs chỉ tải tối đa 100 bản ghi khi mở Nhật ký.
- Tab Rooms chỉ tải tối đa 80 phòng/lời mời; cleanup phòng trùng chỉ chạy khi mở tab Phòng.
- Trang Tổng quan dùng payload user chọn cột cần thiết, room/invite không enrich cosmetic để giảm truy vấn ẩn.
- `list_password_reset_requests()` không còn gọi `users_map()` toàn hệ thống; chỉ lấy đúng user liên quan.
- Admin Room Designer chỉ đọc cấu hình từ Supabase khi mở tab `room-ui`.
- Context cấu hình hệ thống không tải đầy đủ trên mọi lần mở Admin.
- Không đổi schema Supabase, RP, luồng trận đấu, Confirmed/Đá tiếp hay giao diện phòng.
- Test mới `test_v1218_admin_lazy_loading.py`: 3/3 PASS.
- Regression chức năng (bỏ test khóa cứng version cũ): 15/15 PASS.


## V1.2.19 - Chong Supabase 402 lam sap trang + giam truy van doc
- Sua `load_rank_ranges()` de khi Supabase bi 402/quota/giat ket noi se dung cache cu hoac `DEFAULT_RANKS`, khong lam `/login`, `/bxh`, `/admin` bi HTTP 500.
- Giam retry cua truy van Rank trong duong render xuong 1 lan de khong lap lai request vo ich khi project dang bi restricted.
- Them cache RAM ngan cho `list_rooms()`; khi Supabase loi se tra cache gan nhat hoac danh sach rong thay vi lam `/rooms` bi HTTP 500.
- Bao ve `expire_room_if_needed()` va `enrich_room()` trong duong fallback de loi doc du lieu khong lam vo trang.
- Tang cache user hien tai 8s -> 15s, danh sach BXH 8s -> 20s, chuong thong bao 8s -> 30s de giam Egress Supabase.
- Khong thay doi UI, CSS, cong thuc RP, luong xac nhan ket qua hay logic ghi tran.
- Luu y: ban nay chi chong sap web va giam request; Supabase van can duoc mo lai quota de cac chuc nang can ghi/du lieu thuc hoat dong day du.

## V1.2.20 - Vercel-first asset + chuan bi chuyen Supabase moi
- `APP_VERSION` -> `V1.2.20`.
- `modules/static_asset_service.py`: thêm `STATIC_ASSET_MODE=auto|local|remote`.
- Chế độ `auto` ưu tiên file có thật trong `/static` để Vercel CDN phục vụ; asset chưa migrate vẫn fallback URL Supabase Storage cũ, tránh mất ảnh khi chuyển dần.
- Thêm `tools/migrate_supabase_assets_to_vercel_static.py` để tải asset public theo manifest về đúng cấu trúc `/static`, kiểm tra dung lượng/SHA256 khi có dữ liệu đối chiếu.
- Thêm `HUONG_DAN_CHUYEN_SUPABASE_MOI.md`: quy trình Database/Auth/Storage/env + checklist cutover sang project Supabase mới.
- Không thay UI/CSS, không thay RP, không thay luồng trận/confirm.
## V1.2.21 - Bo cong cu don Supabase tu dong an toan
- Them `tools/supabase_cleanup/audit_supabase.py`: audit read-only bang/code/asset.
- Them `cleanup_preview.py`: preview, khong xoa.
- Them `cleanup_storage.py`: dry-run mac dinh, chi cho phep xoa asset UI khi 100% da co local + STATIC_ASSET_MODE=local + khoa execute.
- Them `cleanup_supabase.sql`: clear cache va log cu, khong drop bang/khong dong user-RP-match.
- Them `cleanup_plan.json` va `HUONG_DAN_DON_SUPABASE_TU_DONG.md`.
- Khong thay UI/CSS, khong thay luong tran/RP.



## V1.2.22 - Khoi phuc cache va khoa don nham
- Sua loi V1.2.21 da TRUNCATE read-model/cache qua manh.
- `cleanup_supabase.sql`: bo toan bo TRUNCATE cache; chi trim log cu + ANALYZE.
- Them `KHOI_PHUC_CACHE_SAU_DON_NHAM.sql` de rebuild toan bo cache tu du lieu goc.
- BXH: fallback theo tung user con thieu cache, khong con chi fallback khi toan bo map rong.
- `cleanup_preview.py`: danh dau cache la BAO VE/GIU NGUYEN.
- Khong thay doi RP, matches, Zcoin, user_inventory, user_equipment.

## V1.2.23 — 10/08/2026 (Asia/Bangkok)
- Sửa luồng đăng nhập Admin trên mobile/Vercel: route `/admin*` khi hết phiên luôn quay về `/admin-login`, không rơi sang login người chơi.
- `admin_required` không còn query Supabase lần thứ hai rồi xóa session ngay sau khi Admin vừa đăng nhập; dùng `current_user()` với DB/cache/session fallback đã có.
- Cập nhật trạng thái Online sau Admin login thành best-effort: Supabase chập chờn không còn biến một lần đăng nhập đúng thành lỗi 500/vòng lặp login.
- Giữ kiểm tra quyền thật: khi database đọc được user đã bị hạ quyền, route Admin vẫn từ chối.
- Thêm test hồi quy mobile/Vercel: `test_v1223_admin_mobile_login.py`.
- Không thay UI, RP, lịch sử, Zcoin, kho đồ hay dữ liệu Supabase.

## V1.2.24 - Giao dien phong 6 logo, 4 che do khoa
- Dung Room UI V2 tach rieng bang `static/css/room_v2.css`.
- Chi 2 che do hien tai hoat dong: Rank thuong Random va Random 3 chon 1.
- 4 che do con lai chi hien logo/ten/trang thai khoa, khong them core/API/RP/module nghiep vu.
- Logo 6 che do dung duong dan asset Supabase `v1.3.40/modes/1.webp` -> `6.webp`.

## V1.2.26 - Tich hop RP hoa random + Read Model/Cache + giu kien truc tach Core/Room UI
- Ngay: 2026-08-10 14:43 (Asia/Bangkok)
- RP hoa chenh < 500: moi nguoi random doc lap +1..+6 RP.
- RP hoa chenh >= 500: nguoi RP thap random +1..+6, nguoi RP cao +0.
- Nang `RP_FORMULA_VERSION` len `RP_V1.15.0`; RNG van seed theo match id de Admin rebuild co the tai lap ket qua.
- Sua lop repeat-opponent va Admin ranking rebuild de KHONG ghi de ket qua hoa random thanh +3/+3 hoac +6/+0 co dinh.
- Read Model/Admin: them TTL cache 20 giay cho bao cao tran theo tung khoang thoi gian; giu cache BXH/profile da co.
- Giu kien truc Core da tach khoi app.py: `modules/core/room_runtime.py`, `matchmaking_runtime.py`, `user_repository.py`, `match_repository.py` va cac service lien quan.
- Giu Room UI tach rieng: `static/css/room_v2.css`; khong tron CSS V2 vao legacy `room_detail.css`.
- Khong them 4 core che do Series/BO3; 4 che do moi van chi la logo + khoa giao dien.
- Test RP/Read Model/total matches/daily limit: 25 PASS. Mot so test cu trong project van khoa cung version cu nen khong dung lam regression version moi.

## V1.2.29 - Test 4 phương án ảnh Room UI
- Thêm bộ test chỉ hiển thị cho Admin trong phòng đấu.
- Test trực tiếp 2 nền giữa: `v1.3.40/center-stadium.webp` và `v1.3.40/center-stadium2.webp`.
- Test trực tiếp 2 logo PES ARENA: `v1.3.40/pes-arena-logo.webp` và `v1.3.40/pes-arena-logoknen.webp`.
- Lựa chọn chỉ lưu ở `localStorage` của trình duyệt Admin; không ghi DB, không gọi API, không sửa core/RP/matchmaking.
- Mặc định dùng `center-stadium.webp` + `pes-arena-logoknen.webp`; có nút Khôi phục.


## V1.2.30 - Sua loi xem ho so + dieu chinh do trong suot Room UI
- Route `/profile/<user_id>` duoc boc lop an toan: neu read-model/cache/H2H/room phu tro loi, trang ho so chuyen sang du lieu co ban thay vi Internal Server Error.
- Log loi co ma `PROFILE-XXXXXXXX` de truy vet tren Vercel Logs; fallback chi doc, khong ghi DB/RP/room.
- Admin > Room UI them thanh dieu chinh rieng cho: nen tong, header, chu phong, trung tam, doi thu, sidebar, 6 card che do, khung thao tac.
- Dieu chinh transparency bang alpha cua background, khong lam mo chu/logo/avatar/noi dung ben trong.
- Khong thay core/API/RP/matchmaking/4 che do khoa.


## V1.2.36 - Can lai bo cuc Room va chuyen nen san vao Room UI Designer
- Can lai desktop: khu chinh 468px + day 7 che do 158px; rail phai cao bang tong 2 khu, giam khoang trong duoi phong.
- Tang kich thuoc card/logo vua du de khong che noi dung va van nam trong mot man hinh desktop.
- Thu tu backend/asset giu nguyen: 1 -> 2 -> 7 -> 3 -> 4 -> 5 -> 6.
- So thu tu hien thi doi thanh lien tuc: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7.
- Nhan so 3 la Random Selection Match (asset 7.webp); cac mode sau chi doi so hien thi, khong doi core/code.
- Dua lua chon Nen giua phong (San 1 / San 2) vao Admin -> Room UI Designer va luu trong system_settings.
- Xoa thanh TEST GIAO DIEN trong phong; bo test Logo du an Co nen/Khong nen.
- Khong them/sua core, API, RP hay module gameplay cho Random Selection Match.


## V1.2.37 - Can lai Room va sap xep cot phai
- Bo hien thi khung "Thong tin phong dau" khoi Room UI; du lieu/trang thai backend van giu nguyen.
- Cot phai theo thu tu: Ket noi Parsec -> Lich su phong -> Doi dau 2 nguoi.
- Can lai chieu cao khu dau va 7 mode de giam khoang trong, tranh cat ten CLB/nut.
- Khong render panel Dieu khien phong rong khi trang thai hien tai khong co dieu khien phu.
- Khong thay doi core/API/RP/matchmaking.

## V1.2.38 - Don gian hoa Room UI Designer va khoa Preview on dinh
- Gom toan bo chuc nang thiet ke phong vao 5 nhom trong cung mot cum Admin: Bo cuc, Thanh phan, Vi tri X/Y, 7 che do, Do trong suot.
- Dua lua chon San 1/San 2 vao nhom Bo cuc; giu luu cau hinh `center_stadium` nhu cu.
- Preview chuyen len mot khung rieng full-width, bo sticky va bo keo truc tiep tren Preview de tranh hien tuong preview/slider chay de len nhau.
- Van giu day du thanh X/Y va nut dua toan bo X/Y ve 0.
- Preview cot phai cap nhat dung UI hien tai: Ket noi Parsec -> Lich su phong -> Doi dau 2 nguoi; khong hien Thong tin phong dau.
- 7 che do hien thi lien tuc 1..7, trong khi asset/backend van giu 1 -> 2 -> 7 -> 3 -> 4 -> 5 -> 6.
- Preview dung logo that tu Supabase `v1.3.40/modes/*.webp` thay vi o so gia lap.
- Khong thay core/API/RP/matchmaking/gameplay.
