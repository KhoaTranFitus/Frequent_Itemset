# FP-Growth: Khai thác tập phổ biến (Group 23)

Cài đặt lại thuật toán **FP-Growth** (Han và cộng sự, 2004) bằng Python thuần, kèm hai tối ưu: liệt kê trực tiếp cây một nhánh (Lemma 3.2) và thu nhỏ nút cây bằng `__slots__`. Kết quả khớp **100%** với SPMF trên 35 ca kiểm thử. Cài đặt được dùng cho hai ứng dụng: phân tích giỏ hàng và khai thác mẫu trong chuỗi DNA.

## Thành viên

| Thành viên | Phụ trách |
|---|---|
| Trần Đình Khoa | Cài đặt; thực nghiệm bộ nhớ, độ dài giao dịch, so sánh SPMF; Ứng dụng 2 |
| Lại Minh Thông | Thực nghiệm tính đúng, thời gian, số tập phổ biến, khả năng mở rộng; Ứng dụng 1 |

## Tài nguyên

- **Demo notebook trên Google Colab:** [mở notebook](https://colab.research.google.com/github/KhoaTranFitus/Frequent_Itemset/blob/main/notebooks/demo.ipynb)
- Báo cáo: [`docs/Report.pdf`](docs/Report.pdf)
- Bài báo gốc: [`docs/references/fpgrowth_04.pdf`](docs/references/fpgrowth_04.pdf)
- Dữ liệu: toàn bộ chỉ khoảng 9 MB (file lớn nhất là Retail, 4 MB), dưới giới hạn của GitHub nên **để thẳng trong repo**, không cần host trên Hugging Face hay Kaggle. Clone về là chạy được ngay:

| Thư mục | Nội dung | Nguồn |
|---|---|---|
| `data/toy/` | 4 CSDL nhỏ để kiểm thử nhanh | nhóm tự xây dựng |
| `data/benchmark/` | Chess, Mushroom, Retail, T10I4D100K | [SPMF Datasets](https://www.philippe-fournier-viger.com/spmf/datasets.php) |
| `data/app1/` | Groceries (9.835 giỏ hàng) | gói arules của R, xem [`data/app1/README.md`](data/app1/README.md) |
| `data/app2/` | Splice-junction Gene Sequences (3.190 chuỗi DNA) | UCI Machine Learning Repository |

## Cài đặt môi trường

Yêu cầu **Python 3.9 trở lên** (đã chạy trên Python 3.13).

```bash
git clone https://github.com/KhoaTranFitus/Frequent_Itemset.git
cd Frequent_Itemset
pip install -r requirements.txt
```

- Thuật toán chỉ dùng thư viện chuẩn của Python. `numpy`, `pandas`, `matplotlib` chỉ dùng để vẽ biểu đồ và sinh dữ liệu tổng hợp; `pytest` dùng để kiểm thử.
- Java 25 và `spmf.jar` (đặt trong `tool/`) **chỉ cần** khi muốn chạy đủ 98 test hoặc tự chạy lại SPMF để đối chiếu (xem mục [Kiểm thử](#kiểm-thử)).
- Mọi lệnh bên dưới chạy từ **thư mục gốc của repo**.

## Cách chạy

```bash
python -m src.algorithm.fpgrowth <file_input> --minsup <minsup> --output <file_output>
```

| Tham số | Ý nghĩa |
|---|---|
| `file_input` | file giao dịch định dạng SPMF |
| `--minsup` | ngưỡng support **tương đối** trong khoảng (0, 1], ví dụ `0.6` là 60% |
| `--output` | file kết quả |

Bản cơ bản (không tối ưu) chạy bằng `python -m src.algorithm.fpgrowth_basic` với cùng tham số.

### Ví dụ

Input `data/toy/toy_test1.txt` (mỗi dòng một giao dịch, item là số nguyên dương cách nhau bởi dấu cách):

```
6 1 3 4 7 9 13 16
1 2 3 6 12 13 15
2 6 8 10 15
2 3 11 14 16
1 6 3 5 12 16 13 14
```

Chạy:

```bash
python -m src.algorithm.fpgrowth data/toy/toy_test1.txt --minsup 0.6 --output out.txt
```

```
5 giao dịch, min_count = 3, tìm được 18 tập phổ biến
```

Output `out.txt` (mỗi dòng một tập phổ biến và support tuyệt đối), một vài dòng:

```
3 #SUP: 4
3 6 #SUP: 3
1 3 6 13 #SUP: 3
```

Ngưỡng tuyệt đối được tính là `min_count = ceil(minsup × số giao dịch)`, giống SPMF.

### Dữ liệu có item dạng chữ

```python
from src.utils import encode, decode
from src.algorithm.fpgrowth import fpgrowth

encoded, code = encode([["bread", "milk"], ["bread", "butter"], ["bread", "milk"]])
print(decode(fpgrowth(encoded, 2), code))
# {('bread',): 3, ('milk',): 2, ('bread', 'milk'): 2}
```

## Kiểm thử

Bộ test gồm **98 test**: tính đúng trên CSDL nhỏ (so với số đếm tay và SPMF), 4 CSDL benchmark × 7 minsup (so với SPMF), mã hoá item và sinh luật kết hợp.

Các test so với SPMF đối chiếu kết quả của nhóm với kết quả của SPMF trên cùng input (file tham chiếu trong `data/output/ref/`). File tham chiếu của 7 ca nhỏ có sẵn trong repo; của 28 ca benchmark thì không, vì quá lớn (riêng Mushroom ở minsup 0,05 đã 152 MB), nên cần sinh trước khi chạy test.

**Bước 1.** Cài Java 25 và tải `spmf.jar` vào `tool/` (chỉ làm một lần):

```bash
# Windows (PowerShell hoặc cmd)
winget install EclipseAdoptium.Temurin.25.JDK
mkdir tool
curl -L -o tool/spmf.jar https://www.philippe-fournier-viger.com/spmf/spmf.jar

# macOS
brew install --cask temurin@25
mkdir -p tool && curl -L -o tool/spmf.jar https://www.philippe-fournier-viger.com/spmf/spmf.jar
```

Sau khi cài Java, mở terminal mới rồi kiểm tra bằng `java -version` (phải là 25 trở lên).

**Bước 2.** Sinh file tham chiếu cho 28 ca benchmark (vài phút):

```bash
python -m scripts.make_refs --group benchmark
```

**Bước 3.** Chạy toàn bộ test (khoảng 7 phút), kết quả mong đợi là `98 passed`:

```bash
python -m pytest tests -q
```

Nếu bỏ qua bước 1–2, 28 test benchmark được đánh dấu `SKIPPED` (thiếu file tham chiếu) và 70 test còn lại vẫn pass.

### Output của lần chạy test cuối

Chạy ngày 28/11/2026 trên Windows, Python 3.13, sau khi làm đủ 3 bước trên:

```
$ python -m pytest tests -q
..................................................................................................        [100%]
98 passed in 411.49s (0:06:51)
```

So khớp thủ công một ca với SPMF:

```bash
java -jar tool/spmf.jar run FPGrowth_itemsets data/toy/toy_test1.txt ref.txt 60%
python -m scripts.compare_spmf out.txt ref.txt
```

```
Khớp hoàn toàn: 18/18 = 100.00%
Lệch support: 0
Thừa so với SPMF: 0
Thiếu so với SPMF: 0
```

## Chạy lại thực nghiệm và ứng dụng

Mọi tham số (CSDL, các mức minsup, seed) nằm trong [`src/config.py`](src/config.py). Kết quả ghi vào `data/output/exp/`, biểu đồ vào `docs/figures/`.

```bash
# Thực nghiệm
python -m scripts.exp_runtime        # thời gian, số tập phổ biến, đối chiếu SPMF (khoảng 7 phút)
python -m scripts.exp_scalability    # thời gian theo kích thước CSDL
python -m scripts.exp_memory         # bộ nhớ đỉnh
python -m scripts.exp_txlen          # ảnh hưởng của độ dài giao dịch
python -m scripts.exp_tree_stats     # cấu trúc FP-tree, chi phí dựng cây / khai thác
python -m scripts.plot_ch2           # vẽ biểu đồ

# Ứng dụng 1: phân tích giỏ hàng (Groceries)
python -m scripts.app1_basket        # top 10 luật theo lift
python -m scripts.app1_verify        # đối chiếu arules + null model
python -m scripts.app1_plot

# Ứng dụng 2: chuỗi DNA
python -m scripts.app2_explore       # số tập phổ biến theo minsup
python -m scripts.app2_check         # ngoại lệ quy tắc GT-AG
python -m scripts.app2_emerging      # emerging pattern
python -m scripts.app2_plot
```

Notebook demo chạy lại toàn bộ các phần trên ("Run all"). Riêng SPMF cần Java nên không chạy trên Colab; số liệu SPMF trong notebook đọc từ `data/output/exp/runtime.csv`.

## Tái lập kết quả

- Thuật toán xác định: khi hai item cùng support, item có mã nhỏ hơn đứng trước, nên thứ tự cây và kết quả luôn cố định.
- Mọi chỗ có ngẫu nhiên (cắt tập con, sinh dữ liệu tổng hợp, trộn dữ liệu cho null model) dùng **seed cố định** khai báo trong `src/config.py`.
- Mã hoá item dạng chữ gán số theo thứ tự đã sắp, nên cùng dữ liệu luôn cho cùng bảng mã.

## Cấu trúc thư mục

```
Frequent_Itemset/
├── README.md
├── requirements.txt
├── src/
│   ├── algorithm/
│   │   ├── fpgrowth.py         # bản tối ưu và giao diện dòng lệnh
│   │   └── fpgrowth_basic.py   # bản cơ bản (mốc so sánh)
│   ├── structures.py           # nút cây, dựng FP-tree, conditional FP-tree
│   ├── utils.py                # đọc/ghi SPMF, so sánh kết quả, encode/decode
│   ├── config.py               # CSDL, minsup, seed, đường dẫn
│   ├── rules.py                # sinh luật kết hợp (Ứng dụng 1)
│   ├── apps/basket.py          # đọc dữ liệu giỏ hàng (Ứng dụng 1)
│   └── app2_bio.py             # chuỗi DNA -> giao dịch (Ứng dụng 2)
├── tests/                      # test_correctness, test_benchmark, test_encode, test_rules, test_basket
├── scripts/                    # thực nghiệm, vẽ biểu đồ, hai ứng dụng, đối chiếu SPMF
├── data/                       # toy/, benchmark/, app1/, app2/, output/
├── notebooks/demo.ipynb        # demo chạy trên Google Colab
└── docs/                       # Report.pdf, figures/, references/
```

## Tài liệu tham khảo

1. J. Han, J. Pei, Y. Yin, R. Mao. *Mining Frequent Patterns without Candidate Generation: A Frequent-Pattern Tree Approach.* Data Mining and Knowledge Discovery, 8, 53–87, 2004.
2. P. Fournier-Viger et al. *SPMF: An Open-Source Data Mining Library.* https://www.philippe-fournier-viger.com/spmf/
3. R. Agrawal, R. Srikant. *Fast Algorithms for Mining Association Rules.* VLDB, 1994.
4. M. Hahsler, B. Grün, K. Hornik. *arules — A Computational Environment for Mining Association Rules and Frequent Item Sets.* Journal of Statistical Software, 14(15), 2005.
