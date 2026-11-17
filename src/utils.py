
def read_transactions(path):
    # TODO: đọc từng dòng, tách bằng dấu cách, trả về list các list item

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
    for item in transaction:
        if item in rank:
            kept.append(item)

    return sorted (kept, key= lambda item: rank[item])

def print_tree(node, depth=0):
    for child in node.children.values():
        print("  " * depth + f"{child.item}:{child.count}")
        print_tree(child, depth + 1)

def write_result(result, path):
    with open(path, "w") as f:
        for itemset, sup in result.items():
            items_text = " ".join(str(i) for i in itemset)      # TODO: ghép các item (đang là int) thành chuỗi
            f.write(f"{items_text} #SUP: {sup}\n")

if __name__ == "__main__":
    data = read_transactions("toy.txt")
    freq = find_frequent_items(data, 3)
    flist = sorted(freq, key=lambda item: (-freq[item], item))
    rank = {item: i for i, item in enumerate(flist)}
    print(flist)
    for t in data:
        print(order_transaction(t, rank))