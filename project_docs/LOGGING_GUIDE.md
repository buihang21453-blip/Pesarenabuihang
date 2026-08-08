# PES Arena V1.3.61 — Logging Standard

PES Arena có **2 loại log khác nhau** và không được trộn lẫn.

## 1. `Log.md` — changelog phiên bản

Mỗi phiên bản mới thêm ở **đầu file** theo mẫu:

```md
# Vx.y.z — Tên phiên bản

**Ngày:** DD/MM/YYYY HH:mm (Asia/Bangkok)
**Phạm vi:** module/file chính
**Loại:** Fix | Refactor | Feature | Safety | UI

## Thay đổi
- ...

## File thay đổi
| File | Chức năng | Thay đổi |
|---|---|---|
| `path/file.py` | ... | ... |

## Kiểm tra
- `python -m py_compile ...`: PASS/FAIL
- Test module: PASS/FAIL
- Full pytest: PASS / baseline failures / regression mới

## Không thay đổi
- ...
```

Không ghi password, token, cookie, Supabase key hoặc dữ liệu nhạy cảm vào `Log.md`.

## 2. Runtime log — JSON Lines

Production/serverless: stdout để Vercel thu log.
Local/dev: có thể ghi rotating file `logs/pes_arena.log`.

### Environment variables

| Variable | Default | Mục đích |
|---|---|---|
| `PES_LOG_LEVEL` | `INFO` | INFO/WARNING/ERROR |
| `PES_SLOW_REQUEST_MS` | `1500` | ngưỡng slow request |
| `PES_LOG_TO_FILE` | dev/test=on | bật file local |
| `PES_LOG_FILE` | `logs/pes_arena.log` | đường dẫn log local |

### Field chuẩn

| Field | Ý nghĩa |
|---|---|
| `ts` | UTC ISO timestamp |
| `level` | INFO/WARNING/ERROR |
| `event` | tên sự kiện ổn định để search |
| `request_id` | mã truy vết request |
| `method` | GET/POST/... |
| `path` | URL path |
| `endpoint` | Flask endpoint |
| `user_id` | user id nếu có |
| `status` | HTTP status nếu có |
| `duration_ms` | thời gian request |
| `error_type` | loại exception |
| `error` | mô tả lỗi ngắn |

### Event quan trọng

- `application_logging_ready`
- `request_complete`
- `slow_request`
- `database_query_retry`
- `database_query_failed`
- `uncaught_exception`
- `system_features_load_failed`
- `quick_match_config_load_failed`
- `repeat_opponent_config_load_failed`
- `maintenance_config_load_failed`
- `dispute_evidence_remove_failed`
- `dispute_evidence_signed_url_failed`

## 3. Quy trình debug

1. Tái hiện lỗi.
2. Mở Network và lấy `X-Request-ID` nếu request có response.
3. Search request ID trong Vercel/local log.
4. Xác định `endpoint` và `event` lỗi.
5. Tra `PROJECT_MAP.md` để tìm module sở hữu.
6. Chỉ sửa module liên quan.
7. Chạy test module + dependency trực tiếp.
8. Ghi kết quả vào `Log.md`.

## 4. Không bao giờ log

- password / password hash đầy đủ khi không cần thiết
- session cookie
- authorization header
- Supabase service-role key
- secret key
- Parsec secret/link riêng tư không cần thiết
- bytes ảnh upload
