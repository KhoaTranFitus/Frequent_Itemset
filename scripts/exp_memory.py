"""Thực nghiệm: peak memory của bản basic và bản tối ưu tại minsup giữa.

QUAN TRỌNG: mỗi phép đo chạy trong một tiến trình Python MỚI.
Nếu đo hai bản liên tiếp trong cùng một tiến trình thì bản đo SAU luôn ra thấp
hơn khoảng 1 MB: Python giữ lại vùng nhớ của các object đã giải phóng (freelist)
để dùng lại, và tracemalloc không đếm phần dùng lại này. Bản cũ của script đo
basic trước rồi opt sau nên đã làm bản tối ưu trông tiết kiệm hơn thực tế.

Chạy từ thư mục gốc repo:
    python -m scripts.exp_memory
"""
import argparse
import csv
import os
import subprocess
import sys
import tracemalloc

from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic
from src.config import BENCHMARK, EXP_DIR, mid_minsup, to_min_count, use_utf8_stdout
from src.utils import read_transactions

CSV_PATH = f"{EXP_DIR}/memory.csv"
COLUMNS = ["dataset", "minsup", "peak_basic_mb", "peak_opt_mb"]
VERSIONS = {"basic": fp_basic, "opt": fp_opt}


def measure_here(name, version):
    """Đo MỘT lần trong tiến trình hiện tại, in ra peak (MB). Chỉ gọi qua --one."""
    path, _ = BENCHMARK[name]
    data = read_transactions(path)                 # đọc trước, không tính vào đo
    min_count = to_min_count(mid_minsup(name), len(data))

    tracemalloc.start()
    VERSIONS[version](data, min_count)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{peak / 1024 ** 2:.4f}")


def peak_mb(name, version):
    """Chạy measure_here trong một tiến trình mới, trả về peak (MB)."""
    cmd = [sys.executable, "-m", "scripts.exp_memory", "--one", name, version]
    done = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(done.stdout.strip().splitlines()[-1])


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description="Đo peak memory basic và tối ưu")
    parser.add_argument("--one", nargs=2, metavar=("DATASET", "VERSION"),
                        help="(dùng nội bộ) đo một ca trong tiến trình hiện tại")
    args = parser.parse_args()

    if args.one:
        measure_here(*args.one)
        return

    rows = []
    for name in BENCHMARK:
        minsup = mid_minsup(name)
        basic = peak_mb(name, "basic")
        opt = peak_mb(name, "opt")
        print(f"{name} minsup={minsup}: basic {basic:.2f} MB | opt {opt:.2f} MB | "
              f"{(opt - basic) / basic * 100:+.1f}%", flush=True)
        rows.append([name, minsup, f"{basic:.2f}", f"{opt:.2f}"])

    os.makedirs(EXP_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Đã ghi {CSV_PATH}")


if __name__ == "__main__":
    main()
