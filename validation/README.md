# Validation Plan And Report

Trạng thái hiện tại: `BLOCKED_BY_REAL_USER_DATA`.

Repo chưa có log validation thật từ người ngoài nhóm, vì vậy không đánh dấu R6 PASS và không tạo tên/quote giả. Phần dưới đây là protocol đã chuẩn bị để nhóm chạy nhanh trước hoặc trong ngày pitching.

## Protocol

1. Chọn tối thiểu 5 người ngoài nhóm; ưu tiên ít nhất 2 willing users đã khai từ CP1 nếu có.
2. Giao task thật, ví dụ: mở PDF, hỏi theo trang, hỏi theo đoạn bôi đen, hỏi thuật ngữ toàn tài liệu, thử một case thiếu evidence.
3. Im lặng quan sát thao tác; không thuyết minh thay sản phẩm.
4. Hỏi 3 câu cuối phiên:
   - Điều gì khó hiểu hoặc khó chịu nhất?
   - Kết quả này bạn có tin không, vì sao?
   - Bạn có dùng thật không, vì sao hoặc vì sao chưa?
5. Ghi quote nguyên văn, không sửa ý người thử.

## Task Script

Mỗi người test làm 3 trong 5 task sau, tùy thời lượng:

| Task | Mục tiêu quan sát | Kỳ vọng |
|---|---|---|
| Hỏi theo trang đang xem | Kiểm tra page attachment và citation | Câu trả lời bám đúng page, có citation `Trang N` |
| Hỏi theo đoạn bôi đen | Kiểm tra selected text validation | Nếu đoạn khớp PDF thì trả lời theo đoạn; nếu không khớp thì báo lỗi rõ |
| Khoanh vùng hình/bảng | Kiểm tra visual region | Gửi image context, không trả lời như chỉ có text |
| Hỏi thuật ngữ toàn tài liệu | Kiểm tra retrieval thuật ngữ | Tìm đúng chunk/page cho term như RAG, encoder, multi-head attention |
| Hỏi nội dung không có trong tài liệu | Kiểm tra abstention | Không bịa citation, nói chưa đủ bằng chứng |

## Feedback Log

| Người thử | Vai trò | Willing user? | Task | Quan sát | Quote nguyên văn | Mức nghiêm trọng | Hành động |
|---|---|---|---|---|---|---|---|
| TODO - người thật | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

## Tổng hợp

- Chủ đề feedback lặp lại: TODO - cần dữ liệu thật.
- Thay đổi đã thực hiện từ feedback: TODO - cần dữ liệu thật.
- Điểm giữ nguyên và lý do: Không thêm live provider artifact vào repo; pitching dùng demo prototype và eval offline đã chốt, API key nếu dùng sẽ chỉ nằm trong `.env` local.
- Backlog nếu có thêm thời gian: OCR tốt hơn cho scanned PDF, auth/permission model, giảm bundle size frontend, và validation vòng hai sau khi sửa theo feedback thật.
- Ngày test: TODO - cần điền ngày thật.
- Người ghi nhận: TODO - cần điền người thật.
