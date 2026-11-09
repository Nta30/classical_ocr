# Các thuật toán trong Classical OCR Lab

## 1. Chuyển ảnh sang grayscale

Với thành phần màu `R`, `G`, `B` trong khoảng `[0,255]`:

\[
Y = 0.299R + 0.587G + 0.114B
\]

OpenCV nhận ảnh theo thứ tự BGR nên hàm grayscale dùng cùng trọng số theo channel BGR. Kết quả là một ma trận cường độ 8-bit.

## 2. Binarization

Với ngưỡng `t`, ảnh nền sáng chữ tối được biến thành mask foreground:

\[
B(x,y)=\begin{cases}1,&Y(x,y)<t\\0,&Y(x,y)\geq t\end{cases}
\]

Global threshold dùng một giá trị `t` cố định. Otsu chọn ngưỡng phân hoạch histogram sao cho phương sai giữa hai lớp lớn nhất:

\[
t^* = \arg\max_t \; \omega_0(t)\omega_1(t)[\mu_0(t)-\mu_1(t)]^2
\]

Trong app, OpenCV tự tính ngưỡng Otsu; người dùng không cần cấu hình bước này. Foreground được lưu thành giá trị 255. Otsu phù hợp nền tương đối đồng đều; bóng/ánh sáng không đều có thể cần threshold thích nghi, hiện chưa triển khai.

## 3. Lọc thành phần nhỏ

Connected Component Analysis gán nhãn các vùng foreground 8-liên thông. Nếu diện tích `A_i < A_min`, vùng thường được loại. Bài báo nêu ngưỡng 30 pixel; app giữ nét cao/mảnh như `i`, `l`, `1`, dấu câu nhỏ gần baseline, và các cặp chấm dọc như `:`/`;` theo vị trí cạnh thân chữ. Nhiễu pixel rời vẫn bị loại.

Phép quyết định giữ chấm là heuristic; nhiễu trùng vị trí với nét chữ cũng có thể được giữ. Median filter và morphology là tùy chọn vì chúng có thể làm mòn nét nhỏ hoặc làm các nét gần nhau nối liền.

## 4. Tách dòng và ký tự bằng projection

Với mask nhị phân `B` kích thước `H×W`:

\[
P_y(y)=\sum_{x=0}^{W-1}B(y,x),\qquad
P_x(x)=\sum_{y=y_0}^{y_1-1}B(y,x)
\]

Các đoạn liên tiếp có `P_y(y)>0` tạo vùng dòng. Trong mỗi dòng, đoạn liên tiếp `P_x(x)>0` tạo vùng ký tự. Chấm `i/j` vẫn cùng segment với thân nếu chúng chiếm chung cột x. Những nét chạm nhau không có cột trống sẽ tạo một segment lớn; project gắn cờ vùng rộng để báo cần xem lại thay vì âm thầm coi segmentation là chắc chắn.

**Pseudocode**

```text
row_runs = contiguous_runs(sum_x(B) > 0)
for each row_run:
    col_runs = contiguous_runs(sum_y(B[row_run]) > 0)
    for each col_run:
        bbox = tight_foreground_box(row_run, col_run)
        emit character_crop, bbox
```

Thời gian tính projection là `O(HW)`; tạo các run là tuyến tính theo `H+W`.

Nếu segment rộng có điểm khớp thấp, bộ nhận dạng thử các đường cắt gần đáy sâu của projection theo cột. Chọn đường cắt có điểm trung bình hai phần cao nhất; chỉ giữ khi cả hai phần có điểm match hợp lý và điểm trung bình tăng so với segment ban đầu. Đây là heuristic để tách một số ký tự chạm nhau; các vùng đã thử tách vẫn được đánh dấu cần xem lại.

## 5. Chuẩn hóa template/glyph

Crop được cắt sát foreground, scale đồng đều để vừa vùng canvas 48×48 có padding, rồi căn giữa. Tỷ lệ chiều rộng/chiều cao được giữ nguyên để tránh bóp méo ký tự. Mép grayscale của template font được nhị phân hóa ở mức 128 trước khi resize để tránh coi pixel khử răng cưa mờ là nét chữ. Template dùng mask 0/1, cùng kích thước với glyph trước khi so sánh.

## 6. Pixel Similarity

Với hai mask `I,T ∈ {0,1}^{W×H}`:

\[
S_{pixel}(I,T)=1-\frac{1}{WH}\sum_{x=1}^{W}\sum_{y=1}^{H}|I(x,y)-T(x,y)|
\]

Giá trị nằm trong `[0,1]`, càng lớn càng giống. Nếu có `N` template và `K` ký tự cần nhận dạng, chi phí là `O(KNWH)` phép toán; mỗi template chiếm `WH` giá trị 8-bit.

## 7. Normalized Cross-Correlation (NCC)

Làm phẳng hai mask thành vector `i,t`, trừ trung bình rồi tính:

\[
NCC(i,t)=\frac{\sum_j(i_j-\bar i)(t_j-\bar t)}{\sqrt{\sum_j(i_j-\bar i)^2\sum_j(t_j-\bar t)^2}}
\]

NCC nằm trong `[-1,1]`. Nếu một vector có phương sai bằng 0, mã tránh chia cho 0: hai mask hằng giống hệt trả 1, khác nhau trả 0. Để xếp hạng cùng miền dương, script đánh giá dùng `S_{display}=(NCC+1)/2`. Đây là metric bổ sung để so sánh nghiên cứu; app OCR chính dùng Pixel Similarity. Paper không đưa công thức NCC.

**Pseudocode so khớp**

```text
I = normalize(glyph)
for each character class c:
    best[c] = maximum score over that class's font/size templates
rank classes by best[c], descending
return top 3 classes and their best template images
```

Tập template gồm 100 lớp chữ, số và dấu câu ASCII cùng dấu nháy cong/gạch ngang thông dụng, nhiều font và cỡ render. Xếp hạng gộp các font/cỡ theo ký tự để top 3 là ba lớp ký tự khác nhau, không phải ba biến thể cùng một chữ.

## 8. Tái tạo văn bản và đánh giá

Bounding box được đọc từ trái sang phải. Ngưỡng khoảng trắng bắt đầu từ tỷ lệ chiều cao ký tự, rồi điều chỉnh theo bước nhảy giữa các cụm khoảng cách trong cùng dòng để tránh coi sai kerning 1–2 pixel là dấu cách. Mỗi dải dòng trở thành một dòng output. Khi `I` và `l` có điểm bằng nhau trong sai số nhỏ, vị trí giữa từ ưu tiên `l`, còn đầu từ ưu tiên `I`. Với `i/j` có điểm gần nhau, vị trí đáy glyph so với baseline của dòng giúp nhận ra nét thòng của `j`. Đây là các heuristic bổ sung, không có trong paper.

Với reference dài `L` và khoảng cách chỉnh sửa Levenshtein `D`:

\[
CER = D/L,\qquad CharacterAccuracy=\max(0,1-CER)
\]

Khi reference rỗng, mẫu số dùng 1 để tránh chia cho 0. Exact match là phép so sánh toàn bộ chuỗi, kể cả khoảng trắng và xuống dòng. Các chỉ số phải được tính trên ground truth thực tế.

## Ưu điểm và hạn chế

- Các phép biến đổi trung gian hiển thị được và có thể giải thích bằng công thức.
- Không cần dữ liệu huấn luyện hoặc mô hình đã huấn luyện; template tái tạo từ font cài trên máy.
- So khớp pixel nhạy với kiểu font, độ đậm, antialiasing, scale và chất lượng segmentation.
- Projection phù hợp văn bản gần ngang và tách biệt; không xử lý tốt skew mạnh, ký tự chạm hoặc bố cục nhiều cột.
- Điểm cao nhất không được hiệu chỉnh thành xác suất; ký tự mơ hồ như `O/0`, `I/l/1`, `B/8` có thể nhầm.
