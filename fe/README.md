# VLearn Tutor Frontend

Frontend React/Vite hiển thị trình đọc PDF và chatbot trong cùng màn hình.

## Luồng chính

- Khi đang mở tài liệu, frontend luôn gửi `document_id` và `active_page`.
- Page attachment gửi một phần tử trong `attached_pages`.
- Bôi đen văn bản tạo `text_selection`; tool `Khoanh vùng hỏi AI` tạo `visual_region`.
- Một lần chỉ có một context attachment; context mới thay context cũ.
- Đổi tài liệu sẽ xóa attachment, `conversation_id` và lịch sử chat.
- Pen, highlighter và eraser chỉ lưu annotation trong `localStorage`; không tạo AI attachment.
- Bấm citation cuộn đến trang tương ứng và nháy sáng page card trong 1,5 giây.
- Divider desktop lưu độ rộng bằng key `vlearn-chat-panel-width`; dưới 980px giao diện chuyển sang bố cục dọc.

## Chạy và kiểm tra

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

```powershell
npm run build
npm test -- --run
```

Frontend đọc API URL từ `VITE_API_BASE_URL`. `VITE_ENABLE_DEBUG_PANEL` mặc định là `false`.
