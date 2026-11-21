"""Kiểm thử encode/decode: đổi item dạng chữ sang số và đổi ngược lại.

Hai ứng dụng ở chương 3 đều phải biến dữ liệu gốc thành giao dịch số nguyên
trước khi chạy fpgrowth, nên phần mã hóa này cần đúng và tái lập được.
"""
import math

from src.utils import encode, decode, invert_code
from src.algorithm.fpgrowth import fpgrowth

# giỏ hàng nhỏ, item là chữ
BASKETS = [
    ["bread", "milk"],
    ["bread", "butter"],
    ["bread", "milk", "butter"],
    ["milk"],
]


def test_code_is_dense_and_starts_at_one():
    encoded, code = encode(BASKETS)
    assert sorted(code.values()) == [1, 2, 3]
    # mọi item trong giao dịch đã mã hóa đều là số nguyên dương
    assert all(isinstance(i, int) and i > 0 for t in encoded for i in t)


def test_code_follows_sorted_names():
    _, code = encode(BASKETS)
    assert code == {"bread": 1, "butter": 2, "milk": 3}


def test_encode_is_deterministic():
    # đổi thứ tự giao dịch không được làm đổi bảng mã
    _, code1 = encode(BASKETS)
    _, code2 = encode(list(reversed(BASKETS)))
    assert code1 == code2


def test_start_param():
    _, code = encode(BASKETS, start=10)
    assert sorted(code.values()) == [10, 11, 12]


def test_invert_code_round_trip():
    _, code = encode(BASKETS)
    name_of = invert_code(code)
    assert all(name_of[num] == name for name, num in code.items())


def test_duplicate_items_are_kept():
    encoded, code = encode([["a", "a", "b"]])
    assert encoded == [[code["a"], code["a"], code["b"]]]


def test_empty_input():
    encoded, code = encode([])
    assert encoded == [] and code == {}


def test_mixed_types_do_not_crash():
    # dữ liệu lẫn số và chữ vẫn mã hóa được (sắp theo chuỗi)
    encoded, code = encode([[1, "a"], ["a", 2]])
    assert len(code) == 3
    assert all(isinstance(i, int) for t in encoded for i in t)


def test_fpgrowth_round_trip():
    # mã hóa -> khai thác -> giải mã, kết quả phải khớp tính tay
    encoded, code = encode(BASKETS)
    min_count = math.ceil(round(0.5 * len(encoded), 9))   # = 2
    result = decode(fpgrowth(encoded, min_count), code)

    assert result == {
        ("bread",): 3,
        ("milk",): 3,
        ("butter",): 2,
        ("bread", "milk"): 2,
        ("bread", "butter"): 2,
    }


def test_decoded_itemsets_are_sorted_by_name():
    # encode gán số theo thứ tự item đã sắp, nên itemset giải mã ra cũng đã sắp
    encoded, code = encode(BASKETS)
    for itemset in decode(fpgrowth(encoded, 2), code):
        assert list(itemset) == sorted(itemset)
