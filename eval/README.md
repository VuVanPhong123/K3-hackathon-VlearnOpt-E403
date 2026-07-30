# VLearn Tutor Eval

`golden_set.jsonl` hiện có 46 ca, tăng từ 31 ca của bộ cũ. Trong đó có 10 ca
được chuyển thể từ chatlog VLearn đã ẩn danh và 36 ca tổng hợp.

Bộ eval bao phủ:

- 5 chế độ tương tác: chat chung, chat theo trang, vùng văn bản, vùng hình ảnh
  và tìm kiếm toàn tài liệu.
- Thứ tự ưu tiên ngữ cảnh, trang không hợp lệ, nhiều trang đính kèm và vùng
  văn bản không khớp.
- Retrieval, citation, đường gọi text/multimodal và ảnh đính kèm.
- Fallback OpenAI/Gemini, lỗi request, thiếu API key và giới hạn lịch sử chat.
- Quyết định `answer` / `clarify` / `abstain`, gồm trường hợp không có evidence
  và trường hợp user cho phép kiến thức chung.
- Chuỗi trả lời tiếng Việt UTF-8 có dấu.

Chạy từ thư mục gốc:

```powershell
be\.venv\Scripts\python.exe -X utf8 eval\run_eval.py
be\.venv\Scripts\python.exe -X utf8 eval\validate_coverage.py
be\.venv\Scripts\python.exe -X utf8 eval\render_report.py
```

Runner gọi `OrchestrationService` và retrieval thật, nhưng dùng provider giả để
chạy offline, ổn định và không tốn API. Chỉ scorer được đọc trường `expected`;
runner có kiểm tra chống rò đáp án. Kết quả chi tiết được ghi vào
`eval/results/latest.json`; bảng Markdown đầy đủ nằm tại
`eval/results/latest.md`.

`coverage-map.csv` ánh xạ toàn bộ case vào bốn lớp rủi ro và tier
routine/hard/rare. `validate_coverage.py` kiểm tra exact ID, nguồn, tối thiểu
hai case mỗi lớp, đúng 10 case routine và 4 case rare.

Bộ này đánh giá contract, routing, grounding context và fallback. Chất lượng
ngôn ngữ của mô hình thật cần được kiểm tra riêng bằng live smoke test hoặc
LLM-as-judge khi có API key. Bằng chứng live đã làm sạch nằm tại
`evidence/r5-live-ai-run.md`.
