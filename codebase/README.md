# VLearn Tutor Prototype — Codebase Manifest

Thư mục này là manifest của prototype nộp bài. Mã nguồn hiện được giữ ở hai
thư mục gốc để không làm hỏng các đường dẫn và lệnh chạy đã được kiểm thử:

- [Backend FastAPI](../be/) — API, PDF ingestion, orchestration, retrieval,
  provider gateway và test.
- [Frontend React/Vite](../fe/) — PDF workspace, chọn trang/văn bản/vùng hình
  và chat UI.

## Entry points

| Thành phần | Entry point | Hướng dẫn |
|---|---|---|
| Backend | [`be/app/main.py`](../be/app/main.py) | [`be/README.md`](../be/README.md) |
| Frontend | [`fe/src/App.jsx`](../fe/src/App.jsx) | [`fe/README.md`](../fe/README.md) |
| Offline eval | [`eval/run_eval.py`](../eval/run_eval.py) | [`eval/README.md`](../eval/README.md) |
| Golden-set coverage | [`eval/coverage-map.csv`](../eval/coverage-map.csv) | [`eval/validate_coverage.py`](../eval/validate_coverage.py) |
| Live AI smoke | [`be/tests/live/test_live_chat_smokes.py`](../be/tests/live/test_live_chat_smokes.py) | [Sanitized live evidence](../evidence/r5-live-ai-run.md) |

## Real / mock boundary

| Phần | Trạng thái | Ghi chú / bằng chứng |
|---|---|---|
| React UI và FastAPI API | Real | Chạy từ source trong `fe/` và `be/`. |
| Upload, đọc trang PDF và tạo page context | Real | Backend xử lý PDF được upload cục bộ. |
| Interaction routing và citation theo trang | Real | Chạy trong orchestration service; được kiểm tra bởi integration test và offline eval. |
| OpenAI/Gemini provider | Real khi có API key | Live smoke dùng provider thật; không commit key hoặc `.env`. |
| PDF dùng trong live smoke | Synthetic fixture | File PDF được test tạo tạm thời, không phải dữ liệu người dùng. |
| Document/conversation repository trong live smoke | Stub | Chỉ cô lập lời gọi AI thật và đường multimodal. |
| Provider trong offline eval | Mock (`RecordingProvider`) | Không gọi mạng; ghi lại payload để chấm routing, context và fallback. |
| Page/image/document trong offline eval | Synthetic fixture | Nội dung trang và ảnh giả, tạo ổn định cho regression test. |
| Embedding trong offline eval | Deterministic hash embedding | Không đánh giá chất lượng embedding production. |
| Provider error/fallback trong offline eval | Simulated | Dùng lỗi cấu hình trong từng scenario để kiểm đường lui. |

Offline eval không phải bằng chứng cho chất lượng ngôn ngữ của mô hình thật.
Bằng chứng live là report đã loại dữ liệu nhạy cảm tại
[`evidence/r5-live-ai-run.md`](../evidence/r5-live-ai-run.md), ghi rõ commit, provider/model, trace ID,
trang/citation, `image_used`, latency và kết quả test. Nếu chưa có report đó,
không được tuyên bố đã hoàn tất yêu cầu “AI call thật”.

## Artifact links

- [Golden set](../eval/golden_set.jsonl)
- [Coverage map](../eval/coverage-map.csv)
- [Coverage validator](../eval/validate_coverage.py)
- [Offline evaluation runner](../eval/run_eval.py)
- [Live AI smoke test](../be/tests/live/test_live_chat_smokes.py)
- [Sanitized live AI evidence](../evidence/r5-live-ai-run.md)
- [Versioned evaluation/live reports](../eval/results/)

Không lưu API key, `.env`, Authorization header, raw provider request, ảnh
base64, database hội thoại hoặc dữ liệu người dùng trong các report.
