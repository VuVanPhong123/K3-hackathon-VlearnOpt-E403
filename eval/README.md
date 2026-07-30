# VLearn Tutor Eval

`golden_set.jsonl` có đúng 43 ca, giữ phân bổ category cũ. Trong đó có 10 ca được chuyển thể từ chatlog VLearn đã ẩn danh và 33 ca tổng hợp.

Bộ eval hiện chạy trên PDF thật `d2-slide-hackathon.pdf` (AI IN ACTION DAY 02 - Xác định bài toán cho AI), không còn hardcode text/page fixture. Runner đọc PDF bằng pipeline production: extract page text/block/bbox, detect section, chunk, hash embedding, retrieval, render full page/crop bằng PyMuPDF, rồi gọi provider giả để kiểm contract offline.

PDF không được commit. Khi chạy từ thư mục gốc, truyền rõ đường dẫn PDF:

```powershell
$env:PYTHONPATH=".;codebase/backend"
python -X utf8 eval/run_eval.py --document "path/to/d2-slide-hackathon.pdf"
```

Nếu có file local `eval/fixtures/d2-slide-hackathon.pdf`, runner có thể dùng làm default; nếu thiếu, runner fail rõ và không fallback sang text giả.

Kết quả mới nhất ghi vào `eval/results/latest.json`, gồm manifest tài liệu `{filename, sha256, size_bytes, page_count}` và `generated_at`, không ghi absolute PDF path.

## Term Search Regression

`term_search_regression.jsonl` có đúng 14 ca, tách riêng golden set 43 case. Bộ này dùng vocabulary/chunks sinh từ chính PDF Day 02, kiểm tra uppercase/lowercase, tiếng Việt có dấu/không dấu, cụm nhiều từ, hyphen, typo, no-evidence và prefix mơ hồ.

```powershell
$env:PYTHONPATH=".;codebase/backend"
python -X utf8 eval/run_term_search_regression.py --document "path/to/d2-slide-hackathon.pdf"
```

Kết quả mới nhất: golden 43/43 pass, quality bar passed; term regression 14/14 pass. Đây là regression offline về routing, retrieval, evidence/citation, media path và fallback, không phải live provider semantic evaluation.
