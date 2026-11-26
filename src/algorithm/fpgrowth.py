import argparse
import math
from itertools import combinations

from src.utils import read_transactions, find_frequent_items, write_result
from src.structures import build_tree, get_prefix_paths, build_conditional_tree


def get_single_path(root):
    """Trả về [(item, count), ...] nếu cây chỉ có một nhánh, ngược lại None."""
    path = []
    node = root
    while node.children:
        if len(node.children) > 1:
            return None
        node = next(iter(node.children.values()))
        path.append((node.item, node.count))
    return path


def add_single_path(path, suffix, result):
    """Lemma 3.2: mọi tổ hợp của một nhánh đều phổ biến, support = min count.

    Count giảm dần dọc theo nhánh (cha luôn >= con), và combinations giữ nguyên
    thứ tự của path, nên count nhỏ nhất của một tổ hợp chính là count của phần
    tử cuối cùng: combo[-1][1]. Không cần gọi min() trên cả tổ hợp.
    """
    for r in range(1, len(path) + 1):
        for combo in combinations(path, r):
            items = [x[0] for x in combo]
            support = combo[-1][1]          # = min(count) vì count giảm dần dọc nhánh
            result[tuple(sorted(suffix + items))] = support


def mine_tree(root, header, freq, suffix, min_count, result):
    path = get_single_path(root)
    if path is not None:
        add_single_path(path, suffix, result)
        return

    # duyệt từ item ít phổ biến nhất lên
    items = sorted(freq, key=lambda i: (freq[i], i))
    for item in items:
        new_suffix = suffix + [item]
        result[tuple(sorted(new_suffix))] = freq[item]

        paths = get_prefix_paths(item, header)
        cond_root, cond_header, cond_freq = build_conditional_tree(paths, min_count)
        if cond_freq:
            mine_tree(cond_root, cond_header, cond_freq, new_suffix, min_count, result)


def fpgrowth(transactions, min_count):
    freq = find_frequent_items(transactions, min_count)
    flist = sorted(freq, key=lambda i: (-freq[i], i))
    rank = {i: k for k, i in enumerate(flist)}
    root, header = build_tree(transactions, rank)
    result = {}
    mine_tree(root, header, freq, [], min_count, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="FP-Growth khai thác tập phổ biến (định dạng SPMF)")
    parser.add_argument("input", help="đường dẫn file input (SPMF .txt)")
    parser.add_argument("--minsup", type=float, required=True,
                        help="minsup tương đối trong (0, 1], ví dụ 0.4")
    parser.add_argument("--output", default="output.txt", help="file kết quả")
    args = parser.parse_args()

    if not (0 < args.minsup <= 1):
        parser.error("--minsup phải nằm trong khoảng (0, 1]")

    data = read_transactions(args.input)
    min_count = math.ceil(round(args.minsup * len(data), 9))
    result = fpgrowth(data, min_count)
    write_result(result, args.output)
    print(f"{len(data)} giao dịch, min_count = {min_count}, "
          f"tìm được {len(result)} tập phổ biến")


if __name__ == "__main__":
    main()