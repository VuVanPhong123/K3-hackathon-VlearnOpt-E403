# VLearn Tutor Frontend

Frontend React/Vite hiển thị trình đọc PDF và chatbot trong cùng màn hình.

## Luồng chính

- Khi đang mở tài liệu, frontend gửi `document_id` và `active_page`.
- Page attachment gửi một phần tử trong `attached_pages`.
- Bôi đen văn bản tạo `text_selection`; tool `Khoanh vùng hỏi AI` tạo `visual_region`.
- Một lần chỉ có một context attachment; context mới thay context cũ.
- Chat dùng `POST /api/v2/chat/stream` với `fetch` + `ReadableStream`.
- Frontend chỉ gửi history fallback tối đa 12 message và không gửi welcome message `localOnly`; backend conversation memory là nguồn chính khi có `conversation_id`.
- Nút `Cuộc trò chuyện mới` abort stream đang chạy, xóa conversation server theo best effort, reset local chat/context và không xóa PDF hoặc annotation.
- Đổi tài liệu abort stream cũ, xóa conversation server cũ theo best effort, clear attachment/history và mở chat mới; annotation trong `localStorage` vẫn còn.
- Pen, highlighter và eraser chỉ lưu annotation trong `localStorage`; không tạo AI attachment.
- Bấm citation cuộn đến trang tương ứng và nháy sáng page card trong 1,5 giây.
- Divider desktop lưu độ rộng bằng key `vlearn-chat-panel-width`; dưới 980px giao diện chuyển sang bố cục dọc.

## Chạy và kiểm tra

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Production build check: `npm run build`.

Frontend đọc API URL từ `VITE_API_BASE_URL`. `VITE_ENABLE_DEBUG_PANEL` mặc định là `false`.
