# CHANGELOG — PES Arena

> Nguồn: các `V1.5.xx_RELEASE_NOTES.txt` có thật trong source. Không tự suy diễn các version bị thiếu.

## [V1.5.77] — 2026-09-14
- Phân tích toàn bộ source và bổ sung `PROJECT_MAP.md`.
- Bổ sung `PROJECT_RULES.md` làm quy tắc phát triển/kiểm thử/đóng gói bắt buộc.
- Hợp nhất lịch sử release hiện có vào `CHANGELOG.md`.
- Không thay đổi database, route hoặc nghiệp vụ.

## [V1.5.76]
MỤC TIÊU
- Refactor cấu trúc templates/tournaments.html để các lần sửa giao diện giải đấu sau nhanh hơn và ít ảnh hưởng chéo hơn.
- Không thay đổi giao diện, dữ liệu, route, database hoặc luồng nghiệp vụ hiện tại.

THAY ĐỔI
1. templates/tournaments.html
   - Giảm thành file điều phối chính (orchestrator).
   - Giữ các điều kiện cấp trang: tournament_open và tournament_db_ready.
   - Chuyển từng khu vực giao diện sang partial riêng bằng Jinja include.

2. Tạo templates/tournament/
   - styles.html: toàn bộ CSS hiện tại của trang giải đấu.
   - tournament_list.html: vòng lặp danh sách giải.
   - components/hero.html
   - components/closed.html
   - components/filterbar.html
   - components/database_not_ready.html
   - components/availability_gate.html
   - cards/champions_league.html
   - cards/c1_media.html
   - cards/c1_header_nav.html
   - cards/c1_actions.html
   - cards/c1_registration.html
   - cards/generic.html
   - tabs/ranking.html
   - tabs/lobby.html
   - tabs/schedule.html
   - scripts/page_scripts.html
   - scripts/legacy_tail_scripts.html

3. BẢO TOÀN TƯƠNG THÍCH
   - Giữ nguyên id, class, data-* hook, form action và biến Jinja.
   - Không sửa API/route/backend.
   - Không sửa SQL/database.
   - Không đổi logic 2 tài khoản test, Admin, Host đang rảnh, BXH, lịch thi đấu hoặc popup khai báo lịch.

VERSION
- APP_VERSION: V1.5.75 -> V1.5.76

## [V1.5.75]
1. Sảnh chờ
- Đổi tiêu đề “🏟️ Phòng thi đấu” thành “🏟️ Sảnh chờ”.
- Đổi mô tả thành: “Sảnh trung tâm để theo dõi phòng giải, HLV đang chờ và Host đang rảnh.”

2. Host đang rảnh
- Chỉ lấy HLV active thuộc đúng giải, có đăng ký Host, đang online thật và không ở phòng đấu đang hoạt động.
- Bỏ trạng thái room `confirmed` khỏi danh sách trạng thái bận vì trận đã hoàn tất.
- Bổ sung `waiting_confirm` vào trạng thái bận để tránh hiển thị Host khi còn đang xử lý kết quả.
- Thêm API đọc `/api/tournaments/<tournament_id>/host-ready`.
- Sảnh chờ tự cập nhật danh sách mỗi 15 giây và khi quay lại tab; 2 tài khoản test, Admin và HLV thường đều nhận cùng danh sách live.
- Polling lỗi sẽ giữ nguyên dữ liệu server-render hiện có, không làm trống UI giả.

3. Version
- Đồng bộ APP_VERSION toàn hệ thống lên V1.5.75.
- Không thay đổi SQL/database schema.

File tác động:
- app.py
- modules/tournament_competition.py
- templates/tournaments.html
- V1.5.75_RELEASE_NOTES.txt

## [V1.5.74]
Điều chỉnh thanh menu nhanh của giải đấu:
- Đổi thứ tự: 📊 BXH · 📅 Lịch của tôi · 🏟️ Sảnh chờ · 🎮 Phòng đấu C1.
- Đổi nhãn “Phòng thi đấu” trên menu nhanh thành “Sảnh chờ”; anchor/chức năng phía sau giữ nguyên.
- Bỏ hoàn toàn trạng thái is-active khỏi menu nhanh.
- Bỏ viền vàng cố định và vạch vàng 3px phía dưới tab đang chọn.
- Giữ hiệu ứng hover nền sáng nhẹ + viền vàng.
- Giữ thời gian khởi tranh đã bổ sung ở V1.5.73.

Phạm vi tác động:
- templates/tournaments.html
- app.py (đồng bộ APP_VERSION V1.5.74)

Không thay đổi database/SQL hoặc logic thi đấu.

## [V1.5.73]
Nâng cấp giao diện điều hướng trên card PES Arena Champions League:
- Thêm thời gian khởi tranh GĐ1 ngay cạnh thông tin giải đấu (giờ Việt Nam GMT+7).
- Chuyển 4 chức năng thành thanh menu nhỏ gọn trên cùng một hàng:
  🎮 Phòng đấu C1 · 📅 Lịch của tôi · 📊 BXH · 🏟️ Phòng thi đấu.
- Nền tab #0B1C29, bo góc 11px, viền xanh xám mảnh, chữ trắng và icon nổi hơn.
- Hover: nền sáng nhẹ + viền vàng.
- Tab đang chọn: viền vàng + vạch vàng 3px phía dưới.
- Responsive: màn hình nhỏ tự chuyển 2 cột để không tràn giao diện.

Phạm vi tác động:
- templates/tournaments.html
- modules/tournament_routes.py
- app.py (đồng bộ APP_VERSION V1.5.73)

Không thay đổi database/SQL và không thay đổi logic thi đấu.

## [V1.5.72]
- Nâng cấp khối Tiến trình giải đấu trên card Champions League để nổi bật hơn.
- Countdown GĐ1 được trình bày thành 4 ô Ngày / Giờ / Phút / Giây rõ ràng.
- HLV thuộc giải thấy trạng thái cá nhân: số trận GĐ1 còn chưa hoàn thành hoặc xác nhận đã hoàn thành.
- Hai tài khoản test dùng cùng luồng landing_hub để kiểm tra trạng thái cá nhân.
- Thêm khẩu hiệu: “Chiến hết mình – Cháy cùng đam mê!”
- Giữ nguyên phần Thưởng hoàn thành sớm.
- Đồng bộ APP_VERSION lên V1.5.72.

## [V1.5.71]
- Popup đăng ký lịch thi đấu linh hoạt có sẵn giờ mẫu: 18:30 - 22:00.
- Có nút - / + để tăng giảm thời gian theo bước 30 phút.
- Người chơi vẫn có thể chọn hoặc nhập thời gian trực tiếp trong ô giờ.
- Không thay đổi backend/database; chỉ tác động giao diện templates/tournaments.html.
- Đồng bộ APP_VERSION toàn hệ thống lên V1.5.71.
- Dọn toàn bộ __pycache__, *.pyc và các file tạm/cache trước khi đóng gói.

## [V1.5.70]
- Không hiển thị dòng zalo.me/g/bqbtai165 dưới QR ở sidebar.
- Link click tham gia nhóm vẫn giữ nguyên.
- Thay ảnh QR Zalo bằng zalo_qr.webp ở sidebar và trang Hướng dẫn.

## [V1.5.69]
- Thêm QR nhóm Zalo dưới khung Phiên bản ở sidebar.
- Sidebar mở nhóm: https://zalo.me/g/bqbtai165
- QR mới: https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1/zalo_group_qr.webp
- Trang Hướng dẫn thay link nhóm Zalo cũ bằng link mới.
- Trang Hướng dẫn thay QR cũ bằng QR mới.

## [V1.5.68]
- Tiến độ GĐ1 thêm cột Còn lại.
- Còn 0 trận: xanh nhẹ.
- Còn 1 trận: cam nổi bật.
- Còn >=2 trận: đỏ nổi bật.
- Thêm cột trạng thái, không đổi logic thưởng.

## [V1.5.67]
- Popup lịch rảnh hiển thị Lịch của đối thủ.
- Tick giờ trùng đổi xanh lá realtime cho HLV thật và tài khoản test.

## [V1.5.66]
Realtime giờ rảnh trùng đối thủ
- Tick/bỏ tick giờ rảnh cập nhật ngay, không cần bấm Lưu.
- Khung giờ HLV chọn mà trùng ít nhất một đối thủ được tô xanh lá ngay.
- Khung đã chọn nhưng không trùng giữ màu xanh dương.
- Các khung trong Lịch của đối thủ cũng đổi xanh realtime theo lựa chọn chưa lưu.
- Tích toàn bộ cũng cập nhật realtime.
- Áp dụng đồng nhất cho HLV thật và tài khoản test.

## [V1.5.65]
Fix popup lịch rảnh cho tài khoản test:
- Form LƯU LỊCH trong popup dùng route test khi hub.is_test=True.
- HLV thật vẫn lưu vào tournament_availability_slots.
- Giờ linh hoạt giữ nguyên route dùng chung đã hỗ trợ test.
- Sau lưu redirect về /tournaments, mine_set được đọc lại và popup biến mất khi đã có ít nhất một slot.

## [V1.5.64]
- Fix popup lịch rảnh không hiện trên 2 tài khoản test C1.
- Gate áp cho: HLV thật thuộc tournament_members HOẶC tài khoản test C1.
- Người dùng thường không tham gia giải vẫn xem /tournaments bình thường.
- Popup chỉ xuất hiện khi tài khoản tương ứng chưa có bất kỳ giờ rảnh nào trong mine_set.
- Giữ nguyên popup PES Arena bắt buộc của V1.5.63.

## [V1.5.63]
- Gate lịch rảnh chỉ áp dụng cho HLV tham gia giải.
- Người không tham gia giải xem bình thường.
- Popup bắt buộc phong cách PES Arena, không window.alert, không nút đóng/Escape.
- Form 3 ngày + giờ linh hoạt 24h.

## [V1.5.62]
- Khôi phục gate bắt buộc khai báo giờ rảnh ngay trên /tournaments.
- HLV thật và tài khoản test: chưa có giờ rảnh => chỉ thấy ĐẶT LỊCH THI ĐẤU 3 ngày + Giờ linh hoạt.
- Khi gate khóa: ẩn Phòng đấu C1, BXH, Phòng thi đấu, Đối thủ, Lịch đối thủ.
- Lưu ít nhất một khung giờ => mở toàn bộ giao diện giải.
- Admin được miễn gate.

## [V1.5.61]
- Sửa Tiến trình giải đấu / Thưởng hoàn thành sớm trên /tournaments.
- Overlay không còn phụ thuộc landing_hub/member.
- Admin, HLV thường và tài khoản test đều đọc chung dữ liệu timing công khai của giải.
- Dòng thưởng luôn hiện khi có mốc stage1_early_end_at; hết hạn sẽ báo Đã hết thời gian thưởng.

## [V1.5.60]
- GĐ2 chính thức: 16 HLV chia 3 Pot theo BXH GĐ1 = 5–6–5.
- Pot 1: hạng 1–5; Pot 2: hạng 6–11; Pot 3: hạng 12–16.
- Bỏ cách chia ceil 6–6–4.
- Backend chặn sinh lịch nếu Pot không đúng 5–6–5.
- Giữ 4 trận/HLV: 3 lượt ưu tiên phủ 3 Pot + 1 Random, không lặp đối thủ.
- Test mode 16 HLV/3 Pot dùng cùng cấu trúc 5–6–5.

## [V1.5.59]
THƯỞNG GIAI ĐOẠN 1
- Top hoàn thành sớm #1: 1.000 ZCoin + 2 Lucky Box + 2 vé Random CLB GĐ2.
- Top hoàn thành sớm #2–3: 800 ZCoin + 1 Lucky Box + 1 vé Random CLB GĐ2 mỗi HLV.
- Admin có nút Trao thưởng GĐ1; ZCoin/Lucky Box dùng idempotency để chống cộng trùng.
- Vé Random CLB dùng trong cơ chế chọn CLB GĐ2; CLB bỏ qua không xuất hiện lại cho chính HLV đó.

LUẬT GIAI ĐOẠN 2
- Đúng 4 trận/HLV.
- 3 lượt đầu ưu tiên rải đối thủ qua 3 Pot.
- 1 lượt Random bất kỳ, không lặp đối thủ.
- Kết thúc GĐ2: Top 1–3 BXH tổng nhận mỗi người 1 vé Random lại CLB trước KO.
- HLV có vé thấy nút Random lại CLB trực tiếp tại /tournaments; CLB đã bỏ được loại khỏi lượt random sau.

KNOCKOUT
- Bỏ Play-off.
- Top 8 BXH tổng GĐ1 + GĐ2 vào thẳng Tứ kết.
- Ghép seed 1–8, 2–7, 3–6, 4–5.

## [V1.5.58]
- Sửa overlay Tiến trình: dòng 🎁 Thưởng hoàn thành sớm luôn hiển thị.
- Nếu hạn thưởng còn hiệu lực: hiển thị countdown.
- Nếu đã hết hạn: hiển thị Đã hết thời gian thưởng.
- Nếu chưa cấu hình mốc thưởng: hiển thị Chưa cấu hình hạn thưởng thay vì ẩn dòng.

## [V1.5.57]
- Admin được chủ động gửi lời mời Rank thủ công tới HLV thường.
- HLV thường vẫn không thể mời Admin.
- Admin không xuất hiện trong danh sách Player/đối thủ online dùng cho lời mời Rank.
- Tìm Nhanh của Admin vẫn bị khóa; thay đổi chỉ áp dụng lời mời thủ công.

## [V1.5.56]
- Đưa Tiến trình giải đấu + thời gian GĐ1 + Thưởng hoàn thành sớm lên góc phải background card giải tại /tournaments.
- Gộp Đối thủ của tôi vào khu Phòng thi đấu.
- Nút Phòng thi đấu dẫn tới cụm Host đang rảnh + Trận của tôi + Đối thủ của tôi.

## [V1.5.55]
- Thêm nút 📊 BXH trên card giải tại /tournaments, nhảy trực tiếp tới khu BXH.
- Thêm nút 🏟️ Phòng thi đấu trên card giải tại /tournaments, nhảy trực tiếp tới khu Phòng thi đấu/Host đang rảnh/Trận của tôi.
- Giữ nguyên 🎮 Phòng đấu C1 và 📅 Lịch của tôi.
- Không tạo trang trung gian mới; các nút BXH/Phòng thi đấu dùng anchor trên chính /tournaments.

## [V1.5.54]
- Xóa nút “Xem chi tiết →” khỏi /tournaments vì nội dung HLV cần đã được đưa về hub chính.
- Toàn bộ link/redirect người dùng từng quay về tournament_detail giờ quay về /tournaments (giữ anchor khi có).
- GET /tournaments/<id> chỉ còn là route tương thích và redirect về /tournaments.
- Nút Về giải đấu trong phòng C1, c1-rooms và các redirect lỗi/lịch/CLB/BXH đều quy về /tournaments.
- Không xóa các POST route /tournaments/<id>/... vì tournament_id vẫn cần cho xử lý nghiệp vụ.

## [V1.5.52]
- Giữ nút Phòng đấu C1 đi thẳng vào phòng thật.
- Chuyển khu "Đối thủ của tôi", "Lịch thi đấu / Giờ rảnh" và "Lịch của đối thủ" ra cuối trang /tournaments.
- Loại bỏ các khu này khỏi /tournaments/<id> để không hiển thị trùng.
- Nút "Lịch của tôi" tại card giải nhảy xuống đúng khu lịch ở /tournaments.
- Form lưu giờ rảnh, giờ linh hoạt và mở đối thủ có return_to=tournaments để thao tác xong vẫn ở trang /tournaments.
- Giữ giờ hiển thị 24h.

## [V1.5.51]
- Nút Phòng đấu C1 tại /tournaments POST trực tiếp c1_room_open với tournament_id.
- Nếu HLV đã có phòng C1 đang hoạt động: vào thẳng room_detail.
- Nếu chưa có phòng: tạo Phòng C1 thật và redirect thẳng room_detail.
- Không đi qua trang trung gian /c1-rooms trong luồng bình thường.
- Chuyển Đối thủ của tôi xuống cuối nội dung giải.
- Chuyển Lịch thi đấu / Giờ rảnh và Lịch của đối thủ xuống cuối nội dung giải.
- Giữ link Lịch của tôi trỏ #schedule.

## [V1.5.50]
- Giữ nguyên bố cục /tournaments của V1.5.48.
- Nút "◉ Xem giải đấu" đổi thành "🎮 Phòng đấu C1" và đi tới khu Phòng đấu C1.
- Nút "Đăng ký đã đóng" / "Lịch đấu" đổi thành "📅 Lịch của tôi" và mở #schedule.
- Bỏ dòng mô tả phụ dưới tiêu đề 📊 BXH.
- Khung giờ thi đấu hiển thị theo định dạng 24h; bỏ ký hiệu phân chia sáng/chiều.
- Không áp dụng cơ chế bung thẳng nội dung giải của V1.5.49.

## [V1.5.48]
- Cổng ĐẶT LỊCH THI ĐẤU hiển thị Giờ linh hoạt cho tài khoản test giống HLV thật.
- Tài khoản test dùng cùng route availability/custom; dữ liệu vẫn lưu riêng, không ảnh hưởng dữ liệu giải thật.
- Giữ nguyên khung giờ 3 ngày Hôm nay / Ngày mai / Ngày kia.

## [V1.5.45]
- Phòng C1 chính thức và khu kiểm thử dùng chung một hàm reset/chuyển trạng thái sau khi xác nhận kết quả.
- State chuẩn giống Rank: waiting_ready + guest_ready=False + xóa đội/tỷ số/match cũ.
- Chỉ lớp dữ liệu khác nhau: giải chính thức dùng tournament_matches; khu kiểm thử dùng lịch sử riêng.
- Dọn các nhãn C1 TEST / SANDBOX khỏi giao diện người chơi để tránh gây nhầm với phòng C1 chính thức.
- Không thay đổi dữ liệu BXH/lịch giải chính thức khi dùng tài khoản thử nghiệm.

## [V1.5.44]
- Fix TEST C1/SANDBOX bị kẹt ở status=confirmed và hiển thị "Đang chuyển sang trận tiếp theo..." cho cả hai bên.
- Copy đúng nhịp Rank cho xác nhận kết quả TEST: lưu kết quả -> reset chính room về waiting_ready -> guest_ready=False -> khách bấm Sẵn Sàng -> chủ phòng Quay đội.
- Lưu lịch sử kết quả TEST trong tournament_meta.test_result_history để BXH TEST vẫn cộng đủ các trận dù room được tái sử dụng.
- Tự phục hồi phòng TEST cũ đang kẹt confirmed khi tải phòng; không cần tạo lại phòng.
- Không ghi vào tournament_matches, BXH C1 thật hoặc Rank.

## [V1.5.43]
- Loai bo nut Da Tiep khoi luong C1 giua cac tran.
- C1 confirmed chi la ket thuc that su khi cap dau da du tran.
- Neu phong C1 cu bi ket confirmed nhung con row tran tiep theo, phong tu phuc hoi ve waiting_ready.
- Sau xac nhan ket qua: retry truc tiep Rank-style waiting_ready, guest_ready=false; khong fallback ve confirmed/Da Tiep.
- Dong bo room_detail.html va _room_live_content.html de khong con hai logic render mau thuan.
- CSS khong phai nguyen nhan; loi la do template/state machine cu con ton tai song song.

## [V1.5.42]
Mục tiêu
- Copy đúng cơ chế chuyển Trận 1 -> Trận 2 của phòng Rank sang phòng C1.

Flow Rank chuẩn được áp sang C1
1. Trận hiện tại được xác nhận kết quả.
2. Chính room hiện tại chuyển sang trận C1 kế tiếp của đúng cặp HLV.
3. Room reset về status=waiting_ready.
4. guest_ready=False.
5. Xóa đội, overall, logo/league, tỷ số, match_id và dữ liệu submit của trận cũ.
6. Giữ nguyên host/guest và cập nhật tournament_match_id / current_leg_no sang trận mới.
7. Khách phải bấm Sẵn Sàng lại.
8. Chỉ sau khi guest_ready=True, Chủ phòng mới được Quay đội.
9. Không cần tạo room mới và không cần nút Đá Tiếp ở flow bình thường.

Sửa lỗi V1.5.41
- Bỏ guest_ready=True tự động ở Trận 2+.
- Sửa mâu thuẫn update guest_ready=True nhưng verify lại yêu cầu False.
- Đồng bộ route dự phòng room_rematch với cùng cơ chế Rank.

## [V1.5.41]
- C1 keeps the initial Match 1 flow unchanged: Guest must manually click Ready.
- After Match N is confirmed and the room advances to Match N+1, guest_ready is now TRUE immediately.
- Guest sees "Đã sẵn sàng" on Match 2+.
- Host immediately sees the C1 Random CLB / quay quân action instead of waiting for Guest to click Ready again.
- The legacy/manual Next Match fallback uses the same state, preventing inconsistent behavior between transition paths.
- Teams, scores and match_id are still reset between legs; only the next-leg ready state changes.

## [V1.5.40]
- C1 no longer stops at room.status=confirmed after every confirmed result when the same pair still has a scheduled next match.
- After Guest confirms Match N, the current C1 room is immediately rebound to Match N+1 and reset to waiting_ready, matching Rank flow.
- Clears teams, scores, ready state and transient room match fields while preserving the completed tournament result.
- Updates tournament_match_id/current_leg_no/transition_token in room metadata for the next leg.
- Stage1 legacy schedules missing a required next leg are repaired at confirmation time.
- Only leaves the room in confirmed/final state when the pair truly has no next match under the tournament schedule.

## [V1.5.39]
- Sửa lỗi sau Trận 1 cả Host và Guest vẫn thấy "✅ Cặp đấu đã hoàn tất".
- Nguyên nhân: UI coi tournament_has_next_match=False là bằng chứng cặp đã hoàn tất; trong khi biến này có thể False khi truy vấn trạng thái trận kế tiếp thiếu/chậm/lỗi.
- GĐ1 giờ chỉ hiện "Cặp đấu đã hoàn tất" khi tournament_pair_is_complete=True.
- Nếu là stage1 và chưa chứng minh hoàn tất, luôn hiện nút "Đá Tiếp"; route nghiệp vụ sẽ kiểm tra/tìm/tạo leg 2.
- room_rematch tự khôi phục stage_code và cặp HLV từ tournament_match hiện tại nếu metadata phòng cũ thiếu dữ liệu.
- Không thay đổi luật Rank/Friendly và không tự sửa DB khi render trang.

## [V1.5.38]
FIX CHÍNH
- Sửa lỗi C1 hoàn tất Trận 1 nhưng cả hai bên hiện "✅ Cặp đấu đã hoàn tất" và không thể đá Trận 2.
- GĐ1 giờ xét đúng luật 2 trận/cặp thay vì chỉ đếm số row tournament_matches đang tồn tại.
- Với dữ liệu lịch cũ bị thiếu leg 2, giao diện vẫn hiện Đá Tiếp.
- Khi bấm Đá Tiếp, backend mới tự tạo leg còn thiếu rồi tái sử dụng chính phòng hiện tại cho Trận 2.
- Không tạo/sửa dữ liệu trong GET/render phòng.

FILE TÁC ĐỘNG
- app.py
- modules/room_access_routes.py
- modules/room_rematch_routes.py
- modules/tournament_competition.py
- templates/room_detail.html
- templates/_room_live_content.html

## [V1.5.37]
- Fix C1 after match 1: no more "Tải lại phòng" dead end.
- After result confirmation, room goes to confirmed exactly like Rank.
- If the same tournament pair still has another scheduled/pending match, both participants see "Đá Tiếp".
- Pressing "Đá Tiếp" reuses the existing room_rematch tournament branch to attach the next tournament_match_id and reset the room to waiting_ready.
- Guest pressing "Đá Tiếp" is treated as ready immediately; Host can roll teams. If Host presses first, Guest sees Sẵn Sàng normally.
- If there is no remaining match for that pair/stage, show "Cặp đấu đã hoàn tất".
- No SQL/database schema changes.
- Based on V1.5.36 modular refactor; no rollback of modularization.

## [V1.5.35]
- Fix C1 Guest Ready/Host layout mismatch.
- Loại bỏ auto-repair DB trong lúc render phòng.
- C1 chỉ chuyển state ở backend nghiệp vụ; UI Host/Guest cùng đọc một state DB.
- Xác minh DB sau chuyển trận và sau Ready fallback trước khi báo thành công.
- Bỏ layout confirmed legacy hiển thị ĐỢI KHÁCH SẴN SÀNG.
- Không đổi database schema.

## [V1.5.34]
- Fix C1: Guest bấm Sẵn Sàng nhưng Host vẫn hiện ĐỢI KHÁCH SẴN SÀNG.
- Tournament Ready cập nhật trực tiếp theo room_id sau khi đã xác thực đúng Guest + waiting_ready.
- Đọc lại DB ngay sau update để xác minh guest_ready=true trước khi báo thành công.
- Host tiếp tục dùng state polling hiện có; guest_ready nằm trong state_key nên Host tự refresh sang nút QUAY ĐỘI.
- Không thay đổi SQL/database schema.
- Giữ nguyên Rank/Quick Match và luồng C1 Trận 1 -> trận tiếp theo của V1.5.33.
- APP_VERSION = V1.5.35.

## [V1.5.33]
- Bỏ toàn bộ câu/trạng thái trung gian kiểu "Còn trận trong lịch / Đang chuyển / Đang đồng bộ" khỏi phòng C1.
- Sau khi Guest xác nhận kết quả: nếu cùng cặp HLV trong cùng giai đoạn còn trận, room được reset thẳng về waiting_ready như một trận Rank mới.
- Guest thấy nút Sẵn Sàng; sau khi Guest sẵn sàng, Host quay đội và đá tiếp bình thường.
- Nếu dữ liệu/phòng cũ còn mắc ở confirmed nhưng lịch vẫn còn trận, Guest vẫn có nút Sẵn Sàng để đưa room thẳng về waiting_ready, không phải quay lại trang giải.
- Nếu không còn trận trong lịch thì mới hiện Cặp đấu đã hoàn tất.
- Không thay đổi database schema/SQL.

## [V1.5.32]
- C1 no longer uses a special "Open Match 2" or "Sync next match" step.
- After Guest confirms a result, backend checks the real tournament schedule for the same pair/stage.
- If another match remains: reuse the same room, attach the next tournament_match_id, reset room to waiting_ready, Guest clicks Ready, Host randomizes teams, then play normally.
- If no match remains: only then mark the room confirmed / pair completed.
- Added compatibility recovery for rooms stuck as confirmed by V1.5.29–V1.5.31.
- No database schema/SQL changes.

## [V1.5.31]
- Phòng C1 không còn giả định mọi cặp đều có 2 trận.
- Sau khi xác nhận kết quả, hệ thống đọc lịch thật của đúng cặp HLV trong cùng giai đoạn.
- Nếu còn trận chưa hoàn tất: dùng lại chính room, reset về waiting_ready, Guest bấm Sẵn Sàng, Host quay đội.
- Nếu không còn trận: mới đánh dấu Cặp đấu đã hoàn tất.
- GĐ1 2 trận và GĐ2 1 trận dùng chung một luồng.
- Tự sửa room V1.5.29/V1.5.30 bị kẹt confirmed sau Trận 1 khi tải lại trang.
- UI bỏ toàn bộ câu chữ cứng /2 trận, đủ 2 trận, Trận 1 -> Trận 2 trong trạng thái phòng.
- Không đổi database schema / SQL migration.

## [V1.5.30]
FIX C1 TRẬN 1 -> TRẬN 2
- Sửa lỗi mới đá 1 trận nhưng phòng hiện "Cặp đấu đã hoàn tất".
- Không còn dùng response.data của Supabase UPDATE để quyết định chuyển Trận 2 thành công.
- Sau khi Guest xác nhận Trận 1: xóa cache, đọc trực tiếp DB và xác minh room.status=waiting_ready + tournament_match_id đúng Trận 2.
- Nếu có Trận 2 nhưng xác minh reset room thất bại, tuyệt đối không ghi đè room thành confirmed.
- UI chỉ hiện "Cặp đấu đã hoàn tất" khi có đủ 2 trận completed của đúng cặp HLV.
- Đồng bộ APP_VERSION lên V1.5.30.
- Không thay đổi database schema / SQL migration.

## [V1.5.29]
C1 - tự chuyển Trận 2 theo luồng Rank
- Sau khi Host gửi kết quả Trận 1 và Guest xác nhận, phòng tự chuyển sang Trận 2 (waiting_ready).
- Guest bấm Sẵn Sàng ngay trong phòng.
- Khi Guest sẵn sàng, Host có thể Quay Đội Trận 2 ngay.
- Bỏ bước Host phải bấm nút Trận 2 / Guest phải chờ Chủ phòng mở Trận 2.
- Giữ nguyên kết quả Trận 1 và liên kết sang đúng leg còn lại của cùng cặp HLV.
- Không thay đổi database schema/SQL.
- Đồng bộ APP_VERSION lên V1.5.29.

## [V1.5.28]
FIX: C1 - Chủ phòng mở Trận 2 nhưng khách vẫn đứng ở “Chờ Chủ phòng mở Trận 2”.

Phạm vi:
- modules/tournament_competition.py
- app.py
- templates/room_detail.html

Thay đổi:
1. Chọn đúng leg còn lại của cùng cặp HLV theo leg_no, không phụ thuộc thứ tự query.
2. Đưa tournament_match Trận 2 về pending trước khi mở lại room.
3. Chỉ reset room từ trạng thái confirmed -> waiting_ready và kiểm tra kết quả update/DB sau khi chuyển.
4. Thêm transition_token vào metadata mỗi lần đổi leg.
5. build_room_state_key thêm fingerprint của room note để Host/Guest nhận ra thay đổi tournament_match_id/leg ngay cả khi hai HLV vẫn ở nguyên phòng.
6. Tăng tần suất polling riêng cho phòng C1 khi đang chờ mở Trận 2 / waiting_ready để khách cập nhật nhanh hơn.
7. Đồng bộ APP_VERSION lên V1.5.28.

Không thay đổi:
- Database schema / SQL migration.
- Logic Trận 1 và dữ liệu kết quả đã chốt.
- Quick Match / Rank / Giao hữu.
- Lịch đối thủ 3 ngày và live-overlap của V1.5.27.

## [V1.5.27]
- Lịch đối thủ chia theo 3 ngày.
- Giờ trùng được tô xanh ngay khi người dùng tích giờ rảnh, chưa cần bấm Lưu.
- Đồng bộ APP_VERSION hiển thị toàn hệ thống từ V1.5.24 lên V1.5.27.
- Không thay đổi SQL/database schema.

## [V1.5.26]
- Lich cua doi thu duoc chia thanh 3 cot/ngay: Hom nay, Ngay mai, Ngay kia.
- Moi ngay chi hien cac khung gio ranh cua doi thu thuoc ngay do.
- Khung gio cua doi thu trung voi gio ranh cua HLV dang xem duoc to xanh de nhan biet nhanh.
- Ap dung cho ca tai khoan Test C1 va HLV that.
- Khong thay doi SQL/database schema, API luu gio ranh hay logic chot lich.

Files sua:
- modules/tournament_competition.py
- templates/tournament_detail.html

## [V1.5.25]
Module: Phòng đấu C1 / chuyển Trận 2 + nhập tỷ số

File sửa:
- modules/tournament_competition.py
- templates/partials/tournament_room_result.html
- static/style.css

Thay đổi:
1. Fix Host bấm “Trận 2” nhưng room không chuyển trạng thái ở Guest:
   - Reset room Trận 2 theo chính room_id thay vì ràng buộc thêm host_user_id + guest_user_id.
   - Giữ bước verify DB có tournament_match_id mới, status=waiting_ready, guest_ready=False trước khi báo thành công.
   - Cache room vẫn được xóa để polling Host/Guest nhận state mới.
2. Ô nhập tỷ số C1/TEST C1:
   - Chữ số lớn hơn, in đậm, căn giữa, dễ nhìn hơn.

Không thay đổi SQL/database schema.

## [V1.5.24]
Quick Match hiện tại:
- Nút Tìm Nhanh kích hoạt cửa sổ tìm trong 30 phút.
- Chỉ ghép người Online thật.
- Đối thủ phải đã bật Tìm Nhanh trong 30 phút hoặc đang ở phòng một mình chờ.
- Loại người đang có trận, đang gửi invite khác, phòng đã có người, Admin.
- Ưu tiên: cùng Rank -> lệch <=300 -> <=500 -> <=1000 -> <=2000 RP.
- Quá 2000 RP không ghép.
- Nếu chưa có ứng viên, vẫn giữ trạng thái tìm 30 phút.

C1 Trận 2:
- Đổi nhãn nút thành "🏆 Trận 2".
- Chỉ Host/Admin được bấm chuyển sang Trận 2.
- Guest ở màn kết thúc Trận 1 thấy "Chờ Chủ phòng mở Trận 2".
- Khi Host bấm:
  + giữ nguyên room_id, Host, Guest
  + chuyển tournament_match_id sang leg 2 đúng cặp
  + status = waiting_ready
  + guest_ready = false
  + reset CLB và tỷ số room
- Backend đọc lại DB để verify toàn bộ trạng thái trước khi báo thành công.
- Dọn cache room để Guest polling nhận thay đổi ngay.
- Guest nhận notification "Trận 2 đã sẵn sàng".
- Sau polling, Guest thấy nút Sẵn Sàng.

Không thay đổi BXH, kết quả Trận 1, RP/Rank, thưởng GĐ1.
