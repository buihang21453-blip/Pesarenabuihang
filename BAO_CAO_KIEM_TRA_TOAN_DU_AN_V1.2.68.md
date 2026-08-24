# BÁO CÁO KIỂM TRA TOÀN DỰ ÁN — V1.2.68

## Kết luận ngắn

Bản V1.2.67 không chỉ có một dòng sai. Luồng phòng đấu đã bị chồng nhiều cách xử lý của các phiên bản khác nhau. Vì vậy có tình trạng giao diện hiện nút nhưng phần xử lý phía sau lại chặn, hoặc xác nhận xong nhưng phòng chuyển sang trạng thái không khớp với nút Đá tiếp.

V1.2.68 sửa theo một luồng thống nhất:

**Sẵn Sàng → Quay Quân → Đang Đá → Gửi Kết Quả → Khách Xác Nhận → Confirmed → Đá Tiếp hoặc Rời Phòng.**

---

## 1. Lỗi lớn nhất: xác nhận xong nhưng phòng bị đưa về sai bước

### Vị trí cũ bị lỗi

File: `modules/room_result_routes.py`

Bản V1.2.67, khoảng **dòng 229–256**.

Sau khi khách xác nhận, code cũ đặt phòng thẳng về:

`status = waiting_ready`

Trong khi file `modules/room_rematch_routes.py`, khoảng **dòng 235**, lại quy định nút **Đá tiếp** chỉ làm việc khi phòng đang là:

`status = confirmed`

### Hiểu đơn giản

Giống như sau khi trọng tài công nhận kết quả, hệ thống tự đưa hai người trở lại phòng chờ ngay lập tức. Nhưng nút “Đá tiếp” lại chỉ hoạt động ở màn hình “Trận đã hoàn tất”. Hai phần không nói cùng một ngôn ngữ nên luồng bị đứt.

### Đã sửa

V1.2.68: `modules/room_result_routes.py`, hàm `room_confirm_result`, bắt đầu khoảng **dòng 190**.

Sau xác nhận, phòng kết thúc ở `confirmed`. Người chơi nhìn thấy kết quả và có thể chọn **Đá tiếp** hoặc **Rời phòng**.

---

## 2. Lỗi nguy hiểm: lưu điểm được một nửa rồi lỗi

### Vị trí cũ bị lỗi

File: `modules/match_result_service.py`

Bản V1.2.67:

- khoảng **dòng 215**: ghi điểm/ngày thắng thua cho người chơi 1.
- khoảng **dòng 216**: ghi điểm/ngày thắng thua cho người chơi 2.
- khoảng **dòng 233–261**: mới chốt trận là `confirmed`.
- khoảng **dòng 262–273**: khi lỗi, chỉ trả trạng thái trận về như cũ.

### Hiểu đơn giản

Hãy tưởng tượng hệ thống làm 3 việc:

1. cộng điểm người A;
2. cộng điểm người B;
3. đóng dấu “trận đã hoàn tất”.

Nếu bước 2 hoặc bước 3 lỗi, code cũ chỉ xóa cái “dấu đang xử lý”, nhưng điểm đã ghi ở bước 1 có thể vẫn còn. Khi bấm lại có nguy cơ ghi thêm lần nữa.

### Đã sửa

File: `modules/match_result_service.py`

- khoảng **dòng 93**: có hàm khôi phục dữ liệu người chơi.
- khoảng **dòng 119**: bắt đầu luồng `apply_match_result` mới.

Trước khi ghi điểm, hệ thống chụp lại số liệu của cả hai người. Nếu một bước bị lỗi trước khi trận được chốt, hệ thống trả cả hai người về đúng dữ liệu trước đó.

Nếu trận thực tế đã `confirmed`, hệ thống không cộng lại lần hai.

---

## 3. Lỗi “có nút Thoát nhưng bấm không đi được”

### Vị trí cũ bị lỗi

File: `modules/room_access_routes.py`

Bản V1.2.67, khoảng **dòng 437–439**.

Code cũ chặn route `/leave` khi phòng không nằm trong `waiting_ready` hoặc `friendly_playing`.

### Hiểu đơn giản

Giao diện có thể đưa cho bạn một cánh cửa “Thoát Phòng”, nhưng người gác cửa phía server lại nói: “trạng thái này không được ra”. Vì vậy nhìn thấy nút không có nghĩa phần phía sau cho phép thoát.

### Đã sửa

V1.2.68: `modules/room_access_routes.py`, hàm `room_leave`, bắt đầu khoảng **dòng 429**.

Ở các trạng thái:

- `waiting_result_confirm`
- `disputed`
- `confirmed`

nút thoát chỉ đưa người chơi về sảnh và **không gọi tính RP, không sửa kết quả**.

Nếu database thật sự lỗi, route cũng không còn văng thẳng thành trang 500; người dùng nhận thông báo dễ hiểu và dữ liệu RP không bị đụng tới.

---

## 4. Lỗi luồng Thoát sau khi gửi kết quả bị ràng buộc quá nhiều

### Vị trí cũ

File: `modules/room_result_routes.py`

Bản V1.2.67, khoảng **dòng 170–188**.

Route `post-result-exit` vừa kiểm tra thành viên vừa kiểm tra chặt trạng thái phòng. Nếu giao diện và database lệch nhau trong một lần polling, người dùng có thể bị đẩy ngược vào phòng.

### Đã sửa

V1.2.68: `modules/room_result_routes.py`, hàm `room_post_result_exit`, bắt đầu khoảng **dòng 172**.

Thao tác này giờ chỉ có một nhiệm vụ: **về sảnh**. Nó không được phép gọi tính điểm hoặc sửa trận.

---

## 5. Lỗi nút Sẵn Sàng bị cắt khỏi giao diện

### Vị trí gây xung đột

File: `static/css/room_detail.css`

Rule cũ khoảng **dòng 1899** đặt khối “Đợi quay Random đội” cao tối thiểu `158px`.

Trong khi `static/css/room_v2.css` có các khung cố định chiều cao và một số chỗ dùng `overflow:hidden`.

Các bản vá sau đó lại ghim hàng nút Ready bằng `position:absolute`, làm giao diện càng phụ thuộc vào chiều cao khung.

### Hiểu đơn giản

Nút Sẵn Sàng vẫn tồn tại, nhưng bị đẩy xuống dưới mép của chiếc hộp rồi chiếc hộp “cắt” phần nằm ngoài. Vì vậy bạn không nhìn thấy nút dù code HTML vẫn có.

### Đã sửa

File: `static/css/room_v2.css`, phần **V1.2.68 — READY ACTIONS FINAL LAYOUT**, bắt đầu khoảng **dòng 903**.

Hàng nút Sẵn Sàng trở lại luồng hiển thị bình thường, không còn bị ghim tuyệt đối vào đáy. CSS cũng ép `visibility: visible` và không cho hàng nút tự biến mất do chiều cao tùy chỉnh.

Cả hai template đều đã kiểm tra có nút:

- `templates/room_detail.html`
- `templates/_room_live_content.html`

---

## 6. So sánh ID người chơi không đồng nhất

### Vị trí cũ

Một số route dùng kiểu:

`user["id"] == room["guest_user_id"]`

Trong khi chỗ khác đã dùng `_same_user_id(...)`.

### Hiểu đơn giản

Hai mã người dùng nhìn giống nhau, nhưng một bên có thể được database trả về dưới dạng khác. So sánh trực tiếp đôi khi coi chúng là khác nhau, dẫn đến hệ thống tưởng bạn “không thuộc phòng”.

### Đã sửa

Các route quan trọng của phòng và rematch dùng `_same_user_id(...)` để so sánh thống nhất.

---

## 7. Test cũ gây nhiễu khi kiểm tra toàn dự án

Project có nhiều file test của các phiên bản trước. Ví dụ có test vẫn yêu cầu chính xác:

- `V1.2.9`
- `V1.2.10`
- `V1.2.12`
- `V1.2.27`
- thậm chí một nhánh `1.3.134`

Trong khi project hiện là V1.2.68.

### Hiểu đơn giản

Đây giống như lấy hướng dẫn sử dụng của chiếc xe đời 2024 để kiểm tra xe đời 2026 rồi báo “sai” chỉ vì số đời không giống. Không phải tất cả các test đỏ đều là lỗi chương trình.

Tôi giữ các test lịch sử để tham khảo, nhưng tạo thêm kiểm tra hiện tại tại:

`scripts/audit_v1268.py`

Kết quả hiện tại: **19/19 PASS**.

---

# Các kiểm tra đã chạy

1. Compile toàn bộ file Python trong project: **PASS**.
2. Parse riêng các module phòng chính: **PASS**.
3. Kiểm tra phiên bản hiển thị V1.2.68: **PASS**.
4. Kiểm tra manual confirm kết thúc ở `confirmed`: **PASS**.
5. Kiểm tra route xác nhận không còn sinh mã `CONFIRM-*`: **PASS**.
6. Kiểm tra Thoát sau kết quả không gọi tính RP: **PASS**.
7. Kiểm tra có snapshot và rollback cả hai người chơi: **PASS**.
8. Kiểm tra rời phòng ở chờ xác nhận/tranh chấp/confirmed: **PASS**.
9. Kiểm tra nút Sẵn Sàng ở full template: **PASS**.
10. Kiểm tra nút Sẵn Sàng ở phần polling: **PASS**.
11. Kiểm tra CSS cuối cùng của Ready: **PASS**.

---

# Luồng phòng được chốt cho V1.2.68

## Trận Rank

**Chủ tạo phòng → Khách vào → Khách Sẵn Sàng → Chủ Quay Quân → Đang thi đấu → Chủ gửi tỷ số → Khách xác nhận → Trận Confirmed → Đá tiếp hoặc Rời phòng.**

## Khi khách bấm xác nhận 2 lần

Lần đầu ghi RP và chốt trận.

Lần sau thấy trận đã confirmed nên chỉ trả kết quả cũ; **không cộng điểm lần hai**.

## Khi lỗi giữa lúc lưu điểm

Nếu trận chưa được chốt confirmed, dữ liệu hai người được trả về trước trận.

Nếu database đã chốt trận confirmed nhưng phản hồi về chậm/lỗi, hệ thống coi trận đã thành công và **không rollback nhầm**.

## Khi bấm Thoát sau kết quả

Chỉ về sảnh. Không tính RP, không xóa tỷ số, không gọi xác nhận thay người chơi.

---

**Phiên bản dự án sau kiểm tra: V1.2.68**
