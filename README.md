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

## Kiểm thử mã và bộ ảnh ngắn

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Lệnh trên chạy các unit test cho preprocessing, segmentation, template matching, reconstruction và CER. Muốn kiểm tra OCR trên bộ 32 ảnh ngắn mặc định:

```powershell
.\.venv\Scripts\python.exe scripts\generate_test_data.py
.\.venv\Scripts\python.exe scripts\run_evaluation.py --dataset sample_images\evaluation --matching pixel --output evaluation_pixel.csv
```

Muốn đo riêng hai font paper thì thêm `--train-font Calibri --train-font Verdana`; NCC chỉ dùng để so sánh nghiên cứu, còn giao diện OCR chạy Pixel Similarity. Bộ 32 ảnh ngắn hữu ích cho lần kiểm tra nhanh sau khi sửa code; bộ 100 đoạn văn ở mục dưới dùng để đo OCR trên văn bản dài hơn. Cả hai đều là ảnh tổng hợp, không phải tái lập chính xác thí nghiệm trong paper.

### Kiểm thử các đoạn văn dài

Sinh 100 ảnh, mỗi ảnh có một đoạn tiếng Anh gồm đúng 10 câu. Script tự xuống dòng theo chiều rộng ảnh, lưu ảnh PNG, ground truth TXT và manifest CSV trong thư mục riêng:

```powershell
.\.venv\Scripts\python.exe scripts\generate_paragraph_data.py
```

Chạy thử nhanh 4 ảnh đầu (lần lượt dùng các font có sẵn):

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --dataset sample_images/paragraph_evaluation --matching pixel --limit 4 --output sample_images/paragraph_evaluation/evaluation_pixel_quick.csv
```

Chạy OCR và tính CER cho toàn bộ 100 ảnh bằng cách bỏ `--limit`:

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --dataset sample_images/paragraph_evaluation --matching pixel --output sample_images/paragraph_evaluation/evaluation_pixel.csv
```

Đọc tổng CER, CER trung bình theo từng ảnh và danh sách từng ảnh có CER cao trong kết quả terminal; mở `evaluation_pixel.csv` để so ground truth với dự đoán. Muốn so phương pháp NCC thì chạy lại với `--matching ncc` và một tên output khác. Đây là ảnh tổng hợp bằng font máy tính, không phải ảnh scan/chụp thực tế. Nội dung dùng tiếng Anh ASCII vì OCR hiện chưa nhận tiếng Việt có dấu.

Lượt OCR đủ 100 đoạn đã hoàn tất và được lưu tại `sample_images/paragraph_evaluation/evaluation_pixel.csv`: 2.741 lỗi trên 78.224 ký tự, CER gộp **3,50%**, độ chính xác ký tự **96,50%**, CER trung bình từng ảnh **3,50%**, exact match **50/100**. Calibri và Verdana có CER 0% và exact match 25/25 mỗi font; Arial có CER 0,35%; Times New Roman có CER 13,65%. Các template cũng dùng đủ bốn font này, nên đây là kết quả in-bank trên ảnh tổng hợp, không phải khả năng nhận dạng font chưa gặp. CSV được tính lại chỉ số sau khi bỏ newline thừa cuối ground truth; các dự đoán OCR đã lưu không thay đổi và không cần chạy OCR lần nữa.

Kết quả baseline trên bộ 32 ảnh ngắn: **95,1% độ chính xác ký tự** (34 lỗi trên 688 ký tự tham chiếu), **CER 4,9%**, exact match **15/32 ảnh**. Đây là điểm gộp theo tổng ký tự; script cũng in macro-average để xem trung bình từng ảnh. Theo font: Calibri 96,5%, Verdana 95,3%, Arial 95,9%, Times New Roman 92,4%. Bộ dữ liệu có thêm câu với dấu phẩy, chấm, hai chấm, chấm phẩy, hỏi/chấm than, ngoặc, nháy và gạch ngang; xem từng kết quả trong `evaluation_pixel.csv`.

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
