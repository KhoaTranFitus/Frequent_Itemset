"""Ứng dụng 1 (Chương 3): phân tích giỏ hàng và sinh luật kết hợp.

Chạy đầu-cuối bằng chính cài đặt của nhóm: đọc dữ liệu giỏ hàng, mã hóa item,
khai thác tập phổ biến bằng fpgrowth, sinh luật kết hợp, rồi in bảng top luật
theo lift và ghi kết quả ra CSV.

Chạy từ thư mục gốc repo:
    python -m scripts.app1_basket                                  # Groceries, ngưỡng mặc định
    python -m scripts.app1_basket --minsup 0.01 --minconf 0.5      # ca kiểm chứng, phải ra 15 luật
    python -m scripts.app1_basket --top 20 --sort-by confidence
    python -m scripts.app1_basket --max-consequent 0               # 0 = không giới hạn bên phải
    python -m scripts.app1_basket --dataset retail                 # CSDL lớn, item đã ẩn danh

Kết quả ghi vào data/output/app1/:
    rules_<csdl>_<minsup>_<minconf>.csv   mọi luật vượt ngưỡng, kèm 4 đo lường
    itemsets_<csdl>_<minsup>.txt          tập phổ biến, định dạng SPMF
    code_<csdl>.csv                       bảng mã item (chỉ CSDL có item dạng tên)

Lưu ý về định dạng: itemsets_*.txt được ghi từ dict ĐÃ MÃ HÓA (item là số), vì
write_result ghép item bằng dấu cách và read_result lại int() từng token — tên
item Groceries có dấu cách nên ghi tên vào đó là sai định dạng SPMF và không đọc
lại được. Việc đổi số về tên chỉ làm ở bước trình bày (bảng in ra và CSV luật).
Bảng mã được ghi kèm ra code_<csdl>.csv để tra lại.

Ngưỡng mặc định lấy từ src/config.py, không rải rác trong script, để notebook và
test dùng chung một bộ số — yêu cầu tái lập kết quả của đề.
"""
import argparse
import csv
import os
import time

from src.algorithm.fpgrowth import fpgrowth
from src.apps.basket import describe, load_dataset
from src.config import (APP1_DIR, APP1_MAX_CONSEQUENT, APP1_MINCONF,
                        APP1_MINSUP, APP1_MINSUP_RETAIL, APP1_TOP,
                        APP1_DATASETS, to_min_count, use_utf8_stdout)
from src.rules import (ROW_COLUMNS, format_rule, generate_rules, rules_to_rows,
                       sort_rules)
from src.utils import write_result

CODE_COLUMNS = ["item", "code"]


def default_minsup(dataset):
    """Retail thưa hơn Groceries một bậc nên cần minsup nhỏ hơn mới ra luật."""
    return APP1_MINSUP_RETAIL if dataset == "retail" else APP1_MINSUP


def write_rows(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def print_top(rules, name_of, top, sort_by):
    """In bảng top luật dạng cột cố định."""
    best = sort_rules(rules, by=sort_by)[:top]
    if not best:
        print("Không có luật nào vượt ngưỡng.")
        return best

    texts = [format_rule(rule, name_of) for rule in best]
    width = min(max(len(t) for t in texts), 70)

    print(f"\nTop {len(best)} luật theo {sort_by}:")
    print(f"{'#':>3} | {'luật':<{width}} | {'support':>8} | {'conf':>6} "
          f"| {'lift':>8} | {'leverage':>9} | {'giỏ':>6}")
    print("-" * (3 + width + 55))
    for i, (rule, text) in enumerate(zip(best, texts), start=1):
        print(f"{i:>3} | {text[:width]:<{width}} | {rule.support:>8.4f} "
              f"| {rule.confidence:>6.3f} | {rule.lift:>8.3f} "
              f"| {rule.leverage:>9.5f} | {rule.support_count:>6}")
    return best


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Phân tích giỏ hàng: khai thác tập phổ biến rồi sinh luật kết hợp")
    parser.add_argument("--dataset", default="groceries", choices=sorted(APP1_DATASETS),
                        help="CSDL giỏ hàng (mặc định groceries)")
    parser.add_argument("--minsup", type=float,
                        help="minsup tương đối trong (0, 1] (mặc định theo CSDL)")
    parser.add_argument("--minconf", type=float, default=APP1_MINCONF,
                        help=f"ngưỡng confidence trong (0, 1] (mặc định {APP1_MINCONF})")
    parser.add_argument("--max-consequent", type=int, default=APP1_MAX_CONSEQUENT,
                        help="số item tối đa bên phải luật, 0 là không giới hạn "
                             f"(mặc định {APP1_MAX_CONSEQUENT})")
    parser.add_argument("--top", type=int, default=APP1_TOP,
                        help=f"số luật in ra bảng (mặc định {APP1_TOP})")
    parser.add_argument("--sort-by", default="lift",
                        choices=["lift", "confidence", "support", "leverage"],
                        help="tiêu chí sắp bảng top (mặc định lift, như đề yêu cầu)")
    parser.add_argument("--output-dir", default=APP1_DIR,
                        help=f"thư mục ghi kết quả (mặc định {APP1_DIR})")
    args = parser.parse_args()

    path = APP1_DATASETS[args.dataset]
    if not os.path.exists(path):
        raise SystemExit(f"Thiếu dữ liệu: {path}")

    minsup = args.minsup if args.minsup is not None else default_minsup(args.dataset)
    if not 0 < minsup <= 1:
        raise SystemExit("--minsup phải nằm trong khoảng (0, 1]")
    if not 0 < args.minconf <= 1:
        raise SystemExit("--minconf phải nằm trong khoảng (0, 1]")
    if args.max_consequent < 0:
        raise SystemExit("--max-consequent phải từ 0 trở lên (0 là không giới hạn)")
    max_consequent = args.max_consequent or None

    # 1. dữ liệu
    transactions, code, name_of = load_dataset(args.dataset)
    stats = describe(transactions)
    n = stats["transactions"]
    min_count = to_min_count(minsup, n)

    print(f"CSDL {args.dataset} ({path})")
    print(f"  {n} giao dịch | {stats['items']} item phân biệt "
          f"| {stats['occurrences']} lượt item")
    print(f"  độ dài giao dịch: trung bình {stats['avg_len']:.2f}, "
          f"nhỏ nhất {stats['min_len']}, lớn nhất {stats['max_len']} "
          f"| độ dày {stats['density']:.4f}")
    print(f"  minsup {minsup} -> min_count {min_count} | minconf {args.minconf} "
          f"| bên phải tối đa {max_consequent or 'không giới hạn'} item", flush=True)

    # 2. khai thác tập phổ biến bằng cài đặt của nhóm
    start = time.perf_counter()
    itemsets = fpgrowth(transactions, min_count)
    t_mine = time.perf_counter() - start

    by_size = {}
    for itemset in itemsets:
        by_size[len(itemset)] = by_size.get(len(itemset), 0) + 1
    sizes = ", ".join(f"{k} item: {v}" for k, v in sorted(by_size.items()))
    print(f"\n{len(itemsets)} tập phổ biến trong {t_mine:.3f}s ({sizes})", flush=True)

    # 3. sinh luật
    start = time.perf_counter()
    rules = generate_rules(itemsets, n, args.minconf, max_consequent)
    t_rules = time.perf_counter() - start
    print(f"{len(rules)} luật trong {t_rules:.3f}s", flush=True)

    # 4. bảng top
    print_top(rules, name_of, args.top, args.sort_by)

    # 5. ghi kết quả
    tag = f"{args.dataset}_{minsup}"
    itemsets_path = f"{args.output_dir}/itemsets_{tag}.txt"
    os.makedirs(args.output_dir, exist_ok=True)
    write_result(itemsets, itemsets_path)          # dict đã mã hóa, đúng định dạng SPMF

    rules_path = f"{args.output_dir}/rules_{tag}_{args.minconf}.csv"
    write_rows(rules_path, ROW_COLUMNS,
               rules_to_rows(sort_rules(rules, by=args.sort_by), name_of))

    print(f"\nĐã ghi {itemsets_path}")
    print(f"Đã ghi {rules_path}")

    if code is not None:
        code_path = f"{args.output_dir}/code_{args.dataset}.csv"
        write_rows(code_path, CODE_COLUMNS,
                   sorted(code.items(), key=lambda pair: pair[1]))
        print(f"Đã ghi {code_path}")


if __name__ == "__main__":
    main()
