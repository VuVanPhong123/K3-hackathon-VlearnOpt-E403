# VLearn Tutor Backend

Backend FastAPI lưu PDF local, trích xuất văn bản, render ảnh/crop bằng PyMuPDF và gọi provider AI thật.

## `POST /api/v2/chat`

Active flow có năm mode nội bộ:

- `GENERAL_CHAT`.
- `PAGE_CHAT` cho trang gắn, số trang trong câu hỏi hoặc active page.
- `TEXT_SELECTION_CHAT` với kiểm tra đoạn được chọn trên nội dung trang.
- `VISUAL_REGION_CHAT` với ảnh crop và văn bản giao vùng.
- `DOCUMENT_SEARCH_CHAT` với một lần lexical/dense retrieval và citation theo evidence.

Page chat luôn gửi cả ảnh toàn trang và văn bản trích xuất. Luồng hình ảnh dùng `VISION_PRIMARY_PROVIDER` và `VISION_FALLBACK_PROVIDER`; fallback chỉ xảy ra với rate limit, quota, timeout, lỗi kết nối hoặc HTTP 5xx. Lỗi API key, model hoặc bad request không fallback.

Endpoint `/api/chat` cũ và các API upload/list/file/delete vẫn được giữ để tương thích.

## Cấu hình

```powershell
Copy-Item .env.example .env
```

Điền ít nhất một trong hai key:

```dotenv
OPENAI_API_KEY=
GEMINI_API_KEY=
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

Chưa có OCR riêng cho scanned PDF, authentication hoặc production deployment. Summary, quiz, flashcard và AI hiểu nét vẽ không thuộc active CP3.
