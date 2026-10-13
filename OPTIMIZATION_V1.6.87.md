# PES Arena V1.6.87 — Asset Router

- GitHub/Vercel local asset tree is primary: `/static/assets/...`.
- Supabase remains fallback for IMG assets.
- Namespaces mirror Storage: `Giaidau`, `v1`, `v1.3.40`, `v1.14.41`, `LeBocThamGD2`, `team-logos`.
- Legacy logical paths such as `shop/...`, `luckybox/...`, `ranks/...` map to `v1.14.41/...`.
- Hard-coded PES/Team Storage URLs in active source were changed to local `/static/assets/...` URLs.
- User avatars/uploads remain unchanged and continue using their stored URLs.
- Existing BXH emergency hotfix is preserved.
- No database migration is required.

Environment overrides (optional): `PES_ASSET_ROOT_URL`, `TEAM_LOGO_BASE_URL`, `SHOP_ASSET_BASE_URL`, `LUCKYBOX_ASSET_BASE_URL`.
