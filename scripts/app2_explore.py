from src.utils import encode, save_code
from src.app2_bio import read_splice, to_transaction


rows = read_splice("data/app2/splice.data")

labels = [label for label, _ in rows]
transactions = [to_transaction(seq) for _, seq in rows]

encoded, code = encode(transactions)      # một bảng mã chung

# tách theo nhãn: groups["EI"] là list giao dịch số của nhóm EI, ...
groups = {"EI": [], "IE": [], "N": []}
for label, t in zip(labels, encoded):
    groups[label].append(t)

save_code(code, "data/app2/code.json")
print(len(code))
print({k: len(v) for k, v in groups.items()})