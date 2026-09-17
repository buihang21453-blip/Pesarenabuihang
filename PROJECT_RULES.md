## V1.6.27
- Bảng đối thủ GĐ2 dành riêng cho Admin phải đọc trận league đã lưu, tuyệt đối không gọi random/sinh lịch lại.
- Tier gắn thành viên, CLB và Pot CLB tra từ phân bổ hiện hành để phản ánh vé đổi CLB.
- Danh sách trước công bố chỉ dành cho Admin; không tiết lộ lịch đối thủ bí mật cho HLV.
- Không đụng dữ liệu BXH, vé, trận đã xác nhận và hai tài khoản test.

## V1.6.26
- Host rảnh được tính tự động: HLV active thuộc giải, có Host, online theo heartbeat, không tham gia phòng đang hoạt động. Không phụ thuộc host_live_ready.
- Admin và HLV cùng sử dụng API /api/tournaments/<id>/host-ready và tự động refresh 15 giây.
- Không áp dụng quy tắc host rảnh cho thứ hạng, dữ liệu vé, CLB, trận C1 và tài khoản test.

## V1.6.25
- BXH C1 chính thức phải cộng điểm GĐ1 và GĐ2 một lần/trận completed, không cộng Knockout; không tách thành hai BXH độc lập.
- GĐ2 sử dụng cùng Phòng đấu C1, phân nhánh UI theo stage_code; CLB cố định theo HLV lúc bắt đầu, không Random trong phòng.
- Không thay đổi lịch 32 trận, vé đang còn hạn, hoặc dữ liệu BXH test khi chỉnh điểm hiển thị.

## V1.6.24
- GĐ1 mới dùng Random CLB trong phòng; GĐ2/KO phải lấy CLB HLV từ tournament_members và khóa tại thời điểm bắt đầu trận.
- Vé chỉ sử dụng ngoài phòng, không đổi ảnh chụp CLB của trận đang diễn ra; không ảnh hưởng 32 trận và BXH test.

## V1.6.23
- Không sinh lại lịch 32 trận khi hiển thị đối thủ hoặc Random lại CLB.
- Chỉ hiển thị đối thủ GĐ2 khi đã công bố; dữ liệu CLB phải lấy lại từ tournament_members mỗi lần tải trang.
- Bắt đầu GĐ2 không tự hủy vé thưởng; vé hết hiệu lực theo hạn đã cấu hình hoặc do HLV chốt.
- Host rảnh yêu cầu HLV chủ động bật chế độ, online, không ở phòng hoạt động.
- Chạy SQL V1.6.23 trước khi deploy: RPC cũ cấm đổi CLB khi league open.

## V1.6.22 — Quy tắc hiển thị BXH C1

- Tier HLV gắn với user_id từ tournament_members.pot_no; không nhầm với Pot CLB.
- Pot CLB xác định từ tên CLB đang được gán trong tournament_members.fixed_club_name, không từ lịch sử lễ bốc thăm.
- Đổi CLB bằng vé không thay đổi Tier, kết quả, điểm số, thứ hạng hoặc đối thủ.
- Hiển thị trạng thái chưa phân bổ trung thực, không tự gán CLB hay Pot.
- Tài khoản test không được chèn vào BXH C1 chính thức.

## V1.6.21 — Quy tắc phòng đấu

- Luồng phạt RP và timeout Rank không được áp dụng cho phòng C1 (TOURNAMENT_ROOM hoặc match_mode=tournament).
- Mọi route ghi guest phải khóa theo status/guest_user_id và xác minh kết quả trước khi flash thành công.
- Route Rank/Giao hữu không được thay thế note metadata của C1 bằng chuỗi tự do.
- Giới hạn lượt Rank không chặn tham gia hoặc Sẵn sàng Giao hữu.

## V1.6.20 — Kiểm tra ràng buộc DB trong luồng đổi CLB

- Bắt buộc kiểm tra UNIQUE(tournament_id,selected_by) khi viết transaction đổi CLB: nhả quyền sở hữu CLB cũ trước khi gán CLB mới trong cùng transaction, để DB rollback nguyên trạng nếu bất kỳ bước nào lỗi.
- Không tắt / xóa UNIQUE để xử lý lỗi này; không trừ vé riêng; không tự retry một RPC có trạng thái commit chưa xác định.

## V1.6.19
# V1.6.19 — Quy tắc chẩn đoán giao dịch vé

- Không coi mã tham chiếu 10 ký tự là nguyên nhân lỗi; phải đối chiếu log SQLSTATE thật và kiểm tra Production.
- Không tự chạy lại RPC nếu chưa biết lượt trước đã commit hay chưa.
- Không dùng SQL sửa số vé/CLB thủ công khi chưa xác minh dữ liệu thực tế.

## V1.6.18
# V1.6.18 — Ticket transaction rules

- Cài SQL_V1.6.18_ATOMIC_REWARD_CLUB_REROLL.sql trước khi deploy source V1.6.18.
- Không ghi riêng CLB/vé bằng nhiều Supabase REST calls trong luồng reroll; mỗi lượt chỉ có một giao dịch RPC nguyên tử.
- Không tự retry RPC đổi CLB nếu lỗi kết nối sau khi request đã gửi; kiểm tra dữ liệu thực tế trước.

## V1.6.17
# V1.6.17 — Chặn lỗi Admin quay hộ vé CLB

- Các route thao tác đổi CLB/tiêu vé phải bảo vệ cả bước preflight và ghi mã đối chiếu log khi lỗi.
- Rollback phải có điều kiện, không ghi đè dữ liệu đổi bởi phiên khác; tránh retry khi kết quả giao dịch chưa rõ.

## V1.6.16
# Quy ước lỗi khi dùng vé Random CLB

- Không trừ vé trước khi giữ CLB mới và cập nhật CLB thành công.
- Thất bại khi lưu vé phải có bước bù trừ tốt nhất cho bản ghi CLB và log lỗi để Admin kiểm tra.
- Các lỗi hậu xử lý không được làm người dùng tưởng thao tác đã thất bại nếu vé đã được ghi thành công.

## V1.6.15
# Quy ước Admin quay hộ vé CLB

- Chỉ Admin mới được thao tác thay HLV Top 1–3 có vé hợp lệ, còn hạn và chưa chốt.
- Không cấp vé mới; mỗi lần quay thành công trừ 1 vé hiện có của HLV; lưu `actor_user_id` và `actor_role` trong history.
- Áp dụng cùng các điều kiện random, Pot, loại trừ CLB cũ với nút HLV; không động vào lịch thi đấu hoặc BXH.

## V1.6.14
# V1.6.14 — Vé Random lại CLB / UX HLV

- Khi sửa UX cho HLV trên /tournaments phải ưu tiên popup phong cách PES Arena, tránh alert/confirm mặc định nếu có thể.
- Các nút làm thay đổi CLB hoặc tiêu vé phải hiển thị rõ hành động sẽ xảy ra và trạng thái vé còn lại.
- Mọi lần bump version phải đồng bộ APP_VERSION, label giao diện Admin và tài liệu gốc ở thư mục root.
- Đưa chế độ tập dượt vào Công cụ quản trị phụ; màn hình chính không nhắc tới giả lập. Chế độ tập dượt vẫn hoạt động khi Admin chủ động chọn.
- Giảm lớp phủ trên nền sân vận động; hiển thị crowd overlay ở chân trang.
- Khung ánh sáng phủ sân khấu; bục ở lớp đáy, không che nội dung.
- Thẻ bí ẩn giữ nguyên tỉ lệ ảnh; chỉ hiện khung reveal khi có logo được công bố, không chồng 2 dấu hỏi.
- Hai nút RANDOM CLB / Bốc tiếp căn giữa dưới thẻ và bốn đối thủ.
- Không thay đổi route backend, random, dữ liệu Supabase, lịch, vé hay chính sách mở giải.
- URL Storage chưa kiểm chứng được từ môi trường làm việc; cần kiểm tra trực quan trình duyệt sau deploy.


### V1.5.99
- V1.5.99: Lễ bốc thăm GĐ2 do Admin đặt thời gian trong competition_timing.club_draw_at, hiển thị tại vị trí khung đếm ngược GĐ1 cũ; hết giờ không tự Random hoặc mở quyền vé.


### V1.5.86: Không triển khai bản vá từng phần lên giải thật. Kiểm thử đầy đủ luồng tự kết thúc GĐ1, thưởng, Pot, phòng C1 và đồng thời trước khi phát hành Production.
# PROJECT_RULES — PES Arena

**Áp dụng từ:** V1.5.77  
Đây là quy ước bắt buộc khi ChatGPT hoặc người phát triển sửa PES Arena.

## 1. Hiểu đúng loại yêu cầu

- “Đưa vào dự án”, “sửa cho tôi”, “triển khai đi”, hoặc gửi ZIP kèm yêu cầu thay đổi = **sửa source thật**, không tạo mockup/ảnh.
- “Làm ảnh”, “mockup cho tôi xem” = chỉ tạo ảnh, không sửa source.
- “Thử thiết kế/cho xem giao diện” = mockup trước.
- “Phân tích trước rồi sửa” = phải trình bày module, file, dữ liệu/luồng, ảnh hưởng trước rồi mới sửa.
- “Phân tích thôi, chưa sửa” = tuyệt đối không thay file.
- Ảnh giao diện + “đưa kiểu này vào dự án” = ảnh chỉ là tham chiếu; phải sửa code theo ảnh.
- Phản hồi lỗi phải đi tới **vấn đề → nguyên nhân → phương án → file/module tác động**, không chỉ xác nhận.

## 2. Bắt buộc xác định phạm vi trước khi code

Mỗi yêu cầu phải xác định tối thiểu:
1. Module nào chịu trách nhiệm.
2. File nào cần sửa.
3. Route/API/template/JS/CSS/bảng DB/state nào liên quan.
4. Chức năng nào có nguy cơ ảnh hưởng chéo.

Ưu tiên sửa phạm vi nhỏ nhất. Không “tiện tay” refactor khu vực khác trong cùng release chức năng.

## 3. Version và tài liệu

- **Mỗi lần source thay đổi phải tăng version.**
- Version chuẩn nằm ở `APP_VERSION` trong `app.py`; mọi nơi hiển thị/version metadata phải đồng bộ.
- Mỗi release phải cập nhật `CHANGELOG.md`.
- Nếu đổi cấu trúc/module/file/luồng quan trọng phải cập nhật `PROJECT_MAP.md`.
- Nếu phát sinh quy ước phát triển mới phải cập nhật `PROJECT_RULES.md`.
- Release notes riêng `Vx.x.xx_RELEASE_NOTES.txt` có thể tiếp tục duy trì để tương thích lịch sử, nhưng `CHANGELOG.md` là chỉ mục hợp nhất.
- Không tự bịa lịch sử version thiếu bằng chứng. Ghi rõ “không có release note trong source” nếu cần.

## 4. Quy tắc module hóa

- `app.py` là composition root; **không đưa logic feature mới trở lại app.py** nếu đã có module phù hợp.
- Route nên ở route module; nghiệp vụ tái sử dụng ở service; truy cập DB có cấu trúc nên ở repository khi feature đã theo pattern repository/service/routes.
- Không tách module lớn trong cùng release sửa bug nhỏ trừ khi user yêu cầu refactor.
- Khi refactor HTML phải giữ nguyên `id`, `class`, `data-*`, form action, endpoint, biến Jinja và JS hook trừ khi yêu cầu thay đổi chúng.
- `templates/tournaments.html` chỉ là orchestrator; sửa từng khu vực C1 trong `templates/tournament/...` theo `PROJECT_MAP.md`.
- `modules/tournament_competition.py` chỉ là composition root C1; không đưa nghiệp vụ mới trở lại file này. Sửa đúng partition trong `modules/tournament_competition_parts/` và giữ thứ tự đăng ký `core → admin → test_support → rooms → league → scheduling → rewards`.

## 5. Quy tắc C1 / Tournament

- Hai tài khoản test của dự án phải được kiểm tra **cả hai**, không chỉ một tài khoản.
- Với thay đổi hiển thị/quyền/presence liên quan giải, kiểm tra thêm **Admin** và HLV thật nếu logic khác test.
- Test C1 phải dùng dữ liệu/luồng sandbox đúng thiết kế, không làm bẩn BXH/lịch giải thật.
- Không tạo/sửa DB trong GET/render chỉ để “tự chữa” UI, trừ khi có thiết kế nghiệp vụ rõ ràng và được đánh giá trước.
- State phòng C1 (`waiting_ready`, `playing`, `waiting_confirm`, `confirmed`, v.v.) là vùng rủi ro cao. Sửa chuyển state phải kiểm tra cả Host và Guest.
- Khi thay đổi lịch/Stage/Random CLB/thưởng phải kiểm tra luật giải hiện hành, không dùng giả định cứng từ version cũ.

### Quy tắc vận hành GĐ2 từ V1.6.2
- Có thể sinh và công bố đối thủ ngay khi đủ 16 CLB gốc hợp lệ; pha vé thưởng không khóa việc sinh/công bố lịch.
- Sau khi sinh, đối thủ phải cố định; reroll vé thưởng chỉ được thay CLB của HLV, tuyệt đối không tái sinh/xóa/sửa `tournament_matches`.
- Pha vé đóng khi cả 3 HLV có vé bấm chốt/dùng hết vé hoặc đến deadline do Admin đặt.
- Không mở GĐ2 nếu chưa có đúng 32 trận, mỗi HLV 4 trận, đủ 3 Tier, không trùng đối thủ và lễ công bố chưa hoàn tất.
- Admin có thể ép thời điểm bắt đầu sớm, nhưng không được bỏ qua các kiểm tra lịch/đối thủ; vé chưa dùng sẽ hết hiệu lực khi Admin mở GĐ2 ngay.
- Các mốc thời gian GĐ2 dùng UTC+7 khi nhập từ `datetime-local` và phải được bảo toàn khi sửa các mốc GĐ1 khác.

### Test tối thiểu cho chức năng Host/Sảnh chờ
- TK test A có Host + online + không ở room → TK test B và Admin nhìn thấy A.
- A vào room active → A biến mất khỏi Host đang rảnh.
- A hoàn tất/rời room → A xuất hiện lại nếu còn online.
- Offline/quá timeout → không hiển thị.

## 6. Database / SQL

- Không tạo migration nếu thay đổi chỉ là giao diện hoặc logic không cần schema.
- Nếu cần SQL: nêu rõ bảng/cột/index/RPC bị tác động và khả năng rollback trước khi thực hiện.
- Không xóa dữ liệu production để “fix nhanh”.
- Migration mới phải có tên/version rõ ràng và cập nhật tài liệu liên quan.
- Không đưa secret, service key, password hoặc `.env` thật vào ZIP/repository.

## 7. Kiểm thử bắt buộc trước bàn giao

Tùy phạm vi, phải thực hiện các kiểm tra khả dụng trong môi trường:
- Python syntax/compile cho file Python đã sửa.
- Import/startup smoke test nếu có thể mà không cần secret production.
- Jinja parse/render syntax cho template đã sửa ở mức có thể.
- Kiểm tra endpoint/form action/JS selector không bị mất khi refactor.
- Grep version để phát hiện version cũ bị bỏ sót ở vị trí cần đồng bộ.
- Với logic state: đọc lại DB/state sau mutation nếu nghiệp vụ cần xác nhận thành công.
- Không tuyên bố “đã test 2 tài khoản thật trên server” nếu chỉ kiểm tra source tĩnh. Phải phân biệt **code inspection/test local** với **test runtime production**.

## 8. Đóng gói ZIP

ZIP bàn giao **không được chứa file tạm/cache/artifact không cần thiết**, gồm tối thiểu:
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `*.tmp`, `*.temp`, `*.bak`, `*.swp`
- `.pytest_cache/`, `.mypy_cache/`
- file build/debug phát sinh không thuộc source

Không đóng gói thêm một thư mục cha thừa nếu baseline trước đó là source ở root ZIP. Giữ cấu trúc deploy tương thích.

## 9. Quy tắc giao diện

- Giữ ngôn ngữ thiết kế PES Arena hiện tại trừ khi user yêu cầu đổi style.
- Responsive phải được xem xét khi thêm menu/card/bảng.
- Không dùng popup hệ điều hành (`window.alert/confirm`) nếu khu vực đã có UI modal/toast của PES Arena, trừ khi user yêu cầu.
- Không làm nút/card lớn chiếm diện tích nếu chức năng chỉ là điều hướng phụ.
- Menu nhanh giải hiện dùng thứ tự: **📊 BXH → 📅 Lịch của tôi → 🏟️ Sảnh chờ → 🎮 Phòng đấu C1**.
- Menu nhanh không dùng `is-active`, viền vàng cố định hoặc vạch vàng 3px; vàng chỉ dùng làm hover/điểm nhấn theo thiết kế hiện hành.

## 10. Quy tắc bàn giao

Mỗi bản bàn giao phải nói rõ:
- Version cũ → version mới.
- File/module đã sửa.
- Database/SQL có hay không.
- Những gì đã kiểm tra thực tế.
- Những gì **chưa thể kiểm tra runtime** nếu môi trường không có production credentials.
- Link ZIP cuối cùng.

Không tuyên bố đã sửa/tạo ZIP nếu file chưa thực sự tồn tại và chưa kiểm tra.

## 11. Thứ tự ưu tiên khi có xung đột

1. Không làm mất dữ liệu / không phá production.
2. Đúng nghiệp vụ và state.
3. Không phá chức năng đang chạy.
4. Phạm vi thay đổi nhỏ, dễ rollback.
5. Test được.
6. Sau đó mới tối ưu cấu trúc hoặc thẩm mỹ.


## Quy tắc module hóa `tournament_competition`
- Khi tách/mở rộng `tournament_competition_parts`, phải kiểm tra dependency chéo giữa các partition, không chỉ compile từng file.
- Helper/hằng số được tham chiếu chéo phải có mặt trong shared namespace cuối cùng.
- Sau khi đăng ký toàn bộ partition phải đồng bộ shared namespace về từng partition để bảo toàn forward-reference của monolith cũ.
- Bắt buộc kiểm tra các route Admin, Test Support, Room, League, Scheduling và Rewards sau thay đổi cấu trúc.


## Quy tắc duyệt IP từ V1.5.84
- Player mới trùng IP đăng ký hoặc IP gần nhất với player khác: không tự duyệt, chuyển `pending`.
- Player approved truy cập từ IP đang trùng: chuyển `pending`; Admin được cảnh báo.
- 2 tài khoản test do Admin quản lý và tài khoản Admin được loại khỏi cơ chế chặn tự động.
- Khi chặn vì IP phải cho người chơi thấy hướng liên hệ Admin + QR Zalo.
- Admin có thể gửi notification riêng tới từng tài khoản; ưu tiên mẫu có sẵn trước khi nhập nội dung tùy chỉnh.


## Quy tắc thay HLV giữa giải
- Không xóa hoặc reset kết quả đã hoàn thành khi thay HLV.
- HLV mới kế thừa suất thi đấu: CLB/Pot/seed, lịch/đối thủ, tỷ số/BXH/tiến độ.
- Phải lưu snapshot lịch sử trước khi chuyển owner để Admin truy được ai là người thực sự đá kết quả cũ.
- Không kế thừa lịch rảnh; HLV mới phải đăng ký lịch mới.
- Không phát lại reward đã được cấp cho suất.
- Không cho thay khi HLV cũ đang ở phòng C1 active hoặc HLV mới đã có lịch sử trận trong cùng giải.
- Mọi thay HLV phải ghi `admin_action` và cập nhật `replacement_history`.

### Layout V1.5.84
- Không ẩn QR Zalo hoặc cắt nội dung phòng đấu để ép giao diện vừa màn hình; ưu tiên giảm khoảng trống, giữ scroll trang khi cần.

### V1.5.84
- Chỉnh topbar phòng đấu phải giữ nguyên ID chia sẻ, room code, logo và route; responsive không cắt nội dung.


V1.5.84: Bản bảo vệ dữ liệu GĐ2, chưa hoàn thành toàn bộ yêu cầu; không triển khai lên giải thật trước kiểm thử end-to-end.

### V1.5.85 – An toàn GĐ2
Không tự mở GĐ2 theo thời gian; Admin xác nhận khi đủ dữ liệu và đến mốc bắt đầu. Không cho kết thúc GĐ2 khi chưa xác nhận đủ 32 kết quả. Kiểm thử E2E trước Production.

V1.5.87 is a partial artifact only; do not deploy before stage1 automation, test account parity and DB integration tests.

V1.5.87: không đưa lên Production khi chưa kiểm thử luồng giao dịch thưởng/chia Pot trên Supabase.

- V1.5.87: Không đánh dấu bản phát hành production nếu chưa kiểm chứng giao dịch thưởng và dữ liệu giải thật; kiểm tra đầy đủ Pot trước khi khóa.


### V1.5.96 – Bảo vệ Random CLB theo lượt
- Hạng quay quân căn cứ `seed_no` (BXH GĐ1), không sử dụng thứ tự hoàn tất sớm.
- Một giải chỉ dùng một cơ chế phân CLB gốc tại một thời điểm; Random toàn bộ không được ghi đè một phiên theo lượt đang dở.
- Chỉ random khi đủ 16 HLV chính thức, Tier 5–6–5, GĐ1 completed, GĐ2 draft/pending, chưa có lịch/trận. Một lượt sử dụng một RPC transaction; frontend không là lớp bảo vệ duy nhất.
- Tier 1→Pot 3, Tier 2→Pot 2, Tier 3→Pot 1; CLB không trùng và vé thưởng sớm 2/1/1 không trừ khi random gốc. Chỉ mở vé sau khi đủ 16 CLB.
- Muốn đổi thứ tự/mode giữa chừng, thu hồi theo các chốt bảo vệ trước; không xóa lịch sử hoặc sửa thưởng/GĐ1.

### V1.6.0 – Ràng buộc lịch GĐ2
- Với Tier HLV 5–6–5, từng HLV phải đá 4 trận gặp 4 người khác nhau và có đối thủ thuộc cả Tier 1/2/3 trong tổng 4 trận. Kiểm tra toàn lịch trước ghi và khi mở giải. Không chấp nhận thuật toán tối ưu mềm hoặc giới hạn đủ 3 Tier trong 3 trận đầu.

### Quy tắc Preview Lễ bốc thăm từ V1.6.3
- Màn `Admin Preview` là read-only: không được Random, sinh lịch, công bố hoặc mở GĐ2 từ màn hình preview.
- Preview phải dùng cùng dữ liệu live của giải để Admin kiểm tra bố cục trước khi livestream, nhưng không được tạo side effect database.
- Hai phần preview phải tách rõ: `Random CLB` và `Random đối thủ`; có thể chuyển qua lại và bật toàn màn hình.
- Khi cần thao tác thật, Admin quay về `GĐ2 · Pot / CLB / Lịch`; không đặt chức năng quản trị nguy hiểm trên màn hình trình chiếu.


### Quy tắc điều hành Lễ bốc thăm từ V1.6.4
- Chế độ **Điều hành thật** được phép ghi dữ liệu; mọi nút phải qua route Admin có kiểm tra trạng thái.
- Chế độ **Giả lập** tuyệt đối không ghi database, không trừ vé, không thay đổi CLB/lịch/trạng thái giải.
- Không xóa lịch GĐ2 nếu stage đã mở/completed hoặc bất kỳ trận GĐ2 nào không còn `pending`.
- Khi muốn làm lại trước giờ thi đấu: bắt buộc Thu hồi đối thủ trước, sau đó mới Thu hồi CLB.
- Không dùng giao diện/JS để bỏ qua các kiểm tra backend của 16 HLV, Tier 5–6–5, 32 trận, 4 trận/HLV và đủ 3 Tier.

### V1.6.5 – Luật thao tác lễ bốc thăm
- CLB gốc: đúng 1 lần bấm = 1 HLV, thứ tự 16→1; đối thủ: đúng 1 lần bấm = công bố 4 đối thủ của 1 HLV, thứ tự 1→16. Không nhầm công bố với sinh lại trận. Không vượt ràng buộc/ghi đè dữ liệu giải đã có.

### Logo GĐ2 – V1.6.8
- Đọc `clubs_import` trước, chỉ fallback sang `teams` nếu nguồn chính thiếu URL; giữ nguyên 24 CLB và tên Pot trong mã.
- Không đưa ảnh minh họa thành logo CLB chính thức; không tạo đường dẫn Storage giả cho club chưa có file.
- Chỉ tích hợp asset nền WebP sau khi biết URL/đường dẫn thật người dùng upload; tuyệt đối không lưu Supabase credentials trong source.

### Giao diện Lễ bốc thăm từ V1.6.10
- Giữ đúng một nút chính giữa sân khấu mỗi pha: RANDOM CLB hoặc Bốc tiếp; ẩn nút không thuộc chế độ Live/Simulation.
- Logo CLB dùng dữ liệu clubs_import/teams đã đồng bộ; asset WebP trang trí lấy từ Supabase, không hardcode logo mới.
- Ảnh lỗi phải có nền CSS dự phòng; không sử dụng toàn bộ spritesheet làm một icon.


### Quy tắc GĐ2 từ V1.6.11
- Có thể sinh bí mật 32 trận ngay khi GĐ1 xong và Tier HLV 5–6–5 đã khóa.
- Random/đổi CLB không được sửa lịch đối thủ đã sinh.
- Đối thủ chỉ hiện cho HLV sau công bố hoặc khi GĐ2 mở.
