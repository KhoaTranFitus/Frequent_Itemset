"""Ứng dụng 1 (Chương 3): quét ngưỡng và null model, lấy số liệu để vẽ và phân tích.

Hai phần, chạy một lệnh ra cả hai:

1. **Quét ngưỡng.** Với mỗi minsup trong danh sách, chạy fpgrowth một lần rồi
   sinh luật ở từng minconf, ghi curves.csv. Nhờ vậy thấy được: hạ minsup thì số
   tập phổ biến và số luật bùng nổ thế nào, và minconf siết nhanh hơn hay chậm
   hơn minsup.

2. **Null model.** Trộn item giữa các giỏ bằng swap randomization
   (swap_randomize trong scripts/app1_verify.py, seed cố định), giữ CHÍNH XÁC
   support từng item và độ dài từng giỏ, rồi chạy lại đúng fpgrowth đó ở cùng
   ngưỡng, ghi nullmodel.csv. Cùng hàm, cùng seed với app1_verify nên số liệu
   trùng Bảng XII của báo cáo.

   Câu hỏi mà null model trả lời: các luật tìm được có phải chỉ là hệ quả của
   việc vài item bán rất chạy hay không? Nếu đúng vậy thì dữ liệu đã trộn — vẫn
   giữ nguyên support của từng item — phải sinh ra lượng luật và mức lift
   tương đương. Chỉ thống kê nào của dữ liệu thật vượt hẳn dữ liệu trộn mới là
   bằng chứng các mẫu phản ánh hành vi mua cùng nhau thật (xem
   compare_real_vs_shuffled).

Chạy từ thư mục gốc repo:
    python -m scripts.app1_curves                          # Groceries, đủ cả hai phần
    python -m scripts.app1_curves --dataset retail
    python -m scripts.app1_curves --skip-null              # chỉ quét ngưỡng
    python -m scripts.app1_curves --shuffles 10            # null model kỹ hơn

Kết quả ghi vào data/output/app1/, một bộ file cho mỗi CSDL:
    curves_<csdl>.csv     dataset, minsup, minconf, min_count, itemsets,
                          rules, max_lift, median_lift, max_leverage
    nullmodel_<csdl>.csv  dataset, minsup, minconf, kind, replicate,
                          itemsets, rules, max_lift, rules_lift_gt_1_5

Tên file có CSDL ở trong để chạy groceries rồi chạy retail không ghi mất số
liệu của nhau — khác với exp_scalability.py chỉ làm việc trên một CSDL.

Trong nullmodel.csv, kind = "real" là dữ liệu thật (một dòng, replicate 0) và
kind = "shuffled" là các lần trộn (replicate 1..shuffles), để khi vẽ chỉ cần lọc
theo cột đó. Seed của lần trộn thứ i là SEED + i - 1, nên chạy lại ra đúng số cũ.

Cả hai file đều GHI ĐÈ (mode "w") chứ không nối thêm, giống exp_scalability.py:
một lần chạy là một bộ số liệu hoàn chỉnh, không có chuyện chạy dở rồi tiếp.
"""
import argparse
import csv
import os
import statistics
import time

from src.algorithm.fpgrowth import fpgrowth
from scripts.app1_verify import swap_randomize
from src.apps.basket import load_dataset
from src.config import (APP1_DATASETS, APP1_DIR, APP1_MINCONF, APP1_MINCONFS,
                        APP1_MINSUP, APP1_MINSUP_RETAIL, APP1_MINSUPS,
                        APP1_MINSUPS_RETAIL, APP1_SHUFFLES, SEED,
                        to_min_count, use_utf8_stdout)
from src.rules import generate_rules

CURVES_COLUMNS = ["dataset", "minsup", "minconf", "min_count", "itemsets",
                  "rules", "max_lift", "median_lift", "max_leverage"]

NULL_COLUMNS = ["dataset", "minsup", "minconf", "kind", "replicate",
                "itemsets", "rules", "max_lift", "rules_lift_gt_1_5"]

LIFT_STRONG = 1.5      # ngưỡng "lift đủ mạnh để đáng chú ý", dùng khi so với null model


def curves_path(dataset):
    return f"{APP1_DIR}/curves_{dataset}.csv"


def null_path(dataset):
    return f"{APP1_DIR}/nullmodel_{dataset}.csv"


def defaults(dataset):
    """(minsup mặc định, danh sách minsup) của một CSDL.

    Retail thưa hơn Groceries một bậc nên cần minsup nhỏ hơn mới ra luật.
    """
    if dataset == "retail":
        return APP1_MINSUP_RETAIL, APP1_MINSUPS_RETAIL
    return APP1_MINSUP, APP1_MINSUPS


def write_rows(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def summarize(rules):
    """(số luật, lift lớn nhất, lift trung vị, leverage lớn nhất, số luật lift mạnh)."""
    if not rules:
        return 0, 0.0, 0.0, 0.0, 0
    lifts = [rule.lift for rule in rules]
    return (len(rules),
            max(lifts),
            statistics.median(lifts),
            max(rule.leverage for rule in rules),
            sum(1 for lift in lifts if lift > LIFT_STRONG))


def scan_thresholds(dataset, transactions, minsups, minconfs):
    """Quét minsup × minconf. Mỗi minsup chỉ mine một lần rồi lọc nhiều minconf."""
    n = len(transactions)
    rows = []

    print("\nQuét ngưỡng:", flush=True)
    for minsup in minsups:
        min_count = to_min_count(minsup, n)

        start = time.perf_counter()
        itemsets = fpgrowth(transactions, min_count)
        t_mine = time.perf_counter() - start
        print(f"  minsup {minsup:<7} min_count {min_count:>6} "
              f"| {len(itemsets):>7} tập | mine {t_mine:6.3f}s", flush=True)

        for minconf in minconfs:
            rules = generate_rules(itemsets, n, minconf)
            count, max_lift, median_lift, max_leverage, _ = summarize(rules)
            rows.append([dataset, minsup, minconf, min_count, len(itemsets),
                         count, f"{max_lift:.4f}", f"{median_lift:.4f}",
                         f"{max_leverage:.6f}"])
            print(f"      minconf {minconf:<5} | {count:>7} luật "
                  f"| lift lớn nhất {max_lift:8.3f} | trung vị {median_lift:6.3f}",
                  flush=True)
    return rows


def run_null_model(dataset, transactions, minsup, minconf, shuffles):
    """So dữ liệu thật với các bản swap (giữ nguyên support item và độ dài giỏ)."""
    n = len(transactions)
    min_count = to_min_count(minsup, n)
    rows = []

    print(f"\nNull model tại minsup {minsup} (min_count {min_count}), "
          f"minconf {minconf}, {shuffles} lần trộn:", flush=True)

    itemsets = fpgrowth(transactions, min_count)
    rules = generate_rules(itemsets, n, minconf)
    count, max_lift, _, _, strong = summarize(rules)
    rows.append([dataset, minsup, minconf, "real", 0, len(itemsets),
                 count, f"{max_lift:.4f}", strong])
    print(f"  dữ liệu thật        | {len(itemsets):>7} tập | {count:>6} luật "
          f"| lift lớn nhất {max_lift:8.3f} | lift > {LIFT_STRONG}: {strong}",
          flush=True)

    for i in range(1, shuffles + 1):
        seed = SEED + i - 1
        shuffled, _ = swap_randomize(transactions, seed)
        itemsets = fpgrowth(shuffled, min_count)
        rules = generate_rules(itemsets, n, minconf)
        count, max_lift, _, _, strong = summarize(rules)
        rows.append([dataset, minsup, minconf, "shuffled", i, len(itemsets),
                     count, f"{max_lift:.4f}", strong])
        print(f"  trộn seed {seed:<9} | {len(itemsets):>7} tập | {count:>6} luật "
              f"| lift lớn nhất {max_lift:8.3f} | lift > {LIFT_STRONG}: {strong}",
              flush=True)

    compare_real_vs_shuffled(rows)
    return rows


def compare_real_vs_shuffled(rows):
    """In bảng so dữ liệu thật với trung vị các lần trộn.

    Cố ý KHÔNG viết sẵn một câu kết luận, vì thống kê nào tách được dữ liệu thật
    khỏi dữ liệu trộn còn tùy CSDL. Trên Groceries cả ba thống kê của dữ liệu
    thật đều cao hơn, nhưng không áp đảo: số luật gấp khoảng 1,4 lần, lift lớn
    nhất 1,7 lần, số luật lift > 1,5 khoảng 2,6 lần. Trên CSDL rất thưa như
    Retail thì dữ liệu trộn còn có NHIỀU luật hơn dữ liệu thật, số luật lift > 1,5
    chỉ kém khoảng 1,3 lần, và chỉ phần đỉnh của phân bố lift mới tách ra rõ. Lý
    do: khi support nền của mỗi item đã rất bé thì hai item ngẫu nhiên rơi vào
    cùng giỏ cũng đủ cho lift vượt 1,5, nên ngưỡng lift 1,5 không chứng minh
    được điều gì. Thống kê chắc chắn hơn là số luật thật có lift vượt mọi bản
    trộn, do scripts/app1_verify.py in ra.

    Vì vậy hàm in cả ba tỉ số và chỉ ra thống kê nào tách tốt nhất, để người
    đọc rút kết luận đúng cho từng CSDL thay vì tin một câu viết cứng.
    """
    real, shuffled = rows[0], rows[1:]
    if not shuffled:
        return

    # cột trong NULL_COLUMNS: 6 = rules, 7 = max_lift, 8 = rules_lift_gt_1_5
    stats = [
        ("số luật", 6),
        ("lift lớn nhất", 7),
        (f"số luật lift > {LIFT_STRONG}", 8),
    ]

    print()
    print("  So với trung vị của các lần trộn:")
    ratios = []
    for label, column in stats:
        value = float(real[column])
        median = statistics.median(float(r[column]) for r in shuffled)
        ratio = value / median if median else float("inf")
        ratios.append((ratio, label))
        print(f"    {label:<22} thật {value:>10.3f} | trộn {median:>10.3f} "
              f"| gấp {ratio:>8.2f} lần")

    best_ratio, best_label = max(ratios)
    print(f"  Thống kê tách dữ liệu thật khỏi dữ liệu trộn rõ nhất: "
          f"{best_label} (gấp {best_ratio:.2f} lần).")
    print("  Phép swap giữ nguyên support từng item và độ dài từng giỏ, nên chỉ thống kê"
          " nào tách rõ mới là bằng chứng các item thật sự được mua cùng nhau.")


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Quét ngưỡng và chạy null model cho Ứng dụng 1")
    parser.add_argument("--dataset", default="groceries", choices=sorted(APP1_DATASETS),
                        help="CSDL giỏ hàng (mặc định groceries)")
    parser.add_argument("--minconf", type=float, default=APP1_MINCONF,
                        help=f"minconf dùng cho null model (mặc định {APP1_MINCONF})")
    parser.add_argument("--shuffles", type=int, default=APP1_SHUFFLES,
                        help=f"số lần trộn của null model (mặc định {APP1_SHUFFLES})")
    parser.add_argument("--skip-null", action="store_true",
                        help="chỉ quét ngưỡng, không chạy null model")
    parser.add_argument("--skip-curves", action="store_true",
                        help="chỉ chạy null model, không quét ngưỡng")
    args = parser.parse_args()

    path = APP1_DATASETS[args.dataset]
    if not os.path.exists(path):
        raise SystemExit(f"Thiếu dữ liệu: {path}")
    if not 0 < args.minconf <= 1:
        raise SystemExit("--minconf phải nằm trong khoảng (0, 1]")
    if args.shuffles < 1:
        raise SystemExit("--shuffles phải từ 1 trở lên")

    minsup, minsups = defaults(args.dataset)
    transactions, _, _ = load_dataset(args.dataset)
    print(f"CSDL {args.dataset} ({path}): {len(transactions)} giao dịch", flush=True)

    if not args.skip_curves:
        rows = scan_thresholds(args.dataset, transactions, minsups, APP1_MINCONFS)
        path_out = curves_path(args.dataset)
        write_rows(path_out, CURVES_COLUMNS, rows)
        print(f"\nĐã ghi {path_out} ({len(rows)} dòng)")

    if not args.skip_null:
        rows = run_null_model(args.dataset, transactions, minsup,
                              args.minconf, args.shuffles)
        path_out = null_path(args.dataset)
        write_rows(path_out, NULL_COLUMNS, rows)
        print(f"\nĐã ghi {path_out} ({len(rows)} dòng)")


if __name__ == "__main__":
    main()
