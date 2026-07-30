# Reflection - Nguyễn Quang Vinh

Trạng thái: `DRAFT_NEEDS_MEMBER_CONFIRMATION`.

- Họ tên: Nguyễn Quang Vinh
- MSSV: 2A202601517
- Vai trò: Prompt, failure taxonomy, HAX/PAIR và provider behavior
- Phần đã thực hiện: Xây failure taxonomy bám 4 lớp khó, thiết kế hành vi không đoán khi thiếu căn cứ, provider fallback rule, prompt/context requirements và các kịch bản rủi ro cho page, selection, visual, retrieval, provider error.
- AI hỗ trợ như thế nào: Dùng AI để sinh biến thể failure case, đối chiếu HAX/PAIR với vị trí cụ thể trong prototype và rà prompt xem có khuyến khích hallucination/citation giả không.
- Một case fail của nhóm: Retrieval thuật ngữ dễ bị nhiễu bởi câu hỏi dài hoặc typo, khiến term có trong tài liệu nhưng evidence/citation không ổn định.
- Cách nhóm xử lý: Bổ sung query planner cho câu định nghĩa/giải thích thuật ngữ, query variants, exact phrase boost, fuzzy correction có guardrail và regression 14 case.
- Bài học cá nhân: Prompt không đủ nếu retrieval đầu vào sai; guardrail tốt phải nằm cả ở planner, retrieval và answer behavior.
- Điều sẽ làm khác đi lần sau: Viết regression cho từng bug ngay khi phát hiện, không đợi đến cuối mới gom.
