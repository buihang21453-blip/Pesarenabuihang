# PES Arena V1.6.98 — Friendly Login CTA CSS Fix

## Scope
Fix only the guest Friendly Match CTA styling on the login page.

## Root cause
`templates/login.html` extends `base.html`. The CTA CSS had been appended after `{% endblock %}`. Content outside declared blocks in an extending Jinja template is not emitted into the final rendered page, so the HTML existed but the CTA styling did not.

## Fix
- Keep CTA HTML in `templates/login.html`.
- Move `.guest-friendly-hero-*` CSS into `static/style.css`, which `base.html` always loads.
- Move the adjacent blocked-account popup CSS from the same dead trailing style block as well, preserving its intended styling.
- No inline emergency patch.

## Unchanged
Friendly random pools, 5-turn anti-repeat, EPL/La Liga logos, V1.6.97 mode icon design, DB, Supabase, Realtime, BXH, Room and gameplay.
