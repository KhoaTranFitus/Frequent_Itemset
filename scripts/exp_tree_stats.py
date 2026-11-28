"""Phân tích phụ cho Chương 2A: cấu trúc FP-tree và chi phí của từng giai đoạn.

Số liệu này giải thích các đường cong thời gian và số itemset (runtime.png,
itemsets.png, scalability.png), không thay thế chúng. Script chỉ GỌI các hàm có
sẵn của cài đặt (find_frequent_items, build_tree, mine_tree), không sửa thuật toán.

Chạy từ thư mục gốc repo:
    python -m scripts.exp_tree_stats                   # 4 CSDL x 7 minsup + scalability
    python -m scripts.exp_tree_stats --dataset retail  # một CSDL
    python -m scripts.exp_tree_stats --runs 1          # chạy thử cho nhanh

Kết quả:
    data/output/exp/tree_stats.csv  mỗi ca (dataset, minsup) một dòng
    data/output/exp/tree_scal.csv   kích thước FP-tree trên các tập con của thực
                                    nghiệm scalability, kèm hồi quy t = a + b*N

Các cột của tree_stats.csv:
    freq_items      |F|, số item phổ biến
    occ_freq        tổng |freq(T)| trên mọi giao dịch: giới hạn trên của số nút
                    FP-tree theo Lemma 2.2 của bài báo gốc
    nodes           số nút thực tế của FP-tree gốc (không tính gốc)
    compress        occ_freq / nodes: FP-tree gộp bao nhiêu lượt item vào một nút
    max_freq_len    max |freq(T)|: giới hạn chiều cao cây (Lemma 2.2)
    t_build_s       hai lần quét + dựng FP-tree gốc (trung vị --runs lần)
    t_mine_s        khai thác trên cây đã dựng (trung vị --runs lần)
    build_share_pct t_build / (t_build + t_mine)
    cond_calls      số lần bản TỐI ƯU gọi build_conditional_tree (kể cả lần ra
                    cây rỗng). Bản cơ bản gọi đúng một lần cho mỗi itemset, tức
                    bằng cột itemsets, nên itemsets / cond_calls là số lần bản tối
                    ưu gọi ít hơn.
    single_paths    số lần bản tối ưu gặp cây một nhánh (Lemma 3.2)
    itemsets        |L|, số frequent itemset
    max_len, mode_len, singleton_pct
                    độ dài itemset dài nhất, độ dài gặp nhiều nhất, tỉ lệ itemset
                    một phần tử

Thời gian đo trên máy đang chạy nên chỉ nên dùng TỈ TRỌNG (build_share_pct); các
cột còn lại là đại lượng xác định, chạy lại ở đâu cũng ra như nhau.
"""
import argparse
import csv
import os
import random
import statistics
import time
from collections import Counter

import src.algorithm.fpgrowth as fp
from src.config import (BENCHMARK, EXP_DIR, FRACTIONS, SCALABILITY_DATASET, SEED,
                        cases, mid_minsup, to_min_count, use_utf8_stdout)
from src.structures import build_tree
from src.utils import find_frequent_items, read_transactions

STATS_CSV = f"{EXP_DIR}/tree_stats.csv"
SCAL_CSV = f"{EXP_DIR}/tree_scal.csv"
STATS_COLUMNS = ["dataset", "minsup", "min_count", "freq_items", "occ_freq", "nodes",
                 "compress", "max_freq_len", "t_build_s", "t_mine_s", "build_share_pct",
                 "cond_calls", "single_paths", "itemsets", "max_len", "mode_len",
                 "singleton_pct"]
SCAL_COLUMNS = ["dataset", "fraction", "transactions", "minsup", "min_count",
                "freq_items", "occ_freq", "nodes", "nodes_per_tx"]


def build(data, min_count):
    """Hai lần quét + dựng FP-tree gốc, đúng như fpgrowth() làm."""
    freq = find_frequent_items(data, min_count)
    flist = sorted(freq, key=lambda i: (-freq[i], i))
    rank = {i: k for k, i in enumerate(flist)}
    root, header = build_tree(data, rank)
    return freq, root, header


def count_nodes(root):
    total, stack = 0, [root]
    while stack:
        node = stack.pop()
        for child in node.children.values():
            total += 1
            stack.append(child)
    return total


def count_calls(root, header, freq, min_count):
    """Chạy mine_tree của bản tối ưu, đếm lượt dựng conditional tree và số single path."""
    counter = {"cond": 0, "single": 0}
    orig_cond, orig_single = fp.build_conditional_tree, fp.get_single_path

    def cond(paths, mc):
        counter["cond"] += 1
        return orig_cond(paths, mc)

    def single(node):
        path = orig_single(node)
        if path is not None:
            counter["single"] += 1
        return path

    fp.build_conditional_tree, fp.get_single_path = cond, single
    try:
        result = {}
        fp.mine_tree(root, header, freq, [], min_count, result)
    finally:
        fp.build_conditional_tree, fp.get_single_path = orig_cond, orig_single
    return result, counter["cond"], counter["single"]


def case_row(name, data, minsup, runs):
    min_count = to_min_count(minsup, len(data))

    t_build, t_mine = [], []
    for _ in range(runs):
        start = time.perf_counter()
        freq, root, header = build(data, min_count)
        mid = time.perf_counter()
        result = {}
        fp.mine_tree(root, header, freq, [], min_count, result)
        t_build.append(mid - start)
        t_mine.append(time.perf_counter() - mid)
    tb, tm = statistics.median(t_build), statistics.median(t_mine)

    freq_lens = [sum(1 for i in set(t) if i in freq) for t in data]
    nodes = count_nodes(root)
    checked, cond_calls, single_paths = count_calls(root, header, freq, min_count)
    assert checked == result, "lần đếm cho kết quả khác lần đo"

    lengths = Counter(len(itemset) for itemset in result)
    occ = sum(freq_lens)
    return [name, minsup, min_count, len(freq), occ, nodes,
            f"{occ / nodes:.2f}" if nodes else "",
            max(freq_lens), f"{tb:.4f}", f"{tm:.4f}", f"{tb / (tb + tm) * 100:.1f}",
            cond_calls, single_paths, len(result),
            max(lengths), max(lengths, key=lengths.get),
            f"{lengths[1] / len(result) * 100:.3f}"]


def scal_rows():
    """Kích thước FP-tree trên đúng các tập con của exp_scalability.py."""
    path = BENCHMARK[SCALABILITY_DATASET][0]
    minsup = mid_minsup(SCALABILITY_DATASET)
    full = list(read_transactions(path))
    random.Random(SEED).shuffle(full)          # giống hệt exp_scalability.shuffled

    rows = []
    for fraction in FRACTIONS:
        n = max(1, round(fraction * len(full)))
        subset = full[:n]
        min_count = to_min_count(minsup, n)
        freq, root, _ = build(subset, min_count)
        occ = sum(sum(1 for i in set(t) if i in freq) for t in subset)
        nodes = count_nodes(root)
        rows.append([SCALABILITY_DATASET, fraction, n, minsup, min_count, len(freq),
                     occ, nodes, f"{nodes / n:.3f}"])
    return rows


def regression(csv_path):
    """Hồi quy t = a + b*N trên scalability.csv (bình phương tối thiểu)."""
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="", encoding="utf-8") as f:
        pts = [(int(r["transactions"]), float(r["t_opt_s"])) for r in csv.DictReader(f)]
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in pts)
    ss_tot = sum((y - my) ** 2 for _, y in pts)
    return a, b, 1 - ss_res / ss_tot


def write(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description="Cấu trúc FP-tree và chi phí từng giai đoạn")
    parser.add_argument("--dataset", help="chỉ chạy một CSDL, ví dụ retail")
    parser.add_argument("--runs", type=int, default=3,
                        help="số lần đo thời gian, lấy trung vị (mặc định 3)")
    args = parser.parse_args()

    todo = cases("benchmark")
    if args.dataset:
        todo = [c for c in todo if c[0] == args.dataset]
        if not todo:
            raise SystemExit(f"Không có ca nào cho CSDL '{args.dataset}'.")

    rows, cache = [], {}
    for name, path, minsup in todo:
        if path not in cache:
            cache = {path: read_transactions(path)}      # giữ một CSDL trong bộ nhớ
        row = case_row(name, cache[path], minsup, args.runs)
        rows.append(row)
        print(f"{name} {minsup}: |F|={row[3]} nút={row[5]} nén={row[6]}x "
              f"dựng cây={row[10]}% lượt dựng cây ĐK={row[11]} itemset={row[13]}",
              flush=True)
    write(STATS_CSV, STATS_COLUMNS, rows)
    print(f"Đã ghi {STATS_CSV}")

    if not args.dataset:
        srows = scal_rows()
        write(SCAL_CSV, SCAL_COLUMNS, srows)
        for r in srows:
            print(f"scalability {r[1]:>4}: N={r[2]} |F|={r[5]} nút={r[7]} nút/gd={r[8]}")
        reg = regression(f"{EXP_DIR}/scalability.csv")
        if reg:
            a, b, r2 = reg
            print(f"Hồi quy t = a + b*N: a = {a * 1000:.2f} ms, "
                  f"b = {b * 1e6:.2f} ms / 1.000 giao dịch, R^2 = {r2:.4f}")
        print(f"Đã ghi {SCAL_CSV}")


if __name__ == "__main__":
    main()
