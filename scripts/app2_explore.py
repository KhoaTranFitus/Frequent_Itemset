"""Ứng dụng 2, bước 2: thử nhiều mức minsup cho từng nhóm EI / IE / N.

Chạy từ thư mục gốc repo:
    python -m scripts.app2_explore
"""
from src.algorithm.fpgrowth import fpgrowth
from src.app2_bio import load_groups
from src.config import to_min_count, use_utf8_stdout
from src.utils import decode, save_code

DATA_PATH = "data/app2/splice.data"
CODE_PATH = "data/app2/code.json"

MINSUPS = [0.3, 0.5, 0.7]   # các mức thử để chọn minsup
TOP_MINSUP = 0.5            # mức dùng để in top itemset
TOP_K = 10


def main():
    use_utf8_stdout()
    groups, code = load_groups(DATA_PATH)
    save_code(code, CODE_PATH)

    print(f"{len(code)} item | " + ", ".join(f"{k}: {len(v)}" for k, v in groups.items()))

    # 1. Bảng số itemset: mỗi mức minsup x mỗi nhóm
    print("\nSố itemset theo minsup")
    print(f"{'minsup':>8}" + "".join(f"{label:>10}" for label in groups))
    for minsup in MINSUPS:
        line = f"{minsup:>8}"
        for label, data in groups.items():
            result = fpgrowth(data, to_min_count(minsup, len(data)))
            line += f"{len(result):>10}"
        print(line)

    # 2. Top-K itemset có support cao nhất của mỗi nhóm, tại TOP_MINSUP
    for label, data in groups.items():
        result = fpgrowth(data, to_min_count(TOP_MINSUP, len(data)))
        named = decode(result, code)                # decode sang tên, sắp xếp theo support giảm dần
        top = sorted(named.items(), key=lambda x: x[1], reverse=True)[:TOP_K]

        print(f"\nTop {TOP_K} của {label} (minsup={TOP_MINSUP}, {len(named)} itemset)")
        for itemset, sup in top:
            print(f"  {sup / len(data):6.1%}  {sup:>4}  {itemset}")


if __name__ == "__main__":
    main()