# Hướng dẫn cho Thông: thêm phần 2A và Ứng dụng 1

Tài liệu này tóm tắt những gì đã có trong repo, và những gì Thông cần thêm vào **notebook**, **README** và **báo cáo** cho phần của mình (Chương 2 nửa A và Ứng dụng 1).

---

## 0. Tình trạng hiện tại

| Phần | Trạng thái |
|---|---|
| Chương 1: cài đặt, test | Xong. Khớp SPMF 100% trên 28 ca |
| Chương 2A: script `exp_runtime.py`, `exp_scalability.py` | Xong, đã chạy, CSV có trong repo |
| Chương 2A: biểu đồ `runtime.png`, `itemsets.png`, `scalability.png` | Có rồi. `runtime.png` và `itemsets.png` cần vẽ lại sau khi sửa lỗi trùng dòng (mục 2) |
| Chương 2A: ô notebook + nhận xét | **Thông làm** |
| Chương 2B: bộ nhớ, độ dài giao dịch, so SPMF, hướng tối ưu | Xong (Khoa), xem `docs/chuong_2B.md` |
| Ứng dụng 1 | **Thông làm** |
| Ứng dụng 2 | Xong (Khoa) |
| Notebook: Phần 0, 1, 2B, 4 | Xong, chạy sạch trên Colab |

---

## 1. Chuẩn bị

```bat
git checkout main
git pull
git checkout -b thong-ch2a-app1
pip install -r requirements.txt
```

- Mọi lệnh chạy từ **thư mục gốc repo**.
- Repo đã có `pytest.ini` (thư mục tạm `.pytest_tmp/`), để tránh lỗi `PermissionError: [WinError 5]` của pytest trên Windows.
- **Luôn chạy `git status` trước khi commit**, để chắc chắn file mình sửa (nhất là notebook) đã được lưu và nằm trong danh sách.

---

## 2. Đã sửa: `runtime.csv` bị trùng dòng (Khoa sửa, Thông đọc để nắm)

**Lỗi cũ:** `runtime.csv` có **56 dòng thay vì 28**, mỗi ca xuất hiện hai lần. Nguyên nhân là `exp_runtime.py --force` chạy lại các ca đã có nhưng chỉ **ghi nối thêm** vào cuối file. Vì vậy `plot_ch2.py` vẽ cả hai lần đo lên cùng một đường, làm đường trong `runtime.png` bị gấp khúc.

**Đã sửa 3 chỗ:**

1. **`scripts/exp_runtime.py`:**
   - Thay `append_row` bằng `save_row`: mỗi lần lưu một ca, dòng cũ của **cùng cặp (dataset, minsup)** bị thay chứ không ghi thêm. File vẫn được lưu sau từng ca, nên dừng giữa chừng không mất phần đã chạy.
   - Thêm tham số **`--csv`** để ghi ra file khác (mặc định vẫn là `runtime.csv`). Notebook dùng tham số này, xem mục 3.
2. **`data/output/exp/runtime.csv`:** đã gộp còn **28 dòng**, giữ **lần đo sau cùng** của mỗi ca. Lần đo này có đủ SPMF và cả 28 ca đều khớp 100%.
3. **`scripts/plot_ch2.py`:** hàm `load` bỏ trùng thêm một lần nữa để phòng hờ (giữ dòng cuối của mỗi ca).

**Còn phải làm:** chạy lại `python -m scripts.plot_ch2` để vẽ lại `runtime.png` và `itemsets.png` từ CSV đã sạch, commit hai ảnh, rồi upload đè lên hai file cùng tên trong thư mục `figures/` trên Overleaf.

**Từ giờ:** không cần sợ trùng khi chạy `--force` nữa. Nếu muốn đo lại toàn bộ thì chỉ cần `python -m scripts.exp_runtime --force`.

---

## 3. Thêm Phần 2A vào notebook

Notebook đã có sẵn ô tiêu đề giữ chỗ `### 2A. Thời gian chạy, số itemset, khả năng mở rộng`. Thông chèn các ô **ngay dưới ô đó, phía trên ô `### 2B. Bộ nhớ đỉnh`**. Ô vẽ biểu đồ của 2B (`plot_ch2`) đã vẽ và hiển thị cả 3 biểu đồ của 2A, nên 2A **không cần** ô vẽ riêng.

Quy ước chung của notebook:
- Xen kẽ ô **Markdown** (giải thích: đo gì, mất bao lâu) và ô **Code** (chạy).
- Logic nằm trong `src/` và `scripts/`; notebook chỉ gọi script (`!python -m scripts...`) hoặc gọi hàm, rồi hiển thị kết quả.
- Chỉ dùng `!` với `python` và `pip`. Không dùng `head`, `ls`, `cat` vì cmd của Windows không có.
- Thao tác dài (trên khoảng 2 phút) thì để ở dạng **comment**, kèm một ô Markdown giải thích, giống ô test đầy đủ ở Phần 1.

### Vấn đề cần xử lý: chạy `exp_runtime` trên Colab

- Chạy đầy đủ mất khoảng 7 phút (chưa tính SPMF), quá lâu cho một ô demo.
- Colab không có Java 25 nên không chạy được SPMF.
- Nếu chạy `exp_runtime` trên Colab, nó sẽ ghi thêm vào `runtime.csv` chính thức.

**Cách làm:** `exp_runtime.py` đã có tham số `--csv` để ghi ra file khác. Notebook chạy bản nhẹ ra file riêng `runtime_colab.csv` (đã có trong `.gitignore`), còn bảng và biểu đồ chính thức vẫn lấy từ `runtime.csv`.

### Khung ô gợi ý

**[MD]**
```markdown
#### Thời gian chạy và số itemset theo minsup
4 CSDL × 7 mức minsup. Bản chạy đầy đủ (trung vị 3 lần, kèm bản cơ bản và SPMF) mất khoảng 7 phút và cần Java 25,
nên được chạy ở máy của nhóm; kết quả nằm trong `data/output/exp/runtime.csv`.
Ô dưới chạy bản rút gọn (1 lần, chỉ bản tối ưu, không SPMF) để chứng minh mã nguồn tái thực hiện được.
```

**[CODE]**
```python
!python -m scripts.exp_runtime --runs 1 --skip-basic --skip-spmf --csv data/output/exp/runtime_colab.csv
```

**[CODE]**
```python
# So số itemset của bản chạy lại với số liệu chính thức: phải trùng khớp
colab = pd.read_csv("data/output/exp/runtime_colab.csv")
official = pd.read_csv("data/output/exp/runtime.csv")
...
```
(Thông tự hoàn thiện: ghép hai bảng theo `dataset, minsup`, in ra số ca có `itemsets` trùng nhau, phải là 28/28.)

**[MD]**
```markdown
#### Khả năng mở rộng (Retail, 10% → 100% giao dịch)
Tập con lồng nhau, trộn bằng seed 42, minsup cố định 0,004. Thời gian chạy: vài giây.
```

**[CODE]**
```python
!python -m scripts.exp_scalability
pd.read_csv("data/output/exp/scalability.csv")
```

**[MD]: Nhận xét 2A** (4–6 gạch đầu dòng, rút gọn từ phần viết trong báo cáo, xem mục 5).

`runtime_colab.csv` đã nằm trong `.gitignore`, nên không lo commit nhầm.

---

## 4. Ứng dụng 1

### Yêu cầu của đề

Chọn 1 trong 2 hướng:
- **Giỏ hàng (market basket):** dữ liệu bán lẻ thật (Retail, Groceries…). Từ frequent itemset, sinh **luật kết hợp** X → Y với support của X ≥ minsup và confidence của luật ≥ minconf. Trình bày **top-10 luật theo lift**, giải thích ý nghĩa kinh doanh.
- **Log hệ thống:** tìm tổ hợp sự kiện hay xảy ra cùng nhau, thảo luận khả năng phát hiện lỗi hoặc bất thường.

Kết quả **phải** thu được bằng `fpgrowth` của nhóm, không dùng thư viện FIM.

### Nhắc lại công thức (cho hướng giỏ hàng)

Với luật X → Y (X, Y rời nhau, X ∪ Y là tập phổ biến), N là số giao dịch:
- support(X → Y) = sup(X ∪ Y) / N
- confidence(X → Y) = sup(X ∪ Y) / sup(X)
- lift(X → Y) = confidence(X → Y) / (sup(Y) / N)

Lift > 1: X và Y xuất hiện cùng nhau **nhiều hơn** mức ngẫu nhiên; lift ≈ 1: độc lập; lift < 1: loại trừ nhau.

**Không cần đếm lại support:** mọi tập con của một tập phổ biến cũng phổ biến (tính chất Apriori), nên sup(X) và sup(Y) đều đã có sẵn trong `dict` kết quả của `fpgrowth`. Chỉ cần tra `result[X]`, với X là tuple **đã sắp tăng dần** (`fpgrowth` luôn trả về itemset dạng đó).

### Gợi ý tổ chức code (giống cấu trúc Ứng dụng 2)

| File | Nội dung |
|---|---|
| `src/app1_*.py` | Đọc dữ liệu, biến thành giao dịch, hàm sinh luật (`generate_rules(result, n, minconf)`) |
| `scripts/app1_*.py` | Chạy, in top-10 luật, vẽ biểu đồ vào `docs/figures/app1_*.png` |
| `tests/test_rules.py` | Kiểm thử hàm sinh luật trên một CSDL nhỏ tính tay được |

Dùng lại những thứ đã có:
- `encode`, `decode`, `invert_code`, `save_code` trong `src/utils.py`: Groceries có item là tên mặt hàng (chữ), phải `encode` trước khi chạy `fpgrowth`. Làm sạch chữ (`strip`, `lower`) **trước** khi `encode`.
- `to_min_count` trong `src/config.py`, `SEED = 42` nếu có ngẫu nhiên.
- Nếu dùng Retail thì item đã là số nhưng **không có tên mặt hàng**, nên khó giải thích ý nghĩa kinh doanh. Groceries có tên mặt hàng nên diễn giải dễ hơn.

### Thêm vào notebook (Phần 3)

Chèn **dưới ô tiêu đề giữ chỗ `## 3. Ứng dụng 1`**, phía trên `## 4. Ứng dụng 2`. Gợi ý thứ tự:

1. [MD] Dữ liệu, hướng đã chọn, cách biến dữ liệu thành giao dịch (và vì sao chọn cách đó).
2. [CODE] Đọc dữ liệu, xem vài giao dịch, số giao dịch và số item.
3. [MD] Chọn minsup và minconf (lý do).
4. [CODE] Chạy `fpgrowth`, số itemset theo vài mức minsup (bảng `pd.DataFrame`).
5. [CODE] Sinh luật, hiển thị top-10 theo lift (bảng: luật, support, confidence, lift).
6. [CODE] Biểu đồ (ví dụ scatter support–confidence, màu theo lift), hiển thị bằng `IPython.display.Image`.
7. [MD] Nhận xét: ý nghĩa kinh doanh của các luật nổi bật, hạn chế.

### Ghi chú về README

Mục `## Ứng dụng 1` trong README đang để trống. Điền theo cùng khung với mục Ứng dụng 2: dữ liệu, cách biến thành giao dịch, lệnh chạy, kết quả chính. Thêm tài liệu tham khảo của Ứng dụng 1 vào cuối README.

---

## 5. Phần viết báo cáo của Thông

### Chương 2A

Mỗi thực nghiệm viết theo khung: **thiết lập → kết quả (dẫn chiếu hình/bảng) → giải thích theo bài báo → kết luận**. Mẫu văn phong xem `docs/chuong_2B.md`.

1. **Dữ liệu benchmark:** bảng 4 CSDL (đã có trong README), lý do chọn (2 dày, 2 thưa, 1 tổng hợp), nguồn; giải thích vì sao Mushroom có 8.416 giao dịch thay vì 8.124.
2. **Correctness:** 28/28 ca khớp 100% với SPMF; mô tả cách so khớp (cùng itemset, cùng support, công thức `min_count`).
3. **Thời gian theo minsup** (`runtime.png`): xu hướng trên dữ liệu dày và thưa; chênh lệch bản cơ bản và bản tối ưu (tối ưu có tác dụng ở Mushroom, gần như không ở Retail, T10I4D100K); giải thích bằng Lemma 3.2 và kích thước FP-tree (Lemma 2.2). So sánh với SPMF đã viết ở mục 3 của `docs/chuong_2B.md`, chỉ cần dẫn chiếu, không viết lại.
4. **Số itemset theo minsup** (`itemsets.png`): dữ liệu dày tăng rất nhanh khi giảm minsup (Mushroom: 163 → 4,1 triệu), dữ liệu thưa tăng chậm hơn (Retail: 159 → 7.589); giải thích bằng độ dài giao dịch và mật độ.
5. **Khả năng mở rộng** (`scalability.png`): thời gian tăng gần tuyến tính theo số giao dịch (Retail 10% → 100%: 0,16 s → 1,51 s), số itemset gần như không đổi (831–864) vì minsup tương đối; so với Hình 13 trong bài báo (cũng tuyến tính).
6. **Lưu ý về độ dao động:** thực nghiệm đã được chạy đầy đủ hai lần (CSV giữ lần sau); giữa hai lần, thời gian của cùng một ca lệch nhau tới khoảng ±40% ở một số ca, nên chỉ kết luận dựa trên xu hướng và chênh lệch lớn.

### Chương 3: Ứng dụng 1

Dữ liệu và lý do chọn → cách biến thành giao dịch → chọn minsup, minconf → kết quả (số itemset, số luật, top-10 theo lift) → ý nghĩa kinh doanh (hoặc phát hiện bất thường) → hạn chế.

---

## 6. Chung cho cả nhóm trước khi nộp

- [ ] Chốt dạng mẫu báo cáo IEEE (Overleaf hay Word), khung mục lục và cách đánh số hình/bảng.
- [ ] Ghép báo cáo, xuất `docs/Report.pdf` (10–15 trang, không tính tài liệu tham khảo và phụ lục).
- [ ] Notebook: Restart → Run All ở máy, rồi Run all trên Colab, không ô nào lỗi.
- [ ] README: link Colab, output lần chạy test đầy đủ cuối cùng, mục Ứng dụng 1, họ tên thành viên.
- [ ] Tài liệu tham khảo: bài báo gốc + ít nhất 3 tài liệu khác (đã có 6 trong README, Thông bổ sung cho Ứng dụng 1).
- [ ] Mỗi người tự trả lời được câu hỏi về **cả phần của người kia** ở mức cơ bản (vấn đáp có thể hỏi chéo).
