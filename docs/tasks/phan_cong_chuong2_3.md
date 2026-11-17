# Phân công Chương 2 và Chương 3 (Group 23)

Hai người: **Khoa** và **Thông**.

| | Khoa | Thông |
|---|---|---|
| Chương 3 | **Ứng dụng 2** (sinh học hoặc hình ảnh), 25% | **Ứng dụng 1** (giỏ hàng hoặc log), 25% |
| Chương 2 | Nửa B: bộ nhớ, độ dài giao dịch, đề xuất tối ưu | Nửa A: dữ liệu, correctness, thời gian, số itemset, scalability |

Lý do chia như vậy: Ứng dụng 2 nặng hơn Ứng dụng 1 (phải tự trích đặc trưng hoặc mã hóa chuỗi), nên Khoa nhận nửa chương 2 nhẹ hơn. Thông làm Ứng dụng 1 nhiều khả năng dùng Retail, mà Retail cũng là benchmark chương 2, nên Thông lo phần dữ liệu và scalability luôn.

---

## Việc chung (làm đầu tiên, cả hai cùng thống nhất)

1. **Hàm `encode` / `decode` item** trong `src/utils.py`: đổi item dạng chữ sang số nguyên và đổi ngược lại. Cả hai ứng dụng chương 3 đều cần. Ai viết xong trước thì push, người kia dùng chung.
2. **Không đổi chữ ký hàm** `fpgrowth(transactions, min_count) -> dict{tuple: support}`. Muốn tối ưu thì chỉ sửa bên trong.
3. **Định dạng CSV kết quả đo** (để vẽ biểu đồ thống nhất), đặt trong `data/output/exp/`:
   - `runtime.csv`: `dataset, minsup, min_count, itemsets, t_basic_s, t_opt_s, t_spmf_s, match_pct`
   - `memory.csv`: `dataset, minsup, peak_basic_mb, peak_opt_mb`
   - `scalability.csv`: `dataset, fraction, transactions, minsup, itemsets, t_opt_s`
   - `txlen.csv`: `avg_len, transactions, minsup, itemsets, t_opt_s`
4. **Danh sách minsup cố định** cho mỗi dataset (chốt ngay từ đầu để hai người không phải chờ nhau). Gợi ý ban đầu, Thông chạy thử rồi chỉnh lại nếu quá chậm:
   - Chess: 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6
   - Mushroom: 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05
   - Retail: 0.01, 0.008, 0.005, 0.004, 0.003, 0.002, 0.001
   - T10I4D100K: 0.01, 0.008, 0.005, 0.004, 0.003, 0.002, 0.001
   - **minsup trung bình** (dùng cho đo bộ nhớ): điểm thứ 4 của mỗi danh sách.
5. **Git:** mỗi người một nhánh (`thong/ch2a-app1`, `khoa/ch2b-app2`), commit nhỏ và thường xuyên (đề chấm qua commit history), merge vào `main` qua pull request.
6. **Seed cố định** ở mọi chỗ có ngẫu nhiên (cắt tập con, sinh dữ liệu tổng hợp, k-means): `SEED = 42`.

---

## Thông

### Chương 2, nửa A

- [ ] Tải **Retail** và **T10I4D100K** vào `data/benchmark/` (nếu quá lớn thì host trên Hugging Face/Kaggle, dán link vào README).
- [ ] Thêm hai dataset mới và danh sách minsup vào `scripts/make_refs.py`, sinh ref SPMF.
- [ ] Viết `scripts/exp_runtime.py`: với mỗi dataset × minsup, chạy bản basic, bản tối ưu, SPMF; đo thời gian (trung vị 3 lần), so khớp kết quả với SPMF, ghi `runtime.csv`.
  - Một lần chạy cho ra luôn số liệu của **3 thực nghiệm**: correctness, thời gian theo minsup, số itemset theo minsup.
  - Thời gian SPMF: SPMF tự in ra "Total time ~ ... ms", hoặc đo bằng `time.perf_counter()` quanh `subprocess.run`. Chọn một cách và ghi rõ trong báo cáo.
- [ ] Viết `scripts/exp_scalability.py`: cắt Retail thành 10/25/50/75/100% giao dịch (dùng seed), chạy ở một minsup cố định, ghi `scalability.csv`.
- [ ] Vẽ biểu đồ: thời gian theo minsup (nhóm vs SPMF, mỗi dataset một hình), số itemset theo minsup (dày vs thưa), scalability.
- [ ] Viết nhận xét cho các biểu đồ trên: dày vs thưa, tuyến tính hay phi tuyến, giải thích dựa trên bài báo (kích thước FP-tree, Lemma 2.2, độ sâu đệ quy).

### Chương 3, Ứng dụng 1

- [ ] Chọn hướng: giỏ hàng (Retail/Groceries) hoặc log hệ thống.
- [ ] Biến đổi dữ liệu thành giao dịch (+ `encode`).
- [ ] Viết hàm sinh **luật kết hợp** từ kết quả `fpgrowth`: tính confidence, lift; lọc theo minconf.
- [ ] Top-10 luật theo lift, giải thích ý nghĩa (kinh doanh hoặc phát hiện lỗi/bất thường).
- [ ] Đưa phần này vào `notebooks/demo.ipynb`, chạy sạch trên Colab.

---

## Khoa

### Chương 2, nửa B

- [ ] Viết `scripts/exp_memory.py`: đo **peak memory** bằng `tracemalloc` cho bản basic và bản tối ưu, trên 4 dataset tại minsup trung bình, ghi `memory.csv`.
  - Lưu ý: chạy đo bộ nhớ **riêng** với đo thời gian, vì `tracemalloc` làm code chạy chậm đi.
- [ ] Viết `scripts/exp_txlen.py`: tự sinh CSDL tổng hợp có độ dài giao dịch trung bình tăng dần (ví dụ 5, 10, 15, 20, 25, 30), giữ nguyên số giao dịch và số item, dùng seed; chạy ở một minsup cố định, ghi `txlen.csv`.
- [ ] Vẽ biểu đồ bộ nhớ (basic vs tối ưu) và biểu đồ thời gian theo độ dài giao dịch.
- [ ] Viết nhận xét cho hai biểu đồ trên.
- [ ] Viết mục **điểm mạnh/yếu so với SPMF** và **ít nhất 2 hướng tối ưu tiếp theo** (đọc số liệu của Thông để viết). Ví dụ hướng: dùng mảng/số nguyên thay vì object node, không dựng conditional tree khi chỉ còn ít item, projected database (Mục 4 bài báo), đếm bằng `Counter`.

### Chương 3, Ứng dụng 2

- [ ] Chọn hướng: sinh học (genome/protein) hoặc hình ảnh (bag of visual words).
  - Nếu chọn hình ảnh: **hỏi giảng viên** xem có được dùng OpenCV / scikit-learn cho phần trích đặc trưng và k-means không (đề chỉ cho numpy, pandas, bitarray). Nếu không được, phải tự viết k-means bằng numpy.
- [ ] Biến đổi dữ liệu thành giao dịch (+ `encode`).
- [ ] Chạy `fpgrowth` của nhóm, chọn minsup hợp lý.
- [ ] Phân tích, diễn giải ý nghĩa các pattern (sinh học, hoặc ứng dụng cho phân tích ảnh/huấn luyện mô hình).
- [ ] Đưa phần này vào `notebooks/demo.ipynb`, chạy sạch trên Colab.

---

## Thứ tự gợi ý

| Giai đoạn | Thông | Khoa |
|---|---|---|
| 1 | Tải dataset, sinh ref, chốt minsup | Viết `encode`/`decode`, chọn hướng Ứng dụng 2, hỏi giảng viên |
| 2 | `exp_runtime.py`, `exp_scalability.py` | `exp_memory.py`, `exp_txlen.py` |
| 3 | Ứng dụng 1 | Ứng dụng 2 |
| 4 | Biểu đồ + nhận xét phần mình | Biểu đồ + nhận xét phần mình + đề xuất tối ưu |
| 5 | Cùng ghép notebook Colab, README, báo cáo, chạy lại toàn bộ test |

Chỗ duy nhất phải chờ nhau: Khoa cần dataset Retail và T10I4D100K của Thông để đo bộ nhớ, và cần số liệu `runtime.csv` để viết phần đề xuất tối ưu. Trong lúc chờ, Khoa đo bộ nhớ trên Chess, Mushroom trước.
