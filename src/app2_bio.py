from src.utils import encode

VALID = set("ACGT")

def read_splice(path):
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue  # bo qua dong trong
            parts = [p.strip() for p in line.split(",")] # parts[0] là nhãn, parts[1] là tên mẫu, parts[2] là chuỗi
            rows.append((parts[0], parts[2]))
    return rows
def position_name(i):
    if i < 30:
        pos = i - 30
    else:
        pos = i-29
    return f"{pos:+d}"     # +d: luôn ghi dấu, ví dụ "+1", "-30"


def to_transaction(seq):
    items = []
    for i, base in enumerate(seq):
        if base not in VALID:
            continue                 # bỏ ký tự không chắc chắn (D, N, S, R)
        items.append(f"P{position_name(i)}={base}")
    return items

def load_groups(path):
    """Đọc splice.data, mã hóa chung một bảng mã, tách theo nhãn.

    Trả về (groups, code):
      groups = {"EI": [giao dịch số], "IE": [...], "N": [...]}
      code   = {item gốc: số}, dùng chung cho cả 3 nhóm để so sánh được
    """
    rows = read_splice(path)
    labels = [label for label, _ in rows]
    transactions = [to_transaction(seq) for _, seq in rows]

    encoded, code = encode(transactions)

    groups = {"EI": [], "IE": [], "N": []}
    for label, t in zip(labels, encoded):
        groups[label].append(t)
    return groups, code

def read_splice_with_name(path):
    """Giống read_splice nhưng giữ cả tên mẫu: list (nhãn, tên, chuỗi)."""
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            rows.append((parts[0], parts[1], parts[2]))
    return rows

def count_support(itemset, transactions):
    """Đếm số giao dịch chứa toàn bộ itemset.

    transactions nên là list các set, để kiểm tra "chứa" cho nhanh.
    """
    target = set(itemset)
    return sum(1 for t in transactions if t >= set(target) )


def growth_rate(sup_a, n_a, sup_b, n_b):
    """Tỉ lệ support tương đối của nhóm A so với nhóm B. Trả về inf nếu B bằng 0."""
    if sup_b == 0:
        return float("inf")
    return (sup_a/n_a)/(sup_b/n_b)