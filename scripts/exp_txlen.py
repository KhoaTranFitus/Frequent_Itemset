"""Thực nghiệm: ảnh hưởng của độ dài giao dịch trung bình lên thời gian chạy."""
import csv
import os

import numpy as np

from src.algorithm.fpgrowth import fpgrowth
from src.config import EXP_DIR, SEED, to_min_count, use_utf8_stdout
from scripts.exp_runtime import median_time       # dùng lại hàm của Thông

CSV_PATH = f"{EXP_DIR}/txlen.csv"
COLUMNS = ["avg_len", "transactions", "minsup", "itemsets", "t_opt_s"]

N_TRANSACTIONS = 10_000
N_ITEMS = 200
MINSUP = 0.05
AVG_LENS = [5, 10, 15, 20, 25, 30]
RUNS = 3


def generate(n_transactions, n_items, avg_len, seed=SEED):
    """Sinh CSDL tổng hợp, item phổ biến theo kiểu Zipf (item k có xác suất ~ 1/k)."""
    rng = np.random.default_rng(seed)

    # xác suất của từng item: 1/1, 1/2, ..., 1/n_items, rồi chia cho tổng để cộng lại = 1
    p = 1 / np.arange(1, n_items + 1)
    p = p/p.sum()

    transactions = []
    for _ in range(n_transactions):
        k = rng.poisson(avg_len)
        k = int(np.clip(k, 1, n_items))      # độ dài ít nhất 1, nhiều nhất n_items
        items = rng.choice(n_items, size=k, replace=False, p=p)
        transactions.append([int(i) + 1 for i in items])   # +1 để item bắt đầu từ 1 (SPMF)
    return transactions


def main():
    use_utf8_stdout()
    rows = []
    for L in AVG_LENS:
        # 1. sinh data
        # 2. tính độ dài trung bình THỰC TẾ của data vừa sinh
        # 3. tính min_count, đo thời gian bằng median_time
        # 4. in ra màn hình + thêm dòng vào rows
        data = generate(N_TRANSACTIONS, N_ITEMS, L)
        avg_len = sum(len(t) for t in data) / len (data)

        min_count = to_min_count(MINSUP, len(data))
        result,t = median_time(fpgrowth,data, min_count, RUNS)

        print (f"L={L}: avg thuc {avg_len:.2f} | {len(result)} tap | {t:.3f}s", flush=True)
        rows.append([f"{avg_len:.2f}", len(data), MINSUP, len(result), f"{t:.4f}"])

    os.makedirs(EXP_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Đã ghi {CSV_PATH}")


if __name__ == "__main__":
    main()