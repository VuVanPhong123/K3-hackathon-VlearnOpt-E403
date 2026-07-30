# VLearn Tutor theo ngữ cảnh

Prototype tối ưu AI Tutor hiện có trên VLearn: học viên đang đọc PDF có thể hỏi theo trang, đoạn bôi đen, vùng hình ảnh hoặc toàn tài liệu; hệ thống ưu tiên evidence thật, citation theo trang và nói rõ khi thiếu căn cứ.

Tên nhóm chính thức: **VlearnOpt**.

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

## Tính năng chính

- Upload PDF, trích xuất text, render page/crop và tạo index local.
- Page chat, active page, attached page, text selection và visual region.
- Document search và retrieval thuật ngữ với lexical/dense hybrid, typo guardrail và citation.
- Streaming SSE qua `/api/v2/chat/stream` với event `meta`, `delta`, `done`, `error`.
- Conversation reset và memory bằng recent window + rolling digest.
- Provider thật qua OpenAI/Gemini khi có env key; eval offline dùng provider giả.

## Kiến trúc

```text
codebase/frontend
-> POST /api/v2/chat/stream
-> InteractionResolver
-> OrchestrationService
-> RetrievalService / PageContextService / VisualContextService
-> AnswerService
-> ProviderGateway
```

## Cấu trúc repository

```text
repo/
├── README.md
├── spec.md
├── codebase/
│   ├── backend/
│   └── frontend/
├── evidence/
│   ├── cp1-vlearn-chatlog-mining.md
│   └── scripts/
├── eval/
│   ├── golden_set.jsonl
│   ├── term_search_regression.jsonl
│   ├── pdf_eval_fixture.py
│   ├── run_eval.py
│   ├── run_term_search_regression.py
│   └── results/
├── validation/
└── reflection/
```

`evidence/` được giữ ngoài cấu trúc tối thiểu vì rubric yêu cầu log mining có bằng chứng kiểm chứng được.

## Chạy backend

```powershell
cd codebase/backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger ở `http://localhost:8000/docs`.

## Chạy frontend

```powershell
cd codebase/frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Mở `http://localhost:5173`.

## Environment variables

Không commit `.env`, API key, `.venv`, `node_modules`, PDF upload runtime, SQLite runtime hoặc cache.

Các biến chính: `OPENAI_API_KEY`, `OPENAI_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `PRIMARY_TEXT_PROVIDER`, `FALLBACK_TEXT_PROVIDER`, `VISION_PRIMARY_PROVIDER`, `VISION_FALLBACK_PROVIDER`, `ENABLE_GEMINI_FALLBACK`.

## Eval

```powershell
$env:PYTHONPATH=".;codebase/backend"
python -m compileall codebase/backend/app eval
python -X utf8 eval/run_eval.py --document "path/to/d2-slide-hackathon.pdf"
python -X utf8 eval/run_term_search_regression.py --document "path/to/d2-slide-hackathon.pdf"
```

Golden eval có 43 case trong `eval/golden_set.jsonl`. Latest tracked result: `eval/results/latest.json`, 43/43 pass, quality bar passed trên PDF thật `d2-slide-hackathon.pdf`:

- sha256: `5f729b2788a8f6d56a2252f96e96efec8e8cf7d66a20b39d470bca38f0754c5d`
- size: `2,435,727` bytes
- physical pages: `29`

Term-search regression ở `eval/term_search_regression.jsonl`. Latest result: `eval/results/term_search_latest.json`, 14/14 pass.

PDF eval không commit vào repo. Runner dùng `PageExtractionService`, `SectionService`, `ChunkingService`, `RetrievalService`, hash embedding và PyMuPDF render thật; nếu không truyền được PDF hoặc không có `eval/fixtures/d2-slide-hackathon.pdf`, runner fail rõ, không fallback sang fixture text giả.

## Phần thật và phần fake

- Thật trong prototype: upload PDF, extract text, chunking, embedding/retrieval, render page/crop, routing, citation, provider gateway, streaming, conversation state.
- AI thật khi có env key: text/multimodal provider qua OpenAI hoặc Gemini.
- Fake trong eval offline: provider giả trả text cố định để kiểm contract, routing, prompt context, fallback và citation; không dùng để kết luận chất lượng semantic của model thật.

## Limitations

- Chưa có authentication/permission model.
- Chưa OCR đầy đủ cho scanned PDF; visual flow dựa vào ảnh page/crop và text extraction hiện có.
- SQLite/local storage phù hợp prototype, chưa phải production deployment.
- Document search chỉ truy hồi top-k chunks, không khẳng định đã đọc toàn bộ PDF ở mỗi câu hỏi.
- Prototype đã được thử nghiệm với 7 người vào ngày 30/07/2026. Báo cáo tại `validation/README.md` đã ghi nhận đủ 7 quote nguyên văn, 2 willing user và các chủ đề feedback; 5 người còn lại chỉ test nhanh, không phải willing user.
- Reflection cá nhân đã được nhóm kiểm tra theo phân công trong repo.
- `demo-slides.pdf` do người dùng tự bổ sung ngoài phạm vi dọn repo này; task này không tạo hoặc sửa slide.
- Data pack gốc đã bị xóa khỏi working tree; các evidence còn lại chỉ giữ quote ngắn và mã nguồn tham chiếu.

## Artifact status

| Artifact | Trạng thái | Ghi chú |
|---|---|---|
| `spec.md` | DONE | Đủ spec chính, đã có validation 7 người, 7 quote và 2 willing user |
| `codebase/` | PASS | Chứa source backend/frontend chạy prototype |
| `evidence/` | PASS | Có mining report với số liệu và quote nguồn ngắn |
| `eval/` | PASS | Có golden set, runner, latest result và term regression |
| `validation/` | DONE | Đã test 7 người ngày 30/07/2026; đã ghi 7 quote nguyên văn, 2 willing user và feedback tổng hợp |
| `reflection/` | DONE | Reflection cá nhân đã được nhóm kiểm tra theo phân công |
| Slide | USER_HANDLED | Người dùng tự bổ sung `demo-slides.pdf`; Codex không tạo/sửa slide trong cleanup này |
