# V1.4 - Kiem tra CSS HTML va noi nut bam

**Ngày:** 2026-08-09 (Asia/Bangkok)

## Nội dung
- Kiểm tra lại CSS/HTML/JS của phòng đấu trước khi nâng phiên bản.
- Xóa `static/css/room/19-room-v3-waiting.css` vì không còn được nạp và trùng lớn với bản final.
- Thêm `static/css/room/21-v14-css-isolation.css` để cách ly nút/phần tử của giao diện chờ đối thủ V3 khỏi CSS nút legacy/global.
- CSS audit: selector trùng toàn dự án 219 → 148; xung đột selector Room giữa module 82 → 11; `!important` 2357 → 2339.
- Kiểm tra 27 endpoint được template Room gọi: các endpoint nghiệp vụ đều có Python handler.
- Sửa dependency `is_series_child_match` trong `modules/room_result_routes.py` bằng `_is_series_child_match_safe()` để luồng Xác nhận/Tranh chấp không chết do binding Series thiếu.
- Thêm `test_v14_room_integrity.py` kiểm tra version, CSS isolation, endpoint Room, Quick Match/Copy handler và result binding.
- Tăng `APP_VERSION` từ `1.3.134` lên `1.4`.

## Kiểm tra
- Python compile: PASS.
- Bộ test V1.4 + result routes + confirm safety: **8 passed**.
- Full pytest còn bị chặn bởi 2 test legacy cũ đang kiểm tra cấu trúc monolithic `room_detail.html`; code hiện đã tách partial/module.

---

# V1.3.117 — Dựng lại khung Room ảnh mẫu 3 bằng namespace riêng

- Gốc triển khai: V1.3.115. Không kế thừa bản V1.3.116 lỗi bố cục.
- Chỉ áp dụng giao diện mới cho trạng thái `waiting_ready` khi phòng chưa có đối thủ.
- Thêm `templates/room/_v3_waiting_shell.html` với namespace `pes-room3-*`, không dùng lại các class layout Room cũ.
- Thêm `static/css/room/19-room-v3-waiting.css`; mọi selector layout đều scope dưới `#roomLiveShell.pes-room3-live-shell`.
- Dựng lại 5 khu vực: header, Host/Center/Opponent, Sidebar, Action bar, Mode selector.
- Giữ nguyên dữ liệu thật, route Mời đấu/Tìm nhanh/Thoát phòng, Parsec, chia sẻ phòng và chuyển chế độ.
- Các trạng thái còn lại tiếp tục dùng giao diện V1.3.115 để không gây regression ngoài phạm vi.

## V1.3.115 - Kiem_tra_va_on_dinh_hien_thi_6_trang_thai_phong (2026-08-08)
- Giữ nguyên layout hiện tại; không đổi cấu trúc cột Chủ phòng / Trung tâm / Đối thủ / Thông tin + Parsec.
- Rà soát 6 trạng thái: Chờ đối thủ; Đủ 2 người/Chờ sẵn sàng; Sẵn sàng bắt đầu; Gửi kết quả; Xác nhận kết quả; Đá tiếp.
- Bổ sung lớp an toàn hiển thị để dock nút ở các trạng thái chờ/playing/confirmed luôn nằm trọn trong cột giữa.
- Trạng thái `waiting_result_confirm`: neo khung tỷ số + Xác nhận/Không đồng ý ngay phía trên dock, tránh bị che/cắt.
- Trạng thái `confirmed`: đảm bảo 2 nút `Đá Tiếp` + `Về sảnh` luôn hiển thị đủ.
- Trạng thái `disputed`: giữ nhãn trạng thái phía trên dock và không bị che.
- Mobile giữ flow dọc, không dùng absolute để tránh cắt nội dung.
- Không thay đổi backend, RP, Series, Parsec hoặc logic submit/xác nhận/rematch.
- APP_VERSION: 1.3.114 -> 1.3.115.

## V1.3.114 - Fix_hien_thi_day_du_khu_vuc_dien_ket_qua (2026-08-08)
- Sửa khu vực nhập tỷ số ở trạng thái `playing` bị cắt/thiếu phần hiển thị trong cột giữa.
- Tăng vùng trống dành riêng cho form kết quả ở desktop, khóa form nằm gọn trong khung và luôn hiển thị đầy đủ 2 ô tỷ số + nút `Gửi Kết Quả`.
- Chuẩn hóa `box-sizing`, chiều rộng form, input và nút gửi để không bị CSS cũ ép lệch hoặc tràn khỏi khung.
- Mobile giữ form theo luồng dọc, không dùng absolute và không bị giới hạn chiều cao.
- Không thay đổi backend, route submit kết quả, RP, Series, Parsec hay các trạng thái phòng khác.
- APP_VERSION: 1.3.113 -> 1.3.114.

# V1.3.112 — Don pycache va lam sang khung che do dang chon

- Xoa toan bo thu muc `__pycache__` va file `.pyc` thua khoi goi du an.
- Chi bo sung hieu ung sang vien cho `.room-master-mode-card.is-selected` trong `static/css/room/13-mode-stability.css`.
- Khung sang theo mau san co cua tung che do, ke ca khi card o trang thai `disabled/view-only`.
- Khong thay doi kich thuoc logo, kich thuoc card, bo cuc, noi dung, backend, JS hay luong tran dau.

# V1.3.111 — Sua dung thu tu logo 6 che do

- Sua map logo 6 che do trong `modules/static_asset_service.py` theo dung thu tu ten 1 -> 6.
- Thu tu logo moi: 1 Random | 2 Random 3 chon 1 | 3 Luot di/ve | 4 BO3 | 5 Chien thuat BO3 | 6 Cam chon BO3.
- Dong bo lai so thu tu che do dang chon trong `templates/_room_live_content.html` va `templates/room/_center_stage.html` de khop thu tu ten/logo.
- Khong sua kich thuoc, CSS, bo cuc, backend hay luong tran dau.

# V1.3.110 — Hoàn tất ổn định CSS phòng đấu

- Chốt `.arena-room-v2` về một nơi quản lý duy nhất: `static/css/room/00-room-core.css`.
- Chuyển nguyên trạng các biến, nền, viền, kích thước khung gốc và quy tắc responsive của root shell từ các file 01/02/03/11/12 sang core.
- Xác nhận giá trị CSS cuối cùng của root shell trước/sau giống nhau ở tất cả context đang có.
- Rà soát selector Room theo từng module: 0 selector trùng giữa hai file quản lý khác nhau.
- Thêm `CSS_OWNERSHIP.md` làm bản đồ nơi quản lý CSS và quy tắc nâng cấp về sau.
- Thêm `test_css_ownership_v13110.py` để chặn việc CSS Room bị chồng module trở lại.
- Không thay đổi thiết kế, chức năng, backend, RP hoặc JavaScript.


## V1.3.109 — 2026-08-08
- Tiếp tục ổn định CSS, không thiết kế lại giao diện.
- Gom quyền quản lý: bảng nhập tỷ số/kết quả về 17-center-match-stability.css.
- Gom nút chia sẻ về 14-shell-player-stability.css.
- Gom khu vực chế độ phía dưới về 13-mode-stability.css.
- Gom điều khiển phụ + modal xác nhận về 15-room-actions-stability.css.
- Gỡ các selector tương ứng khỏi CSS cũ sau khi chuyển.
# V1.3.109 — On dinh CSS khung ngoai va tieu de phong

- Nen sua: V1.3.107.
- Chi don CSS frontend; khong thay doi backend, JS, RP, kich thuoc/logo/chuc nang.
- Gom quyen quan ly: logo PES ARENA tren phong, khung nguoi choi, tieu de chon CLB, can le tieu de/chia se phong ve `static/css/room/14-shell-player-stability.css`.
- Go cac khai bao cu tu 01/02/11/12 sau khi chuyen nguyen khai bao va thu tu cascade sang file 14.
- Muc tieu: giam CSS chong cheo, giu giao dien V1.3.107 nguyen trang.

# V1.3.107 — On dinh CSS che do dang choi va trang thai san sang

- Ngay: 2026-08-08.
- Nen sua: V1.3.106.
- Muc tieu: tiep tuc don CSS tung khu vuc, khong thay doi giao dien.
- Tao owner moi: `static/css/room/18-active-mode-status-stability.css`.
- Gom CSS cua: khung che do dang choi, so che do, tieu de/mo ta che do, nhan mo khoa, trang thai san sang/so nguoi.
- Go cac selector cung pham vi khoi `01`, `03`, `05`, `06`, `10`, `11`, `12`, `17`; giu nguyen thu tu cascade lich su trong module 18.
- Khong sua logo 6 che do, nut hanh dong, Parsec, backend, RP, JavaScript hoac gameplay.
- Visual regression: 1920 / 1280 / 820 / 600, 4 trang thai phong = 0 khac biet tren cac thanh phan vua di chuyen.
- CSS audit: Room cross-file ownership conflicts 25 -> 16; exact cross-file duplicate selectors 162 -> 153.
- APP_VERSION: 1.3.106 -> 1.3.107.

# V1.3.106 — On dinh CSS khu vuc giua phong dau

- Gom CSS khu vuc giua phong: khung trung tam, VS, dong ho/trang thai, bang ty so/ket qua, vi tri HUD series vao `static/css/room/17-center-match-stability.css`.
- Go cac selector tuong ung khoi CSS room 01..12 sau khi chuyen, giu nguyen thu tu cascade lich su.
- Nap module 17 ngay sau 12 va truoc 13 de khong doi thu tu hien thi voi cac module stability da co.
- Khong thay doi giao dien, kich thuoc, mau sac, backend, RP hay JavaScript.
- APP_VERSION: 1.3.105 -> 1.3.106.

# V1.3.105 — On dinh CSS rail thong tin Parsec va lich su phong

- Ngay: 2026-08-08.
- Nen sua: V1.3.104.
- Muc tieu: tiep tuc don CSS theo tung khu vuc, khong thay doi giao dien.
- Tao owner moi: `static/css/room/16-side-rail-history-stability.css`.
- Gom CSS cua: cot thong tin ben phai, thong tin phong, Parsec trong Room, vi tri Chat rail, khung day va lich su ty so trong phong.
- Go cac selector cung pham vi khoi `01`, `03`, `04`, `06`, `07`, `11`, `12`; giu `static/css/parsec_room.css` lam skin component Parsec dung chung.
- Khong sua: mode/logo, the nguoi choi, nut hanh dong, gameplay, backend, route, RP.
- Visual regression: 1920 / 1280 / 820 / 600 = 0 khac biet tren cac thanh phan vua di chuyen.
- CSS audit: Room cross-file ownership conflicts 58 -> 40; exact cross-file duplicate selectors 195 -> 177.
- APP_VERSION: 1.3.104 -> 1.3.105.

# V1.3.104 — On dinh CSS nut va trang thai phong dau

- Muc tieu: gom CSS nut va trang thai hanh dong trong Room ve mot noi quan ly, giu nguyen giao dien V1.3.103.
- Tao owner: `static/css/room/15-room-actions-stability.css`.
- Gom cac rule lien quan Moi dau / San sang / Thoat / Quay quan / Gui ket qua / Xac nhan / Khong dong y / Da tiep / action modal.
- Skin mau nut dung chung van do `static/css/gaming_neon_buttons.css` quan ly.
- Khong sua backend, route, RP, logo, bo cuc nguoi choi hay Parsec.
- Visual regression: 1920 / 1280 / 820 / 600 = 0 khac biet.
- CSS audit: Room cross-file ownership conflicts 104 -> 58; exact cross-file duplicate selectors 241 -> 195.
- APP_VERSION: 1.3.103 -> 1.3.104.

# V1.3.103 — On dinh CSS bo cuc phong va the nguoi choi

- Ngay: 2026-08-08
- Muc tieu: tiep tuc don CSS theo tung khu vuc, giu nguyen giao dien V1.3.102.
- Tao owner moi: `static/css/room/14-shell-player-stability.css`.
- Gom CSS cua: khung phong, topbar, chia se link, the Chu phong/Doi thu, avatar/rank, CLB, tong diem.
- Go cac rule cung pham vi khoi `01-shell-layout.css`, `02-club-visuals.css`, `11-index-layout-reconnect.css`, `12-mockup-layout-lock.css`.
- Khong sua: mode/logo, nut hanh dong, Parsec, ket qua, gameplay, backend.
- Visual regression: 1920 / 1280 / 820 khong phat hien khac biet tren cac thanh phan vua di chuyen.
- CSS audit: Room cross-file duplicate selectors 129 -> 104; exact cross-file duplicate selectors 266 -> 241.
- APP_VERSION: 1.3.102 -> 1.3.103.

# V1.3.102 — On dinh CSS logo va khu vuc che do

- Dừng nâng cấp giao diện V1.4 để xử lý chồng chéo CSS trước.
- Chỉ xử lý khu vực logo chế độ ở giữa phòng và 6 thẻ chế độ phía dưới.
- Di chuyển toàn bộ các quy tắc đang điều khiển khu vực này từ `01`, `03`, `04`, `06`, `08`, `11`, `12` sang `static/css/room/13-mode-stability.css`, giữ nguyên thứ tự cũ.
- Các file cũ không còn chứa selector điều khiển logo/thẻ chế độ; tránh nhiều file cùng đè một thành phần.
- Không thiết kế lại, không chủ động thay kích thước/màu/bố cục. Mốc hiển thị vẫn là V1.3.101.
- Không thay backend, JavaScript, RP, luồng phòng, Parsec, Tìm nhanh, Mời đấu hoặc Sẵn sàng.
- APP_VERSION: 1.3.101 → 1.3.102.

# V1.3.89 — Sửa bố cục bắt đầu trận gọn gàng

- Dọn riêng trạng thái **Đủ 2 người / Chờ sẵn sàng** ở cột giữa, không thay đổi luồng Backend/Series.
- Bỏ khung/viền thừa bao quanh cụm **BẮT ĐẦU TRẬN + Thoát Phòng**.
- Thu gọn nút **BẮT ĐẦU TRẬN 1**, đổi về tông vàng đậm đồng bộ PES Arena; giữ **Thoát Phòng** màu đỏ.
- Thu gọn phần thời gian, không để số đếm lấn xuống khu vực nút.
- Thu nhỏ VS ở trạng thái trước trận và đặt theo luồng tự nhiên để không còn bị nút/thời gian đè lên.
- Ẩn Series HUD ở màn hình chờ bắt đầu vì thông tin chế độ đã có ngay phía trên; HUD vẫn giữ nguyên ở các trạng thái thi đấu/kết quả.
- Chỉ sửa CSS scope `.room-state-waiting_ready`; không sửa RP, random, Parsec, lời mời, kết quả hay điều phối Series.

**File sửa:** `app.py`, `static/css/room/12-mockup-layout-lock.css`, `Log.md`.

---

# V1.3.88 – Sửa logo chế độ hiển thị đúng kích thước

- Xác định nguyên nhân logo vẫn bé: file logo nguồn 1536×1024 có khoảng trống trong suốt rất lớn quanh artwork.
- Không tiếp tục tăng `width/height` vô nghĩa; dùng viewport 104×100 px + zoom artwork `scale(2.20)` để phần logo nhìn thấy lớn đúng tỷ lệ.
- Giữ nền khu vực chế độ tối/trong suốt, không nền xám mặc định.
- Sửa thứ tự asset đúng quy ước giao diện:
  1. Rank thường Random
  2. Random 3 chọn 1
  3. Chiến thuật BO3
  4. BO3
  5. Cấm chọn BO3
  6. Lượt đi/về
- Web chỉ hiển thị số phiên bản **V1.3.88**, không hiển thị nội dung sửa chữa.
- Không thay đổi route, RP, trạng thái phòng hay luồng thi đấu.
- `app.py` chỉ đổi `APP_VERSION` từ 1.3.87 → 1.3.88.
- `modules/static_asset_service.py` chỉ sửa map logo mode 1→6, không thay xử lý backend.

# V1.3.87 – Điều chỉnh kích thước logo chế độ

- Không hiển thị nội dung sửa chữa trên giao diện web; web chỉ hiển thị số phiên bản.
- Tăng logo 6 chế độ từ 52 × 52 px lên 76 × 76 px để chỉ thu nhỏ vừa phải.
- Giữ nền khu vực chế độ trong suốt/tối, không quay lại nền xám mặc định.
- Không thay đổi route, RP, trạng thái phòng hoặc logic backend.
- `app.py` chỉ đổi `APP_VERSION` từ 1.3.86 → 1.3.87.

# V1.3.86 – Sửa logo chế độ và nền đục

- Sửa lỗi khu vực **CÁC CHẾ ĐỘ KHÁC** rơi về giao diện button mặc định của trình duyệt.
- Xóa nền xám/đục của thẻ chế độ và form chứa thẻ.
- Khóa logo 6 chế độ ở 52 × 52 px, không còn phóng to toàn khung.
- CSS bảo vệ không phụ thuộc wrapper `.arena-room-v2`, tránh lỗi khi fragment DOM bị tách scope.
- Cập nhật phiên bản hiển thị trên web thành **V1.3.86**.
- Hiển thị thêm tên bản sửa: **Sửa logo chế độ và nền đục**.
- Không thay đổi route, công thức RP, trạng thái phòng hoặc logic xử lý backend.
- `app.py` chỉ đổi hằng số `APP_VERSION` từ 1.3.84 → 1.3.86 để đồng bộ phiên bản/cache.

# V1.3.85 – Thu gọn khu vực chế độ thi đấu

- Thu nhỏ 6 thẻ chế độ ở khu vực **CÁC CHẾ ĐỘ KHÁC**.
- Logo chế độ khóa ở kích thước 54 × 54 px, không còn bị phóng to.
- Giảm chiều cao thẻ, cỡ chữ và nút **Đã mở khóa** để gần ảnh mẫu.
- Giữ nguyên logo chế độ đang chọn ở khu vực trung tâm.
- Không thay đổi backend, route, form action, JavaScript hoặc luồng phòng đang chạy.
- File sửa: `static/css/room/12-mockup-layout-lock.css`.

# V1.3.84 — Room Jinja Nesting Hotfix

- Date: 2026-08-08 Asia/Bangkok
- FIX NHANH: sửa TemplateSyntaxError khi vào `/room/<id>` sau V1.3.83.
- Nguyên nhân: khi gom nút host pre-start, nhánh host cũ bị bỏ nhưng thiếu `{% endif %}` đóng `if room_viewer_is_guest`, làm Jinja gặp `else` sai nesting.
- Sửa đồng thời `templates/room/_center_stage.html` và `templates/_room_live_content.html`.
- Giữ nguyên bố cục mới: BẮT ĐẦU TRẬN + Thoát Phòng cùng hàng, mô tả riêng phía dưới.
- Không thay backend, RP, Supabase, matchmaking hay logic Series.
- Validation: parse toàn bộ Jinja templates = 0 syntax errors.

# V1.3.82 — Gaming Neon Semantic Color Admin

- Mời đấu được đồng bộ role riêng, mặc định **Vàng** trên Room / Player list / Profile / Dashboard.
- Tìm nhanh dùng role riêng, mặc định **Xanh lá**.
- Thêm cấu hình Admin `Hệ thống → Bộ màu nút Gaming Neon` cho 8 nhóm màu chức năng.
- Cấu hình lưu bằng `system_settings.gaming_neon_button_theme`; không cần migration mới.
- CSS dùng semantic variables và cascade guard riêng cho Room; không thay logic, ID, route, kích thước.
- Admin và Parsec tiếp tục bị loại khỏi Gaming Neon.

# V1.3.81 — Gaming Neon Scope Isolation Hotfix

- FIX NHANH CSS cascade sau ảnh production V1.3.80: các card chế độ Room bị Gaming Neon phủ nền xanh/đục vì global selector bắt mọi thẻ `<button>`.
- `static/css/gaming_neon_buttons.css`: bỏ bare `<button>` khỏi global visual/hover/active selectors; chỉ skin action button có class rõ (`.btn`, `.arena-btn`, CTA chuyên dụng, input submit/button).
- Không skin các component dùng `<button>` nhưng thực chất là card/tab/selector: `room-master-mode-card`, `room-mode-select-btn`, `series-club-btn` và các icon/control cấu trúc.
- Loại `.mode-random3` khỏi purple skin toàn cục; chỉ `random3-trigger`/Lucky Box action thật mới nhận màu tím.
- Giữ nguyên Gaming Neon cho các nút thao tác, giữ nguyên Admin/Parsec exclusion. Không sửa HTML, route, ID, JS, backend, RP hay Supabase.
- Thêm `test_gaming_neon_scope_v1381.py` để chặn regression kiểu "button-card bị skin như CTA".

# V1.3.80 — Button Cascade Reality Fix

- Chế độ: FIX NHANH giao diện.
- Nguyên nhân: V1.3.77 chỉ đổi custom properties semantic, trong khi Room legacy có các declaration `background: ... !important` với specificity cao hơn; kết quả class red/green/gold tồn tại nhưng màu render vẫn có thể là cyan/dark.
- Sửa `static/css/gaming_neon_buttons.css`: thêm FINAL CASCADE GUARD với background/border/glow cụ thể cho từng màu chức năng; thêm specificity riêng cho Room, Invite; vẫn loại Admin và Parsec.
- Không thay ID, route, logic, position, width/height layout.
- Giữ V1.3.79 rollback an toàn đối với phần dead-code cleanup.

# V1.3.79 — Emergency Rollback V1.3.78 Cleanup

- Chế độ: FIX NHANH khẩn cấp.
- Người dùng báo V1.3.78 lỗi nặng ngay sau đợt dọn CSS/Python dead-code.
- Rollback TOÀN BỘ thay đổi cleanup rủi ro của V1.3.78 về baseline V1.3.77:
  - khôi phục nguyên vẹn 6 file `static/css/legacy/*.css`;
  - khôi phục `static/css/admin.css`;
  - khôi phục `modules/zcoin_service.py`;
  - khôi phục `modules/zcoin_routes.py`.
- Không rollback các tính năng/bugfix V1.3.70–V1.3.77.
- Không thay gameplay, RP, database hoặc Supabase.
- Black Box Safety V1.3.78 vẫn PASS toàn bộ critical server modules; production không có incident ghi `app_version=1.3.78`, nên rollback tập trung UI/compatibility là phương án an toàn nhất.
- APP_VERSION: 1.3.78 → 1.3.79.

# V1.3.78 — CSS/Python Dead-Code Cleanup

- Chế độ: AUDIT TOÀN HỆ THỐNG có dọn mã.
- Prune CSS legacy theo bằng chứng runtime: chỉ bỏ selector có class/ID không còn xuất hiện trong `templates/`, `static/js/`, `modules/` hoặc `app.py`; giữ selector động/không chắc chắn.
- Xóa `static/css/admin.css` vì không có runtime reference.
- Xóa `modules/zcoin_service.py`: bản sao byte-for-byte của `modules/zcoin/service.py`.
- Xóa `modules/zcoin_routes.py`: route compatibility cũ không còn được import; `app.py` dùng `modules.zcoin.register_routes`.
- Không thay gameplay, RP, schema Supabase, route hiện hành, HTML/JS hoặc visual mới Gaming Neon.
- Cập nhật APP_VERSION 1.3.77 → 1.3.78.
- Kết quả: CSS 537,174 → 432,491 bytes (-104,683 bytes, khoảng -19.5% toàn CSS); 9,006 → 7,138 dòng CSS; module Python 18,523 → 18,242 dòng (-281 dòng); tổng source loại cache 378 → 375 file và 2,527,566 → 2,413,022 bytes.
- Audit CSS: `!important` 1,470 → 1,279; cross-file duplicate selector 197 → 177; selector có thể hide UI 131 → 102.
- Validation: Python compile PASS; CSS parse 0 lỗi; CSS reference/import thiếu = 0; Jinja parse 0 lỗi; Zcoin package smoke PASS. Nhóm regression rộng: 70 PASS + 7 baseline FAIL y hệt V1.3.77 (test lịch sử ghim version/source monolith).

# V1.3.77 — Global Gaming Neon 3D Button Sync

- Ngày: 2026-08-08 (Asia/Bangkok)
- Chế độ: NÂNG CẤP MODULE — UI toàn giao diện người chơi.
- Lấy trực tiếp mẫu `Gaming Neon 3D Button Demo` làm chuẩn: gradient 3 tầng có chiều sâu, viền neon, glow ngoài + inset, highlight mặt trên, chữ trắng đậm, hover sáng và active nhấn xuống.
- Thêm `static/css/gaming_neon_buttons.css` và nạp SAU toàn bộ page-specific CSS để trở thành lớp visual cuối, tránh CSS cũ ghi đè.
- Chỉ thay visual CSS; không đổi ID, route, JS handler, form action, vị trí hay kích thước layout.
- Giữ màu semantic: xanh lá = xác nhận/sẵn sàng; đỏ = thoát/nguy hiểm/từ chối; vàng = mời/đá tiếp/CTA; xám-xanh = phụ/hủy; xanh dương = mặc định; tím = Lucky Box/Random3.
- Loại trừ toàn bộ Admin bằng `data-ui-scope="admin"` và loại trừ Parsec tại `.parsec-room-panel` + `#parsec-profile`.
- `APP_VERSION`: 1.3.76 → 1.3.77.

# V1.3.76 — Room Pre-start Hierarchy + Invite Buttons

- Ngày: 2026-08-08 (Asia/Bangkok)
- Chế độ: NÂNG CẤP MODULE — Room UI / Invite UI.
- Đồng bộ `Chấp nhận` / `Từ chối` sang glass-neon và căn giữa trong popup/banner/trang lời mời.
- Loại trạng thái lặp `Chờ đối thủ sẵn sàng` khỏi center stage; readiness chỉ còn tại player card, counter giữa chỉ hiển thị số người.
- Bỏ pseudo-button `ĐỢI QUAY RANDOM ĐỘI` / `ĐỢI KHÁCH SẴN SÀNG`; readiness chỉ hiển thị một lần tại card người chơi, không lặp ở center stage.
- Host `BẮT ĐẦU TRẬN` có lane riêng phía trên action dock; `Thoát Phòng` nằm trong dock nền kính đậm riêng, tránh chồng chữ/trạng thái.
- Giảm footprint VS ở trạng thái waiting_ready để đủ không gian cho Series HUD + start/action controls.
- Áp dụng cùng cấu trúc cho Home/Away, BO3, Tactical BO3, Ban/Pick BO3 và các mode trận đơn.

# V1.3.75 — Room Action Button Visual Sync

- Chế độ: NÂNG CẤP MODULE giao diện phòng đấu.
- Dùng đúng ngôn ngữ visual glass/neon đã chốt ở V1.3.71 làm chuẩn cho toàn bộ nút chức năng của người chơi.
- Đồng bộ: Sẵn Sàng, Hủy Sẵn Sàng, Thoát Phòng/Bỏ cuộc, Gửi Kết Quả, Đá Tiếp, Về sảnh, Thoát an toàn, Đưa khỏi phòng và nút xác nhận kết quả.
- Màu semantic giữ nguyên: xanh = tích cực; xanh lam = phụ/huỷ; vàng = đá tiếp; đỏ = thoát/nguy hiểm.
- Giảm nền đặc/tối, tăng độ trong kính, viền neon và độ sáng chữ; hover tăng glow vừa phải.
- Chỉ scope trong Room action/result/kick; không tác động Parsec, gameplay, RP, backend hay Supabase.

# V1.3.74 — Room Action Visibility Guard

- Chế độ: FIX NHANH giao diện phòng đấu.
- Kiểm tra đủ 7 nhóm thao tác: Sẵn Sàng + Thoát Phòng; Hủy Sẵn Sàng; Thoát Phòng/Bỏ cuộc; Đá Tiếp + Về sảnh; Gửi Kết Quả; Thoát an toàn; Đưa khỏi phòng.
- Nguyên nhân: action group bị đặt lại về normal-flow trong `08-action-layout-guard.css`; với Mode card + Series HUD + VS, control ở cuối có thể bị đẩy khỏi khung center cố định 535px.
- Sửa: desktop dùng action dock cố định ở đáy cho các trạng thái `waiting_ready`, `playing`, `waiting_result_confirm`, `disputed`, `confirmed`; chừa khoảng trống 76px.
- `Gửi Kết Quả` dùng score dock riêng và chừa 158px.
- Host `Đưa khỏi phòng` được guard riêng trên card đối thủ khi `waiting_ready`, không phụ thuộc trạng thái Ready.
- Mobile giữ normal-flow để không che nội dung.
- Đồng bộ kiểm tra cả `_center_stage.html` và `_room_live_content.html` (polling).
- Test: 11 passed; compileall PASS.

# V1.3.73 — Profile + Match History Repository Binding Hotfix

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Chế độ
- FIX NHANH — Hồ sơ cá nhân / Lịch sử trận đấu.

## Lỗi
- `/matches` trả 500 tại `decorate_match_for_view()` vì `modules/core/match_repository.py` không có `is_forfeit_match` trong runtime globals.
- Hồ sơ cá nhân dùng cùng `decorate_match_for_view()` nên có thể lỗi cùng nguyên nhân khi dựng lịch sử/form/H2H.
- Supabase trả 200; lỗi nằm ở thứ tự binding Python, không phải dữ liệu.

## Nguyên nhân
- `match_repository` được configure trong core pass trước khi `forfeit_history_service` và các service sau đó export helper.
- Sau service registration chỉ `room_runtime` được refresh; `match_repository` không được refresh nên giữ context thiếu `is_forfeit_match`.

## Sửa
- `app.py`: refresh `_core_match_repository.configure(globals())` ngay sau khi toàn bộ service exports đã sẵn sàng.
- Giữ nguyên `decorate_match_for_view`, dữ liệu trận, RP và schema Supabase.
- `APP_VERSION`: 1.3.72 → 1.3.73.

## Không thay đổi
- Không sửa UI, RP, kết quả trận, database, Supabase, Room hoặc Admin.

---

# V1.3.72 — Room Host/Guest Action Visibility Hotfix

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Chế độ
- FIX NHANH giao diện phòng đấu.

## Lỗi
- Các nút chức năng của người chơi, đặc biệt phía đối thủ/guest khi đang thi đấu, có thể bị đẩy xuống dưới khung giữa và bị cắt vì center stage cố định 535px + overflow hidden.
- Khối Series HUD V1.3.71 làm tăng chiều cao luồng trung tâm, khiến lỗi dễ xuất hiện hơn ở playing/result states.

## Sửa
- `static/css/room/08-action-layout-guard.css`: compact các trạng thái playing/waiting_result_confirm/disputed/confirmed để dành lane hiển thị cho action footer.
- Thu gọn VS/countdown/mode card trong các trạng thái có nhiều control; không đổi logic gameplay.
- Giữ action zone của cả host và guest luôn visible trong vùng center stage.
- Bảo vệ nút `Đưa khỏi phòng` trên card đối thủ khỏi bị co/cắt bởi tên dài, streak badge hoặc trạng thái ready.
- `templates/room_detail.html`: thêm `data-viewer-role` để debug rõ host/guest/admin.
- `APP_VERSION`: 1.3.71 → 1.3.72.

## Không thay đổi
- Không sửa RP, API, Supabase, matchmaking, Series logic hay Parsec.

---

# V1.3.70 — Black Box Signal Cleanup

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Chế độ
- FIX NHANH / bảo trì Black Box; chỉ xử lý 2 WARNING còn lại của Safety Lab V1.3.69.

## Thay đổi
- Thay baseline nguồn Black Box cũ V1.3.52 bằng baseline an toàn V1.3.69 sau khi các regression hiện tại đã được xác nhận.
- `modules/blackbox/safety.py`: đọc `baseline_v1369.json` và hiển thị phiên bản baseline động thay vì hard-code V1.3.52.
- `static/js/blackbox_safety_lab.js`: overlap scanner chỉ so control trong cùng UI layer; bỏ false-positive giữa sticky topbar/overlay và nội dung trang cuộn phía dưới.
- Giữ kiểm tra off-screen control từ V1.3.68.
- `APP_VERSION`: 1.3.69 → 1.3.70.

## Không thay đổi
- Không sửa CSS layout thực tế, Room gameplay, RP, Match, Invite, Admin permission hay Supabase.
- Không thay schema/data production.

## Regression guard
- Thêm `test_v1370_blackbox_signal_cleanup.py` bảo vệ baseline mới, hash `room_runtime`, phân lớp overlap scanner và version.

---

# V1.3.69 — Project Docs / SQL Cleanup

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Chế độ
- AUDIT TOÀN HỆ THỐNG — dọn cấu trúc tài liệu/SQL/asset, không thay gameplay.

## Thay đổi
- Giữ `AGENTS.md`, `PROJECT_MAP.md`, `Log.md` ở root vì đây là entrypoint bắt buộc của dự án/chat mới.
- Gom tài liệu vận hành còn cần vào `project_docs/`: `README.md`, `FIX_NHANH_PES_ARENA.md`, `LOGGING_GUIDE.md`, `BLACKBOX_SAFETY_LAB.md`.
- Gom toàn bộ SQL duy nhất còn cần vào `project_docs/sql/`.
- Xóa 3 SQL root trùng 100% với bản trong docs: V1.3.34, V1.3.35, V1.3.48.
- Xóa các audit/version-note `.md` lịch sử không còn là source of truth.
- Xóa `.pytest_cache` và `logs/README.md`; hướng dẫn log đã được hợp nhất vào `project_docs/LOGGING_GUIDE.md`.
- Cập nhật toàn bộ path đang được source/template/test tham chiếu sang `project_docs/`.
- Asset scan: 0 file ảnh local; không cần upload thêm. Supabase chỉ được kiểm tra read-only, không thay đổi production.
- `APP_VERSION`: 1.3.68 → 1.3.69.

## An toàn
- Không thay RP, Room gameplay, Invite, Match, Admin permission hay schema production.
- Không chạy SQL/migration trên Supabase production.

---

# V1.3.68 — Black Box Storage + Admin Sticky Safety

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Phạm vi
- Xử lý các tồn tại từ Black Box Safety V1.3.67, không thay đổi gameplay/RP.

## Đã sửa
- `project_docs/sql/20260808_blackbox.sql`: bổ sung quyền server-only cho `service_role`, khóa `anon/authenticated`, giữ RLS.
- `modules/blackbox/safety.py`: nếu thiếu bảng Black Box thì báo rõ cần chạy migration thay vì chỉ hiện `APIError`.
- `static/css/admin_dashboard.css`: đẩy sticky Admin tabs xuống dưới sticky topbar (`102px`, mobile `84px`) để tránh chồng vùng thao tác khi cuộn.
- `static/js/blackbox_safety_lab.js`: bỏ qua control nằm hoàn toàn ngoài viewport để giảm false-positive overlap.
- `app.py`: tăng `APP_VERSION` lên `1.3.68`.
- Thêm `test_v1368_remaining_issues.py` bảo vệ migration/overlap/binding series.

## Supabase production
- Kiểm tra trực tiếp xác nhận `public.blackbox_events` và `public.blackbox_incidents` hiện chưa tồn tại.
- Việc áp dụng migration production qua connector bị chặn vì chưa được phê duyệt; source đã kèm migration hoàn chỉnh để chạy trên Supabase.

## Regression review Room
- Xác nhận `rank_series` export `is_series_child_match` trước khi `room_result_routes` được đăng ký. Không sửa luồng kết quả vì không tái hiện lỗi binding.

---

# V1.3.66 - Black Box Safety Lab Import Hotfix

**Ngày:** 2026-08-08 (Asia/Bangkok)

- Chế độ: FIX NHANH.
- Lỗi: Safety Lab báo `ImportError: attempted relative import with no known parent package` dù `/api/admin/blackbox/safety` vẫn trả HTTP 200 degraded.
- Nguyên nhân gốc: `modules/blackbox/routes.py::register_routes()` gọi `globals().update(context)`. Context lấy từ `app.py` có thể ghi đè metadata module như `__package__`, nên lazy relative import `from .safety ...` mất package cha.
- Sửa: đổi lazy import Safety Lab sang absolute import `from modules.blackbox.safety import run_server_safety_audit`.
- Phạm vi: chỉ Black Box Safety Lab import; không đổi gameplay, Admin permission, database, Supabase, CSS hoặc UI.
- Regression guard: cập nhật `test_blackbox_safety_import_guard.py` để cấm quay lại relative import trong route có context binding.
- Kiểm tra: Python compile + Black Box Safety import regression + Safety Lab server smoke test.

# V1.3.65 - Admin Permission Binding Hotfix

- Chế độ: FIX NHANH.
- Lỗi: `/admin` trả HTTP 500 với `NameError: _admin_permissions is not defined`.
- Nguyên nhân: `modules/core/system_settings_runtime.py` có `_admin_permissions()` nhưng không export qua `EXPORTED_NAMES`; các module `user_repository.py` và `admin_dashboard_routes.py` nhận dependency bằng `globals()` nên không thấy helper này.
- Sửa: thêm `_admin_permissions` vào `EXPORTED_NAMES`, giữ nguyên logic permission hiện tại; không thay đổi route, UI, database hoặc RLS.
- Kiểm tra: compile Python + binding smoke test + test Admin liên quan.

# V1.3.64 — Persistent AI Workflow Rules

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Mục tiêu
- Lưu quy tắc làm việc trực tiếp trong dự án để các phiên/đoạn chat mới không phụ thuộc vào lịch sử chat cũ.
- Tự động phân loại yêu cầu thành: **FIX NHANH**, **NÂNG CẤP MODULE**, hoặc **AUDIT TOÀN HỆ THỐNG**.

## Thay đổi
- Tạo `AGENTS.md` ở root: quy tắc khởi động, điều kiện chọn 3 chế độ, luồng xử lý, quy tắc tự chuyển chế độ và safety guard.
- `PROJECT_MAP.md`: thêm chỉ dẫn bắt buộc đọc `AGENTS.md` trước khi định tuyến file/module; cập nhật mốc V1.3.64.
- `project_docs/FIX_NHANH_PES_ARENA.md`: liên kết về workflow 3 chế độ trong `AGENTS.md`.
- `app.py`: tăng phiên bản 1.3.63 → 1.3.64.

## Không thay đổi
- Không thay route/API/gameplay/RP/Admin/Supabase/CSS.
- Không thay cấu trúc runtime ngoài tài liệu workflow.

## Kiểm tra
- Python compile `app.py`: PASS.
- Xác minh `AGENTS.md`, `PROJECT_MAP.md`, `project_docs/FIX_NHANH_PES_ARENA.md` có liên kết chéo: PASS.

---

# V1.3.63 — Admin 500 Safety Hotfix

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Lỗi
- Sau V1.3.62, người dùng báo `/admin` trả `Internal Server Error`.
- Diff xác nhận route/template Admin không bị sửa trực tiếp trong V1.3.62; thay đổi rủi ro nhất là đã xóa `templates/partials/room_dynamic_state.html` trong quá trình dọn asset.

## Sửa
- Khôi phục `templates/partials/room_dynamic_state.html` từ V1.3.61 để không xóa thành phần template/runtime chỉ vì không thấy tham chiếu tĩnh.
- Thay 3 đường dẫn `static/rank_frames/*.png` trong partial bằng `asset_url('ranks/*-card.webp')` trên Supabase.
- Giữ kiến trúc remote-only: không khôi phục bất kỳ ảnh local nào.
- `app.py`: tăng phiên bản 1.3.62 → 1.3.63.

## Kiểm tra
- `admin.html` Jinja parse: PASS.
- `partials/room_dynamic_state.html` Jinja parse: PASS.
- Python compile: PASS.
- Nhóm test Admin chính: PASS (admin performance, admin room cleanup, rank modes, blackbox, read model, system inspection).
- Một số test lịch sử khác vẫn stale/missing fixture từ trước và không liên quan hotfix này.

---

# V1.3.62 — Remote Asset Cleanup

**Ngày:** 2026-08-08 (Asia/Bangkok)

## Mục tiêu
- Làm gọn ZIP Production và loại bỏ ảnh đã có trên Supabase Storage.
- Biến Supabase thành nguồn mặc định cho ảnh chung, Shop, Lucky Box, Room và logo chế độ.

## Thay đổi
- `modules/static_asset_service.py`: thêm default URL Supabase đã xác minh cho `STATIC_ASSET_BASE_URL`, `SHOP_ASSET_BASE_URL`, `LUCKYBOX_ASSET_BASE_URL`; Room/Mode tiếp tục dùng URL mặc định Supabase.
- `static/css/room/01-shell-layout.css`, `static/css/room/02-club-visuals.css`: fallback ảnh Room chuyển từ file local sang URL Supabase.
- Xóa `static/assets/room_v2/`: 8 ảnh local đã trùng với `pes-assets/room-assets/v1.3.18/`.
- Xóa `UPLOAD_SUPABASE/`: gói staging 8 ảnh đã upload xong, không còn cần trong bản Production.
- `.env.example`: các biến asset đổi thành optional override, không còn bắt buộc để ảnh hoạt động.
- `PROJECT_MAP.md`: bổ sung chính sách asset remote-only.
- Cập nhật test Room asset theo kiến trúc remote-only.
- Xóa `templates/partials/room_dynamic_state.html`: partial không còn được runtime tham chiếu và còn trỏ tới `static/rank_frames/*.png` đã không tồn tại.
- Xóa `HUONG_DAN_UPLOAD_LOGO_V1.3.40.txt`: hướng dẫn upload một lần đã hoàn tất, tránh làm rối root dự án.
- Fallback nền login trong CSS legacy cũng chuyển sang Supabase, không còn URL ảnh local.
- `app.py`: tăng phiên bản `1.3.61` → `1.3.62`.

## Supabase đã đối chiếu
- `pes-assets/v1/`: 27 file.
- `pes-assets/v1.14.41/shop/`: 30 file.
- `pes-assets/v1.14.41/luckybox/`: 18 file.
- `pes-assets/room-assets/v1.3.18/`: 21 file.
- `pes-assets/room-assets/v1.3.40/modes/`: 6 file.

---

# V1.3.61 — App Core Map + Logging Standard

**Ngày:** 08/08/2026 02:13 (Asia/Bangkok)  
**Phạm vi:** `app.py`, core infrastructure, project map, logging docs  
**Loại:** Refactor an toàn + Developer Workflow

## Thay đổi
- Giảm `app.py` từ khoảng 3.547 xuống khoảng 3.193 dòng mà không di chuyển các route Invite/Quick Match/Room nhạy cảm đang bị regression test đọc trực tiếp.
- Tách xử lý ảnh bằng chứng tranh chấp sang `modules/core/dispute_evidence.py`.
- Tách System Features / Quick Match config / Repeat Opponent config / Maintenance sang `modules/core/system_settings_runtime.py`.
- Giữ public function/constant được bind ngược vào `app.py` để các route module cũ tiếp tục dùng cùng tên, giảm nguy cơ circular import/startup crash.
- Thay các `print(... warning)` ở hai nhóm helper vừa tách bằng structured runtime event qua `log_system_event`.
- Tạo `PROJECT_MAP.md`: lỗi/luồng → frontend → backend → database → test cần đọc.
- Lưu prompt chuẩn tại `project_docs/FIX_NHANH_PES_ARENA.md`.
- Chuẩn hóa changelog/runtime log bằng `project_docs/LOGGING_GUIDE.md` và `logs/README.md`.

## File thay đổi
| File | Chức năng | Thay đổi |
|---|---|---|
| `app.py` | Flask bootstrap/legacy routes | tách helper hạ tầng, giữ compatibility binding, version 1.3.61 |
| `modules/core/dispute_evidence.py` | Dispute evidence | validate/resize/upload/remove/signed URL |
| `modules/core/system_settings_runtime.py` | System runtime config | permissions/features/Quick Match/repeat-opponent/maintenance |
| `PROJECT_MAP.md` | Project routing map | xác định file cần đọc theo từng luồng |
| `project_docs/FIX_NHANH_PES_ARENA.md` | Prompt workflow | lưu prompt FIX NHANH chuẩn |
| `project_docs/LOGGING_GUIDE.md` | Logging standard | chuẩn hóa changelog + JSONL runtime log |
| `logs/README.md` | Runtime log quick guide | schema/search/rotate |
| `test_app_structure_v1361.py` | Regression | kiểm tra cấu trúc và compatibility binding |

## Kiểm tra
- `python -m py_compile app.py modules/core/dispute_evidence.py modules/core/system_settings_runtime.py`: PASS.
- Smoke test `system_settings_runtime`: PASS.
- Smoke test ảnh PNG → WebP qua `dispute_evidence`: PASS.
- Test kiến trúc/binding chọn lọc: **10/10 PASS**.
- Baseline V1.3.60 full pytest đã có 4 lỗi collection trước khi sửa: 2 source-test Room cũ + thiếu 2 SQL Lucky Box lịch sử.
- Một số regression test lịch sử còn hard-code version/HTML monolith cũ; không dùng chúng để kết luận regression V1.3.61 nếu failure giống baseline.
- Không import được full Flask runtime trong sandbox hiện tại vì môi trường thiếu package `flask`; đây là giới hạn môi trường kiểm tra, không phải lỗi compile của source.

## Không thay đổi
- Không thay logic RP/gameplay.
- Không thay Invite/Quick Match route flow.
- Không thay Room route flow.
- Không thay CSS/UI gameplay.
- Không thay schema Supabase.

---

# V1.3.60 — Safety Lab Import Guard

- Sửa `NameError: cannot access free variable 'exc'` trong Safety API V1.3.59.
- Nguyên nhân: fallback function được định nghĩa trong `except Exception as exc` rồi tham chiếu `exc`; Python xóa exception variable sau khi rời `except`.
- Chuyển Safety Lab sang lazy loader `_load_safety_runner()` tại thời điểm gọi API.
- Nếu `modules.blackbox.safety` import lỗi: API vẫn trả JSON `200` ở chế độ degraded và ghi rõ lỗi import thật.
- Nếu audit runtime lỗi: API vẫn trả JSON lỗi có cấu trúc.
- Không sửa Room / RP / Match / Invite / Presence / CSS gameplay.
- Thêm regression test chống closure giữ exception variable.

# V1.3.59 — Safety API + Modular Boundary Cleanup

- Sửa Safety Lab: backend luôn trả JSON khi audit runtime lỗi; frontend không parse JSON mù khi nhận HTML/redirect.
- Sửa `room/_extra_controls.html` không còn đóng thẻ thuộc file cha; loại bỏ 1 `</div>` dư legacy.
- `room_detail.html` tự sở hữu/đóng `#roomLiveShell`.
- Audit `room_detail.html`, `style.css`, `app.py`; ghi `MODULAR_CLEANUP_AUDIT_V1.3.59.md`.
- Không thay logic RP / Room core / Match / Invite / Presence.
- Thêm `test_v1359_safety_cleanup_regression.py`.

# V1.3.58 — Modular Startup Binding Audit Fix

- Sửa `AttributeError: module 'modules.blackbox' has no attribute 'blackbox_config'`.
- `modules/blackbox/__init__.py` giờ re-export toàn bộ `EXPORTED_NAMES` từ service giống các package module khác.
- Thêm test tổng quát `test_service_binding_exports.py` để mọi module trong vòng service binding phải có đủ export trước deploy.
- Giữ các guard V1.3.56/V1.3.57 cho core symbol và import-time dependencies.
- Không thay logic Room / RP / Match / Invite / Presence.

# V1.3.57 — Modular Import-Time Dependency Fix

- Sửa startup crash `RECENT_TEAM_EXCLUSION_COUNT is not defined` trong `rank_team_service.py`.
- Rà toàn bộ `modules/core` và sửa cùng lúc 4 dependency bị đánh giá quá sớm khi import:
  - `RECENT_TEAM_EXCLUSION_COUNT`
  - `HOST_XP_FACTOR`
  - `ROOM_ABANDON_PENALTY`
  - `SERIES_FORFEIT_RP`
- Không copy/nhân đôi giá trị config sang module; default argument đổi thành `None`, constant được đọc khi hàm chạy sau `configure(context)`.
- Thêm `test_core_import_time_dependencies.py` để chặn lỗi tương tự trước deploy.
- Không thay đổi công thức RP, Room, Match, Invite hay Presence.

# V1.3.56 — Core Startup Binding Fix

- Sửa `NameError: list_user_devices is not defined` khi Vercel import `app.py`.
- Nguyên nhân: V1.3.52 đã tách `list_user_devices()` sang `modules/core/user_repository.py` nhưng để sót dòng khởi tạo `.last_status` trong `app.py` trước block bind core.
- Chuyển dòng khởi tạo về đúng module sở hữu hàm.
- Không thay logic Room / RP / Match / Invite / Presence.
- Thêm `test_core_startup_binding_regression.py` để phát hiện core symbol bị dùng trước khi bind.

# V1.3.54 — Black Box Safety Lab / Kill Switch / Automated Audit

**Ngày:** 08/08/2026 (Asia/Bangkok)

## An toàn triển khai
- Sửa Kill Switch frontend: chỉ load `blackbox.js` khi cả `BLACKBOX_ENABLED` và `BLACKBOX_CLIENT_ENABLED` bật. Khi client OFF không gắn listener/timer/wrap fetch.
- Thêm `modules/blackbox/safety.py` và baseline hash V1.3.52 cho 14 module gameplay quan trọng.
- Thêm crash test fail-open bằng storage override trong bộ nhớ; không ghi dữ liệu giả vào Supabase.
- Thêm storage probe read-only.

## Safety Lab Admin
- Tab `🛡 Black Box` có nút `▶ Chạy kiểm tra tự động`.
- Tự chạy Server audit + Browser micro benchmark + UI/CSS overlap scan + Navigation Timing.
- Kết quả tách `PASS / WARNING / FAIL / NOT TESTED`, không giả PASS cho luồng gameplay 2 người.
- Cho phép xuất báo cáo JSON.

## Kiểm tra trước đóng gói
- Python compile: PASS.
- JavaScript syntax (`blackbox.js`, `blackbox_safety_lab.js`): PASS.
- Source isolation: 14/14 module gameplay quan trọng không đổi so với V1.3.52.
- Forced storage exception fail-open: PASS.
- Full Flask runtime chưa chạy trong sandbox do môi trường không cài Flask.

---

# V1.3.53 — PES Arena Black Box + Chrome Debugger

**Ngày:** 08/08/2026 (Asia/Bangkok)

## Black Box tích hợp
- Nâng `modules/observability` thành hệ giám sát hai lớp: logging request sẵn có + `modules/blackbox` lưu event/incident riêng.
- Frontend `static/js/blackbox.js` ghi buffer tối đa, gửi batch nền, theo dõi JS error/unhandled rejection/API chậm/API lỗi/click quan trọng/page visibility.
- Luồng fail-open: lỗi bảng Black Box hoặc lỗi lưu telemetry không làm hỏng request/gameplay; endpoint ingest vẫn trả accepted để tránh block giao diện.
- Tự che các trường nhạy cảm: password, secret, token, Authorization, cookie, session, API key và Parsec.
- Thêm tab Admin `🛡 Black Box` và trang Timeline theo incident/session.
- Thêm migration riêng `project_docs/sql/20260808_blackbox.sql`; không sửa schema Room/Match/RP.

## Chrome Extension bổ trợ
- `chrome_extension/pes_arena_blackbox/`: Manifest V3, giữ 60 giây event gần nhất trên tab test.
- Bắt JS error, unhandled rejection, console.error, fetch status/duration và click nút/link.
- Cho phép xuất report JSON và chụp màn hình hiện tại.
- Extension là công cụ Admin/Test, không thay thế Black Box server.

## Test
- `test_blackbox_v1353.py`: 6/6 PASS.
- Python compile Black Box + app.py: PASS.
- Chrome manifest JSON: PASS.
- Full Flask runtime import chưa chạy trong sandbox do môi trường không cài package Flask; không phải lỗi source của dự án.

---

# V1.3.52 — Module hóa Room / CSS legacy / App Core + System Logging

**Ngày:** 08/08/2026 (Asia/Bangkok)

## Tái cấu trúc
- `templates/room_detail.html`: giảm từ 1.596 dòng xuống còn file điều phối ~50 dòng; tách thành 8 partial giao diện + 3 module script theo chức năng.
- `static/style.css`: giảm từ 5.320 dòng xuống entrypoint 11 dòng; tách nguyên thứ tự cascade cũ thành 6 file `static/css/legacy/*` để tránh thay đổi giao diện ngoài ý muốn.
- `app.py`: giảm từ 6.577 dòng xuống dưới 3.500 dòng; tách core thành `modules/core/achievements.py`, `rank_team_service.py`, `room_runtime.py`, `user_repository.py`, `match_repository.py`, `social_runtime.py`, `matchmaking_runtime.py`.
- Giữ tên hàm public cũ thông qua lớp compatibility export để các route/module hiện tại không phải đổi đồng loạt trong một release.

## Logging hệ thống
- Thêm `modules/observability/app_logging.py`.
- Mỗi request có `X-Request-ID`, thời gian xử lý, endpoint, status.
- Request quá `PES_SLOW_REQUEST_MS` ghi event `slow_request`.
- Supabase retry/fail ghi `database_query_retry` / `database_query_failed`.
- Exception chưa xử lý ghi `uncaught_exception` kèm traceback.
- Local/dev hỗ trợ rotating file `logs/pes_arena.log`; production/serverless ghi stdout để Vercel thu log.
- Không ghi password/session cookie/API key/bytes bằng chứng vào log.

## Tài liệu / Test
- `docs/MODULE_ARCHITECTURE_V1.3.52.md`
- `project_docs/LOGGING_GUIDE.md`
- `test_modular_refactor_v1352.py`
- Python compile: PASS.
- Jinja parse toàn bộ module Room mới: PASS.
- 4 kiểm tra cấu trúc V1.3.52: PASS.
- Không thay schema Supabase, công thức RP, Series, Ban/Pick hoặc luật gameplay.

---

# V1.3.50 — Sửa lõi chọn chế độ + tối ưu tải phòng + audit Series

**Ngày:** 08/08/2026 (Asia/Bangkok)

## Sửa lỗi
- Sửa nguồn chọn mode mặc định: không còn dùng `rank_standard_enabled` để suy ra Rank thường. Nếu Admin chỉ bật Lượt đi/về, phòng mới lưu đúng `home_away`.
- Xóa fallback trong `enrich_room()` từng ép room về Random 3; thêm reconcile có điều kiện cho waiting room cũ có mode đã bị khóa.
- Thêm `team_tier`, `match_mode`, `updated_at`, `series_version` vào state key để mode/Series thay đổi được realtime refresh.
- API state dùng `get_room_poll_snapshot()` thay `get_room()` để không hydrate users/team/cosmetics trên mỗi poll.
- Gỡ N+1 ở catalog 6 chế độ: daily status chỉ tải 1 lần/player; cache config Rank/Daily trong request + TTL ngắn.
- Sửa auto-confirm child Series: dùng `confirm_series_child_match()` thay vì engine RP trận đơn.
- Sửa tranh chấp child Series: hủy Series và đóng child game đang mở, tránh Series mồ côi/duplicate game.

## File chính
- `app.py`
- `modules/rank_modes/service.py`
- `modules/daily_rank_limit_service.py`
- `modules/room_access_routes.py`
- `modules/room_result_routes.py`
- `modules/rank_series/service.py`
- `test_room_architecture_v1350.py`
- `docs/ROOM_SERIES_ARCHITECTURE_AUDIT_V1.3.50.md`

## Test
- 45 test tập trung phòng/Series PASS.
- Không cần SQL mới so với V1.3.49/V1.3.48.

---

# V1.3.49 — Sửa quay quân trận con thứ 2 của Series

- Ngày: 2026-08-07 (Asia/Bangkok)
- Lỗi: sau khi xác nhận trận con đầu tiên, live polling render `templates/partials/room_dynamic_state.html` với form quay đội trỏ nhầm về `/room/<id>/random-teams`. Endpoint này chặn mọi mode khác Rank thường nên hiện popup “Phòng đã được quay đội hoặc đã tạo trận” / không thể tạo trận thứ 2.
- Sửa `templates/partials/room_dynamic_state.html`: đồng bộ route với `room_detail.html` và `_room_live_content.html`; 4 mode Series gọi `room_series_start_next_game`, Random 3 gọi route riêng, Rank thường mới gọi `room_random_teams`.
- Sửa `modules/room_team_routes.py`: thêm lớp tương thích ngược, nếu client/polling cũ vẫn gọi `/random-teams` trong Series thì tự dispatch sang `prepare_next_series_game()` thay vì rơi vào luồng Rank thường.
- Giữ nguyên `team_tier` của Series, `guest_ready=True`, xóa `match_id`/đội cũ sau trận con để trận tiếp theo tạo sạch.
- Thêm `test_series_second_game_v149.py`.

## V1.3.47 - 2026-08-07 22:58 (Asia/Bangkok)

### Sửa luồng hiển thị 6 chế độ Rank + chống CSS chồng nút
- Sửa `enrich_room()` để `match_mode_label` lấy trực tiếp từ `rank_mode_configs_v1` theo `team_tier`; Lượt đi/về, BO3, Chiến thuật BO3 và Cấm chọn BO3 không còn bị hiển thị thành Rank thường.
- Khóa `room_random_teams()` chỉ cho `rank_random`; ngăn các mode Series rơi nhầm vào smart random rồi ghi đè `team_tier`.
- Đồng bộ `room_detail.html` và `_room_live_content.html` cùng dùng `selected_rank_mode`.
- Thêm module CSS `08-action-layout-guard.css`: bỏ offset `left/bottom/transform` gây chồng `QUAY QUÂN` với `THOÁT PHÒNG`, đồng thời nén riêng trạng thái `waiting_ready`.
- Kiểm tra kiến trúc: Admin là nguồn bật/tắt mode; phòng chỉ lưu/chọn `mode_code`; giao diện đọc đúng mode hiện tại. 4 mode Series hiện có lõi cấu hình/RP nhưng chưa có bộ điều phối trận con hoàn chỉnh nên được chặn không cho chạy nhầm luồng Rank thường.
- Thêm `test_room_mode_display_v147.py`.

## V1.3.37 — Module hóa luồng dữ liệu + CSS Flow Audit

**Ngày giờ:** 2026-08-07 13:28 (Asia/Bangkok)

### Nội dung
- Tách Presence Frontend khỏi `base.html` sang `static/js/presence.js`.
- Tách quyết định Online/Offline sang `modules/presence/service.py`; Players, Invite và Quick Match tiếp tục dùng một nguồn chuẩn `is_user_online_now()`.
- Tách popup/fetch lời mời Frontend sang `static/js/invite_center.js`.
- Tách điều kiện chặn gửi/nhận lời mời sang `modules/invites/service.py`; route chỉ còn đọc request, lấy trạng thái DB, gọi service và ghi dữ liệu.
- Thêm `docs/MODULE_FLOW_V1.3.37.md` mô tả chuỗi kiểm lỗi Frontend -> API -> Backend -> Supabase -> View Model -> DOM -> CSS.
- Thêm `scripts/audit_css_flow.py` và báo cáo `docs/CSS_FLOW_AUDIT_V1.3.37.txt`.
- Audit phát hiện `arena_room_v2.css` có 124 selector lặp; `style.css`/các module hiện có nhiều `!important`. Không xóa hàng loạt để tránh làm vỡ giao diện; đưa vào danh sách hotspot cần dọn theo module ở các bản sau.
- Xác nhận `.arena-room-v2 .room-center-mode-zone {display:none}` là UI legacy ẩn có chủ đích vì giao diện hiện tại dùng `.room-master-mode-switcher`; không tự mở lại.
- Không thay đổi schema Supabase, công thức RP hoặc điều kiện mở khóa Rank.

### File chính thay đổi/thêm
- `app.py`
- `templates/base.html`
- `static/js/presence.js`
- `static/js/invite_center.js`
- `modules/presence/__init__.py`
- `modules/presence/service.py`
- `modules/invites/__init__.py`
- `modules/invites/service.py`
- `scripts/audit_css_flow.py`
- `docs/MODULE_FLOW_V1.3.37.md`
- `docs/CSS_FLOW_AUDIT_V1.3.37.txt`
- `test_module_boundaries_v137.py`
- `test_presence_invite_modules_v137.py`

### Kiểm tra
- `python -m py_compile app.py modules/presence/service.py modules/invites/service.py`: PASS.
- `node --check` Presence/Invite/Quick Match JS: PASS.
- 31 test hiện hành liên quan Presence, Invite, Quick Match, Rank Mode, Room Action/Result, Parsec và Room cleanup: PASS.
- Một số test legacy trong source vẫn hard-code version/HTML cũ; không dùng làm tiêu chí V1.3.37.

### So với V1.3.36
- V1.3.36 sửa độ tin cậy Presence/Invite.
- V1.3.37 giữ logic đó nhưng tách thành module độc lập và bổ sung CSS flow audit để truy nguyên lỗi dễ hơn.

## V1.3.36 — Fix Presence Online + Invite Reliability
**Thời gian:** 2026-08-07 13:20 (Asia/Bangkok)

### Nội dung
- Nâng `APP_VERSION` từ `1.3.35` lên `1.3.36`.
- Tăng `ONLINE_TIMEOUT_SECONDS` từ 60 lên 120 giây để tránh heartbeat sát ngưỡng timeout.
- Heartbeat Frontend: 30 giây khi tab hiển thị, 60 giây khi tab nền, `runWhenHidden: true`, `immediate: true`, jitter 3 giây.
- Khi quay lại trình duyệt từ PES2021/Parsec (`focus`/`visibilitychange`) gửi heartbeat ngay, có throttle 5 giây.
- Bỏ `pagehide -> /presence/offline` ở Frontend để tránh Refresh/Back/Forward ghi Offline giả.
- Giữ `/presence/offline` dạng no-op tương thích với tab/client cũ đang mở khi deploy.
- Logout thật vẫn cập nhật `is_online=false` như cũ.
- Loại bỏ việc heartbeat bị UPDATE presence hai lần trong cùng request (`before_request` + route `/heartbeat`).
- Request thường vẫn cập nhật presence dự phòng tối đa mỗi 60 giây.
- Đồng bộ Tìm Nhanh với cùng `ONLINE_TIMEOUT_SECONDS=120`, không còn ngưỡng riêng 90 giây.
- Không thay đổi schema Supabase, không cần chạy SQL mới.

### Kiểm thử
- `python -m py_compile app.py`: PASS.
- 15/15 test hiện hành liên quan Presence / Quick Match / Room action / Rank unlock: PASS.
- Thêm `test_presence_invite_v136.py` để khóa các quy tắc Presence mới.
- Một số test legacy V1.2.x trong source vẫn hard-code version/HTML cũ và đã stale từ trước; không dùng làm tiêu chí release V1.3.36.

### File sửa
- `app.py`
- `templates/base.html`
- `Log.md`
- `test_presence_invite_v136.py`

## V1.3.35 — Chốt công thức RP Series + hòa random

- Random thường và Random 3 chọn 1 tiếp tục dùng cùng cơ chế RP thắng/thua hiện tại.
- Tất cả kết quả hòa: chênh dưới 500 RP thì mỗi người random độc lập +1..+6; chênh từ 500 RP thì chỉ người điểm thấp random +1..+6, người điểm cao +0.
- Bỏ bonus chênh trình khỏi luật hòa.
- Bỏ cuộc toàn hệ thống giữ mức cố định -20 RP; người được xử thắng không nhận RP từ sự kiện bỏ cuộc.
- Lượt đi/về: base +30/+22/+15/-10/-22/-28 đúng bảng đã chốt.
- BO3: +32/+25/-23/-28.
- Chiến thuật BO3: +32/+25/-23/-31.
- Cấm chọn BO3: +32/+25/-23/-31.
- RP Series cuối = base + random(-2,+3), random đúng một lần cho mỗi người.
- Thêm helper audit `mode_rp_audit_payload()` và migration Supabase cho base/variance/final của hai người.
- Các trường audit RP không được tham chiếu trong template người chơi; UI chỉ hiện tổng RP cuối.
- Bump RP engine lên `RP_V1.14.6` và APP_VERSION lên `1.3.35`.

### SQL cần chạy
- `SUPABASE_UPDATE_V1.3.35.sql`

## V1.3.34 — Read Model / Stats Cache, bỏ tính toán nặng khi click

- Chuyển **Admin → Báo cáo số trận** sang mô hình read-model: tab chỉ SELECT dữ liệu tổng hợp có sẵn trong Supabase, không tải `matches / match_rooms / match_series / match_series_games` rồi tính lại trong Python.
- Thêm các bảng cache thống kê theo ngày/chế độ/series/người tham gia và số user mở khóa mode.
- Thêm trigger Supabase: dữ liệu cache được cập nhật khi trận/series/user/unlock/config thay đổi; có backfill cho dữ liệu cũ.
- Thêm `mode_code` trực tiếp vào `matches` để báo cáo không phải đoán mode từ `note` hoặc `rp_details`.
- BXH lấy phong độ 5 trận từ `player_recent_form_cache`, bỏ quét toàn bộ trận confirmed mỗi lần mở BXH.
- Dashboard chỉ lấy trận của đúng user (`LIMIT 30`), không `list_matches()` toàn hệ thống.
- Hồ sơ người chơi dùng cache đội yêu thích, đối thủ thường gặp và H2H; lịch sử gần đây query đúng user/cặp người chơi.
- Admin IP trùng ưu tiên `admin_user_ip_summary_cache`, không group toàn bộ `user_devices` ở mỗi lần mở tab.
- Nếu SQL V1.3.34 chưa được chạy, Báo cáo trận **không fallback quét lịch sử**; giao diện báo rõ cần chạy migration để tránh request bị treo.
- Thêm `SUPABASE_UPDATE_V1.3.34.sql` ở thư mục gốc và tài liệu `docs/READ_MODEL_AUDIT_V1.3.34.md`.
- Cập nhật `APP_VERSION` thành `1.3.34`.

### File chính đã sửa/thêm
- `app.py`
- `modules/read_model_service.py`
- `modules/admin_dashboard_routes.py`
- `modules/profile/service.py`
- `modules/room_team_routes.py`
- `modules/forfeit_history_service.py`
- `templates/admin/tabs/match-report.html`
- `static/css/admin_dashboard.css`
- `SUPABASE_UPDATE_V1.3.34.sql`
- `project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql`
- `docs/READ_MODEL_AUDIT_V1.3.34.md`


## V1.3.33 — Tối ưu toàn bộ luồng Admin và sửa lỗi hủy phòng 500

### Nguyên nhân chính đã phát hiện
- Route `/admin` cũ vừa đọc dữ liệu vừa chạy `cleanup_duplicate_waiting_rooms()` cho từng người tham gia phòng. Đây là N+1 truy vấn Supabase và có thể tạo hàng chục/hàng trăm request chỉ trong một lần mở tab.
- Tab Báo cáo gọi `list_matches()` nên tải toàn bộ bảng `matches`, enrich người chơi và chạy kiểm tra auto-confirm trên từng trận, dù chỉ xem Hôm nay/Hôm qua.
- Phần “Đã mở khóa” gọi `check_rank_mode_eligibility()` cho từng user × 6 chế độ; mỗi lần tiếp tục đọc config và quyền mở khóa từ database, gây bùng nổ số truy vấn.
- Báo cáo tải toàn bộ `match_series`, `match_series_games`, `match_rooms` và `users` trước khi lọc thời gian.
- Trang Tổng quan tải toàn bộ phòng và toàn bộ trận chỉ để lấy số lượng trạng thái.
- Route hủy phòng dùng `.execute()` trực tiếp và không có lớp bắt lỗi tổng; chỉ cần update phòng/lời mời lỗi là trả thẳng Internal Server Error.

### Đã sửa
- Loại bỏ hoàn toàn cleanup phòng trùng khỏi request đọc tab Admin. Không còn thao tác ghi/xóa dữ liệu khi chỉ mở trang.
- Tab Báo cáo dùng query riêng, chỉ chọn các cột cần thiết và lọc `created_at` ngay tại Supabase.
- Khoảng Hôm nay/Hôm qua/3 ngày/1 tuần/1 tháng không còn tải toàn bộ lịch sử.
- Toàn thời gian có giới hạn an toàn 10.000 trận để tránh request serverless vượt tài nguyên.
- Query phòng liên kết và Series được lọc theo cùng khoảng ngày; chế độ Toàn thời gian có limit an toàn.
- Tải cấu hình Rank và quyền mở khóa đúng 1 lần; tính số tài khoản đủ điều kiện hoàn toàn trong RAM, không gọi database theo từng user × mode.
- Trang Tổng quan chỉ query các cột `id,status,note` và giới hạn dữ liệu phục vụ thống kê.
- Thêm log `ADMIN_PERF` gồm tab, khoảng báo cáo, thời gian xử lý và số dòng đã tải để kiểm tra trực tiếp trong Vercel Logs.
- Route hủy phòng chuyển sang `execute_query()` có retry ngắn, idempotent khi double-click, tách lỗi cập nhật lời mời khỏi lỗi hủy phòng và luôn redirect kèm thông báo thay vì trang 500.
- Lỗi ghi nhật ký hoặc lỗi lời mời phụ không còn làm hỏng thao tác chính.
- Cập nhật `APP_VERSION` thành `1.3.33`.

### File đã sửa
- `app.py`
- `modules/admin_dashboard_routes.py`
- `modules/admin_data_routes.py`
- `test_admin_performance_v1333.py`

### Kiểm tra
- Python compile: đạt.
- Jinja parse các tab Admin: đạt.
- Test tối ưu V1.3.33: 3/3 đạt.
- Hai test legacy cũ đọc chuỗi trực tiếp từ `admin.html` không còn phù hợp sau khi Admin đã tách tab thành partial; không phải lỗi runtime.


## V1.3.32 — Tách Admin theo tab, thu gọn Parsec và làm sáng nút phòng

- Giảm `templates/admin.html` từ khoảng 71 KB xuống còn khung chung khoảng 4 KB.
- Tách 12 tab Admin thành các template trong `templates/admin/tabs/`.
- Route `/admin` nhận `?tab=` và chỉ gọi dữ liệu cần cho tab đang mở; không còn tải đồng thời user, phòng, trận, báo cáo, nhật ký và cấu hình cho mọi lần truy cập.
- Sửa `admin_dashboard.js`: bấm tab chuyển sang URL module riêng và hiển thị trạng thái đang tải.
- Cập nhật các redirect của Quản lý người dùng và Quản lý chế độ Rank về đúng tab mới.
- Đưa nút `Lưu` và `Xóa` lên cùng hàng với ô Link Parsec.
- Bỏ `flex: 1` của panel Parsec, thu gọn padding, khoảng cách, input và nút để panel chỉ cao đúng nội dung.
- Tăng không gian hiển thị và vùng cuộn của Lịch sử đấu.
- Làm sáng Mời đấu / Tìm nhanh / Thoát phòng bằng nền kính vàng, xanh, đỏ trong hơn; viền nhẹ và đồng bộ hơn.
- Thêm `docs/MODULE_AUDIT_V1.3.32.md`.
- Cập nhật `APP_VERSION` thành `1.3.32`.

### File chính đã sửa
- `app.py`
- `modules/admin_dashboard_routes.py`
- `modules/admin_player_routes.py`
- `templates/admin.html`
- `templates/admin/tabs/*.html`
- `templates/partials/parsec_room_panel.html`
- `static/js/admin_dashboard.js`
- `static/css/arena_room_v2.css`
- `docs/MODULE_AUDIT_V1.3.32.md`


## V1.3.31 — Sửa lag tab Admin, gom quản lý chế độ và chuẩn hóa thông báo

- Sửa lỗi nghiêm trọng trong `admin_dashboard.js`: listener `pointerdown` từng được tạo lại bên trong hàm đổi tab, khiến số listener tăng sau mỗi lần click và tab Admin ngày càng lag.
- Viết lại luồng tab Admin bằng một listener duy nhất, lazy-load iframe đúng lúc và lọc user bằng `requestAnimationFrame`.
- Trình bày lại tab **Quản lý chế độ Rank**: bỏ công tắc trùng, thu gọn thẻ và đóng phần công thức RP mặc định.
- Chuyển **Mở khóa chế độ theo tài khoản** vào phần Quản lý của từng người dùng.
- Chuyển công tắc bật/tắt cả 6 chế độ Rank về **Bật/tắt tính năng hệ thống**.
- Route lưu cấu hình Rank không còn tự tắt mode khi form không gửi trường `enabled`.
- Thêm module dùng chung `ui_dialog.js/css` để thay các hộp xác nhận trình duyệt bằng modal phù hợp giao diện PES Arena; `window.alert` chuyển thành toast.
- Tách rõ Core / CSS / JS và bổ sung `docs/MODULE_AUDIT_V1.3.31.md` báo cáo phần còn chồng chéo.
- Cập nhật `APP_VERSION` thành `1.3.31`.

### File chính đã sửa
- `app.py`
- `modules/admin_dashboard_routes.py`
- `modules/admin_system_routes.py`
- `templates/admin.html`
- `templates/base.html`
- `static/js/admin_dashboard.js`
- `static/js/ui_dialog.js`
- `static/js/luckybox_user.js`
- `static/css/admin_dashboard.css`
- `static/css/ui_dialog.css`
- `docs/MODULE_AUDIT_V1.3.31.md`


## V1.3.30 — Cân nút phòng, lịch sử luôn hiển thị, sắp xếp chế độ và sửa phản hồi tab báo cáo

- Thu nhỏ và căn giữa cụm `Mời đấu / Tìm nhanh / Thoát phòng`.
- Giảm độ đậm viền, giảm nền đặc và tăng độ trong suốt riêng cho ba nút chờ đối thủ.
- Lịch sử phòng luôn hiển thị, kể cả khi chưa có khách hoặc chưa có trận; khi trống sẽ hiện thông báo rõ ràng.
- Sắp xếp chế độ từ trái sang phải: `Random → 3 chọn 1 → Lượt đi/về → BO3 → Chiến thuật BO3 → Cấm chọn BO3`.
- Thêm phản hồi tab Admin ngay từ `pointerdown` để thao tác chuyển tab có cảm giác tức thời hơn.
- Thêm trạng thái đang tải khi chọn khoảng thời gian trong Báo cáo số trận, tránh cảm giác nút không nhận lệnh.
- Cập nhật `APP_VERSION` thành `1.3.30`.

### File đã sửa
- `app.py`
- `modules/rank_modes/catalog.py`
- `templates/partials/room_history_panel.html`
- `static/css/arena_room_v2.css`
- `static/css/admin_dashboard.css`
- `static/js/admin_dashboard.js`


## V1.3.29 — Tối ưu độ trễ click và giảm request nền

- Loại bỏ việc gọi heartbeat và kiểm tra lời mời ngay trên mỗi `pointerdown`, `touchstart`, `keydown`; đây là nguyên nhân khiến một cú click đồng thời kích hoạt nhiều request nền.
- Giãn polling lời mời từ 2,2 giây lên 5 giây khi hoạt động và 15 giây khi không thao tác; tab ẩn không tiếp tục polling liên tục.
- Giảm watchdog lời mời từ mỗi 5 giây xuống mỗi 30 giây và chỉ chạy khi tab đang hiển thị.
- Không gọi lại API thông báo hệ thống mỗi lần cửa sổ được focus.
- Tăng cache người dùng và chuông thông báo từ 8 giây lên 30 giây để giảm truy vấn Supabase lặp khi chuyển tab.
- Giảm cập nhật trạng thái online từ tối đa 1 lần/45 giây xuống 1 lần/90 giây.
- Giãn polling phòng đấu ở các trạng thái thường, đồng thời tránh refresh lại phòng quá sớm ngay sau khi vừa submit thao tác.
- Tắt `backdrop-filter` trong giao diện phòng và giảm transition/box-shadow động để hạn chế GPU repaint.
- Không thay đổi logic trận đấu, RP, lời mời hoặc lịch sử phòng.
- Cập nhật `APP_VERSION` thành `1.3.29`.

### File đã sửa
- `app.py`
- `modules/notification_service.py`
- `templates/base.html`
- `templates/room_detail.html`
- `static/css/arena_room_v2.css`


## V1.3.28 — Tinh gọn luồng phòng đấu và làm nhẹ viền nút

- Gỡ khu chọn chế độ lặp ở cột giữa; chỉ giữ **1 nơi chọn chế độ chính** là hàng 6 chế độ bên dưới, giảm thao tác rườm rà.
- Giữ **Lịch sử đấu trong phòng** ở cột phải bên dưới khối Parsec.
- Đơn giản hóa trạng thái giữa sân:
  - Chưa có khách: hiển thị chờ đối thủ.
  - Có khách nhưng chưa sẵn sàng: hiển thị chờ đối thủ sẵn sàng.
  - Đã sẵn sàng: mới hiện đồng hồ chờ chủ phòng quay quân.
- Trước khi quay quân / bắt đầu trận, cả chủ phòng và khách đều có thể **thoát an toàn** bằng `room_leave`, không còn bị coi là bỏ cuộc ở trạng thái `waiting_ready`.
- Bỏ dòng **Loại trận** bị trùng thông tin với **Chế độ** trong cột thông tin phòng đấu.
- Ở trạng thái sau trận `confirmed`, đổi nút `Thoát Phòng` thành **Về sảnh** để đúng ngữ cảnh hơn.
- Ẩn nút `Sẵn sàng` giả khi phòng chưa có đối thủ; nếu tắt Tìm nhanh thì chỉ còn các thao tác thực sự cần thiết.
- Làm viền nút nhẹ hơn: giảm độ đậm viền, giảm glow và làm cụm nút nhìn mềm hơn so với bản trước.
- Thu nhỏ độ nổi của nút `Đưa khỏi phòng` để nó bớt lấn át các thao tác chính.
- Cập nhật `APP_VERSION` thành `1.3.28`.

### File đã sửa
- `app.py`
- `static/css/arena_room_v2.css`
- `templates/room_detail.html`
- `templates/_room_live_content.html`


## V1.3.26 — Tinh chỉnh nút và trạng thái theo style mềm hơn

- Tinh chỉnh lại bộ nút hành động trong phòng để bớt cảm giác thô: viền sáng rõ hơn, nền có chiều sâu hơn, bo góc mềm hơn và màu gần với mẫu vàng / xanh / đỏ bạn chọn.
- Bỏ khung nền dày bao quanh cụm nút giữa sân; chỉ giữ bố cục nổi trực tiếp trên giao diện để nhìn gọn và sang hơn.
- Tăng chất lượng hiển thị cho các nút `Mời đấu`, `Sẵn sàng`, `Thoát phòng`, `Đưa khỏi phòng`, `Gửi kết quả`, `Xác nhận`, `Không đồng ý`.
- Làm lại khối `Phòng đã sẵn sàng` + `2 / 2` theo kiểu pill tối, gọn và nổi bật hơn.
- Tinh chỉnh khối `Đợi quay random đội` / `Đợi khách sẵn sàng` để đồng bộ phong cách với cụm nút mới.
- Không thay đổi logic phòng đấu; chỉ tinh chỉnh giao diện và cập nhật `APP_VERSION` thành `1.3.26`.

### File đã sửa
- `app.py`
- `static/css/arena_room_v2.css`


## V1.3.25 — Tinh chỉnh nút phòng đấu và đưa lịch sử sang cột phải

- Làm lại cụm nút hành động ở giữa phòng theo phong cách gọn hơn: nền kính tối ấm hơn, viền neon rõ, kích thước nút hợp giao diện và không còn cảm giác thô/chiếm chỗ.
- Cân lại chiều rộng cụm nút theo số lượng nút thực tế (1 / 2 / 3 nút) để chủ phòng và đối thủ hiển thị cân đối hơn.
- Đưa khối **Lịch sử đấu** sang cột phải, nằm bên dưới **Kết nối Parsec** để không còn chèn lên hàng 6 chế độ.
- Tạo khung `room-bottom-shell` để hàng **6 chế độ** chỉ chiếm đúng phần ngang từ cột chủ phòng đến cột đối thủ; ô chế độ số 6 không còn đè vào lịch sử đấu.
- Thu gọn kích thước thẻ 6 chế độ để vừa khung mới nhưng vẫn giữ icon, tên chế độ và trạng thái mở khóa rõ ràng.
- Đồng bộ bố cục này cho cả `room_detail.html` và `_room_live_content.html` để polling realtime không làm lệch layout.
- Tách khối lịch sử đấu thành partial riêng `templates/partials/room_history_panel.html` để dùng chung và dễ bảo trì.
- Cập nhật `APP_VERSION` thành `1.3.25`.

### File đã sửa
- `app.py`
- `static/css/arena_room_v2.css`
- `templates/room_detail.html`
- `templates/_room_live_content.html`
- `templates/partials/room_history_panel.html`


## V1.3.24 — Nút kính tối viền neon, đồng bộ hai phía và ổn định lịch sử phòng

- Thay hai lớp CSS nút V1.3.21/V1.3.23 bị ghi đè lẫn nhau bằng một lớp duy nhất, giới hạn trong `.arena-room-v2 .arena-btn`; khu Parsec không bị ảnh hưởng.
- Chuyển nút hành động sang nền kính tối, viền neon theo trạng thái, chữ trắng rõ như mẫu; cân bằng kích thước cặp `Xác Nhận / Không Đồng Ý`.
- Đồng bộ chiều cao và bố cục nút của chủ phòng, đối thủ, nút gửi kết quả, sẵn sàng và thoát phòng.
- Đồng bộ fragment cập nhật realtime `_room_live_content.html` với giao diện ban đầu: giữ đủ 6 chế độ sau polling, không quay về giao diện 2 chế độ cũ.
- Lịch sử đấu luôn hiện khi phòng đã đủ 2 người; khi chưa có trận hiển thị trạng thái trống thay vì biến mất.
- Cập nhật `APP_VERSION` thành `1.3.24`.

### File đã sửa
- `app.py`
- `static/css/arena_room_v2.css`
- `templates/room_detail.html`
- `templates/_room_live_content.html`


## V1.3.23 — Làm sáng và đồng bộ nút phòng đấu
- Kiểm tra xung đột giữa `static/style.css` và `static/css/arena_room_v2.css`.
- Tăng độ sáng nền cho 4 nhóm nút: gold, success, secondary và danger.
- Ép chữ nút màu trắng, tăng độ đậm và thêm text-shadow nhẹ.
- Giảm mức làm tối của nút disabled để nội dung vẫn đọc được.
- Loại bỏ lớp nền phụ bên trong nút Quay quân để tránh nút hai lớp.
- Không thay đổi nút thuộc khu Parsec.
- Không thay đổi API, route hoặc logic phòng đấu.
# PES Arena V1.3.21 — Unified Room Buttons

- Đồng bộ nút phòng đấu theo một hệ thiết kế bo góc navy/neon.
- 4 biến thể: gold, success, secondary, danger.
- Áp dụng cho Mời đấu, Tìm nhanh, Sẵn sàng, Hủy sẵn sàng, Thoát phòng, Gửi kết quả, xác nhận, từ chối, Quay quân, đá tiếp và điều khiển phòng.
- Không áp dụng cho nút trong khu vực Parsec.
- Giữ nguyên route, API, JavaScript và logic phòng đấu.

## V1.3.18 - 2026-08-07

- Dùng `room-texture-dark.webp` làm nền toàn bộ khu phòng đấu.
- Bỏ nền mờ/đục ở card chế độ; thay bằng viền Neon tím, xanh và gold.
- Tăng kích thước emblem chế độ trung tâm và icon của 6 chế độ.
- Chuyển URL Supabase mặc định sang `pes-assets/room-assets/v1.3.18`.
- Không thay đổi API, polling hoặc luồng phòng đấu.

## V1.3.17 - 2026-08-07

- Bỏ hoàn toàn `light-effect-blue.webp` và `light-effect-red.webp` khỏi CSS, template, asset local và gói upload Supabase.
- Card Chủ phòng/Đối thủ chỉ dùng trực tiếp `stadium-blue.webp` và `stadium-red.webp`, không còn request 404 hoặc lớp đèn chồng ảnh.
- Cắt vùng trong suốt dư của `pes-arena-room-logo.webp` và tăng kích thước hiển thị cân đối trên thanh tiêu đề phòng đấu.
- Chuyển đường dẫn Supabase mặc định sang `pes-assets/room-assets/v1.3.17` để tránh cache ảnh cũ.

## V1.3.16 - 2026-08-07
- Bỏ đường kẻ ngang legacy trong card Chủ phòng/Đối thủ (`border-bottom` của `.room-player-heading-plain`).
- Thay nền khu VS bằng WebP sân ngang mới và giảm lớp phủ tối để ảnh hiện rõ.
- Thay texture nền khu chế độ bằng WebP người dùng cung cấp.
- Đổi đường dẫn Supabase sang `pes-assets/room-assets/v1.3.16` để tránh cache bản cũ.
- Không đổi API, route, polling hoặc luồng sẵn sàng/thoát phòng.

# PES Arena V1.3.14

- Thay thanh “CHỌN 1 TRONG 3” bằng chữ HTML và CSS thuần.
- Cấu trúc: đường kẻ vàng, hình thoi, tiêu đề, hình thoi, đường kẻ vàng.
- Chỉ hiển thị trong chế độ `random3_pick1`.
- Áp dụng đồng bộ cho Host/Opponent và các template cập nhật động.
- CSS được giới hạn trong namespace `.arena-room-v2`.
- Không thay đổi API, JavaScript, polling hoặc logic phòng đấu.
- Không cần SQL và không cần upload thêm ảnh Supabase.

# PES Arena V1.3.6 — Room UI Asset Pack

- Ngày: 2026-08-06 22:45 (Asia/Bangkok)
- Dựa trên: V1.3.5 Arena Room V2 UI MASTER.
- Tạo đủ asset WebP: logo phòng đấu, nền sân xanh/đỏ, light effect xanh/đỏ, VS emblem, Parsec, chia sẻ phòng, 6 icon chế độ.
- Viết lại CSS phòng đấu dưới namespace `.arena-room-v2`: layout, card, nút, typography, grid, spacing, badge, Tổng điểm và hệ thống khung neon.
- Giữ nguyên API, form, polling, sidebar, header và các module ngoài phòng đấu.
- Asset có thể dùng local ngay; chuẩn bị sẵn cấu trúc để tải lên Supabase Storage.

# PES Arena V1.3.5 — Arena Room V2

- Ngày: 2026-08-06 (Asia/Bangkok)
- Dựng lại riêng khu vực phòng đấu theo UI MASTER, không tiếp tục vá layout cũ.
- Root namespace mới: `.arena-room-v2`.
- Viết lại bố cục chính bằng CSS Grid 4 cột: 31% / 24% / 31% / 14%.
- Giữ nguyên Sidebar, Header chung, API, form action, dữ liệu Jinja và JavaScript phòng đấu hiện có.
- Ba nút hành động được trình bày ngang trong khu trung tâm ở trạng thái chờ đối thủ.
- Sáu card chế độ nằm cùng một hàng desktop; giữ đúng tên “Cấm chọn CLB”.
- Thay emoji chế độ chính bằng 6 SVG riêng trong `static/icons/rank_modes/`.
- Không dùng OVR, inline style, selector chung hoặc `!important`.
- File CSS mới: `static/css/arena_room_v2.css`.
- Không có SQL mới. SQL mới nhất vẫn nằm tại `project_docs/sql/PES_ARENA_UPDATE_LATEST.sql`.

## File sửa

- `app.py`
- `templates/room_detail.html`
- `static/css/arena_room_v2.css`
- `static/icons/rank_modes/*.svg`
- `test_arena_room_v2_v135.py`

---

# PES Arena V1.3.4 — Fix UI MASTER 100%

- Sửa `room-arena-frame` còn kế thừa `min-height: 720px` từ CSS cũ.
- Khung thi đấu desktop còn 405px và dải 6 chế độ luôn nằm ngay phía dưới ở zoom 100%.
- Thu gọn topbar riêng trang `room_detail`, không ảnh hưởng trang khác.
- Không dùng CSS zoom/transform scale, không thêm polling hoặc JavaScript.
- CSS mới chỉ nằm trong `body[data-page="room_detail"]` và `.room-layout-v137`.
- Không cần chạy SQL mới.

## V1.3.1 — 06/08/2026 21:47 (GMT+7)
- Thêm tab `Quản lý chế độ Rank` trong Dashboard Admin cho đủ 6 chế độ.
- Cho phép lưu bật/tắt, RP mở khóa, số trận tối thiểu, chênh RP tối đa và bảng RP Series vào `system_settings`.
- Bổ sung cấu hình Pool CLB, lượt cấm, thời gian cấm và thời gian chọn cho Cấm chọn CLB BO3.
- Mở rộng báo cáo đủ 6 chế độ: trận, Series, hoàn thành, 2-0, 2-1, hòa, bỏ cuộc, tranh chấp, RP cộng/trừ, RP trung bình, lội ngược dòng và số người đã mở khóa.
- Tương thích dữ liệu trận cũ; nếu bảng Series chưa được tạo, trang Admin vẫn hoạt động và hiển thị số liệu Series bằng 0.
- File sửa: `app.py`, `modules/rank_modes/service.py`, `modules/admin_dashboard_routes.py`, `templates/admin.html`, `static/css/admin_dashboard.css`, `Log.md`.

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

## V1.3.0 — 06/08/2026 21:37 (GMT+7)

### Nội dung
- Thêm lõi cấu hình chung cho 6 chế độ Rank: Rank thường Random, Random 3 chọn 1, Đấu chiến thuật BO3, BO3, Cấm chọn CLB BO3, Lượt đi – lượt về.
- Chuẩn hóa điều kiện mở khóa: RP tối thiểu, số trận Rank, chênh lệch RP.
- Chuẩn hóa bảng RP Series 2–0, 2–1, hòa và bỏ cuộc; RP chỉ trả về để áp dụng một lần khi Series kết thúc.
- Thêm hàm xác định kết quả BO3 và tổng tỷ số hai lượt; không áp dụng bàn thắng sân khách.
- Thêm giao diện chọn 6 chế độ dạng lưới gọn, có khóa và lý do khóa.
- Thêm SQL nền cho Series, trận con và lịch sử cấm/chọn CLB.
- Giữ nguyên luồng đang hoạt động của Rank thường và Random 3 chọn 1.
- Bốn chế độ Series được khóa nút bắt đầu cho đến khi chạy SQL và nối hoàn chỉnh luồng trận con, tránh tạo nhầm trận Rank thường.

### File chính
- `modules/rank_modes/catalog.py`
- `modules/rank_modes/service.py`
- `modules/rank_modes/__init__.py`
- `modules/room_team_routes.py`
- `modules/room_access_routes.py`
- `templates/room_detail.html`
- `static/style.css`
- `docs/update_rank_modes_core_v1_3_0.sql`
- `test_rank_modes_core_v130.py`

## V1.3.2 - UI MASTER phòng đấu + sắp xếp SQL
- Áp dụng bố cục phòng đấu theo ảnh UI MASTER đã chốt.
- Thêm PES ARENA nhỏ gọn ở giữa thanh đầu.
- Giữ khu chủ phòng xanh, đối thủ đỏ, chế độ đang chọn tím, trạng thái hợp lệ xanh lá.
- Thêm thẻ thông tin chế độ ở giữa và 6 thẻ chế độ nhỏ phía dưới.
- Chỉ hiển thị Tổng điểm, không dùng OVR.
- Giữ nguyên API chọn chế độ `room_select_ranked_mode` và cơ chế AJAX hiện có.
- CSS mới giới hạn trong `.room-layout-v137`, không dùng selector toàn cục.
- Gom toàn bộ SQL cũ vào `project_docs/sql/`; chỉ để `project_docs/sql/PES_ARENA_UPDATE_LATEST.sql` ở ngoài.


## V1.3.3 - Sửa mở khóa chế độ + hiển thị desktop 100%
- Sửa nguồn RP mở khóa: ưu tiên `rank_points`, giữ fallback `rating`/`rp`.
- Sửa số trận Rank: ưu tiên tổng `wins + draws + losses`, tránh `total_matches` cũ khóa sai.
- Sửa kiểm tra chênh RP của đối thủ dùng đúng `rank_points`.
- Loại bỏ khối CSS UI MASTER bị lặp hai lần.
- Thêm breakpoint theo chiều cao màn hình để desktop zoom 100% nhìn được khu thi đấu và 6 chế độ.
- Không thay đổi API, polling, luồng tạo phòng/mời đấu/sẵn sàng/thoát phòng.

## V1.3.7 - 2026-08-06 23:08 (Asia/Bangkok)

### Nội dung
- Ghép bộ logo WebP do người dùng cung cấp vào UI phòng đấu V2.
- Thay logo PES ARENA ở thanh tiêu đề.
- Thay VS emblem.
- Thay icon đủ 6 chế độ Rank.
- Tách icon card và emblem lớn ở card chế độ trung tâm để đúng tỷ lệ từng logo.
- Giữ nguyên nút hành động bằng CSS vì nội dung và trạng thái nút là dữ liệu động.
- Giữ toàn bộ file WebP gốc trong `static/assets/room_v2/source_user_logo/`.

### File sửa
- `app.py`
- `templates/room_detail.html`
- `static/css/arena_room_v2.css`
- `static/assets/room_v2/pes-arena-room-logo.webp`
- `static/assets/room_v2/vs-gold-emblem.webp`
- `static/assets/room_v2/modes/*.webp`
- `static/assets/room_v2/emblems/*.webp`
- `static/assets/room_v2/USER_LOGO_MAPPING.txt`

### So với V1.3.6
- V1.3.6 dùng bộ asset minh họa tự tạo.
- V1.3.7 dùng đúng bộ logo WebP người dùng đã chuẩn bị và căn chỉnh riêng theo từng vị trí UI.


## V1.3.8 — Room UI CSS/Neon cleanup
- Fixed overlapping center action controls by using one 3-column grid.
- Consolidated logo sizing into one CSS flow.
- Standardized neon hierarchy.
- Removed unused room_master.css, legacy SVG mode icons, source logo dump, stale UI tests and caches.
- Added exact Supabase upload manifest and audit report.

## V1.3.10 — Supabase Room Asset Upload Pack

- Thêm thư mục `UPLOAD_SUPABASE/UPLOAD_VAO_BUCKET_public-assets/room-assets/v1.3.10/` chứa đúng 20 file WebP cần upload.
- Thêm manifest CSV ghi rõ bucket, object path, URL public mẫu, dung lượng và SHA-256.
- Thêm biến `ROOM_ASSET_BASE_URL` và helper `room_asset()`; khi chưa cấu hình, hệ thống tự dùng asset local.
- Không thay đổi API hoặc logic phòng đấu.

## V1.3.10 — Fix tên chế độ và nút Neon
- Đổi tên thẻ chế độ desktop: Random, 3 chọn 1, Chiến thuật BO3, BO3, Cấm chọn BO3, Lượt đi/về.
- Tách class vai trò cho Mời đấu, Tìm nhanh/Sẵn sàng và Thoát phòng.
- Sửa xung đột với rule `.btn` toàn cục có `!important` trong `static/style.css`.
- Ba nút dùng Grid 3 cột, không chồng, không chung nền.
- Không đổi route/API hoặc logic sẵn sàng, tìm nhanh, thoát phòng.

## V1.3.11 - Ghép trực tiếp Supabase pes-assets
- Chuyển gói upload sang bucket thật `pes-assets`.
- Folder đích: `room-assets/v1.3.11`.
- Ghép sẵn public URL `https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/room-assets/v1.3.11` vào helper asset phòng đấu.
- Không bắt buộc cấu hình biến Vercel; `ROOM_ASSET_BASE_URL` vẫn có thể dùng để ghi đè.
- Làm lại `UPLOAD_SUPABASE` và manifest chi tiết đúng bucket của dự án.


## V1.3.12 - Chuẩn hóa tỷ lệ UI MASTER phòng đấu
- Chỉnh Grid desktop theo tỷ lệ 31% / 24% / 31% / 14%, gap 12px.
- Dựng lại tỷ lệ card Host/Opponent, nền sân, light effect, avatar, rank, vùng CLB và Tổng điểm.
- Tăng tỷ lệ card chế độ trung tâm, emblem và VS; căn lại hàng 3 nút Neon.
- Tăng chiều cao 6 card chế độ, thu gọn sidebar Info/Parsec và chuẩn hóa typography/neon.
- Không đổi API, route, polling hoặc logic phòng đấu. Không có SQL mới.


## V1.3.19 - Fix state action dock
- Giữ hiển thị Sẵn sàng, Hủy sẵn sàng, Thoát phòng và các nút theo trạng thái ở đáy khu trung tâm.
- Giữ bảng nhập tỷ số và nút Gửi kết quả trong vùng nhìn thấy khi trận đang Playing.
- Không thay route, API, RP hoặc logic trạng thái phòng.

## V1.3.20 — 2026-08-07
- Sửa nút Quay quân của chế độ 3 chọn 1 bị nền/viền hồng tím do rule legacy `.room-center-random-trigger.random3-trigger` trong `static/style.css`.
- Thêm override giới hạn trong `.arena-room-v2`: bỏ toàn bộ nền tím, viền tím và glow tím của wrapper.
- Giữ riêng nút QUAY QUÂN màu vàng gold, subtitle nằm bên dưới nền trong suốt.
- Không sửa route, API, trạng thái phòng hoặc luồng random 3 CLB.

## V1.3.38 - 2026-08-07 13:55 (Asia/Bangkok)

### Nội dung
- Dọn `arena_room_v2.css` 1.500+ dòng thành 7 module CSS Room có trách nhiệm rõ ràng.
- Giữ nguyên thứ tự cascade cũ để tránh thay đổi giao diện ngoài ý muốn.
- `arena_room_v2.css` trở thành compatibility index; code mới không thêm rule trực tiếp vào đây.
- Nâng `scripts/audit_css_flow.py` để quét CSS đệ quy, thống kê selector trùng trong từng module, xung đột giữa module, `!important` và rule có khả năng ẩn UI.
- Thêm tài liệu `docs/MODULE_STRUCTURE_V1.3.38.md` quy định luồng kiểm lỗi Frontend -> Backend -> Data -> DOM -> CSS và quyền sở hữu từng module.
- Thêm test bảo vệ thứ tự CSS Room, scope `.arena-room-v2` và cân bằng block CSS.
- Không thay route/API, Presence, Invite, Quick Match, RP, Rank unlock hoặc schema Supabase.

### File chính
- `app.py`
- `templates/room_detail.html`
- `static/css/arena_room_v2.css`
- `static/css/room/01-shell-layout.css`
- `static/css/room/02-club-visuals.css`
- `static/css/room/03-mode-selector.css`
- `static/css/room/04-actions-history.css`
- `static/css/room/05-action-states.css`
- `static/css/room/06-responsive-performance.css`
- `static/css/room/07-parsec-history-polish.css`
- `scripts/audit_css_flow.py`
- `docs/MODULE_STRUCTURE_V1.3.38.md`
- `docs/CSS_MODULE_AUDIT_V1.3.38.txt`
- `test_module_css_structure_v138.py`

### So với V1.3.37
- V1.3.37 phát hiện CSS Room chồng chéo nhưng vẫn dùng một file lớn.
- V1.3.38 tách vật lý CSS Room thành các module có thứ tự tải rõ ràng và có test/audit bảo vệ ranh giới module.

### Kiểm thử V1.3.38
- So sánh CSS Room trước/sau khi tách: 69.797 ký tự rule, byte-equivalent sau khi chuẩn hóa relative asset URL: PASS.
- 7/7 module cân bằng ngoặc và toàn bộ selector được scope `.arena-room-v2`: PASS.
- Nhóm Room/Presence/Invite/Quick Match/Rank Mode: 22/22 PASS.
- Full pytest không chạy hết do source đầu vào thiếu 2 SQL Lucky Box lịch sử; không phải regression của V1.3.38.


## V1.3.39 - 2026-08-07 16:24 (Asia/Bangkok)

- Thay toàn bộ 6 logo chế độ Rank bằng bộ `1.webp` -> `6.webp` người dùng cung cấp.
- Map theo ý nghĩa biểu tượng: 1 Tactical BO3, 2 Ban Pick BO3, 3 Rank Random, 4 Random 3 chọn 1, 5 Lượt đi/về, 6 BO3.
- Đồng bộ logo ở cả thẻ chọn chế độ (`modes/`) và logo chế độ đang chọn (`emblems/`).
- Chuẩn hóa viewport logo bằng `object-fit: contain`; ảnh nguồn to/nhỏ hoặc khác tỉ lệ vẫn hiển thị cùng kích thước.
- Xóa các rule CSS riêng từng mode từng làm Random 3 chọn 1 / Lượt đi-về có kích thước khác.
- Thêm `?v=1.3.39` cho URL mode/emblem để phá cache ảnh cũ trên trình duyệt/CDN.
- Tạo `UPLOAD_SUPABASE_MODE_LOGOS_V1.3.39/` và manifest SHA-256 cho đúng 12 object cần overwrite trong bucket `pes-assets`.


## V1.3.40 - 2026-08-07 17:16 (Asia/Bangkok)

- Tách 6 logo chế độ Rank sang đường dẫn Supabase riêng `pes-assets/room-assets/v1.3.40/modes/`.
- Web đọc trực tiếp file `1.webp` -> `6.webp`; người dùng không cần đổi tên ảnh sang mã mode.
- Map: 1 Tactical BO3, 2 Ban Pick BO3, 3 Rank Random, 4 Random 3 chọn 1, 5 Lượt đi/về, 6 BO3.
- Cả logo thẻ chọn mode và logo mode đang chọn dùng chung helper `mode_asset()`, bỏ nhu cầu upload trùng vào `emblems/`.
- Giữ toàn bộ asset phòng khác ở `room-assets/v1.3.18` để không phải upload lại nền/VS/Parsec.
- Thêm sẵn cây thư mục rỗng `pes-assets/room-assets/v1.3.40/modes/` trong gói release để người dùng tự đặt 6 WebP rồi upload Supabase.


## V1.3.41 - 2026-08-07 17:19 (Asia/Bangkok)

- Dọn ảnh thừa sau khi chuyển 6 logo mode sang Supabase `room-assets/v1.3.40/modes/1.webp` -> `6.webp`.
- Xóa 12 logo cũ trùng lặp trong `static/assets/room_v2/modes/` và `static/assets/room_v2/emblems/`.
- Xóa 12 logo mode/emblem cũ trong gói `UPLOAD_SUPABASE` v1.3.18; các asset Room nền/VS/Parsec còn dùng vẫn được giữ nguyên.
- Xóa `trophy_gold.svg`, `trophy_silver.svg`, `trophy_bronze.svg` vì không có HTML/CSS/JS/Python nào tham chiếu.
- Giữ nguyên cây `pes-assets/room-assets/v1.3.40/modes/` để người dùng tự đặt `1.webp` -> `6.webp` và upload Supabase.
- Không thay logic Backend, API, RP, Rank Mode, Presence hoặc Invite.


## V1.3.44 - 2026-08-07 17:48 (Asia/Bangkok)
- Chỉ sửa CSS hiển thị logo chế độ.
- Sửa lỗi cascade: 04-actions-history.css trước đây load sau và ghi đè kích thước logo từ 03-mode-selector.css về 50x50px.
- Phóng phần artwork thực của 1.webp -> 6.webp khoảng 3 lần bằng transform + khung crop, không thay Backend/mapping/Supabase.
- Nới cột icon vừa đủ để logo lớn nhưng không đè tên chế độ/trạng thái mở khóa.


## V1.3.45 - Series Forfeit +20/-20
- 4 mode Series (Lượt đi/về, BO3, Chiến thuật BO3, Cấm chọn BO3): bên bỏ cuộc luôn -20 RP, bên còn lại +20 RP.
- Áp dụng không phụ thuộc tỷ số/trận con đã diễn ra trước đó.
- Đồng bộ cho bỏ cuộc thủ công, host offline giữa trận và timeout bị tính bỏ trận.
- Lịch sử matches lưu đồng thời delta người bỏ cuộc và người được xử thắng.
- Rank Random và Random 3 chọn 1 giữ nguyên luật hiện tại.


## V1.3.46 - 2026-08-07 19:09 (Asia/Bangkok)
- Bổ sung quota theo số trận PES thực tế cho từng Rank mode.
- Rank Random / Random 3 chọn 1 cần còn tối thiểu 1 lượt.
- Lượt đi - lượt về cần còn tối thiểu 2 lượt trước khi bắt đầu.
- BO3 / Chiến thuật BO3 / Cấm chọn BO3 cần còn tối thiểu 3 lượt trước khi bắt đầu.
- Nếu đã chơi 9/10: chỉ được vào mode trận đơn; Series bị khóa.
- Nếu đã chơi 8/10: được Lượt đi/về, không được các BO3.
- Nếu đã chơi 7/10: đủ điều kiện quota cho toàn bộ Series.
- Khi Series đã bắt đầu và phòng đang giữ nguyên mode, RP/min-match không bị kiểm tra lại giữa chuỗi. Mỗi trận con tiếp theo chỉ cần còn 1 lượt thực tế.
- BO3 kết thúc 2-0 chỉ phát sinh 2 match thực tế nên chỉ tốn 2 lượt; nếu cần trận 3 mới tốn lượt thứ 3.
- Catalog chọn mode hiển thị lý do khóa khi một trong hai người không đủ lượt ngày.
- Test mới V1.3.46: 6/6 PASS. Nhóm Rank mode lõi bổ sung: 17 PASS; 2 test legacy Admin toggle cũ không còn khớp kiến trúc partial hiện tại, không liên quan thay đổi này.

## V1.3.51 — 2026-08-08
- Ban/Pick BO3: hết giờ cấm tự random 1 CLB để cấm; hết giờ chọn tự random 1 CLB hợp lệ.
- Thêm deadline từng lượt + countdown UI + watchdog qua room polling 3 giây chỉ khi Ban/Pick đang chờ thao tác.
- Thêm optimistic guard theo `match_series.updated_at` để giảm xử lý timeout trùng.
- Tactical BO3: không tái sử dụng bất kỳ CLB nào đã xuất hiện trong 3 lựa chọn trước đó của Series.
- Admin Ban/Pick: ép pool tối thiểu = 2 x số lượt cấm mỗi bên + 6; thời gian cấm/chọn tối thiểu 5 giây.
- Admin permission: sửa Rank modes yêu cầu `system_features_manage`; sửa unlock mode người dùng yêu cầu `users_edit`.
- Thêm `docs/SYSTEM_INSPECTION_V1.3.51.md` và test audit V1.3.51.


## V1.3.55 - Black Box Startup Crash Guard (2026-08-08)
- Hotfix sau lỗi Vercel `FUNCTION_INVOCATION_FAILED` ở V1.3.54.
- Black Box config trong context processor chuyển sang `_safe_blackbox_runtime_config()`; mọi exception => Black Box OFF, trang chính vẫn render.
- Numeric env BLACKBOX_* parse an toàn; giá trị sai không còn làm Flask ném ValueError.
- `modules.blackbox.__init__` không import Safety Lab lúc startup.
- Safety Lab import lỗi => chỉ Safety Lab NOT_TESTED, không làm app crash.
- Không sửa module gameplay/RP/Room/Invite/Presence.

## V1.3.67 — Room Rank Mode Binding Hotfix
- Chế độ: FIX NHANH.
- Lỗi: `POST /rooms/create` trả 500 do `modules/core/room_runtime.py` không có `normalize_rank_mode_code`.
- Nguyên nhân: Core modules được configure trước khi `modules.rank_modes` export helper; sau khi service modules nạp xong không refresh Room Runtime.
- Sửa: gọi lại `_core_room_runtime.configure(globals())` ngay sau khi service exports hoàn tất.
- Phạm vi: chỉ dependency binding cho Room Runtime; không đổi logic RP, gameplay, Supabase hay CSS.
- Kiểm tra: compile + smoke test dependency Rank Mode/Room.


## Room UI Fidelity + Exit Penalty Frontend Hotfix — 2026-08-08
- Không sửa backend Python / database / route logic.
- Sửa template để nút Thoát ở trạng thái khách đã Sẵn Sàng gọi đúng route bỏ cuộc hiện có (`room_host_forfeit` / `room_guest_forfeit`) thay vì gọi `room_leave` rồi bị backend từ chối.
- Modal cảnh báo hiển thị rõ `−20 RP` trước khi xác nhận bỏ cuộc.
- Khi chưa Sẵn Sàng vẫn dùng `room_leave` và hiển thị `KHÔNG TRỪ RP`.
- Đồng bộ logic trên cả template lần đầu và `_room_live_content.html` dùng cho polling.
- Sửa số thứ tự 6 chế độ: 1 Rank Random, 2 Random 3 chọn 1, 3 Đấu chiến thuật BO3, 4 BO3, 5 Cấm chọn CLB, 6 Lượt đi–lượt về.
- Tăng độ giống mockup: PES ARENA lớn hơn, logo chế độ trung tâm đúng kích thước, cân lại 4 cột, VS lớn hơn, panel phải cân đối hơn, Tổng điểm ép màu trắng.

## 2026-08-08 — Room UI mockup layout lock (frontend-only)
- Phạm vi: Room frontend, không thay route/service/RP/backend.
- Sửa cấu trúc `room_detail.html`: main battle grid chỉ chứa Host → Center → Guest → Side rail; mode/history chuyển ra dưới grid đúng bố cục mockup.
- `room/_bottom_modes_history.html`: giữ 6 mode cards luôn hiện để layout không nhảy giữa các trạng thái; khi trận/series đang chạy card chỉ xem, không gửi form đổi mode.
- Thêm `static/css/room/12-mockup-layout-lock.css` tải cuối để khóa tỷ lệ desktop, logo PES ARENA, VS, player cards, center mode, sidebar, action buttons và mode strip theo ảnh đã chốt.
- Giữ nguyên toàn bộ endpoint/form action hiện tại, gồm ready/start/result/confirm/rematch/forfeit/leave/Parsec.

## V1.3.91 - 2026-08-08 - Sua_loi_CSS_nut_bam_1_lop
- Nền sửa: quay lại trực tiếp từ `V1.3.89_Sua_bo_cuc_bat_dau_tran_gon_gang.zip`; không dùng thay đổi của V1.3.90 trước đó.
- Giữ nguyên backend, route, JS xử lý nút, RP và luồng phòng đấu.
- Sửa CSS tại đúng module cũ đang xung đột; không tạo CSS vá mới ở cuối chuỗi load.
- `BẮT ĐẦU TRẬN`: bỏ style ép vàng của `room-center-random-trigger`; Series dùng class semantic xanh lá, form bọc ngoài được reset ngay trong `10-prestart-flow.css`, chỉ còn một lớp nút.
- `BẮT ĐẦU TRẬN` và `Thoát Phòng`: cân lại cùng tỷ lệ form/chiều cao trong rule prestart hiện có.
- Thêm icon ▶ trực tiếp trong nội dung nút Series, không thay action/form submit.
- `Tìm nhanh`: loại cụm 3 nút khỏi rule action-dock nền/viền của trạng thái `waiting_ready`, nên không còn khung ngoài bọc thêm quanh Mời đấu / Tìm nhanh / Thoát phòng.
- Sửa rule cũ gây `overflow:hidden/text-overflow:ellipsis` để cụm 3 nút không cắt icon ⚡ và chữ `Tìm nhanh`.
- `gaming_neon_buttons.css`: random trigger không còn bị mặc định ép màu vàng; màu được quyết định bởi class semantic (`green` / `is-gold` / `random3-trigger`) để tránh cascade chồng màu.
- Đồng bộ template render đầu và template live polling.
- Kiểm tra: `python -m py_compile app.py` PASS; 23 test Room/CSS liên quan PASS. Test legacy `test_gaming_neon_buttons_v1377.py::test_version` không dùng vì kiểm tra cứng APP_VERSION 1.3.77.

## V1.3.92 - 2026-08-08 15:08 (Asia/Bangkok) - Sua_nut_bam_con_1_khoi_xanh
- Nền sửa: tiếp tục từ V1.3.91, chỉ xử lý đúng lỗi CSS nút trong Room UI.
- Giữ nguyên backend, route, JS, RP và toàn bộ luồng xử lý của các nút.
- `BẮT ĐẦU TRẬN`: Series không còn dùng class `room-center-random-trigger` vốn kéo theo nhiều lớp CSS random cũ. Nút chuyển sang đúng bộ class hành động xanh giống `Sẵn Sàng`; icon ▶ và chữ nằm trực tiếp trong một button duy nhất.
- Form `room-center-random-form` vẫn giữ action/submit cũ nhưng chỉ là wrapper không nền/không viền/không shadow theo rule sẵn có trong `10-prestart-flow.css`.
- `Tìm nhanh`: bỏ class legacy `room-quick-match-btn` khỏi template vì class này còn bị rule cũ trong `11-index-layout-reconnect.css` ép nền xanh dương riêng.
- Xóa rule `.room-quick-match-btn` ép nền xanh dương trong `11-index-layout-reconnect.css`.
- Xóa block room-specific `.gaming-quick-action` trong `gaming_neon_buttons.css` vì nó tạo thêm một lớp skin riêng; `Tìm nhanh` giờ đi cùng semantic `.green` như `Sẵn Sàng` nhưng vẫn giữ `gaming-quick-action` để role màu Admin còn hoạt động.
- Không thêm file CSS mới, không chèn override vá ở cuối chuỗi CSS.
- Đồng bộ `templates/room/_center_stage.html` và `templates/_room_live_content.html` để render đầu và live polling giống nhau.
- APP_VERSION: 1.3.92.
- Kiểm tra: app.py compile PASS; 23 test CSS/Room PASS; 14 test Quick Match/Room action PASS.

## V1.3.94 - Xoa_toan_bo_CSS_nut_bat_dau_tran_va_tim_nhanh (2026-08-08)
- Quét toàn bộ `static/css`, legacy CSS, Room CSS và Gaming Neon để xác định các rule có thể đè nút.
- `BẮT ĐẦU TRẬN`: bỏ toàn bộ class giao diện (`btn`, `arena-btn`, `green`, `room-center-action-btn`) và bỏ `series-primary-form` khỏi form Series để không còn CSS Series/Random bọc ngoài.
- `Tìm nhanh`: bỏ toàn bộ class giao diện khỏi button; chỉ giữ `data-quick-match-url` cho JavaScript.
- Hai nút chỉ còn inline reset `all: unset !important` + chữ + 1 border + padding cơ bản; background/shadow/filter/transform/text-shadow đều bị reset về không.
- Quick Match JS đổi hook icon/label từ class sang `data-quick-match-icon` / `data-quick-match-label`, không phụ thuộc CSS.
- Không thay endpoint, route, RP, trạng thái, polling hay luồng submit/click.


## V1.3.95 - Can_doi_nut_Tim_nhanh_va_tang_nen_Bat_dau_tran (2026-08-08)
- Bắt đầu từ V1.3.94.
- Không thêm CSS module mới, không sửa backend/route/JS/RP.
- Nút `BẮT ĐẦU TRẬN 1`: giữ tách khỏi CSS cũ, tăng nền xanh đậm rõ ràng; cao 52px để cân với `Thoát Phòng`.
- Nút `Tìm nhanh`: sửa kích thước flex trực tiếp, bỏ `width:100%` gây lệch trong hàng 3 nút; cao 48px, chữ/icon cân giữa.
- Cả hai nút vẫn dùng `data-*`/form action cũ nên luồng xử lý không thay đổi.


## V1.3.96 - Can_doi_3_nut_Moi_dau_Tim_nhanh_Thoat_phong_va_bo_icon_Bat_dau_tran (2026-08-08)
- Cân lại cụm 3 nút khi phòng chưa có đối thủ thành grid 3 cột bằng nhau: Mời đấu / ⚡ Tìm nhanh / Thoát phòng.
- Đồng bộ chiều cao 52px, khoảng cách 10px và chiều rộng mỗi nút bằng nhau trên desktop.
- Giữ nguyên màu và chức năng hiện tại của từng nút.
- Bỏ icon `▶` khỏi nút `BẮT ĐẦU TRẬN`, chỉ giữ chữ.
- Sửa trực tiếp rule CSS hiện có trong `01-shell-layout.css` và `06-responsive-performance.css`, không thêm file CSS vá mới.
- Đồng bộ template render ban đầu và template polling.

## V1.3.97 - Sua_cum_3_nut_can_deu_va_loai_bo_CSS_xung_dot (2026-08-08)
- Rà soát lại toàn bộ CSS của cụm 3 nút `Mời đấu / Tìm nhanh / Thoát phòng`.
- Nguyên nhân lỗi: `Tìm nhanh` dùng inline `all:unset + width:100%!important` trong khi hai nút còn lại dùng hệ `.arena-btn`; đồng thời layout cụm 3 nút bị khai báo lặp ở nhiều module 01/04/05/06/08/11/12, gây flex/grid tranh nhau kích thước.
- Bỏ toàn bộ inline style riêng của `Tìm nhanh`; chuyển về cùng hệ nút chuẩn `btn arena-btn green room-center-action-btn`.
- Cụm 3 nút chỉ còn một nơi sở hữu kích thước/layout trong `static/css/room/01-shell-layout.css`: grid 3 cột bằng nhau, cao 52px, cùng padding và gap.
- Loại các rule kích thước trùng của cụm 3 nút trong `04-actions-history.css`, `05-action-states.css`, `06-responsive-performance.css`.
- Loại block màu riêng V1.3.71 trong `08-action-layout-guard.css`; ba nút dùng chung hệ màu chuẩn gold/green/red.
- Gỡ class riêng `arena-action-invite`, `arena-action-exit`, `gaming-invite-action` khỏi cụm Room để tránh cascade từ nhiều file CSS khác.
- Giữ nguyên route/JS/Quick Match/modal/luồng xử lý.
- Test liên quan Room/Quick Match: 32 PASS. `app.py` compile PASS.


## V1.3.98 - Bo_icon_Tim_nhanh_giu_nguyen_kich_thuoc (2026-08-08)
- Giữ nguyên toàn bộ kích thước/cân đối cụm 3 nút từ V1.3.97.
- Bỏ icon ⚡ khỏi nút `Tìm nhanh` ở template render chính và template polling.
- Không sửa CSS, không thay route, JS gọi Quick Match, backend hay luồng xử lý.

## V1.3.100 - Dong_bo_giao_dien_Tim_nhanh_va_cap_nhat_version (2026-08-08)
- Đồng bộ nút `Tìm nhanh` theo đúng hệ nút chung đang dùng cho `Mời đấu` và `Sẵn Sàng`.
- Giữ nguyên màu xanh và kích thước 52px trong cụm 3 nút.
- Xóa block CSS riêng `room-quick-flat` của V1.3.99 để không còn một skin riêng cạnh tranh với `.arena-btn.green`.
- Nút Tìm nhanh hiện dùng cùng class giao diện: `btn arena-btn green room-center-action-btn`, nhưng vẫn giữ `room-quick-flat` làm hook nhận diện không có CSS riêng.
- Không đổi `data-quick-match-url`, JavaScript, route hay luồng Quick Match.
- Cập nhật `APP_VERSION` từ 1.3.92 lên 1.3.100 nên sidebar hiển thị `V1.3.100`.


## V1.3.101 - Xoa_lop_nen_duoi_chu_Tim_nhanh (2026-08-08)
- Phạm vi: frontend Room / Quick Match; không đổi route, backend, RP hay luồng mời đấu.
- Nguyên nhân lớp nền dưới chữ `Tìm nhanh`: nội dung nút vẫn bọc trong một thẻ `<span data-quick-match-label>`, nên phần tử con có thể nhận CSS/global style riêng dù CSS nút đã dọn.
- Xóa hoàn toàn thẻ `<span>` bên trong nút Tìm nhanh ở cả render chính và live polling; nút chỉ còn text node thuần.
- `quick_match.js` đổi sang cập nhật trực tiếp `button.textContent`, không còn query hay thao tác `data-quick-match-label`.
- Giữ nguyên các class chuẩn `btn arena-btn green room-center-action-btn` để giao diện Tìm nhanh dùng đúng cùng hệ nút với Mời đấu / Sẵn Sàng.
- Cập nhật APP_VERSION thành 1.3.101.


## V1.3.113 - Phong_lon_logo_che_do_dang_chon_va_can_doi_khung_trung_tam (2026-08-08)
- Tăng rõ kích thước logo của chế độ đang được chọn trong khung trung tâm phòng đấu.
- Logo trung tâm được phóng lớn hơn logo ở danh sách 6 chế độ để đúng thứ bậc thị giác.
- Giữ nguyên chiều cao tổng thể khung chế độ; chỉ dùng vùng trống hiện có nên không đẩy lệch VS, nút Sẵn Sàng/Thoát Phòng hoặc hai cột người chơi.
- Tăng nhẹ đổ bóng vàng của logo để logo rõ trên nền tối.
- Chỉ áp dụng ở trạng thái `waiting_ready`; các trạng thái đang thi đấu/gửi kết quả giữ kích thước gọn như trước.
- Không đổi backend, route, RP, Series, Parsec hay luồng chọn chế độ.
- Cập nhật APP_VERSION thành 1.3.113.

## V1.3.119 - Lam_noi_that_room_sat_anh_mau_3 (2026-08-09)
- Tiếp tục trực tiếp từ V1.3.118; không dựng lại grid và không thay backend/route/API/RP.
- Chỉ áp dụng shell mới cho trạng thái `Chờ đối thủ`.
- Làm đậm phần header: PES ARENA lớn hơn, mã phòng vàng hơn, nút Chia sẻ phòng lớn và rõ hơn.
- Tăng chiều sâu card Chủ phòng/Đối thủ bằng background sân thật, lớp phủ xanh/đỏ, neon và shadow; tăng avatar, tên, rank và vùng CLB.
- Tăng logo chế độ đang chọn lên 172x154, tăng VS và tăng trọng lượng thị giác của center column.
- Làm sidebar Thông tin phòng/Parsec/Lịch sử gần phong cách khung vàng của ảnh mẫu hơn.
- Làm lại 3 nút Mời đấu/Tìm nhanh/Thoát phòng lớn hơn, có icon, giữ màu vàng/xanh/đỏ và hook chức năng cũ.
- Tăng 6 mode card lên 205px; logo 128px; thêm badge số góc và nền/glow theo từng chế độ.
- Sửa đúng thứ tự hiển thị 6 chế độ theo ảnh mẫu: 1 Rank Random, 2 Random 3 chọn 1, 3 Chiến thuật BO3, 4 BO3, 5 Cấm chọn CLB, 6 Lượt đi - lượt về.
- Đồng bộ số badge của chế độ đang chọn theo đúng thứ tự trên.
- Cập nhật APP_VERSION từ 1.3.118 lên 1.3.119.


## V1.3.120 - so_khop_anh_mau_3_lan_cuoi
- Chot lai shell phong dau trang thai Cho doi thu theo anh mau 3.
- Them CSS moi `static/css/room/20-room-v3-waiting-final.css` de tang nen trong suot, chieu sau, glow va can chinh ty le.
- Co dinh thu tu 6 che do: rank_random -> random3_pick1 -> tactical_bo3 -> bo3 -> ban_pick_bo3 -> home_away.
- Dong bo so thu tu mode dang chon va mode card.
- Wrapper cho waiting shell dung `pes-room3-live-shell arena-room-v2` de nhan bien nen san dau.


## V1.3.121 - trong_suot_khu_vuc_3_va_khung_vang_neon
- Khu vuc 3 (center mode) chuyen sang nen trong suot hon, bo goc va bo khung vang anh kim co glow neon.
- 6 logo che do va card che do chuyen ve nen trong suot, vien vang anh kim va hieu ung chieu sau.
- Thu gon chieu cao toan bo waiting shell de o tile 100% nhin thay day du host / center / opponent / sidebar / nut / 6 che do.
- Giu nguyen logic phong dau, chi tinh chinh giao dien trang thai Cho doi thu.


## V1.3.122 - giam_header_va_tang_logo_che_do
- Giam co chu PHONG DAU va giam kich thuoc anh PES ARENA o header.
- Sua hien thi ten nguoi choi de khong bi che / cat nua ben duoi.
- Tang manh logo che do o giua man hinh de chiem phan lon hon trong khung.
- Tang manh logo cua 6 che do khac de logo chiem da so dien tich card.


## V1.3.123 - thu_nho_header_va_sua_ten_nguoi_choi
- Giam tiep co chu PHONG DAU va thu nho them anh PES ARENA theo phan hoi.
- Sua template ten nguoi choi sang cau truc span ben trong de tranh bi cat / mat chu.
- Tang them kich thuoc logo che do o giua man hinh.
- Tang them kich thuoc logo cua cac che do khac de logo chiem phan lon hon trong card.


## V1.3.123 - tinh_chinh_theo_anh_sau_deploy
- Giam tiep co chu PHONG DAU va anh PES ARENA sau khi kiem tra anh deploy.
- Sua lai CSS ten nguoi choi va template de tranh mat / cat chu.
- Tang tiep kich thuoc logo che do o giua man hinh.
- Tang tiep kich thuoc logo cac che do khac.


## V1.3.124 - sap_xep_lai_thu_tu_6_che_do
- Chinh thu tu 6 che do dung yeu cau:
  1. Rank Random
  2. Random 3 chon 1
  3. Luot di / luot ve
  4. BO3
  5. Chien thuat BO3
  6. Cam chon CLB
- So thu tu card va so mode o center dung chung danh sach nay nen duoc dong bo.
- Khong thay doi logic / backend khac.


## V1.3.125 - can_ty_le_logo_va_khu_vuc_che_do
- Can lai ty le 4 khu vuc: host / center / opponent / sidebar de sat giao dien mau hon.
- Thu gon khu mode dang chon o center, giam do phong VS, can lai title / mo ta / logo / line trang thai.
- Can lai khu vuc CAC CHE DO KHAC: dieu chinh chieu cao card, khoang cach, ty le logo va khung ten/nut.
- Them tuning rieng theo tung che do de logo nhin can doi hon, tranh logo qua to hoac qua nho.


## V1.3.126 - thay_anh_vs_va_nen_center
- Thay ảnh nền phía sau khu VS bằng asset người dùng cung cấp: `static/assets/room_custom/center-stadium-v126.webp`.
- Thay ảnh chữ VS bằng asset PNG/WebP nền trong suốt người dùng cung cấp: `static/assets/room_custom/vs-gold-v126.webp`.
- Áp dụng ảnh nền center qua biến `--arena-center-stadium` cho toàn bộ giao diện Room.
- Áp dụng ảnh VS mới cho cả trạng thái Chờ đối thủ và các trạng thái Room còn lại.
- Không thay đổi Backend, RP, API hoặc luồng chức năng.


## V1.3.127_can_lai_card_cac_che_do_theo_anh_mau
- Can lai khu CAC CHE DO KHAC theo anh mau nguoi dung gui.
- Dieu chinh 3 thanh phan chinh cua card: ty le logo, ten che do, trang thai mo khoa / tam tat.
- Tang chieu cao card, can giua logo, phong to ten che do va lam nut trang thai ro hon.
- Giu tong the 6 card dong bo nhung van co tuning nhe theo tung logo de tranh lech ty le.


## V1.3.128_trang_thai_3_muc_cho_cac_che_do
- Chuan hoa trang thai card o phan CAC CHE DO KHAC thanh 3 muc ro rang: Da mo khoa / Chua mo khoa / Che do dang tam tat.
- Ap dung cho giao dien room moi va giao dien room tong hop de hien thi dong bo.
- Them class mau rieng cho tung trang thai de nguoi dung nhin vao la phan biet duoc ngay.


## V1.3.129_phong_to_logo_va_tang_be_ngang_trang_thai_che_do
- Phong to tiep logo trong cac card che do ben duoi de sat hon anh mau nguoi dung gui.
- Tang chieu cao the mode va mo rong be ngang dong trang thai de gan nhu an kin khung ben duoi.
- Tang nhe co chu ten che do va can lai khoang trang giua logo / ten / trang thai.


## V1.3.130 - Room UI Designer trong Admin
- Thêm tab `🎨 Thiết kế phòng đấu` trong Admin, tách module `modules/admin_room_ui/`.
- Cho phép kéo slider để chỉnh tỷ lệ Host / Center / Opponent / Sidebar, chiều cao khu chính, logo chế độ đang chọn, VS, chiều cao card, độ rộng trạng thái và 6 logo riêng biệt.
- Có Preview trực tiếp trong Admin, nút đồng bộ 6 logo, lưu cấu hình và khôi phục mặc định.
- Cấu hình lưu vào `system_settings.setting_key = room_ui_designer_config`, có validate giới hạn và cache.
- `room_detail.html` truyền cấu hình xuống CSS variables; không sửa Backend gameplay, RP, matchmaking hay polling.
- Room V3 chờ đối thủ nhận đầy đủ biến; các trạng thái Room cũ nhận tương thích cho mode card, logo active và VS.

## V1.3.131 - Nang_cap_Room_UI_Designer_keo_XY_va_preview_khung
- Sửa Preview tỷ lệ các khung chính: giá trị Host / Center / Opponent / Sidebar giờ dùng đúng đơn vị `fr`, kéo slider thấy thay đổi trực tiếp.
- Thêm kéo trực tiếp X/Y trên Preview cho 4 khung chính: Chủ phòng, Center, Đối thủ, Sidebar.
- Thêm chỉnh kích thước + X/Y cho Avatar chủ phòng, tên người chơi, ảnh PES ARENA, logo chế độ đang chọn và VS.
- Thêm khoảng cách giữa 4 khung chính và khoảng cách giữa 6 card chế độ.
- Bỏ 6 thanh tỷ lệ logo riêng; thay bằng 1 thanh `mode_logo_scale` đồng bộ cả 6 logo.
- Tự chuyển cấu hình V1.3.130 cũ: lấy trung bình 6 tỷ lệ logo cũ làm tỷ lệ chung mới.
- Các thông số mới được nối xuống giao diện Room thật; giữ breakpoint responsive để tránh phá bố cục mobile/tablet.


## V1.3.132 - Khoi_phuc_luong_tran_sau_Room_UI_Designer
- Co lap Room UI Designer chi vao trang thai Cho doi thu (waiting_ready + chua co guest).
- Khoi phuc CSS on dinh V1.3.129 cho cac trang thai co thao tac tran: san sang / playing / gui ket qua / xac nhan / da tiep / doi che do.
- Bo viec doc cau hinh Room UI tu Supabase tren moi request/template; chi doc khi mo room_detail ban dau.
- Bo viec doc Room UI config o cac tab Admin khong lien quan.
- Muc tieu: Room UI Designer khong duoc cham vao backend, API, form submit, polling, result/confirm/rematch/mode switch.


## V1.3.133_sua_xac_nhan_ket_qua_va_ghi_loi_server_vao_blackbox
- Tang do tin cay luong Xac Nhan ket qua Rank thuong: theo doi phase xu ly claim / tinh RP / chong farm / gioi han ngay / cap RP / ghi user / chot match.
- Neu loi sau khi da cap nhat mot nguoi choi, tu dong rollback chinh xac ve snapshot truoc khi xac nhan, tranh bam lai bi cong/tru RP va thong ke trung.
- Kiem tra bat buoc ket qua PATCH finalize match phai tra ve row; neu khong se bao loi thay vi coi nhu thanh cong gia.
- Cache invalidation sau cap nhat user chuyen thanh fail-open, khong duoc phep lam hong viec xac nhan tran.
- Ma loi CONFIRM moi duoc luu server-side vao Blackbox kem phase, room_id, match_id va loai exception de co the truy vet truc tiep.
- Khong thay doi cong thuc RP, Series, giao dien Room UI Designer hay schema database.


## V1.3.134_sua_triet_de_loi_CONFIRM_safe_int
- Sua dung nguyen nhan Blackbox CONFIRM-E81965F2: `match_result_service.py` goi `_safe_int` nhung phu thuoc vao global configure/import order.
- Dua `_safe_int` thanh helper cuc bo ngay trong module ket qua tran, khong con phu thuoc `app.py` hoac module khac.
- Nang test xac nhan de KHONG inject `_safe_int` tu context; test phai tu chay bang helper cua chinh module.
- Giu nguyen co che claim/idempotency/rollback cua V1.3.133 de tranh cong RP hai lan khi retry.

## V1.4.1 — 09/08/2026 13:17+07:00 — Don xung dot CSS Room + tu sua phong Series bi ket

### Phat hien
- CSS Room van con selector action/button bi so huu dong thoi boi `15-room-actions-stability.css` va `17-center-match-stability.css`.
- `21-v14-css-isolation.css` lap selector chinh xac voi `20-room-v3-waiting-final.css`.
- Luong Series co rui ro: match con da `confirmed` nhung reset phong tu `waiting_result_confirm` ve `waiting_ready` that bai; lan xac nhan lai chi thay match da confirmed va co the de phong bi ket.

### Sua
- `static/css/room/15-room-actions-stability.css`: gom toan bo selector nut/action ve dung owner.
- `static/css/room/17-center-match-stability.css`: bo cac selector nut/action da chuyen sang file 15, giu nguyen gia tri hien thi.
- `static/css/room/21-v14-css-isolation.css`: doi sang selector `:is()` de cach ly V3 ma khong trung exact selector voi file 20.
- `modules/rank_series/service.py`: them `_reset_room_after_series_confirm()` co kiem tra ket qua update va tu repair khi retry neu match con da confirmed.
- `app.py`: APP_VERSION 1.4 -> 1.4.1.

### Kiem tra
- Python compile: PASS.
- JavaScript `node --check`: PASS.
- CSS cross-module Room selector ownership conflicts: 0.
- Regression quan trong Room/Confirm/Series/CSS/Quick Match/Presence: PASS.
- Full pytest lich su van co nhieu test source/version cu; khong thay production code de ep cac test lich su nay pass.

## V1.4.2 — 09/08/2026 13:21+07:00 — Dong bo mau thong bao + giam loi BlackBox gia
- `app.py`: APP_VERSION 1.4.1 -> 1.4.2.
- `static/css/invite_center.css`: popup lời mời dùng tone hồng thống nhất; nút chính Chấp nhận/Vào phòng cùng tone hồng, nút Từ chối chuyển thành neutral secondary.
- `static/css/quick_match.css`: nút trong thông báo Quick Match đi theo tone success/danger/info thay vì luôn màu vàng.
- `static/css/ui_dialog.css` + `static/js/ui_dialog.js`: dialog warning/success/danger/info đồng bộ viền, icon, kicker và nút chính theo cùng tone.
- `static/js/blackbox.js`: tách lỗi tải asset thành `resource_error` thay vì ghi nhầm `js_error`; fetch bị hủy khi rời trang/offline/AbortError ghi `network_cancelled` WARNING thay vì `api_error`; JS exception thật bổ sung stack.
- `modules/match_result_service.py`: giữ helper `_safe_int` nội bộ của V1.4.1 và thêm regression test bảo vệ pha `calculate_deltas`.
- Test: Python compile PASS; toàn bộ JS `node --check` PASS; regression trọng tâm 17/17 PASS (1 test version cũ được deselect).

## V1.4.3 - Noi lai toan bo luong tran dau va du lieu
- Ngay: 2026-08-09
- Kiem tra state machine: Moi dau -> San sang -> Quay quan -> Gui ket qua -> Xac nhan -> Da tiep -> Thoat phong.
- Sua Xac nhan de room dung o `confirmed`, khong nhay thang `waiting_ready`.
- Sua Da tiep bat buoc ca hai nguoi dong y, doi xung Host/Guest.
- Sua Series: chi tran con chua ket thuc moi quay ve `waiting_ready`; Series hoan tat vao `confirmed`.
- Them rollback match mo coi neu tao `matches` thanh cong nhung cap nhat `match_rooms` that bai.
- Kiem tra ket qua DB khi San sang/Huy san sang truoc khi bao thanh cong.
- Sua Auto-confirm 60 giay dung cung state machine `confirmed -> Da tiep/Roi phong`.
- Gia co luong nhan loi moi: claim invite truoc khi dong phong cu, cleanup phu khong rollback gameplay chinh.
- Don `invite_id` cu khi tu choi/huy loi moi.
- Giu phong `confirmed` la busy cho den khi roi phong/het han/da tiep.
- Them `test_v143_match_flow_integrity.py` va `AUDIT_V1.4.3_LUONG_TRAN_DAU.txt`.
