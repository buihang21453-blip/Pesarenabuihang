-- V1.5.88: add the 'pending' (GĐ2 preparation) stage status used by Python.
-- Run once in Supabase SQL Editor BEFORE deploying the V1.5.88 code.
-- Does not change existing statuses, matches, results, ranks or rewards.
BEGIN;
ALTER TABLE public.tournament_stages
  DROP CONSTRAINT IF EXISTS tournament_stages_status_check;
ALTER TABLE public.tournament_stages
  ADD CONSTRAINT tournament_stages_status_check
  CHECK (status IN ('draft','pending','open','locked','completed'));
COMMIT;
-- Verification (run after migration):
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
-- WHERE conrelid='public.tournament_stages'::regclass AND conname='tournament_stages_status_check';
-- Rollback only after confirming no row has status='pending':
-- ALTER TABLE public.tournament_stages DROP CONSTRAINT tournament_stages_status_check;
-- ALTER TABLE public.tournament_stages ADD CONSTRAINT tournament_stages_status_check
-- CHECK (status IN ('draft','open','locked','completed'));
