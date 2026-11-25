"""Sinh luật kết hợp từ tập phổ biến (Chương 3, Ứng dụng 1).

Module này chỉ tiêu thụ dict kết quả của fpgrowth, không import gì từ
src.algorithm, nên phân tầng một chiều algorithm -> structures -> utils của đồ án
không bị động tới.

Định nghĩa dùng trong đồ án (ký hiệu: N = số giao dịch, sup(S) = số giao dịch
chứa trọn tập S):

    luật           X -> Y   với X, Y rời nhau và khác rỗng, Z = X hợp Y
    support(Z)   = sup(Z) / N                      -- luật này phủ bao nhiêu giỏ
    confidence   = sup(Z) / sup(X)                 -- mua X thì bao nhiêu phần mua Y
    lift         = confidence / (sup(Y) / N)       -- so với mua Y một cách độc lập
    leverage     = sup(Z)/N - sup(X)/N * sup(Y)/N  -- phần giỏ tăng thêm tuyệt đối

Cả bốn đo lường đều cần thiết và không thay thế được nhau:

- support nói luật có đáng làm không (luật đúng trên 3 giỏ thì không làm gì được),
- confidence nói từ X có dự đoán được Y không,
- lift nói X và Y có thật là liên quan không, hay chỉ vì Y vốn bán rất chạy
  (lift = 1 là độc lập, lớn hơn 1 là hút nhau, nhỏ hơn 1 là đẩy nhau),
- leverage nói quan hệ đó đổi ra bao nhiêu giỏ, nên luật lift cao mà support bé
  tí thì leverage sẽ lộ ra ngay là không đáng làm.

Vì sao sup(X) và sup(Y) luôn tra được: X và Y là tập con thực sự của Z, mà Z là
tập phổ biến, nên theo tính chất đóng xuống của Apriori (tập con của tập phổ biến
cũng phổ biến) cả hai đều phổ biến; fpgrowth của nhóm trả về TOÀN BỘ tập phổ biến
kể cả các tập một phần tử, nên chúng chắc chắn có trong dict. Nếu tra không thấy
thì dict đầu vào bị thiếu (ví dụ ai đó đã lọc bỏ singleton), và hàm báo lỗi rõ
ràng chứ không âm thầm trả số sai.
"""
from collections import namedtuple
from itertools import combinations

# Một luật kết hợp. antecedent và consequent là tuple item đã sắp; item ở dạng
# nào thì tùy đầu vào (thường là số nguyên sau encode, đổi về tên khi trình bày).
Rule = namedtuple(
    "Rule",
    "antecedent consequent support_count support confidence lift leverage",
)

# Cột của CSV luật, dùng chung cho script và notebook.
ROW_COLUMNS = ["antecedent", "consequent", "n_antecedent", "n_consequent",
               "support_count", "support", "confidence", "lift", "leverage"]


def _support(itemsets, items):
    """sup của một tập item, với thông báo lỗi rõ ràng nếu dict thiếu tập con."""
    key = tuple(sorted(items))
    try:
        return itemsets[key]
    except KeyError:
        raise KeyError(
            f"dict tập phổ biến không đầy đủ: thiếu tập con {key}. "
            "generate_rules cần toàn bộ tập phổ biến (kể cả tập một phần tử) "
            "như fpgrowth trả về, không dùng được với dict đã lọc bớt."
        ) from None


def generate_rules(itemsets, n_transactions, min_conf, max_consequent=1):
    """Sinh mọi luật kết hợp có confidence >= min_conf từ tập phổ biến.

    itemsets: dict {tuple item đã sắp: support tuyệt đối} — đúng thứ fpgrowth
        trả về. Phải là kết quả đầy đủ, kể cả các tập một phần tử.
    n_transactions: N, số giao dịch của CSDL gốc. Cần để tính support tương đối
        và lift; không suy ra được từ dict nên phải truyền vào.
    min_conf: ngưỡng confidence trong (0, 1]. Lọc bằng >= cho giống cách
        find_frequent_items lọc support (support >= min_count) và giống SPMF.
    max_consequent: số item tối đa ở bên phải luật. Mặc định 1 (luật dạng
        "mua X thì mua thêm món Y"), là dạng dùng được trong phân tích giỏ hàng
        và cũng là dạng đọc được. None nghĩa là xét mọi cách tách, tức
        2**k - 2 luật cho mỗi tập phổ biến kích thước k.

    Trả về list các Rule, THEO THỨ TỰ DUYỆT (chưa sắp) — dùng sort_rules để sắp.

    Mọi tập phổ biến kích thước từ 2 trở lên đều được xét; tập một phần tử không
    sinh được luật nào vì cắt ra là có bên rỗng.
    """
    if not 0 < min_conf <= 1:
        raise ValueError("min_conf phải nằm trong khoảng (0, 1]")
    if n_transactions <= 0:
        raise ValueError("n_transactions phải là số dương")
    if max_consequent is not None and max_consequent < 1:
        raise ValueError("max_consequent phải từ 1 trở lên, hoặc None nếu không giới hạn")

    n = n_transactions
    rules = []

    for itemset, sup_z in itemsets.items():
        k = len(itemset)
        if k < 2:
            continue

        # bên phải nhiều nhất k - 1 item, vì bên trái phải còn ít nhất 1 item
        limit = k - 1 if max_consequent is None else min(max_consequent, k - 1)

        for size in range(1, limit + 1):
            for consequent in combinations(itemset, size):
                tail = set(consequent)
                antecedent = tuple(i for i in itemset if i not in tail)

                sup_x = _support(itemsets, antecedent)
                confidence = sup_z / sup_x
                if confidence < min_conf:
                    continue

                sup_y = _support(itemsets, consequent)
                rules.append(Rule(
                    antecedent=antecedent,
                    consequent=consequent,
                    support_count=sup_z,
                    support=sup_z / n,
                    confidence=confidence,
                    lift=confidence / (sup_y / n),
                    leverage=sup_z / n - (sup_x / n) * (sup_y / n),
                ))

    return rules


# Khóa sắp cho từng tiêu chí. Tiêu chí phụ luôn đi kèm để thứ tự là XÁC ĐỊNH:
# hai luật cùng lift mà không có tiêu chí phụ thì mỗi lần chạy lại đổi chỗ nhau,
# và bảng top-10 trong báo cáo sẽ không khớp notebook. Bước cuối so antecedent
# rồi consequent nên kết quả không phụ thuộc thứ tự duyệt dict.
_SORT_KEYS = {
    "lift": lambda r: (-r.lift, -r.confidence, -r.support_count),
    "confidence": lambda r: (-r.confidence, -r.lift, -r.support_count),
    "support": lambda r: (-r.support_count, -r.lift, -r.confidence),
    "leverage": lambda r: (-r.leverage, -r.lift, -r.confidence),
}


def sort_rules(rules, by="lift"):
    """Sắp luật giảm dần theo một tiêu chí, có tie-break xác định.

    by: "lift" (mặc định, đề yêu cầu top-10 theo lift), "confidence", "support"
    hoặc "leverage". Không sửa list gốc.
    """
    if by not in _SORT_KEYS:
        raise ValueError(f"tiêu chí không hợp lệ: {by}. "
                         f"Chọn một trong {sorted(_SORT_KEYS)}")
    primary = _SORT_KEYS[by]
    return sorted(rules, key=lambda r: primary(r) + (r.antecedent, r.consequent))


def rule_names(rule, name_of=None):
    """Đổi một luật về tên item -> (tuple tên bên trái, tuple tên bên phải).

    name_of: dict {số: tên item}, lấy bằng src.utils.invert_code(code). Để None
    nếu item vốn đã là thứ muốn in (ví dụ retail.txt, item đã là số).
    """
    if name_of is None:
        return rule.antecedent, rule.consequent
    return (tuple(name_of[i] for i in rule.antecedent),
            tuple(name_of[i] for i in rule.consequent))


def format_rule(rule, name_of=None):
    """Chuỗi một dòng của luật, dạng '{rau củ, sữa chua} -> {sữa}'."""
    left, right = rule_names(rule, name_of)
    left_text = ", ".join(str(i) for i in left)
    right_text = ", ".join(str(i) for i in right)
    return "{" + left_text + "} -> {" + right_text + "}"


def rules_to_rows(rules, name_of=None):
    """Đổi list Rule thành list dòng CSV theo đúng thứ tự ROW_COLUMNS.

    Tên item trong một tập được ghép bằng dấu | chứ không phải dấu phẩy, vì dấu
    phẩy là dấu phân cột của CSV và tên item Groceries có cả dấu cách.
    """
    rows = []
    for rule in rules:
        left, right = rule_names(rule, name_of)
        rows.append([
            "|".join(str(i) for i in left),
            "|".join(str(i) for i in right),
            len(left),
            len(right),
            rule.support_count,
            f"{rule.support:.6f}",
            f"{rule.confidence:.6f}",
            f"{rule.lift:.6f}",
            f"{rule.leverage:.6f}",
        ])
    return rows
