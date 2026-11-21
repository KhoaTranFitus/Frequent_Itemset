"""Kiểm thử phần sinh luật kết hợp (Chương 3, Ứng dụng 1).

Hai nhóm test:

1. Trên CSDL 4 giao dịch viết thẳng dưới đây, mọi con số đều tính tay được và là
   phân số đẹp, nên test khẳng định đúng giá trị chứ không chỉ "chạy không lỗi".
2. Mốc kiểm chứng trên Groceries thật: minsup 0,01 với minconf 0,5 phải ra đúng
   15 luật, và hai luật kinh điển phải khớp giá trị đã công bố cùng bộ dữ liệu.
   SKIPPED nếu chưa có file.

CSDL nhỏ và toàn bộ số liệu tính tay (N = 4, min_count = 2):

    T1: banh, sua
    T2: banh, ta, bia, trung
    T3: sua, ta, bia, cola
    T4: banh, sua, ta, bia

    sup: banh 3, sua 3, ta 3, bia 3   (trung 1 và cola 1 bị loại)
         (banh,bia) 2  (banh,sua) 2  (banh,ta) 2
         (bia,sua)  2  (bia,ta)   3  (sua,ta)  2
         (banh,bia,ta) 2  (bia,sua,ta) 2
    -> 12 tập phổ biến: 4 tập 1 item, 6 tập 2 item, 2 tập 3 item

    {ta} -> {bia}:   sup 3/4 = 0,75   conf 3/3 = 1        lift 1/(3/4) = 4/3
                     leverage = 3/4 - (3/4)(3/4) = 3/16
    {bia} -> {banh}: sup 2/4 = 0,5    conf 2/3            lift (2/3)/(3/4) = 8/9
                     leverage = 1/2 - (3/4)(3/4) = -1/16

    Số luật với max_consequent=1: minconf 0,5 -> 18; minconf 1,0 -> 6.
"""
import os
from fractions import Fraction

import pytest

from src.algorithm.fpgrowth import fpgrowth
from src.apps.basket import read_baskets
from src.config import GROCERIES, to_min_count
from src.rules import (ROW_COLUMNS, format_rule, generate_rules, rule_names,
                       rules_to_rows, sort_rules)
from src.utils import encode, invert_code

BASKETS = [
    ["banh", "sua"],
    ["banh", "ta", "bia", "trung"],
    ["sua", "ta", "bia", "cola"],
    ["banh", "sua", "ta", "bia"],
]

need_groceries = pytest.mark.skipif(
    not os.path.exists(GROCERIES),
    reason=f"chưa có {GROCERIES}",
)


def small(min_count=2):
    """-> (itemsets, N, code, name_of) của CSDL nhỏ ở trên."""
    encoded, code = encode(BASKETS)
    itemsets = fpgrowth(encoded, min_count)
    return itemsets, len(encoded), code, invert_code(code)


def find(rules, left, right, name_of):
    """Tìm đúng một luật theo tên item; lỗi nếu không có hoặc có nhiều hơn một."""
    hits = [r for r in rules
            if set(rule_names(r, name_of)[0]) == set(left)
            and set(rule_names(r, name_of)[1]) == set(right)]
    assert len(hits) == 1, f"tìm thấy {len(hits)} luật cho {left} -> {right}"
    return hits[0]


# --------------------------------------------------------------------------
# 1. Giá trị tính tay
# --------------------------------------------------------------------------

def test_so_tap_pho_bien_cua_csdl_nho():
    """Chốt lại đầu vào trước khi kiểm luật: phải đúng 12 tập phổ biến."""
    itemsets, n, _, _ = small()
    assert n == 4
    assert len(itemsets) == 12
    sizes = sorted(len(k) for k in itemsets)
    assert sizes.count(1) == 4 and sizes.count(2) == 6 and sizes.count(3) == 2


def test_tinh_tay_luat_confidence_mot():
    """{ta} -> {bia}: conf = 1, lift = 4/3, leverage = 3/16."""
    itemsets, n, _, name_of = small()
    rule = find(generate_rules(itemsets, n, 0.5), ["ta"], ["bia"], name_of)

    assert rule.support_count == 3
    assert rule.support == pytest.approx(Fraction(3, 4))
    assert rule.confidence == pytest.approx(1.0)
    assert rule.lift == pytest.approx(Fraction(4, 3))
    assert rule.leverage == pytest.approx(Fraction(3, 16))


def test_tinh_tay_luat_lift_duoi_mot():
    """{bia} -> {banh}: conf = 2/3, lift = 8/9 (nhỏ hơn 1 nên hai món đẩy nhau)."""
    itemsets, n, _, name_of = small()
    rule = find(generate_rules(itemsets, n, 0.5), ["bia"], ["banh"], name_of)

    assert rule.support_count == 2
    assert rule.support == pytest.approx(Fraction(1, 2))
    assert rule.confidence == pytest.approx(Fraction(2, 3))
    assert rule.lift == pytest.approx(Fraction(8, 9))
    assert rule.leverage == pytest.approx(Fraction(-1, 16))


def test_so_luat_dung_bang_tay():
    itemsets, n, _, _ = small()
    assert len(generate_rules(itemsets, n, 0.5)) == 18
    assert len(generate_rules(itemsets, n, 1.0)) == 6


# --------------------------------------------------------------------------
# 2. Bất biến toán học — bắt được lỗi tra sai support
# --------------------------------------------------------------------------

def test_confidence_khong_vuot_qua_mot():
    itemsets, n, _, _ = small()
    for rule in generate_rules(itemsets, n, 0.01, max_consequent=None):
        assert 0 < rule.confidence <= 1


def test_support_bang_support_cua_hop():
    """support_count của luật phải đúng bằng sup của tập hợp X hợp Y."""
    itemsets, n, _, _ = small()
    for rule in generate_rules(itemsets, n, 0.01, max_consequent=None):
        key = tuple(sorted(rule.antecedent + rule.consequent))
        assert rule.support_count == itemsets[key]
        assert rule.support == pytest.approx(itemsets[key] / n)


def test_lift_doi_xung():
    """lift(X -> Y) = lift(Y -> X) vì cả hai đều bằng sup(Z)·N / (sup(X)·sup(Y))."""
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.01, max_consequent=None)
    by_pair = {(r.antecedent, r.consequent): r.lift for r in rules}

    checked = 0
    for (left, right), lift in by_pair.items():
        if (right, left) in by_pair:
            assert lift == pytest.approx(by_pair[(right, left)])
            checked += 1
    assert checked > 0, "không có cặp luật ngược chiều nào để kiểm"


def test_leverage_khop_dinh_nghia():
    itemsets, n, _, _ = small()
    for rule in generate_rules(itemsets, n, 0.01, max_consequent=None):
        sup_x = itemsets[rule.antecedent] / n
        sup_y = itemsets[rule.consequent] / n
        assert rule.leverage == pytest.approx(rule.support - sup_x * sup_y)


def test_lift_bang_mot_khi_doc_lap():
    """Hai item độc lập hoàn toàn thì lift đúng bằng 1.

    4 giao dịch: A có ở 2 giao dịch, B có ở 2 giao dịch, và đúng 1 giao dịch có
    cả hai. sup(AB)/N = 1/4 = (2/4)·(2/4) nên A và B độc lập.
    """
    data = [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]]
    encoded, code = encode(data)
    itemsets = fpgrowth(encoded, 1)
    rules = generate_rules(itemsets, len(encoded), 0.01)

    rule = find(rules, ["a"], ["b"], invert_code(code))
    assert rule.lift == pytest.approx(1.0)
    assert rule.leverage == pytest.approx(0.0)


# --------------------------------------------------------------------------
# 3. Tham số và trường hợp biên
# --------------------------------------------------------------------------

def test_bien_minconf_dung_dau_bang():
    """Lọc bằng >=, nên luật có confidence đúng bằng ngưỡng vẫn được giữ.

    Ngưỡng phải truyền ở dạng float 2/3, đúng kiểu mà phép chia sup_z/sup_x cho
    ra. Nếu truyền Fraction(2, 3) thì đó là phân số chính xác, lớn hơn float
    0,6666666666666666 một chút, và luật sẽ bị lọc oan — đây cũng là lý do mọi
    so sánh số thực trong test đều đi qua pytest.approx.
    """
    itemsets, n, _, name_of = small()
    rule = find(generate_rules(itemsets, n, 2 / 3), ["bia"], ["banh"], name_of)
    assert rule.confidence == pytest.approx(Fraction(2, 3))

    # nhích ngưỡng lên trên 2/3 thì luật đó phải biến mất
    higher = generate_rules(itemsets, n, 0.667)
    assert not [r for r in higher
                if set(rule_names(r, name_of)[0]) == {"bia"}
                and set(rule_names(r, name_of)[1]) == {"banh"}]


def test_max_consequent_mot_item():
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.01, max_consequent=1)
    assert rules and all(len(r.consequent) == 1 for r in rules)


def test_max_consequent_none_cho_moi_cach_tach():
    """Không giới hạn thì mỗi tập phổ biến kích thước k cho đúng 2**k - 2 luật."""
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.01, max_consequent=None)

    expected = sum(2 ** len(k) - 2 for k in itemsets if len(k) >= 2)
    assert len(rules) == expected == 6 * 2 + 2 * 6      # 6 tập 2 item, 2 tập 3 item


def test_max_consequent_lon_hon_kich_thuoc_tap():
    """max_consequent=5 trên tập 3 item vẫn phải để bên trái còn ít nhất 1 item."""
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.01, max_consequent=5)
    assert all(r.antecedent for r in rules)
    assert len(rules) == len(generate_rules(itemsets, n, 0.01, max_consequent=None))


def test_tap_mot_item_khong_sinh_luat():
    itemsets = {(1,): 4, (2,): 3}
    assert generate_rules(itemsets, 4, 0.01, max_consequent=None) == []


def test_tham_so_sai_thi_bao_loi():
    itemsets, n, _, _ = small()
    for bad in (0, -0.1, 1.5):
        with pytest.raises(ValueError):
            generate_rules(itemsets, n, bad)
    with pytest.raises(ValueError):
        generate_rules(itemsets, 0, 0.5)
    with pytest.raises(ValueError):
        generate_rules(itemsets, n, 0.5, max_consequent=0)


def test_dict_thieu_tap_con_thi_bao_loi():
    """Dict thiếu singleton thì phải nổ KeyError, không được trả số sai."""
    itemsets, n, code, _ = small()
    thieu = {k: v for k, v in itemsets.items() if k != (code["bia"],)}

    with pytest.raises(KeyError, match="không đầy đủ"):
        generate_rules(thieu, n, 0.01, max_consequent=None)


# --------------------------------------------------------------------------
# 4. Sắp xếp và trình bày
# --------------------------------------------------------------------------

def test_sort_giam_dan_va_xac_dinh():
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.01, max_consequent=None)

    for by in ("lift", "confidence", "support", "leverage"):
        ordered = sort_rules(rules, by=by)
        values = [getattr(r, "support_count" if by == "support" else by) for r in ordered]
        assert values == sorted(values, reverse=True)
        # đảo thứ tự đầu vào vẫn phải ra đúng thứ tự đó
        assert sort_rules(list(reversed(rules)), by=by) == ordered


def test_sort_khong_sua_list_goc():
    itemsets, n, _, _ = small()
    rules = generate_rules(itemsets, n, 0.5)
    truoc = list(rules)
    sort_rules(rules)
    assert rules == truoc


def test_sort_tieu_chi_sai_thi_bao_loi():
    with pytest.raises(ValueError):
        sort_rules([], by="khong_co")


def test_format_rule():
    itemsets, n, _, name_of = small()
    rule = find(generate_rules(itemsets, n, 0.5), ["banh", "ta"], ["bia"], name_of)
    assert format_rule(rule, name_of) == "{banh, ta} -> {bia}"
    assert format_rule(rule) == "{1, 5} -> {2}"      # không truyền name_of thì in số


def test_rules_to_rows():
    itemsets, n, _, name_of = small()
    rule = find(generate_rules(itemsets, n, 0.5), ["banh", "ta"], ["bia"], name_of)
    row = rules_to_rows([rule], name_of)[0]

    assert len(row) == len(ROW_COLUMNS)
    cells = dict(zip(ROW_COLUMNS, row))
    assert cells["antecedent"] == "banh|ta"          # ghép bằng | vì CSV dùng dấu phẩy
    assert cells["consequent"] == "bia"
    assert cells["n_antecedent"] == 2 and cells["n_consequent"] == 1
    assert cells["support_count"] == 2
    assert float(cells["confidence"]) == pytest.approx(1.0)


# --------------------------------------------------------------------------
# 5. Đầu-cuối và mốc kiểm chứng Groceries
# --------------------------------------------------------------------------

def test_dau_cuoi_tren_csdl_nho():
    """read_baskets -> encode -> fpgrowth -> generate_rules -> đổi về tên item."""
    itemsets, n, _, name_of = small()
    rules = sort_rules(generate_rules(itemsets, n, 0.5))

    duoc = {(rule_names(r, name_of)[0], rule_names(r, name_of)[1]):
            (r.support_count, round(r.confidence, 6), round(r.lift, 6))
            for r in rules}

    assert duoc[(("ta",), ("bia",))] == (3, 1.0, round(4 / 3, 6))
    assert duoc[(("bia",), ("banh",))] == (2, round(2 / 3, 6), round(8 / 9, 6))
    assert duoc[(("banh", "ta"), ("bia",))] == (2, 1.0, round(4 / 3, 6))
    assert len(duoc) == 18


@need_groceries
def test_moc_groceries_so_luat():
    """minsup 0,01 + minconf 0,5 phải ra đúng 15 luật — giá trị đã công bố."""
    encoded, _ = encode(read_baskets(GROCERIES))
    itemsets = fpgrowth(encoded, to_min_count(0.01, len(encoded)))

    assert len(itemsets) == 333
    assert len(generate_rules(itemsets, len(encoded), 0.5)) == 15
    assert len(generate_rules(itemsets, len(encoded), 0.3)) == 125


@need_groceries
def test_moc_groceries_gia_tri_luat():
    """Hai luật kinh điển phải khớp giá trị đã công bố tới 4 chữ số thập phân."""
    encoded, code = encode(read_baskets(GROCERIES))
    n = len(encoded)
    itemsets = fpgrowth(encoded, to_min_count(0.01, n))
    rules = generate_rules(itemsets, n, 0.3)
    name_of = invert_code(code)

    rule = find(rules, ["other vegetables", "yogurt"], ["whole milk"], name_of)
    assert rule.support == pytest.approx(0.02227, abs=1e-5)
    assert rule.confidence == pytest.approx(0.51288, abs=1e-5)
    assert rule.lift == pytest.approx(2.00723, abs=1e-5)

    rule = find(rules, ["butter"], ["whole milk"], name_of)
    assert rule.support == pytest.approx(0.02755, abs=1e-5)
    assert rule.confidence == pytest.approx(0.49725, abs=1e-5)
    assert rule.lift == pytest.approx(1.94605, abs=1e-5)


@need_groceries
def test_moc_groceries_top_lift():
    """Luật lift cao nhất ở minsup 0,01 / minconf 0,3 và thứ tự top-3."""
    encoded, code = encode(read_baskets(GROCERIES))
    n = len(encoded)
    itemsets = fpgrowth(encoded, to_min_count(0.01, n))
    top = sort_rules(generate_rules(itemsets, n, 0.3))[:3]
    name_of = invert_code(code)

    assert [format_rule(r, name_of) for r in top] == [
        "{citrus fruit, other vegetables} -> {root vegetables}",
        "{other vegetables, tropical fruit} -> {root vegetables}",
        "{beef} -> {root vegetables}",
    ]
    assert top[0].lift == pytest.approx(3.29505, abs=1e-5)
