# V1.2.22 - Sua loi cache bi don nham

## Lam ngay
1. Supabase -> SQL Editor -> New query.
2. Mo `tools/supabase_cleanup/KHOI_PHUC_CACHE_SAU_DON_NHAM.sql`, copy toan bo, Run.
3. Cho den khi query tra bang dem row va khong co loi do.
4. Deploy V1.2.22 len Vercel.
5. Mo lai BXH; code V1.2.22 con co fallback cho tung user neu cache bi thieu mot phan.

## Khong lam
- Khong chay lai file cleanup cua V1.2.21.
- Khong chay `cleanup_storage.py` cho den khi asset local du 57/57.
- Khong xoa tay cac bang cache.

## Cleanup V1.2.22
`cleanup_supabase.sql` da bo TOAN BO TRUNCATE cache. File nay chi trim log cu va ANALYZE.
