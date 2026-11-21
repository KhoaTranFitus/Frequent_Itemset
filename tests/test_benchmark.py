import csv
import os
import statistics
import time

import pytest

from src.config import cases, ref_path, to_min_count
from src.utils import read_transactions, read_result, compare
from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic

LOG_PATH = "data/output/benchmark_log.csv"
TIME_LIMIT = 300   # giây, áp dụng cho mỗi bản
RUNS = 3           # số lần đo, lấy trung vị

# Lấy thẳng danh sách ca từ src/config.py, không khai báo lại ở đây: trước đó
# file này dùng chess 0.55 và 0.5, còn config chốt 0.9 đến 0.6, nên make_refs
# không sinh ref cho hai mức đó và hai test lặng lẽ bị SKIPPED.
CASES = cases("benchmark")


def median_time(fn, data, min_count, runs=RUNS):
    times = []
    result = None
    for _ in range(runs):
        start = time.perf_counter()
        result = fn(data, min_count)
        times.append(time.perf_counter() - start)
    return result, statistics.median(times)


def append_log(row):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    new_file = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["dataset", "minsup", "transactions", "min_count",
                             "itemsets", "t_basic_s", "t_opt_s", "speedup"])
        writer.writerow(row)


@pytest.mark.parametrize("name, path, minsup", CASES)
def test_benchmark(name, path, minsup):
    ref_file = ref_path(name, minsup)
    if not os.path.exists(path):
        pytest.skip(f"thiếu dữ liệu: {path}")
    if not os.path.exists(ref_file):
        pytest.skip(f"thiếu file ref: {ref_file} (chạy SPMF để tạo)")

    data = read_transactions(path)
    min_count = to_min_count(minsup, len(data))

    r_basic, t_basic = median_time(fp_basic, data, min_count)
    r_opt, t_opt = median_time(fp_opt, data, min_count)
    speedup = t_basic / t_opt

    ref = read_result(ref_file)
    matched, mismatched, extra, missing = compare(r_opt, ref)
    rate = len(matched) / len(ref) * 100

    print(f"\n{name} minsup={minsup} min_count={min_count}: {len(r_opt)} tập | "
          f"basic {t_basic:.3f}s | opt {t_opt:.3f}s | x{speedup:.2f} | "
          f"khớp SPMF {rate:.2f}%")
    append_log([name, minsup, len(data), min_count, len(r_opt),
                f"{t_basic:.4f}", f"{t_opt:.4f}", f"{speedup:.3f}"])

    # đúng đắn trước, tốc độ sau
    assert r_basic == r_opt, "bản tối ưu khác bản basic"
    assert not mismatched, f"lệch support: {len(mismatched)}"
    assert not extra, f"thừa so với SPMF: {len(extra)}"
    assert not missing, f"thiếu so với SPMF: {len(missing)}"
    assert len(matched) == len(ref)
    assert t_basic < TIME_LIMIT and t_opt < TIME_LIMIT, "quá chậm"