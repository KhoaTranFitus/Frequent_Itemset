import argparse
import math

from src.utils import read_transactions, find_frequent_items,write_result
from src.structures import build_tree, get_prefix_paths, build_conditional_tree


def mine_tree (header, freq, suffix, min_count, result):
    # duyệt item tuef ít phổ biến nhất lên (ngược flist)
    items = sorted (freq, key = lambda i: (freq[i], i))
    for item in items:
        new_suffix = suffix + [item]
        result[tuple(sorted(new_suffix))] = freq[item]

        paths = get_prefix_paths(item,header)
        cond_root, cond_header, cond_freq = build_conditional_tree(paths,min_count)

        if cond_freq:
            mine_tree(cond_header,cond_freq,new_suffix, min_count, result)


def fpgrowth(transactions, min_count):
    freq = find_frequent_items(transactions, min_count)
    flist = sorted(freq, key=lambda i: (-freq[i], i))
    rank = {i: k for k, i in enumerate(flist)}
    root, header = build_tree(transactions, rank)
    result = {}
    mine_tree(header, freq, [], min_count, result)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input",help ="đường dẫn file input")
    parser.add_argument ("--minsup", type=float,required=True, help="minsup tương đối, vd 0.4")
    parser.add_argument("--output", default="output.txt")
    args = parser.parse_args()

    data = read_transactions(args.input)
    min_count = math.ceil(args.minsup * len(data))
    result = fpgrowth (data, min_count)
    write_result(result, args.output)
    print(f"Tìm được {len(result)} tập phổ biến")