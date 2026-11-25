"""Thực nghiệm: peak memory của bản basic và bản tối ưu tại minsup giữa."""
import tracemalloc
import csv
import os
from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic
from src.config import BENCHMARK, EXP_DIR, mid_minsup, to_min_count, use_utf8_stdout
from src.utils import read_transactions

CSV_PATH = f"{EXP_DIR}/memory.csv"
COLUMNS = ["dataset", "minsup", "peak_basic_mb", "peak_opt_mb"]


def peak_mb(fn, data, min_count):
    """Chạy fn một lần, trả về peak memory (MB) của riêng lần chạy đó."""
    # 1. start theo dõi
    # 2. gọi fn
    # 3. lấy peak
    # 4. stop
    # 5. đổi byte -> MB
    tracemalloc.start()
    fn(data, min_count)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak/1024**2

def main():
    use_utf8_stdout()
    rows = []
    for name, (path, _) in BENCHMARK.items():
        # đọc data, lấy minsup giữa, tính min_count
        # đo peak cho basic và opt
        # in ra màn hình cho dễ theo dõi
        # thêm một dòng vào rows
        ...
    # ghi rows ra CSV (tạo thư mục EXP_DIR nếu chưa có)
        data = read_transactions(path)
        minsup = mid_minsup(name)
        min_count = to_min_count(minsup, len(data))

        basic = peak_mb(fp_basic, data, min_count)
        opt = peak_mb(fp_opt, data, min_count)
        print(f"{name} minsup={minsup}: basic {basic:.2f} MB | opt {opt:.2f} MB")
        rows.append([name, minsup, f"{basic:.2f}", f"{opt:.2f}"])
    os.makedirs(EXP_DIR, exist_ok=True)        # tạo thư mục nếu chưa có
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)               # dòng tiêu đề
        writer.writerows(rows)                 # các dòng số liệu
    print(f"Đã ghi {CSV_PATH}")
if __name__ == "__main__":
    main()