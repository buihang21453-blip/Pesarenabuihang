# V1.6.102

Scope: player presence/invite correctness and public Friendly random pools only.

1. Solo waiting room is authoritative over stale live-match rows in both Python fallback and DB RPC.
2. Run `SQL_V1.6.102_FIX_PLAYER_ACTIVITY_RPC.sql` in Supabase SQL Editor after deploy.
3. Friendly 5★ = clubs_import Tier S/S+; 4★ = clubs_import Tier A/A+. No fixed pair list.
4. The public tier-pool endpoint is read-only and process-cached for 5 minutes.
