# FP-Growth: Khai thác tập phổ biến (Group 23)

Cài đặt lại thuật toán **FP-Growth** (Han, Pei, Yin, Mao, 2004) bằng Python thuần, tự viết từ đầu dựa trên bài báo gốc, kèm tối ưu **single path (Lemma 3.2)**. Kết quả được kiểm chứng so với thư viện tham chiếu **SPMF**.

> Đồ án môn Khai phá dữ liệu, Bộ môn Khoa học máy tính.


## Tài nguyên

- Demo notebook (Google Colab): _dán link public tại đây_
- Báo cáo: [`docs/Report.pdf`](docs/Report.pdf)
- Bài báo gốc: [`docs/references/fpgrowth_04.pdf`](docs/references/fpgrowth_04.pdf)
- Dữ liệu benchmark: xem mục [Dữ liệu benchmark](#dữ-liệu-benchmark) — ba CSDL nằm trong repo, T10I4D100K tự tải một lệnh
- SPMF: https://www.philippe-fournier-viger.com/spmf/

## Yêu cầu môi trường

- Python **3.9 trở lên** (đã chạy trên Python 3.13).
- Thuật toán chỉ dùng **thư viện chuẩn** của Python (`argparse`, `itertools`, `math`...). Không dùng thư viện FIM có sẵn.
- `pytest` chỉ cần để chạy kiểm thử.
- Java và `spmf.jar` chỉ cần khi muốn **tự sinh lại** file tham chiếu. Chạy test với ref có sẵn thì không cần.

## Cài đặt

```bash
git clone <link-repo-cua-nhom>
cd <ten-thu-muc-repo>
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

## Dữ liệu benchmark

Bốn CSDL benchmark đều tải từ [SPMF Datasets](https://www.philippe-fournier-viger.com/spmf/datasets.php), thư mục `publicdatasets/`.

Chess, Mushroom và Retail nằm sẵn trong `data/benchmark/`. **T10I4D100K không nằm trong repo**, phải tự tải một lần trước khi chạy thực nghiệm:

```bash
curl -o data/benchmark/T10I4D100K.txt https://www.philippe-fournier-viger.com/spmf/publicdatasets/T10I4D100K.txt
```

File khoảng 3,8 MB. Thiếu nó thì các script thực nghiệm bỏ qua CSDL này và in `[bỏ qua] thiếu dữ liệu`, phần còn lại vẫn chạy.

| CSDL | Giao dịch | Số item | Độ dài TB | Mật độ | Đặc điểm |
|---|---|---|---|---|---|
| Chess | 3.196 | 75 | 37,00 | 49,33% | dày đặc, itemset dài |
| Mushroom | 8.416 | 119 | 23,00 | 19,33% | dày đặc, nhiều item |
| Retail | 88.162 | 16.470 | 10,31 | 0,06% | thưa, dữ liệu thật |
| T10I4D100K | 100.000 | 870 | 10,10 | 1,16% | tổng hợp, thưa |

Các số trên do `src/utils.py` đọc trực tiếp từ file trong repo và khớp với bảng của SPMF.

Danh sách minsup dùng cho thực nghiệm được chốt trong [`src/config.py`](src/config.py), mỗi CSDL 7 mức:

| CSDL | minsup |
|---|---|
| Chess | 0,9 · 0,85 · 0,8 · 0,75 · 0,7 · 0,65 · 0,6 |
| Mushroom | 0,5 · 0,4 · 0,3 · 0,2 · 0,15 · 0,1 · 0,05 |
| Retail | 0,01 · 0,008 · 0,005 · 0,004 · 0,003 · 0,002 · 0,001 |
| T10I4D100K | 0,01 · 0,008 · 0,005 · 0,004 · 0,003 · 0,002 · 0,001 |

## Kiểm thử

```bash
# toàn bộ test
python -m pytest tests -v

# chỉ benchmark (Mushroom, Chess), in kèm thời gian
python -m pytest tests/test_benchmark.py -v -s

# chỉ kiểm tra tính đúng trên các CSDL nhỏ
python -m pytest tests/test_correctness.py -v
```

- `test_correctness.py` kiểm tra **không cần SPMF**: số tập phổ biến tính tay, bản tối ưu giống bản cơ bản, ví dụ bài báo, xử lý item lặp và dòng trống.
- Các test **so với SPMF** cần file tham chiếu trong `data/output/ref/`. Thư mục `data/output/` **không nằm trong repo**, nên lần đầu chạy các test này sẽ bị `SKIPPED`. Muốn chạy đầy đủ, làm theo mục "So sánh với SPMF" bên dưới để sinh ref.
- `test_benchmark.py` chạy **cả bản cơ bản và bản tối ưu** trên Mushroom, Chess, kiểm tra hai bản cho kết quả giống nhau, rồi ghi thời gian vào `data/output/benchmark_log.csv`. Mất khoảng 4 phút và cần ref.

## So sánh với SPMF

Cần **Java** (kiểm tra bằng `java -version`) và file `spmf.jar` đặt vào thư mục `tool/` (tải ở trang SPMF, mục Download; file không nằm trong repo vì nặng).

### Cách 1: sinh toàn bộ ref rồi chạy test (khuyên dùng)

```bash
# sinh ref cho các CSDL toy (nhanh)
python -m scripts.make_refs --group toy

# sinh thêm ref cho Mushroom, Chess (vài giây đến vài chục giây)
python -m scripts.make_refs --group benchmark

# chạy test, lúc này các test so với SPMF sẽ chạy thật
python -m pytest tests -v
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

## Cấu trúc thư mục

```
Group_23/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── utils.py              # đọc/ghi file SPMF, đếm support, sắp xếp giao dịch, so sánh kết quả, encode/decode item
│   ├── config.py             # CSDL benchmark, danh sách minsup, đường dẫn kết quả, to_min_count
│   ├── structures.py         # FPNode, dựng FP-tree, prefix path, conditional FP-tree
│   └── algorithm/
│       ├── __init__.py
│       ├── fpgrowth.py       # FP-Growth + tối ưu single path (bản chính) và CLI
│       └── fpgrowth_basic.py # bản cơ bản, không tối ưu (mốc so sánh)
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # bật UTF-8 cho output của pytest -s
│   ├── test_correctness.py   # đúng đắn trên CSDL nhỏ, so với SPMF
│   ├── test_encode.py        # mã hóa item dạng chữ sang số và giải mã ngược
│   └── test_benchmark.py     # Mushroom, Chess: đúng đắn + thời gian basic vs optimized
├── scripts/
│   ├── __init__.py
│   ├── make_refs.py          # chạy SPMF để sinh file tham chiếu
│   ├── compare_spmf.py       # so sánh 2 file kết quả
│   └── run_toy_compare.py    # so bản basic và optimized trên các CSDL toy
├── data/
│   ├── toy/                  # CSDL nhỏ để kiểm thử nhanh (toy_test1..4)
│   ├── benchmark/            # chess.txt, mushroom.txt, retail.txt (T10I4D100K.txt tự tải)
│   └── output/               # KHÔNG nằm trong repo, được sinh khi chạy
│       ├── ref/              # kết quả tham chiếu do SPMF sinh ra (scripts/make_refs.py)
│       ├── mine/             # kết quả của nhóm
│       └── benchmark_log.csv # thời gian đo được (test_benchmark.py)
├── notebooks/
│   └── demo.ipynb            # demo chạy trên Google Colab
├── docs/
│   ├── Report.pdf            # báo cáo
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

Máy: Windows, Python 3.13.9. Thời gian là **trung vị của 3 lần chạy**, chỉ tính phần thuật toán (không tính đọc file).

**Tính đúng đắn:** khớp SPMF **100%** (cùng itemset, cùng support) trên toàn bộ các ca bên dưới.

| CSDL | minsup | Số tập phổ biến | Bản cơ bản (s) | Bản tối ưu (s) | Tăng tốc |
|---|---|---|---|---|---|
| Mushroom | 0.2 | 53.337 | 0.368 | 0.227 | x1.62 |
| Mushroom | 0.1 | 600.817 | 3.191 | 1.264 | x2.52 |
| Mushroom | 0.05 | 4.137.547 | 22.093 | 8.248 | x2.68 |
| Chess | 0.7 | 48.731 | 0.382 | 0.344 | x1.11 |
| Chess | 0.65 | 111.239 | 0.845 | 0.705 | x1.20 |
| Chess | 0.55 | 574.998 | 3.856 | 3.158 | x1.22 |
| Chess | 0.5 | 1.272.932 | 8.633 | 6.737 | x1.28 |

Nhận xét ngắn:

- Minsup càng thấp, số tập sinh ra càng lớn và mức tăng tốc càng rõ, vì cây điều kiện dài hơn và có nhiều nhánh đơn hơn.
- Mushroom được lợi nhiều hơn Chess. Ở Chess, phần lớn thời gian còn lại là chi phí ghi từng tập vào kết quả.
- Cài đặt Python chậm hơn SPMF (Java) khoảng một bậc độ lớn ở minsup thấp.

Số liệu chi tiết nằm trong `data/output/benchmark_log.csv`.

## Tái lập kết quả

- Thuật toán xác định (deterministic): không dùng số ngẫu nhiên, thứ tự item luôn cố định nhờ tiêu chí phụ khi support bằng nhau.
- Toàn bộ dữ liệu benchmark tải từ trang SPMF Datasets, xem mục [Dữ liệu benchmark](#dữ-liệu-benchmark). Lưu ý bản Mushroom dùng có **8.416 giao dịch**, đúng bằng con số SPMF công bố; con số 8.124 hay gặp là của bản UCI gốc.
- Muốn chạy lại toàn bộ benchmark: `python -m pytest tests/test_benchmark.py -v -s`.

## Xử lý sự cố thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | Chạy không đúng thư mục hoặc không dùng `-m` | Đứng ở thư mục gốc và dùng `python -m src.algorithm.fpgrowth ...` |
| `FileNotFoundError` khi đọc dữ liệu | Sai đường dẫn tương đối | Chạy từ thư mục gốc |
| Test bị `SKIPPED` | Chưa có file ref (thư mục `data/output/` không nằm trong repo) | Chạy `python -m scripts.make_refs --group toy` (và `--group benchmark`) |
| `'java' is not recognized` | Chưa cài Java | Cài JDK/JRE rồi mở terminal mới |
| `Unable to access jarfile spmf.jar` | Chưa có `spmf.jar` | Tải về và đặt vào `tool/` |
| `error: --minsup phải nằm trong khoảng (0, 1]` | Giá trị minsup không hợp lệ | Dùng minsup tương đối, ví dụ `0.4` |

## Tài liệu tham khảo

1. J. Han, J. Pei, Y. Yin, R. Mao. *Mining Frequent Patterns without Candidate Generation: A Frequent-Pattern Tree Approach.* Data Mining and Knowledge Discovery, 8, 53-87, 2004.
2. P. Fournier-Viger et al. *SPMF: An Open-Source Data Mining Library.* https://www.philippe-fournier-viger.com/spmf/
3. _bổ sung thêm các tài liệu dùng trong báo cáo_