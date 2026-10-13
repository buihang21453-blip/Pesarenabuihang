# PES Arena V1.6.82 — Database Usage Optimization

## Implemented
- Personal match history (`/matches?view=mine`) now uses Supabase DB-side pagination for the normal path (20 rows/page).
- Status filters `confirmed`, `disputed`, and `waiting_confirm` are pushed into the DB before pagination.
- Match history/ranking hot reads use explicit match columns instead of `select("*")`.
- Ranking activity no longer loads full match objects; it reads only player IDs, status, note and created time, and only confirmed/cancelled rows.
- Added optional production indexes in `SQL_CU/SQL_V1.6.82_DB_READ_INDEXES.sql`.

## Compatibility fallbacks kept intentionally
The following history modes keep the legacy full-filter path so behavior does not change:
- text search (`q=`), because player display names are decorated from user/archive identity data;
- `cancelled` / forfeit filter, because legacy forfeit recognition depends on note/delta/business rules;
- system-wide history, because Invisible-player visibility must be applied before a correct page can be formed.

## Players / BXH
A blind DB `LIMIT/OFFSET` was NOT applied to Players/BXH. Their visible order depends on derived Presence/room state, invisible-account rules, season eligibility and ranking tie-breakers. Paging the raw `users` table first would silently change who appears on each page and can produce wrong ranks.

V1.6.82 therefore optimizes the safe BXH match-activity read now and leaves a true Players/BXH DB-pagination redesign for a DB view/RPC (or denormalized read model) later. This is deliberate correctness protection, not an unfinished find/replace.

## Assets
No asset/storage changes in this release. Supabase Storage remains external to keep source ZIPs small as requested.
