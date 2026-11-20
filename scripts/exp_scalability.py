"""Thực nghiệm 2: khả năng mở rộng theo kích thước CSDL.

Cắt một CSDL lớn thành các tập con 10%, 25%, 50%, 75%, 100% số giao dịch rồi đo
thời gian chạy bản tối ưu ở một minsup cố định, để xem thời gian tăng tuyến tính
hay phi tuyến.

Chạy từ thư mục gốc repo:
    python -m scripts.exp_scalability                          # retail, minsup giữa
    python -m scripts.exp_scalability --minsup 0.002
    python -m scripts.exp_scalability --dataset T10I4D100K
    python -m scripts.exp_scalability --runs 1                 # chạy thử cho nhanh

Kết quả ghi vào data/output/exp/scalability.csv.

Cách cắt: trộn danh sách giao dịch một lần bằng random.Random(SEED) rồi lấy tiền
tố, nên các tập con lồng nhau (10% nằm trong 25%, 25% nằm trong 50%...) và cố
định qua mọi lần chạy. Nếu cắt độc lập cho từng tỉ lệ thì đường cong sẽ lẫn thêm
dao động do thành phần tập con khác nhau, không chỉ do kích thước.

minsup giữ nguyên ở dạng tương đối, nên min_count giảm theo kích thước tập con.
Đây là điều cần nói rõ khi nhận xét: số giao dịch tăng thì ngưỡng tuyệt đối cũng
tăng, không phải chỉ có dữ liệu nhiều hơn.
"""
import argparse
import csv
import os
import random
import statistics
import time

from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.config import (BENCHMARK, EXP_DIR, FRACTIONS, SCALABILITY_DATASET,
                        SEED, mid_minsup, to_min_count, use_utf8_stdout)
from src.utils import read_transactions

CSV_PATH = f"{EXP_DIR}/scalability.csv"
COLUMNS = ["dataset", "fraction", "transactions", "minsup", "itemsets", "t_opt_s"]


def shuffled(transactions):
    """Bản trộn cố định của danh sách giao dịch (không sửa danh sách gốc)."""
    order = list(transactions)
    random.Random(SEED).shuffle(order)
    return order


def median_time(data, min_count, runs):
    times = []
    result = None
    for _ in range(runs):
        start = time.perf_counter()
        result = fp_opt(data, min_count)
        times.append(time.perf_counter() - start)
    return result, statistics.median(times)


def write_rows(rows):
    os.makedirs(EXP_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description="Đo thời gian theo kích thước CSDL")
    parser.add_argument("--dataset", default=SCALABILITY_DATASET,
                        choices=sorted(BENCHMARK),
                        help=f"CSDL để cắt (mặc định {SCALABILITY_DATASET})")
    parser.add_argument("--minsup", type=float,
                        help="minsup tương đối cố định (mặc định mức giữa của CSDL)")
    parser.add_argument("--runs", type=int, default=3,
                        help="số lần đo, lấy trung vị (mặc định 3)")
    args = parser.parse_args()

    path = BENCHMARK[args.dataset][0]
    if not os.path.exists(path):
        raise SystemExit(f"Thiếu dữ liệu: {path}")

    minsup = args.minsup if args.minsup is not None else mid_minsup(args.dataset)
    if not 0 < minsup <= 1:
        raise SystemExit("--minsup phải nằm trong khoảng (0, 1]")

    full = shuffled(read_transactions(path))
    print(f"{args.dataset}: {len(full)} giao dịch, minsup cố định {minsup}", flush=True)

    rows = []
    for fraction in FRACTIONS:
        n = max(1, round(fraction * len(full)))
        subset = full[:n]                       # tập con lồng nhau
        min_count = to_min_count(minsup, n)

        result, t_opt = median_time(subset, min_count, args.runs)
        print(f"  {fraction:>5.0%} | {n:>7} giao dịch | min_count={min_count:>5} "
              f"| {len(result):>8} tập | {t_opt:8.3f}s", flush=True)
        rows.append([args.dataset, fraction, n, minsup, len(result), f"{t_opt:.4f}"])

    write_rows(rows)
    print(f"Xong, số liệu trong {CSV_PATH}.")


if __name__ == "__main__":
    main()
