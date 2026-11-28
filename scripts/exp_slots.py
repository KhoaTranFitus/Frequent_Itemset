"""Thực nghiệm: bộ nhớ đỉnh của bản cơ bản KHI CÓ và KHI KHÔNG CÓ __slots__ ở FPNode.

Cách làm: trong tiến trình đo bản "noslots", thay lớp FPNode của src.structures
bằng một lớp giống hệt nhưng không khai báo __slots__ (mỗi nút lại có __dict__).
build_tree và build_conditional_tree tìm FPNode trong module src.structures lúc
chạy, nên sẽ dùng lớp được thay. Code của thuật toán không phải sửa gì.

Giống exp_memory: mỗi phép đo chạy trong một tiến trình Python mới.

Chạy từ thư mục gốc repo:
    python -m scripts.exp_slots
"""
import argparse
import csv
import os
import subprocess
import sys
import tracemalloc

import src.structures as structures
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic
from src.config import BENCHMARK, EXP_DIR, mid_minsup, to_min_count, use_utf8_stdout
from src.utils import read_transactions

CSV_PATH = f"{EXP_DIR}/slots.csv"
COLUMNS = ["dataset", "minsup", "peak_noslots_mb", "peak_slots_mb"]


class FPNodeNoSlots:
    """Giống FPNode nhưng không có __slots__ (như trước khi tối ưu)."""

    def __init__(self, item, parent, count=1):
        self.item = item
        self.count = count
        self.parent = parent
        self.children = {}


def measure_here(name, version):
    """Đo MỘT lần trong tiến trình hiện tại, in ra peak (MB). Chỉ gọi qua --one."""
    if version == "noslots":
        structures.FPNode = FPNodeNoSlots

    path, _ = BENCHMARK[name]
    data = read_transactions(path)                 # đọc trước, không tính vào đo
    min_count = to_min_count(mid_minsup(name), len(data))

    tracemalloc.start()
    fp_basic(data, min_count)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{peak / 1024 ** 2:.4f}")


def peak_mb(name, version):
    """Chạy measure_here trong một tiến trình mới, trả về peak (MB)."""
    cmd = [sys.executable, "-m", "scripts.exp_slots", "--one", name, version]
    done = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(done.stdout.strip().splitlines()[-1])


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description="Đo bộ nhớ khi có / không có __slots__")
    parser.add_argument("--one", nargs=2, metavar=("DATASET", "VERSION"),
                        help="(dùng nội bộ) đo một ca trong tiến trình hiện tại")
    args = parser.parse_args()

    if args.one:
        measure_here(*args.one)
        return

    rows = []
    for name in BENCHMARK:
        minsup = mid_minsup(name)
        noslots = peak_mb(name, "noslots")
        slots = peak_mb(name, "slots")
        print(f"{name} minsup={minsup}: không slots {noslots:.2f} MB | "
              f"có slots {slots:.2f} MB | {(slots - noslots) / noslots * 100:+.1f}%",
              flush=True)
        rows.append([name, minsup, f"{noslots:.2f}", f"{slots:.2f}"])

    os.makedirs(EXP_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Đã ghi {CSV_PATH}")


if __name__ == "__main__":
    main()