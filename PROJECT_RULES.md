
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
