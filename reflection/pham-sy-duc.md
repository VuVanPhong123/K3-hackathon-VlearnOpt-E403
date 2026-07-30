# Reflection - Phạm Sỹ Đức

Trạng thái: `DONE`.

- Họ tên: Phạm Sỹ Đức
- MSSV: 2A202601601
- Vai trò: Golden set, evaluation, validation plan và demo preparation
- Phần đã thực hiện: Chuẩn bị golden set 43 case, term-search regression 14 case, runner/scorer offline, quality bar và validation protocol cho người test thật.
- AI hỗ trợ như thế nào: Dùng AI để rà độ phủ eval theo mode, status, citation, media path, fallback, history và UTF-8; đồng thời tách eval offline khỏi live provider semantic quality.
- Một case fail của nhóm: Nếu chỉ chạy vài happy path thủ công thì rất dễ bỏ sót lỗi citation, fallback hoặc retrieval thuật ngữ.
- Cách nhóm xử lý: Chốt quality bar bằng số, chạy toàn bộ eval sau mỗi thay đổi lớn và giữ term-search regression riêng để không chỉnh lịch sử golden set CP4.
- Bài học cá nhân: Eval tốt cần vừa ổn định offline để lặp nhanh, vừa trung thực về giới hạn không đo được chất lượng ngôn ngữ model thật.
- Điều sẽ làm khác đi lần sau: Chạy validation thật sớm hơn để biến feedback người dùng thành ít nhất một changelog trước demo.
