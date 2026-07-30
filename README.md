# VLearn Tutor theo ngữ cảnh

Prototype tối ưu AI Tutor hiện có trên VLearn: học viên đang đọc PDF có thể hỏi theo trang, đoạn bôi đen, vùng hình ảnh hoặc toàn tài liệu; hệ thống ưu tiên evidence thật, citation theo trang và nói rõ khi thiếu căn cứ.

Tên nhóm chính thức: **TODO - cần nhóm xác nhận trước khi nộp**.

## Mục tiêu lab

- Chọn một pain cụ thể có bằng chứng từ data pack VLearn.
- Viết spec sản phẩm AI theo `03-template-ai-spec.md`.
- Build prototype working cho lát cắt đã chọn.
- Đo bằng golden set và regression, không chỉnh số liệu để làm đẹp kết quả.
- Validation/reflection phải dùng dữ liệu người thật; repo hiện chỉ có template vì chưa có log thật.

## Thành viên và phân công

| Thành viên | MSSV | Phân công |
|---|---|---|
| Vũ Văn Phong | 2A202601647 | Spec owner, điều phối checkpoint, tổng hợp changelog |
| Đoàn Nhật Nam | 2A202601123 | Mining CSV, thống kê số liệu, quote và evidence có `conversation_id/turn_id` |
| Hà Duy Anh | 2A202601511 | JTBD, problem statement, impact table, pain candidates bị loại |
| Nguyễn Quang Vinh | 2A202601517 | Prompt, failure taxonomy, HAX/PAIR và provider behavior |
| Hoàng Lê Minh | 2A202601653 | Prototype/frontend flow: PDF workspace, chat panel, attachment, reset/streaming UI |
| Phạm Sỹ Đức | 2A202601601 | Golden set, evaluation, validation plan và demo preparation |

## Problem và lát cắt

Pain đã chọn: khi học viên hỏi về trang/đoạn/vùng đang xem, tutor đôi khi không dùng đúng context hoặc citation, khiến học viên phải cung cấp lại thông tin và khó kiểm chứng câu trả lời.

Lát cắt một câu: với học viên hỏi về một trang, đoạn văn hoặc vùng hình ảnh trong PDF, hệ thống quyết định context đó có đủ căn cứ để trả lời hay phải báo thiếu thông tin, để học viên nhận lời giải thích có thể kiểm chứng theo đúng trang.

## Kiến trúc ngắn gọn

- `fe/`: React Vite frontend, PDF workspace, page attachment, text selection, visual region, chat streaming.
- `be/`: FastAPI backend, document upload, page extraction, chunking, embedding, retrieval, answer orchestration.
- Storage local: SQLite ở `app/storage/index/vlearn.db`, PDF/runtime cache trong `app/storage/...`.
- Provider: OpenAI/Gemini qua env; tests và eval offline dùng provider giả.

Active chat path:

```text
Frontend
-> POST /api/v2/chat hoặc /api/v2/chat/stream
-> InteractionResolver
-> OrchestrationService
-> RetrievalService / PageContextService / VisualContextService
-> AnswerService
-> ProviderGateway
```

## Các flow chính

- General chat khi không có document hoặc user cho phép kiến thức chung.
- Page chat khi user gắn trang, hỏi trang cụ thể hoặc hỏi "trang này".
- Text selection chat khi đoạn bôi đen khớp nội dung trang.
- Visual region chat khi user khoanh vùng ảnh/bảng/biểu đồ.
- Document search khi user hỏi toàn tài liệu, gồm truy hồi thuật ngữ.
- Document visual search khi câu hỏi toàn tài liệu có tín hiệu hình/bảng/figure.
- Streaming SSE qua `/api/v2/chat/stream` với event `meta`, `delta`, `done`, `error`.
- Conversation memory dùng recent window + rolling digest.

## Cơ chế retrieval

- Lexical: BM25 trên token đã normalize; BM25 score 0 không còn được xem là hit.
- Dense: embedding query/chunk, mặc định HuggingFace nếu có thể tải model, fallback hash embedding để test offline ổn định.
- Hybrid: merge lexical và dense bằng reciprocal-rank style score, lọc theo `retrieval_min_score`.
- Term extraction: nhận diện câu định nghĩa/giải thích tiếng Việt và tiếng Anh, tách term trung tâm như `encoder`, `RAG`, `multi head attention`, `chuỗi cung ứng`.
- Query variants: giữ query gốc, term trích ra, bản normalize/bỏ dấu khi khác, biến thể hyphen như `multi-head attention`, và candidate typo nếu đủ chắc; giới hạn tối đa 5 variant.
- Typo-tolerant search: RapidFuzz so với vocabulary động lấy từ heading/text/chunk của tài liệu hiện tại. Không dùng dictionary hardcode theo domain.
- Guardrail: không sửa term quá ngắn, không sửa nếu exact phrase đã có, không sửa prefix/truncated mơ hồ, không sửa khi similarity thấp hoặc nhiều candidate gần ngang nhau.
- Evidence/citation: merge theo `chunk_id`, boost exact phrase trong heading/text, ưu tiên page khác nhau và chỉ citation các chunk thật sự đưa vào prompt.

## Chạy backend

```powershell
cd be
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Chạy frontend

```powershell
cd fe
npm install
Copy-Item .env.example .env
npm run dev
```

Mở `http://localhost:5173`. Swagger backend ở `http://localhost:8000/docs`.

## Env an toàn

Không commit `.env`, API key, `.venv`, `node_modules`, PDF upload runtime, SQLite runtime ngoài artifact được chủ đích track, cache hoặc model cache.

Các biến chính: `OPENAI_API_KEY`, `OPENAI_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `PRIMARY_TEXT_PROVIDER`, `FALLBACK_TEXT_PROVIDER`, `VISION_PRIMARY_PROVIDER`, `VISION_FALLBACK_PROVIDER`, `ENABLE_GEMINI_FALLBACK`.

## Tests và eval

```powershell
$env:PYTHONPATH=".;be"
python -m compileall be/app
pytest -q be/tests/unit/test_query_planner.py be/tests/integration/test_document_search.py be/tests/integration/test_chat_v2_mvp.py be/tests/integration/test_chat_v2_streaming.py
pytest -q be/tests
python -X utf8 eval/run_eval.py
python -X utf8 eval/run_term_search_regression.py
```

Golden eval hiện có 43 case trong `eval/golden_set.jsonl`. Latest tracked result: `eval/results/latest.json`, 43/43 pass, quality bar passed.

Term-search regression mới ở `eval/term_search_regression.jsonl`. Latest result: `eval/results/term_search_latest.json`, 14/14 pass.

Live provider tests trong `be/tests/live/` chỉ chạy khi có API key thật; không tính là PASS nếu bị skip hoặc chưa chạy.

## Phần thật và phần fake

- Thật trong prototype: upload PDF, extract text, chunking, embedding/retrieval, render page/crop, routing, citation, provider gateway, streaming, conversation state.
- AI thật khi có env key: text/multimodal provider qua OpenAI hoặc Gemini.
- Fake trong tests/eval offline: provider giả trả text cố định để kiểm contract, routing, prompt context, fallback và citation; không dùng để kết luận chất lượng semantic của model thật.

## Limitation

- Chưa có authentication/permission model.
- Chưa OCR đầy đủ cho scanned PDF; visual flow dựa vào ảnh trang/crop và text extraction hiện có.
- SQLite/local storage phù hợp prototype, chưa phải production deployment.
- Document search chỉ truy hồi top-k chunks, không khẳng định đã đọc toàn bộ PDF ở mỗi câu hỏi.
- Validation với người thật và quote nguyên văn chưa có trong repo, đang blocked bởi dữ liệu người thật.
- Tên nhóm chính thức chưa có nguồn xác nhận trong repo.

## Artifact

| Artifact | Trạng thái | Ghi chú |
|---|---|---|
| `spec.md` | PARTIAL | Đủ spec chính, còn blocked tên nhóm/willing users/validation thật |
| `cp1-canvas.md` | PARTIAL | Đã điền phân công, willing users còn blocked |
| `evidence/` | PASS | Có mining report với số liệu và quote nguồn |
| `eval/` | PASS | Có golden set, runner, latest result và term regression |
| `validation/` | BLOCKED_BY_REAL_USER_DATA | Có template, chưa có người thử/quote thật |
| `reflection/` | BLOCKED_BY_REAL_USER_DATA | Có template từng thành viên, mỗi người phải tự điền |
| `lab-audit.md` | PASS | Audit rubric/artifact hiện tại |
| Slide | Ngoài phạm vi task này | Người dùng tự làm slide; Codex không tạo/sửa slide |
