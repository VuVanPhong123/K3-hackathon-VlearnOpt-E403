# VLearn Tutor Eval

`golden_set.jsonl` hiện có 43 ca, tăng từ 31 ca của bộ cũ. Trong đó có 10 ca
được chuyển thể từ chatlog VLearn đã ẩn danh và 33 ca tổng hợp.

Bộ eval bao phủ:

- 5 chế độ tương tác: chat chung, chat theo trang, vùng văn bản, vùng hình ảnh
  và tìm kiếm toàn tài liệu.
- Thứ tự ưu tiên ngữ cảnh, trang không hợp lệ, nhiều trang đính kèm và vùng
  văn bản không khớp.
- Retrieval, citation, đường gọi text/multimodal và ảnh đính kèm.
- Fallback OpenAI/Gemini, lỗi request, thiếu API key và giới hạn lịch sử chat.
- Chuỗi trả lời tiếng Việt UTF-8 có dấu.

Chạy từ thư mục gốc:

```powershell
codebase\backend\.venv\Scripts\python.exe -X utf8 eval\run_eval.py
```

Runner gọi `OrchestrationService` và retrieval thật, nhưng dùng provider giả để
chạy offline, ổn định và không tốn API. Chỉ scorer được đọc trường `expected`;
runner có kiểm tra chống rò đáp án. Kết quả chi tiết được ghi vào
`eval/results/latest.json`.

Bộ này đánh giá contract, routing, grounding context và fallback. Chất lượng
ngôn ngữ của mô hình thật cần được kiểm tra riêng bằng live smoke test hoặc
LLM-as-judge khi có API key.

## Term Search Regression

`term_search_regression.jsonl` là bộ regression bổ sung sau khi phát hiện bug
hỏi thuật ngữ trong tài liệu. Bộ này tách riêng khỏi golden set 43 case để
không chỉnh lịch sử CP4.

Chạy từ thư mục gốc:

```powershell
codebase\backend\.venv\Scripts\python.exe -X utf8 eval\run_term_search_regression.py
```

Runner dùng retrieval thật, query planner thật và fixture offline có nhiều loại
thuật ngữ: tiếng Anh, tiếng Việt, cụm nhiều từ, hyphen, chữ viết tắt, typo,
không tồn tại và prefix mơ hồ. Kết quả mới nhất ghi vào
`eval/results/term_search_latest.json`.

Kết quả hiện tại: 14/14 case pass, `failed=[]`. Đây là regression về truy hồi
và evidence/citation, không phải live provider semantic evaluation.
