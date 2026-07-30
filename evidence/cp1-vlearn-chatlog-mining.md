# CP1 VLearn Chatlog Mining

## 1. Dataset Và Phạm Vi

Nguồn dữ liệu ban đầu: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`.

Data pack gốc không nằm trong repo nộp bài cuối để tránh commit dữ liệu nguồn. Report này chỉ giữ số liệu tổng hợp, quote ngắn cần cho rubric và mã tham chiếu `conversation_id/turn_id`.

Phạm vi phân tích: toàn bộ chatlog VLearn tutor trong file CSV, gồm message của `student` và `tutor`. Transcript bài giảng không được dùng làm evidence pain; chỉ CSV được dùng để đếm và trích dẫn failure signal.

Tài liệu đã đọc trước khi mining:

- `01-de-bai.md`
- `02-guide.md`
- `03-template-ai-spec.md`
- `04-rubric.md`
- `README.md`
- `data/vlearn-pack/README.md`
- `data/vlearn-pack/chatlog/DATA_DICTIONARY.md`
- `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

## 2. Phương Pháp Đếm

Script: `evidence/scripts/analyze_vlearn_chatlog_pain.py`.

Cách chạy:

```bash
python evidence/scripts/analyze_vlearn_chatlog_pain.py --csv <path-to-chat_history_anonymized_for_hackathon.csv> --limit 60
```

Quy tắc:

- Đọc CSV bằng encoding UTF-8, không sửa CSV.
- Một turn hỏi-đáp được xác định bằng `turn_id` có đủ một message `student` và một message `tutor`.
- Tutor response là các dòng `role=tutor`.
- Empty citation là `citations` rỗng hoặc bằng `[]`.
- Retrieval/fallback response là tutor content match một trong các regex ở mục 3 sau khi lowercase và bỏ dấu tiếng Việt.
- Selected page là số đầu tiên match regex `Trang\s*(\d+)` trong student content.
- Page/citation mismatch là student có `Trang N`, tutor có citation không rỗng, nhưng citation list không chứa `N`.
- Rating chỉ lấy từ tutor row, vì rating gắn với response.

## 3. Regex/Rules Đã Dùng

Retrieval/fallback patterns sau khi bỏ dấu:

```text
khong tim thay
chua tim thay
khong chua thong tin
khong co tai lieu
cung cap them thong tin
cung cap noi dung hoac tieu de
cung cap noi dung
cung cap.*tieu de
```

Whole-session/document summary intent patterns:

```text
tom tat.*toan bo
tong hop.*toan bo
tom tat.*buoi hoc
tom tat.*ngay hom nay
tom tat.*hom nay
tom gon.*day
toan bo slide
toan bo tai lieu
toan bo bai giang
tai lieu toi xem
```

Visual/chart/image intent patterns:

```text
bieu do
do thi
hinh anh
\bhinh\b
boi do
visual
chart
```

## 4. Aggregate Results

Kết quả từ lần chạy trên data pack ban đầu với `--limit 60`:

| Metric | Result |
|---|---:|
| Total messages | 2,522 |
| Total question-answer turns | 1,261 |
| Total tutor responses | 1,261 |
| Tutor responses with empty citations | 582/1,261 (46.2%) |
| Tutor responses with retrieval/fallback language | 175/1,261 (13.9%) |
| Retrieval/fallback responses with `rating=down` | 13 |
| Rated tutor responses | 70 (`up=33`, `down=37`) |
| Student turns mentioning `Trang N` | 1,252 |
| `Trang N` + retrieval/fallback language | 174 |
| `Trang N` + retrieval/fallback language + empty citations | 164 |
| `Trang N` + citation does not include selected page | 239 |
| Whole-session/document summary intents | 57 |
| Whole-session/document summary with failure/empty citation signal | 37 |
| Visual/chart/image intents | 32 |
| Visual/chart/image with failure/mismatch signal | 6 |

## 5. Evidence Table

| Evidence ID | Source file | conversation_id | turn_id | day_code | student_message_id | tutor_message_id | selected_page | citations | rating | Observed failure |
|---|---|---|---|---|---|---|---:|---|---|---|
| CP1-E01 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0021 | T0769 | Lecture_material_ms204i6x_gqwyya | M0060 | M0419 | 4 | `[]` | down | User nêu trang 4, tutor báo không tìm thấy và yêu cầu cung cấp lại nội dung/tiêu đề. |
| CP1-E02 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0023 | T0399 | New learning material | M1331 | M2317 | 6 | `[71]` | null | User hỏi biểu đồ trang 6, tutor nói kết quả tra cứu trả về trang 71 và hỏi thêm mô tả. |
| CP1-E03 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0001 | T0649 | Lecture_material_ms2044ey_k6uor3 | M1149 | M1637 | 37 | `[]` | null | User nêu trang 37, tutor báo không tìm thấy nội dung cụ thể. |
| CP1-E04 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0015 | T0811 | Lecture_material_ms4ahenz_7cpqa2 | M1739 | M2052 | 2 | `[]` | null | Selected text có `ReAct` nhưng tutor vẫn báo không tìm thấy định nghĩa chi tiết. |
| CP1-E05 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0002 | T0092 | Lecture_material_ms4x7dx1_t0qyxg | M1501 | M0506 | 50 | `[]` | null | User nêu ba chủ đề, tutor vẫn hỏi lại tên chủ đề/mục tiêu học tập. |
| CP1-E06 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0031 | T0408 | Lecture_material_ms5r18w1_oe5xlz | M2134 | M1124 | 14 | `[]` | down | User hỏi tóm tắt slide cụ thể, tutor không tìm thấy file/nội dung và bị downvote. |
| CP1-E07 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0076 | T1258 | New learning material | M2065 | M0780 | 33 | `[]` | down | User hỏi tóm tắt slide này, tutor nói chưa thấy trang 33 và search ra các trang khác. |
| CP1-E08 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0228 | T1023 | Lecture_material_ms203vsq_ob7vqp | M0634 | M2138 | 43 | `[]` | down | User hỏi theo page 43, tutor không tìm thấy thông tin tại trang 43 và bị downvote. |
| CP1-E09 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0266 | T1084 | New learning material | M1646 | M0499 | 4 | `[70]` | down | User hỏi slide 4, tutor trả lời với citation trang 70. |
| CP1-E10 | `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` | C0547 | T0135 | New learning material | M0380 | M0605 | 16 | `[]` | down | User hỏi tóm tắt các giai đoạn trên slide có biểu đồ, tutor không tìm thấy nội dung liên quan và bị downvote. |

## 6. Full Quote Của Evidence Mạnh

### CP1-E01

Evidence ID: CP1-E01

Source file: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

conversation_id: C0021

turn_id: T0769

day_code: Lecture_material_ms204i6x_gqwyya

student_message_id: M0060

tutor_message_id: M0419

selected_page: 4

Student quote:

```text
(Trang 4, đoạn được chọn: "giải thích nghĩa chi tiết của trang 4")
giải thích nghĩa chi tiết của trang 4
```

Tutor quote:

```text
Chào bạn, rất xin lỗi vì hiện tại hệ thống tìm kiếm không tìm thấy nội dung cụ thể cho trang 4 trong tài liệu của bài học hôm nay. Bạn có thể vui lòng cung cấp nội dung hoặc tiêu đề của trang 4 đó để mình hỗ trợ giải thích rõ hơn cho bạn không?
```

citations: `[]`

rating: `down`

Observed failure: Tutor không truy xuất được nội dung trang user đã nêu và yêu cầu user cung cấp lại context.

What this evidence proves: Có ít nhất một selected-page retrieval failure nhận downvote.

What this evidence does NOT prove: Không chứng minh mọi học viên mất niềm tin hoặc nguyên nhân kỹ thuật nằm ở retriever.

### CP1-E02

Evidence ID: CP1-E02

Source file: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

conversation_id: C0023

turn_id: T0399

day_code: New learning material

student_message_id: M1331

tutor_message_id: M2317

selected_page: 6

Student quote:

```text
(Trang 6, đoạn được chọn: "Giải thích biều đồ đc bôi đỏ")
Giải thích biều đồ đc bôi đỏ
```

Tutor quote:

```text
Rất tiếc, tôi đã thực hiện tra cứu trong các slide bài giảng nhưng hiện tại không tìm thấy thông tin cụ thể về "biểu đồ được bôi đỏ" trên trang 6 trong dữ liệu được cung cấp. Kết quả tra cứu trang 6 hiện đang trả về nội dung của trang 71, đề cập đến việc so sánh phong cách trả lời của ba mô hình Claude, GPT và một mô hình khác dựa trên cùng một prompt [trang 71].

Nếu biểu đồ bạn đang đề cập liên quan đến các số liệu tài chính hoặc so sánh hiệu năng giữa các mô hình, bạn có thể mô tả thêm các thông số hoặc tiêu đề trên biểu đồ đó để tôi có thể hỗ trợ giải thích chính xác nhất cho bạn.
```

citations: `[71]`

rating: `null`

Observed failure: Tutor thừa nhận tra cứu trang 6 trả về nội dung trang 71; sau đó hỏi user mô tả thêm biểu đồ.

What this evidence proves: Có dấu hiệu page/source mismatch và hạn chế với context dạng biểu đồ/visual.

What this evidence does NOT prove: Chưa đủ dữ liệu để kết luận đây là lỗi retrieval, lỗi page mapping hay thiếu khả năng xử lý hình ảnh. Tutor có phỏng đoán thêm về nội dung biểu đồ, nhưng CSV không đủ để xác định mức độ đúng sai của phỏng đoán.

### CP1-E03

Evidence ID: CP1-E03

Source file: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

conversation_id: C0001

turn_id: T0649

day_code: Lecture_material_ms2044ey_k6uor3

student_message_id: M1149

tutor_message_id: M1637

selected_page: 37

Student quote:

```text
(Trang 37, đoạn được chọn: "tóm tắt nội dung chính trong slide này")
tóm tắt nội dung chính trong slide này
```

Tutor quote:

```text
Xin lỗi bạn, tôi không tìm thấy nội dung cụ thể cho slide 37 trong tài liệu hiện có. Bạn có thể cung cấp thêm thông tin hoặc tiêu đề của slide đó để tôi có thể hỗ trợ bạn chính xác hơn không?
```

citations: `[]`

rating: `null`

Observed failure: User đã nêu trang và intent tóm tắt, tutor không tìm thấy nội dung cụ thể.

What this evidence proves: Có case user nêu rõ trang nhưng tutor vẫn fallback và không có citation.

What this evidence does NOT prove: Không chứng minh trang 37 chắc chắn tồn tại đúng trong nguồn hệ thống tại thời điểm đó.

### CP1-E04

Evidence ID: CP1-E04

Source file: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

conversation_id: C0015

turn_id: T0811

day_code: Lecture_material_ms4ahenz_7cpqa2

student_message_id: M1739

tutor_message_id: M2052

selected_page: 2

Student quote:

```text
(Trang 2, đoạn được chọn: "Designt Pattern ReAct là gì có lưu ý gì về nó?")
Designt Pattern ReAct là gì có lưu ý gì về nó?
```

Tutor quote:

```text
Rất tiếc, tôi không tìm thấy định nghĩa chi tiết về "ReAct" trong các slide bài giảng hiện tại của ngày học này. Nếu bạn có tài liệu cụ thể hoặc tên gọi khác của kỹ thuật này trong ngữ cảnh bài học, hãy chia sẻ thêm để tôi có thể hỗ trợ bạn chính xác hơn nhé!
```

citations: `[]`

rating: `null`

Observed failure: Selected text chứa keyword `ReAct`, có lỗi chính tả `Designt`, nhưng tutor vẫn không tìm thấy định nghĩa và hỏi user cung cấp thêm.

What this evidence proves: Có dấu hiệu selected text/keyword không được tận dụng đủ tốt trong fallback.

What this evidence does NOT prove: Chưa xác định được nguyên nhân là retrieval failure, query normalization failure hay selected context không được ưu tiên.

### CP1-E05

Evidence ID: CP1-E05

Source file: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`

conversation_id: C0002

turn_id: T0092

day_code: Lecture_material_ms4x7dx1_t0qyxg

student_message_id: M1501

tutor_message_id: M0506

selected_page: 50

Student quote:

```text
(Trang 50, đoạn được chọn: "kỹ thuật tối ưu prompt, cơ chế gọi tool và cách xử lý ngữ cảnh")
kỹ thuật tối ưu prompt, cơ chế gọi tool và cách xử lý ngữ cảnh
```

Tutor quote:

```text
Rất tiếc, tôi không tìm thấy tài liệu tổng hợp đầy đủ cho nội dung của Day 04 trong các file slide đã được cung cấp.

Để có thể giúp bạn tóm tắt chính xác, bạn có thể cho tôi biết tên các chủ đề hoặc mục tiêu học tập cụ thể trong Day 04 được ghi chú trong giáo trình của bạn không? Khi có thông tin đó, tôi sẽ giúp bạn giải thích từng phần về kỹ thuật tối ưu prompt, cơ chế gọi tool và quản lý ngữ cảnh một cách cụ thể nhất.
```

citations: `[]`

rating: `null`

Observed failure: User đã nêu ba chủ đề cụ thể, tutor vẫn hỏi lại tên chủ đề/mục tiêu học tập.

What this evidence proves: Có dấu hiệu fallback không tận dụng đủ context đã có trong selected text.

What this evidence does NOT prove: Không chứng minh hệ thống không thể tóm tắt toàn bộ Day 04 trong mọi tình huống.

## 7. Candidate Pain Comparison

| Pain candidate | Số case quan sát được | Ví dụ đại diện | Hậu quả trực tiếp | Khả năng build trong hackathon | Evidence | Chọn/loại | Lý do |
|---|---:|---|---|---|---|---|---|
| Selected-context/retrieval failure | 164 strong cases: user có `Trang N`, tutor retrieval/fallback, `citations=[]`; thêm 239 case citation không chứa selected page | CP1-E01, CP1-E02, CP1-E03, CP1-E04, CP1-E05 | Học viên phải nhập lại context hoặc không nhận được câu trả lời có nguồn kiểm chứng | Cao: có thể build flow đánh giá context, trả lời có nguồn, hoặc hỏi đúng một câu làm rõ | Mạnh | Chọn | Có aggregate rõ, nhiều quote trực tiếp, có downvote, vừa đủ hẹp cho CP1/CP2. |
| Không thể tóm tắt toàn bộ buổi học/tài liệu | 57 intent; 37 có failure/empty citation signal | CP1-E06, C0002/T0905, C0537/T1096 | Học viên không nhận được bản tổng hợp để ôn hoặc theo dõi nội dung lớn | Trung bình: cần retrieval đa trang/toàn tài liệu, dễ mở rộng quá phạm vi một feature nhỏ | Trung bình | Loại khỏi CP1 | Đây là job khác với giải thích đoạn đang xem; scope rộng hơn và cần đánh giá coverage toàn tài liệu. |
| Không hiểu hình ảnh/biểu đồ được chọn | 32 intent visual/chart/image; 6 có failure/mismatch signal | CP1-E02, CP1-E10 | Học viên không hiểu phần visual trên slide dù đã chọn đoạn liên quan | Thấp đến trung bình: có thể cần slide image/OCR/vision context, trong pack hiện tại chưa có slide image | Yếu đến trung bình | Loại khỏi primary CP1 | Có ví dụ mạnh nhưng số case ít hơn và nguyên nhân có thể là visual limitation, không chỉ retrieval/context. |

## 8. Những Điều Dữ Liệu Chứng Minh

- Trong CSV có nhiều tutor response không có citation: `582/1261 (46.2%)`.
- Có `175/1261 (13.9%)` tutor response dùng ngôn ngữ retrieval/fallback theo rule đã định.
- Có `164` turn user nêu `Trang N`, tutor dùng retrieval/fallback và không có citation.
- Có `13` retrieval/fallback response nhận `rating=down`.
- Có case page/source mismatch rõ về mặt log, như `C0023/T0399` hỏi trang 6 nhưng citation là `[71]`.
- Có case selected text có keyword cụ thể nhưng tutor vẫn fallback, như `C0015/T0811` với `ReAct`.

## 9. Những Điều Dữ Liệu Chưa Chứng Minh

- Chưa chứng minh học viên mất niềm tin vào tutor.
- Chưa chứng minh tutor thường xuyên hallucinate.
- Chưa chứng minh citation đều sai; script chỉ đếm citation không chứa selected page.
- Chưa chứng minh học viên học sai kiến thức.
- Chưa chứng minh phần lớn học viên gặp pain này; CSV cho thấy số turn/case, không phải tỷ lệ người bị ảnh hưởng theo khảo sát.
- Chưa chứng minh nguyên nhân kỹ thuật chính xác là retriever, page mapping, query normalization hay thiếu visual context.

## 10. Cách Chạy Lại Phân Tích

```bash
python evidence/scripts/analyze_vlearn_chatlog_pain.py --csv <path-to-chat_history_anonymized_for_hackathon.csv> --limit 60
```

Output cần khớp các aggregate ở mục 4 nếu CSV không thay đổi. Script không hardcode kết quả aggregate và không tạo file tạm. Vì CSV gốc không được ship trong repo cuối, người audit cần có bản data pack được cấp hợp lệ để chạy lại.
