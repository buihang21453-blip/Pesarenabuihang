from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
errors, warnings = [], []

app_text = (root / "app.py").read_text(encoding="utf-8")
if "def static_asset(filename):" not in app_text:
    errors.append("app.py: missing static_asset() content fingerprint helper")

base = (root / "templates" / "base.html").read_text(encoding="utf-8")
for asset in re.findall(r"(?:href|src)=\"([^\"]+\.(?:css|js)[^\"]*)\"", base):
    if "static_asset(" not in asset and "{{" in asset:
        errors.append(f"templates/base.html: CSS/JS does not use static_asset(): {asset}")

weekly_css = root / "static" / "css" / "admin_weekly_rewards.css"
if not weekly_css.exists():
    errors.append("missing static/css/admin_weekly_rewards.css")
else:
    css = weekly_css.read_text(encoding="utf-8")
    if 'body[data-page="admin"]' not in css:
        errors.append("admin_weekly_rewards.css is not scoped to the admin page")
    if "!important" in css:
        errors.append("admin_weekly_rewards.css contains !important")

admin = (root / "templates" / "admin.html").read_text(encoding="utf-8")
if "Weekly RP: inline critical CSS" in admin:
    errors.append("weekly RP CSS is still duplicated inline in admin.html")
if "weekly-rp-panel" in (root / "static" / "style.css").read_text(encoding="utf-8"):
    errors.append("weekly RP CSS is duplicated in global style.css")

for p in (root / "templates").rglob("*.html"):
    if "<style>" in p.read_text(encoding="utf-8"):
        warnings.append(f"{p.relative_to(root)} contains legacy inline CSS")

if warnings:
    print("Warnings:")
    print("\n".join(f"- {w}" for w in warnings))
if errors:
    print("UI asset check failed:")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print("UI asset check passed")
