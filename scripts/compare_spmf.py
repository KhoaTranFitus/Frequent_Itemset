"""So sánh file kết quả của nhóm với file kết quả của SPMF.

    python -m scripts.compare_spmf <file_cua_nhom> <file_cua_spmf>
"""
import sys

from src.config import use_utf8_stdout
from src.utils import compare, read_result


def main():
    use_utf8_stdout()
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    mine = read_result(sys.argv[1])    # file kết quả của nhóm
    ref = read_result(sys.argv[2])     # file kết quả của SPMF

    matched, mismatched, extra, missing = compare(mine, ref)
    rate = len(matched) / len(ref) * 100 if ref else 0.0

    print(f"Khớp hoàn toàn: {len(matched)}/{len(ref)} = {rate:.2f}%")
    print(f"Lệch support: {len(mismatched)}")
    print(f"Thừa so với SPMF: {len(extra)}")
    print(f"Thiếu so với SPMF: {len(missing)}")


if __name__ == "__main__":
    main()
