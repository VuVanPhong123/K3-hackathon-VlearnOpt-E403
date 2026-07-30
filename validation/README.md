# Báo cáo thử nghiệm prototype

Trạng thái: `DONE` - đã thử nghiệm với 7 người, đã có 7 quote nguyên văn và 2 willing user; 5 người còn lại chỉ tham gia test nhanh, không phải willing user.

## 1. Thông tin buổi thử nghiệm

- Ngày thử nghiệm: 30/07/2026
- Số người tham gia: 7
- Đối tượng: Sinh viên tham gia thử nghiệm prototype
- Phạm vi: Các chức năng chính của VLearn Tutor

## 2. Người tham gia

| STT | Người thử nghiệm | MSSV | Ngày test | Task | Quote nguyên văn | Willing user? |
| --: | ---------------- | ---- | --------- | ---- | ---------------- | ------------- |
| 1 | Tô Ngọc Hải | 2A202601686 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | app cũng ok, nhưng mà sao lại bỏ cái tính năng vẽ để hỏi của vlearn thế | Không |
| 2 | Đào Văn Đà | 2A202601089 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | ok thấy app trả lời ok hơn vlearn đấy, mà hình như tốc độ phản hồi hơi chậm nhỉ | Không |
| 3 | Nguyễn Văn Trường | 2A202601974 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | tính năng thì hơn rồi nhưng mà việc bạn nối workflow với sử dụng model thế này thì chi phí cao quá nhỉ, nếu scale lớn thì chắc không hỗ trợ nổi vì số lượng câu hỏi của học viên chắc là căng lắm | Không |
| 4 | Lê Anh Tiến | 2A202601145 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | thử hỏi một thuật ngữ trong slide mà không cho biết trang nào đi, fail ngay, cần thêm trích xuất chính xác từ mà tìm kiếm rồi hỗ trợ thêm nếu người dùng gõ sai chính tả nữa | Không |
| 5 | Lê Tiến Minh | 2A202601193 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | phần chat không có streaming nên người dùng hơi khó chịu, giao diện nhìn cũng ok, các tính năng đã đầy đủ và độ chính xác khi truy xuất tài liệu, tổng hợp tài liệu cũng được cải thiện | Có |
| 6 | Trần Văn Tài | 2A202601339 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | bạn thử crop ảnh sơ đồ rồi paste vào xem nó có phân tích được không, ok rồi, model đọc context, trả lời cũng khá ổn | Không |
| 7 | Nguyễn Huy Nghĩa | 2A202601943 | 30/07/2026 | Thử nghiệm các luồng chính của prototype. | đã giải quyết painpoint nhưng giao diện hơi xấu và thời gian trả lời hơi chậm | Có |

Tất cả quote trong bảng là quote nguyên văn do nhóm cung cấp. Không sử dụng nội dung tổng hợp ở dưới như một quote trực tiếp.

## 3. Phạm vi thử nghiệm

Tất cả 7 người đã thử các chức năng chính của prototype:

- Mở hoặc tải tài liệu PDF.
- Hỏi đáp dựa trên tài liệu.
- Sử dụng ngữ cảnh trang, đoạn hoặc vùng nội dung.
- Tìm kiếm thông tin trong tài liệu.
- Kiểm tra citation và khả năng quay lại đúng trang.
- Quan sát trải nghiệm giao diện và thời gian phản hồi.

## 4. Các chủ đề feedback

Các nhận xét dưới đây là phần tổng hợp chủ đề từ ghi nhớ của nhóm sau buổi thử nghiệm, chưa phải trích dẫn nguyên văn của từng người tham gia.


| Chủ đề | Quan sát tổng hợp | Mức độ | Hành động/Trạng thái |
| ------ | ----------------- | ------ | -------------------- |
| Khả năng sử dụng | Prototype nhìn chung có thể sử dụng được và các luồng chính hoạt động. | Tích cực | Giữ nguyên product slice chính và tiếp tục kiểm tra các trường hợp biên. |
| Giao diện | Giao diện vẫn cần được cải thiện để trực quan và dễ sử dụng hơn, dù có phản hồi cho rằng giao diện hiện tại nhìn ổn. | Trung bình | Nhóm đã cập nhật giao diện sau feedback; vẫn cần kiểm tra lại với người dùng ở vòng tiếp theo. |
| Tốc độ phản hồi | Thời gian xử lý hoặc phản hồi đôi lúc còn chậm; việc thiếu streaming làm trải nghiệm chat khó chịu hơn. | Trung bình | Nhóm đã bổ sung response streaming để cải thiện cảm nhận chờ phản hồi; hiệu năng thực tế vẫn cần theo dõi khi scale. |
| Mức độ giải quyết pain point | Prototype đã cải thiện pain point VLearn mà nhóm lựa chọn, đặc biệt ở việc cung cấp đúng ngữ cảnh tài liệu và citation để người học kiểm tra lại nguồn. | Tích cực | Tiếp tục giữ selected-context, grounded answer và citation là trọng tâm của sản phẩm. |
| Chi phí vận hành | Workflow dùng model có thể tốn chi phí nếu scale lớn với nhiều câu hỏi của học viên. | Trung bình | Ghi nhận là rủi ro cần cân nhắc ở bước production; chưa biến thành metric định lượng trong bài lab. |
| Tương tác theo hình ảnh | Người dùng quan tâm khả năng hỏi bằng crop ảnh/sơ đồ hoặc kéo trang vào chat thay cho thao tác khoanh/vẽ. | Tích cực | Nhóm quyết định bỏ phần khoanh tròn để hỏi và ưu tiên crop ảnh hoặc kéo trang vào chat để hỏi. |

## 5. Thay đổi sau validation

Các cải tiến dưới đây được nhóm ghi nhận sau khi nhận feedback từ buổi thử nghiệm prototype. Báo cáo chỉ gắn với chủ đề feedback đã xác nhận, không suy diễn thêm ngoài dữ liệu nhóm cung cấp.

- Duy trì trọng tâm selected-context: page chat, active page, attached page, text selection và visual region đều trả citation theo trang.
- Retrieval thuật ngữ được tổng quát hóa bằng tách thuật ngữ, query variants, exact phrase boost và fuzzy correction có guardrail từ vocabulary của chính tài liệu.
- Document search dùng evidence thật từ chunk/page và citation để người học kiểm tra lại nguồn.
- Visual context gửi ảnh render page/crop cho provider vision khi người dùng hỏi theo trang hoặc vùng hình ảnh.
- Nhóm quyết định bỏ phần khoanh tròn để hỏi, thay bằng crop ảnh hoặc kéo trang vào chat để hỏi.
- Giao diện đã được cập nhật sau feedback để dễ sử dụng hơn.
- Response streaming đã được bổ sung để cải thiện trải nghiệm trong lúc chờ câu trả lời.
- Hệ thống có thông báo rõ khi thiếu tài liệu, trang ngoài range, selection không khớp hoặc provider chưa cấu hình.
- Conversation reset và streaming SSE đã có trong prototype để cải thiện flow sử dụng.

Các điểm chi phí vận hành và hiệu năng khi scale vẫn được ghi nhận là limitation/backlog, chưa biến thành số liệu định lượng trong báo cáo này.

## 6. Trạng thái hoàn tất

- Validation prototype đã hoàn tất với 7 người thử nghiệm.
- Quote nguyên văn đã đủ cho 7 người trong báo cáo.
- Willing user chỉ có Lê Tiến Minh và Nguyễn Huy Nghĩa; 5 người còn lại chỉ test nhanh, không phải willing user.
- Không thêm metric định lượng hoặc quote ngoài dữ liệu nhóm cung cấp.
