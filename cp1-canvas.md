# CP1 Canvas - VLearn Tutor Selected Context

## 1. Hướng

Hướng A - Tối ưu AI Tutor hiện có trên VLearn.

Lý do chốt hướng: mining CSV cho thấy nhóm selected-context/retrieval có bằng chứng mạnh nhất trong phạm vi CP1: 164 turn có `Trang N`, tutor dùng ngôn ngữ retrieval/fallback và `citations=[]`; 13 response retrieval/fallback nhận `rating=down`.

## 2. Job Executor

Học viên đang học trực tiếp trên VLearn, đã chọn một trang hoặc đoạn slide chưa hiểu và muốn nhận lời giải thích ngay trong lúc học.

## 3. Core Job

Hiểu đúng nội dung của đoạn tài liệu đang xem để tiếp tục theo kịp bài học mà không phải tự nhập lại toàn bộ ngữ cảnh.

## 4. Pain Statement

Khi yêu cầu giải thích hoặc tóm tắt nội dung ở trang hay đoạn đang xem, học viên đôi khi phải cung cấp lại thông tin vì hệ thống không sử dụng được context đã chọn hoặc truy xuất không đúng nguồn, làm gián đoạn việc học.

## 5. Evidence Ban Đầu

- `582/1261` tutor response không có citation (`46.2%`).
- `175/1261` tutor response có ngôn ngữ retrieval/fallback (`13.9%`); trong đó `13` response nhận `rating=down`.
- `164` turn có user ghi `Trang N`, tutor dùng ngôn ngữ retrieval/fallback và `citations=[]`.
- `C0021/T0769`: user hỏi trang 4, tutor báo không tìm thấy nội dung cụ thể, `citations=[]`, `rating=down`.
- `C0023/T0399`: user hỏi biểu đồ trang 6, tutor nói kết quả tra cứu trang 6 đang trả về nội dung trang 71, `citations=[71]`.

Nguồn và quote đầy đủ nằm trong [evidence/cp1-vlearn-chatlog-mining.md](evidence/cp1-vlearn-chatlog-mining.md).

## 6. Lát Cắt Một Câu

Với học viên hỏi về một đoạn slide đã chọn, hệ thống đánh giá context và bằng chứng; nếu đủ thì trả lời kèm nguồn, nếu thiếu thì hỏi đúng một câu làm rõ, để học viên nhận được lời giải thích có thể kiểm chứng mà không phải nhập lại toàn bộ ngữ cảnh.

## 7. Automation Và Cost-Of-Error

Mức automation: Conditional automation.

Lý do: khi có nguồn rõ ràng, hệ thống có thể tự trả lời kèm citation; khi context thiếu hoặc nguồn yếu, hệ thống hỏi lại một câu; khi không có căn cứ, hệ thống không đoán. Sai kiến thức hoặc dẫn sai nguồn có thể khiến học viên hiểu sai nội dung bài học, nên không nên automate mọi trường hợp.

## 8. Willing Users

- [TODO - tên người thử 1]
- [TODO - tên người thử 2]
- [TODO - tên người thử 3]

Script hỏi người thật:

> "Bọn mình đang thử một tính năng giúp tutor sử dụng đúng đoạn slide đang chọn và nói rõ khi thiếu nguồn. Bạn có đồng ý dành 10 phút thử prototype trước buổi demo không?"

## 9. Phân Công

| Vai trò | Người phụ trách | Deliverable |
|---|---|---|
| Evidence/mining | `[TODO]` | Mining log + số liệu |
| Product/JTBD | `[TODO]` | Canvas + pain statement |
| Prompt/evaluation | `[TODO]` | Failure taxonomy ban đầu |
| Prototype | `[TODO]` | Flow bấm được ở CP2 |
| Validation/demo | `[TODO]` | Willing users + test plan |

## 10. Assumption Nguy Hiểm Nhất

Assumption cần kiểm chứng: học viên thật thấy việc phải cung cấp lại context hoặc nhận citation lệch là đủ khó chịu để muốn thử flow mới. CSV chỉ chứng minh hành vi/failure signal và một số downvote, chưa chứng minh mức độ đau, niềm tin, hay willingness ở quy mô lớp.

## 11. Thông Tin Còn Thiếu Trước Khi Gặp TA

- Tên thành viên phụ trách từng vai trò.
- Tối thiểu ba willing users thật ngoài nhóm.
- Xác nhận với team kỹ thuật về ý nghĩa `day_code=New learning material` và mapping trang/citation.
- Khảo sát/phỏng vấn nhanh để kiểm chứng mức độ đau và willingness, không chỉ dựa vào chatlog.
- Quyết định CP2 sẽ demo bằng mock flow nào: context đủ, context thiếu, citation mismatch, hoặc user sửa câu hỏi.
