"""Kiểm thử phần đọc dữ liệu giỏ hàng của Ứng dụng 1 (Chương 3).

Hai nhóm test:

1. read_baskets / describe / shuffle_keep_marginals trên dữ liệu nhỏ viết tạm,
   kiểm được từng trường hợp biên (dòng trống, dấu phẩy cuối dòng, khoảng trắng).
2. Mốc kiểm chứng trên CSDL Groceries thật: các con số này đã được công bố rộng
   rãi cùng bộ dữ liệu, nên nếu cài đặt của nhóm ra đúng thì phần đọc dữ liệu và
   phần đếm support đều đúng. SKIPPED nếu chưa có file.
"""
import os
from collections import Counter

import pytest

from src.algorithm.fpgrowth import fpgrowth
from src.apps.basket import describe, read_baskets, shuffle_keep_marginals
from src.config import GROCERIES, SEED, to_min_count
from src.utils import encode

SMALL = "citrus fruit,yogurt\n\nwhole milk\n  bread , butter ,\nwhole milk,bread\n"

need_groceries = pytest.mark.skipif(
    not os.path.exists(GROCERIES),
    reason=f"chưa có {GROCERIES}",
)


def write_small(tmp_path):
    path = tmp_path / "small.csv"
    path.write_text(SMALL, encoding="utf-8")
    return str(path)


def test_read_baskets_small(tmp_path):
    baskets = read_baskets(write_small(tmp_path))
    assert baskets == [
        ["citrus fruit", "yogurt"],          # bình thường
        ["whole milk"],                      # dòng trống phía trên bị bỏ
        ["bread", "butter"],                 # khoảng trắng bị cắt, dấu phẩy cuối không sinh item rỗng
        ["whole milk", "bread"],
    ]


def test_read_baskets_keeps_spaces_inside_names(tmp_path):
    # "citrus fruit" là MỘT item, không phải hai; chỉ khoảng trắng ở hai đầu bị cắt
    baskets = read_baskets(write_small(tmp_path))
    assert "citrus fruit" in baskets[0]


def test_describe_small(tmp_path):
    stats = describe(read_baskets(write_small(tmp_path)))
    assert stats["transactions"] == 4
    assert stats["items"] == 5                   # citrus fruit, yogurt, whole milk, bread, butter
    assert stats["occurrences"] == 7
    assert stats["avg_len"] == pytest.approx(7 / 4)
    assert stats["min_len"] == 1 and stats["max_len"] == 2
    assert stats["density"] == pytest.approx(7 / (4 * 5))


def test_describe_empty():
    assert describe([]) == {
        "transactions": 0, "items": 0, "occurrences": 0,
        "avg_len": 0.0, "min_len": 0, "max_len": 0, "density": 0.0,
    }


def test_shuffle_keeps_marginals_and_lengths(tmp_path):
    baskets = read_baskets(write_small(tmp_path))
    shuffled = shuffle_keep_marginals(baskets, SEED)

    assert [len(t) for t in shuffled] == [len(t) for t in baskets]
    assert Counter(i for t in shuffled for i in t) == Counter(i for t in baskets for i in t)
    assert baskets == read_baskets(write_small(tmp_path))      # không sửa danh sách gốc


def test_shuffle_is_deterministic(tmp_path):
    baskets = read_baskets(write_small(tmp_path))
    assert shuffle_keep_marginals(baskets, SEED) == shuffle_keep_marginals(baskets, SEED)
    # seed khác thì nói chung ra khác; kiểm trên dữ liệu đủ lớn để không gặp trùng ngẫu nhiên
    big = baskets * 50
    assert shuffle_keep_marginals(big, SEED) != shuffle_keep_marginals(big, SEED + 1)


@need_groceries
def test_groceries_shape():
    """9.835 giỏ, 169 item, 43.367 lượt item — thông số công bố của bộ Groceries."""
    stats = describe(read_baskets(GROCERIES))
    assert stats["transactions"] == 9835
    assert stats["items"] == 169
    assert stats["occurrences"] == 43367
    assert stats["avg_len"] == pytest.approx(4.4095, abs=1e-4)


@need_groceries
def test_groceries_no_duplicate_item_in_basket():
    baskets = read_baskets(GROCERIES)
    assert all(len(set(t)) == len(t) for t in baskets)


@need_groceries
def test_groceries_whole_milk_support():
    """support(whole milk) = 2513/9835 = 0,25552 — giá trị đã công bố.

    Đi qua đúng đường mà ứng dụng dùng: read_baskets -> encode -> fpgrowth, nên
    test này chứng minh cả ba khâu khớp nhau.
    """
    baskets = read_baskets(GROCERIES)
    encoded, code = encode(baskets)
    result = fpgrowth(encoded, to_min_count(0.01, len(encoded)))

    support = result[(code["whole milk"],)]
    assert support == 2513
    assert support / len(encoded) == pytest.approx(0.25552, abs=1e-5)
