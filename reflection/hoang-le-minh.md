# Reflection - Hoàng Lê Minh

Trạng thái: `DRAFT_NEEDS_MEMBER_CONFIRMATION`.

- Họ tên: Hoàng Lê Minh
- MSSV: 2A202601653
- Vai trò: Prototype/frontend flow
- Phần đã thực hiện: Xây PDF workspace, chat panel, page attachment, text selection, visual region, citation click, streaming UI, reset conversation và document-switch cleanup.
- AI hỗ trợ như thế nào: Dùng AI để rà edge case UI như abort stream, local-only welcome message, history fallback, và trạng thái khi đổi document hoặc xóa attachment.
- Một case fail của nhóm: Streaming có thể tạo trải nghiệm khó hiểu nếu lỗi xảy ra sau khi đã có partial delta hoặc khi đổi tài liệu giữa chừng.
- Cách nhóm xử lý: Frontend abort stream khi reset/đổi document, backend chỉ fallback provider trước delta đầu tiên, còn lỗi sau partial response thì báo retry thay vì ghép hai provider.
- Bài học cá nhân: Với AI UI, trạng thái chuyển tiếp quan trọng không kém happy path; user cần thấy hệ thống đang dùng context nào và có thể sửa ngay.
- Điều sẽ làm khác đi lần sau: Tách component state và API state sớm hơn để dễ kiểm soát reset, retry và attachment lifecycle.
