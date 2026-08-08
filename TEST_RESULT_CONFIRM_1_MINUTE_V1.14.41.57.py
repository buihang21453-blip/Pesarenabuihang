from pathlib import Path
src = Path("app.py").read_text(encoding="utf-8")
assert 'APP_VERSION = "V1.14.41.57"' in src
assert 'RESULT_CONFIRM_TIMEOUT_SECONDS = 60' in src
assert 'sau 1 phút tự xác nhận kết quả' in src
assert 'status") != "waiting_confirm"' in src
print("PASS: 1-minute auto-confirm is configured and disputed matches are excluded")
