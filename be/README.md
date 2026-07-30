# VLearn Tutor Backend

Backend FastAPI lưu PDF local, trích xuất văn bản, render ảnh/crop bằng PyMuPDF, truy xuất evidence và gọi provider AI thật khi có API key.

## Chat endpoints

`POST /api/v2/chat` giữ backward compatibility cho eval runner và integration tests hiện có. Active flow có năm mode nội bộ:

- `GENERAL_CHAT`.
- `PAGE_CHAT` cho trang gắn, số trang trong câu hỏi hoặc active page.
- `TEXT_SELECTION_CHAT` với kiểm tra đoạn được chọn trên nội dung trang.
- `VISUAL_REGION_CHAT` với ảnh crop và văn bản giao vùng.
- `DOCUMENT_SEARCH_CHAT` với lexical/dense retrieval và citation theo evidence.

`POST /api/v2/chat/stream` dùng cùng bước resolve context với `/api/v2/chat`, nhưng trả SSE:

- `meta`: `conversation_id`, `trace_id`, `mode`.
- `delta`: phần text mới.
- `done`: answer đầy đủ, citations, confidence, provider/model, fallback và trace.
- `error`: thông báo tiếng Việt; không stream stack trace, system prompt, API key hoặc image bytes.

Frontend dùng `fetch` + `ReadableStream` vì request cần POST body. Fallback streaming chỉ xảy ra khi provider chính lỗi trước delta đầu tiên; nếu đã có partial delta thì stream trả `error` để người dùng retry thay vì ghép câu trả lời từ provider khác.

Endpoint `/api/chat` cũ và các API upload/list/file/delete vẫn được giữ để tương thích.

## Conversation memory

Backend là nguồn lịch sử chính khi request có `conversation_id` hợp lệ. Context gửi model gồm:

- rolling digest deterministic trong `conversations.summary`;
- tối đa `CHAT_RECENT_MESSAGE_LIMIT` message gần nhất;
- character budget `CHAT_MAX_HISTORY_CHARS`.

Nếu conversation chưa có trên server, request `history` từ frontend chỉ là fallback. Full message log không bị xóa chỉ vì đã compact.

## Cấu hình

```powershell
Copy-Item .env.example .env
```

Điền ít nhất một trong hai key:

```dotenv
OPENAI_API_KEY=
GEMINI_API_KEY=
```

Các biến context mặc định:

```dotenv
CHAT_RECENT_MESSAGE_LIMIT=12
CHAT_SUMMARY_TRIGGER_MESSAGES=16
CHAT_MAX_HISTORY_CHARS=24000
CHAT_SUMMARY_MAX_CHARS=4000
```

Chọn model hỗ trợ image input trong `OPENAI_VISION_MODEL` hoặc `GEMINI_VISION_MODEL`. Nếu biến vision model để rỗng, backend dùng model chữ tương ứng. Không commit `.env`.

## Chạy và kiểm tra

Khuyến nghị Python 3.11 hoặc 3.12 64-bit:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall app
pytest -q
uvicorn app.main:app --reload --port 8000
```

Swagger ở `http://localhost:8000/docs`.

## Giới hạn

Chưa có OCR riêng cho scanned PDF, authentication hoặc production deployment. Summary, quiz, flashcard và AI hiểu nét vẽ không thuộc active CP4/CP5 scope.
