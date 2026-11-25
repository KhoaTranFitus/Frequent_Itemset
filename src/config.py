"""Cấu hình dùng chung cho phần thực nghiệm: CSDL, danh sách minsup, đường dẫn kết quả.

Mọi script thực nghiệm và script sinh ref đều đọc file này, nên sửa minsup ở đây
là tất cả đi theo, hai người không phải chờ nhau hay sửa trùng chỗ.

Danh sách minsup được chốt bằng cách chạy thử bản tối ưu trên từng CSDL rồi giữ
lại 7 mức mà Python chạy xong trong thời gian chấp nhận được (đề yêu cầu 5 đến 7
mức cho mỗi CSDL, từ cao xuống thấp).

Đo thử ngày 21/11/2026 tại mức minsup thấp nhất của mỗi CSDL, bản tối ưu, một
lần chạy: chess 0.6 và mushroom 0.05 theo số liệu đã có trong README; retail
0.001 ra 7.589 tập trong 3,9s; T10I4D100K 0.001 ra 27.532 tập trong 7,2s. Không
mức nào phải bỏ.
"""
import math
import os
import sys

# Seed cố định cho mọi chỗ có ngẫu nhiên (cắt tập con, sinh dữ liệu tổng hợp...)
SEED = 42

SPMF_JAR = "tool/spmf.jar"

# Lệnh java để chạy SPMF. Máy có nhiều bản Java thì PATH thường trỏ vào bản cũ
# (ví dụ shim java8path của Oracle), trong khi spmf.jar cần Java 25, nên cho phép
# chỉ rõ bản muốn dùng:
#   JAVA="C:/Program Files/Java/jdk-25.0.5.0.3/bin/java.exe" python -m scripts.make_refs
JAVA_BIN = os.environ.get("JAVA", "java")

REF_DIR = "data/output/ref"      # kết quả tham chiếu do SPMF sinh
MINE_DIR = "data/output/mine"    # kết quả của nhóm
EXP_DIR = "data/output/exp"      # CSV của các thực nghiệm chương 2
APP1_DIR = "data/output/app1"     # CSV và kết quả của Ứng dụng 1 (chương 3)

# {tên: (đường dẫn, [minsup tương đối từ cao xuống thấp])}
BENCHMARK = {
    "chess": (
        "data/benchmark/chess.txt",
        [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6],
    ),
    "mushroom": (
        "data/benchmark/mushroom.txt",
        [0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05],
    ),
    "retail": (
        "data/benchmark/retail.txt",
        [0.01, 0.008, 0.005, 0.004, 0.003, 0.002, 0.001],
    ),
    "T10I4D100K": (
        "data/benchmark/T10I4D100K.txt",
        [0.01, 0.008, 0.005, 0.004, 0.003, 0.002, 0.001],
    ),
}

# CSDL nhỏ để kiểm thử nhanh, cùng danh sách ca với tests/test_correctness.py
TOY = {
    "test1": ("data/toy/toy_test1.txt", [0.6]),
    "test2": ("data/toy/toy_test2.txt", [0.5, 0.375]),
    "test3": ("data/toy/toy_test3.txt", [0.5, 0.33]),
    "test4": ("data/toy/toy_test4.txt", [0.3, 0.2]),
}

# Thực nghiệm khả năng mở rộng: cắt CSDL lớn theo các tỉ lệ này
SCALABILITY_DATASET = "retail"
FRACTIONS = [0.1, 0.25, 0.5, 0.75, 1.0]

# ---------------------------------------------------------------------------
# Chương 3, Ứng dụng 1: phân tích giỏ hàng và sinh luật kết hợp
# ---------------------------------------------------------------------------
# CSDL chính: Groceries (gói R arules), item có tên đọc được nên mới diễn giải
# được ý nghĩa kinh doanh. Nguồn và các mốc kiểm chứng ghi trong
# data/app1/README.md.
GROCERIES = "data/app1/groceries.csv"
GROCERIES_URL = ("https://raw.githubusercontent.com/stedy/"
                 "Machine-Learning-with-R-datasets/master/groceries.csv")

# CSDL phụ: retail.txt đã có trong data/benchmark (88.162 giỏ, 16.470 item, đã
# ẩn danh thành số). Dùng để cho thấy phương pháp chạy được ở quy mô thật.
APP1_DATASETS = {
    "groceries": GROCERIES,
    "retail": BENCHMARK["retail"][0],
}

# Ngưỡng mặc định, chốt bằng cách chạy thử trên Groceries: minsup 0,01 cho 333
# tập phổ biến và 125 luật ở minconf 0,3 — lượng mà người đọc được. Riêng mức
# 0,01 / 0,5 cho đúng 15 luật, là con số đã công bố của bộ dữ liệu nên dùng làm
# mốc kiểm chứng.
APP1_MINSUP = 0.01
APP1_MINCONF = 0.3
APP1_TOP = 10                   # số luật đưa vào bảng top theo lift (đề yêu cầu 10)
APP1_MAX_CONSEQUENT = 1         # consequent một item: luật dễ đọc và dễ dùng

# Quét ngưỡng để vẽ các đường cong phân tích.
APP1_MINSUPS = [0.02, 0.01, 0.005, 0.002, 0.001]
APP1_MINCONFS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

# Retail thưa hơn Groceries một bậc nên cần minsup nhỏ hơn mới ra luật.
APP1_MINSUP_RETAIL = 0.001
APP1_MINSUPS_RETAIL = [0.01, 0.005, 0.002, 0.001]

# Null model: số lần trộn item giữa các giỏ (giữ nguyên tần suất item) để kiểm
# xem các luật tìm được có phải chỉ là hệ quả của vài item bán chạy hay không.
APP1_SHUFFLES = 5


def use_utf8_stdout():
    """Cho phép in tiếng Việt ra console.

    Console Windows mặc định dùng cp1252, in chữ có dấu là nổ UnicodeEncodeError.
    Mọi script có output tiếng Việt phải gọi hàm này ở dòng đầu của main().
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass        # stdout bị chuyển hướng sang chỗ không reconfigure được


def to_min_count(minsup, n_transactions):
    """Đổi minsup tương đối sang support tuyệt đối.

    Làm tròn lên giống SPMF; round(..., 9) để sai số số thực không đẩy kết quả
    lên thêm 1. Mọi chỗ cần min_count phải dùng hàm này, lệch công thức là mọi
    so khớp với SPMF sai theo.
    """
    return math.ceil(round(minsup * n_transactions, 9))


def mid_minsup(name):
    """minsup giữa của một CSDL, dùng cho thực nghiệm bộ nhớ.

    Với danh sách 7 mức thì đây đúng là mức thứ 4 như nhóm đã chốt.
    """
    minsups = BENCHMARK[name][1]
    return minsups[len(minsups) // 2]


def cases(group="benchmark"):
    """Liệt kê các ca cần chạy: trả về [(tên, đường dẫn, minsup), ...].

    group: "toy", "benchmark" hoặc "all".
    """
    groups = {"toy": [TOY], "benchmark": [BENCHMARK], "all": [TOY, BENCHMARK]}
    if group not in groups:
        raise ValueError(f"group không hợp lệ: {group}")

    out = []
    for table in groups[group]:
        for name, (path, minsups) in table.items():
            for minsup in minsups:
                out.append((name, path, minsup))
    return out


def ref_path(name, minsup):
    """Đường dẫn file ref của một ca. Tên phải khớp với các file test."""
    return f"{REF_DIR}/{name}_{minsup}.txt"
