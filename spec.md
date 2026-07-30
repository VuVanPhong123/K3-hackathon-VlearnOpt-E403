# AI SPEC - VLearn Tutor theo ngữ cảnh - Nhóm VlearnOpt

Tên nhóm chính thức: VlearnOpt.
Hướng: [x] A - VLearn
Loại: [x] Tối ưu tính năng có sẵn

## §1. User & Job

- Job executor + workflow: Học viên đang học trực tiếp trên VLearn, đã chọn một trang, đoạn văn bản hoặc vùng nội dung chưa hiểu và muốn được giải thích ngay trong lúc học. Người dùng đang đọc PDF, kéo trang vào chat, bôi đen văn bản hoặc khoanh vùng hình ảnh để hỏi Tutor.
- Core JTBD: Hiểu đúng nội dung của phần tài liệu đang xem để tiếp tục bài học mà không phải nhập lại toàn bộ ngữ cảnh.
- Problem statement: Khi yêu cầu giải thích nội dung đang xem, học viên đôi khi không nhận được câu trả lời dựa đúng trên trang hoặc vùng đã chọn, phải cung cấp lại thông tin hoặc có nguy cơ nhận nguồn không khớp.

Evidence đạt chuẩn mining B, ghi chi tiết tại `evidence/cp1-vlearn-chatlog-mining.md`:

- Nguồn dữ liệu ban đầu: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`. Data pack gốc không nằm trong repo nộp bài cuối; evidence giữ số liệu tổng hợp, quote ngắn và mã `conversation_id/turn_id` để kiểm chứng.
- Tổng 2.522 messages, 1.261 question-answer turns, 1.261 tutor responses.
- 582/1.261 tutor responses không có citation, tương đương 46,2%.
- 175/1.261 tutor responses có ngôn ngữ retrieval/fallback, tương đương 13,9%; 13 response trong nhóm này bị `rating=down`.
- 164 turn có user ghi `Trang N`, tutor dùng ngôn ngữ retrieval/fallback và `citations=[]`.
- 239 turn có `Trang N` nhưng citation không chứa selected page.
- 32 visual/chart/image intents; 6 có failure hoặc mismatch signal.

Năm case nguyên văn đại diện, có `conversation_id` và `turn_id`:

| Evidence | conversation_id | turn_id | Tín hiệu |
|---|---|---|---|
| CP1-E01 | C0021 | T0769 | User hỏi trang 4: `(Trang 4, đoạn được chọn: "giải thích nghĩa chi tiết của trang 4") giải thích nghĩa chi tiết của trang 4`. Tutor trả lời không tìm thấy nội dung cụ thể cho trang 4, yêu cầu cung cấp nội dung/tiêu đề, `citations=[]`, `rating=down`. |
| CP1-E02 | C0023 | T0399 | User hỏi trang 6: `(Trang 6, đoạn được chọn: "Giải thích biều đồ đc bôi đỏ") Giải thích biều đồ đc bôi đỏ`. Tutor nói kết quả tra cứu trang 6 đang trả về nội dung trang 71, `citations=[71]`. |
| CP1-E03 | C0001 | T0649 | User hỏi trang 37: `(Trang 37, đoạn được chọn: "tóm tắt nội dung chính trong slide này") tóm tắt nội dung chính trong slide này`. Tutor không tìm thấy nội dung cụ thể cho slide 37, `citations=[]`. |
| CP1-E04 | C0015 | T0811 | User chọn đoạn có `ReAct`: `(Trang 2, đoạn được chọn: "Designt Pattern ReAct là gì có lưu ý gì về nó?")`. Tutor vẫn không tìm thấy định nghĩa chi tiết về ReAct, `citations=[]`. |
| CP1-E05 | C0002 | T0092 | User nêu ba chủ đề trên trang 50: `kỹ thuật tối ưu prompt, cơ chế gọi tool và cách xử lý ngữ cảnh`. Tutor vẫn hỏi lại tên chủ đề/mục tiêu học tập, `citations=[]`. |
| CP1-E10 | C0547 | T0135 | User hỏi tóm tắt các giai đoạn trên biểu đồ ở trang 16, tutor không tìm thấy nội dung liên quan và bị `rating=down`. |

Giới hạn của evidence: chatlog chứng minh tín hiệu hành vi và failure signal, không chứng minh học viên mất niềm tin, không kết luận mọi citation đều sai, và không xác định chắc chắn nguyên nhân kỹ thuật là retriever, page mapping hay thiếu visual context.

## §2. Impact & Quyết Định Chọn

| Ứng viên pain | Tác động | Tần suất / evidence | Effort | Quyết định |
|---|---|---:|---|---|
| Không sử dụng đúng selected page/context | Học viên phải nhập lại context hoặc nhận câu trả lời không có nguồn kiểm chứng. | 164 strong cases `Trang N` + fallback + empty citations; thêm 239 case citation không chứa selected page. | Cao khả thi trong hackathon: gắn page, text selection, retrieval và citation đã có đường build rõ. | Chọn làm slice trung tâm. |
| Không đọc được bảng, hình và biểu đồ | Học viên không hiểu phần visual trên slide dù đã chỉ ra vị trí cần hỏi. | 32 visual/chart/image intents; 6 có failure/mismatch; CP1-E02, CP1-E10. | Trung bình: cần render page/crop và provider vision; chưa có OCR riêng. | Đưa vào scope prototype qua page image và visual region, nhưng không chọn làm pain primary độc lập. |
| Không tìm được nội dung trong toàn tài liệu | Học viên không nhận được phần liên quan khi câu hỏi không gắn trang cụ thể. | Whole-session/document summary intents 57; 37 có failure/empty citation signal. | Trung bình đến cao: cần retrieval đa trang và coverage. | Đưa vào backlog/secondary mode document search; không mở thành summarization toàn bộ trong CP4. |

Lý do chọn ứng viên 1: số lượng case mạnh nhất, có nhiều quote kiểm tra được, có downvote, phù hợp lát cắt một việc là giải thích nội dung đang xem. Ứng viên visual/table/figure được hỗ trợ trong prototype vì có liên quan trực tiếp tới selected context, nhưng không phóng đại thành OCR hoàn chỉnh. Ứng viên tìm toàn tài liệu và summary toàn bộ bị loại khỏi primary slice vì scope rộng hơn và cần đánh giá coverage riêng.

## §3. Giải Pháp Tương Tự Đã Nghiên Cứu

- ChatGPT với file/PDF: flow mạnh ở chat liên tục và có thể hỏi về file, nhưng nếu không gắn đúng trang/nguồn thì user khó kiểm chứng trong bài học. VLearn Tutor cần ưu tiên trang/vùng đang xem và citation theo page.
- NotebookLM: đáng học ở việc hiện nguồn cạnh câu trả lời và buộc người dùng quay lại source. Điểm cần né là không biến prototype thành công cụ tổng hợp toàn bộ notebook; slice này chỉ giải thích page/selection/region.
- Khanmigo / tutor học tập: đáng học ở giọng điệu hỗ trợ và không đưa đáp án thay học viên trong ngữ cảnh học. Điểm cần né là trả lời quá tự tin khi thiếu căn cứ.
- ChatPDF / AskYourPDF: flow upload và hỏi tài liệu nhanh, nhưng thường tập trung toàn tài liệu; VLearn khác ở việc user đang ở đúng trang, có drag page, text selection, visual region và citation click.

Không có số liệu mới được tạo cho mục này; đây là tổng hợp flow tương tự ở mức định hướng thiết kế.

## §4. Thiết Kế

- Lát cắt một câu: Với học viên hỏi về một trang, đoạn văn hoặc vùng hình ảnh trong PDF, hệ thống quyết định ngữ cảnh đó có đủ căn cứ để trả lời hay phải báo thiếu thông tin, để học viên nhận lời giải thích có thể kiểm chứng theo đúng trang.
- Quyết định AI trung tâm: AI quyết định nội dung trong trang, đoạn văn hoặc vùng hình ảnh được chọn có đủ căn cứ để trả lời hay phải thông báo chưa đủ thông tin.
- Mức prototype: [x] Working. Flow thật: upload PDF, extract page text, build retrieval index, render page/crop image, call model provider, return answer with citation. Citation click, drag page, text selection, visual region, streaming UI, reset conversation và truy hồi thuật ngữ toàn tài liệu đã có. Limitations: chưa authentication, chưa OCR đầy đủ cho scanned PDF, dùng SQLite/local storage, offline eval không tự chấm toàn bộ semantic correctness của model thật.
- Model: Text primary theo env/source là OpenAI qua `OPENAI_MODEL`, default `gpt-5-mini`. Vision primary là Gemini qua `GEMINI_VISION_MODEL` hoặc `GEMINI_MODEL`, default `gemini-3.5-flash-lite`. Infrastructure fallback OpenAI <-> Gemini theo `PRIMARY_TEXT_PROVIDER`, `FALLBACK_TEXT_PROVIDER`, `VISION_PRIMARY_PROVIDER`, `VISION_FALLBACK_PROVIDER` và `ENABLE_GEMINI_FALLBACK`.
- Automation: Conditional automation. Đủ context thì trả lời có citation. Không đủ context thì nói rõ hoặc hỏi lại. Cost-of-error: trả lời sai hoặc cite sai có thể làm học viên học sai nội dung bài học, nên không đoán khi thiếu căn cứ.
- Retrieval thuật ngữ: `RetrievalService` dùng `QueryPlanner.plan_for_retrieval` để nhận diện câu định nghĩa/giải thích, tách term trung tâm, sinh tối đa 5 query variants, sửa typo bằng vocabulary động từ heading/text/chunk trong tài liệu, merge lexical/dense theo `chunk_id`, boost exact phrase ở heading/text và chỉ citation chunk thật sự đưa vào prompt. Không hardcode `encoder`, tên tài liệu hay số trang.

Non-goals:

- Không làm authentication.
- Không làm collaborative annotation.
- Không làm LMS production hoàn chỉnh.
- Không gửi toàn bộ PDF vào mọi request.
- Không tự đưa đáp án bài kiểm tra.
- Không khai OCR đầy đủ cho scanned PDF.

Nguyên tắc HAX/PAIR áp dụng:

| Nguyên tắc | Áp cụ thể vào prototype |
|---|---|
| Làm rõ khả năng và giới hạn | Welcome message trong `ChatPanel` nói user có thể nhập câu hỏi, kéo trang, bôi đen văn bản hoặc khoanh vùng hình ảnh; spec và README ghi rõ chưa authentication/OCR đầy đủ. |
| Hiển thị citation đúng trang | `ChatResponseV2.citations` trả `page_number`; `ChatMessage` hiện nút `Trang N`; click citation gọi `onCitationClick` để nhảy đến page card. |
| Cho phép người dùng sửa/chọn lại context | `PageAttachment` có nút remove; context mới từ drag page/text selection/visual region thay context cũ. |
| Hỗ trợ correction bằng xóa attachment và tạo cuộc trò chuyện mới | `ChatPanel` có nút `Cuộc trò chuyện mới`, abort stream đang chạy, xóa conversation server theo best effort và reset local context. |
| Không đoán khi thiếu căn cứ | Prompt page/selection/document search yêu cầu chỉ trả lời dựa trên nội dung thấy được và nói rõ khi không đủ bằng chứng. |
| Hiển thị tiến trình phản hồi bằng streaming | `/api/v2/chat/stream` trả SSE `meta/delta/done/error`; frontend nối delta vào một assistant bubble. |

## §5. Kiểu Lỗi - 4 Lớp Chỗ Khó Và Kịch Bản

Không thêm golden-set case mới trong CP4. Các kịch bản dưới đây dựa trên 43 case hiện có trong `eval/golden_set.jsonl`.

| Lớp | Kịch bản | Trigger | Hành vi mong muốn | Hành vi không cho phép | Hậu quả | Case liên quan |
|---|---|---|---|---|---|---|
| Không có căn cứ | Trang không tồn tại | User hỏi trang 99 | HTTP 400 nói tài liệu không có trang 99 | Gọi provider và đoán nội dung | Học sai/cite sai | `page_out_of_range` |
| Không có căn cứ | Không có document khi cần page | User gắn page nhưng thiếu `document_id` | HTTP 400 yêu cầu có PDF | Trả lời bằng trí nhớ chung | Mất grounding | `page_missing_document` |
| Không có căn cứ | Selection bị forge | Selected text không khớp page text | Từ chối với lỗi không khớp nội dung trang PDF | Chấp nhận selected text giả | Học viên tin vào context sai | `selection_forged` |
| Mơ hồ/confidence thấp | Câu hỏi visual cần đúng trang | User hỏi biểu đồ/hình trên page | Dùng image render/crop và page text, citation đúng trang | Chỉ trả lời text chung | Bỏ sót thông tin visual | `visual_region_standard`, `page_visual_question` |
| Mơ hồ/confidence thấp | Câu hỏi không gắn page nhưng có document | User hỏi RAG/multi-head | Retrieval chọn page liên quan, citation | Lấy active page bất kỳ | Citation lệch nguồn | `search_rag`, `search_multi_head` |
| Ngoài phạm vi/không được phép | General chat bị ép search nhưng không document | `interaction_mode=document_search` không có PDF | Rơi về general chat an toàn | Báo đã search tài liệu không tồn tại | Gây hiểu nhầm | `forced_search_without_document` |
| Ngoài phạm vi/không được phép | Provider request/config sai | Provider báo bad request/model/key invalid | Không fallback, báo lỗi cấu hình rõ | Fallback để che lỗi config | Khó debug và sai provider | `provider_text_request_error` |
| Sai gây hậu quả thật | Citation không đúng selected page | User hỏi trang cụ thể | Citation phải đúng page đã dùng trong context | Citation sang page khác | Học viên học sai source | `page_real_C0021_T0769`, `page_real_C0266_T1084` |
| Sai gây hậu quả thật | Fallback provider sai thời điểm | Primary lỗi tạm thời trước khi có answer | Fallback chỉ với temporary/rate/timeout/5xx trước delta đầu | Fallback sau khi đã gửi partial delta hoặc fallback với bad request | Kết quả không nhất quán | `fallback_text_temporary`, `fallback_vision_temporary` |
| Sai gây hậu quả thật | Lịch sử chat quá dài/rò context | History dài hơn giới hạn | Chỉ dùng recent window theo config, không đưa lượt cũ nhất | Gửi vô hạn hoặc leak welcome/local UI | Tăng token, nhiễu context | `history_limit_general` |
| Mơ hồ/confidence thấp | Hỏi định nghĩa thuật ngữ có typo nhỏ | User hỏi `encodr là gì` khi document có `encoder` rõ ràng | Sửa typo bằng candidate lấy từ chính document, vẫn giữ query gốc trong plan | Hardcode thuật ngữ hoặc tự sửa sang từ không có trong document | Không tìm thấy evidence hoặc cite sai | `term_encoder_typo`, `test_document_term_typo_is_corrected_from_document_vocabulary` |
| Không có căn cứ | Hỏi thuật ngữ không tồn tại | User hỏi `xyzabc là gì` | Không tạo citation, prompt báo không tìm thấy bằng chứng phù hợp | Trả kiến thức chung trong document-only hoặc cite giả | Học viên tin nhầm tài liệu có nội dung đó | `term_nonexistent`, `test_document_term_no_evidence_does_not_create_fake_citation` |
| Mơ hồ/confidence thấp | Typo/prefix mơ hồ | Document có `encoder` và `encoding`, user hỏi `encod là gì` | Không âm thầm chọn một candidate; không trả citation tùy tiện | Tự chọn `encoder` chỉ vì phổ biến hơn | Sai ý người dùng | `term_ambiguous_prefix`, `test_ambiguous_prefix_typo_is_not_silently_rewritten` |

## §6. Bốn Đường Đi Của Trải Nghiệm

- Happy path: User mở PDF, kéo một trang hoặc chọn text/region, hỏi. Backend validate document/page/selection, tạo context, gọi provider text hoặc multimodal, lưu conversation và trả answer kèm citation. Case: `page_attached_standard`, `selection_valid`, `visual_region_standard`.
- Low-confidence: User hỏi nội dung có thể cần tìm trong toàn tài liệu. Backend retrieval các page liên quan; nếu evidence yếu, prompt yêu cầu nói rõ không đủ thông tin. Case: `search_grounded_abstention`.
- Failure/no evidence: Trang ngoài range, thiếu document, selection không khớp hoặc provider chưa có key. Hệ thống trả lỗi rõ ràng, không gọi model khi validation fail. Case: `page_out_of_range`, `page_missing_document`, `selection_forged`, `provider_credentials_missing`.
- Correction: User xóa attachment, chọn lại page/text/region hoặc tạo chat mới. Nút tạo chat mới abort stream đang chạy, xóa conversation server theo best effort, reset messages/attachment và focus textarea.
- Term search: User hỏi `encoder là gì`, `RAG nghĩa là gì`, `multi head attention hoạt động thế nào` hoặc có typo nhỏ như `overfiting`. Backend tách term, tạo variants, sửa typo có guardrail nếu document vocabulary đủ chắc, rồi đưa 2-4 chunk evidence vào prompt kèm citation thật.
- Ngoài phạm vi: Khi user ép document search mà không có document, hệ thống không giả vờ có tài liệu và xử lý như general chat. Case: `forced_search_without_document`.
- Visual/table/figure: Page chat và visual region gửi image bytes cho vision provider; table/figure/chart có citation page. Case: `page_visual_question`, `search_table_comparison`, `visual_real_C0547_T0135`.
- Đổi tài liệu: Khi `currentDocument.id` thay đổi, frontend abort stream cũ, xóa conversation server cũ theo best effort, clear attachment/history và mở chat mới; không xóa PDF hay annotation.
- Tạo chat mới: Nút `Cuộc trò chuyện mới` reset context chat và server conversation; không xóa PDF, document metadata, annotation hoặc panel width.

## §7. Kiểm Thử

Golden set hiện có 43 case, giữ nguyên tổng số case. Trong đó 10 case được chuyển thể từ chatlog VLearn đã ẩn danh và 33 case tổng hợp. Không thêm golden case mới; chỉ cập nhật case history hiện có từ `max_history_count=8` sang `12` để khớp default mới.

Regression bổ sung sau bug truy hồi thuật ngữ: `eval/term_search_regression.jsonl` có 14 case mới, tách riêng với golden set CP4. Bộ này kiểm tra uppercase/lowercase, tiếng Việt có dấu/không dấu, cụm nhiều từ, hyphen, typo một từ, typo cụm từ, no-evidence và prefix mơ hồ. Runner: `python -X utf8 eval/run_term_search_regression.py`.

Chiều chất lượng và định nghĩa pass/fail:

- Status accuracy: status code đúng với expected.
- Mode accuracy: routing đúng `GENERAL_CHAT`, `PAGE_CHAT`, `TEXT_SELECTION_CHAT`, `VISUAL_REGION_CHAT`, `DOCUMENT_SEARCH_CHAT`.
- Page context accuracy: page đúng exact hoặc include required page.
- Citation accuracy: citation page đúng expected.
- Provider invocation/media path: gọi provider đúng/không gọi đúng text hoặc multimodal; image path có image khi cần.
- Fallback accuracy: provider và `fallback_used` đúng, attempted providers đúng với expected.
- Prompt context accuracy: prompt chứa/không chứa các chuỗi bắt buộc/cấm.
- History limit accuracy: không vượt giới hạn lịch sử theo case.
- UTF-8 response accuracy: answer/lỗi có dấu tiếng Việt.
- No crash: runner không crash.

Quality bar trong `eval/run_eval.py`:

| Metric | Bar | Latest actual |
|---|---:|---:|
| overall_case_pass_rate | 0.90 | 1.00 |
| status_accuracy | 1.00 | 1.00 |
| mode_accuracy | 0.95 | 1.00 |
| page_context_accuracy | 0.95 | 1.00 |
| citation_accuracy | 0.95 | 1.00 |
| provider_invocation_accuracy | 1.00 | 1.00 |
| media_path_accuracy | 1.00 | 1.00 |
| fallback_accuracy | 1.00 | 1.00 |
| prompt_context_accuracy | 0.95 | 1.00 |
| history_limit_accuracy | 1.00 | 1.00 |
| utf8_response_accuracy | 1.00 | 1.00 |
| no_crash_rate | 1.00 | 1.00 |

Kết quả latest sau implementation từ `eval/results/latest.json`: 43/43 case pass, `quality_bar_passed=true`, `failed_cases=[]`.

Kết quả term-search regression từ `eval/results/term_search_latest.json`: 14/14 case pass, `failed=[]`. Đây là kiểm thử offline của retrieval/plan/citation, không phải live provider semantic eval.

Offline eval chạy `OrchestrationService`, retrieval và fake provider. Nó kiểm tra contract, routing, page, media path, fallback, UTF-8 và history. Nó không thay thế việc chấm chất lượng ngôn ngữ của model thật và không phải bằng chứng tuyệt đối rằng model trả lời đúng kiến thức. Trước cleanup cuối, backend unit/integration tests đã chạy để ghi baseline; các test build-only không còn là artifact nộp bài. Nhóm không ghi PASS live provider trong repo vì buổi pitching dùng demo prototype và kết quả eval offline đã được chốt.

## §8. Phân Công & Kế Hoạch

Thành viên và phân công:

| Thành viên | MSSV | Phân công |
|---|---|---|
| Vũ Văn Phong | 2A202601647 | Spec owner, điều phối checkpoint, tổng hợp changelog. |
| Đoàn Nhật Nam | 2A202601123 | Evidence/mining, kiểm tra số liệu và quote có `conversation_id/turn_id`. |
| Hà Duy Anh | 2A202601511 | JTBD, problem statement, impact table, pain candidates bị loại. |
| Nguyễn Quang Vinh | 2A202601517 | Prompt, failure taxonomy, HAX/PAIR và provider behavior. |
| Hoàng Lê Minh | 2A202601653 | Frontend flow: PDF workspace, chat panel, attachment, reset/streaming UI. |
| Phạm Sỹ Đức | 2A202601601 | Eval/validation/demo, golden set, latest result và demo readiness. |

Willing users: TODO - chưa có tên người dùng ngoài nhóm được xác nhận trong repo. Đây là blocker CP5 và R6, cần người thật ngoài nhóm. Cần tối thiểu 5 người validation, ưu tiên 3 willing users từ CP1 nếu xác nhận được. Không có quote validation thật trong repo nên không đánh dấu R6 PASS.

Việc còn thiếu trước khi nộp:

- Validation ít nhất năm người ngoài nhóm, có tên/vai trò/quote thật.
- Bổ sung `demo-slides.pdf` sau khi nhóm tự hoàn thiện slide pitching.
- Mỗi thành viên đọc lại reflection draft và xác nhận nội dung cá nhân.

Không cần thêm live provider artifact cho đợt nộp này; nếu có API key trong lúc demo, chỉ dùng qua `.env` local và không commit key/log nhạy cảm.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| CP1 | Chốt pain selected-context/retrieval failure và canvas VLearn Tutor. | Mining cho thấy 164 strong cases `Trang N` + fallback + empty citation và 239 mismatch citation page. |
| CP2 | Có prototype PDF/chat: upload PDF, đọc page, chat với provider, drag page vào chat. | Cần flow bấm được để chứng minh học viên hỏi theo context đang xem. |
| CP3 | Mở rộng multimodal, text selection, visual region, retrieval và eval offline 43 case. | Bao phủ page, selection, region, document search, provider fallback và UTF-8. |
| CP4 | Track `eval/results/latest.json`, chốt quality bar và spec gần cuối; ghi kế hoạch hoàn thiện context/streaming/reset. | Artifact CP4 cần được commit/push trước khi thêm streaming; latest result 43/43 pass. |
| Sau CP4 | Thêm `/api/v2/chat/stream`, provider streaming, fallback rule trước delta đầu, rolling conversation digest + recent window 12 + character budget, nút `Cuộc trò chuyện mới`, document-switch cleanup và tests fake streaming provider. | Hoàn thiện các việc CP4 đã ghi là cần làm trước CP5 mà không thêm golden case mới. |
| Sau phát hiện bug thuật ngữ | Sửa query planning cho câu hỏi định nghĩa/giải thích thuật ngữ, thêm query variants, exact phrase boost, fuzzy correction có guardrail và regression 14 case. | Bug nằm trong primary slice document retrieval/context grounding: term có trong tài liệu nhưng query bị nhiễu bởi từ hội thoại hoặc typo nên evidence/citation không ổn định. |
