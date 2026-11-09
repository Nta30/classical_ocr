# Phân tích bài báo và phạm vi triển khai

**Tài liệu:** Md. Anwar Hossain và Sadia Afrin, “Optical Character Recognition based on Template Matching,” *Global Journal of Computer Science and Technology*, 19(C2), 2019, trang 31–35. Bản PDF dùng để phân tích: `Optical_Character_Recognition_based_on_T.pdf` trong workspace.

## Quy trình được bài báo mô tả

Section III chia hệ thống thành bốn phần: **Pre-processing → Feature Extraction → Feature Training → Feature Matching**. Hình 1 biểu diễn nhánh dữ liệu huấn luyện và dữ liệu kiểm tra đi qua xử lý trước, trích xuất đặc trưng, so sánh rồi trả kết quả.

- Ảnh văn bản grayscale được chuyển thành ảnh binary; phần chữ được biểu diễn foreground 1, nền 0.
- Feature extraction áp dụng cho từng ký tự đã trích xuất; các object có ít hơn 30 pixel bị loại bỏ.
- Tập huấn luyện dùng hai font Calibri và Verdana; tác giả nói sẽ kiểm tra các font khác.
- Thuật toán chọn ảnh ký tự, đổi kích thước cho bằng template đầu, tính metric so khớp, lưu điểm cao nhất, rồi lấy chỉ số mẫu tốt nhất làm ký tự nhận dạng.
- Thí nghiệm ghi nhận đúng/sai trên năm ảnh (10, 20, 25, 30 và 62 ký tự), với Calibri, Verdana, Arial, Berlin Sans, Cambria, Lucida Fax và Times New Roman. Bài báo báo cáo kết quả thay đổi theo font; Calibri/Verdana có các trường hợp đạt 100%, trong khi Cambria và Times New Roman thấp hơn.

## Điều bài báo không đặc tả

Bài báo không đưa công thức cụ thể cho metric similarity, không chỉ rõ thuật toán threshold, quy tắc tách dòng/ký tự hay cách khôi phục khoảng trắng. Kích thước template, padding, chuẩn hóa hình dạng và cách xử lý ký tự dính nhau cũng không được quy định đủ để tái tạo implementation. Vì vậy không thể coi một công thức similarity hoặc kết quả chạy trên dữ liệu mới là kết quả do tác giả đề xuất/tái lập.

## Lựa chọn của project

Các mục sau là kỹ thuật triển khai để có demo nhiều dòng, có thể kiểm tra và chạy trên nhiều hệ điều hành; chúng không được gán cho bài báo:

| Hạng mục | Lựa chọn trong project | Lý do |
|---|---|---|
| Grayscale và nhị phân hóa | App dùng OpenCV grayscale và tự chọn ngưỡng Otsu; người dùng không cần cấu hình | Paper yêu cầu ảnh nhị phân nhưng không chỉ định cách lấy ngưỡng; Otsu là lựa chọn cố định của bản triển khai |
| Làm sạch | App cố định median/morphology ở trạng thái tắt và dùng connected components với ngưỡng 30 pixel | Giảm nhiễu; nét cao/mảnh `i/j`, `l`, `1` và dấu câu nhỏ gần baseline được giữ theo hình học |
| Segmentation | Horizontal/vertical projection; gộp mảnh nhỏ thẳng hàng như chấm `i/j`; thử tách vùng điểm thấp nếu glyph rộng và kết quả yếu | Cải thiện ký tự dính mà vẫn giữ phương pháp cổ điển có thể giải thích |
| Chuẩn hóa | Giữ tỷ lệ glyph, đặt giữa canvas 48×48 | Giữ nhiều chi tiết nét hơn khi so sánh các ảnh cùng kích thước |
| Template bank | App tạo mẫu từ các font khả dụng trên máy; gồm Calibri/Verdana nếu cài | Mở rộng khỏi hai font paper để bớt phụ thuộc vào một kiểu chữ |
| Matching trong app | `1 - mean(abs(I-T))` trên mask 0/1, tự tính bằng NumPy | Một metric cố định cho luồng nhận dạng chính, đơn giản và dễ diễn giải |
| Tie-break glyph gần nhau | `I/l` chọn theo vị trí trong từ; `i/j` dùng baseline khi điểm gần nhau | Khai thác ngữ cảnh vị trí khi nét pixel gần như trùng |
| NCC trong script đánh giá | Zero-mean normalized cross-correlation tự tính bằng NumPy | Phép so sánh nghiên cứu bổ sung; không phải lựa chọn người dùng trong app |
| Text reconstruction | Ngưỡng gap theo chiều cao ký tự trung vị | Ước lượng space và newline từ bounding box |
| Evaluation | Exact match, edit distance, character accuracy, CER và thời gian đo | Kết quả có thể kiểm chứng trên ground truth đi kèm |

Pixel Similarity là metric của luồng OCR chính vì bài báo không đặc tả công thức similarity. NCC được giữ trong script đánh giá để so sánh nghiên cứu. Điểm Pixel Similarity chỉ phục vụ xếp hạng, không phải xác suất đúng. Tie-break `I/l` là heuristic; nó có thể sai với acronym hoặc chữ hoa giữa từ.

## Phạm vi và giới hạn

Đầu vào mục tiêu là chữ in tiếng Anh trên nền sáng, bố cục tương đối thẳng. Một mảnh nhỏ thẳng hàng và gần nét lớn được gộp vào cùng dải dòng để giữ chấm `i/j`; projection theo cột sau đó tạo bbox chung. Ký tự chạm/dính có thể thành một segment rộng và được tô cam để người xem nhận ra bất định. Khoảng cách giữa các từ được suy đoán từ gap, nên font kerning hoặc ảnh có scale thay đổi mạnh có thể làm sai dấu cách.

Bộ ảnh do `scripts/generate_test_data.py` sinh dùng font cài trên máy, Pillow rasterizer và noise seed cố định. App và evaluation mặc định dùng mọi font khả dụng để tăng độ phủ; có thể truyền `--train-font Calibri --train-font Verdana` để kiểm tra riêng với template bank gần cách paper mô tả. Cả hai phép đo đều hữu ích cho implementation, nhưng không tương đương năm ảnh và điều kiện thí nghiệm trong paper. Không có số accuracy nào được hard-code trong ứng dụng.
