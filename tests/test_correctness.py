import os

import pytest

from src.config import ref_path, to_min_count
from src.utils import read_transactions, read_result, compare
from src.algorithm.fpgrowth import fpgrowth
from src.algorithm.fpgrowth_basic import fpgrowth as fpgrowth_basic

# (tên, file, minsup, số tập tính tay)
CASES = [
    ("test1", "data/toy/toy_test1.txt", 0.6,   18),
    ("test2", "data/toy/toy_test2.txt", 0.5,   10),
    ("test2", "data/toy/toy_test2.txt", 0.375, 14),
    ("test3", "data/toy/toy_test3.txt", 0.5,   15),
    ("test3", "data/toy/toy_test3.txt", 0.33,  31),
    ("test4", "data/toy/toy_test4.txt", 0.3,    6),
    ("test4", "data/toy/toy_test4.txt", 0.2,   13),
]


@pytest.mark.parametrize("name, path, minsup, expected", CASES)
def test_count_by_hand(name, path, minsup, expected):
    data = read_transactions(path)
    result = fpgrowth(data, to_min_count(minsup, len(data)))
    assert len(result) == expected


@pytest.mark.parametrize("name, path, minsup, expected", CASES)
def test_optimized_equals_basic(name, path, minsup, expected):
    data = read_transactions(path)
    mc = to_min_count(minsup, len(data))
    assert fpgrowth(data, mc) == fpgrowth_basic(data, mc)


@pytest.mark.parametrize("name, path, minsup, expected", CASES)
def test_matches_spmf(name, path, minsup, expected):
    ref_file = ref_path(name, minsup)
    if not os.path.exists(ref_file):
        pytest.skip(f"thiếu ref: {ref_file}")
    data = read_transactions(path)
    mine = fpgrowth(data, to_min_count(minsup, len(data)))
    matched, mismatched, extra, missing = compare(mine, read_result(ref_file))
    assert not mismatched and not extra and not missing


def test_paper_example():
    # ví dụ bài báo (đã đổi chữ sang số): {a,c,f,m} = {1,3,6,13}, {c,p} = {3,16}
    data = read_transactions("data/toy/toy_test1.txt")
    result = fpgrowth(data, 3)
    assert result[(1, 3, 6, 13)] == 3
    assert result[(3, 16)] == 3
    assert result[(3,)] == 4 and result[(6,)] == 4


def test_duplicates_and_blank_lines():
    path = "data/toy/_dirty_tmp.txt"
    with open(path, "w") as f:
        f.write("1 1 2\n\n1 2 3 1 2 3 4 5\n1 1 2\n")
    try:
        data = read_transactions(path)
        assert len(data) == 3                      # dòng trống bị bỏ
        result = fpgrowth(data, 2)
        assert result == {(1,): 3, (2,): 3, (1, 2): 3}
    finally:
        os.remove(path)