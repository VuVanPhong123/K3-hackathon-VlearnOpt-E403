# VLearn Tutor

VLearn Tutor là MVP học tập gồm hai khu vực: trình đọc PDF có ghi chú local ở bên trái và chatbot ở bên phải.

## Phạm vi đang hỗ trợ

- Tải lên, mở, liệt kê và xóa PDF.
- Đọc PDF, phóng to/thu nhỏ và chuyển trang.
- Vẽ bằng bút, bút đánh dấu, tẩy, hoàn tác và xóa ghi chú của trang hiện tại.
- Lưu ghi chú theo từng tài liệu và từng trang trong `localStorage`.
- Chat thông thường khi chưa mở tài liệu hoặc khi người dùng chào hỏi rõ ràng.
- Kéo đúng một trang PDF vào chat hoặc dùng nút `Gắn trang vào chat`.
- Hỏi trực tiếp `giải thích trang 5`, hỏi `trang này` hoặc tìm nội dung trên toàn tài liệu.
- Chat theo trang gửi cả văn bản trích xuất và ảnh toàn trang cho mô hình có hỗ trợ hình ảnh.
- Bôi đen văn bản hoặc khoanh vùng bảng, hình, biểu đồ để hỏi Tutor.
- Citation dẫn về đúng trang và có thể bấm để cuộn tới trang đó.
- Provider chữ và provider hình ảnh có cấu hình primary/fallback riêng.
- Kéo divider hoặc dùng phím mũi tên để đổi độ rộng hai panel.

## Chưa hỗ trợ

CP3 chưa hỗ trợ summary toàn tài liệu, quiz, flashcard, AI hiểu nét vẽ, OCR riêng cho PDF scan, authentication hoặc production deployment. Nét vẽ chỉ được lưu local và không được gửi cho AI.

## Chạy thủ công

Backend trên Windows PowerShell:

```powershell
cd be
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend ở terminal khác:

```powershell
cd fe
npm install
Copy-Item .env.example .env
npm run dev
```

Mở `http://localhost:5173`. Swagger của backend ở `http://localhost:8000/docs`.

## Kiểm tra

```powershell
cd be
python -m compileall app
pytest -q

cd ..\fe
npm install
npm run build
npm test -- --run
```

Live provider test chỉ chạy khi `.env` có ít nhất một API key. Không commit `.env`, API key, `.venv`, `node_modules`, PDF runtime, SQLite runtime hoặc model cache.

Model trong `OPENAI_VISION_MODEL` hoặc `GEMINI_VISION_MODEL` phải hỗ trợ image input. Nếu để rỗng, backend dùng model chữ tương ứng.
