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