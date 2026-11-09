# Hướng dẫn thuyết trình

## 1. Bài toán

OCR (Optical Character Recognition) chuyển ảnh chứa chữ thành văn bản có thể chỉnh sửa. Project tập trung vào chữ in tiếng Anh A–Z, a–z, 0–9. Ứng dụng có một luồng sử dụng: tải ảnh lên, nhấn **Nhận dạng**, rồi xem hoặc tải văn bản.

## 2. Vì sao template matching?

Mỗi lớp ký tự có các mẫu raster lấy từ font. Glyph đầu vào được chuẩn hóa về cùng kích thước, chấm điểm với các template, rồi nhận lớp có điểm cao nhất. Cách này trực quan, không cần mô hình học sâu và phù hợp môn xử lý ảnh. Đổi lại, kết quả nhạy với font, cỡ chữ, antialiasing và chất lượng phân đoạn.

## 3. Tóm tắt bài báo

Hossain và Afrin (2019) mô tả bốn phần: preprocessing, feature extraction, feature training và feature matching. Paper chuyển ảnh grayscale thành ảnh nhị phân, loại object nhỏ hơn 30 pixel, tạo template huấn luyện từ Calibri/Verdana, rồi chọn template có metric cao nhất.

Paper không công bố công thức similarity hay quy tắc phân đoạn đủ chi tiết để tái tạo chính xác. Project chọn Pixel Similarity bằng NumPy và bổ sung tách dòng/ký tự bằng hình chiếu, khôi phục khoảng trắng và đo CER. Đây là các quyết định triển khai, không phải công thức được paper công bố.

## 4. Luồng hệ thống

```text
Ảnh PNG/JPG
   ↓
Grayscale → tiền xử lý tự động theo một cấu hình cố định
   ↓
Tách dòng và ký tự bằng horizontal/vertical projection
   ↓
Chuẩn hóa glyph 48×48
   ↓
Pixel Similarity (NumPy) ↔ template từ font cài trên máy
   ↓
Văn bản OCR + bounding box + điểm so khớp
```

Paper yêu cầu biểu diễn ký tự dạng nhị phân nhưng không quy định cách lấy ngưỡng. App tự chọn Otsu bên trong; người dùng không cần cấu hình bước này. Lọc thành phần nhỏ dùng ngưỡng 30 pixel theo paper, đồng thời giữ dấu câu nhỏ gần baseline và cặp chấm dọc như `:`/`;` theo vị trí cạnh thân chữ. Segment rộng có điểm thấp được thử tách quanh đáy projection, rồi chọn cách cắt cho hai glyph khớp template tốt nhất. Template 48×48 bao gồm chữ, số, dấu câu ASCII, nháy cong và gạch ngang thông dụng. Heuristic baseline giúp phân biệt `i/j`, dấu phẩy/dấu nháy gần giống nhau và gạch ngang/gạch dưới.

## 5. Demo

1. Cài Python và dependencies theo README, rồi chạy `python app.py`; mở `http://127.0.0.1:8501` trong trình duyệt.
2. Tải ảnh PNG/JPG có chữ in lên.
3. Nhấn **Nhận dạng**; app tự chạy tiền xử lý, phân đoạn và template matching.
4. Xem hoặc tải văn bản `.txt`. Mở **Chi tiết từng ký tự** nếu cần xem bounding box, điểm so khớp và các vùng cần kiểm tra lại.

Để kiểm tra mã, chạy `python -m pytest -q`. Để đo OCR trên 100 đoạn có nhãn, chạy `python scripts/generate_paragraph_data.py`, sau đó `python scripts/run_evaluation.py --dataset sample_images/paragraph_evaluation --matching pixel --output sample_images/paragraph_evaluation/evaluation_pixel.csv`; thêm `--limit 4` cho lượt nhanh. Kết quả đã lưu trên 100 ảnh: 96,50% độ chính xác ký tự gộp, CER 3,50%, exact match 50/100. Calibri và Verdana đều khớp 25/25; Times New Roman có CER 13,65%. Đây là đánh giá template matching trên ảnh tổng hợp; project không huấn luyện trọng số mô hình và kết quả không đại diện cho ảnh chụp thực tế. Script cũng giữ NCC làm phép so sánh nghiên cứu; app chính chạy Pixel Similarity.

## 6. Giới hạn

- Chữ dính hoặc ảnh nghiêng có thể làm phép chiếu ghép nhầm ký tự.
- Khoảng trắng được suy ra từ khoảng cách bounding box, không dựa trên ngữ cảnh ngôn ngữ.
- Pixel Similarity nhạy với font, độ đậm, antialiasing, scale và chất lượng segmentation.
- Các cặp gần giống như `O/0`, `I/l/1`, `B/8` có thể bị nhầm.
- Bộ template dùng font cài trên máy; nếu thiếu Calibri/Verdana, app tự dùng font khả dụng khác.

## 7. Câu hỏi giảng viên có thể hỏi

1. **Vì sao cần grayscale?** Giảm ba channel màu thành một cường độ để đơn giản hóa xử lý.
2. **Vì sao paper dùng ảnh nhị phân?** Tách foreground chữ và nền để trích xuất, so sánh hình dạng ký tự.
3. **Otsu làm gì trong app?** Tự chọn một ngưỡng từ histogram ảnh; người dùng không cần nhập thông số.
4. **Connected component có luôn bằng một ký tự không?** Không. Dấu `i/j` có thể tách rời; ký tự chạm nhau có thể thành một vùng lớn.
5. **Tại sao không xóa mọi vùng dưới 30 pixel?** Dấu chấm và nét mảnh có thể nhỏ; project giữ một số thành phần nhỏ thẳng hàng với thân ký tự.
6. **Pixel Similarity đo gì?** Tỷ lệ pixel trên hai mask đã chuẩn hóa trùng nhau: `1 - mean(|I-T|)`.
7. **Công thức similarity này có trong paper không?** Không. Paper nói dùng matching metric nhưng không nêu công thức; đây là lựa chọn triển khai.
8. **Vì sao segmentation dùng hình chiếu?** Cách này nhẹ, dễ giải thích và hiệu quả với các dòng chữ gần ngang, tách rời.
9. **CER được tính thế nào?** Khoảng cách Levenshtein chia cho độ dài ground truth; chèn, xóa và thay ký tự đều là lỗi.
10. **Khi nào hệ thống dễ sai?** Ảnh mờ/nghiêng, ký tự dính, font ngoài bộ mẫu, khoảng cách bất thường và ký tự có hình dáng gần giống.
