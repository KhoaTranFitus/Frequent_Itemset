"""Ứng dụng 1: kiểm chứng với arules và null model giữ đúng support (số liệu cho báo cáo).

Hai phần, chạy một lệnh ra cả hai:

1. **Đối chiếu với arules.** Bộ Groceries là dữ liệu mẫu của gói R arules, nên số
   luật ở nhiều cặp ngưỡng đã được in sẵn trong tài liệu công khai. arules dùng
   Apriori (một thuật toán khác, một cài đặt khác), nên khớp ở cả lưới ngưỡng là
   kiểm chứng độc lập cho CẢ phần khai thác tập phổ biến LẪN phần sinh luật
   (Chương 1 mới chỉ so tập phổ biến với SPMF). Nhóm chỉ so KẾT QUẢ SỐ, không đọc
   hay dùng mã nguồn của arules. Mặc định của arules: vế phải đúng một item, vế trái
   được phép rỗng, độ dài luật tối đa 10. Ở các ngưỡng dưới, luật vế trái rỗng
   không bao giờ đạt minconf (item phổ biến nhất chỉ có support 0,2555) và tập dài
   nhất có 6 item, nên mặc định đó trùng với generate_rules(max_consequent=1).

2. **Null model giữ đúng support (swap randomization).** shuffle_keep_marginals
   trộn phẳng mọi lượt item rồi cắt lại theo độ dài giỏ, nên giữ đúng SỐ LƯỢT của
   mỗi item; nhưng khi hai lượt của cùng một item rơi vào cùng một giỏ thì chúng
   gộp làm một (fpgrowth đếm theo set). Trên Groceries cách đó làm mất khoảng 5,5%
   lượt và support của whole milk giảm từ 2.513 xuống khoảng 2.100 giỏ, tức dữ liệu
   trộn "loãng" hơn thật và cho ít luật hơn, nghiêng về phía có lợi cho dữ liệu thật.

   swap_randomize ở đây giữ CHÍNH XÁC cả support của từng item lẫn số item phân
   biệt của từng giỏ: mỗi bước chọn ngẫu nhiên hai lượt (giỏ a, item x), (giỏ b,
   item y) và đổi chỗ x với y nếu x chưa có trong b và y chưa có trong a. Đây là
   swap randomization của Gionis và cộng sự (ACM TKDD, 2007) viết cho dạng danh
   sách giỏ.

Chạy từ thư mục gốc repo:
    python -m scripts.app1_verify                      # cả hai phần, Groceries + Retail
    python -m scripts.app1_verify --skip-null          # chỉ đối chiếu arules (~2 s)
    python -m scripts.app1_verify --dataset groceries  # null model chỉ trên Groceries
    python -m scripts.app1_verify --reps 10 --rounds 10

Kết quả: in ra màn hình và ghi data/output/app1/nullswap_<csdl>.csv với các cột
    dataset, minsup, minconf, kind, replicate, itemsets, rules, max_lift,
    median_lift, rules_lift_gt_1_5, rules_rare_items, top_item_support
(kind = "real" là dữ liệu thật, "swap" là các lần trộn; seed lần thứ i là SEED + i - 1;
rules_rare_items là số luật mà mọi item đều có support dưới 5% số giỏ).
"""
import argparse
import csv
import os
import random
import statistics
import time
from collections import Counter

from src.algorithm.fpgrowth import fpgrowth
from src.apps.basket import load_dataset
from src.config import (APP1_DIR, APP1_MINCONF, APP1_MINSUP, APP1_MINSUP_RETAIL,
                        SEED, to_min_count, use_utf8_stdout)
from src.rules import generate_rules

LIFT_STRONG = 1.5      # cùng ngưỡng với scripts/app1_curves.py
RARE = 0.05            # item "hiếm": support dưới 5% số giỏ

NULL_COLUMNS = ["dataset", "minsup", "minconf", "kind", "replicate", "itemsets",
                "rules", "max_lift", "median_lift", "rules_lift_gt_1_5",
                "rules_rare_items", "top_item_support"]

# Số liệu đã công bố trên Groceries (arules, vế phải một item):
#   - lưới 3 x 3: vignette "Market Basket Analysis" của gói R tidylearn (gọi arules)
#   - 5.668 luật ở 0,001 / 0,5 và thống kê lift: vignette arulesViz và tidylearn
#   - 463 luật ở 0,006 / 0,25, minlen 2: B. Lantz, Machine Learning with R (2013)
GRID = {  # (minsup, minconf): số luật
    (0.001, 0.3): 13770, (0.005, 0.3): 482, (0.01, 0.3): 125,
    (0.001, 0.5): 5668, (0.005, 0.5): 120, (0.01, 0.5): 15,
    (0.001, 0.7): 1279, (0.005, 0.7): 1, (0.01, 0.7): 0,
}
LIFT_5668 = (1.956824513, 2.89899928, 18.99565427)     # nhỏ nhất, trung vị, lớn nhất
LANTZ = (0.006, 0.25, 463, {2: 150, 3: 297, 4: 16}, 3.9565)


def swap_randomize(baskets, seed, rounds=5):
    """Trộn item giữa các giỏ, giữ CHÍNH XÁC support từng item và độ dài từng giỏ.

    baskets: list các giao dịch (item trùng trong một giỏ được bỏ trước khi trộn).
    rounds: số lượt thử đổi = rounds x tổng số lượt item.
    Trả về (list giỏ đã trộn, tỉ lệ lượt thử đổi được). Không sửa đầu vào.
    """
    rng = random.Random(seed)
    sets = [set(b) for b in baskets]
    lists = [sorted(s) for s in sets]                 # sorted: thứ tự xác định
    slots = [(j, k) for j, items in enumerate(lists) for k in range(len(items))]
    m = len(slots)
    swapped = 0
    for _ in range(rounds * m):
        a, ka = slots[rng.randrange(m)]
        b, kb = slots[rng.randrange(m)]
        if a == b:
            continue
        x, y = lists[a][ka], lists[b][kb]
        if x in sets[b] or y in sets[a]:
            continue                                  # đổi thì sinh item trùng: bỏ qua
        sets[a].remove(x)
        sets[a].add(y)
        sets[b].remove(y)
        sets[b].add(x)
        lists[a][ka], lists[b][kb] = y, x
        swapped += 1
    return lists, swapped / (rounds * m) if m else 0.0


def check_arules():
    """So số luật và thống kê lift của nhóm với các giá trị đã công bố của arules."""
    data, _, _ = load_dataset("groceries")
    n = len(data)
    print(f"Đối chiếu với arules trên Groceries ({n} giỏ):")
    ok = 0
    cache = {}

    def mine(minsup):
        if minsup not in cache:
            cache[minsup] = fpgrowth(data, to_min_count(minsup, n))
        return cache[minsup]

    for (minsup, minconf), expected in sorted(GRID.items()):
        got = len(generate_rules(mine(minsup), n, minconf))
        ok += got == expected
        print(f"  minsup {minsup:<6} minconf {minconf:<4} | nhóm {got:>6} | "
              f"công bố {expected:>6} | {'khớp' if got == expected else 'LỆCH'}")

    lifts = [r.lift for r in generate_rules(mine(0.001), n, 0.5)]
    mine_stats = (min(lifts), statistics.median(lifts), max(lifts))
    same = all(abs(a - b) < 5e-8 for a, b in zip(mine_stats, LIFT_5668))
    ok += same
    print(f"  5.668 luật, lift nhỏ nhất / trung vị / lớn nhất: nhóm "
          f"{' / '.join(f'{v:.8f}' for v in mine_stats)} | "
          f"{'khớp' if same else 'LỆCH'}")

    minsup, minconf, expected, by_len, top_lift = LANTZ
    rules = generate_rules(mine(minsup), n, minconf)
    lengths = Counter(len(r.antecedent) + len(r.consequent) for r in rules)
    best = max(r.lift for r in rules)
    same = (len(rules) == expected and dict(lengths) == by_len
            and round(best, 4) == top_lift)
    ok += same
    print(f"  minsup {minsup} minconf {minconf}: {len(rules)} luật, độ dài "
          f"{dict(sorted(lengths.items()))}, lift lớn nhất {best:.4f} | "
          f"{'khớp' if same else 'LỆCH'}")
    total = len(GRID) + 2
    print(f"  => {ok}/{total} mốc khớp.")
    return ok == total


def summarize(data, n, min_count, minconf):
    itemsets = fpgrowth(data, min_count)
    rules = generate_rules(itemsets, n, minconf)
    lifts = [r.lift for r in rules]
    top = max(itemsets[k] for k in itemsets if len(k) == 1)
    # luật mà MỌI item đều hiếm; support từng item tra thẳng trong dict (item của
    # luật luôn phổ biến) và giống hệt nhau ở dữ liệu thật lẫn dữ liệu swap
    rare = sum(1 for r in rules
               if all(itemsets[(i,)] < RARE * n for i in r.antecedent + r.consequent))
    return (len(itemsets), len(rules), max(lifts, default=0.0),
            statistics.median(lifts) if lifts else 0.0,
            sum(1 for v in lifts if v > LIFT_STRONG), rare, top, lifts)


def null_model(dataset, minsup, minconf, reps, rounds):
    data, _, _ = load_dataset(dataset)
    data = [sorted(set(t)) for t in data]
    n = len(data)
    min_count = to_min_count(minsup, n)
    lengths = [len(t) for t in data]
    mean = statistics.mean(lengths)
    baseline = sum(v * (v - 1) for v in lengths) / n / mean ** 2

    print(f"\nNull model swap trên {dataset}: minsup {minsup} (min_count {min_count}), "
          f"minconf {minconf}, {reps} lần trộn x {rounds} vòng")
    print(f"  độ dài giỏ trung bình {mean:.2f}; lift nền của cặp item hiếm dưới null "
          f"giữ độ dài giỏ, E[L(L-1)]/E[L]^2 = {baseline:.3f}")

    real = summarize(data, n, min_count, minconf)
    rows = [[dataset, minsup, minconf, "real", 0, *[_fmt(v) for v in real[:7]]]]
    print(f"  thật        | {real[0]:>6} tập | {real[1]:>6} luật | lift lớn nhất "
          f"{real[2]:8.3f} | trung vị {real[3]:6.3f} | lift > {LIFT_STRONG}: {real[4]:>5} "
          f"| chỉ item hiếm: {real[5]:>4} | item phổ biến nhất {real[6]}")

    swaps = []
    for i in range(1, reps + 1):
        start = time.perf_counter()
        shuffled, rate = swap_randomize(data, SEED + i - 1, rounds)
        if i == 1:
            show_top_item_lengths(data, shuffled)
        stats = summarize(shuffled, n, min_count, minconf)
        swaps.append(stats)
        rows.append([dataset, minsup, minconf, "swap", i, *[_fmt(v) for v in stats[:7]]])
        print(f"  swap seed {SEED + i - 1} | {stats[0]:>6} tập | {stats[1]:>6} luật | "
              f"lift lớn nhất {stats[2]:8.3f} | trung vị {stats[3]:6.3f} | "
              f"lift > {LIFT_STRONG}: {stats[4]:>5} | chỉ item hiếm: {stats[5]:>4} "
              f"| item phổ biến nhất {stats[6]} "
              f"(đổi được {rate:.0%}, {time.perf_counter() - start:.1f}s)", flush=True)

    print("  So với trung vị các lần trộn:")
    for label, k in (("số tập phổ biến", 0), ("số luật", 1), ("lift lớn nhất", 2),
                     ("lift trung vị", 3), (f"số luật lift > {LIFT_STRONG}", 4),
                     (f"số luật chỉ gồm item support < {RARE:.0%}", 5)):
        med = statistics.median(s[k] for s in swaps)
        ratio = f"gấp {real[k] / med:6.2f} lần" if med else "trộn bằng 0"
        print(f"    {label:<34} thật {real[k]:>10.3f} | trộn {med:>10.3f} | {ratio}")
    ceiling = max(s[2] for s in swaps)
    beyond = sum(1 for v in real[7] if v > ceiling)
    print(f"    luật thật có lift vượt lift lớn nhất của MỌI lần trộn ({ceiling:.3f}): "
          f"{beyond}/{real[1]}")

    os.makedirs(APP1_DIR, exist_ok=True)
    path = f"{APP1_DIR}/nullswap_{dataset}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(NULL_COLUMNS)
        writer.writerows(rows)
    print(f"  Đã ghi {path}")


def show_top_item_lengths(real, shuffled, k=3):
    """Độ dài trung bình của giỏ chứa k item phổ biến nhất: thật so với một bản swap.

    Null model đặt item vào giỏ gần như tỉ lệ với độ dài giỏ; nếu ở dữ liệu thật item
    phổ biến nằm trong giỏ ngắn hơn thế, bản trộn sẽ cho chúng đồng xuất hiện nhiều hơn.
    """
    top = [item for item, _ in Counter(i for t in real for i in t).most_common(k)]

    def mean_len(data, item):
        return statistics.mean(len(t) for t in data if item in t)

    real_sets = [set(t) for t in real]
    swap_sets = [set(t) for t in shuffled]
    text = ", ".join(f"{item}: {mean_len(real_sets, item):.2f} -> {mean_len(swap_sets, item):.2f}"
                     for item in top)
    print(f"  độ dài TB giỏ chứa {k} item phổ biến nhất (thật -> swap seed {SEED}): {text}")


def _fmt(value):
    return f"{value:.4f}" if isinstance(value, float) else value


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Ứng dụng 1: đối chiếu với arules và null model giữ đúng support")
    parser.add_argument("--dataset", choices=["groceries", "retail"],
                        help="chỉ chạy null model trên một CSDL (mặc định cả hai)")
    parser.add_argument("--reps", type=int, default=5, help="số lần trộn (mặc định 5)")
    parser.add_argument("--rounds", type=int, default=5,
                        help="số vòng đổi chỗ, tính theo tổng số lượt item (mặc định 5)")
    parser.add_argument("--skip-arules", action="store_true", help="bỏ phần đối chiếu arules")
    parser.add_argument("--skip-null", action="store_true", help="bỏ phần null model")
    args = parser.parse_args()
    if args.reps < 1 or args.rounds < 1:
        raise SystemExit("--reps và --rounds phải từ 1 trở lên")

    if not args.skip_arules:
        check_arules()
    if not args.skip_null:
        todo = [args.dataset] if args.dataset else ["groceries", "retail"]
        for dataset in todo:
            minsup = APP1_MINSUP_RETAIL if dataset == "retail" else APP1_MINSUP
            null_model(dataset, minsup, APP1_MINCONF, args.reps, args.rounds)


if __name__ == "__main__":
    main()
