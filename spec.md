# AI SPEC - VLearn Tutor theo ngu canh - Nhom TODO
Huong: [x] A - VLearn
Loai: [x] Toi uu tinh nang co san

## §1. User & Job

- Job executor + workflow: Hoc vien dang hoc truc tiep tren VLearn, da chon mot trang, doan van ban hoac vung noi dung chua hieu va muon duoc giai thich ngay trong luc hoc. Nguoi dung dang doc PDF, keo trang vao chat, boi den van ban hoac khoanh vung hinh anh de hoi Tutor.
- Core JTBD: Hieu dung noi dung cua phan tai lieu dang xem de tiep tuc bai hoc ma khong phai nhap lai toan bo ngu canh.
- Problem statement: Khi yeu cau giai thich noi dung dang xem, hoc vien doi khi khong nhan duoc cau tra loi dua dung tren trang hoac vung da chon, phai cung cap lai thong tin hoac co nguy co nhan nguon khong khop.

Evidence dat chuan mining B, ghi chi tiet tai `evidence/cp1-vlearn-chatlog-mining.md`:

- Nguon du lieu: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`.
- Tong 2.522 messages, 1.261 question-answer turns, 1.261 tutor responses.
- 582/1.261 tutor responses khong co citation, tuong duong 46,2%.
- 175/1.261 tutor responses co ngon ngu retrieval/fallback, tuong duong 13,9%; 13 response trong nhom nay bi `rating=down`.
- 164 turn co user ghi `Trang N`, tutor dung ngon ngu retrieval/fallback va `citations=[]`.
- 239 turn co `Trang N` nhung citation khong chua selected page.
- 32 visual/chart/image intents; 6 co failure hoac mismatch signal.

Nam case nguyen van dai dien, co `conversation_id` va `turn_id`:

| Evidence | conversation_id | turn_id | Tin hieu |
|---|---|---|---|
| CP1-E01 | C0021 | T0769 | User hoi trang 4: `(Trang 4, đoạn được chọn: "giải thích nghĩa chi tiết của trang 4") giải thích nghĩa chi tiết của trang 4`. Tutor tra loi khong tim thay noi dung cu the cho trang 4, yeu cau cung cap noi dung/tieu de, `citations=[]`, `rating=down`. |
| CP1-E02 | C0023 | T0399 | User hoi trang 6: `(Trang 6, đoạn được chọn: "Giải thích biều đồ đc bôi đỏ") Giải thích biều đồ đc bôi đỏ`. Tutor noi ket qua tra cuu trang 6 dang tra ve noi dung trang 71, `citations=[71]`. |
| CP1-E03 | C0001 | T0649 | User hoi trang 37: `(Trang 37, đoạn được chọn: "tóm tắt nội dung chính trong slide này") tóm tắt nội dung chính trong slide này`. Tutor khong tim thay noi dung cu the cho slide 37, `citations=[]`. |
| CP1-E04 | C0015 | T0811 | User chon doan co `ReAct`: `(Trang 2, đoạn được chọn: "Designt Pattern ReAct là gì có lưu ý gì về nó?")`. Tutor van khong tim thay dinh nghia chi tiet ve ReAct, `citations=[]`. |
| CP1-E05 | C0002 | T0092 | User neu ba chu de tren trang 50: `kỹ thuật tối ưu prompt, cơ chế gọi tool và cách xử lý ngữ cảnh`. Tutor van hoi lai ten chu de/muc tieu hoc tap, `citations=[]`. |
| CP1-E10 | C0547 | T0135 | User hoi tom tat cac giai doan tren bieu do o trang 16, tutor khong tim thay noi dung lien quan va bi `rating=down`. |

Gioi han cua evidence: chatlog chung minh tin hieu hanh vi va failure signal, khong chung minh hoc vien mat niem tin, khong ket luan moi citation deu sai, va khong xac dinh chac chan nguyen nhan ky thuat la retriever, page mapping hay thieu visual context.

## §2. Impact & quyet dinh chon

| Ung vien pain | Tac dong | Tan suat / evidence | Effort | Quyet dinh |
|---|---|---:|---|---|
| Khong su dung dung selected page/context | Hoc vien phai nhap lai context hoac nhan cau tra loi khong co nguon kiem chung. | 164 strong cases `Trang N` + fallback + empty citations; them 239 case citation khong chua selected page. | Cao kha thi trong hackathon: gan page, text selection, retrieval va citation da co duong build ro. | Chon lam slice trung tam. |
| Khong doc duoc bang, hinh va bieu do | Hoc vien khong hieu phan visual tren slide du da chi ra vi tri can hoi. | 32 visual/chart/image intents; 6 co failure/mismatch; CP1-E02, CP1-E10. | Trung binh: can render page/crop va provider vision; chua co OCR rieng. | Dua vao scope prototype qua page image va visual region, nhung khong chon lam pain primary doc lap. |
| Khong tim duoc noi dung trong toan tai lieu | Hoc vien khong nhan duoc phan lien quan khi cau hoi khong gan trang cu the. | Whole-session/document summary intents 57; 37 co failure/empty citation signal. | Trung binh-den-cao: can retrieval da trang va coverage. | Dua vao backlog/secondary mode document search; khong mo thanh summarization toan bo trong CP4. |

Ly do chon ung vien 1: so luong case manh nhat, co nhieu quote kiem tra duoc, co downvote, phu hop lat cat mot viec la giai thich noi dung dang xem. Ung vien visual/table/figure duoc ho tro trong prototype vi co lien quan truc tiep toi selected context, nhung khong phong dai thanh OCR hoan chinh. Ung vien tim toan tai lieu va summary toan bo bi loai khoi primary slice vi scope rong hon va can danh gia coverage rieng.

## §3. Giai phap tuong tu da nghien cuu

- ChatGPT voi file/PDF: flow manh o chat lien tuc va co the hoi ve file, nhung neu khong gan dung trang/nguon thi user kho kiem chung trong bai hoc. VLearn Tutor can uu tien trang/vung dang xem va citation theo page.
- NotebookLM: dang hoc o viec hien nguon canh cau tra loi va buoc nguoi dung quay lai source. Diem can ne la khong bien prototype thanh cong cu tong hop toan bo notebook; slice nay chi giai thich page/selection/region.
- Khanmigo / tutor hoc tap: dang hoc o giong dieu ho tro va khong dua dap an thay hoc vien trong ngu canh hoc. Diem can ne la tra loi qua tu tin khi thieu can cu.
- ChatPDF / AskYourPDF: flow upload va hoi tai lieu nhanh, nhung thuong tap trung toan tai lieu; VLearn khac o viec user dang o dung trang, co drag page, text selection, visual region va citation click.

Khong co so lieu moi duoc tao cho muc nay; day la tong hop flow tuong tu o muc dinh huong thiet ke.

## §4. Thiet ke

- Lat cat mot cau: Voi hoc vien hoi ve mot trang, doan van hoac vung hinh anh trong PDF, he thong quyet dinh ngu canh do co du can cu de tra loi hay phai bao thieu thong tin, de hoc vien nhan loi giai thich co the kiem chung theo dung trang.
- Quyet dinh AI trung tam: AI quyet dinh noi dung trong trang, doan van hoac vung hinh anh duoc chon co du can cu de tra loi hay phai thong bao chua du thong tin.
- Muc prototype: [x] Working. Flow that: upload PDF, extract page text, build retrieval index, render page/crop image, call model provider, return answer with citation. Citation click, drag page, text selection va visual region da co trong UI. Limitations: chua authentication, chua OCR day du cho scanned PDF, dung SQLite/local storage, offline eval khong tu cham toan bo semantic correctness cua model that.
- Model: Text primary theo env/source la OpenAI qua `OPENAI_MODEL`, default `gpt-5-mini`. Vision primary la Gemini qua `GEMINI_VISION_MODEL` hoac `GEMINI_MODEL`, default `gemini-3.5-flash-lite`. Infrastructure fallback OpenAI <-> Gemini theo `PRIMARY_TEXT_PROVIDER`, `FALLBACK_TEXT_PROVIDER`, `VISION_PRIMARY_PROVIDER`, `VISION_FALLBACK_PROVIDER` va `ENABLE_GEMINI_FALLBACK`.
- Automation: Conditional automation. Du context thi tra loi co citation. Khong du context thi noi ro hoac hoi lai. Cost-of-error: tra loi sai hoac cite sai co the lam hoc vien hoc sai noi dung bai hoc, nen khong doan khi thieu can cu.

Non-goals:

- Khong lam authentication.
- Khong lam collaborative annotation.
- Khong lam LMS production hoan chinh.
- Khong gui toan bo PDF vao moi request.
- Khong tu dua dap an bai kiem tra.
- Khong khai OCR day du cho scanned PDF.

Nguyen tac HAX/PAIR ap dung:

| Nguyen tac | Ap cu the vao prototype |
|---|---|
| Lam ro kha nang va gioi han | Welcome message trong `ChatPanel` noi user co the nhap cau hoi, keo trang, boi den van ban hoac khoanh vung hinh anh; spec va README ghi ro chua authentication/OCR day du. |
| Hien thi citation dung trang | `ChatResponseV2.citations` tra `page_number`; `ChatMessage` hien nut `Trang N`; click citation goi `onCitationClick` de nhay den page card. |
| Cho phep nguoi dung sua/chon lai context | `PageAttachment` co nut remove; context moi tu drag page/text selection/visual region thay context cu. |
| Ho tro correction bang xoa attachment va tao cuoc tro chuyen moi | CP4 ghi viec can hoan thien nut `Cuoc tro chuyen moi` va reset context; sau CP4 se cap nhat changelog khi da implement/test. |
| Khong doan khi thieu can cu | Prompt page/selection/document search yeu cau chi tra loi dua tren noi dung thay duoc va noi ro khi khong du bang chung. |
| Hien thi tien trinh phan hoi bang streaming | La viec con thieu truoc CP5; se them `/api/v2/chat/stream` va UI streaming sau commit artifact CP4. |

## §5. Kieu loi - 4 lop cho kho + kich ban

Khong them golden-set case moi trong CP4. Cac kich ban duoi day dua tren 43 case hien co trong `eval/golden_set.jsonl`.

| Lop | Kich ban | Trigger | Hanh vi mong muon | Hanh vi khong cho phep | Hau qua | Case lien quan |
|---|---|---|---|---|---|---|
| Khong co can cu | Trang khong ton tai | User hoi trang 99 | HTTP 400 noi tai lieu khong co trang 99 | Goi provider va doan noi dung | Hoc sai/cite sai | `page_out_of_range` |
| Khong co can cu | Khong co document khi can page | User gan page nhung thieu `document_id` | HTTP 400 yeu cau co PDF | Tra loi bang tri nho chung | Mat grounding | `page_missing_document` |
| Khong co can cu | Selection bi forge | Selected text khong khop page text | Tu choi voi loi khong khop noi dung trang PDF | Chap nhan selected text gia | Hoc vien tin vao context sai | `selection_forged` |
| Mo ho/confidence thap | Cau hoi visual can dung trang | User hoi bieu do/hinh tren page | Dung image render/crop va page text, citation dung trang | Chi tra loi text chung | Bo sot thong tin visual | `visual_region_standard`, `page_visual_question` |
| Mo ho/confidence thap | Cau hoi khong gan page nhung co document | User hoi RAG/multi-head | Retrieval chon page lien quan, citation | Lay active page bat ky | Citation lech nguon | `search_rag`, `search_multi_head` |
| Ngoai pham vi/khong duoc phep | General chat bi ep search nhung khong document | `interaction_mode=document_search` khong co PDF | Roi ve general chat an toan | Bao da search tai lieu khong ton tai | Gay hieu nham | `forced_search_without_document` |
| Ngoai pham vi/khong duoc phep | Provider request/config sai | Provider bao bad request/model/key invalid | Khong fallback, bao loi cau hinh ro | Fallback de che loi config | Kho debug va sai provider | `provider_text_request_error` |
| Sai gay hau qua that | Citation khong dung selected page | User hoi trang cu the | Citation phai dung page da dung trong context | Citation sang page khac | Hoc vien hoc sai source | `page_real_C0021_T0769`, `page_real_C0266_T1084` |
| Sai gay hau qua that | Fallback provider sai thoi diem | Primary loi tam thoi truoc khi co answer | Fallback chi voi temporary/rate/timeout/5xx | Fallback voi bad request hoac config | Ket qua khong nhat quan | `fallback_text_temporary`, `fallback_vision_temporary` |
| Sai gay hau qua that | Lich su chat qua dai/ro context | History dai hon gioi han | Chi dung recent window theo config, khong dua luot cu nhat | Gui vo han hoac leak welcome/local UI | Tang token, nhieu context | `history_limit_general` |

## §6. Bon duong di cua trai nghiem

- Happy path: User mo PDF, keo mot trang hoac chon text/region, hoi. Backend validate document/page/selection, tao context, goi provider text hoac multimodal, luu conversation va tra answer kem citation. Case: `page_attached_standard`, `selection_valid`, `visual_region_standard`.
- Low-confidence: User hoi noi dung co the can tim trong toan tai lieu. Backend retrieval cac page lien quan; neu evidence yeu, prompt yeu cau noi ro khong du thong tin. Case: `search_grounded_abstention`.
- Failure/no evidence: Trang ngoai range, thieu document, selection khong khop hoac provider chua co key. He thong tra loi loi ro rang, khong goi model khi validation fail. Case: `page_out_of_range`, `page_missing_document`, `selection_forged`, `provider_credentials_missing`.
- Correction: User xoa attachment, chon lai page/text/region hoac tao chat moi. CP4 hien da co remove attachment; nut tao chat moi va xoa remote conversation la viec con thieu truoc CP5.
- Ngoai pham vi: Khi user ep document search ma khong co document, he thong khong gia vo co tai lieu va xu ly nhu general chat. Case: `forced_search_without_document`.
- Visual/table/figure: Page chat va visual region gui image bytes cho vision provider; table/figure/chart co citation page. Case: `page_visual_question`, `search_table_comparison`, `visual_real_C0547_T0135`.
- Doi tai lieu: Hien tai frontend reset local chat/attachment khi `currentDocument.id` thay doi; CP5 can xoa conversation server cu theo best effort va khong mang context cu sang document moi.
- Tao chat moi: CP5 can them nut `Cuoc tro chuyen moi`, abort stream dang chay, xoa conversation server neu co, reset messages va focus textarea.

## §7. Kiem thu

Golden set hien co 43 case, giu nguyen tong so case trong CP4. Trong do 10 case duoc chuyen the tu chatlog VLearn da an danh va 33 case tong hop. Khong them golden case moi.

Chieu chat luong va dinh nghia pass/fail:

- Status accuracy: status code dung voi expected.
- Mode accuracy: routing dung `GENERAL_CHAT`, `PAGE_CHAT`, `TEXT_SELECTION_CHAT`, `VISUAL_REGION_CHAT`, `DOCUMENT_SEARCH_CHAT`.
- Page context accuracy: page dung exact hoac include required page.
- Citation accuracy: citation page dung expected.
- Provider invocation/media path: goi provider dung/khoi goi dung text hoac multimodal; image path co image khi can.
- Fallback accuracy: provider va `fallback_used` dung, attempted providers dung voi expected.
- Prompt context accuracy: prompt chua/chua khong chua cac chuoi bat buoc/cam.
- History limit accuracy: khong vuot gioi han lich su theo case.
- UTF-8 response accuracy: answer/lỗi co dau tieng Viet.
- No crash: runner khong crash.

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

Ket qua latest CP4 tu `eval/results/latest.json`: 43/43 case pass, `quality_bar_passed=true`, `failed_cases=[]`.

Offline eval chay `OrchestrationService`, retrieval va fake provider. No kiem tra contract, routing, page, media path, fallback, UTF-8 va history. No khong thay the viec cham chat luong ngon ngu cua model that va khong phai bang chung tuyet doi rang model tra loi dung kien thuc. Live smoke can ghi rieng khi co API key; tai CP4 chua ghi PASS live provider neu test bi skip.

## §8. Phan cong & ke hoach

Thanh vien va phan cong:

| Thanh vien | MSSV | Phan cong |
|---|---|---|
| Vu Van Phong | 2A202601647 | Spec owner, dieu phoi checkpoint, tong hop changelog. |
| Doan Nhat Nam | 2A202601123 | Evidence/mining, kiem tra so lieu va quote co `conversation_id/turn_id`. |
| Ha Duy Anh | 2A202601511 | JTBD, problem statement, impact table, pain candidates bi loai. |
| Nguyen Quang Vinh | 2A202601517 | Prompt, failure taxonomy, HAX/PAIR va provider behavior. |
| Hoang Le Minh | 2A202601653 | Frontend flow: PDF workspace, chat panel, attachment, reset/streaming UI. |
| Pham Sy Duc | 2A202601601 | Eval/validation/demo, golden set, latest result va live smoke plan. |

Willing users: TODO - chua co ten nguoi dung ngoai nhom duoc xac nhan trong repo. Day la blocker CP5. Can toi thieu 5 nguoi validation, uu tien 3 willing users tu CP1 neu xac nhan duoc.

Viec con thieu truoc CP5:

- Streaming response.
- Rolling conversation context.
- Reset conversation.
- Live smoke.
- Validation it nhat nam nguoi.
- Dry run.

Nhung viec tren da duoc ghi trong spec o CP4, nen khi hoan thien se la hoan thien scope da khai, khong phai mo feature moi tuy tien.

## §9. Changelog

| Thoi diem | Doi gi | Vi sao |
|---|---|---|
| CP1 | Chot pain selected-context/retrieval failure va canvas VLearn Tutor. | Mining cho thay 164 strong cases `Trang N` + fallback + empty citation va 239 mismatch citation page. |
| CP2 | Co prototype PDF/chat: upload PDF, doc page, chat voi provider, drag page vao chat. | Can flow bam duoc de chung minh hoc vien hoi theo context dang xem. |
| CP3 | Mo rong multimodal, text selection, visual region, retrieval va eval offline 43 case. | Bao phu page, selection, region, document search, provider fallback va UTF-8. |
| CP4 | Track `eval/results/latest.json`, chot quality bar va spec gan cuoi; ghi ke hoach hoan thien context/streaming/reset. | Artifact CP4 can duoc commit/push truoc khi them streaming; latest result 43/43 pass. |
| Sau CP4 | TODO: them streaming/reset/context memory vao changelog sau khi implement va test pass. | Chua duoc khai la hoan thanh trong artifact CP4. |
