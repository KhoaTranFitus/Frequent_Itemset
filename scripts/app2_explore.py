"""Ứng dụng 2: kiểm tra ngoại lệ GT-AG và vùng giàu pyrimidine trước acceptor.

Chạy từ thư mục gốc repo:
    python -m scripts.app2_check
"""
from collections import Counter

from src.algorithm.fpgrowth import fpgrowth
from src.app2_bio import load_groups, read_splice, read_splice_with_name
from src.config import to_min_count, use_utf8_stdout
from src.utils import decode

DATA_PATH = "data/app2/splice.data"


def show_exceptions(rows, label, start, expected):
    """In các mẫu thuộc nhãn label mà 2 ký tự tại seq[start:start+2] khác expected."""
    group = [(name, seq) for lab, name, seq in rows if lab == label]
    bad = [(name, seq) for name, seq in group if seq[start:start + 2] != expected]

    print(f"\n{label}: {len(bad)}/{len(group)} mẫu không có {expected}")
    print("  thay vào đó là:", Counter(seq[start:start + 2] for _, seq in bad))
    for name, seq in bad:
        # in 10 ký tự quanh ranh giới, dấu | là ranh giới (giữa vị trí -1 và +1)
        print(f"  {name:<25} {seq[25:30]}|{seq[30:35]}")


def position_of(item):
    """'P-5=C' -> -5, 'P+12=T' -> 12."""
    return int(item[1:item.index("=")])


def single_items(data, code, minsup):
    """Các item đơn (1-itemset) phổ biến, sắp theo vị trí."""
    result = decode(fpgrowth(data, to_min_count(minsup, len(data))), code)
    singles = [(itemset[0], sup) for itemset, sup in result.items() if len(itemset) == 1]
    return sorted(singles, key=lambda x: position_of(x[0]))


def main():
    use_utf8_stdout()

    # Việc 1: ngoại lệ của quy tắc GT-AG
    rows = read_splice_with_name(DATA_PATH)
    show_exceptions(rows, "EI", 30, "GT")    # donor: GT ở +1,+2 = seq[30:32]
    show_exceptions(rows, "IE", 28, "AG")    # acceptor: AG ở -2,-1 = seq[28:30]

    # Việc 2: item đơn của IE ở minsup thấp, tìm vùng giàu C/T
    groups, code = load_groups(DATA_PATH)
    data = groups["IE"]
    print("\nItem đơn của IE ở minsup 0.3, theo vị trí:")
    for item, sup in single_items(data, code, 0.3):
        print(f"  {item:<8} {sup / len(data):6.1%}")


if __name__ == "__main__":
    main()