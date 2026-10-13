# PES Arena V1.6.83 — Players/BXH DB-side Pagination

- Players: backend-only Supabase RPC filters visibility/search/status, derives live room/match state, sorts, counts and returns 30 rows/page.
- Current BXH: backend-only RPC applies season eligibility, inactivity, invisible visibility, global rank, search/rank filter and returns 100 rows/page.
- Historical BXH intentionally keeps frozen snapshot logic from V1.6.82.
- Both routes automatically fall back to V1.6.82 logic if the SQL migration has not been installed.
- RPC execute permission is revoked from anon/authenticated and granted only to service_role.
- Assets/Supabase Storage are unchanged.

## Required Supabase step
Run `SQL_CU/SQL_V1.6.83_PLAYERS_BXH_RPC.sql` once in Supabase SQL Editor, then redeploy V1.6.83.
