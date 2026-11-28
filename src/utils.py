import json

def read_transactions(path):
    """Đọc file SPMF: mỗi dòng một giao dịch, item là số nguyên cách nhau bởi dấu cách.

    Trả về list các list item; dòng trống bị bỏ qua.
    """

    transaction = []
    with open (path) as f:
        for line in f:
            items = [int(x) for x in line.split()]
            if items:
                transaction.append(items)
    return transaction           

    
def find_frequent_items(transactions, min_count):
    #  trả về dict {item: support} chỉ gồm item có support >= min_count
    count = {}
    for n in transactions:
        for item in set(n):
            if item in count:
                count[item]+=1
            else:
                count [item] = 1

    frequent = {}
    for item, c in count.items():
        if c >= min_count:
            frequent[item] = c 
    return frequent


def order_transaction(transaction, rank):

    kept = []
    for item in set(transaction):
        if item in rank:
            kept.append(item)

    return sorted (kept, key= lambda item: rank[item])

def print_tree(node, depth=0):
    """In FP-tree dạng thụt lề, mỗi nút một dòng 'item:count' (dùng khi gỡ lỗi)."""
    for child in node.children.values():
        print("  " * depth + f"{child.item}:{child.count}")
        print_tree(child, depth + 1)

def write_result(result, path):
    with open(path, "w") as f:
        for itemset, sup in result.items():
            items_text = " ".join(str(i) for i in itemset)
            f.write(f"{items_text} #SUP: {sup}\n")


def read_result(path):
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            items_part, sup_part = line.split("#SUP:")
            itemset = tuple(sorted (int(x) for x in items_part.split()))
            result[itemset] = int(sup_part.strip())
    return result

def compare (mine, ref):
    extra = mine.keys() - ref.keys()
    missing = ref.keys() - mine.keys()
    common = mine.keys() & ref.keys()

    matched = []
    unmatched = []

    for itemset in common:
        if mine[itemset] == ref[itemset]:
            matched.append(itemset)
        else:
            unmatched.append(itemset)


    return matched, unmatched, extra, missing


def encode(transactions, start=1):
    """Đổi item dạng chữ sang số nguyên để chạy được fpgrowth.

    Trả về (giao dịch đã mã hóa, code), với code = {item gốc: số nguyên}.
    Số được gán theo thứ tự item đã sắp nên cùng dữ liệu luôn cho cùng bảng mã,
    đáp ứng yêu cầu tái lập kết quả của đồ án. Mã bắt đầu từ 1 để kết quả ghi ra
    vẫn đúng định dạng SPMF (item là số nguyên dương).

    Item trùng trong một giao dịch được giữ nguyên, vì fpgrowth tự bỏ trùng khi
    đếm support.
    """
    names = {item for t in transactions for item in t}
    try:
        names = sorted(names)              # số sắp theo giá trị, chữ sắp theo a-z
    except TypeError:
        names = sorted(names, key= lambda x: (type(x).__name__,str(x)))     # dữ liệu lẫn nhiều kiểu thì sắp theo chuỗi

    code = {name: i for i, name in enumerate(names, start=start)}
    encoded = [[code[item] for item in t] for t in transactions]
    return encoded, code


def invert_code(code):
    """Đổi chiều bảng mã: {item gốc: số} -> {số: item gốc}."""
    return {num: name for name, num in code.items()}


def decode(result, code):
    """Đổi kết quả fpgrowth về item gốc: {tuple số: support} -> {tuple item gốc: support}.

    Vì encode gán số theo thứ tự item đã sắp, thứ tự số trong mỗi itemset cũng
    chính là thứ tự item gốc, nên không cần sắp lại.

    Muốn đổi riêng một itemset (ví dụ khi sinh luật kết hợp), lấy bảng mã ngược
    một lần bằng invert_code rồi dùng trực tiếp:

        name_of = invert_code(code)
        tuple(name_of[i] for i in itemset)
    """
    name_of = invert_code(code)
    return {tuple(name_of[num] for num in itemset): sup
            for itemset, sup in result.items()}


def save_code(code, path):
    """Ghi bảng mã ra file JSON dạng danh sách cặp [item gốc, số].

    Không lưu thẳng dict vì JSON luôn đổi khóa thành chuỗi: item số 5 sẽ
    thành "5" khi đọc lại. Lưu dạng cặp thì giữ được kiểu của item.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(code.items()), f, ensure_ascii=False)


def load_code(path):
    """Đọc lại bảng mã do save_code ghi: trả về dict {item gốc: số}."""
    with open(path, encoding="utf-8") as f:
        pairs = json.load(f)
    return {item: num for item, num in pairs}