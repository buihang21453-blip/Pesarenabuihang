# BAO CAO NUT BAM V1.2.47

## Pham vi quet
- Quet toan bo `templates/`: 44 template co nut bam.
- Tim thay 242 the `<button>` + 63 the `<a>` mang phong cach nut = 305 vi tri nut/clickable.
- 305 la so vi tri xuat hien trong template, co nhieu nut lap theo trang thai/nhanh dieu kien. Bao cao ben duoi gom theo nhom giao dien thuc te.
- Khong doi route, form action, JavaScript, RP, Supabase hay luong phong dau.

## Bang nhom nut sau khi can doi kich thuoc

| # | Khu vuc | Nut / nhom nut | Phong cach hien tai | Mau chinh | Kich thuoc chot |
|---|---|---|---|---|---|
| 1 | Header / Topbar | Theme, thong bao, menu tai khoan | Icon button toi gian | Nen toi, chu trang; hover vang | 32-40px vuong |
| 2 | Sidebar mobile | Nut menu hamburger | Icon button toi gian | Trung tinh | 40px vung bam |
| 3 | Dashboard | Tao phong, Vao phong | Gaming CTA co gradient | Vang | 44px |
| 4 | Dashboard | Tim doi thu nhanh | Gaming neutral | Xam/xanh den | 44px |
| 5 | Dashboard card doi thu | Moi dau mini | Outline Gaming | Vang | 34px, min 78px |
| 6 | Phong dau - cum trung tam | Moi Dau | Neon Gaming | Vang | 40px desktop; 38/36px responsive |
| 7 | Phong dau - cum trung tam | Tim Nhanh | Neon Gaming | Xanh la | 40px desktop; 38/36px responsive |
| 8 | Phong dau - cum trung tam | San Sang | Neon Gaming | Xanh la | 40px desktop; 38/36px responsive |
| 9 | Phong dau - cum trung tam | Huy San Sang | Neon Gaming neutral | Xam xanh | 40px desktop; 38/36px responsive |
| 10 | Phong dau - cum trung tam | Thoat Phong | Neon Gaming | Do | 40px desktop; 38/36px responsive |
| 11 | Phong dau - sau tran | Da Tiep | Neon Gaming | Vang | 40px desktop; 38/36px responsive |
| 12 | Phong dau - ket qua | Gui Ket Qua | Action button | Lop green theo he thong | 42px / full width |
| 13 | Phong dau - xac nhan | Xac Nhan | Result action | Xanh la trong suot | 50-54px |
| 14 | Phong dau - xac nhan | Khong Dong Y / Tranh chap | Result/Warning | Nen toi / do | 50-54px / form 40px |
| 15 | Phong dau - chon che do | Random / Random 3 chon 1 | Mode card gradient | Xanh-cyan / tim-hong | 58-65px |
| 16 | Phong dau - Random 3 | CHON CLB | Compact mode action | Tim-hong | 36-40px |
| 17 | Phong dau - quay quan | QUAY QUAN | Gaming card CTA | Vang gradient | Khoang 40px label trong card |
| 18 | Phong dau - quan ly doi thu | Dua khoi phong | Danger action | Do | 40px |
| 19 | Parsec | Copy ID, Luu, Xoa, Copy Link | Compact utility button | Hong/do theo module Parsec | 34px |
| 20 | Ho so | Moi dau, Chia se | Profile action | Vang / xam xanh | 38px |
| 21 | Ho so | Tab Tong quan / Thanh tich / Lich su / Quan ly | Tab button | Vang khi active, neutral khi thuong | 38-42px |
| 22 | Tim kiem / BXH / Players / Matches | Tim kiem, Loc, Xoa loc | Utility / neutral | Vang + xam | 38px |
| 23 | Dang nhap / Dang ky / Mat khau | Submit chinh | Full-width CTA | Theo theme chung | 44px |
| 24 | Kho do / Shop | Trang bi, Go, Mua, Xem truoc | Gaming action | Vang / xam / trang thai | 40px; small 32px |
| 25 | Lucky Box / Rewards | Mo hop, quay, doi qua | Gaming CTA | Vang; nut phu xam | 40-43px |
| 26 | Loi moi | Gui, Chap nhan, Tu choi, Huy | Action button | Lop green / do | 40px |
| 27 | Thong bao | Danh dau da doc / Kiem tra | Action / small action | Lop green / neutral | 40px; small 32px |
| 28 | Admin - tab dieu huong | Cac tab quan tri | Admin tab | Neutral; active vang/tim legacy | 40px |
| 29 | Admin - thao tac form | Luu, reset, backup, khoi phuc... | Admin action | Vang / do / xam | 38px; small 32px |
| 30 | Admin - Thiet ke phong Preview | Tim nhanh, Moi dau, Thoat | Neon Preview | Xanh la / vang / do | Bien CSS Admin; mac dinh 38px |
| 31 | Modal xac nhan trong phong | O lai phong / Xac nhan | Modal action | Neutral / vang; tone danger/safe thay mau | 49px |
| 32 | Chat sanh | Gui, dong chat | Compact action/icon | Vang/xanh legacy + neutral | 40px / icon compact |

## Phat hien quan trong
1. `room_detail.html` (lan tai dau) truoc V1.2.47 van con nut trung tam dung style cu, trong khi `_room_live_content.html` (sau khi polling) moi dung Neon. Dieu nay co the gay hien tuong giao dien doi style sau khi trang cap nhat. V1.2.47 da dong bo hai noi.
2. `static/style.css` co lich su nhieu lan doi mau `.btn`. Rieng `.btn.green` o cac trang ngoai phong hien dang bi rule legacy V1.7.3 doi thanh mau vang. V1.2.47 khong tu y doi he mau nay vi yeu cau hien tai la can kich thuoc; bao cao de tach xu ly mau o mot ban rieng neu can.
3. `partials/room_dynamic_state.html`, `room_ready_controls.html`, `room_confirmed_actions.html` van ton tai nhu template cu/reference, nhung route hien tai cua room dung `room_detail.html` + `_room_live_content.html`. Khong xoa de tranh anh huong luong cu chua duoc xac minh.
4. V1.2.47 tao `static/css/button_sizes.css` lam owner duy nhat cho KICH THUOC nut dung chung. File nay khong so huu mau/gradient/neon. CSS module (Room, Parsec, Profile, Lucky Box, Admin...) van so huu style rieng cua khu vuc do.

## Thay doi V1.2.47
- Dong bo Neon Gaming cho cum nut trung tam ngay tu lan render dau va sau khi room polling.
- Them icon/label dong bo cho Da Tiep, Huy San Sang, Tim Nhanh, Moi Dau, Thoat Phong.
- Tach kich thuoc nut dung chung vao `static/css/button_sizes.css`.
- Goi nut dung chung: 40px; nut small: 32px; CTA rong/auth: 44px; filter/search: 38px; admin action: 38px; admin tab: 40px; invite-mini: 34px.
- Bo quyen so huu `min-height/padding/font-size` khoi block `.btn` nen dau file `style.css`, de tranh hai noi cung quan ly kich thuoc co ban.
- Khong doi chuc nang, backend, form action, JavaScript, Supabase, RP.
