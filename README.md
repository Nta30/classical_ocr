# Classical OCR

Ứng dụng nhận dạng chữ in tiếng Anh bằng xử lý ảnh cổ điển và template matching. Cách dùng chỉ gồm tải ảnh lên, nhấn **Nhận dạng**, rồi xem hoặc tải văn bản. Không dùng OCR dựng sẵn, deep learning hay dịch vụ nhận dạng bên ngoài.

## Chạy trên Windows

Project dùng Python đã cài trên máy (Python 3.11 trở lên; Python Launcher `py -3` chọn bản Python 3 mới nhất khả dụng). Mở PowerShell tại thư mục project:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python app.py
```

Mở `http://127.0.0.1:8501` trong trình duyệt. Tải ảnh PNG/JPG lên và nhấn **Nhận dạng ảnh**. Giao diện dùng máy chủ HTTP trong thư viện chuẩn Python, không cần Streamlit. Dừng server bằng `Ctrl+C`.

Nếu `.venv` đã được tạo và dependencies đã cài, chỉ cần:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Nếu cổng 8501 đang được dùng, chạy `python app.py --port 8502` rồi mở `http://127.0.0.1:8502`.

## Phương pháp

Paper mô tả OCR bằng template matching, ảnh ký tự dạng nhị phân, và bộ template huấn luyện từ Calibri/Verdana. Paper không quy định công thức similarity hay chi tiết phân đoạn đủ để tái tạo chính xác. Ứng dụng cố định một luồng tự động: grayscale, ngưỡng Otsu tự chọn bên trong, lọc thành phần nhỏ có bảo vệ nét mảnh và dấu câu nhỏ gần baseline, tách dòng/ký tự bằng hình chiếu, rồi xếp hạng template chữ, số và dấu câu bằng Pixel Similarity tự cài đặt với NumPy. Gạch đỏ kiểm lỗi chính tả được tự phát hiện và loại khỏi ảnh trước khi phân đoạn để không dính vào chữ. Dấu chấm/phẩy nhỏ và cặp chấm dọc như `:`/`;` được giữ theo baseline của từng dòng; dấu phẩy nhỏ dính vào chữ cuối từ được tách riêng, còn dấu gạch ngang được phân biệt với gạch dưới. Segment rộng, điểm thấp được thử các đường cắt quanh vùng mực thưa và chỉ nhận khi hai glyph khớp template tốt hơn rõ rệt. Người dùng không cần chọn ngưỡng hoặc phép so khớp.

App tạo template từ các font tìm được trên máy, bao gồm Calibri/Verdana nếu có, để tăng độ phủ font; đây là phần mở rộng ngoài hai font huấn luyện paper nêu. Kết quả điểm so khớp dùng để xếp hạng, không phải xác suất đúng. Phạm vi hiện tại gồm chữ in A–Z, a–z, 0–9 và dấu câu phổ biến trên nền tương đối sáng, bố cục gần thẳng; chữ viết tay, ảnh nghiêng mạnh hoặc ký tự dính có thể nhận sai.

Chi tiết phương pháp và giới hạn: [phân tích paper](docs/paper_analysis.md), [thuật toán](docs/algorithms.md), [hướng dẫn thuyết trình](docs/presentation_guide.md).

## Đánh giá phát triển

```powershell
python -m pytest
python scripts/generate_test_data.py
python scripts/run_evaluation.py --matching pixel
python scripts/run_evaluation.py --matching pixel --train-font Calibri --train-font Verdana --output evaluation_paper_fonts.csv
python scripts/run_evaluation.py --matching ncc --output evaluation_ncc.csv
```

Mặc định script dùng cùng bộ font cục bộ như app; `--train-font` cho phép đo riêng hai font paper. NCC chỉ giữ lại để so sánh nghiên cứu; giao diện OCR thông thường chỉ chạy Pixel Similarity. Dữ liệu kiểm thử được sinh từ font cài trên máy và không được xem là tái lập chính xác thí nghiệm trong paper.

Kết quả trên bộ 32 ảnh tổng hợp hiện tại: **95,1% độ chính xác ký tự** (34 lỗi trên 688 ký tự tham chiếu), **CER 4,9%**, exact match **15/32 ảnh**. Đây là điểm gộp theo tổng ký tự; script cũng in macro-average để xem trung bình từng ảnh. Theo font: Calibri 96,5%, Verdana 95,3%, Arial 95,9%, Times New Roman 92,4%. Bộ dữ liệu có thêm câu với dấu phẩy, chấm, hai chấm, chấm phẩy, hỏi/chấm than, ngoặc, nháy và gạch ngang; xem từng kết quả trong `evaluation_pixel.csv`.

## Thư mục

```text
app.py
web/                    # giao diện web thuần HTML/CSS/JS
src/classical_ocr/       # tiền xử lý, phân đoạn, template matching, đánh giá
scripts/                 # tạo template, dữ liệu kiểm thử, chạy đánh giá
tests/                   # pytest
docs/                    # phân tích paper và giải thích thuật toán
sample_images/           # ảnh demo và dữ liệu đánh giá
```
