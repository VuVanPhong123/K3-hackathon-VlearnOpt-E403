# Reflection - Đoàn Nhật Nam

Trạng thái: `DONE`.

- Họ tên: Đoàn Nhật Nam
- MSSV: 2A202601123
- Vai trò: Evidence/mining, số liệu và quote có nguồn
- Phần đã thực hiện: Mining chatlog VLearn để định lượng pain selected-context/retrieval: tổng số message/turn, tỷ lệ empty citation, retrieval/fallback language, page-citation mismatch và các case có `conversation_id/turn_id`.
- AI hỗ trợ như thế nào: Dùng AI để kiểm tra logic đếm, chuẩn hóa cách mô tả regex/rules, và nhắc phân biệt rõ điều dữ liệu chứng minh với điều dữ liệu chưa chứng minh.
- Một case fail của nhóm: Có nguy cơ dùng aggregate như 46,2% empty citation để kết luận quá rộng rằng tutor luôn sai citation.
- Cách nhóm xử lý: Evidence report tách riêng mục “dữ liệu chứng minh” và “dữ liệu chưa chứng minh”, chỉ giữ quote ngắn cần thiết và không ship data pack gốc.
- Bài học cá nhân: Evidence mạnh không nằm ở số thật lớn, mà ở rule đếm có thể audit và quote đủ ngắn, đủ nguồn.
- Điều sẽ làm khác đi lần sau: Chuẩn bị script mining và README evidence ngay từ đầu để các thành viên khác dùng cùng một định nghĩa pain.
