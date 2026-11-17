import sys
from src.utils import read_result
from src.utils import compare,read_result   # hoặc nơi bạn đặt hàm compare

if __name__ == "__main__":
    mine = read_result(sys.argv[1])    # file kết quả của bạn
    ref = read_result(sys.argv[2])     # file kết quả của SPMF

    matched, mismatched, extra, missing = compare(mine, ref)
    rate = len(matched) / len(ref) * 100

    print(f"Khớp hoàn toàn: {len(matched)}/{len(ref)} = {rate:.2f}%")
    print(f"Lệch support: {len(mismatched)}")
    print(f"Thừa so với SPMF: {len(extra)}")
    print(f"Thiếu so với SPMF: {len(missing)}")