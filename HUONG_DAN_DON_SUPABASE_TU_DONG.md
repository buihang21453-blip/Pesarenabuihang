# CHECKLIST DON SUPABASE TU DONG - PES ARENA

| Buoc | Lenh / thao tac | Ket qua |
|---|---|---|
| 1 | `python tools/supabase_cleanup/audit_supabase.py` | Quet project, KHONG xoa |
| 2 | `python tools/supabase_cleanup/cleanup_preview.py` | Xem truoc nhung gi se duoc don |
| 3 | Chay tool `tools/migrate_supabase_assets_to_vercel_static.py` | Tai asset UI ve `/static` |
| 4 | Chay lai `audit_supabase.py` | Phai bao asset local day du |
| 5 | Dat Vercel `STATIC_ASSET_MODE=local`, deploy va test web | Cat phu thuoc Storage UI |
| 6 | `python tools/supabase_cleanup/cleanup_storage.py` | DRY-RUN danh sach file se xoa |
| 7 | Neu preview dung: `SUPABASE_CLEANUP_ALLOW_EXECUTE=YES` + `--execute` | Xoa hang loat asset UI, KHONG dong avatar/evidence |
| 8 | Paste `tools/supabase_cleanup/cleanup_supabase.sql` vao SQL Editor | Dọn cache + log cu, KHONG drop bang |
| 9 | Kiem tra web: Login, BXH, Room, Admin, Shop, Lucky Box | Xac nhan an toan |

## Nguyen tac khoa an toan

- `cleanup_storage.py` mac dinh KHONG xoa.
- Neu thieu 1 asset local, tool TU CHOI xoa Storage.
- Tool chi xoa object nam trong `SUPABASE_ASSET_MANIFEST.csv` cua bucket `pes-assets`.
- Khong dung vao bucket avatar va bang chung tranh chap.
- `cleanup_supabase.sql` KHONG drop bat ky bang nao.
- `clubs_import` va `match_series_club_actions` chi duoc danh dau REVIEW, khong tu dong xoa.
