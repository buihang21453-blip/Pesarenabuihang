## V1.6.36 — Cập nhật hướng dẫn công khai RP và Zcoin
- Thay phần giải thích công thức RP chi tiết trong Hướng dẫn bằng giới hạn lượt Rank, chống farm, thưởng chuỗi thắng và thưởng hoạt động tuần đã công khai.
- Thêm phần Zcoin: điểm danh, Gift Code, phần thưởng sự kiện, Ví, Cửa hàng, Lucky Box; liên kết đến các trang người chơi.
- Không công khai hệ số RP, tỷ lệ CLB/Lucky Box, quy tắc vận hành nội bộ hoặc cấu hình Admin. Không thêm hướng dẫn C1.
- Chỉ thay đổi template Hướng dẫn, version và tài liệu; không thay đổi logic hay SQL.

## V1.6.35 — Khôi phục chỉnh/Import tỷ lệ Rank; sửa gửi thông báo Admin
- Mở module RANK_CLUB_TIER_WEIGHTS trong Admin → Hệ thống: chỉnh 10 Rank, import JSON/Python literal, export JSON, validate 100% mỗi Rank.
- Lưu system_settings rank_club_tier_weights và làm mới bộ đệm; không ảnh hưởng trận cũ.
- Sửa lỗi HTTP 500 của tuyến gửi thông báo: thay hai hàm không tồn tại bằng decorator quyền và get_user hiện có.
- Không thay đổi schema/SQL.

## V1.6.34 — Sảnh chờ: sửa màu trùng giờ, chuyển chế độ Admin

- Lịch của tôi hiển thị xanh dương; chỉ khung giờ đối thủ trùng chính xác ngày và giờ với lịch của tôi mới xanh lá. Khắc phục hiểu nhầm do tất cả giờ cá nhân đều màu xanh lá.
- Admin có thanh chọn ở đầu trang: Lịch rảnh toàn bộ 16 HLV / Góc nhìn HLV; mặc định hiển thị tổng quan, mỗi lần chỉ hiển thị một phần.
- Chọn HLV qua danh sách hoặc liên kết tại bảng tổng quan sẽ chuyển sang Góc nhìn HLV, không cần cuộn qua 16 HLV.
- Bảng tổng quan không gắn cờ trùng giờ với HLV đang xem; chỉ hiển thị giờ đăng ký.
- Không thay đổi DB, lịch 32 trận, kết quả, BXH, vé hoặc phòng đấu.

## V1.6.33 — Sảnh chờ: lịch rảnh 4 đối thủ và tổng quan Admin 16 HLV

- Khắc phục CSS V1.6.32 bị đặt ngoài thẻ style khiến khối Lịch của tôi không có định dạng đúng.
- Truy vấn lịch rảnh theo lô từ tournament_availability_slots, bao gồm mốc giờ tùy chọn và lịch trận hoàn thành; không bỏ cả 4 thẻ chỉ vì số trận khác bốn.
- Truy vấn trực tiếp lịch GĐ2 đã lưu theo HLV, giữ điều kiện công bố/đã mở giải để không lộ lịch bí mật.
- Sảnh chờ HLV chỉ còn Lịch của tôi và lịch 4 đối thủ GĐ2 (mỗi người ba ngày); loại dải Host khỏi Sảnh chờ.
- Admin thấy bảng giờ rảnh toàn bộ HLV (ba ngày) và có Góc nhìn HLV chỉ đọc bên dưới.
- Nếu truy vấn Supabase thất bại, hiển thị thông báo lỗi thay vì nói HLV chưa đăng ký giờ.
- Không thay đổi DB, lịch 32 trận, tỷ số, BXH, vé hay phòng đấu.

## V1.6.32 — Lịch của tôi trên, lịch 4 đối thủ dưới trong Sảnh chờ

- Hiển thị lịch rảnh đã đăng ký của HLV theo Hôm nay / Ngày mai / Ngày kia phía trên danh sách đối thủ.
- Bên dưới là 4 thẻ đối thủ GĐ2, giữ tên/Tier/CLB/logo/Pot và lịch rảnh 3 ngày của từng người.
- Giờ trùng lịch tô xanh; Admin xem lịch của HLV đã chọn ở cùng bố cục chỉ đọc.
- Không khôi phục trạng thái trận, thao tác xem lịch, tạo trận trong Sảnh chờ; không đổi DB hay lịch 32 trận.

## V1.6.31 — Sảnh chờ C1 gọn: đối thủ, Tier, CLB và khung giờ rảnh

- Thiết kế lại Sảnh chờ thành 4 thẻ đối thủ GĐ2; mỗi thẻ gắn HLV, Tier, CLB hiện tại, logo CLB, Pot và giờ rảnh 3 ngày.
- Giờ trùng lịch của HLV được tô xanh và tiếp tục cập nhật trực quan khi tick giờ tại tab Lịch của tôi.
- Bỏ danh sách phòng đang thi đấu, bảng trạng thái trận, link xem lịch và toàn bộ nút tạo/vào trận khỏi Sảnh chờ. Các chức năng điều hành phòng vẫn tồn tại ở Phòng đấu C1.
- Giữ danh sách Host đang rảnh dạng dải gọn phía dưới, cập nhật tự động như cũ.
- Admin dùng đúng giao diện Sảnh chờ mới ở chế độ chỉ xem; bỏ bảng lịch rảnh trùng lặp dưới trang Admin.
- Không thay đổi 32 trận, quyền vé, BXH, kết quả hay DB.

## V1.6.30 — Ma trận 16 HLV × 4 đối thủ GĐ2 trong 1 màn hình

- Thiết kế lại bảng Admin thành ma trận 5 cột: HLV + Đối thủ 1–4.
- Hiển thị toàn bộ 16 HLV theo 16 dòng cực gọn để theo dõi đồng thời trên một màn hình Full HD.
- Mỗi ô đối thủ hiển thị tên, Tier HLV, CLB, Pot CLB và trạng thái/tỷ số trận.
- Thêm chế độ Toàn màn hình để tối đa diện tích quan sát.
- Không thay đổi lịch 32 trận, BXH, vé hoặc dữ liệu thi đấu.

## V1.6.29 — Bảng 4 đối thủ GĐ2 toàn bộ HLV trên 1 màn hình

- Bổ sung trang Admin riêng hiển thị đồng thời 4 đối thủ GĐ2 của từng HLV trên cùng một màn hình.
- Mỗi HLV hiển thị theo dạng khối riêng: Tier HLV, CLB hiện tại, Pot CLB và 4 thẻ đối thủ.
- Mỗi thẻ đối thủ hiển thị tên HLV, Tier, CLB, Pot CLB, trạng thái trận và tỷ số nếu đã xong.
- Bổ sung nút mở nhanh trang mới từ khu GĐ2 Admin và từ Sảnh chờ C1 (Admin).
- Không thay đổi lịch 32 trận, BXH, vé Random lại CLB hoặc dữ liệu kết quả.

## V1.6.28 — Admin xem Sảnh chờ C1 như HLV (chỉ xem)
- Thêm route Admin /admin/tournaments/<id>/lobby với lựa chọn góc nhìn một HLV đang tham gia giải.
- Dùng cùng dữ liệu Sảnh chờ, 4 đối thủ, CLB/Pot/Tier, Host rảnh và phòng đang chạy với HLV.
- Ẩn các form mở trận và công bố đối thủ trong chế độ Admin; không thay đổi session hay thao tác thay HLV.
- Hiển thị giờ rảnh của HLV và đối thủ; Host được cập nhật mỗi 15 giây.
- Thay link mở Sảnh chờ ở Admin GĐ2 và menu nhanh của Admin bằng đường dẫn Admin riêng. Không cần SQL.

## V1.6.27 — Bảng đối thủ GĐ2 theo từng HLV dành cho Admin
- Thêm giao diện riêng trong Admin → GĐ2: chọn HLV, xem đồng thời bốn thẻ đối thủ hoặc toàn bộ HLV.
- Hiển thị Tier HLV, CLB hiện tại, Pot CLB, logo nếu có, trạng thái trận và tỷ số đã xác nhận.
- Tải từ lịch league đã lưu; CLB cập nhật khi Admin bấm làm mới; không sinh lại lịch hay tác động vé, BXH.
- Không cần SQL mới.

## V1.6.26 — Host rảnh tự động
- Host đang rảnh = HLV active có Host, online theo heartbeat và không tham gia phòng đang hoạt động; bỏ điều kiện bật rảnh.
- Xóa nút bật/tắt chế độ rảnh trong Sảnh chờ; API và danh sách Admin tiếp tục cập nhật tự động 15 giây.
- POST bật/tắt cũ tương thích nhưng không ghi dữ liệu; loại bỏ đọc host_live_ready khỏi các luồng hiển thị.
- Giữ nguyên phòng C1, BXH, vé, lịch 32 trận; không cần SQL.

## V1.6.25 — BXH C1 cộng dồn & phòng C1 GĐ2
- BXH công khai /tournaments hiển thị Điểm GĐ1, Điểm GĐ2 và Tổng điểm C1; cộng đúng một lần chỉ những trận completed của stage1/league.
- BXH trung tâm /tournaments/<id> hiển thị cùng 3 cột từ nguồn _combined_ranking; Knockout không cộng điểm.
- Phòng C1 GĐ2 giữ nguyên route và xác nhận kết quả, bổ sung hướng dẫn điểm GĐ2 cộng BXH chung; không tạo phòng GĐ2 riêng.
- CLB theo HLV vẫn lấy mới trước trận, khóa lúc bắt đầu; không làm mất vé hoặc thay đổi 32 trận.
- Không SQL mới; không ảnh hưởng dữ liệu trận đã xác nhận hoặc tài khoản test.

## V1.6.24 — Phòng C1 GĐ2 sử dụng CLB gắn với HLV
- Tách UI phòng GĐ2/Knockout khỏi Random CLB GĐ1, bao gồm cả giao diện polling realtime.
- Trước trận hiển thị CLB hiện tại từ tournament_members; vé đổi CLB trước giờ thi đấu không làm dùng đội cũ.
- Chủ phòng bắt đầu trận khi đủ hai HLV và CLB hợp lệ; server khóa CLB cho trận, không trừ vé, không random và không đụng 32 trận.
- Giữ quy trình Chủ phòng nhập tỷ số, Khách xác nhận và GĐ1/test độc lập.
- Không thay đổi cấu trúc database; dự án vẫn cần các SQL migration trước đó nếu chưa triển khai.

## V1.6.23 — Đối thủ GĐ2, Host rảnh, mở giải giữ vé
- Hiển thị bốn đối thủ từ lịch 32 trận đã lưu, Tier HLV, CLB hiện tại, Pot, logo, Zalo, trạng thái và nút trận khi GĐ2 mở.
- Cho Admin mở GĐ2 ngay mà không chốt/hủy vé chưa dùng.
- Host rảnh yêu cầu bật chế độ rảnh, online và không ở phòng; thêm bảng Admin cập nhật trực tiếp.
- Không tạo lại lịch. Cần chạy SQL_V1.6.23_KEEP_TICKETS_AFTER_LEAGUE_START.sql để RPC cho phép dùng vé khi league open.

## V1.6.22 — BXH C1: Tier HLV và Pot CLB

- BXH chính tại /tournaments hiển thị công khai Tier HLV, CLB đang sở hữu và Pot CLB ở từng dòng, kể cả tài khoản không phải Admin.
- Dữ liệu lấy trực tiếp từ tournament_members theo user_id, Pot tra từ pool C1 24 CLB; cập nhật tự nhiên theo mỗi lượt tải trang sau khi đổi CLB bằng vé.
- Giữ nguyên cách cộng điểm, sắp xếp BXH, 2 tài khoản test riêng biệt, lịch GĐ2 và cơ chế vé.
- Làm rõ cột Pot cũ trong chi tiết Admin thực tế là Tier HLV; tăng colspan phù hợp.
- Không cần SQL migration.

## V1.6.21 — Kiểm tra và sửa Phòng đấu / Phòng C1

- Ngăn cơ chế offline và auto-timeout 30/60 phút của Rank đóng phòng C1, phá note hoặc trừ RP / ghi nhận bỏ cuộc sai loại trận.
- Sửa nhận phòng C1: chỉ ghi khách khi phòng waiting_ready và guest_user_id còn trống; không reset ready khi nhận lặp; chặn ghi đè khách khi có race. Bấm Sẵn Sàng cũng kiểm tra status và đúng khách ở thời điểm ghi.
- Chặn endpoint kick khách của Rank xóa metadata TOURNAMENT_ROOM; ẩn nút Rank kick ở phòng C1.
- Không áp giới hạn Rank/ngày khi vào phòng Giao hữu qua link, bấm Sẵn sàng hoặc rời phòng; luồng Rank giữ nguyên.
- Không chỉnh tournament_matches, BXH, lịch 32 trận hay ticket RPC. Không yêu cầu migration SQL mới.

## V1.6.20
# V1.6.20 — Sửa xung đột UNIQUE khi dùng vé Random CLB

- Kiểm toán SQL V1.6.18: hàm giữ CLB mới trước khi nhả CLB cũ dù tournament_clubs ràng buộc UNIQUE(tournament_id,selected_by), gây 23505 và rollback vé/CLB.
- SQL V1.6.20 thay thế đúng hàm RPC: chọn CLB mới đang trống, nhả CLB cũ, giữ CLB mới, cập nhật member, trừ vé và lưu lịch sử trong cùng một transaction; mọi lỗi rollback toàn bộ.
- Không thay đổi route HLV/Admin, số vé, danh sách Pot, lịch 32 trận, hay BXH. Bắt buộc chạy SQL V1.6.20 trước khi triển khai web.

## V1.6.19
# V1.6.19 — Chẩn đoán lỗi RPC Random vé CLB

- Phân biệt RPC chưa cài, sai quyền service_role, lỗi schema/SQLSTATE, lỗi quy tắc nghiệp vụ và lỗi kết nối không rõ trạng thái commit.
- Thêm log mã giao dịch + SQLSTATE; không tự retry khi không xác nhận được giao dịch.
- Chấp nhận cả định dạng JSON object và một object trong mảng do API trả về.
- Thêm SQL chẩn đoán CHỈ ĐỌC, không đổi CLB, vé, lịch.

## V1.6.18
# V1.6.18 — Đổi CLB & trừ vé bằng giao dịch SQL duy nhất

- Sửa chức năng HLV tự dùng vé và Admin quay hộ: thay luồng ghi nhiều API bằng RPC PostgreSQL nguyên tử, hoặc hoàn thành cả đổi CLB/trừ vé/lịch sử/trả CLB cũ, hoặc rollback toàn bộ.
- Một lượt chỉ gọi RPC một lần; không tự retry khi kết quả giao dịch chưa rõ.
- Báo rõ nếu SQL V1.6.18 chưa cài; giữ nguyên 32 trận và dữ liệu hiện hữu.
- SQL bắt buộc phải chạy trước khi deploy source.

## V1.6.17
# V1.6.17 — Chặn lỗi Admin quay hộ vé CLB

- Bỏ preflight Admin quay hộ gọi DB ngoài try/except; route nay chuyển toàn bộ xác thực vào shared reroll đã bảo vệ.
- Gắn mã thao tác và nhãn bước lỗi vào log/flash để tra traceback Vercel; rollback CLB có điều kiện nhằm không ghi đè phiên khác.
- Không SQL mới; chưa xác nhận lỗi Production nếu thiếu log Vercel.
- Thêm 7 smoke test giả lập cho đường Admin (thành công, lỗi đọc DB, hết vé, pool hết, lỗi cập nhật/lưu vé).

## V1.6.16
# V1.6.16 — Fix HLV dùng vé Random CLB bị trang lỗi

- Bảo vệ route POST của HLV và Admin quay hộ: lỗi dữ liệu được ghi log và đưa về đúng trang với thông báo thay vì trang lỗi máy chủ.
- Chỉ lưu trừ vé khi đã giữ được CLB mới và cập nhật CLB thành công; kiểm tra kết quả trả về từ các thao tác ghi Supabase.
- Nếu cập nhật CLB hoặc lưu vé không thành công, cố gắng khôi phục CLB cũ và giải phóng CLB mới đã giữ.
- Sau khi lượt quay thành công, sự cố dọn CLB cũ hoặc tự mở GĐ2 được ghi log riêng thay vì biến lượt quay thành trang lỗi.
- Giữ nguyên route/form của HLV, nút Admin quay hộ, pool theo Pot, 32 trận và bảng xếp hạng.

## V1.6.15
# V1.6.15 — Admin quay hộ vé thưởng CLB

- Bổ sung route POST Admin xác thực quay hộ một vé cho HLV Top 1–3 GĐ1.
- Tái sử dụng chính xác luồng đổi CLB hiện hữu của HLV: kiểm tra hạn, vé, trạng thái đã chốt, đủ 16 CLB, Pot, CLB cũ đã bỏ.
- Bổ sung nút Quay hộ · 1 vé riêng từng HLV trong Admin và màn điều hành lễ; có xác nhận trước khi trừ vé.
- Lưu actor_user_id/actor_role=admin trong lịch sử lượt quay để phân biệt người thao tác.
- Không thay đổi lịch đối thủ, bảng xếp hạng, schema hay việc cấp vé; giữ nguyên SQL V1.6.13.

## V1.6.14
# V1.6.14 — Vé Random lại CLB / UX HLV

- Bổ sung thẻ hiển thị vé Random lại CLB cho HLV trên /tournaments.
- Hiển thị hạn dùng vé theo mốc Admin thực tế và trạng thái sẵn sàng / đang dùng / đã chốt / hết hạn.
- Bổ sung popup xác nhận phong cách PES Arena và overlay “Đang Random CLB…” khi sử dụng vé hoặc chốt CLB.
- Làm rõ luồng dùng vé: nhận CLB đầu tiên miễn phí → dùng vé đổi CLB → chốt CLB cuối cùng.
- Đưa chế độ tập dượt vào Công cụ quản trị phụ; màn hình chính không nhắc tới giả lập. Chế độ tập dượt vẫn hoạt động khi Admin chủ động chọn.
- Giảm lớp phủ trên nền sân vận động; hiển thị crowd overlay ở chân trang.
- Khung ánh sáng phủ sân khấu; bục ở lớp đáy, không che nội dung.
- Thẻ bí ẩn giữ nguyên tỉ lệ ảnh; chỉ hiện khung reveal khi có logo được công bố, không chồng 2 dấu hỏi.
- Hai nút RANDOM CLB / Bốc tiếp căn giữa dưới thẻ và bốn đối thủ.
- Không thay đổi route backend, random, dữ liệu Supabase, lịch, vé hay chính sách mở giải.
- URL Storage chưa kiểm chứng được từ môi trường làm việc; cần kiểm tra trực quan trình duyệt sau deploy.

## V1.6.11 – Sinh lịch bí mật trước Random CLB & căn giữa nút sân khấu
- `Sinh lịch GĐ2` giờ chỉ phụ thuộc 16 HLV active + Tier 5–6–5 đã khóa; không cần Random CLB trước.
- 32 trận được lưu bí mật; HLV không thấy đối thủ trước khi tới lượt được công bố hoặc GĐ2 mở.
- Random CLB và vé thưởng chỉ đổi CLB, không thay đổi đối thủ đã sinh.
- Phần 2 `Bốc tiếp` chỉ công bố 4 đối thủ đã lưu, không sinh lại lịch.
- Ép nút `🎲 RANDOM CLB` và `🎲 Bốc tiếp` nằm chính giữa cột sân khấu bằng CSS grid/place-items.
- Không SQL mới.

## V1.6.10 – Tích hợp bộ ảnh WebP GĐ2 và chuyển nút quay về giữa sân khấu
- Dùng URL 8 tài nguyên từ bucket pes-assets/LeBocThamGD2 do chủ dự án cung cấp; giao diện fallback nền CSS/initials khi ảnh lỗi. Bộ spritesheet được khai báo nhưng chưa dùng vì chưa có tọa độ cắt icon.
- Chuyển hai cụm điều khiển từ thanh phía trên vào chính giữa phần sân khấu, dưới nội dung công bố; mỗi pha chỉ có một nút thao tác hiển thị theo mode Live/Simulation.
- Phần 1: RANDOM CLB 16→1. Phần 2: Bốc tiếp 1→16. Không đổi form action, RPC, quyền, thuật toán, luật vé thưởng và cơ chế thu hồi.
- Không xác minh được HTTP đến Supabase trong môi trường đóng gói; cần thử tải 8 asset trong trình duyệt ở Production. Không cần SQL.

## V1.6.9 – Chuẩn hóa mapping logo CLB GĐ2
- Đối chiếu CSV clubs_import 182 hàng: PSV đã có logo psv.png; Porto và RB Leipzig chưa có bản ghi.
- Đồng bộ thêm alias Lille/Como; URL Porto/Leipzig chỉ là fallback chính xác theo người dùng cung cấp.
- Không tự suy đoán URL PSV WebP từ đường dẫn Porto bị gửi lặp; hiển thị nguồn URL dự phòng trên màn hình Admin.
- Không sửa DB/Storage/luật giải; chưa xác thực HTTP Storage trên Production.

## V1.6.8 – Đồng bộ logo Lễ bốc thăm từ clubs_import
- Admin GĐ2 đọc `clubs_import` (read-only) để lấy URL logo của đúng 24 CLB; ưu tiên dữ liệu clubs_import trước `teams`.
- Chuẩn hóa các biến thể tên CLB (Manchester United/Man United, FC Porto/Porto, v.v.) để khớp đúng tên đã chốt trong Pot; không đổi tên hoặc danh sách CLB gốc.
- Nếu clubs_import chưa có bản ghi/URL hoặc không đọc được, thử logo có sẵn trong teams; nếu vẫn thiếu, giao diện hiển thị tên CLB và biểu tượng dự phòng, không phát minh logo.
- Admin có bảng kiểm tra số logo tìm được và danh sách CLB thiếu; ba CLB Porto, RB Leipzig, PSV sẽ được tự phát hiện khi chưa có trong clubs_import, tự có logo khi người quản trị bổ sung.
- Chưa tải bộ asset WebP do người dùng sẽ tự chuyển và upload lên Supabase; không sửa database, Storage, vé thưởng, thuật toán hay lịch đối thủ. Chưa xác minh schema/dữ liệu Supabase Production.

## V1.6.7 – Gom đúng một nút điều hành cho mỗi phần lễ bốc thăm
- Phần 1: giữ một nút 🎲 RANDOM CLB tại thanh điều khiển phía trên sân khấu; mỗi lần bấm bốc CLB cho một HLV theo thứ tự 16→1.
- Phần 2: giữ một nút 🎲 Bốc tiếp tại thanh điều khiển phía trên sân khấu; mỗi lần bấm công bố bốn đối thủ cho một HLV theo thứ tự 1→16.
- Gỡ hai nút bốc trùng khỏi khu vực sân khấu; chế độ giả lập dùng cùng vị trí nút tương ứng, không hiển thị đồng thời.
- Giữ nguyên endpoint POST, quyền Admin, thuật toán, các thao tác quản trị phụ, vé thưởng và dữ liệu giải. Không cần SQL mới.

## V1.6.6 – Giao diện sân khấu tối giản và avatar HLV
- Sân khấu mỗi pha có đúng một nút chính: CLB 16→1 / Đối thủ 1→16; chuyển các thao tác quản trị khác vào mục thu gọn, vẫn giữ đầy đủ endpoint và khóa an toàn.
- Hiển thị avatar thật từ users.avatar_url cho danh sách, HLV trên sân khấu và bốn đối thủ; khi không có ảnh/ảnh lỗi, dùng chữ cái đầu.
- Chỉ hiển thị logo CLB khi công bố kết quả CLB hoặc nhận diện CLB của HLV ở pha đối thủ; lấy URL từ danh mục teams Supabase hiện hữu, nếu không có logo hiển thị biểu tượng và tên CLB; không tự đoán logo. Giao diện thật giữ kết quả CLB vừa bốc trong lúc nút chuẩn bị HLV tiếp theo.
- Giả lập CLB đúng thứ tự 16→1, không ghi DB; chặn bấm nút thật trùng trong lúc đang chờ phản hồi; không thay thuật toán 32 trận, vé thưởng, nghiệp vụ thu hồi hay schema.
- Chưa xác thực hiển thị với dữ liệu/avatar/logo Supabase Production hoặc 2 tài khoản test.

## V1.6.5 – Một nút một lượt bốc thăm
- Điều hành thật: `Bốc CLB tiếp theo` tự cấu hình thứ tự 16→1 ở lần đầu khi chưa phân CLB; mỗi POST phân đúng 1 CLB cho đúng HLV tiếp theo qua RPC V1.5.96; không trừ vé.
- Đối thủ: sau khi sinh đủ 32 trận hợp lệ, chỉ cần `Bốc tiếp`; lần đầu tự khởi động công bố, mỗi lần công bố cả 4 đối thủ của 1 HLV theo hạng 1→16. Không sinh lại lịch, không thay đổi cặp đấu.
- Chặn lịch thiếu 32 trận, trùng cặp, thiếu 4 đối thủ hoặc 3 Tier trước khi công bố; giữ trạng thái cũ nếu ghi database thất bại.
- Sân khấu chỉ thấy đối thủ đã công bố, tránh lộ lịch chưa công bố; giả lập CLB cũng theo 16→1.
- Giữ nguyên thao tác thu hồi đối thủ trước, thu hồi CLB sau; không tự ghi đè dữ liệu khi chuyển từ chế độ khác.
- Không cần migration mới ngoài SQL V1.5.96 đã có. Chưa thử với Supabase Production.

## V1.6.4 – Điều hành trực tiếp & giả lập Lễ bốc thăm GĐ2
- Nâng màn hình Admin Preview thành **Admin Control**: Admin thao tác trực tiếp Random CLB, sinh lịch, bắt đầu công bố, Bốc tiếp và mở GĐ2.
- Bổ sung **Thu hồi đối thủ GĐ2** an toàn trước khi GĐ2 bắt đầu; thao tác này giữ nguyên CLB và vé thưởng.
- Cho phép làm lại theo thứ tự: Thu hồi đối thủ → Thu hồi CLB.
- Bổ sung chế độ **Lễ bốc thăm giả lập** chạy toàn bộ 16 CLB + công bố đối thủ Tier 1→2→3 hoàn toàn trong trình duyệt, không ghi database/không trừ vé.
- Giữ các khóa an toàn: không thu hồi đối thủ khi GĐ2 đã mở hoặc có trận đổi trạng thái/kết quả.

## V1.6.3 – Admin Preview giao diện Lễ bốc thăm GĐ2
- Thêm route Admin read-only `/admin/tournaments/<id>/draw-preview` để xem trước sân khấu Lễ bốc thăm trước khi livestream/vận hành thật.
- Thêm nút `👁 Xem trước giao diện Lễ bốc thăm` ngay đầu khối `GĐ2 · Pot / CLB / Lịch`.
- Preview có 2 chế độ: `Phần 1 · Random CLB` và `Phần 2 · Random đối thủ`, chuyển đổi ngay trên màn hình và hỗ trợ Fullscreen.
- Preview dùng dữ liệu giải hiện tại: 16 HLV, Tier, CLB đã phân, kho CLB còn lại, vé thưởng, 32 trận GĐ2 và tiến độ công bố đối thủ; không có POST/action thay đổi database.
- Hiển thị countdown theo 3 mốc Admin cấu hình: mở lễ, hạn vé thưởng, mở GĐ2.
- Không thay đổi thuật toán V1.6.2: lịch đối thủ vẫn cố định sau khi sinh; vé thưởng chỉ đổi CLB.

## V1.6.2 – Tách lịch đối thủ khỏi vé Random CLB
- Cho phép sinh 32 trận GĐ2 ngay khi đủ 16 CLB gốc hợp lệ, không cần chờ 3 HLV dùng/chốt hết vé thưởng.
- Cho phép bắt đầu công bố đối thủ Tier 1 → Tier 2 → Tier 3 trong lúc vé thưởng vẫn còn hiệu lực.
- Cặp đối thủ sau khi sinh được giữ cố định; reroll vé thưởng chỉ đổi CLB của HLV, không đụng `tournament_matches`.
- Giữ nguyên điều kiện mở GĐ2: lịch hợp lệ, công bố xong và pha vé đóng; Admin mở ngay vẫn có thể đóng vé còn lại.
- Cập nhật giao diện Admin để diễn đạt đúng luồng mới.

## V1.6.1 – Kịch bản Lễ bốc thăm GĐ2, hạn vé và mở GĐ2 theo điều kiện
- Chốt quy trình vận hành: 20:00 17/09/2026 mở lễ → Random CLB gốc đủ 16 theo Tier/Pot → 3 HLV dùng vé đến 12:00 18/09/2026 → bốc đối thủ theo Tier 1→2→3 → mở GĐ2.
- Admin chỉnh được 3 mốc `club_draw_at`, `gd2_reward_ticket_deadline_at`, `league_start_at` trong `competition_timing`; mặc định lần lượt 20:00 17/09, 12:00 18/09, 12:00 18/09 (UTC+7).
- Vé thưởng sớm: chỉ dùng sau đủ 16 CLB gốc; HLV có thể dùng tùy ý hoặc bấm `Chốt CLB cuối cùng`. Chốt sớm làm vé chưa dùng hết hiệu lực; dùng hết vé tự chốt. Đến deadline hệ thống chốt/khóa vé còn lại.
- Sinh lịch/công bố đối thủ chỉ khi pha vé đã đóng; thứ tự công bố HLV là Tier 1 → Tier 2 → Tier 3. Luật V1.6.0 4 trận/HLV, đủ 3 Tier và không trùng đối thủ giữ nguyên.
- GĐ2 tự thử mở ở mốc 12:00 khi đủ 32 trận hợp lệ và công bố xong; có thể mở sớm khi cả 3 HLV vé thưởng đã chốt và lễ công bố hoàn tất. Admin `Bắt đầu GĐ2 ngay` đóng vé còn lại nhưng không bỏ qua kiểm tra lịch/công bố.
- UI Admin có timeline 5 bước; UI HLV có hạn vé + nút chốt; card Giải đấu đổi countdown theo pha. Không schema/SQL mới.
- Kiểm tra local: Python compile + Jinja parse OK; thuật toán lịch validate 500 lượt. Chưa kiểm thử Supabase Production/2 tài khoản test/Admin thật.

## V1.6.0 – GĐ2: bắt buộc gặp đủ 3 Tier trong 4 trận
- Thay thuật toán chấm điểm/xác suất bằng lịch mẫu hợp lệ 4 lượt × 8 trận, hoán vị ngẫu nhiên HLV trong mỗi Tier 5–6–5; mỗi HLV có đúng 4 đối thủ khác nhau, gặp đủ Tier 1/2/3 trên CẢ BỐN trận (không ép đủ trong 3 trận đầu).
- Bộ kiểm tra độc lập xác nhận 32 trận, bốn lượt hoàn chỉnh, mỗi HLV 4 trận, không trùng cặp và phủ đủ 3 Tier; từ chối trước khi ghi dữ liệu nếu sai. Nút mở GĐ2 kiểm tra lại độ phủ của lịch đã lưu.
- Cập nhật nhãn Admin và league_config cho luật chính thức. Không đổi lịch đã tồn tại, lịch GĐ1, CLB, vé hoặc schema DB; không SQL migration.
- Giới hạn hiện hữu: route tạo lịch ghi từng trận qua Supabase, chưa giao dịch atomic cho 32 insert. Nếu một lần ghi thất bại giữa chừng phải kiểm tra và xử lý lịch dở dang trước khi thử lại, không xóa dữ liệu Production tự động.
- Kiểm tra local thuật toán nhiều lần và cú pháp; chưa thử Supabase Production, luồng Admin/2 tài khoản test trên server.

## V1.5.99 – Đồng hồ lễ bốc thăm CLB GĐ2
- Admin đặt lại ngày giờ lễ bốc thăm GĐ2 (giờ Việt Nam) và lưu trong competition_timing.club_draw_at; đồng hồ thay toàn bộ khung tiến trình GĐ1 ở card Giải đấu.
- Đồng hồ chỉ đổi nhãn khi đến giờ, không tự thực thi Random hay can thiệp vé thưởng.

## V1.5.98 – Sửa lỗi thu hồi và Random lại khi giải có HLV dự phòng/ngừng tham gia
- Kết quả chẩn đoán Production: 17 thành viên toàn bộ nhưng chỉ 16 active, đã phân CLB cho 16 người; GĐ1 completed, GĐ2 pending, không có lịch, RPC tồn tại và role có quyền EXECUTE.
- Sửa hai RPC `c1_admin_revoke_tier_clubs` và `c1_admin_rerandom_tier_clubs`: đếm đúng 16 thành viên `status=active` thay vì tất cả bản ghi; vẫn xác minh đủ 16 ID trong danh sách Random và không ghi đè thành viên inactive.
- SQL `SQL_V1.5.98_FIX_ACTIVE_16_REVOKE_RERANDOM.sql` chỉ thay định nghĩa RPC, KHÔNG thực thi thao tác thu hồi/Random, không sửa CLB hay thưởng lúc chạy migration.
- Chưa có log RPC thực tế: lỗi lệch 17/16 được xác nhận từ code và dữ liệu chẩn đoán; còn các ràng buộc khác chỉ xác nhận khi bấm thao tác sau migration. Chưa kiểm thử trên Supabase Production.

## V1.5.97 – Chẩn đoán lỗi thu hồi CLB GĐ2, không thay đổi dữ liệu
- Route `admin_tournament_revoke_clubs`: phân loại mã lỗi RPC (không tồn tại, thiếu quyền, ràng buộc, điều kiện nghiệp vụ) và hiển thị hướng xử lý ngay tại GĐ2; ghi traceback đầy đủ trong log backend nhưng không lộ raw error hoặc khóa cho client.
- Thêm `SQL_V1.5.97_DIAGNOSE_REVOKE_READ_ONLY.sql` để kiểm tra RPC, quyền service_role, tình trạng stage, số HLV, draft 16 người và lịch GĐ2/KO. Chỉ SELECT, không sửa/xóa dữ liệu.
- Chưa xác định lỗi thực tế trên Production khi chưa có mã lỗi/log hoặc kết quả chẩn đoán; không thay thế và không tự chạy lại SQL V1.5.91 trên dữ liệu thật.
- Không thay đổi cơ chế Random, vé thưởng, bảng CLB, DB schema hay các endpoint khác. Chưa kiểm thử Supabase Production / hai tài khoản test.

## V1.5.96 – Gom điều hành Random CLB và thêm Random theo lượt 1–16 / 16–1
- Admin GĐ2: gom Random toàn bộ, cấu hình Random lần lượt, Random hộ, Thu hồi vào một khối; bỏ nút/chỉ dẫn trùng.
- Thứ tự Random theo `tournament_members.seed_no` (hạng BXH GĐ1), không nhầm với thứ tự về đích nhận thưởng sớm. Chọn 1→16 hoặc 16→1; chỉ một HLV đến lượt được Random.
- Chế độ: Admin Random hộ tại GĐ2, hoặc HLV tự Random ở `/tournaments` và trang giải. Chỉ Admin cấu hình; backend xác minh tài khoản đăng nhập và lượt.
- SQL RPC `c1_allocate_one_base_club` chạy trong một transaction, khóa giải trước khi chọn CLB, xác minh Tier 5–6–5 và Pot 3/2/1, chặn CLB trùng, lần bấm lặp, lịch/trận GĐ2, trạng thái sai. Ghi lịch sử, không trừ vé, mở vé Top 1–3 chỉ khi 16 CLB gốc hoàn tất.
- Không cho Random toàn bộ ghi đè phiên Random lần lượt đang dở; muốn chuyển cách phải Thu hồi theo điều kiện bảo vệ V1.5.91. Giữ nguyên tất cả thưởng, lịch sử và dữ liệu GĐ1.
- Bảng Admin có cột hạng BXH GĐ1 và sắp xếp theo hạng; cột thứ tự nhận thưởng sớm phân biệt rõ.
- Phải chạy `SQL_V1.5.96_SEQUENTIAL_CLUB_DRAFT.sql` trước khi sử dụng Random từng người; SQL V1.5.90/91 vẫn cần cho Random toàn bộ/Thu hồi. Chưa kiểm thử Production/Supabase thật.

## V1.5.95 – Xóa nút Random hạng 4–16 đã thay thế ở Admin GĐ2
- Xóa hẳn form/nút ④ Random hạng 4–16 (đã thay thế) khỏi `templates/admin.html`, tránh giao diện chồng lấn nút Random mới.
- Giữ nguyên nút Admin Random lại 16 CLB theo Tier/Pot và Thu hồi CLB; không đổi API, DB, vé thưởng hoặc nghiệp vụ Random. Không có SQL migration.
- Kiểm tra tĩnh nội bộ; chưa kiểm thử trên Production.

## V1.5.94 – Sửa nút Random lại / Thu hồi không phản hồi
- Bỏ hộp thoại `confirm()` của trình duyệt cho hai thao tác Admin GĐ2 theo yêu cầu.
- Hai form POST trực tiếp qua fetch; báo lỗi ngay trong khu GĐ2 (không popup), chỉ tải lại khi backend xác nhận RPC trả đúng 16.
- API giữ nguyên điều kiện an toàn GĐ1/GĐ2, chưa có trận, chưa dùng vé, khóa chọn thủ công; không tự vượt qua chốt chặn.
- POST truyền thống dự phòng đưa Admin về đúng `#c1-admin-gd2`; log lỗi SQL giữ ở server.
- Không thay đổi schema/SQL, dữ liệu giải và thưởng; SQL V1.5.90/91 vẫn phải được chạy trước.
- Kiểm tra tĩnh không tương đương với kiểm thử Supabase Production.

## V1.5.93 – Đưa điều hướng GĐ1/GĐ2/KO lên đầu khu Điều hành giải đấu
- Di chuyển tiêu đề “🎯 Điều hành vòng hiện tại” và ba nút chuyển giai đoạn lên ngay đầu màn Điều hành giải đấu, tránh phải cuộn qua toàn bộ danh sách HLV/lịch.
- Nút dùng đúng URL fragment `/admin#c1-admin-gd1`, `/admin#c1-admin-gd2`, `/admin#c1-admin-ko`; mở liên kết trực tiếp vào đúng tab Admin và đúng giai đoạn, kể cả khi tải lại trang.
- Giữ nguyên các form/API và nghiệp vụ Random/thu hồi, không sửa DB/SQL; chưa xác minh Production.

## V1.5.92 – Phân CLB gốc cho 16 HLV trước khi dùng vé; bổ sung Tier HLV
- Chặn ở backend cả ba route `/club-draft/random`, `/club-draft/accept`, `/club-draft/reward-reroll` cho đến khi Admin hoàn tất Random CLB gốc đủ 16 HLV, xác minh Tier 1→Pot 3, Tier 2→Pot 2, Tier 3→Pot 1; không trừ vé khi bị chặn.
- `/tournaments` và trang giải ẩn nút Random/đổi CLB khi chưa phân đủ CLB, vẫn hiện số vé bảo lưu; khi đủ 16 thì Top thưởng sớm mới được đổi CLB cùng Pot.
- Admin: bảng Theo dõi Random CLB có thêm cột Tier HLV lấy từ `tournament_members.pot_no` (không nhầm với Pot CLB); sửa colspan; cập nhật hướng dẫn trình tự.
- Chặn thao tác Admin thu hồi/Random lại toàn bộ khi đã có vé được sử dụng, tránh ghi đè CLB đổi thưởng. Số dư vé và lịch sử cũ được giữ nguyên.
- Không cần migration mới: dùng lại SQL V1.5.90 và V1.5.91 theo đúng thứ tự từ phiên bản trước. Chưa kiểm thử Supabase Production/2 tài khoản test.

## V1.5.91 – Sửa tab Admin GĐ1/GĐ2/KO và thu hồi CLB GĐ2 (chưa kiểm thử Production)
- Sửa lỗi JS khởi tạo tab trước khi DOM chứa các panel được parse: chuyển sang DOMContentLoaded, kiểm tra panel, duy trì tab giai đoạn sau POST bằng sessionStorage.
- Admin GĐ2 có nút thu hồi 16 CLB đã Random, yêu cầu xác nhận. RPC một giao dịch bảo vệ giai đoạn, lịch/trận, đủ 16 thành viên, đóng chọn CLB thủ công; giải phóng CLB và xóa fixed_club, candidate, selected_club; ghi audit CLB cũ, giữ nguyên vé, skipped, thưởng và kết quả GĐ1.
- Sau thu hồi phải dùng Admin Random lại theo Tier1→Pot3, Tier2→Pot2, Tier3→Pot1. Không tự động mở GĐ2.
- BẮT BUỘC chạy SQL_V1.5.91_ADMIN_REVOKE_CLUBS.sql trước khi dùng nút thu hồi (và SQL V1.5.90 trước nút Random). Chưa kiểm thử Supabase Production/2 tài khoản test.

## V1.5.90 – Admin Random lại 16 CLB đúng Tier/Pot (chưa kiểm thử Production)
- Sửa sai phân bổ CLB: Tier HLV 1 (5 người) → Pot CLB 3; Tier HLV 2 (6 người) → Pot CLB 2; Tier HLV 3 (5 người) → Pot CLB 1.
- Nút Admin Random lại toàn bộ 16 CLB trước khi có lịch/trận GĐ2, xác nhận trước khi chạy và cho phép bấm lại. SQL RPC một transaction: nếu lỗi rollback toàn bộ, kiểm tra 16 user/CLB không trùng, 24 CLB hợp lệ, Stage chưa bắt đầu.
- Bảo lưu số vé thưởng sớm hiện có, ZCoin/Lucky Box và lịch sử; ghi lịch sử trước/sau của từng lần quay. Không cấp/trừ vé khi Admin sửa phân bổ.
- Người dùng đổi CLB bằng vé sau khi sửa chỉ quay trong Pot CLB theo Tier, giữ nguyên cơ chế không quay lại CLB đã bỏ.
- Chặn khởi động/sinh lịch GĐ2 nếu CLB chưa đúng Tier/Pot; vô hiệu nút Random hạng 4–16 cũ hoàn toàn; trước khi sửa, vé Top 1–3 không thể đổi CLB sai Pot.
- **BẮT BUỘC chạy SQL_V1.5.90_ADMIN_RERANDOM_TIER_POT.sql trước khi deploy**; chưa có kiểm chứng Supabase Production/2 tài khoản test.

## V1.5.89 – Bảo lưu vé Random thưởng sớm Top 1–3 (chưa kiểm thử Production)
- Bỏ giới hạn 10/5 phút và cơ chế tự chốt đối với ba HLV nhận vé GĐ1, kể cả state cũ có deadline.
- Top 1–3 tự Random/chốt độc lập; lần Random CLB đầu tiên miễn phí, Random lại chỉ trừ một vé khi có CLB phù hợp.
- Sau khi chốt CLB vẫn dùng vé chưa tiêu để đổi CLB về sau; CLB bỏ qua không xuất hiện lại cho chính HLV đó. Không tự reset dữ liệu/cấp thêm vé.
- Chặn mở lại draft và chặn Admin Random thay Top 1–3; giữ nguyên Random hạng 4–16.
- Bổ sung nút sử dụng vé ngay /tournaments, cập nhật giao diện Admin và route tương thích.
- Dữ liệu: dùng JSON `tournament_settings.club_draft_v2`, không migration SQL. Cần kiểm thử với Supabase và 2 tài khoản test trước khi deploy Production.

## V1.5.88 – Sửa lỗi 500 khi Admin kết thúc GĐ1 (chưa kiểm thử Production)
- Bổ sung SQL migration cho trạng thái `pending` của `tournament_stages` (SQL gốc chỉ cho phép draft/open/locked/completed).
- Hai nút kết thúc GĐ1 dùng chung route: kiểm tra trạng thái, ghi chuẩn bị GĐ2 trước khi hoàn tất GĐ1 và báo lỗi có log thay vì trang 500.
- Không tự động mở GĐ2; giữ kết quả và BXH hiện tại. Cần chạy SQL migration trước deploy, kiểm tra Production và hai tài khoản test trước khi phát hành.

## V1.5.87 – Bổ sung bản vá khôi phục GĐ1 và tab Admin (chưa xác nhận Production)
- Tự hoàn tất GĐ1 có thể chạy lại khi bước chia/khóa Pot bị gián đoạn; kiểm chứng đủ 16 hạng và đúng seed trước khi khóa.
- Tab Admin GĐ1 / GĐ2 / KO tương tác, GĐ2 gồm Pot/CLB và League.
- Chưa xác nhận tính nguyên tử giữa các RPC thưởng, chưa kiểm thử Supabase và 2 tài khoản test thực tế.

## V1.5.87 – bổ sung sau bản partial (chưa kiểm thử tích hợp)
- Nối xác nhận tỷ số GĐ1 với tự kết thúc khi đủ 16 HLV đạt điều kiện và tất cả trận completed.
- Dùng lại engine thưởng có idempotency RPC; tự chia và khóa Pot 5–6–5; GĐ2 giữ pending và đặt lịch mặc định +2 ngày.
- Giữ các chỉnh sửa CLB cố định và khởi động GĐ2 của bản partial.
- Chưa chứng minh an toàn giao dịch toàn chuỗi, chưa kiểm thử Supabase và hai tài khoản test; không triển khai Production.

## V1.5.87 – C1 free-room fixed-club guard (partial, NOT production ready)
- Room C1 tự do lấy CLB cố định của chủ khi GĐ2/KO mở; khách nhận phòng được gán CLB từ tournament_members, không từ client.
- Chặn HLV chưa có CLB cố định vào phòng tự do GĐ2/KO; giữ cơ chế random GĐ1.
- Chưa triển khai tự kết thúc GĐ1, tự thưởng/chia/khóa Pot, quyền đầy đủ TK test hoặc kiểm thử tích hợp với Supabase. KHÔNG triển khai production.

## V1.5.86 – Bản vá bước đầu: bắt đầu GĐ2 ngay và khóa CLB tại phòng theo lịch

- Admin có thể bắt đầu GĐ2 ngay sau khi đủ điều kiện, ghi đè mốc bắt đầu và đặt hạn 7 ngày; vẫn giữ lựa chọn bắt đầu theo lịch.
- Chặn vào phòng theo trận GĐ2/KO nếu giai đoạn chưa mở hoặc HLV thiếu CLB cố định.
- Khi tạo/vào lại phòng theo trận, lấy CLB từ tournament_members; không lấy CLB tùy ý từ form.
- CHƯA hoàn tất: tự kết thúc GĐ1, tự trao thưởng/chia/khóa Pot, khóa CLB ở mọi API phòng C1 tự do, kiểm thử tích hợp.
- KHÔNG đưa bản này lên Production khi chưa hoàn thành các mục còn thiếu.

## V1.5.84 – GĐ2: bản bảo vệ dữ liệu (CHƯA hoàn tất toàn bộ quy trình)
- Kết thúc GĐ1 chuyển GĐ2 sang chuẩn bị, không tự mở thi đấu.
- Sinh lịch chỉ sau khi GĐ1 hoàn tất, Pot khóa, đủ 16 CLB cố định; không sinh đè lịch đã có.
- Kiểm chứng 4 lượt × 8 trận, 32 cặp duy nhất, mỗi HLV đúng 4 trận trước khi ghi dữ liệu.
- Công bố đối thủ lượt thứ tư; chặn kết thúc GĐ2 khi chưa đủ 32 trận.
- Chưa hoàn thành: mốc hai ngày/một tuần, UI tab Admin, cố định CLB trong room, kiểm thử end-to-end và giao dịch nguyên tử khi sinh lịch. Không triển khai production cho giải thật trước khi hoàn tất.

## V1.5.83
- Thu gọn riêng thanh tiêu đề phòng Rank/C1: cao khoảng 62px desktop, chữ PHÒNG ĐẤU/mã phòng nhỏ, logo và nút chia sẻ cân đối.
- Mobile dùng thanh ngang gọn, giữ nút chia sẻ dạng biểu tượng, không thay đổi JS/ID/endpoint.
- Không thay đổi dữ liệu hay luật thi đấu.

## V1.5.82
- Cân đối sidebar desktop theo chiều cao viewport: logo, menu, phiên bản và QR Zalo thu gọn có giới hạn; QR vẫn bấm được.
- Thu gọn khoảng trống trang phòng đấu ở màn hình laptop (cao <=1000px), giảm chiều cao tối thiểu 3 cột, khung CLB, topbar và dải chế độ.
- Không ẩn nội dung/khóa cuộn trang khi nội dung thực tế dài; giữ nguyên endpoint, logic trận và form.

# CHANGELOG — PES Arena

> Nguồn: các `V1.5.xx_RELEASE_NOTES.txt` có thật trong source. Không tự suy diễn các version bị thiếu.

## [V1.5.78] — 2026-09-15
- Tách `modules/tournament_competition.py` từ monolith 4.339 dòng thành composition root nhỏ và 7 module chức năng trong `modules/tournament_competition_parts/`.
- Giữ nguyên public registrar `register_routes(context)`, Flask endpoint/URL/method/decorator và thứ tự dependency.
- Các nhóm mới: core, Admin, test support, C1 rooms, League/club draw, scheduling/Host, rewards/Knockout.
- Cập nhật `PROJECT_MAP.md` theo cấu trúc backend C1 mới.
- Cập nhật `PROJECT_RULES.md`: `tournament_competition.py` chỉ còn là composition root, feature mới phải sửa đúng partition.
- Không thay đổi database/SQL, template hoặc luật giải; đây là refactor cấu trúc backend.

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


## V1.5.81
- Thêm chức năng Admin `🔄 Thay HLV` khi giải đang diễn ra.
- HLV mới tiếp quản nguyên suất: Pot/seed/CLB, đối thủ, lịch trận, tỷ số completed, BXH và tiến độ.
- Toàn bộ `tournament_matches` của suất được đổi owner sang HLV mới để các phép tính hiện tại tiếp tục dùng đúng kết quả cũ.
- Lưu snapshot trước khi thay vào `tournament_settings.replacement_history` để truy vết HLV cũ và tỷ số gốc.
- HLV cũ/member + registration chuyển `withdrawn`; HLV mới chuyển `active/approved`.
- Không kế thừa lịch rảnh; HLV mới bắt buộc đăng ký lịch của chính mình.
- Reward marker đã cấp được chuyển theo suất để không phát thưởng hoàn thành sớm lần hai.
- Chặn thay HLV nếu HLV cũ đang ở phòng C1 active hoặc HLV mới đã có lịch sử trận trong cùng giải.
- Gửi notification cho HLV mới sau khi tiếp quản.
- Không cần SQL/migration mới.

## V1.5.80
- Siết duyệt tài khoản: trùng IP đăng ký hoặc IP gần nhất của player khác -> `pending`, không tự duyệt.
- Player approved truy cập từ IP đang trùng sẽ chuyển `pending` và Admin nhận cảnh báo.
- Thêm QR nhóm Zalo tại trang đăng ký; bấm QR mở nhóm.
- Tài khoản bị chặn thấy popup nổi bật + QR và tin nhắn Admin mới nhất ngay tại login.
- Admin gửi thông báo riêng từng tài khoản với 4 mẫu: Nhắc nhở / Yêu cầu xác minh / Cảnh cáo / Thông báo chung.
- Tận dụng bảng `user_notifications`, không thêm SQL/schema.
- Cập nhật cảnh báo IP trên Admin theo chính sách mới.

## V1.5.79
- Hotfix lỗi namespace sau khi tách `tournament_competition.py` ở V1.5.78.
- Đồng bộ namespace hoàn chỉnh ngược lại tất cả `tournament_competition_parts` để giữ hành vi forward-reference của monolith cũ.
- Export các hằng số nội bộ cần dùng chéo module, gồm `C1_TEST_ACCOUNTS_KEY`.
- Sửa nguy cơ `NameError` ở `/admin` và các route C1/module khác chỉ xuất hiện lúc request runtime.
- Không thay đổi database, SQL, endpoint hay luật giải đấu.


## V1.5.85 – GĐ2: Admin xác nhận mở giải, điều hướng giai đoạn
- Bỏ tự động mở GĐ2 chỉ vì đồng hồ đến hạn; Admin mở thủ công khi đủ 16 HLV/CLB, Pot 5–6–5, 32 trận, mốc bắt đầu đã đến. Thời hạn 7 ngày.
- Không cho kết thúc GĐ2 khi còn trận chưa xác nhận, kể cả force.
- Thêm điều hướng Admin GĐ1 / GĐ2 / KO và nút xác nhận bắt đầu GĐ2.
- Chưa xác nhận kiểm thử E2E phòng C1, vé Random và dữ liệu Supabase thật; KHÔNG triển khai Production trước khi kiểm thử.
