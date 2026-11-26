# chứa cấu trúc cây
from src.utils import order_transaction



class FPNode:
    # __slots__: mỗi nút chỉ có đúng 4 thuộc tính này, Python không cần tạo dict
    # __dict__ riêng cho từng nút -> mỗi nút nhẹ hơn, cây lớn tiết kiệm nhiều bộ nhớ.
    __slots__ = ("item", "count", "parent", "children")

    def __init__(self, item, parent, count = 1):
        self.item = item
        self.count = count
        self.parent =parent
        self.children = {}

def insert_transaction(root, transaction, header, count = 1):
    node =  root

    for item in transaction:
        if item in node.children:
            node.children[item].count += count
        else:
            newNode = FPNode (item, node,count)
            node.children[item] = newNode
            header.setdefault(item,[]).append(newNode)

        node = node.children[item]

def build_tree(transactions, rank):
    root = FPNode(None, None)
    header = {}
    for t in transactions:
        ordered =  order_transaction(t, rank)               
        insert_transaction(root, ordered, header)
    return root, header

def get_prefix_paths(item, header):
    paths = []                           #kết quả: list các (path,count)
    for node in header[item]:            # duyệt từng node của item (nhờ header)
        path = []
        cur = node.parent                 # bắt đầu từ cha của node
        while cur.item is not None:       
            path.append(cur.item)          # ghi item vao path
            cur = cur.parent               # lên 1 bậc
        if path:                           # bỏ qua path rỗng
            paths.append((path[::-1], node.count))  # đảo ngược lại, đi kèm count 
    return paths

def build_conditional_tree(paths, min_count):
    #1. đếm support từng item trong paths (nhân count)
    cnt = {}
    for path, c in paths:
        for item in path:
            cnt[item] = cnt.get(item, 0) + c

    #2. giu item co cnt >= min_count,  tao rank mới
    freq = {i:n for i, n in cnt.items() if n >= min_count}
    flist = sorted (freq, key=lambda i: (-freq[i], i))
    rank = {i:k for k,i in enumerate (flist)}

    # 3. dựng cây từ các path đã lọc
    root = FPNode(None, None)
    header = {}
    for path, c in paths:
        ordered = order_transaction(path,rank)
        insert_transaction(root, ordered, header, c)

    return root, header,  freq