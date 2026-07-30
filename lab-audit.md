# Lab Artifact Audit

Ngày audit: 2026-07-30.

Phạm vi audit: artifact văn bản trong repo và code/test hiện có. Slide do người dùng tự hoàn thiện; Codex không tạo, không sửa và không đánh giá nội dung slide trong task này. Thiếu slide không thuộc phạm vi task hiện tại.

| Requirement/Rubric | Artifact yêu cầu | Bằng chứng hiện tại | Trạng thái | Việc đã sửa | Blocker còn lại |
|---|---|---|---|---|---|
| R1: Bằng chứng và impact | `spec.md` §1-§2, evidence mining | `evidence/cp1-vlearn-chatlog-mining.md` có 2.522 messages, 1.261 turns, 164 strong cases, >=5 quote có `conversation_id/turn_id`; `spec.md` có impact table 3 ứng viên | PASS | Đối chiếu README/spec/evidence, giữ số liệu nhất quán | Không có khảo sát A; repo dựa trên chuẩn mining B |
| R2: Lát cắt và thiết kế | `spec.md` §4 | Lát cắt một câu, non-goals, working prototype, automation conditional, HAX/PAIR >=4 | PASS | Bổ sung retrieval thuật ngữ trong phần thiết kế | Tên nhóm chính thức còn TODO |
| R3: Chỗ khó và kịch bản | `spec.md` §5-§6 | Có 4 lớp chỗ khó, >=8 kịch bản, happy/low-confidence/failure/correction | PASS | Bổ sung kịch bản term typo, no-evidence và ambiguous prefix | Không có blocker artifact |
| R4: Kiểm thử | `spec.md` §7, `eval/`, backend tests | Golden set 43 case, quality bar, `eval/results/latest.json`; regression term-search 14 case | PASS | Thêm `eval/term_search_regression.jsonl`, `eval/run_term_search_regression.py`, `eval/results/term_search_latest.json` | Live provider semantic quality chưa chạy nếu thiếu API key |
| R5: Prototype | `fe/`, `be/`, README commands | FastAPI + React Vite, upload PDF, page/selection/visual/document search, streaming, citation | PASS | README mô tả phần thật/fake và cách chạy | Chưa audit slide/demo live vì ngoài phạm vi task |
| R6: Validation | `validation/` | Chưa có người thử/quote thật trong repo | BLOCKED_BY_REAL_USER_DATA | Tạo `validation/README.md` template đúng format và ghi blocker | Cần >=5 người ngoài nhóm, quote nguyên văn, severity, hành động |
| R7: Quy trình và repo | README, cấu trúc repo | README có thành viên/MSSV/phân công, link artifact; repo có spec, evidence, eval, validation, reflection, audit | PASS | README được viết lại theo artifact nhóm | Tên nhóm chính thức còn cần xác nhận |
| CP1: Canvas | `cp1-canvas.md` | Có hướng, job executor, pain, evidence, lát cắt, automation, assumption | PARTIAL | Điền phân công bằng tên thật từ README/spec; willing users chuyển blocker thật | Cần 3 willing users thật ngoài nhóm |
| CP2: Prototype bấm được | `fe/`, `be/` | Frontend/backend có flow upload/chat/page attachment | PASS | README ghi cách chạy frontend/backend | Cần nhóm tự demo live |
| CP3: AI thật + đo lượt đầu | `be/app/services/provider_gateway.py`, `eval/` | Provider gateway thật qua env; eval offline provider giả; latest 43/43 | PARTIAL | README/spec phân biệt fake eval với live provider | Cần log/trace live provider thật nếu rubric yêu cầu |
| CP4: Spec + quality bar | `spec.md`, `eval/results/latest.json` | Quality bar chốt trong `eval/run_eval.py`, latest 43/43 | PASS | Giữ golden set 43 case, thêm regression riêng không sửa lịch sử | Không có blocker artifact |
| CP5: Validation + dry run | `validation/`, slide do user tự làm | Chưa có feedback log thật, chưa có dry-run artifact trong repo | BLOCKED_BY_REAL_USER_DATA | Tạo validation template | Cần nhóm chạy validation/dry run thật |
| CP6: Demo | Slide/demo | Người dùng tự làm slide theo yêu cầu task | BLOCKED_BY_REAL_USER_DATA | Ghi rõ ngoài phạm vi Codex task | Cần người dùng tạo slide và demo live |
| Checklist nộp cuối: README | `README.md` | Có project, mục tiêu, thành viên, flow, retrieval, commands, eval, limitation, artifact status | PASS | Viết lại README | Tên nhóm chính thức còn TODO |
| Checklist nộp cuối: Spec | `spec.md` | Đủ §1-§9, changelog có term retrieval bug | PARTIAL | Bổ sung root cause, mechanism và regression | Willing users/validation/tên nhóm còn TODO |
| Checklist nộp cuối: Eval | `eval/` | Golden set + latest result + term regression + runner | PASS | Thêm regression riêng và README eval | Live provider test chưa chạy nếu thiếu key |
| Checklist nộp cuối: Validation | `validation/README.md` | Template đúng format, không có dữ liệu giả | BLOCKED_BY_REAL_USER_DATA | Tạo template | Cần dữ liệu người thật |
| Checklist nộp cuối: Reflection | `reflection/*.md` | 6 template theo thành viên xác định được | BLOCKED_BY_REAL_USER_DATA | Tạo template từng thành viên | Mỗi thành viên phải tự viết nội dung cá nhân |
| Checklist nộp cuối: Slide | `demo-slides.pdf` | Không kiểm tra/tạo theo phạm vi task | BLOCKED_BY_REAL_USER_DATA | Không tạo hoặc sửa slide | Người dùng tự hoàn thiện slide |

## Tóm tắt trạng thái

- PASS: R1, R2, R3, R4, R5, R7, CP2, CP4, checklist README/eval.
- PARTIAL: CP1, CP3, checklist spec.
- MISSING: Không ghi nhận artifact văn bản bắt buộc nào bị thiếu hoàn toàn sau audit; validation/reflection có template nhưng thiếu dữ liệu thật.
- BLOCKED_BY_REAL_USER_DATA: R6, CP5, CP6/slide, validation thật, reflection cá nhân, willing users, tên nhóm chính thức nếu nhóm không xác nhận.
- BLOCKED_BY_ENVIRONMENT: Live provider smoke/semantic test nếu môi trường không có API key.
