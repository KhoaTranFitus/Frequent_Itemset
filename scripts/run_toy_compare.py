import math
import time
import statistics

from src.utils import read_transactions, read_result, compare
from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic

# (tên, file, minsup, số tập tính tay)
CASES = [
    ("test1", "data/toy/toy_test1.txt", 0.6,   18),
    ("test2", "data/toy/toy_test2.txt", 0.5,   10),
    ("test2", "data/toy/toy_test2.txt", 0.375, 14),
    ("test3", "data/toy/toy_test3.txt", 0.5,   15),
    ("test3", "data/toy/toy_test3.txt", 0.33,  31),
    ("test4", "data/toy/toy_test4.txt", 0.3,    6),
    ("test4", "data/toy/toy_test4.txt", 0.2,   13),
]

def to_min_count(minsup, n):
    return math.ceil(round(minsup * n, 9))   # cùng công thức với fpgrowth.py

def median_time(fn, data, min_count, runs=5):
    times = []
    for _ in range(runs):
        t = time.perf_counter()
        res = fn(data, min_count)
        times.append(time.perf_counter() - t)
    return res, statistics.median(times)

print(f"{'test':6}{'minsup':>8}{'tay':>5}{'basic':>7}{'opt':>6}"
      f"{'basic==opt':>12}{'opt==SPMF':>11}{'t_basic(ms)':>13}{'t_opt(ms)':>11}")

for name, path, minsup, expected in CASES:
    data = read_transactions(path)
    mc = to_min_count(minsup, len(data))
    r_basic, t_basic = median_time(fp_basic, data, mc)
    r_opt, t_opt = median_time(fp_opt, data, mc)

    same = (r_basic == r_opt)

    ref_path = f"data/output/ref/{name}_{minsup}.txt"
    try:
        ref = read_result(ref_path)
        matched, mism, extra, missing = compare(r_opt, ref)
        vs_spmf = "100%" if not (mism or extra or missing) else "LECH"
    except FileNotFoundError:
        vs_spmf = "no ref"

    print(f"{name:6}{minsup:>8}{expected:>5}{len(r_basic):>7}{len(r_opt):>6}"
          f"{str(same):>12}{vs_spmf:>11}{t_basic*1000:>13.3f}{t_opt*1000:>11.3f}")