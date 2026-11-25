# FP-Growth: Khai thác tập phổ biến (Group 23)

Cài đặt lại thuật toán **FP-Growth** (Han, Pei, Yin, Mao, 2004) bằng Python thuần, tự viết từ đầu dựa trên bài báo gốc, kèm tối ưu **single path (Lemma 3.2)**. Kết quả được kiểm chứng so với thư viện tham chiếu **SPMF**: khớp **100%** trên cả 28 ca benchmark. Cài đặt được dùng cho hai ứng dụng: phân tích giỏ hàng/log (Ứng dụng 1) và khai thác mẫu trong chuỗi DNA (Ứng dụng 2).

> Đồ án môn Khai phá dữ liệu, Bộ môn Khoa học máy tính.

## Thành viên

| Thành viên | Phụ trách |
|---|---|
| Trần Đình Khoa | Chương 1 (cài đặt), Chương 2 nửa B (bộ nhớ, độ dài giao dịch, so sánh SPMF, hướng tối ưu), Ứng dụng 2 |
| Lại Minh Thông | Chương 2 nửa A (dữ liệu, correctness, thời gian, số itemset, scalability), Ứng dụng 1 |

_(Sửa lại họ tên, MSSV và phân công cho đúng.)_

## Tài nguyên

- Demo notebook (Google Colab): _dán link public tại đây_
- Notebook trong repo: [`notebooks/demo.ipynb`](notebooks/demo.ipynb)
- Báo cáo: [`docs/Report.pdf`](docs/Report.pdf)
- Bài báo gốc: [`docs/references/fpgrowth_04.pdf`](docs/references/fpgrowth_04.pdf)
- Dữ liệu benchmark: cả bốn CSDL nằm trong `data/benchmark/`, xem mục [Dữ liệu benchmark](#dữ-liệu-benchmark)
- Dữ liệu Ứng dụng 1 (Groceries): `data/app1/groceries.csv`, nguồn và mốc kiểm chứng ghi trong [`data/app1/README.md`](data/app1/README.md)
- Dữ liệu Ứng dụng 2: `data/app2/`, xem mục [Ứng dụng 2](#ứng-dụng-2-khai-thác-mẫu-trong-chuỗi-dna)
- SPMF: https://www.philippe-fournier-viger.com/spmf/

## Yêu cầu môi trường

- Python **3.9 trở lên** (đã chạy trên Python 3.13).
- **Thuật toán** chỉ dùng **thư viện chuẩn** của Python (`argparse`, `itertools`, `math`...). Không dùng thư viện FIM có sẵn. Điều này đúng cho cả phần sinh luật kết hợp của chương 3 ([`src/rules.py`](src/rules.py)).
- `numpy`, `pandas`, `matplotlib` chỉ dùng cho **sinh dữ liệu tổng hợp, đọc CSV và vẽ biểu đồ** ở chương 2 và các ứng dụng, không dùng trong thuật toán.
- `pytest` chỉ cần để chạy kiểm thử.
- Java và `spmf.jar` chỉ cần khi muốn **tự đo lại** thời gian SPMF hoặc **tự sinh lại** file tham chiếu.
- Bản `spmf.jar` hiện tại trên trang SPMF **biên dịch cho Java 25**, bản trước đó (`spmf2.64.jar`) cần Java 21. Java 8 chạy không được, báo `UnsupportedClassVersionError`.

## Cài đặt

```bash
git clone https://github.com/KhoaTranFitus/Frequent_Itemset.git
cd Frequent_Itemset
pip install -r requirements.txt
```

> **Quan trọng:** mọi lệnh bên dưới phải chạy từ **thư mục gốc của repo**, vì đường dẫn dữ liệu là đường dẫn tương đối (`data/...`).

## Cách chạy

### Chạy thuật toán

```bash
python -m src.algorithm.fpgrowth <file_input> --minsup <0..1> --output <file_output>
```

| Tham số | Ý nghĩa |
|---|---|
| `input` | File giao dịch định dạng SPMF `.txt` |
| `--minsup` | Ngưỡng hỗ trợ **tương đối** trong khoảng (0, 1], ví dụ `0.4` là 40% |
| `--output` | File kết quả (mặc định `output.txt`) |

Ví dụ:

```bash
python -m src.algorithm.fpgrowth data/toy/toy_test1.txt --minsup 0.6 --output out.txt
```

Kết quả mong đợi: `5 giao dịch, min_count = 3, tìm được 18 tập phổ biến`.

Xem trợ giúp: `python -m src.algorithm.fpgrowth -h`.

### Định dạng dữ liệu (SPMF)

**Input:** mỗi dòng một giao dịch, item là số nguyên cách nhau bằng dấu cách.

```
1 3 4
2 3 5
1 2 3 5
```

**Output:** mỗi dòng một tập phổ biến, theo sau là support (số giao dịch, tuyệt đối).

```
1 3 #SUP: 2
2 3 5 #SUP: 2
```

**Đổi minsup:** thuật toán dùng support tuyệt đối, được tính từ minsup tương đối bằng

```
min_count = ceil(minsup * số_giao_dịch)
```

(có làm tròn `round(..., 9)` để tránh sai số số thực, giống cách SPMF làm tròn lên.)

### Dữ liệu có item dạng chữ

Định dạng SPMF yêu cầu item là số nguyên dương. Với dữ liệu có item là chữ (tên mặt hàng, sự kiện log, nucleotide…), dùng `encode` / `decode` trong `src/utils.py`:

```python
from src.utils import encode, decode, save_code
from src.algorithm.fpgrowth import fpgrowth

encoded, code = encode([["bread", "milk"], ["bread", "butter"]])   # chữ -> số, bảng mã cố định
result = decode(fpgrowth(encoded, 2), code)                        # số -> chữ
save_code(code, "code.json")                                        # lưu bảng mã để giải mã về sau
```

Bảng mã được gán theo thứ tự item đã sắp xếp, nên cùng dữ liệu luôn cho cùng bảng mã. `encode` **không** chuẩn hóa chữ: làm sạch dữ liệu (`strip`, `lower`…) ở bước tiền xử lý trước khi gọi.

## Demo notebook

[`notebooks/demo.ipynb`](notebooks/demo.ipynb) chạy được trên **Google Colab** và ở máy. Ô đầu tiên tự `git clone` repo khi chạy trên Colab và đưa thư mục làm việc về thư mục gốc repo.

| Phần | Nội dung |
|---|---|
| 0 | Cài đặt môi trường |
| 1 | Demo FP-Growth bằng dòng lệnh, test nhanh, bảng so khớp SPMF |
| 2 | Chương 2: chạy lại các thực nghiệm, vẽ biểu đồ |
| 3 | Ứng dụng 1 |
| 4 | Ứng dụng 2: khai thác mẫu trong chuỗi DNA |

SPMF cần Java 25 nên **không chạy trên Colab**; số liệu SPMF trong notebook đọc từ `data/output/exp/runtime.csv` đã đo ở máy của nhóm. Bộ test đầy đủ (khoảng 7 phút) để ở dạng comment trong notebook, kết quả lần chạy cuối ở mục [Kiểm thử](#kiểm-thử).

## Dữ liệu benchmark

Cả bốn CSDL benchmark **nằm sẵn trong `data/benchmark/`**, clone về là chạy được ngay, không phải tải gì thêm. Tổng khoảng 9 MB.

| CSDL | Giao dịch | Số item | Độ dài TB | Mật độ | Đặc điểm | Nguồn |
|---|---|---|---|---|---|---|
| Chess | 3.196 | 75 | 37,00 | 49,33% | dày đặc, itemset dài | UCI, qua FIMI |
| Mushroom | 8.416 | 119 | 23,00 | 19,33% | dày đặc, nhiều item | UCI, qua FIMI |
| Retail | 88.162 | 16.470 | 10,31 | 0,06% | thưa, dữ liệu thật | cửa hàng bán lẻ ở Bỉ, qua FIMI |
| T10I4D100K | 100.000 | 870 | 10,10 | 1,16% | tổng hợp, thưa | IBM Quest generator |

Các số trên do `src/utils.py` đọc trực tiếp từ file trong repo và khớp với bảng của [SPMF Datasets](https://www.philippe-fournier-viger.com/spmf/datasets.php), thư mục `publicdatasets/`, nơi tải cả bốn file.

**T10I4D100K là dữ liệu tổng hợp**, do IBM Quest Synthetic Data Generator sinh theo thủ tục trong Agrawal và Srikant (1994), không phải dữ liệu thật và không do nhóm sinh ra. Tên file là tham số sinh: `T10` độ dài giao dịch trung bình 10, `I4` độ dài trung bình của mẫu ẩn tiềm năng 4, `D100K` một trăm nghìn giao dịch. Đây đúng là CSDL mà bài báo FP-Growth dùng trong phần thực nghiệm (mục 5 của [`docs/references/fpgrowth_04.pdf`](docs/references/fpgrowth_04.pdf)), nên số liệu của nhóm so sánh được với bài báo gốc.

Danh sách minsup dùng cho thực nghiệm được chốt trong [`src/config.py`](src/config.py), mỗi CSDL 7 mức. **minsup giữa** (mức thứ 4) dùng cho thực nghiệm bộ nhớ.

| CSDL | minsup |
|---|---|
| Chess | 0,9 · 0,85 · 0,8 · **0,75** · 0,7 · 0,65 · 0,6 |
| Mushroom | 0,5 · 0,4 · 0,3 · **0,2** · 0,15 · 0,1 · 0,05 |
| Retail | 0,01 · 0,008 · 0,005 · **0,004** · 0,003 · 0,002 · 0,001 |
| T10I4D100K | 0,01 · 0,008 · 0,005 · **0,004** · 0,003 · 0,002 · 0,001 |

## Kiểm thử

```bash
# toàn bộ test (khoảng 7 phút khi có file tham chiếu SPMF)
python -m pytest -q

# test nhanh (vài giây): tính đúng trên CSDL nhỏ + encode/decode
python -m pytest -q tests/test_correctness.py tests/test_encode.py

# chỉ phần chương 3 (luật kết hợp, loader giỏ hàng) — không cần SPMF, chạy dưới 2 giây
python -m pytest tests/test_rules.py tests/test_basket.py -v

# chỉ benchmark (4 CSDL x 7 mức minsup), in kèm thời gian
python -m pytest tests/test_benchmark.py -v -s
```

- `test_correctness.py` kiểm tra **không cần SPMF**: số tập phổ biến tính tay, bản tối ưu giống bản cơ bản, ví dụ bài báo, xử lý item lặp và dòng trống.
- `test_encode.py` kiểm tra `encode` / `decode` / `save_code` / `load_code`: bảng mã đúng, tái lập được, đọc ghi file giữ nguyên kiểu item.
- `test_rules.py` và `test_basket.py` (chương 3) cũng **không cần SPMF**. Phần lớn test chạy trên CSDL 4 giao dịch viết thẳng trong file, mọi giá trị confidence và lift là phân số đẹp nên kiểm được bằng tay; phần còn lại đối chiếu với các giá trị đã công bố của bộ Groceries.
- Các test **so với SPMF** cần file tham chiếu trong `data/output/ref/`. Thư mục này **không nằm trong repo**, nên lần đầu chạy các test này sẽ bị `SKIPPED`. Muốn chạy đầy đủ, làm theo mục "So sánh với SPMF" bên dưới để sinh ref.
- `test_benchmark.py` lấy danh sách ca từ `src/config.py` (4 CSDL × 7 mức), chạy **cả bản cơ bản và bản tối ưu**, so với file tham chiếu SPMF, rồi ghi thời gian vào `data/output/benchmark_log.csv`. Mất khoảng 6 phút và cần ref.
- File `pytest.ini` đặt thư mục tạm của pytest là `.pytest_tmp/` trong repo, để tránh lỗi `PermissionError: [WinError 5]` khi pytest dọn thư mục Temp của Windows.

### Output của lần chạy test cuối cùng

Chạy ngày 21/11/2026, sau khi đã sinh đủ file ref bằng `python -m scripts.make_refs --group all`:

```
$ python -m pytest tests -q
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\PC\Downloads\24127127-local\Frequent_Itemset
plugins: anyio-4.11.0
collected 96 items

........................................................................ [ 75%]
........................                                                 [100%]

96 passed in 402.90s (0:06:42)
```

| File test | Số test | Nội dung |
|---|---|---|
| `test_correctness.py` | 23 | 7 ca toy: số tập phổ biến tính tay, basic == optimized, so với SPMF; ví dụ bài báo; item lặp và dòng trống |
| `test_benchmark.py` | 28 | 4 CSDL benchmark × 7 minsup: basic == optimized, khớp SPMF 100% |
| `test_encode.py` | 10 | mã hóa item dạng chữ sang số và giải mã ngược |
| `test_basket.py` | 9 | loader giỏ hàng, null model, mốc Groceries (9.835 giỏ, 169 món, support whole milk = 2513) |
| `test_rules.py` | 26 | luật kết hợp: giá trị tính tay, bất biến toán học, trường hợp biên, mốc Groceries (15 và 410 luật) |
| **Tổng** | **96** | |

Chạy trên máy mới clone về, chưa có file ref, thì 35 test so với SPMF bị `SKIPPED` còn 61 test kia vẫn phải xanh hết — và chỉ mất khoảng 1 giây vì phần lâu nhất (`test_benchmark.py`) nằm trong nhóm bị skip:

```
$ python -m pytest tests -q
.........ssssssssssssssssssssssssssss..............sssssss.............. [ 75%]
........................                                                 [100%]
61 passed, 35 skipped in 1.14s
```

## Thực nghiệm chương 2

Danh sách CSDL, minsup, seed và đường dẫn kết quả lấy từ [`src/config.py`](src/config.py), sửa một chỗ là mọi script đi theo.

```bash
# nửa A: thời gian + số itemset + correctness theo minsup (4 CSDL x 7 mức), khoảng 7 phút chưa tính SPMF
python -m scripts.exp_runtime

# nửa A: thời gian theo kích thước CSDL (Retail, cắt 10/25/50/75/100%)
python -m scripts.exp_scalability

# nửa B: bộ nhớ đỉnh bản cơ bản và bản tối ưu, tại minsup giữa (khoảng 1 phút)
python -m scripts.exp_memory

# nửa B: thời gian theo độ dài giao dịch, CSDL tổng hợp (khoảng 1 phút)
python -m scripts.exp_txlen

# vẽ toàn bộ biểu đồ chương 2 vào docs/figures/
python -m scripts.plot_ch2
```

| Script | CSV | Các cột |
|---|---|---|
| `exp_runtime.py` | `data/output/exp/runtime.csv` | `dataset, minsup, min_count, itemsets, t_basic_s, t_opt_s, t_spmf_s, match_pct` |
| `exp_scalability.py` | `data/output/exp/scalability.csv` | `dataset, fraction, transactions, minsup, itemsets, t_opt_s` |
| `exp_memory.py` | `data/output/exp/memory.csv` | `dataset, minsup, peak_basic_mb, peak_opt_mb` |
| `exp_txlen.py` | `data/output/exp/txlen.csv` | `avg_len, transactions, minsup, itemsets, t_opt_s` |

Các file CSV trong `data/output/exp/` **nằm trong repo** (biểu đồ chính thức vẽ từ đây); phần còn lại của `data/output/` thì không.

Vài điểm cần nắm khi đọc số liệu:

- `exp_runtime.py` lưu CSV **sau từng ca** và bỏ qua ca đã có, nên dừng giữa đường rồi chạy lại không mất phần đã làm. Muốn đo lại thì thêm `--force`: dòng cũ của ca đó được **thay**, mỗi cặp (dataset, minsup) luôn chỉ có một dòng.
- `--csv <file>` ghi ra file khác thay cho `runtime.csv`, ví dụ bản chạy nhẹ trong notebook: `python -m scripts.exp_runtime --runs 1 --skip-basic --skip-spmf --csv data/output/exp/runtime_colab.csv` (file này nằm trong `.gitignore`).
- Nó cũng **tự sinh file ref** khi chạy SPMF. Thiếu `tool/spmf.jar`, hoặc Java cũ hơn bản jar, thì hai cột `t_spmf_s`, `match_pct` để trống và phần còn lại vẫn đo được; script nói rõ lý do ở dòng cuối.
- **Thời gian SPMF** lấy từ dòng `Total time` do chính SPMF in ra, không tính thời gian khởi động JVM. Thời gian của nhóm chỉ tính phần thuật toán, không tính đọc file. Thời gian là **trung vị của 3 lần chạy**.
- `exp_scalability.py` trộn giao dịch một lần bằng `random.Random(42)` rồi lấy tiền tố, nên các tập con **lồng nhau** và cố định qua mọi lần chạy. minsup giữ ở dạng tương đối nên `min_count` giảm theo kích thước tập con.
- `exp_memory.py` đo bằng `tracemalloc`, chỉ tính phần thuật toán (dữ liệu đọc trước khi bắt đầu đo), mỗi bản đo 1 lần vì bộ nhớ không dao động giữa các lần chạy. Chạy riêng với đo thời gian vì `tracemalloc` làm chương trình chậm đi.
- `exp_txlen.py` sinh CSDL tổng hợp: 10.000 giao dịch, 200 item, minsup 0,05, seed 42; độ dài theo phân bố Poisson, item theo phân bố Zipf (item thứ k có xác suất tỉ lệ 1/k). Chỉ độ dài trung bình thay đổi (5 → 30).

## Chương 3 — Ứng dụng 1: phân tích giỏ hàng

Đề cho chọn một trong hai hướng cho Ứng dụng 1; nhóm chọn **hướng A — Market Basket Analysis**: từ các tập phổ biến do FP-Growth của nhóm sinh ra, sinh **luật kết hợp** thỏa minsup và minconf, lấy **top 10 luật theo lift** và giải thích ý nghĩa kinh doanh.

Toàn bộ kết quả do cài đặt của nhóm sinh ra. Phần sinh luật ([`src/rules.py`](src/rules.py)) chỉ dùng thư viện chuẩn và **không import gì từ `src.algorithm`** — nó chỉ tiêu thụ dict kết quả của `fpgrowth`, nên phân tầng `algorithm → structures → utils` không bị động tới.

### Dữ liệu

| CSDL | Vai trò | Quy mô |
|---|---|---|
| `data/app1/groceries.csv` | CSDL **chính** — item có tên đọc được nên mới diễn giải được ý nghĩa kinh doanh | 9.835 giỏ, 169 mặt hàng, giỏ dài trung bình 4,41 |
| `data/benchmark/retail.txt` | CSDL **phụ** — chạy ở quy mô thật, nối lại số liệu chương 2 | 88.162 giỏ, 16.470 mặt hàng |

Retail đã bị ẩn danh thành số nên chỉ dùng cho phân tích định lượng. Nguồn của Groceries ghi trong [`data/app1/README.md`](data/app1/README.md).

### Lệnh chạy

```bash
# phân tích đầy đủ, in bảng top 10 theo lift (mặc định minsup 0,01, minconf 0,3)
python -m scripts.app1_basket

# ca kiểm chứng: phải ra đúng 15 luật
python -m scripts.app1_basket --minsup 0.01 --minconf 0.5

# xếp theo tiêu chí khác, hoặc bỏ giới hạn số món bên phải luật
python -m scripts.app1_basket --top 20 --sort-by leverage
python -m scripts.app1_basket --max-consequent 0

# CSDL lớn
python -m scripts.app1_basket --dataset retail

# quét ngưỡng + null model
python -m scripts.app1_curves
python -m scripts.app1_curves --dataset retail
```

| Script | CSV | Các cột |
|---|---|---|
| `app1_basket.py` | `data/output/app1/rules_<csdl>_<minsup>_<minconf>.csv` | `antecedent, consequent, n_antecedent, n_consequent, support_count, support, confidence, lift, leverage` |
| `app1_basket.py` | `data/output/app1/itemsets_<csdl>_<minsup>.txt` | tập phổ biến, định dạng SPMF |
| `app1_basket.py` | `data/output/app1/code_<csdl>.csv` | `item, code` — bảng mã, chỉ sinh cho CSDL có item dạng tên |
| `app1_curves.py` | `data/output/app1/curves_<csdl>.csv` | `dataset, minsup, minconf, min_count, itemsets, rules, max_lift, median_lift, max_leverage` |
| `app1_curves.py` | `data/output/app1/nullmodel_<csdl>.csv` | `dataset, minsup, minconf, kind, replicate, itemsets, rules, max_lift, rules_lift_gt_1_5` |

Trong CSV luật, các item của một vế ghép bằng dấu `|` chứ không phải dấu phẩy, vì dấu phẩy là dấu phân cột và tên món Groceries có dấu cách. `itemsets_*.txt` ghi từ dict **đã mã hóa** (item là số) để đúng định dạng SPMF; tra ngược tên món bằng `code_<csdl>.csv`.

### Bốn mốc kiểm chứng

Nhóm đối chiếu **kết quả số** với các giá trị đã được công bố cùng bộ Groceries. Không đọc, không chạy, không dịch mã nguồn của bất kỳ cài đặt nào.

| Mốc | Nhóm tính được | Giá trị công bố |
|---|---|---|
| support(`whole milk`) | 2513 / 9835 = 0,25552 | 0,25552 |
| `{other vegetables, yogurt} → {whole milk}` | sup 0,02227 · conf 0,51288 · lift 2,00723 | 0,02226 · 0,5128 · 2,0072 |
| số luật tại minsup 0,01 và minconf 0,5 | 15 | 15 |
| số luật tại minsup 0,001 và minconf 0,8 | 410 | 410 |

Khớp ở cả hai đầu của dải tham số (333 và 13.492 tập phổ biến) nên khó mà đúng do may. Bốn mốc này được khẳng định trong `tests/test_rules.py` và `tests/test_basket.py`.

### Top 10 luật theo lift (Groceries, minsup 0,01, minconf 0,3)

| # | Luật | support | conf | lift | leverage |
|---|---|---|---|---|---|
| 1 | {citrus fruit, other vegetables} → {root vegetables} | 0,0104 | 0,359 | 3,295 | 0,00722 |
| 2 | {other vegetables, tropical fruit} → {root vegetables} | 0,0123 | 0,343 | 3,145 | 0,00839 |
| 3 | {beef} → {root vegetables} | 0,0174 | 0,331 | 3,040 | 0,01167 |
| 4 | {citrus fruit, root vegetables} → {other vegetables} | 0,0104 | 0,586 | 3,030 | 0,00695 |
| 5 | {root vegetables, tropical fruit} → {other vegetables} | 0,0123 | 0,585 | 3,021 | 0,00823 |
| 6 | {other vegetables, whole milk} → {root vegetables} | 0,0232 | 0,310 | 2,842 | 0,01503 |
| 7 | {curd, whole milk} → {yogurt} | 0,0101 | 0,385 | 2,761 | 0,00642 |
| 8 | {rolls/buns, root vegetables} → {other vegetables} | 0,0122 | 0,502 | 2,595 | 0,00750 |
| 9 | {root vegetables, yogurt} → {other vegetables} | 0,0129 | 0,500 | 2,584 | 0,00792 |
| 10 | {tropical fruit, whole milk} → {yogurt} | 0,0151 | 0,358 | 2,568 | 0,00925 |

Diễn giải đầy đủ nằm trong [`notebooks/app1_basket.ipynb`](notebooks/app1_basket.ipynb), mục 5.

### Null model

Để kiểm xem các luật trên có phải chỉ là hệ quả của việc vài món bán rất chạy hay không, `app1_curves.py` dựng một CSDL đối chứng bằng cách **trộn món giữa các giỏ** nhưng giữ **chính xác** tần suất từng món và độ dài từng giỏ (seed 42), rồi chạy lại đúng `fpgrowth` đó.

| | số luật | lift lớn nhất | số luật lift > 1,5 |
|---|---|---|---|
| Groceries, dữ liệu thật | 125 | 3,295 | 108 |
| Groceries, trung vị 5 lần trộn | 11 | 1,733 | 5 |
| **tỉ số** | **11,4×** | 1,9× | **21,6×** |
| Retail, dữ liệu thật | 6.365 | 338,34 | 1.506 |
| Retail, trung vị 5 lần trộn | 4.177 | 2,68 | 2.175 |
| **tỉ số** | 1,5× | **126,2×** | **0,69×** |

Trên Groceries kết luận rõ ràng: dữ liệu thật sinh ra gấp hơn 20 lần số luật có lift mạnh, nên các mẫu tìm được phản ánh hành vi mua cùng nhau thật.

Trên Retail thì **không**, và đây là một **kết quả âm đáng báo cáo**: số luật gần như không giảm, và số luật có lift > 1,5 của dữ liệu trộn còn *nhiều hơn* dữ liệu thật. CSDL này quá thưa (độ dày 0,0006) nên hai món ngẫu nhiên rơi cùng giỏ cũng đủ vượt lift 1,5 — tức ngưỡng đó không chứng minh được gì. Chỉ phần đỉnh của phân bố lift mới tách ra. Vì vậy `compare_real_vs_shuffled` cố ý in cả ba tỉ số và chỉ ra thống kê nào tách tốt nhất, thay vì viết sẵn một câu kết luận.

## So sánh với SPMF

Cần **Java 25 trở lên** (kiểm tra bằng `java -version`) và file `spmf.jar` đặt vào thư mục `tool/` (tải ở trang SPMF, mục Download; file không nằm trong repo vì nặng, khoảng 15 MB).

Trang SPMF chỉ còn host bản mới nhất và bản ngay trước đó, nên không tải được bản cũ chạy trên Java 8. Nếu chỉ có Java 21 thì dùng `spmf2.64.jar` và đổi tên thành `tool/spmf.jar`.

Máy có nhiều bản Java và `java` trong PATH lại là bản cũ thì chỉ rõ bản muốn dùng bằng biến `JAVA`:

```bash
JAVA="C:/Program Files/Java/jdk-25.0.5.0.3/bin/java.exe" python -m scripts.make_refs --group toy
```

### Cách 1: sinh toàn bộ ref rồi chạy test (khuyên dùng)

```bash
# sinh ref cho các CSDL toy (nhanh)
python -m scripts.make_refs --group toy

# sinh thêm ref cho 4 CSDL benchmark
python -m scripts.make_refs --group benchmark

# chạy test, lúc này các test so với SPMF sẽ chạy thật
python -m pytest -q
```

Ref được ghi vào `data/output/ref/` theo tên `<tên>_<minsup>.txt` (ví dụ `test1_0.6.txt`, `chess_0.7.txt`).

### Cách 2: so khớp thủ công một ca

```bash
# 1. chạy cài đặt của nhóm
python -m src.algorithm.fpgrowth data/toy/toy_test1.txt --minsup 0.6 --output out.txt

# 2. chạy SPMF
java -jar tool/spmf.jar run FPGrowth_itemsets data/toy/toy_test1.txt ref.txt 60%

# 3. so sánh hai file kết quả
python -m scripts.compare_spmf out.txt ref.txt
```

Kết quả mong đợi:

```
Khớp hoàn toàn: 18/18 = 100.00%
Lệch support: 0
Thừa so với SPMF: 0
Thiếu so với SPMF: 0
```

Ý nghĩa các dòng: **khớp hoàn toàn** là cùng itemset và cùng support; **lệch support** là cùng itemset nhưng khác support; **thừa** là có ở cài đặt của nhóm mà SPMF không có; **thiếu** là SPMF có mà cài đặt của nhóm không có.

> Lưu ý: SPMF dùng minsup tương đối và làm tròn lên (`ceil`), giống cách tính `min_count` của nhóm, nên hai bên luôn dùng cùng ngưỡng tuyệt đối.

Lưu ý: SPMF chỉ nhận item là số nguyên; file `data/toy/toy.txt` (ví dụ Table 1 của bài báo, item là chữ cái) chỉ dùng cho cài đặt của nhóm, không chạy SPMF trên file này được.

## Ứng dụng 2: Khai thác mẫu trong chuỗi DNA

**Dữ liệu:** UCI *Molecular Biology (Splice-junction Gene Sequences)*, đặt trong `data/app2/` (`splice.data`, mô tả trong `splice.names`). Gồm 3.190 chuỗi DNA dài 60 nucleotide, nhãn **EI** (767 mẫu, donor: ranh giới exon→intron), **IE** (768 mẫu, acceptor: ranh giới intron→exon) và **N** (1.655 mẫu, không có ranh giới).

**Biến chuỗi thành giao dịch:** mỗi chuỗi là một giao dịch; mỗi item có dạng `P<vị trí>=<nucleotide>`, vị trí tính từ −30 đến +30 so với ranh giới (không có vị trí 0), ví dụ `P+1=G`. Ký tự không chắc chắn (D, N, S, R theo mã IUPAC) bị bỏ qua. Item được `encode` sang số bằng **một bảng mã chung** cho cả 3 nhóm, lưu ở `data/app2/code.json`.

```bash
# bước 2: số itemset theo minsup cho từng nhóm EI / IE / N, top itemset
python -m scripts.app2_explore

# ngoại lệ của quy tắc GT-AG, item đơn của IE ở minsup thấp
python -m scripts.app2_check

# emerging pattern của EI và IE so với N (growth rate)
python -m scripts.app2_emerging

# heatmap tần suất nucleotide theo vị trí, biểu đồ top emerging pattern
python -m scripts.app2_plot
```

**Kết quả chính** (minsup 0,5, chạy FP-Growth riêng từng nhóm):

- FP-Growth tự tìm ra **quy tắc GT–AG**: `{P+1=G, P+2=T}` có trong **99,0%** mẫu EI, `{P-2=A, P-1=G}` có trong **99,5%** mẫu IE.
- Nhóm N không có itemset nào kể cả ở minsup 0,3: nhóm đối chứng.
- Pattern đặc trưng nhất của donor `{P+1=G, P+2=T, P+5=G}` phổ biến trong EI gấp khoảng 94 lần so với N; acceptor có growth cao nhất chỉ 34, do tín hiệu polypyrimidine tract bị chia giữa C và T.

Diễn giải chi tiết ở Phần 4 của notebook và trong báo cáo.

## Cấu trúc thư mục

```
Frequent_Itemset/
├── README.md
├── requirements.txt
├── pytest.ini                # thư mục tạm của pytest (.pytest_tmp/)
├── src/
│   ├── __init__.py
│   ├── utils.py              # đọc/ghi file SPMF, đếm support, sắp xếp giao dịch, so sánh kết quả, encode/decode item
│   ├── config.py             # CSDL benchmark, danh sách minsup, seed, đường dẫn kết quả, to_min_count, tham số Ứng dụng 1
│   ├── structures.py         # FPNode, dựng FP-tree, prefix path, conditional FP-tree
│   ├── rules.py              # sinh luật kết hợp: support, confidence, lift, leverage (chương 3)
│   ├── app2_bio.py           # Ứng dụng 2: đọc dữ liệu splice, chuỗi DNA -> giao dịch, growth rate
│   ├── algorithm/
│   │   ├── __init__.py
│   │   ├── fpgrowth.py       # FP-Growth + tối ưu single path (bản chính) và CLI
│   │   └── fpgrowth_basic.py # bản cơ bản, không tối ưu (mốc so sánh)
│   └── apps/
│       ├── __init__.py
│       └── basket.py         # đọc dữ liệu giỏ hàng dạng chữ, thống kê, null model (chương 3)
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # bật UTF-8 cho output của pytest -s
│   ├── test_correctness.py   # đúng đắn trên CSDL nhỏ, so với SPMF
│   ├── test_encode.py        # mã hóa item dạng chữ sang số và giải mã ngược
│   ├── test_basket.py        # loader giỏ hàng, null model, mốc Groceries
│   ├── test_rules.py         # luật kết hợp: giá trị tính tay, bất biến, mốc Groceries
│   └── test_benchmark.py     # 4 CSDL x 7 minsup: đúng đắn + thời gian basic vs optimized
├── scripts/
│   ├── __init__.py
│   ├── make_refs.py          # chạy SPMF để sinh file tham chiếu
│   ├── compare_spmf.py       # so sánh 2 file kết quả
│   ├── run_toy_compare.py    # so bản basic và optimized trên các CSDL toy
│   ├── exp_runtime.py        # chương 2: thời gian, số itemset, correctness theo minsup
│   ├── exp_scalability.py    # chương 2: thời gian theo kích thước CSDL
│   ├── exp_memory.py         # chương 2: bộ nhớ đỉnh basic vs optimized
│   ├── exp_txlen.py          # chương 2: thời gian theo độ dài giao dịch (CSDL tổng hợp)
│   ├── plot_ch2.py           # vẽ toàn bộ biểu đồ chương 2
│   ├── app1_basket.py        # Ứng dụng 1: phân tích giỏ hàng đầu-cuối, bảng top theo lift
│   ├── app1_curves.py        # Ứng dụng 1: quét ngưỡng và null model
│   ├── app2_explore.py       # Ứng dụng 2: chọn minsup, top itemset
│   ├── app2_check.py         # Ứng dụng 2: ngoại lệ GT-AG, item đơn của IE
│   ├── app2_emerging.py      # Ứng dụng 2: emerging pattern so với N
│   └── app2_plot.py          # Ứng dụng 2: heatmap vị trí, biểu đồ emerging pattern
├── data/
│   ├── toy/                  # CSDL nhỏ để kiểm thử nhanh (toy_test1..4)
│   ├── benchmark/            # chess.txt, mushroom.txt, retail.txt, T10I4D100K.txt
│   ├── app1/                 # groceries.csv + README ghi nguồn (Ứng dụng 1)
│   ├── app2/                 # dữ liệu splice-junction (UCI) và bảng mã code.json
│   └── output/
│       ├── exp/              # CSV số liệu thực nghiệm chương 2 (nằm trong repo)
│       ├── ref/              # KHÔNG nằm trong repo: tham chiếu do SPMF sinh ra
│       ├── mine/             # KHÔNG nằm trong repo: kết quả của nhóm
│       ├── app1/             # KHÔNG nằm trong repo: CSV luật kết hợp và null model (chương 3)
│       └── benchmark_log.csv # KHÔNG nằm trong repo: thời gian đo được (test_benchmark.py)
├── notebooks/
│   ├── demo.ipynb            # demo chạy trên Google Colab (ghép ở giai đoạn cuối)
│   └── app1_basket.ipynb     # Ứng dụng 1: phân tích giỏ hàng, chạy sạch đầu-cuối
├── docs/
│   ├── Report.pdf            # báo cáo
│   ├── figures/              # biểu đồ chương 2 và Ứng dụng 2
│   ├── tasks/                # phân công công việc
│   └── references/
│       └── fpgrowth_04.pdf   # bài báo gốc
└── tool/
    └── spmf.jar              # tự tải về, không nằm trong repo
```

## Tóm tắt cài đặt

FP-Growth gồm 3 giai đoạn, ứng với các hàm trong mã nguồn:

| Giai đoạn | Hàm | Ý tưởng |
|---|---|---|
| 1. Quét lần 1 | `find_frequent_items` | Đếm support từng item, giữ item có support ≥ `min_count`. Mỗi giao dịch đếm item **một lần** (dùng `set`). |
| 2. Dựng FP-tree | `order_transaction`, `build_tree`, `insert_transaction` | Lọc và sắp item theo support giảm dần (bằng nhau thì theo tên để thứ tự cố định), chèn vào cây prefix. Các giao dịch chung tiền tố dùng chung đường đi. |
| 3. Khai thác | `get_prefix_paths`, `build_conditional_tree`, `mine_tree` | Với mỗi item (từ ít phổ biến nhất), lấy conditional pattern base, dựng conditional FP-tree, đệ quy. Không sinh candidate. |

### Tối ưu single path (Lemma 3.2)

Khi một (conditional) FP-tree chỉ có **một nhánh**, mọi tổ hợp khác rỗng của các item trên nhánh đều là tập phổ biến, với support bằng support nhỏ nhất trong tổ hợp. Cài đặt liệt kê thẳng các tổ hợp (`get_single_path`, `add_single_path`) thay vì dựng thêm conditional tree cho từng item.

## Kết quả thực nghiệm

Máy: Windows, Python 3.13. Thời gian là **trung vị của 3 lần chạy**, chỉ tính phần thuật toán. Số liệu đầy đủ trong `data/output/exp/`, biểu đồ trong `docs/figures/`.

**Tính đúng đắn:** khớp SPMF **100%** (cùng itemset, cùng support) trên cả **28 ca** (4 CSDL × 7 mức minsup).

**Thời gian tại minsup thấp nhất** của mỗi CSDL:

| CSDL | minsup | Số tập phổ biến | Bản cơ bản (s) | Bản tối ưu (s) | SPMF (s) |
|---|---|---|---|---|---|
| Chess | 0,6 | 254.944 | 1,890 | 1,554 | 0,506 |
| Mushroom | 0,05 | 4.137.547 | 28,246 | 12,336 | 1,385 |
| Retail | 0,001 | 7.589 | 3,855 | 3,671 | 0,955 |
| T10I4D100K | 0,001 | 27.532 | 6,814 | 6,645 | 1,255 |

**Bộ nhớ đỉnh tại minsup giữa:**

| CSDL | Bản cơ bản (MB) | Bản tối ưu (MB) | Thay đổi |
|---|---|---|---|
| Chess | 4,20 | 3,15 | −25,0% |
| Mushroom | 10,66 | 8,37 | −21,5% |
| Retail | 39,91 | 39,82 | −0,2% |
| T10I4D100K | 204,63 | 204,66 | ≈ 0% |

Nhận xét ngắn:

- Tối ưu single path có hiệu quả trên **dữ liệu dày**: nhanh hơn bản cơ bản tới 3,5 lần (Mushroom 0,1) và giảm 21–25% bộ nhớ. Trên **dữ liệu thưa** gần như không đổi, vì đỉnh bộ nhớ và thời gian chủ yếu nằm ở FP-tree gốc.
- Cài đặt Python chậm hơn SPMF (Java) khoảng **3–5 lần** ở minsup thấp, tới gần **9 lần** với Mushroom 0,05 (4,1 triệu tập phổ biến).
- Độ dài giao dịch tăng 6 lần (5 → 30) làm thời gian tăng khoảng 180 lần: thời gian tăng **phi tuyến** theo độ dài giao dịch.
- Thời gian tăng gần **tuyến tính** theo số giao dịch (Retail, 10% → 100%).
- Thời gian đo có dao động giữa các lần chạy (tới khoảng ±40% ở một số ca), nên chỉ nên so sánh xu hướng và chênh lệch lớn.

Phân tích chi tiết và các hướng tối ưu tiếp theo ở chương 2 của báo cáo.

## Tái lập kết quả

- Thuật toán xác định (deterministic): không dùng số ngẫu nhiên, thứ tự item luôn cố định nhờ tiêu chí phụ khi support bằng nhau.
- Mọi chỗ có ngẫu nhiên (cắt tập con, sinh dữ liệu tổng hợp) dùng **seed cố định 42** (`SEED` trong `src/config.py`).
- `encode` gán số theo thứ tự item đã sắp, nên cùng dữ liệu luôn cho cùng bảng mã.
- Toàn bộ dữ liệu benchmark tải từ trang SPMF Datasets, xem mục [Dữ liệu benchmark](#dữ-liệu-benchmark). Lưu ý bản Mushroom dùng có **8.416 giao dịch**, đúng bằng con số SPMF công bố; con số 8.124 hay gặp là của bản UCI gốc.
- Muốn chạy lại toàn bộ benchmark: `python -m pytest tests/test_benchmark.py -v -s`.
- Phần chương 3 có hai chỗ ngẫu nhiên (trộn giỏ cho null model), cả hai đều dùng `SEED = 42` trong [`src/config.py`](src/config.py); mọi ngưỡng minsup/minconf cũng chốt ở đó. Chạy lại Ứng dụng 1: `python -m scripts.app1_basket` rồi `python -m scripts.app1_curves`.
- Notebook [`notebooks/app1_basket.ipynb`](notebooks/app1_basket.ipynb) chạy được từ đầu tới cuối sau khi Restart runtime, không phụ thuộc `data/output/` (tự tính lại số liệu tại chỗ). Ô đầu tự nhận biết đang chạy trên Colab hay trên máy cá nhân.
- Chạy lại toàn bộ: các lệnh ở mục [Thực nghiệm chương 2](#thực-nghiệm-chương-2), [Ứng dụng 1](#chương-3--ứng-dụng-1-phân-tích-giỏ-hàng) và [Ứng dụng 2](#ứng-dụng-2-khai-thác-mẫu-trong-chuỗi-dna), hoặc "Run all" trong notebook.

## Xử lý sự cố thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | Chạy không đúng thư mục hoặc không dùng `-m` | Đứng ở thư mục gốc và dùng `python -m ...` |
| `FileNotFoundError` khi đọc dữ liệu | Sai đường dẫn tương đối | Chạy từ thư mục gốc |
| Test bị `SKIPPED` | Chưa có file ref (`data/output/ref/` không nằm trong repo) | Chạy `python -m scripts.make_refs --group toy` (và `--group benchmark`) |
| `PermissionError: [WinError 5] Access is denied` khi chạy pytest | Windows chặn pytest dọn thư mục Temp | Đảm bảo có `pytest.ini` ở thư mục gốc; nếu vẫn lỗi, xóa thư mục `.pytest_tmp` rồi chạy lại |
| `'head' is not recognized` | Lệnh Linux, không có trên cmd của Windows | Dùng lệnh Python tương đương |
| `'java' is not recognized` | Chưa cài Java | Cài JDK/JRE rồi mở terminal mới |
| `UnsupportedClassVersionError ... class file version 69.0` | Java trên máy cũ hơn bản `spmf.jar` đang dùng (69 là Java 25, 65 là Java 21, 52 là Java 8) | Cài Java 25 trở lên, hoặc dùng bản `spmf.jar` cũ hơn khớp với Java đang có |
| `NumberFormatException: For input string` khi chạy SPMF | File input có item không phải số nguyên | SPMF chỉ nhận số nguyên; dùng `encode` hoặc file toy dạng số |
| `Unable to access jarfile spmf.jar` | Chưa có `spmf.jar` | Tải về và đặt vào `tool/` |
| `error: --minsup phải nằm trong khoảng (0, 1]` | Giá trị minsup không hợp lệ | Dùng minsup tương đối, ví dụ `0.4` |
| `ValueError: ... chuỗi dài 61, phải là 60` (Ứng dụng 2) | File `splice.data` bị sửa nhầm | Khôi phục bằng `git checkout -- data/app2/splice.data` |

## Tài liệu tham khảo

1. J. Han, J. Pei, Y. Yin, R. Mao. *Mining Frequent Patterns without Candidate Generation: A Frequent-Pattern Tree Approach.* Data Mining and Knowledge Discovery, 8, 53–87, 2004.
2. P. Fournier-Viger et al. *SPMF: An Open-Source Data Mining Library.* https://www.philippe-fournier-viger.com/spmf/
3. R. Agrawal, R. Srikant. *Fast Algorithms for Mining Association Rules.* VLDB 1994. — định nghĩa luật kết hợp, support và confidence.
4. S. Brin, R. Motwani, J. D. Ullman, S. Tsur. *Dynamic Itemset Counting and Implication Rules for Market Basket Data.* SIGMOD 1997. — lift (interest).
5. M. Hahsler, B. Grün, K. Hornik. *arules — A Computational Environment for Mining Association Rules and Frequent Item Sets.* Journal of Statistical Software, 14(15), 2005. — nguồn dữ liệu Groceries và các giá trị số dùng để kiểm chứng (không phải nguồn mã nguồn).
6. P.-N. Tan, M. Steinbach, V. Kumar. *Introduction to Data Mining.* — chương về interestingness measures (lift, leverage, conviction).
7. G. Grahne, J. Zhu. *Efficiently Using Prefix-trees in Mining Frequent Itemsets.* Proc. FIMI'03, 2003.
8. J. Pei, J. Han, H. Lu, S. Nishio, S. Tang, D. Yang. *H-Mine: Hyper-Structure Mining of Frequent Patterns in Large Databases.* Proc. IEEE ICDM, 2001.
9. G. Dong, J. Li. *Efficient Mining of Emerging Patterns: Discovering Trends and Differences.* Proc. KDD'99, 1999.
10. M. Burset, I. A. Seledtsov, V. V. Solovyev. *Analysis of canonical and non-canonical mammalian splice sites.* Nucleic Acids Research, 28(21), 2000.
11. G. Towell, M. Noordewier, J. Shavlik. *Molecular Biology (Splice-junction Gene Sequences).* UCI Machine Learning Repository, 1992.