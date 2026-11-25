"""Ứng dụng 2 (sinh học): đọc dữ liệu splice-junction và biến chuỗi DNA thành giao dịch."""
from src.utils import encode

VALID = set("ACGT")

def read_splice(path):   # đọc file và trả về (nhãn, chuỗi)
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue  # bo qua dong trong
            parts = [p.strip() for p in line.split(",")] # parts[0] là nhãn, parts[1] là tên mẫu, parts[2] là chuỗi
            rows.append((parts[0], parts[2]))
    return rows

def read_splice_with_name(path):     # như trên, giữ lại thêm tên mẫu
    """Giống read_splice nhưng giữ cả tên mẫu: list (nhãn, tên, chuỗi)."""
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            rows.append((parts[0], parts[1], parts[2]))
    return rows
def position_name(i):  # đổi chỉ số 0 .. 59 sang -30 .. -1, +1 .. +30
    """Đổi chỉ số Python i (0..59) sang vị trí sinh học (-30..-1, +1..+30)."""
    if i < 30:
        pos = i - 30
    else:
        pos = i-29
    return f"{pos:+d}"     # +d: luôn ghi dấu, ví dụ "+1", "-30"


def to_transaction(seq):#  chuỗi --> list item "P +- k = X"
    """Biến một chuỗi DNA thành giao dịch, mỗi item là 'P<vị trí>=<nucleotide>'."""
    
    items = []
    for i, base in enumerate(seq):
        if base not in VALID:
            continue                 # bỏ ký tự không chắc chắn (D, N, S, R)
        items.append(f"P{position_name(i)}={base}")
    return items

def load_groups(path):   # đọc --> mã hóa __> tách nhóm. Mã hóa chung một bảng mã cho cả 3 nhóm
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


def count_support(itemset, transactions):   # đếm số giao dịch chứa itemset  t >= target: phép chứa của set
    """Đếm số giao dịch chứa toàn bộ itemset.

    transactions nên là list các set, để kiểm tra "chứa" cho nhanh.
    """
    target = set(itemset)
    return sum(1 for t in transactions if t >= target )


def growth_rate(sup_a, n_a, sup_b, n_b):        # tỉ lệ support tương đối 
    """Tỉ lệ support tương đối của nhóm A so với nhóm B. Trả về inf nếu B bằng 0."""
    if sup_b == 0:
        return float("inf")
    return (sup_a/n_a)/(sup_b/n_b)