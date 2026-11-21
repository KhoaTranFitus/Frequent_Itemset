"""I/O và tiện ích cho Ứng dụng 1 (Chương 3): phân tích giỏ hàng.

Tách riêng khỏi src/utils.py vì hai thứ đọc hai định dạng khác nhau:

- utils.read_transactions đọc định dạng SPMF, item là **số nguyên** (int(x) từng
  token), dùng cho data/benchmark/*.txt.
- read_baskets ở đây đọc file giỏ hàng, item là **tên** (ví dụ "whole milk"),
  dùng cho data/app1/groceries.csv.

Tên item phải qua src.utils.encode thành số trước khi gọi fpgrowth, rồi đổi lại
bằng invert_code/decode khi trình bày.
"""
import random

from src.config import APP1_DATASETS, GROCERIES
from src.utils import encode, invert_code, read_transactions


def read_baskets(path, sep=","):
    """Đọc file giỏ hàng dạng chữ, mỗi dòng một giỏ -> list các list tên item.

    Định dạng của data/app1/groceries.csv: không có dòng header, mỗi dòng là một
    giỏ, các món cách nhau bằng sep.

        citrus fruit,semi-finished bread,margarine,ready soups
        tropical fruit,yogurt,coffee

    Bỏ dòng rỗng, cắt khoảng trắng quanh từng tên item, bỏ item rỗng (dòng kết
    thúc bằng dấu phẩy thì tách ra một chuỗi rỗng). Giữ nguyên thứ tự item trong
    giỏ vì encode sẽ sắp lại; cũng giữ nguyên item trùng nếu có, vì fpgrowth tự
    bỏ trùng khi đếm support.

    Đọc với encoding utf-8 để tên item có dấu vẫn đúng.
    """
    baskets = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            items = [name.strip() for name in line.strip().split(sep)]
            items = [name for name in items if name]
            if items:
                baskets.append(items)
    return baskets


def describe(baskets):
    """Thống kê nhanh một CSDL giao dịch -> dict.

    Trả về số giao dịch, số item phân biệt, tổng lượt item, độ dài giao dịch
    trung bình / nhỏ nhất / lớn nhất, và độ dày (tổng lượt / (số giao dịch × số
    item)). Dùng cho phần mô tả dữ liệu trong notebook và script, để không phải
    viết lại mấy dòng đếm ở nhiều chỗ.
    """
    n = len(baskets)
    items = {item for basket in baskets for item in basket}
    lengths = [len(basket) for basket in baskets]
    total = sum(lengths)
    return {
        "transactions": n,
        "items": len(items),
        "occurrences": total,
        "avg_len": total / n if n else 0.0,
        "min_len": min(lengths) if lengths else 0,
        "max_len": max(lengths) if lengths else 0,
        "density": total / (n * len(items)) if n and items else 0.0,
    }


def shuffle_keep_marginals(baskets, seed):
    """Trộn item giữa các giỏ nhưng giữ nguyên tần suất item và độ dài từng giỏ.

    Dùng làm **null model** (mô hình đối chứng) cho phần diễn giải: nếu các luật
    kết hợp tìm được chỉ là hệ quả của việc vài item bán rất chạy, thì dữ liệu đã
    trộn phải cho ra những luật lift tương đương. Thực tế không như vậy, và đó
    chính là bằng chứng các mẫu tìm được là thật.

    Cách trộn: làm phẳng toàn bộ lượt item thành một danh sách, trộn một lần bằng
    random.Random(seed), rồi cắt lại theo đúng độ dài từng giỏ ban đầu. Nhờ vậy:

    - tần suất mỗi item được giữ **chính xác** (vẫn là từng ấy lượt),
    - độ dài mỗi giỏ được giữ **chính xác**,
    - chỉ có sự đồng xuất hiện giữa các item bị phá.

    Hạn chế đã biết, phải nêu trong báo cáo: cách này có thể đặt hai lượt của
    cùng một item vào một giỏ. fpgrowth đếm support bằng set(transaction) nên
    support vẫn đúng, nhưng số item phân biệt trong giỏ đó giảm đi một chút, nên
    dữ liệu trộn hơi "loãng" hơn dữ liệu thật. Lệch này chỉ làm null model dễ
    thắng hơn, tức là kết luận "dữ liệu thật có nhiều luật mạnh hơn hẳn" vẫn
    đứng, không bị thổi phồng.

    Không sửa danh sách gốc.
    """
    flat = [item for basket in baskets for item in basket]
    random.Random(seed).shuffle(flat)

    shuffled = []
    start = 0
    for basket in baskets:
        shuffled.append(flat[start:start + len(basket)])
        start += len(basket)
    return shuffled


def load_dataset(name):
    """Đọc một CSDL của Ứng dụng 1 -> (giao dịch đã mã hóa, code, name_of).

    Hai CSDL có hai định dạng khác nhau nên phải đi hai đường, và cả script,
    notebook lẫn test đều cần đúng một chỗ quyết định việc này:

    - "groceries": item là tên, nên read_baskets rồi encode thành số.
      code = {tên: số}, name_of = {số: tên} để đổi lại khi trình bày.
    - "retail": file định dạng SPMF, item đã là số nên read_transactions là xong.
      code và name_of đều None, nghĩa là "in thẳng item, không cần đổi tên" —
      đúng kiểu mà src.rules.rule_names nhận.

    Luôn trả về giao dịch mà fpgrowth dùng được ngay.
    """
    if name not in APP1_DATASETS:
        raise ValueError(f"CSDL không hợp lệ: {name}. "
                         f"Chọn một trong {sorted(APP1_DATASETS)}")

    path = APP1_DATASETS[name]
    if path == GROCERIES:
        encoded, code = encode(read_baskets(path))
        return encoded, code, invert_code(code)
    return read_transactions(path), None, None
