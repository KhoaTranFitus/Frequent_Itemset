"""Ứng dụng 2, bước 3: emerging pattern của EI và IE so với N.

Chạy từ thư mục gốc repo:
    python -m scripts.app2_emerging
"""
from src.algorithm.fpgrowth import fpgrowth
from src.app2_bio import count_support, growth_rate, load_groups
from src.config import to_min_count, use_utf8_stdout
from src.utils import invert_code

DATA_PATH = "data/app2/splice.data"
MINSUP = 0.5
TOP_K = 10


def emerging(target, other, minsup):
    """Itemset phổ biến trong target, kèm support tương đối ở hai nhóm và growth rate."""
    result = fpgrowth(target, to_min_count(minsup, len(target)))
    other_sets = [set(t) for t in other]          # đổi sang set một lần, dùng nhiều lần

    rows = []
    for itemset, sup_a in result.items():
        sup_b = count_support(itemset, other_sets)
        g = growth_rate(sup_a, len(target), sup_b, len(other))
        rows.append((itemset, sup_a / len(target), sup_b / len(other), g, sup_b))
    return rows


def main():
    use_utf8_stdout()
    groups, code = load_groups(DATA_PATH)
    name_of = invert_code(code)

    for label in ["EI", "IE"]:
        rows = emerging(groups[label], groups["N"], MINSUP)
        # sắp theo growth giảm dần; bằng nhau thì theo support trong nhóm giảm dần
        rows.sort(key=lambda r: (r[3], r[1]), reverse=True)

        print(f"\nTop {TOP_K} emerging pattern của {label} so với N (minsup={MINSUP})")
        print(f"  {'growth':>7} {label:>6} {'N':>6} {'#N':>4}  itemset")
        for itemset, s_a, s_b, g, n_b in rows[:TOP_K]:
            names = tuple(name_of[i] for i in itemset)
            print(f"  {g:7.1f} {s_a:6.1%} {s_b:6.1%} {n_b:4d}  {names}")
                # tìm growth của các cặp quy tắc GT-AG
        pair = {"EI": ("P+1=G", "P+2=T"), "IE": ("P-2=A", "P-1=G")}[label]
        key = tuple(sorted(code[name] for name in pair))
        for itemset, s_a, s_b, g, n_b in rows:
            if itemset == key:
                print(f"\n  Cặp {pair}: growth {g:.1f} | {label} {s_a:.1%} | N {s_b:.1%} ({n_b} mẫu)")

if __name__ == "__main__":
    main()