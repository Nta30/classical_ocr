# Giải thích dự án Classical OCR từ đầu, kèm công thức và ví dụ

Tài liệu dành cho người chưa học xử lý ảnh. Có thể đọc tuần tự từ đầu; không cần biết trước các từ tiếng Anh trong mã. Khi nhắc một thuật ngữ, tài liệu giải thích ngay ý nghĩa của nó.

Các ví dụ bảng số nhỏ trong tài liệu dùng để học cách tính. Chúng là ví dụ minh họa, không phải ảnh thật của người dùng hoặc kết quả chạy thực nghiệm mới. Những con số đánh giá thực tế được ghi riêng ở phần 19 và lấy từ tệp evaluation_pixel.csv đang có trong dự án.

## Mục lục

1. [Dự án giải quyết việc gì?](#1-dự-án-giải-quyết-việc-gì)
2. [Kiến thức nền: ảnh, tọa độ và phép tính](#2-kiến-thức-nền-ảnh-tọa-độ-và-phép-tính)
3. [Toàn bộ chương trình chạy theo thứ tự nào?](#3-toàn-bộ-chương-trình-chạy-theo-thứ-tự-nào)
4. [Chuẩn bị kho ảnh chữ mẫu lúc khởi động](#4-chuẩn-bị-kho-ảnh-chữ-mẫu-lúc-khởi-động)
5. [Bước 1: nhận và đọc ảnh tải lên](#5-bước-1-nhận-và-đọc-ảnh-tải-lên)
6. [Bước 2: chuyển ảnh màu thành ảnh xám](#6-bước-2-chuyển-ảnh-màu-thành-ảnh-xám)
7. [Bước 3: phát hiện và xóa gạch đỏ](#7-bước-3-phát-hiện-và-xóa-gạch-đỏ)
8. [Bước 4: tách chữ khỏi nền bằng Otsu](#8-bước-4-tách-chữ-khỏi-nền-bằng-otsu)
9. [Bước 5: lọc chấm nhiễu và giữ nét nhỏ](#9-bước-5-lọc-chấm-nhiễu-và-giữ-nét-nhỏ)
10. [Bước 6: tìm các dòng chữ](#10-bước-6-tìm-các-dòng-chữ)
11. [Bước 7: cắt từng dòng thành vùng ký tự](#11-bước-7-cắt-từng-dòng-thành-vùng-ký-tự)
12. [Bước 8: tìm dấu cách giữa các từ](#12-bước-8-tìm-dấu-cách-giữa-các-từ)
13. [Bước 9: đưa ảnh ký tự về 48 × 48](#13-bước-9-đưa-ảnh-ký-tự-về-48--48)
14. [Bước 10: tính điểm giống mẫu và xếp hạng](#14-bước-10-tính-điểm-giống-mẫu-và-xếp-hạng)
15. [Bước 11: thử tách vùng bị dính](#15-bước-11-thử-tách-vùng-bị-dính)
16. [Bước 12: xét vị trí để phân biệt chữ và dấu](#16-bước-12-xét-vị-trí-để-phân-biệt-chữ-và-dấu)
17. [Bước 13 và 14: ghép văn bản, vẽ khung và trả kết quả](#17-bước-13-và-14-ghép-văn-bản-vẽ-khung-và-trả-kết-quả)
18. [NCC: phép so sánh bổ sung trong mã](#18-ncc-phép-so-sánh-bổ-sung-trong-mã)
19. [Dữ liệu đánh giá và cách tính mọi chỉ số](#19-dữ-liệu-đánh-giá-và-cách-tính-mọi-chỉ-số)
20. [Sơ đồ mã nguồn, cách chạy và tài liệu tham khảo](#20-sơ-đồ-mã-nguồn-cách-chạy-và-tài-liệu-tham-khảo)

## 1. Dự án giải quyết việc gì?

Ví dụ bạn có ảnh chứa dòng chữ “Classical OCR 2026”. Với mắt người, bạn đọc được chữ ngay. Với máy tính, ảnh ban đầu chỉ là nhiều con số biểu diễn màu của các ô nhỏ. Chương trình phải tìm phần nào là nét chữ, tách từng chữ, xác định đó là chữ gì rồi tạo chuỗi văn bản.

Tên công việc này là **OCR**, viết đầy đủ là Optical Character Recognition: nhận dạng ký tự từ hình ảnh. “Ký tự” bao gồm chữ cái, chữ số và dấu câu.

Ứng dụng hiện tại cho bạn tải ảnh, bấm **Nhận dạng ảnh**, xem chữ được đọc ra, sao chép hoặc tải tệp TXT. Nó còn vẽ khung quanh các vùng ký tự và hiển thị thông tin từng vùng để bạn xem hệ thống đã cắt và đoán như thế nào.

Phương pháp chính là **so khớp mẫu**: chương trình có nhiều ảnh chữ mẫu, cắt từng vùng chữ trong ảnh đầu vào, rồi chấm xem vùng đó giống mẫu nào nhất. Tên tiếng Anh là template matching; từ đây “mẫu” có nghĩa là ảnh mẫu của một ký tự.

Ví dụ máy có các ảnh mẫu A, B, C, a, b, c, 0, 1… Một vùng ảnh được đem so với các mẫu này. Nếu mẫu B đạt điểm cao nhất thì dự đoán sơ bộ là B. Sau đó một số quy tắc về vị trí và kích thước có thể điều chỉnh dự đoán.

Dự án dùng cách xử lý ảnh cổ điển và các quy tắc do người viết đặt ra. Không có mạng học sâu, mô hình OCR có sẵn hoặc dịch vụ nhận dạng bên ngoài. Chương trình tạo ảnh mẫu từ font chữ trên máy. **Font** là kiểu hình dáng của chữ, ví dụ Arial hoặc Times New Roman.

Phạm vi mục tiêu là chữ in tiếng Anh A–Z, a–z, số 0–9 và dấu câu phổ biến; ảnh tương đối rõ, các dòng gần ngang. Chữ viết tay, tiếng Việt có dấu, bố cục nhiều cột và ảnh nghiêng mạnh chưa phải phạm vi được xử lý tốt.

## 2. Kiến thức nền: ảnh, tọa độ và phép tính

### 2.1. Ảnh là một bảng số

Một ảnh được ghép từ các ô màu rất nhỏ gọi là **pixel**, tiếng Việt là điểm ảnh.

Ảnh rộng 600 điểm và cao 200 điểm có:

~~~text
600 × 200 = 120.000 điểm ảnh
~~~

Chương trình xem ảnh như một bảng có 200 hàng và 600 cột. “Ma trận” chỉ là tên toán học của bảng số đó. Trong Python, NumPy là thư viện giúp lưu bảng số và thực hiện phép tính trên bảng.

### 2.2. Tọa độ x và y

- x cho biết vị trí theo chiều ngang, tăng từ trái sang phải.
- y cho biết vị trí theo chiều dọc, tăng từ trên xuống dưới.
- Điểm đầu tiên ở góc trái trên có x = 0, y = 0.
- W là chiều rộng: số cột.
- H là chiều cao: số hàng.

Khi viết bảng trong mã, chỉ số hàng đứng trước chỉ số cột, nên pixel tọa độ (x, y) thường được lấy bằng ảnh[y, x].

Ví dụ bảng 3 hàng, 4 cột:

~~~text
         x=0  x=1  x=2  x=3
y=0       10   20   30   40
y=1       50   60   70   80
y=2       90  100  110  120
~~~

Giá trị tại x = 2, y = 1 là 70.

### 2.3. Một điểm ảnh có thể mang những số gì?

Ảnh màu lưu ba số cho một điểm:

- R là lượng màu đỏ.
- G là lượng màu xanh lá.
- B là lượng màu xanh lam.

Mỗi số thường từ 0 đến 255. “8-bit” nghĩa là một giá trị được lưu bằng 8 chữ số nhị phân, cho 2^8 = 256 mức từ 0 đến 255. OpenCV sắp ba số theo thứ tự B, G, R. “BGR” chỉ nói về thứ tự lưu này.

Ảnh xám chỉ còn một số cho mỗi điểm: 0 thường là đen, 255 thường là trắng, các số ở giữa là xám.

Trong các bước tìm nét chữ, mã lại dùng bảng chỉ có hai giá trị: 0 là nền, 255 là nét chữ. Vì thế hình làm việc nội bộ có thể hiện nét chữ màu trắng trên nền đen dù ảnh gốc là chữ đen trên giấy trắng.

Đôi khi mã đổi bảng 0/255 thành 0/1 để dễ đếm. Tài liệu gọi:

~~~text
B(y,x): bảng 0 hoặc 255
M(y,x): bảng 0 hoặc 1

M(y,x) = 1 nếu B(y,x) > 0
M(y,x) = 0 nếu B(y,x) = 0
~~~

“Mask”, thường gặp trong mã, nghĩa là một bảng đánh dấu vị trí cần giữ, cần xóa hoặc thuộc nét chữ. Tài liệu sẽ gọi là bảng đánh dấu.

### 2.4. Các ký hiệu toán học sẽ dùng

| Cách viết | Đọc như thế nào? | Ví dụ |
|---|---|---|
| a × b | Nhân a với b | 3 × 4 = 12 |
| a / b | Chia a cho b | 12 / 4 = 3 |
| a² hoặc a^2 | Bình phương: a nhân với chính nó | 3² = 9 |
| \|a\| hoặc abs(a) | Lấy độ lớn, bỏ dấu âm | abs(-3) = 3 |
| max(a,b) | Chọn số lớn hơn | max(3,7) = 7 |
| min(a,b) | Chọn số nhỏ hơn | min(3,7) = 3 |
| round(a) | Làm tròn đến số nguyên gần nhất | round(3.2) = 3 |
| floor(a) | Lấy số nguyên không lớn hơn a | floor(3.8) = 3 |
| sum hoặc ∑ | Cộng tất cả các số được chỉ ra | ∑ của 2,3,5 là 10 |
| mean | Trung bình cộng | mean(2,3,7) = 4 |
| median | Số ở giữa sau khi sắp xếp | median(2,100,3) = 3 |
| ≥, ≤ | Lớn hơn hoặc bằng; nhỏ hơn hoặc bằng | 5 ≥ 5 đúng |
| “và” | Tất cả điều kiện phải đúng | A ≥ 6 và h ≥ 6 |
| “hoặc” | Chỉ cần một trong các điều kiện đúng | H ≤ 12 hoặc H ≥ 170 |

Nếu dãy có số phần tử chẵn, trung vị là trung bình hai phần tử ở giữa. Ví dụ median(10,18,20,100) = (18 + 20)/2 = 19. Nó ít bị một số quá lớn như 100 kéo lệch hơn trung bình cộng. Mã dùng trung vị nhiều lần để ước lượng chiều cao chữ thường gặp.

Trong phần diễn giải tiếng Việt, 0,40 nghĩa là số thập phân 0.40; khi viết mã Python phải dùng dấu chấm thập phân. Các khối công thức có tên tiếng Việt là cách mô tả phép tính để học, không phải đoạn Python có thể chép chạy trực tiếp. Dấu chấm phẩy trong max(3; 0,40q) chỉ dùng để ngăn các đối số cho dễ đọc. Những từ như round/median khi xuất hiện trong công thức được dùng theo nghĩa ở bảng trên; cách tính đúng tại các trường hợp làm tròn sát nửa số nguyên phụ thuộc hàm Python/Pillow được mã gọi.

Các số như 0,40 hay 1,35 trong quy tắc hình dạng là các hằng số đặt trong mã để điều chỉnh cách xử lý. Chúng không phải định luật toán học bảo đảm đúng với mọi ảnh.

## 3. Toàn bộ chương trình chạy theo thứ tự nào?

Có hai luồng gặp nhau ở bước so sánh:

~~~text
KHI MỞ CHƯƠNG TRÌNH:
Font chữ có trên máy
  → vẽ các chữ mẫu
  → đưa từng mẫu về 48 × 48
  → giữ kho mẫu trong bộ nhớ
                              ┐
KHI NGƯỜI DÙNG TẢI ẢNH:      │
Đọc ảnh                      │
  → đổi sang xám             │
  → xóa gạch đỏ nếu phát hiện│
  → tách nét chữ/nền         │
  → loại chấm nhiễu          │
  → tách dòng và vùng chữ    │
  → ước lượng dấu cách      │
  → đưa vùng chữ về 48 × 48 ─┴→ so với kho mẫu
                                  → xử lý vùng dính và trường hợp dễ nhầm
                                  → ghép thành văn bản
                                  → vẽ khung và trả kết quả
~~~

Kho mẫu được chuẩn bị **trước khi nhận ảnh**. Việc đặt phần giải thích kho mẫu trước ở đây phản ánh đúng cách app.py khởi động.

Không phải bước nào cũng có một “công thức nhận dạng”. Một số bước chỉ kiểm tra điều kiện, chọn vùng hoặc chuyển dữ liệu giữa trình duyệt và Python. Ở các bước đó, tài liệu sẽ ghi chính xác quy tắc được dùng thay vì gán thêm một công thức không có trong chương trình.

## 4. Chuẩn bị kho ảnh chữ mẫu lúc khởi động

**Chỗ làm việc này:** app.py gọi available_fonts() và generate_templates() trong src/classical_ocr/template_generator.py.

**Đầu vào:** tệp font được cài trên máy, ví dụ Arial.ttf.

**Cần làm gì:** tạo những ảnh nhỏ mà chương trình đã biết sẵn đáp án. Khi vẽ chữ A bằng font Arial, mã biết ảnh vừa tạo thuộc lớp A. “Lớp ký tự” chỉ có nghĩa là nhóm các mẫu có cùng đáp án A, B hoặc một ký tự cụ thể.

Danh sách font mà mã tìm gồm Calibri, Verdana, Arial, Times New Roman và DejaVu Sans. Có font nào trên máy thì dùng font đó; nó không tự lấy tất cả font bất kỳ của hệ điều hành.

### 4.1. Có bao nhiêu loại ký tự mẫu?

~~~text
26 chữ hoa + 26 chữ thường + 10 chữ số
+ 32 dấu câu/ký hiệu ASCII
+ 6 dấu nháy/gạch ngang bổ sung
= 100 loại ký tự
~~~

ASCII là một bộ ký tự cơ bản trong máy tính; ở đây phần dấu câu chứa những dấu quen thuộc như . , ! ? ( ) [ ] - và các ký hiệu khác.

Mỗi ký tự được vẽ ở năm cỡ: 28, 33, 34, 38 và 42. Sau đó tất cả được đưa về cùng bảng 48 × 48. Vẽ ở nhiều cỡ trước khi thu/phóng giúp có thêm biến thể nét, vì cách vẽ mép chữ ở các cỡ ban đầu có thể khác.

Nếu có 4 font:

~~~text
Số ảnh mẫu = số loại ký tự × số font × số cỡ
           = 100 × 4 × 5
           = 2.000 ảnh mẫu
~~~

Con số 2.000 chỉ đúng khi tìm thấy đúng bốn font như cấu hình trong CSV đánh giá hiện có. Máy khác có thể tìm thấy số font khác.

### 4.2. Chữ được vẽ như thế nào?

Pillow là thư viện dùng để vẽ chữ từ tệp font. Mã tạo một bảng xám 64 × 64 có nền 0, vẽ nét chữ với giá trị 255, tìm vị trí nét chữ để căn tương đối ở giữa, rồi gọi bước đưa ảnh về 48 × 48.

Một mẫu lưu bốn phần: ký tự đáp án, tên font, đường dẫn font và bảng số của ảnh mẫu.

**Đầu ra:** một danh sách ảnh mẫu trong bộ nhớ. App dùng lại danh sách này cho các ảnh tải lên. Nó không phải mô hình được học bằng cập nhật trọng số qua nhiều vòng huấn luyện. Nếu báo cáo dùng từ “huấn luyện mẫu”, cần giải thích rằng phần mã hiện tại tạo kho tham chiếu bằng cách vẽ chữ từ font.

## 5. Bước 1: nhận và đọc ảnh tải lên

**Đầu vào:** tệp PNG/JPG/JPEG người dùng chọn.

**Chỗ mã:** web/index.html gửi dữ liệu; OCRRequestHandler.do_POST() trong app.py nhận; load_image() trong preprocessing.py đọc ảnh.

### 5.1. Trình duyệt gửi ảnh thế nào?

Tệp là một dãy byte. Byte là đơn vị lưu dữ liệu gồm 8 bit. Trình duyệt đổi byte ảnh thành chuỗi Base64 rồi gửi trong JSON.

Base64 là cách biểu diễn byte bằng các ký tự văn bản. Nó giữ dữ liệu để phía Python khôi phục, không tự làm ảnh rõ hơn hoặc thực hiện nhận dạng.

JSON là cách đóng gói dữ liệu theo cặp tên và giá trị. Yêu cầu gửi đi có tên tệp và chuỗi dữ liệu ảnh:

~~~text
filename: tên tệp
image: dữ liệu ảnh đã chuyển thành chuỗi Base64
~~~

Địa chỉ nhận là POST /api/recognize. “API” ở đây là điểm nhận yêu cầu của chương trình Python; “POST” là kiểu yêu cầu dùng để gửi dữ liệu.

### 5.2. Quy tắc kiểm tra

~~~text
Dung lượng ảnh ≤ 15 × 1024 × 1024 = 15.728.640 byte

Dung lượng toàn bộ yêu cầu ≤ 21 × 1024 × 1024 = 22.020.096 byte
~~~

Base64 thường dài khoảng 4/3 số byte ban đầu:

~~~text
Số ký tự Base64 = 4 × ceil(n / 3)
~~~

n là số byte ảnh. ceil nghĩa là làm tròn lên. Ví dụ 3 byte được biểu diễn bằng 4 ký tự; 4 byte cần 8 ký tự vì phải chia thành hai nhóm. Vì vậy giới hạn toàn bộ yêu cầu cần lớn hơn giới hạn ảnh.

Máy chủ kiểm tra có dữ liệu hay không, có đúng chuỗi Base64 không, đuôi tên tệp có thuộc PNG/JPG/JPEG không, byte ảnh có đọc được không và có vượt giới hạn không.

### 5.3. Giải mã thành bảng màu

Python khôi phục byte ảnh rồi OpenCV giải mã PNG/JPEG thành bảng số màu BGR. Nếu dữ liệu không tạo được ảnh hoặc ảnh rỗng thì dừng và báo lỗi.

**Đầu ra:** ảnh màu có kích thước H × W × 3, nghĩa là H hàng, W cột và ba giá trị màu ở mỗi điểm. Ở bước này chương trình vẫn chưa biết điểm nào thuộc chữ.

## 6. Bước 2: chuyển ảnh màu thành ảnh xám

**Đầu vào:** ảnh BGR ba kênh màu.

**Cần làm gì:** rút ba số màu thành một số độ sáng để dễ tìm nét chữ và nền.

**Chỗ mã:** to_grayscale() trong preprocessing.py gọi cv2.cvtColor().

### Công thức

~~~text
Y = 0,299 × R + 0,587 × G + 0,114 × B
~~~

R, G, B là lượng đỏ, xanh lá, xanh lam tại cùng một điểm. Y là độ sáng xám thu được. Tổng ba hệ số bằng 1. Kênh xanh lá được đặt trọng số lớn hơn, không phải lấy ba kênh bằng nhau.

### Ví dụ tính

Một điểm có R = 200, G = 100, B = 50:

~~~text
Y = 0,299 × 200 + 0,587 × 100 + 0,114 × 50
  = 59,8 + 58,7 + 5,7
  = 124,2
~~~

Ảnh 8-bit lưu giá trị nguyên nên kết quả gần 124. Chấm màu đó trở thành một mức xám.

**Đầu ra:** bảng H × W. Mỗi điểm chỉ còn số từ 0 đến 255. Đen gần 0, trắng gần 255.

**Nếu làm không tốt:** hai màu khác nhau nhưng có độ sáng gần nhau sẽ gần giống nhau trong ảnh xám. Đó là lý do bước dò gạch đỏ vẫn nhìn lại ảnh màu gốc, không chỉ nhìn ảnh xám.

## 7. Bước 3: phát hiện và xóa gạch đỏ

**Đầu vào:** ảnh màu gốc và ảnh xám vừa tạo.

**Chỗ mã:** _remove_spellcheck_underlines() trong preprocessing.py.

**Mục đích:** gạch đỏ kiểm lỗi chính tả trong ảnh chụp màn hình có thể dính vào chữ khi chuyển sang đen/trắng. Mã cố tìm và xóa những vệt như vậy trước khi cắt ký tự.

### 7.1. Xác định điểm màu đỏ

Mã đổi cách biểu diễn màu từ BGR sang HSV. HSV gồm:

- H: màu thuộc nhóm nào, như đỏ/xanh/vàng; OpenCV biểu diễn từ 0 đến 179.
- S: màu đậm hay nhạt, từ 0 đến 255; xám thường có S thấp.
- V: sáng hay tối, từ 0 đến 255.

OpenCV thực hiện phép đổi màu qua cv2.cvtColor(). Mã dự án không tự cài công thức chuyển BGR thành HSV. Sau khi có H, S, V, nó áp dụng đúng điều kiện:

~~~text
Là điểm đỏ khi:
(H ≤ 12 hoặc H ≥ 170) và S ≥ 65 và V ≥ 80
~~~

H có hai khoảng vì màu đỏ nằm gần hai đầu thang biểu diễn màu. Ví dụ H = 5, S = 200, V = 180 qua cả ba điều kiện nên được đánh dấu; điểm xám có S = 0 không qua điều kiện S ≥ 65.

### 7.2. Nối các đoạn đỏ đứt nhỏ

Vệt kiểm lỗi thường là đường lượn sóng có chỗ đứt. Mã dùng một ô dò dài 5 điểm, cao 1 điểm để nối các khe hẹp theo chiều ngang.

Tên thư viện gọi phép này là “closing”, tức làm kín khoảng trống nhỏ. Nó gồm hai thao tác:

~~~text
Nới rộng: tại một điểm, lấy giá trị lớn nhất trong ô dò.
Thu lại: tại một điểm, lấy giá trị nhỏ nhất trong ô dò.

Closing(M) = thu_lại(nới_rộng(M))
~~~

M là bảng đánh dấu điểm đỏ. “Ô dò” là một vùng nhỏ được trượt qua ảnh, không phải ô cửa sổ giao diện. Với bảng 0/1, lấy lớn nhất có nghĩa chỉ cần một điểm gần đó bằng 1 thì đánh dấu; lấy nhỏ nhất có nghĩa tất cả điểm trong ô cần bằng 1.

### 7.3. Chọn vệt đỏ có dạng mảnh, dài

Mã nhóm các điểm đỏ chạm nhau, rồi xét mỗi nhóm bằng chiều rộng w và chiều cao h:

~~~text
w ≥ max(16, round(0,015 × W))
h ≤ 10
w ≥ 2,5 × max(1,h)
~~~

W là chiều rộng ảnh gốc. Cả ba điều kiện phải đúng.

Ví dụ ảnh rộng 1.000 điểm, nhóm đỏ rộng 40, cao 4:

~~~text
Ngưỡng rộng = max(16, round(15)) = 16
40 ≥ 16       đúng
4 ≤ 10        đúng
40 ≥ 2,5 × 4  đúng
~~~

Nhóm này được chọn để xóa. Một vùng đỏ cao 30 điểm không qua điều kiện h ≤ 10.

### 7.4. Lấp vùng đã xóa

Mã nới bảng vùng cần xóa bằng ô 3 × 3 để bao cả mép đỏ, sau đó gọi:

~~~python
cv2.inpaint(gray, erase, 2, cv2.INPAINT_TELEA)
~~~

gray là ảnh xám; erase đánh dấu vùng cần sửa; 2 là bán kính lân cận dùng khi lấp. OpenCV dùng phương pháp Telea để suy ra giá trị từ vùng xung quanh, lấp dần từ biên vào trong.

Ý tưởng tính có thể hiểu bằng trung bình có trọng số:

~~~text
Giá trị mới ≈ tổng(trọng số × giá trị điểm lân cận)
              / tổng trọng số
~~~

Ví dụ minh họa có ba điểm xung quanh là 240, 250, 245 và trọng số giả định là 1, 2, 1 thì kết quả là (240 + 500 + 245)/4 = 246,25. Các trọng số 1,2,1 chỉ dùng để giải thích khái niệm; OpenCV tự tính trọng số của phương pháp Telea, dự án không đặt cố định như ví dụ.

**Đầu ra:** ảnh xám đã xử lý vệt đỏ được chọn, vẫn cùng kích thước H × W.

**Giới hạn:** quy tắc này có thể bỏ sót vệt không đỏ hoặc hình dạng khác; chi tiết đỏ thật trong ảnh cũng có thể bị tác động nếu giống đường cần xóa.

## 8. Bước 4: tách chữ khỏi nền bằng Otsu

**Đầu vào:** ảnh xám sau bước trên.

**Chỗ mã:** binarize() trong preprocessing.py.

**Mục đích:** quyết định điểm nào thuộc nét chữ, điểm nào thuộc nền. “Nhị phân hóa” nghĩa là biến nhiều mức xám thành chỉ hai giá trị.

### 8.1. Nếu đã biết ngưỡng t thì xử lý thế nào?

t là một số độ sáng. Mã dùng ngưỡng đảo của OpenCV:

~~~text
B(y,x) = 255 nếu G(y,x) ≤ t
B(y,x) =   0 nếu G(y,x) > t
~~~

G(y,x) là độ xám tại vị trí đang xét. B là ảnh hai giá trị. Dấu ≤ tương ứng cách THRESH_BINARY_INV của OpenCV xử lý điểm bằng ngưỡng.

Ví dụ t = 100:

~~~text
Ảnh xám:       20   80  100  180  240
Kết quả B:    255  255  255    0    0
~~~

Các điểm tối trở thành nét chữ 255. Các điểm sáng trở thành nền 0.

### 8.2. Otsu tìm t như thế nào?

Không phải ảnh nào cũng nên dùng t = 100. Otsu thử các ngưỡng có thể có và tìm cách chia ảnh thành hai nhóm độ sáng tách nhau rõ.

Đầu tiên lập bảng đếm độ sáng, gọi là histogram. Ví dụ ảnh có 8 điểm:

~~~text
20, 20, 30, 30, 220, 220, 230, 230

Độ sáng v:      20   30  220  230
Số điểm h(v):    2    2    2    2
~~~

h(v) là số điểm có độ sáng v. N là tổng số điểm ảnh; ở đây N = 8.

~~~text
p(v) = h(v) / N
~~~

p(v) là tỷ lệ số điểm ở mức v. Mỗi mức trong ví dụ chiếm 2/8 = 0,25.

Với một ngưỡng t, chia hai nhóm:

- Nhóm 0: mức sáng từ 0 đến t.
- Nhóm 1: mức sáng từ t+1 đến 255.

Tính tỷ lệ hai nhóm:

~~~text
w0(t) = ∑ p(v), với v từ 0 đến t
w1(t) = ∑ p(v), với v từ t+1 đến 255
~~~

Tính độ sáng trung bình mỗi nhóm:

~~~text
mu0(t) = [∑ v × p(v), v từ 0 đến t] / w0(t)
mu1(t) = [∑ v × p(v), v từ t+1 đến 255] / w1(t)
~~~

mu đọc là “miu”, chỉ là tên cho giá trị trung bình. Nếu một nhóm không có điểm thì không dùng phép chia cho 0 này.

Cuối cùng tính điểm phân tách:

~~~text
J(t) = w0(t) × w1(t) × [mu0(t) − mu1(t)]²
~~~

Bình phương chênh lệch trung bình làm hai nhóm cách xa nhau có điểm lớn. Hai tỷ lệ w0,w1 làm việc chỉ tách một nhóm quá nhỏ ít được ưu tiên hơn. Otsu chọn t làm J(t) lớn nhất.

### 8.3. Ví dụ tính đầy đủ

Chọn thử t = 30:

~~~text
Nhóm 0: 20,20,30,30      Nhóm 1: 220,220,230,230
w0 = 4/8 = 0,5           w1 = 4/8 = 0,5
mu0 = (20+20+30+30)/4 = 25
mu1 = (220+220+230+230)/4 = 225

J(30) = 0,5 × 0,5 × (25−225)²
      = 0,25 × 40.000
      = 10.000
~~~

Nếu thử t = 20:

~~~text
Nhóm 0: 20,20
Nhóm 1: 30,30,220,220,230,230

w0 = 0,25; w1 = 0,75
mu0 = 20; mu1 = 160

J(20) = 0,25 × 0,75 × (20−160)² = 3.675
~~~

Vì 10.000 lớn hơn 3.675, ngưỡng 30 chia tốt hơn 20 trong ví dụ này. Nhiều ngưỡng ở khoảng trống 30 đến 219 có thể cho cùng phân nhóm; không phải lúc nào chỉ có một ngưỡng tốt nhất duy nhất.

Dự án gọi OpenCV để tính Otsu, không tự viết vòng thử các ngưỡng. Các công thức trên giải thích thuật toán được yêu cầu qua cờ THRESH_OTSU.

### 8.4. Kiểm tra ảnh có đang bị đảo trắng/đen không?

Sau ngưỡng, mã tính:

~~~text
f = số điểm có B > 0 / (H × W)

Nếu f > 0,5 thì đổi B thành 255 − B.
~~~

Ví dụ 90% ảnh đang được đánh dấu là nét chữ, khả năng cao nền đã bị nhận thành chữ nên mã đảo lại. Đây là một quy tắc dựa trên giả định nền chiếm phần lớn ảnh, không đảm bảo đúng với ảnh bị cắt quá sát hoặc bố cục đặc biệt.

**Đầu ra:** ảnh B chỉ có nét chữ 255 và nền 0.

**Giới hạn:** Otsu dùng một ngưỡng cho toàn ảnh. Nếu nửa trái tối do bóng còn nửa phải sáng, một ngưỡng có thể giữ tốt bên này và làm mất chữ bên kia. Mã hiện chưa dùng ngưỡng riêng theo từng vùng.


## 9. Bước 5: lọc chấm nhiễu và giữ nét nhỏ

**Đầu vào:** ảnh hai giá trị B.

**Mục tiêu:** bỏ những đốm nhỏ do bụi, ảnh nén hoặc nhiễu, nhưng giữ dấu chấm, dấu phẩy và nét chữ mảnh.

**Chỗ mã:** clean_binary(), remove_small_components(), _small_punctuation_components() trong preprocessing.py.

### 9.1. Nhóm các điểm chạm nhau

Đổi B thành M gồm 0/1. Với mỗi điểm mực, xét tám điểm quanh nó:

~~~text
↖  ↑  ↗
←  ●  →
↙  ↓  ↘
~~~

Hai điểm mực được xem là nối với nhau nếu có đường đi qua các điểm mực kề ngang, dọc hoặc chéo. Từng nhóm được gắn một số nhãn.

Ví dụ:

~~~text
M:                  Nhãn nhóm:
1 1 0 0 0           1 1 0 0 0
0 1 0 0 1           0 1 0 0 2
0 0 0 0 1           0 0 0 0 2
~~~

Nhóm số 1 có 3 điểm mực. Nhóm số 2 có 2 điểm mực. Những số nhãn chỉ dùng để phân biệt nhóm, không có nghĩa nhãn 1 là chữ “1”.

Tên kỹ thuật của việc này là tìm thành phần liên thông. Hàm OpenCV dùng là connectedComponentsWithStats().

### 9.2. Tính kích thước mỗi nhóm

Với một nhóm C:

~~~text
A = số điểm mực thuộc nhóm C
x_min = cột trái nhất có mực
x_max = cột phải nhất có mực
y_min = hàng trên nhất có mực
y_max = hàng dưới nhất có mực

w = x_max − x_min + 1
h = y_max − y_min + 1
~~~

A là **diện tích mực**, còn w × h là **diện tích hình chữ nhật bao ngoài**. Hai số này khác nhau.

Ví dụ một chữ O có thể được bao bởi hình 20 × 30 = 600 điểm nhưng thực tế chỉ có 180 điểm mực vì giữa O rỗng. Khi nói ngưỡng 30 ở bước này, mã xét A = 180, không xét 600.

### 9.3. Quy tắc cơ bản: giữ vùng đủ lớn

~~~text
Nếu A ≥ 30: giữ nhóm.
Nếu A < 30: xét các ngoại lệ bên dưới.
~~~

Ví dụ đốm rời có 2 điểm thường bị xóa; thân chữ có 100 điểm được giữ.

Giá trị 30 có trong bài báo dự án tham khảo. Các ngoại lệ để bảo vệ nét/dấu nhỏ là phần bổ sung trong mã.

### 9.4. Giữ nét mảnh như l hoặc 1

Một nhóm dưới 30 vẫn được giữ khi:

~~~text
A ≥ 6 và h ≥ 6 và h ≥ 1,8 × w
~~~

Ví dụ nét có A = 20, w = 2, h = 12:

~~~text
20 ≥ 6          đúng
12 ≥ 6          đúng
12 ≥ 1,8×2      đúng
~~~

Nó cao và hẹp, có thể là thân chữ nên được giữ.

### 9.5. Giữ chấm gần thân i/j

Chấm i và thân i là hai nhóm mực khác nhau. Mã tìm một thân cao, hẹp và lớn hơn chấm. Nó so tâm ngang và khoảng cách dọc:

~~~text
Tâm ngang chấm = x + w/2
Tâm ngang thân = xo + wo/2

Chênh tâm ngang ≤ 0,65 × max(w,wo)

Khoảng trống dọc =
max(yo − (y+h), y − (yo+ho), 0)
~~~

x,y,w,h mô tả chấm; xo,yo,wo,ho mô tả thân được xét. Nếu hai vùng nằm cạnh nhau theo chiều dọc, công thức lấy số điểm trắng ngăn giữa. Nếu chồng theo chiều dọc, giá trị này bằng 0.

Thân được xét cần có diện tích ít nhất max(6; 1,5 × diện tích chấm), cao ít nhất 6 và hẹp với ho ≥ 1,5 × wo. Khoảng trống dọc phải không vượt max(12; 3 × max(h,ho)).

Đây là điều kiện khá rộng để tránh làm mất chấm. Nó giữ pixel chấm, chưa vẽ đường nối chấm vào thân. Việc đưa chúng vào cùng một vùng dòng được làm ở bước sau.

### 9.6. Giữ dấu câu dựa vào “đường chân chữ”

Các chữ như a, e, n thường có đáy nằm gần một đường ngang. Ta gọi đó là **đường chân chữ**; tên tiếng Anh trong mã là baseline. Nó không phải một đường có sẵn trong ảnh, mà là vị trí do mã ước lượng.

Với các thân chữ ở cùng hàng:

~~~text
Đáy của một thân = y + h
Đường chân chữ b = median(các vị trí đáy)
Chiều cao thường gặp q = median(các chiều cao)
~~~

Ví dụ đáy bốn thân là 100,101,100,99 thì:

~~~text
b = median(99,100,100,101) = 100
~~~

Mã xét những cụm nhỏ có ít nhất 3 điểm mực, nằm gần thân chữ theo chiều ngang. Nếu tâm dấu nằm gần đường chân chữ thì có thể là chấm/phẩy. Nếu dấu ở cao hơn thì có thể là dấu nháy. Hai cụm nhỏ thẳng hàng theo chiều dọc có thể tạo dấu hai chấm hoặc chấm phẩy.

Các điều kiện chính được mã dùng:

| Phép xét | Điều kiện |
|---|---|
| Nhóm coi là thân để ước lượng | A ≥ 30 và h ≥ 6 |
| Khoảng cách ngang tới thân gần nhất | ≤ max(3; 0,70 × chiều cao thường gặp) |
| Dấu nhỏ gọn | w ≤ max(3; round(0,40q)) và h ≤ max(3; round(0,55q)) |
| Hoặc vệt ngang mảnh | w ≥ 1,8h và h ≤ max(2; round(0,25q)) |
| Tâm dấu trong khoảng gần dòng | b − 1,30q ≤ tâm_y ≤ b + 0,45q |
| Vệt ngang giữa thân chữ | b − 0,75q ≤ tâm_y ≤ b − 0,20q |
| Hai chấm gần thẳng hàng | chênh tâm x ≤ max(2; 0,16 × chiều cao thường gặp toàn ảnh) |
| Độ cách dọc hai chấm | từ 0,25 đến 0,90 lần chiều cao thường gặp toàn ảnh |

Trong các phép xét gần dòng, b và q được ước lượng lại từ các thân gần hàng của dấu đang xét. Mã không dùng một đường chân chung cho cả trang, vì mỗi dòng ở vị trí y khác nhau.

Các hệ số chỉ tạo tiêu chí “có vẻ giống dấu câu”. Một đốm nhiễu nằm đúng vị trí vẫn có thể được giữ; một dấu quá nhỏ hoặc quá xa thân vẫn có thể bị xóa.

### 9.7. Bộ lọc nào thực sự đang bật?

Ứng dụng web gọi:

~~~text
median_kernel = 1
morphology = "none"
min_component_area = 30
~~~

Điều này có nghĩa:

- Bộ lọc trung vị đang tắt. “Bộ lọc trung vị” thay giá trị ở giữa một ô dò bằng trung vị các giá trị xung quanh, giúp bỏ chấm nhiễu nhưng có thể làm mất nét nhỏ. Ô 1 × 1 không thay đổi gì.
- Phép mở/đóng hình dạng trên ảnh chữ đang tắt. Phép mở là thu nhỏ rồi nới lại, có thể bỏ chấm nhỏ; phép đóng là nới rồi thu lại, có thể lấp khe. Mã có hỗ trợ nhưng app không dùng ở bước lọc ảnh chữ.
- Quy tắc lọc nhóm mực diện tích 30 và các ngoại lệ phía trên vẫn chạy.

Đừng nhầm với phép đóng đã dùng riêng trên bảng dò gạch đỏ ở phần 7: đó là thao tác khác, ở vị trí khác.

**Đầu ra:** ảnh nét chữ đã giảm một số chấm nhiễu, kích thước không đổi. Các điểm còn lại được dùng để tìm dòng.

## 10. Bước 6: tìm các dòng chữ

**Đầu vào:** bảng 0/1 M sau lọc.

**Chỗ mã:** segment_text(), _runs(), _merge_detached_mark_bands() trong segmentation.py.

**Cần làm gì:** xác định những khoảng hàng nào chứa một dòng chữ.

### 10.1. Đếm mực trên từng hàng

~~~text
Py(y) = ∑ M(y,x), với x từ 0 đến W−1
~~~

Py(y) đọc là tổng theo hàng y. Vì mỗi điểm mực bằng 1, phép cộng này đếm số điểm mực trong hàng. Người ta gọi đây là hình chiếu ngang.

Ví dụ:

~~~text
M:                    Py:
0 0 0 0 0 0             0
0 1 1 0 1 0             3
0 1 1 0 1 0             3
0 0 0 0 0 0             0
0 0 1 1 0 0             2
0 0 1 1 0 0             2
0 0 0 0 0 0             0
~~~

Dãy tổng là [0,3,3,0,2,2,0]. Các hàng 1–2 có mực, hàng 4–5 có mực, giữa chúng có hàng trắng. Ban đầu ta có hai dải ứng viên dòng.

Mã lưu dải theo dạng [đầu, cuối), nghĩa là lấy đầu nhưng không lấy cuối. Dải hàng 1–2 được ghi [1,3). Quy ước này thuận tiện cho thao tác cắt bảng của Python.

### 10.2. Tại sao không chỉ lấy mọi dải làm một dòng?

Chấm i có thể nằm ở một dải riêng phía trên thân. Nếu coi mỗi dải là một dòng, chữ i sẽ bị chia thành “dòng chấm” và “dòng thân”.

Mã xem một cụm nhỏ có giống chấm không rồi tìm cụm lớn hơn gần bên dưới/ở gần nó:

~~~text
0,55 ≤ chiều rộng chấm / chiều cao chấm ≤ 1,80

Chiều cao chấm ≤ 0,55 × chiều cao thân
Diện tích chấm ≤ 0,45 × diện tích thân

Chênh tâm ngang ≤ max(2; 0,65 × max(rộng_chấm,rộng_thân))
Khoảng trống dọc ≤ max(4; round(0,35 × cao_thân))
~~~

Ví dụ chấm 2 × 2 có diện tích 4; thân cao 16, rộng 3 và có 30 điểm mực. Chấm vuông có tỷ lệ 1; cao 2 ≤ 8,8; diện tích 4 ≤ 13,5. Nếu thẳng hàng và chỉ cách thân 3 điểm thì phù hợp để gộp dải.

Gộp dải nghĩa là mở vùng dòng để chứa cả chấm và thân. Nó vẫn không biến chấm và thân thành một cụm mực liền nhau.

**Đầu ra:** danh sách các vùng dòng, mỗi vùng là một khoảng hàng trên ảnh.

**Dễ sai ở đâu:** dòng nghiêng mạnh có thể chồng hàng của nhau; chấm rời hoặc dòng quá sát có thể gây gộp nhầm. Mã không có bước tự xoay ảnh cho thẳng trước khi đếm.

## 11. Bước 7: cắt từng dòng thành vùng ký tự

**Đầu vào:** một vùng dòng gồm các hàng từ y0 đến trước y1.

**Chỗ mã:** segment_text(), _trim_bbox(), _merge_same_component_runs() trong segmentation.py.

### 11.1. Đếm mực theo từng cột

~~~text
Px(x) = ∑ M(y,x), với y từ y0 đến y1−1
~~~

Px(x) là số điểm mực trong cột x thuộc dòng đang xét; tên kỹ thuật là hình chiếu dọc.

Ví dụ một dòng:

~~~text
0 1 1 0 0 1 1 0
0 1 1 0 0 1 0 0
0 1 1 0 0 1 1 0

Tổng từng cột:
0 3 3 0 0 3 2 0
~~~

Cột 1–2 có mực, cột 5–6 có mực; mã tạo hai vùng chữ sơ bộ. Ở thời điểm này chưa biết đó là chữ gì.

Nếu hai chữ dính nhau, giữa chúng không còn cột trắng. Chúng có thể bị cắt chung thành một vùng. Đây là hạn chế chính của cách đếm theo cột.

Mã còn có một phép kiểm tra trước khi nối hai dải cách rất gần: chỉ cho nối nếu cách không quá một cột và cùng mang một nhãn cụm mực. Mục đích là không nối hai vùng chỉ vì khoảng cách nhỏ; việc có nhãn chung hay không do phép tìm cụm mực quyết định.

### 11.2. Cắt sát vùng mực và lưu khung chữ

Tìm các điểm mực trong vùng sơ bộ rồi lấy:

~~~text
x = x_min
y = y_min
w = x_max − x_min + 1
h = y_max − y_min + 1
~~~

Bốn số (x,y,w,h) chính là **khung chữ**, tên tiếng Anh là bounding box. Ví dụ (20,40,8,15) nghĩa là vùng bắt đầu ở cột 20, hàng 40, rộng 8 và cao 15 điểm.

Trong cách cắt của Python:

~~~text
Lấy các cột từ x đến trước x+w
Lấy các hàng từ y đến trước y+h
~~~

Khi vẽ khung, điểm cuối cần là x+w−1 và y+h−1. Vì vậy cùng một khung có thể xuất hiện phép cộng w trong chỗ cắt và w−1 trong chỗ vẽ.

Ở bước này, mã bỏ vùng có w × h < 6. Đây là diện tích **khung bao**, khác với diện tích mực A đã dùng ở phần lọc nhiễu.

### 11.3. Đánh dấu vùng rộng bất thường

Mã lấy trung vị chiều cao các vùng hợp lệ, gọi là q. Với vùng đang xét:

~~~text
Nếu w > 1,35 × max(h,q) thì gắn cờ cần xem lại.
~~~

Ví dụ q = 20, vùng có w = 35, h = 18:

~~~text
Ngưỡng = 1,35 × max(18,20) = 27
35 > 27 nên gắn cờ.
~~~

Vùng rộng có thể chứa hai chữ dính, cũng có thể chỉ là một ký tự vốn rộng. Cờ này không chứng minh chắc chắn vùng đó sai.

**Đầu ra:** từng vùng ký tự có ảnh cắt, khung (x,y,w,h), số thứ tự dòng, số thứ tự ký tự và cờ cần xem lại. Dấu cách được bổ sung ở bước tiếp.

## 12. Bước 8: tìm dấu cách giữa các từ

**Đầu vào:** các khung chữ theo thứ tự trái sang phải trong cùng dòng.

**Chỗ mã:** _estimate_word_gap_threshold() và segment_text().

**Cần làm gì:** phân biệt khoảng trống giữa hai chữ cùng từ với khoảng trắng giữa hai từ.

### 12.1. Đo khoảng trống

Với vùng trước bắt đầu ở x1, rộng w1; vùng sau bắt đầu ở x2:

~~~text
gap = x2 − (x1+w1)
~~~

gap là số cột trống giữa hai khung. Ví dụ x1 = 10, w1 = 8, x2 = 21 thì gap = 21−18 = 3.

### 12.2. Đặt ngưỡng ban đầu theo chiều cao chữ

q là trung vị chiều cao các khung hợp lệ trong dòng:

~~~text
tau = max(3; round(0,40 × q)+1)
~~~

tau là tên ngưỡng dấu cách. Nếu q = 20:

~~~text
tau = max(3; round(8)+1) = 9
~~~

Khoảng trống từ 9 trở lên có khả năng là dấu cách.

### 12.3. Điều chỉnh bằng chính khoảng cách trong dòng

Mã lấy các gap dương, sắp tăng dần. Nếu có ít hơn bốn khoảng thì giữ ngưỡng ban đầu. Nếu có đủ, xét từng cặp liên tiếp low, high:

~~~text
r = high / max(1,low)
~~~

Chọn cặp có r lớn nhất. Nếu r ≥ 1,30 và high ≥ tau thì:

~~~text
tau_mới = max(tau; round((low+high)/2))
~~~

Ví dụ các gap là [2,2,3,3,17,18] và tau ban đầu = 9. Bước nhảy lớn nhất là 3 lên 17:

~~~text
r = 17/3 ≈ 5,67
r ≥ 1,30 và 17 ≥ 9

tau_mới = max(9; round((3+17)/2))
        = max(9;10)
        = 10
~~~

Sau điều chỉnh, gap = 3 không thành dấu cách; gap = 17 thành dấu cách.

**Đầu ra:** với mỗi vùng, cờ space_before cho biết có nên đặt dấu cách trước nó không. Ở phần ghép cuối, quy tắc dấu câu có thể bỏ dấu cách này.

**Giới hạn:** quy tắc không biết từ tiếng Anh nào đúng. Khoảng cách font và hình ảnh thay đổi có thể làm mất dấu cách dù nhận đúng mọi chữ.

## 13. Bước 9: đưa ảnh ký tự về 48 × 48

**Đầu vào:** ảnh cắt của một vùng ký tự, kích thước bất kỳ.

**Chỗ mã:** normalize_glyph() trong template_generator.py. rank_templates() gọi nó cho ảnh ký tự; phần tạo kho mẫu cũng dùng cùng cách chuẩn hóa.

**Mục đích:** đưa ảnh đầu vào và ảnh mẫu về cùng kích thước để có thể so từng vị trí.

### 13.1. Chuyển nét mờ thành hai giá trị

Đầu vào có thể chứa mép chữ xám do cách vẽ font. Mã đặt:

~~~text
Giá trị ≥ 128 → 255
Giá trị < 128 → 0
~~~

Nếu đầu vào đã chỉ có 0/255 thì không đổi. Ngưỡng 128 này dùng trong chuẩn hóa ảnh ký tự/mẫu; nó khác ngưỡng Otsu tính cho toàn ảnh.

### 13.2. Cắt sát mực

Mã tìm x_min, x_max, y_min, y_max của các điểm còn mực và cắt bỏ nền thừa xung quanh. Nếu không còn mực thì trả bảng 48 × 48 toàn số 0.

### 13.3. Tính hệ số thu/phóng mà không làm méo chữ

Gọi w,h là rộng và cao ảnh sau khi cắt sát. Đích là 48 × 48, chừa lề p = 4 mỗi bên. Vùng bên trong còn:

~~~text
Rộng trong = 48 − 2p = 40
Cao trong  = 48 − 2p = 40

s = min(40/w;40/h)
w_mới = round(s × w)
h_mới = round(s × h)
~~~

s là tỷ lệ thay đổi kích thước. Dùng cùng một s cho cả chiều ngang và dọc giúp giữ hình dáng; nếu ép cả hai chiều độc lập, chữ hẹp có thể bị kéo bè.

Ví dụ chữ rộng 12, cao 30:

~~~text
s = min(40/12;40/30) = 1,333...
w_mới = round(12 × 1,333...) = 16
h_mới = round(30 × 1,333...) = 40
~~~

### 13.4. Đặt vào giữa bảng đích

~~~text
Lề trái = floor((48−w_mới)/2)
Lề trên = floor((48−h_mới)/2)
~~~

Ví dụ 16 × 40:

~~~text
Lề trái = (48−16)/2 = 16
Lề trên = (48−40)/2 = 4
~~~

Tạo bảng 48 × 48 toàn số 0 rồi đặt ảnh 16 × 40 vào vị trí này.

Pillow đổi cỡ bằng cách lấy giá trị điểm gần vị trí cần lấy nhất, gọi là nearest-neighbor. Cách này giữ hai giá trị 0/255, không lấy trung bình tạo thêm viền xám. Mã giới hạn chiều mới ít nhất 1 và không vượt phần trong.

**Đầu ra:** một bảng 48 × 48 có vị trí và kích thước tương đối thống nhất.

**Giới hạn:** nếu phân đoạn đã bỏ mất nét hoặc gộp hai chữ, bước đổi cỡ chỉ chuẩn hóa vùng sai đó; nó không tự biết cách khôi phục chữ đúng.


## 14. Bước 10: tính điểm giống mẫu và xếp hạng

**Đầu vào:** ảnh ký tự 48 × 48 và kho mẫu 48 × 48 đã tạo lúc mở ứng dụng.

**Chỗ mã:** build_template_index(), rank_templates(), pixel_similarity() trong template_matching.py.

**Cần làm gì:** thử xem hình ký tự đầu vào giống loại chữ nào nhất.

### 14.1. Đưa ảnh về bảng 0/1

Gọi Q là ảnh ký tự cần đọc, T là một ảnh mẫu. Chữ Q ở đây chỉ là tên bảng cần so, không có nghĩa bảng chứa ký tự “Q”.

~~~text
Điểm mực > 0 → 1
Điểm nền = 0 → 0
~~~

Sau đó so Q(y,x) và T(y,x) ở cùng vị trí.

### 14.2. Công thức Pixel Similarity

Pixel Similarity nghĩa là độ giống nhau theo từng điểm ảnh:

~~~text
d(y,x) = abs(Q(y,x) − T(y,x))

D = ∑ d(y,x), trên mọi hàng và cột

S(Q,T) = 1 − D/(W × H)
~~~

Giải thích từng ký hiệu:

- d(y,x) bằng 0 nếu hai điểm cùng là nền hoặc cùng là nét chữ.
- d(y,x) bằng 1 nếu một bên là nền, bên kia là nét chữ.
- D là số điểm khác nhau.
- W × H là tổng điểm được so; với 48 × 48 thì bằng 2.304.
- S là điểm giống nhau, từ 0 đến 1.

### 14.3. Tự tính bằng một bảng nhỏ

Để dễ đếm, dùng ví dụ 2 × 3 thay vì 48 × 48:

~~~text
Q:          T1:         abs(Q−T1):
0 1 0       0 1 0       0 0 0
1 1 1       1 0 1       0 1 0
~~~

Có một vị trí khác nhau:

~~~text
D = 1
Tổng điểm = 2 × 3 = 6
S(Q,T1) = 1 − 1/6 ≈ 0,8333
~~~

So tiếp với mẫu khác:

~~~text
Q:          T2:         abs(Q−T2):
0 1 0       1 1 0       1 0 0
1 1 1       1 0 1       0 1 0

D = 2
S(Q,T2) = 1 − 2/6 ≈ 0,6667
~~~

T1 giống hơn T2 vì 0,8333 > 0,6667.

Trong kích thước thật, nếu khác 230 trên 2.304 điểm:

~~~text
S = 1 − 230/2304 ≈ 0,9002
~~~

Mã NumPy đếm các điểm khác nhau của nhiều mẫu cùng lúc để giảm việc lặp Python. Đó là cách thực hiện nhanh cùng công thức, không phải thuật toán nhận dạng khác.

### 14.4. Một ký tự có nhiều font: chọn điểm nào?

Giả sử đang xét loại chữ A. Các mẫu A có thể cho điểm:

~~~text
A, Arial, cỡ 28:             0,88
A, Arial, cỡ 34:             0,92
A, Times New Roman, cỡ 34:   0,85
~~~

Điểm đại diện của lớp A là số **lớn nhất**, ở đây là 0,92:

~~~text
Điểm_lớp(c) = max S(Q,T)
              với T là tất cả mẫu có đáp án c
~~~

c là một ký tự như A hoặc B. Sau đó sắp các lớp giảm dần theo điểm. Giả sử:

~~~text
A: 0,92
R: 0,89
B: 0,87
~~~

Dự đoán ban đầu là A. Tên font lưu kèm là font của mẫu A đạt điểm tốt nhất, không phải kết luận đáng tin cậy rằng toàn bộ ảnh đầu vào dùng font đó.

Hàm xếp hạng có mặc định riêng top_k = 3, nhưng luồng recognize() hiện gọi với top_k = 20 để giữ tối đa 20 loại ký tự ứng viên cho các quy tắc sau. “Ứng viên” nghĩa là một đáp án có thể được cân nhắc.

### 14.5. Điểm cao có nghĩa gì?

Điểm cao nghĩa là ít vị trí khác nhau trên hai bảng đã căn chỉnh. Nó không bảo đảm đúng chữ:

- Hai chữ I và l có thể thật sự gần giống hình.
- Nếu có nhiều nền 0 ở cả hai ảnh, những điểm nền giống nhau cũng được cộng vào độ giống.
- Dấu câu sau khi phóng to có thể giống chữ lớn.
- Cắt sai vùng có thể làm ảnh đầu vào giống nhầm một mẫu khác.

Mã không có quy tắc chung “điểm thấp thì trả dấu ?”. Nó vẫn thường chọn một ký tự trong kho mẫu. Vì vậy người dùng cần kiểm tra văn bản.

### 14.6. Đoạn mã làm gì để đỡ tính lại?

build_template_index() chuyển kho mẫu thành các bảng đúng kích thước, giữ bảng đúng/sai của từng mẫu và nhóm vị trí mẫu theo ký tự. Trong một lần nhận dạng, danh sách này được chuẩn bị rồi dùng lại cho nhiều chữ của ảnh.

Nếu có K vùng ký tự, N ảnh mẫu và mỗi ảnh có W × H điểm, lượng so sánh cơ bản tỷ lệ với:

~~~text
K × N × W × H
~~~

Ví dụ K = 100, N = 2.000, W × H = 2.304 thì có quy mô khoảng 460,8 triệu phép so sánh vị trí, chưa tính các lần thử tách lại. NumPy xử lý theo khối; số này mô tả lượng công việc, không dùng để suy ra thời gian chạy chính xác.

## 15. Bước 11: thử tách vùng bị dính

**Đầu vào:** vùng ký tự sơ bộ và danh sách điểm so khớp ban đầu.

**Chỗ mã:** _split_attached_small_punctuation(), _candidate_projection_splits() và recognize() trong recognition.py.

**Cần làm gì:** sửa một số trường hợp một vùng chứa nhiều hơn một ký tự hoặc chứa dấu câu dính vào chữ.

### 15.1. Tách dấu câu nhỏ nằm chồng cột với chữ cuối từ

Có thể một dấu phẩy rời về mặt điểm mực nhưng nằm chồng cột với chữ trước nó. Khi cộng theo cột, hai phần bị lấy chung thành một vùng.

Mã chỉ thử cách này ở cuối từ hoặc cuối dòng. Nó tìm nhóm mực lớn nhất làm thân chữ, rồi tìm một nhóm nhỏ ở phía phải, gần/phía dưới đáy thân.

Các điều kiện gồm thân cao ít nhất 0,75 lần chiều cao vùng thường gặp, thân chiếm ít nhất 0,25 diện tích khung đang xét. Dấu nhỏ cần có ít nhất 3 điểm mực, không lớn quá 0,50 diện tích thân, không quá rộng/cao (giới hạn 0,55 và 0,65 lần chiều cao thường gặp), đồng thời nằm đúng phía phải và gần đáy.

Nếu hợp, mã tạo hai vùng mới: thân và dấu. Dấu không có dấu cách trước nó và được gắn cờ cần xem lại. Nếu không hợp, giữ nguyên vùng.

### 15.2. Khi nào mới thử cắt một vùng rộng?

Mã dùng điểm ban đầu để nhận biết vùng có vẻ khó. Các khái niệm tại đây là:

~~~text
Vùng tương đối rộng: w ≥ 1,05h

Ứng viên hẹp nhưng đáng nghi:
điểm cao nhất < 0,94 và w ≥ 0,65h
~~~

Phần quyết định còn tránh cắt một dấu nháy kép nhỏ đúng hình, đồng thời xem trường hợp một vùng cao bị nhận nhầm thành dấu nháy kép.

Điều kiện thông thường để vào bước thử cắt là điểm cao nhất < 0,92 và vùng thuộc một trong các dạng rộng/đáng nghi. Các trường hợp dấu nháy có nhánh xử lý bổ sung trong mã.

Những điều kiện này khác với công thức w > 1,35 × max(h,q) dùng để gắn cờ rộng ở phần 11. Một công thức quyết định thử cắt, công thức kia quyết định cờ hiển thị; chúng phục vụ hai việc khác nhau.

### 15.3. Tìm vị trí cột ít mực

Tính lại số điểm mực theo từng cột P(x). Đường cắt thường hợp lý hơn ở cột có ít nét.

Chỉ tìm trong khoảng từ 20% đến 80% chiều rộng để tránh cắt một mẩu cực nhỏ ở mép. Với một vị trí cắt c:

~~~text
L = giá trị P lớn nhất ở phía trái c
R = giá trị P lớn nhất ở phía phải c
m = min(L,R)
~~~

Một cột được xem là vùng thưa mực khi:

~~~text
P(c) ≤ max(1; round(0,22 × m))
~~~

Nếu không có cột đạt, mã thử tiêu chí rộng hơn với 0,60 × m và giữ tối đa năm vị trí ít mực nhất. Sau đó thử thêm các cột quanh vùng đã tìm, với bán kính khoảng 8% chiều rộng.

“Đáy hình chiếu” hay “valley” trong mã chỉ có nghĩa vị trí mà số điểm mực theo cột thấp hơn những vùng xung quanh.

Mỗi nửa sau cắt cần còn mực, rộng ít nhất 2 và có ít nhất 6 điểm mực. Sau đó cắt sát mỗi nửa và đem so mẫu lại.

### 15.4. Quyết định nhận hay bỏ đường cắt

Gọi S0 là điểm tốt nhất trước khi cắt, SL là điểm tốt nhất nửa trái, SR là điểm tốt nhất nửa phải:

~~~text
S_mới = (SL + SR)/2
Mức tăng = S_mới − S0
~~~

Mã chọn đường cắt cho S_mới tốt nhất, nhưng chỉ nhận nếu thỏa:

| Loại vùng theo w ≥ 1,05h | Điểm mỗi nửa tối thiểu | Mức tăng tối thiểu |
|---|---:|---:|
| Rộng | 0,72 | 0,07 |
| Chưa đạt tỷ lệ rộng đó | 0,95 | 0,05 |

Ví dụ vùng rộng có S0 = 0,83; sau cắt SL = 0,95 và SR = 0,97:

~~~text
S_mới = (0,95+0,97)/2 = 0,96
Mức tăng = 0,96−0,83 = 0,13
~~~

Hai nửa đều qua 0,72 và mức tăng 0,13 qua 0,07, nên đường cắt có thể được nhận nếu nó là phương án tốt nhất.

Nếu S0 = 0,91 và hai nửa là 0,93; 0,94:

~~~text
S_mới = 0,935
Mức tăng = 0,025 < 0,07
~~~

Mã bỏ cách cắt này.

**Đầu ra:** giữ nguyên một vùng, hoặc thay bằng hai vùng cùng với kết quả so mẫu mới.

**Giới hạn:** điểm cao hơn không chứng minh chắc chắn đường cắt đúng. Mã chỉ thử một số đường chia hai phần; đây không phải bộ tách mọi dạng chữ dính.

## 16. Bước 12: xét vị trí để phân biệt chữ và dấu

**Đầu vào:** các vùng chữ đã so mẫu và danh sách tối đa 20 đáp án cho mỗi vùng.

**Mục tiêu:** tận dụng chiều cao, đường chân chữ và vị trí lân cận để xử lý hình gần giống nhau.

**Chỗ mã:** các hàm _prefer_... và _merge_adjacent_quote_strokes() trong recognition.py.

Các quy tắc chạy nối tiếp. Một đáp án điểm pixel cao nhất có thể bị đổi nếu một đáp án gần điểm hơn phù hợp hình dạng/vị trí. “Gần điểm” nghĩa là hiệu số điểm không vượt một mức cụ thể, không phải phần trăm độ tin cậy.

### 16.1. Ước lượng chiều cao và đường chân chữ

Sau phân loại sơ bộ, mã lấy đáy các vùng được đoán là chữ/số, loại i và j khi ước lượng đáy:

~~~text
đáy_i = y_i + h_i
b = median(các đáy_i)
~~~

Chỉ đặt b nếu có ít nhất bốn vùng đủ điều kiện. Nếu quá ít thì b để trống và những quy tắc cần b không chạy.

Chiều cao chữ/số thường gặp:

~~~text
q = median(các chiều cao được đoán là chữ/số)
~~~

Lưu ý b và q ở bước này phụ thuộc cả vào dự đoán sơ bộ, nên dự đoán sai có thể ảnh hưởng quy tắc phía sau.

### 16.2. Chữ I hoa, l thường, i thường và số 1

Ba hình I hoa, l thường, số 1 có thể giống một nét đứng. Mã xét vùng có đứng giữa một từ không, có ở đầu câu không, và các điểm ứng viên có gần nhau không.

Một số mức chênh trong mã:

- Ứng viên I, i hoặc l thường được xem là gần nếu lệch tối đa 0,045 so với điểm cao nhất.
- Ở giữa từ, chữ thường có thể được chọn thay I/1/ký hiệu đứng nếu lệch tối đa 0,035.
- Nếu đang ưu tiên đầu câu/đầu tiêu đề, biến thể chữ hoa có thể được chọn khi lệch tối đa 0,025.

Ví dụ kết quả pixel là l: 0,95; I: 0,93. Hiệu 0,02 ≤ 0,045. Nếu vị trí được coi là đầu câu, quy tắc có thể chọn I.

Đầu câu được suy từ đầu dòng đầu tiên, dấu kết câu trước đó và một phép đoán dòng tiêu đề ngắn. Mã không thực sự hiểu nghĩa đoạn văn. Vì thế ảnh chỉ chứa i có thể bị ưu tiên thành I nếu điểm gần nhau. CSV hiện có lỗi i thành I; để kết luận đường xử lý chính xác của từng ảnh cần xem cả điểm ứng viên, không chỉ chuỗi trong CSV.

### 16.3. Phân biệt i và j bằng phần thòng xuống

~~~text
đáy = y+h

Nếu đáy > b+1: nghiêng về j
Nếu đáy ≤ b+1: nghiêng về i
~~~

Quy tắc chỉ chọn trong nhóm ứng viên lệch điểm không quá 0,10 và đúng điều kiện loại ký tự đang xét. Lý do là j thường có nét xuống thấp hơn đường chân chữ; i thường không.

Ví dụ b = 100, đáy = 105 thì vượt b+1 = 101, nên j hợp vị trí hơn nếu điểm đủ gần.

### 16.4. Phân biệt dấu gạch ngang và gạch dưới

Đầu tiên vùng phải mảnh và nằm ngang:

~~~text
h ≤ 0,25q
w ≥ 1,8h
tâm_y = y+h/2
~~~

Nếu tâm_y > b+0,08q thì nghiêng về dấu gạch dưới _. Nếu cao hơn, dùng tỷ lệ w/q để phân độ dài:

~~~text
w/q ≥ 1,15       → gạch dài —
0,60 ≤ w/q <1,15 → gạch vừa –
w/q < 0,60       → gạch ngắn -
~~~

Chỉ đổi nếu ứng viên mong muốn lệch không quá 0,08 điểm.

Ví dụ q = 20, w = 16, h = 2 thì h ≤ 5, w ≥ 3,6. Nếu ở giữa thân chữ, w/q = 0,8 nên nghiêng về gạch vừa.

### 16.5. Phân biệt dấu phẩy, dấu nháy và dấu chấm

Hai dấu , và ' có thể gần giống nếu cắt sát rồi phóng to. Vị trí cao/thấp giúp phân biệt:

- Nếu ảnh nhỏ, tâm gần đáy b, dấu phẩy hợp hơn.
- Nếu ảnh nhỏ nằm cao hơn nhiều so với b, dấu nháy hợp hơn.
- Cụm rất ngắn và nhỏ gần b có thể là dấu chấm.

Các ngưỡng chủ yếu:

| Tình huống | Điều kiện chính | Chênh điểm tối đa |
|---|---|---:|
| Đổi nháy thành phẩy | h ≤ 0,65q; tâm_y ≥ b−0,15q | 0,08 |
| Đổi phẩy thành nháy | h ≤ 0,65q; tâm_y < b−0,35q | 0,08 |
| Nhận dấu chấm nhỏ | h ≤ 0,36q; w ≤ 0,55q; tâm_y ≥ b−0,30q | 0,15 |
| Nhận phẩy nhỏ | không vào nhánh chấm; h ≤ 0,62q; w ≤ 0,60q; đáy ≥ b−0,08q | 0,15 |

Ví dụ q = 20, b = 100, vùng rộng 3, cao 4, tâm_y = 99: vùng đủ nhỏ và ở thấp nên có khả năng là dấu chấm.

### 16.6. Dấu nháy bị nhầm với nét chữ cao

Nếu một vùng nằm giữa từ, cao ít nhất 0,78q và rộng không quá 0,70q nhưng bị đọc thành nháy hoặc ký hiệu đứng, mã có thể chọn chữ thường có điểm lệch tối đa 0,12.

Lý do: dấu nháy thật thường ngắn, một nét cao gần toàn thân chữ nằm giữa từ có thể là l/f hoặc chữ hẹp khác. Quy tắc vẫn có thể sai với văn bản đặc biệt.

### 16.7. Hai nét nháy thành dấu nháy kép

Trước khi chấm điểm từng vùng trong dòng, mã có thể ghép hai nét nhỏ ở cạnh nhau. Nó so chiều cao gần bằng nhau, vị trí y gần nhau, cả hai không quá lớn và khoảng cách ngang nhỏ.

Ví dụ hai nét đều cao 5, rộng 2, nằm cùng hàng, chỉ cách 1 điểm có thể là hai nét của một dấu nháy kép. Nếu giữ riêng, chúng có thể bị đọc thành hai dấu nháy đơn. Sau khi dự đoán, bước ghép chuỗi còn một phép kiểm tra tương tự để gộp các cặp nháy phù hợp.

### 16.8. Dấu hai chấm/chấm phẩy trước đầu câu

Nếu vùng bị đoán là : hoặc ;, trước nó là chữ/số và sau nó có khoảng cách cùng ứng viên chữ hoa đạt điểm ít nhất 0,85, mã cân nhắc đổi thành dấu chấm nếu điểm dấu chấm lệch không quá 0,20.

Có thêm một nhánh xử lý hình học cho dấu nằm sát sau y. Quy tắc giả định đây có thể là kết câu, nên vẫn có thể đọc sai một dấu hai chấm thật.

### 16.9. Đuôi phẩy chạm nét thòng của chữ trước

Sau y/g/p/q/j, một đuôi phẩy có thể dính sát vào nét kéo xuống và bị nhận thành j, ;, | hoặc }. Mã xét độ rộng nhỏ, độ cao đủ lớn, vị trí sát chữ trước và thấp hơn b. Nếu thỏa vị trí cuối từ, nó đổi thành dấu phẩy.

Trong nhánh đổi này, điểm/font mẫu đang giữ có thể được **kế thừa** từ đáp án trước khi đổi. Vì vậy cột điểm trong giao diện không phải lúc nào cũng là điểm so trực tiếp với mẫu của đúng dấu cuối cùng sau mọi quy tắc.

### 16.10. Dấu ngoặc lẻ có thể là chữ bị nhầm

Nếu một vùng trong từ bị đọc là ngoặc mà không tìm được cặp ngoặc tương ứng ở vị trí phù hợp, mã xem đáp án chữ/số gần nhất. Có thể đổi nếu chênh tối đa 0,12. Với nét cao, còn ưu tiên nhóm chữ có thân cao khi điểm gần nhau trong phạm vi 0,03.

**Đầu ra của toàn bước:** đáp án cuối cùng cho từng vùng trước khi ghép chuỗi.

**Điều cần hiểu:** đây là một tập quy tắc hỗ trợ. Không có từ điển kiểm tra từ tiếng Anh, không có mô hình đọc hiểu, không bảo đảm sửa đúng mọi trường hợp. Một số quy tắc còn có thể làm đáp án ban đầu đúng trở thành sai.

## 17. Bước 13 và 14: ghép văn bản, vẽ khung và trả kết quả

### 17.1. Ghép đáp án thành dòng

**Đầu vào:** mỗi vùng đã có một ký tự dự đoán và cờ dấu cách trước nó.

**Chỗ mã:** reconstruct_text() trong reconstruction.py.

Mã xử lý các vùng từ trái sang phải. Nếu vùng sau có cờ space_before và không vướng quy tắc dấu câu, thêm một khoảng trắng trước khi thêm ký tự đó.

Ví dụ:

~~~text
Ký tự:            C     a     t     d     o     g
Dấu cách trước:  sai   sai   sai   đúng  sai   sai
Kết quả:         Cat dog
~~~

Không tự thêm dấu cách trước . , ; : ! ? % và một số dấu đóng ngoặc. Không tự thêm dấu cách ngay sau dấu mở ngoặc. Dấu nháy được xét xem là nháy mở hay nháy đóng. Dấu nháy đơn giữa hai chữ/số có thể được xem là phần nối từ, như trong don't.

Ví dụ nếu cờ khoảng cách đặt sai trước dấu phẩy, quy tắc dấu câu có thể vẫn tạo “Hello, world” thay vì “Hello , world”. Nhưng nếu khoảng cách giữa hai từ thường bị đoán sai, mã không có từ điển để khôi phục chắc chắn.

Mỗi vùng dòng tạo một chuỗi. Các chuỗi được nối bằng ký tự xuống dòng:

~~~text
Dòng 1: ABC DEF 123
Dòng 2: XYZ 789

Văn bản:
ABC DEF 123
XYZ 789
~~~

Nếu một vị trí cần đáp án nhưng không có trong bảng dự đoán, hàm có ký tự dự phòng �. Đây là dấu thay thế dữ liệu thiếu; không phải quy tắc chung tự phát hiện mọi chữ OCR sai.

### 17.2. Vẽ khung lên ảnh gốc

**Chỗ mã:** draw_character_boxes() trong segmentation.py.

Mỗi vùng có khung (x,y,w,h). Mã vẽ hình chữ nhật từ (x,y) đến (x+w−1,y+h−1).

- Khung xanh: cờ uncertain của vùng đang là sai.
- Khung cam: cờ uncertain đang là đúng.

uncertain có nghĩa là “vùng cần xem lại”. Nó được đặt cho những vùng rộng theo quy tắc và một số vùng tạo ra khi thử tách.

**Khung xanh không bảo đảm đọc đúng.** Một chữ i bị đọc thành I có thể vẫn có khung xanh vì vùng không rộng bất thường. Mã cũng không dùng mọi điểm match thấp để tự động tô cam.

### 17.3. Đo thời gian

recognize() lấy mốc trước khi chạy xử lý và mốc khi hoàn thành:

~~~text
thời_gian_giây = mốc_kết_thúc − mốc_bắt_đầu
thời_gian_ms = thời_gian_giây × 1.000
~~~

ms là mili giây; 1.000 ms = 1 giây. Ví dụ 0,25 giây tương ứng 250 ms.

Đồng hồ này nằm trong hàm nhận dạng. Nó không đo toàn bộ thời gian người dùng chờ: việc đọc tệp, truyền Base64, tạo kho mẫu lúc mở server và hiển thị trên trình duyệt nằm ngoài toàn bộ hoặc một phần phép đo đó.

### 17.4. Dữ liệu trả về trang web

Máy chủ gửi JSON gồm:

| Tên trường | Ý nghĩa |
|---|---|
| filename | Tên tệp ảnh. |
| text | Chuỗi văn bản cuối cùng. |
| processing_ms | Thời gian nhận dạng tính bằng mili giây. |
| character_count | Số vùng đã gán ký tự; không gồm những dấu cách/xuống dòng được thêm khi ghép. |
| annotated_png | Ảnh PNG đã vẽ khung, biểu diễn dạng Base64. |
| characters | Danh sách dòng, ký tự, khung, font, điểm, cờ xem lại của từng vùng. |

Bên trong OCRResult.steps còn giữ ảnh gốc, ảnh xám sau xử lý gạch đỏ, ảnh nhị phân, ảnh sau lọc và ngưỡng Otsu. **Giao diện hiện tại không trả ra hoặc hiển thị mọi ảnh trung gian này**; giao diện hiển thị ảnh đầu vào và ảnh đã vẽ khung.

Trình duyệt đọc JSON, điền text vào ô kết quả, đặt ảnh có khung vào màn hình và tạo các hàng chi tiết. Nút sao chép đưa chuỗi vào bộ nhớ sao chép; nút tải tạo tệp recognized.txt.

## 18. NCC: phép so sánh bổ sung trong mã

NCC là tên viết tắt của Normalized Cross-Correlation, có thể hiểu là đo xem hai bảng số thay đổi cùng nhau đến mức nào sau khi trừ trung bình và điều chỉnh độ lớn.

**Vị trí:** normalized_cross_correlation() trong template_matching.py.

**Nó chạy khi nào:** script đánh giá chọn matching=ncc. API web hiện đặt matching_method="pixel", nên người dùng bấm nhận dạng thông thường không dùng NCC.

### 18.1. Công thức và ý nghĩa

Trải bảng ảnh thành một dãy q1,q2,…,qn; mẫu thành t1,t2,…,tn. Trải bảng nghĩa là đọc các hàng nối tiếp nhau thành một dãy, không làm thay đổi dữ liệu.

~~~text
q_trung_bình = (q1+q2+…+qn)/n
t_trung_bình = (t1+t2+…+tn)/n

ai = qi − q_trung_bình
bi = ti − t_trung_bình

rho = ∑(ai × bi) / sqrt[∑ai² × ∑bi²]
~~~

sqrt là căn bậc hai: sqrt(9) = 3. rho đọc là “rô”, là tên cho điểm tương quan.

- Tử số lớn khi các vị trí cao/thấp so với trung bình trùng hướng nhau.
- Mẫu số giúp điều chỉnh theo độ lớn của hai dãy đã trừ trung bình.
- Điểm rho nằm trong khoảng −1 đến 1.
- Mã đổi điểm dùng hiển thị/xếp hạng về khoảng 0 đến 1 bằng (rho+1)/2.

### 18.2. Ví dụ số

~~~text
q = [0,1,1,0]       trung bình = 0,50
t = [0,1,0,0]       trung bình = 0,25

a = [−0,50; 0,50; 0,50; −0,50]
b = [−0,25; 0,75; −0,25; −0,25]

∑ai×bi = 0,125+0,375−0,125+0,125 = 0,50
∑ai²   = 1,00
∑bi²   = 0,75

rho = 0,50 / sqrt(1,00×0,75) ≈ 0,57735
Điểm đổi về [0,1] = (0,57735+1)/2 ≈ 0,78868
~~~

### 18.3. Nếu mẫu số bằng 0?

Nếu một dãy toàn 0 hoặc toàn 1 thì sau trừ trung bình mọi giá trị bằng 0; không được chia cho 0.

Mã có nhánh bảo vệ: nếu mẫu số quá nhỏ thì trả 1 khi hai bảng nhị phân giống nhau hoàn toàn, ngược lại trả 0 làm điểm rho. Với rho = 0, điểm sau đổi miền là 0,5. Đây là cách mã xử lý trường hợp đặc biệt, không phải kết quả công thức khi chia cho 0.

NCC và Pixel Similarity là hai phép chấm điểm do bản triển khai cung cấp; không nên gán các công thức cụ thể này cho bài báo tham khảo vì bài báo không nêu rõ metric.


## 19. Dữ liệu đánh giá và cách tính mọi chỉ số

### 19.1. Vì sao phải có đáp án đúng?

Kết quả OCR nhìn có vẻ hợp lý không có nghĩa là đúng. Muốn đo sai bao nhiêu, cần biết văn bản thật trong ảnh.

Tên tiếng Anh ground truth nghĩa là **đáp án đúng dùng để đối chiếu**. Ví dụ ảnh có “Classical OCR 2026” thì tệp TXT đi kèm ghi đúng chuỗi đó, bao gồm khoảng trắng.

evaluation.py nhận hai chuỗi:

~~~text
reference: đáp án đúng
hypothesis: văn bản OCR đọc ra
~~~

Hai từ tiếng Anh chỉ là tên hai đầu vào này.

### 19.2. Bộ ảnh đang có được tạo ra thế nào?

scripts/generate_test_data.py dùng Pillow vẽ chữ màu đen trên nền trắng bằng các font tìm được trên máy.

Tám tình huống cho mỗi font:

| Tên tình huống trong mã | Nội dung và mục đích |
|---|---|
| single_i | Chỉ có i; xem có giữ chấm và đọc đúng chữ thường không. |
| single_j | Chỉ có j; xem nét thòng/dấu chấm được xử lý ra sao. |
| confusable | “O0 B8 I1 l”; thử các ký tự dễ giống nhau. |
| word | “Matching”; một từ. |
| one_line | “Classical OCR 2026”; một dòng có khoảng trắng và số. |
| multiple_lines | “Pixel Matching” và “Uses NumPy 123”; thử nhiều dòng. |
| noisy_line | “Noise Filter 456”; thêm một ít chấm đen/trắng ngẫu nhiên. |
| punctuation | Câu dài có chấm, phẩy, hỏi, than, ngoặc, nháy và gạch ngang. |

Cỡ chữ dùng khi tạo dữ liệu là:

~~~text
28 + (thứ_tự_tình_huống chia_lấy_dư 3) × 5
~~~

Thứ tự bắt đầu từ 0 nên cỡ lặp 28,33,38. “Chia lấy dư” là lấy phần dư sau phép chia nguyên: 4 chia 3 dư 1 nên cỡ cho chỉ số 4 là 28+1×5 = 33.

Chỉ tình huống noisy_line được thêm chấm. Nếu ảnh có H × W điểm:

~~~text
Số lượt chọn vị trí nhiễu = max(1; floor(H×W×0,001))
~~~

Ví dụ ảnh 200 × 100 = 20.000 điểm thì chọn khoảng 20 vị trí để đặt ngẫu nhiên 0 hoặc 255. Có thể chọn trùng vị trí hoặc giá trị trùng giá trị cũ, nên số điểm thực sự thay đổi không nhất thiết bằng đúng 20.

Mã đặt số khởi tạo cho bộ sinh ngẫu nhiên, giúp có thể tạo lại kiểu nhiễu tương tự với cùng môi trường và cài đặt. Đây là cách tạo ảnh thử có kiểm soát, chưa giống mọi dạng ảnh chụp thật.

Mỗi ảnh có tệp TXT đáp án. manifest.csv là danh sách chỉ ra tên ảnh, font và tên tệp đáp án tương ứng. CSV là bảng văn bản, mỗi dòng lưu một bản ghi và các cột được phân cách.

### 19.3. Đếm lỗi bằng khoảng cách chỉnh sửa

Không thể chỉ so ký tự thứ 1 với thứ 1, thứ 2 với thứ 2… vì một dấu bị thiếu sẽ làm lệch tất cả vị trí sau nó. Dự án dùng **khoảng cách Levenshtein**, nghĩa là số thao tác ít nhất để biến một chuỗi thành chuỗi kia.

Mỗi thao tác có giá 1:

- Thay một ký tự: CAT thành CUT bằng thay A thành U.
- Xóa một ký tự.
- Chèn thêm một ký tự.

Khoảng trắng và xuống dòng cũng là ký tự. Mất một dấu cách vẫn tính lỗi.

### 19.4. Công thức tìm số chỉnh sửa ít nhất

Gọi C(i,j) là số lỗi ít nhất khi so i ký tự đầu của đáp án với j ký tự đầu của OCR.

Trường hợp đầu:

~~~text
C(0,0) = 0
C(i,0) = i
C(0,j) = j
~~~

Chuỗi rỗng thành chuỗi có i ký tự cần i lần chèn/xóa.

Tại vị trí i,j:

~~~text
cost = 0 nếu hai ký tự đang xét giống nhau
cost = 1 nếu chúng khác nhau

C(i,j) = min(
    C(i−1,j) + 1,
    C(i,j−1) + 1,
    C(i−1,j−1) + cost
)
~~~

Ba lựa chọn lần lượt tương ứng bỏ một ký tự phía đáp án, bỏ một ký tự phía OCR hoặc ghép hai ký tự hiện tại với giá thay thế 0/1. Mã chọn cách có chi phí nhỏ nhất. Đọc kết quả tại ô cuối bảng.

Ví dụ đáp án CAT, OCR CUT:

~~~text
             OCR
          rỗng  C  U  T
Đáp án rỗng  0  1  2  3
       C     1  0  1  2
       A     2  1  1  2
       T     3  2  2  1
~~~

Ô cuối bằng 1: chỉ cần thay A/U. Hàm mã chỉ giữ hàng trước và hàng hiện tại để giảm bộ nhớ, nhưng phép tính tương đương bảng đầy đủ trên.

### 19.5. CER: tỷ lệ lỗi ký tự

CER là Character Error Rate: tỷ lệ lỗi ký tự.

~~~text
D = khoảng cách chỉnh sửa của hai chuỗi
L = số ký tự đáp án

CER = D / max(1,L)
~~~

max(1,L) bảo vệ trường hợp đáp án rỗng, tránh chia cho 0.

Ví dụ CAT/CUT có D = 1, L = 3:

~~~text
CER = 1/3 ≈ 0,3333 = 33,33%
~~~

Trong chuỗi dài 100 ký tự, có 4 chỉnh sửa thì CER = 4%. CER thấp hơn là tốt hơn.

Nếu OCR chèn quá nhiều ký tự, D có thể lớn hơn L, nên CER có thể vượt 100%. Nó không phải xác suất luôn bị chặn trong khoảng 0–100%.

### 19.6. “Độ chính xác ký tự” trong dự án được định nghĩa thế nào?

Hàm evaluate_text() dùng:

~~~text
character_accuracy = max(0; 1−CER)
~~~

Ví dụ CER = 4% thì độ chính xác theo định nghĩa này là 96%. Nếu CER vượt 100% thì độ chính xác được chặn ở 0.

Đây là chỉ số suy từ khoảng cách chỉnh sửa. Không nên mô tả nó như một phép đếm ký tự khớp đúng từng vị trí tuyệt đối khi chuỗi đã có chèn/xóa.

### 19.7. Exact match: chuỗi đúng hoàn toàn

~~~text
exact_match = đúng nếu đáp_án == OCR
exact_match = sai nếu còn bất kỳ khác biệt nào
~~~

Dấu cách, xuống dòng, hoa/thường, dấu câu đều phải giống.

Ví dụ “Cat dog” và “Catdog” không khớp hoàn toàn dù mọi chữ cái đều đúng. Chỉ số này phản ánh ảnh nào có thể dùng nguyên kết quả mà không sửa một ký tự nào.

### 19.8. Hai cách gộp CER trên nhiều ảnh

Gọi Di là số chỉnh sửa của ảnh i, Li là số ký tự đáp án ảnh i, n là số ảnh.

**CER gộp theo tổng ký tự**, còn gọi weighted/aggregate CER trong script:

~~~text
CER_gộp = (D1+D2+…+Dn) / max(1;L1+L2+…+Ln)
~~~

Ảnh dài có ảnh hưởng lớn hơn vì chứa nhiều ký tự. Script in độ chính xác gộp bằng 1−CER_gộp trực tiếp; nó không chặn ở 0 tại dòng tổng hợp như cách evaluate_text() chặn chỉ số từng ảnh. Với số liệu hiện có, CER nhỏ hơn 1 nên khác biệt này không ảnh hưởng kết quả báo cáo.

**CER trung bình theo ảnh**, còn gọi macro CER:

~~~text
CER_trung_bình_ảnh = [CER1+CER2+…+CERn] / n
~~~

Mỗi ảnh có trọng số bằng nhau.

Ví dụ:

~~~text
Ảnh 1: 1 ký tự, sai 1 → CER = 100%
Ảnh 2: 100 ký tự, sai 1 → CER = 1%

CER_gộp = (1+1)/(1+100) ≈ 1,98%
CER_trung_bình_ảnh = (100%+1%)/2 = 50,5%
~~~

Hai con số cùng đúng nhưng đo hai cách phân bố lỗi khác nhau. Vì thế tài liệu/báo cáo cần nói rõ dùng cách nào.

### 19.9. Số liệu đang được lưu trong evaluation_pixel.csv

Đây là số tổng hợp từ CSV hiện có, không phải kết quả chạy lại ứng dụng trong lần viết tài liệu này:

| Chỉ số | Giá trị |
|---|---:|
| Số ảnh | 32 |
| Số font ảnh | 4 |
| Tổng ký tự đáp án | 688 |
| Tổng số chỉnh sửa ít nhất | 34 |
| CER gộp | 34/688 ≈ 4,9419% |
| Độ chính xác ký tự gộp | 1−34/688 ≈ 95,0581% |
| CER trung bình theo ảnh | ≈ 16,2808% |
| Ảnh khớp hoàn toàn | 15/32 ≈ 46,875% |

Làm tròn báo cáo là độ chính xác 95,1%, CER gộp 4,9% và CER trung bình ảnh 16,3%.

Theo từng font, mỗi font có 8 ảnh và 172 ký tự đáp án:

| Font | Số chỉnh sửa | Độ chính xác ký tự gộp trong font |
|---|---:|---:|
| Calibri | 6 | ≈ 96,5% |
| Verdana | 8 | ≈ 95,3% |
| Arial | 7 | ≈ 95,9% |
| Times New Roman | 13 | ≈ 92,4% |

Tại sao độ chính xác 95,1% mà chỉ 15/32 ảnh đúng hoàn toàn? Một ảnh dài 89 ký tự chỉ sai 1–4 ký tự vẫn có độ chính xác cao, nhưng exact match của cả ảnh đã bằng sai.

Bốn ảnh chỉ chứa i đều có kết quả I trong CSV. Mỗi ảnh một ký tự bị sai có CER 100%, góp phần làm CER trung bình từng ảnh cao hơn nhiều CER gộp.

Những lỗi khác có trong CSV:

- Dấu ! trong “world!” bị đọc thành l.
- Một số I/1/l bị lẫn nhau.
- Với Times New Roman, “Classical OCR 2026” thành “ClassicalOCR2026”.
- Có chuỗi nhiều dòng đọc “123” thành “l23”.

### 19.10. Dữ liệu này chứng minh được đến đâu?

Cột template_fonts cho biết kho mẫu dùng Calibri, Verdana, Arial và Times New Roman. Bốn font tạo ảnh test cũng thuộc bốn font này.

Vì vậy đây là phép thử **font đã có ảnh mẫu**, tiếng Anh thường gọi in-bank. Nó đo hoạt động trong phạm vi font đã được đưa vào kho; chưa đo nhận dạng font hoàn toàn mới.

Ảnh được vẽ bằng máy trên nền trắng nên chưa có đủ biến dạng của ảnh chụp: bóng, cong giấy, nghiêng phối cảnh, nhòe do tay rung, nén nhiều hoặc nền phức tạp. Không nên dùng riêng số 95,1% để khẳng định nhận dạng chính xác 95,1% trên mọi ảnh thực tế.

### 19.11. Chỉ số số lượng vùng có trong script

Script còn đếm:

~~~text
N_đúng = số ký tự đáp án không tính dấu cách/xuống dòng
N_cắt = số vùng mà bộ phân đoạn tạo ra

Điểm_số_lượng = max(0; 1−abs(N_đúng−N_cắt)/max(1,N_đúng))
~~~

Nếu đáp án có 10 chữ và cắt ra 9 vùng thì điểm = 1−1/10 = 0,9.

Chỉ số này chỉ kiểm tra **số lượng**. Có đúng 10 vùng không bảo đảm ranh giới từng vùng đúng; một chỗ gộp hai chữ và một chỗ chẻ đôi chữ khác có thể bù số lượng cho nhau.

### 19.12. Muốn tự chạy phép đo thì dùng gì?

Khi môi trường đã được cài như README và bộ ảnh hiện có đủ tệp:

~~~powershell
python scripts/run_evaluation.py --matching pixel --output evaluation_pixel_new.csv
python scripts/run_evaluation.py --matching ncc --output evaluation_ncc_new.csv
~~~

Dùng tên đầu ra mới để giữ kết quả cũ tiện đối chiếu.

Để tạo kho mẫu chỉ từ Calibri/Verdana và kiểm tra trên bộ ảnh hiện có:

~~~powershell
python scripts/run_evaluation.py --matching pixel --train-font Calibri --train-font Verdana --output evaluation_two_fonts_new.csv
~~~

Lệnh này không biến toàn bộ dữ liệu thành ảnh font chưa gặp: Calibri/Verdana vẫn có mẫu, còn Arial/Times New Roman mới là nhóm font không nằm trong kho hai font đó. Khi phân tích phải tách các nhóm để kết luận đúng.

Không so hai tệp CSV từ hai thời điểm khác nhau rồi quy toàn bộ chênh lệch cho Pixel/NCC nếu mã, dữ liệu hoặc kho mẫu đã thay đổi. Phép so sánh cần giữ các điều kiện khác giống nhau.

## 20. Sơ đồ mã nguồn, cách chạy và tài liệu tham khảo

### 20.1. Các thành phần phối hợp như thế nào?

~~~text
Trình duyệt
web/index.html
  │
  │  Gửi tệp ảnh đã chuyển thành chuỗi
  ▼
app.py — máy chủ HTTP trên máy của người dùng
  │
  ├─ mở chương trình: tìm font → tạo kho mẫu
  │
  └─ nhận ảnh: gọi recognize()
                  │
                  ├─ preprocessing.py: đổi xám, gạch đỏ, Otsu, lọc cụm mực
                  ├─ segmentation.py: dòng, vùng chữ, khoảng cách
                  ├─ template_matching.py: tính điểm với kho mẫu
                  ├─ recognition.py: thử tách, áp dụng quy tắc
                  ├─ reconstruction.py: ghép chuỗi
                  └─ segmentation.py: vẽ khung
  │
  ▼
Kết quả JSON → trình duyệt hiện ảnh khung, văn bản và bảng chi tiết
~~~

evaluation.py được dùng khi so kết quả với đáp án trong quá trình đánh giá. Ứng dụng nhận ảnh bình thường không có sẵn đáp án nên không tự tính được độ chính xác cho ảnh người dùng vừa tải lên.

### 20.2. Mỗi tệp có vai trò gì?

| Tệp/thư mục | Cách hiểu |
|---|---|
| app.py | Cổng vào ứng dụng: tạo kho mẫu, mở server, nhận yêu cầu và trả kết quả. |
| web/index.html | Nội dung, kiểu hiển thị và thao tác của trang web. |
| preprocessing.py | Những việc biến đổi ảnh trước khi tìm vị trí chữ. |
| segmentation.py | Cắt ảnh thành dòng/vùng chữ, lưu khung và vẽ khung. |
| template_generator.py | Vẽ mẫu từ font và đưa ảnh ký tự về kích thước thống nhất. |
| template_matching.py | Đếm pixel khác nhau, tính NCC và xếp đáp án theo điểm. |
| recognition.py | Điều phối các bước, sửa một số vùng dính và trường hợp dễ nhầm. |
| reconstruction.py | Ghép đáp án đơn lẻ thành câu/dòng có dấu cách. |
| evaluation.py | So chuỗi OCR với đáp án và tính số lỗi. |
| scripts/generate_test_data.py | Tạo ảnh tổng hợp và đáp án TXT. |
| scripts/generate_templates.py | Tạo/lưu kho mẫu ra tệp khi cần; app hiện tạo trong bộ nhớ. |
| scripts/run_evaluation.py | Lần lượt nhận dạng bộ ảnh có đáp án rồi ghi chỉ số ra CSV. |
| tests/ | Các tệp kiểm tra hành vi của thành phần mã. |
| sample_images/ | Ảnh minh họa, ảnh đo, đáp án và bảng danh sách. |
| docs/ | Tài liệu giải thích phương pháp và báo cáo. |

Các tệp Python xử lý OCR nằm trong src/classical_ocr/. “Hàm” là một nhóm lệnh được đặt tên để gọi lại, như binarize() là hàm làm bước ngưỡng.

### 20.3. Các thư viện được dùng để làm gì?

| Tên | Vai trò cụ thể |
|---|---|
| Python | Ngôn ngữ dùng viết máy chủ và thuật toán. |
| NumPy | Lưu/tính toán bảng số: cộng hàng/cột, trung vị, đếm điểm khác nhau. |
| OpenCV | Đọc/giải mã ảnh, chuyển màu, ngưỡng Otsu, tìm cụm mực, lấp vùng gạch đỏ, vẽ khung và tạo PNG. |
| Pillow | Vẽ chữ từ font và đổi cỡ ảnh ký tự. |
| http.server | Phần có sẵn của Python để phục vụ trang web và nhận yêu cầu. |
| HTML | Mô tả nội dung của trang. |
| CSS | Chọn cách trình bày, màu sắc, kích thước và bố cục trang. |
| JavaScript | Xử lý thao tác chọn ảnh, gửi yêu cầu và hiển thị kết quả trong trình duyệt. |
| pytest | Chạy các tệp kiểm tra mã trong giai đoạn phát triển. |

Thư viện là bộ công cụ do người khác cung cấp sẵn. Dự án tự nối các công cụ xử lý ảnh và tự tính phép so mẫu bằng NumPy; điều đó không có nghĩa tự viết lại mọi phép đổi màu/đọc PNG bên trong OpenCV.

### 20.4. Cách chạy và dừng

Yêu cầu khai báo trong pyproject.toml là Python 3.11 trở lên. Nếu môi trường .venv đã được tạo và cài đủ thư viện, tại PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
python app.py
~~~

.venv là môi trường Python riêng cho thư viện của dự án. Mở trình duyệt tại:

~~~text
http://127.0.0.1:8501
~~~

127.0.0.1 là địa chỉ quay về chính máy đang chạy. 8501 là số cổng để trình duyệt tìm đúng chương trình. App chỉ nhận kết nối trên địa chỉ này; ảnh được xử lý tại máy này.

Nếu cổng bận:

~~~powershell
python app.py --port 8502
~~~

Sau đó mở địa chỉ dùng cổng 8502.

Các đường dẫn:

| Yêu cầu | Việc làm |
|---|---|
| GET / hoặc GET /index.html | Lấy trang web. |
| GET /health | Hỏi server còn đáp ứng không; trả ok = true. |
| POST /api/recognize | Gửi ảnh để nhận dạng. |

Dừng bằng Ctrl+C ở cửa sổ chạy Python. Nếu có traceback kết thúc bằng KeyboardInterrupt, Python đang báo nó nhận lệnh ngắt. app.py hiện chưa bắt riêng ngoại lệ đó để in thông báo dừng gọn.

Trình duyệt có thể tự hỏi favicon.ico (hình biểu tượng trang). App không cung cấp đường dẫn đó nên có thể ghi 404. Điều này không liên quan đến độ đúng của bước OCR.

### 20.5. Chức năng hiện có và giới hạn cần nhớ

Ứng dụng nhận PNG/JPG/JPEG tối đa 15 MB, cho kéo thả/chọn ảnh, hiển thị kết quả, sao chép và tải TXT. Hình chụp đầu vào không được gửi đến dịch vụ OCR bên ngoài. Ảnh trong giao diện được trao đổi với Python đang chạy trên cùng máy.

Những giới hạn nằm ở cơ chế nhận dạng:

- Đếm hàng/cột phù hợp hơn khi dòng gần thẳng và tách nhau.
- Mẫu pixel nhạy với kiểu chữ, độ đậm, độ nghiêng và cách làm mịn mép.
- Ảnh thiếu nét sau ngưỡng không thể phục hồi bằng so khớp đơn giản.
- Dấu cách phụ thuộc khoảng cách hình học.
- Các quy tắc theo vị trí có thể làm đúng hoặc sai tùy tình huống.
- Chưa có bước tự xoay thẳng ảnh, bộ đọc bố cục nhiều cột hay mô hình đọc ngôn ngữ.
- Chưa có tập ảnh chụp độc lập đủ lớn để khẳng định chất lượng ngoài dữ liệu tổng hợp hiện có.

### 20.6. Bài báo và phần tự lựa chọn của dự án

Theo tài liệu phân tích bài báo trong dự án, bài tham khảo chính là:

Md. Anwar Hossain và Sadia Afrin, “Optical Character Recognition based on Template Matching”, Global Journal of Computer Science and Technology, tập 19(C2), 2019.

Bài báo trình bày bốn nhóm công việc: xử lý ảnh trước, lấy đặc trưng, tạo tập mẫu và so khớp. “Đặc trưng” nghĩa là thông tin của ký tự dùng để phân biệt; ở cách triển khai này, mẫu hình pixel chuẩn hóa là thông tin chủ yếu được đem so.

Bài báo nêu ảnh xám/nhị phân, loại vùng nhỏ hơn 30 điểm, mẫu từ Calibri/Verdana và chọn mẫu có điểm cao nhất. Bài báo không đặc tả đủ công thức similarity, cách tìm ngưỡng, quy tắc cắt dòng/ký tự hay cách ghép dấu cách.

Vì vậy khi trình bày cần ghi:

| Nội dung | Nguồn của lựa chọn |
|---|---|
| Hướng nhận dạng bằng mẫu ảnh chữ | Theo bài báo tham khảo. |
| Ngưỡng diện tích 30 | Giá trị bài báo nêu; mã bổ sung ngoại lệ. |
| Tự chọn Otsu | Lựa chọn của bản triển khai. |
| Cộng hàng/cột để cắt chữ | Lựa chọn của bản triển khai. |
| Bảng mẫu 48 × 48, lề 4 | Lựa chọn của bản triển khai. |
| Công thức Pixel Similarity và NCC | Phép đo do bản triển khai chọn; bài báo không ghi công thức cụ thể này. |
| Kho font mở rộng, quy tắc dấu câu/vị trí | Phần bổ sung của bản triển khai. |
| Bộ 32 ảnh và các chỉ số trong CSV | Thí nghiệm của dự án trên dữ liệu riêng. |

Không gọi số liệu hiện tại là tái tạo chính xác kết quả paper vì dữ liệu và chi tiết triển khai khác nhau.

### 20.7. Nếu chuẩn bị báo cáo thì nên minh họa gì?

Nên chọn một ảnh và trình bày theo đúng thứ tự ảnh thay đổi: ảnh gốc, ảnh xám, ảnh hai giá trị, ảnh đã lọc, biểu đồ tổng mực theo hàng/cột hoặc bảng đếm, vùng chữ sau cắt, ảnh vùng chữ 48 × 48, vài ảnh mẫu gần nhất và văn bản cuối.

Mã nội bộ có giữ một số ảnh trung gian nhưng giao diện hiện chỉ hiện ảnh gốc và ảnh vẽ khung. Nếu muốn hình minh họa đầy đủ trong báo cáo, cần xuất các ảnh trung gian bằng công cụ phục vụ phân tích; không nên ghi rằng giao diện đã cho xem tất cả chúng.

Với lỗi, nên trả lời cụ thể:

1. Nét chữ còn nguyên sau ngưỡng hay đã mất?
2. Vùng ảnh đã cắt đúng một ký tự chưa?
3. Ảnh mẫu nào đạt điểm cao và chênh bao nhiêu?
4. Quy tắc theo vị trí có đổi dự đoán ban đầu không?
5. Ký tự đúng nhưng khoảng trắng bị ghép sai không?

Cách này giúp biết cần cải thiện bước nào, thay vì chỉ nhìn một tỷ lệ rồi kết luận chung.

Những việc đáng làm tiếp là tạo bộ ảnh chụp có đáp án, thử font không nằm trong kho, so Pixel/NCC với điều kiện giống nhau và phân tích lỗi theo các bước trên. Chưa cần mở rộng thêm chức năng giao diện nếu mục tiêu trước mắt là hiểu, giải thích và đánh giá đúng phương pháp.

### 20.8. Những từ cần tra nhanh

| Từ xuất hiện trong mã/tài liệu | Nghĩa trong dự án |
|---|---|
| pixel | Một ô nhỏ của ảnh. |
| array / matrix | Bảng số trong bộ nhớ. |
| grayscale | Ảnh chỉ còn độ sáng xám. |
| binary image | Ảnh hai giá trị, ở đây 0/255. |
| mask | Bảng đánh dấu một nhóm vị trí ảnh. |
| foreground / background | Phần mực cần tìm / phần nền. |
| connected component | Nhóm điểm mực nối được với nhau. |
| threshold | Ngưỡng dùng để chia điểm tối/sáng. |
| histogram | Bảng đếm có bao nhiêu điểm ở mỗi mức sáng. |
| projection | Cộng/đếm điểm mực theo hàng hoặc cột. |
| segmentation | Cắt/chia ảnh thành các vùng dòng hoặc ký tự. |
| crop | Phần ảnh được cắt ra. |
| glyph | Hình vẽ cụ thể của một ký tự. |
| normalize | Đưa ảnh về một quy cách chung, ở đây cùng kích thước và cách căn giữa. |
| padding | Phần lề trống quanh ảnh chữ. |
| template bank | Kho ảnh mẫu đã biết đáp án. |
| ranking / top-k | Xếp điểm từ cao xuống và giữ k đáp án đầu. |
| baseline | Đường chân chữ ước lượng từ vị trí đáy các chữ. |
| heuristic | Quy tắc suy đoán dựa trên đặc điểm thường gặp. |
| ground truth | Đáp án đúng để đo lỗi. |
| edit distance | Số chỉnh sửa ít nhất giữa hai chuỗi. |
| CER | Số chỉnh sửa chia số ký tự đáp án. |
| exact match | Chuỗi đúng hoàn toàn. |
| API | Điểm nhận yêu cầu giữa các phần chương trình. |
| JSON | Văn bản đóng gói dữ liệu theo tên trường và giá trị. |
| Base64 | Cách chuyển byte thành chuỗi ký tự để truyền. |

### 20.9. Nguồn đọc kèm

Đối chiếu trong dự án:

- [README: cài đặt và chạy](../README.md)
- [Các công thức thuật toán đã có](algorithms.md)
- [Phân tích bài báo và phần triển khai](paper_analysis.md)
- [Hướng dẫn demo](presentation_guide.md)
- [Mã tiền xử lý](../src/classical_ocr/preprocessing.py)
- [Mã tách dòng và ký tự](../src/classical_ocr/segmentation.py)
- [Mã tạo và chuẩn hóa mẫu](../src/classical_ocr/template_generator.py)
- [Mã so khớp](../src/classical_ocr/template_matching.py)
- [Mã điều phối và quy tắc nhận dạng](../src/classical_ocr/recognition.py)
- [Mã ghép văn bản](../src/classical_ocr/reconstruction.py)
- [Mã tính sai số](../src/classical_ocr/evaluation.py)
- [CSV kết quả Pixel Similarity](../evaluation_pixel.csv)
- [Bài báo PDF trong dự án](../pdf/Optical_Character_Recognition_based_on_T.pdf)

Tham khảo chính thức để hiểu các lời gọi thư viện được giải thích trong tài liệu:

- [OpenCV: cách ngưỡng và Otsu hoạt động](https://docs.opencv.org/4.13.0/d7/d4d/tutorial_py_thresholding.html)
- [OpenCV: ý nghĩa các kênh HSV](https://docs.opencv.org/4.13.0/df/d9d/tutorial_py_colorspaces.html)
- [OpenCV: lấp vùng ảnh và phương pháp Telea](https://docs.opencv.org/4.13.0/df/d3d/tutorial_py_inpainting.html)

Những công thức và điều kiện gắn với hành vi dự án trong tài liệu được đối chiếu từ mã nguồn hiện có. Các ví dụ tính bằng bảng số nhỏ là minh họa cách làm, không phải số liệu nhận dạng thực nghiệm mới.

