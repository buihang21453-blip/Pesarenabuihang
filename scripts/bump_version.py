from pathlib import Path
import re, sys

if len(sys.argv) != 2 or not re.fullmatch(r"V\d+\.\d+\.\d+", sys.argv[1]):
    raise SystemExit("Usage: python scripts/bump_version.py V1.2.2")
path = Path(__file__).resolve().parents[1] / "app.py"
text = path.read_text(encoding="utf-8")
new_text, count = re.subn(r'APP_VERSION = "V\d+\.\d+\.\d+"', f'APP_VERSION = "{sys.argv[1]}"', text, count=1)
if count != 1:
    raise SystemExit("APP_VERSION not found or duplicated")
path.write_text(new_text, encoding="utf-8")
print(f"Updated APP_VERSION to {sys.argv[1]}")
