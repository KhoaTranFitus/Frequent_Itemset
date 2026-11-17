"""Sinh file tham chiếu bằng SPMF (FPGrowth_itemsets) cho các CSDL dùng trong test.

Chạy từ thư mục gốc repo:
    python -m scripts.make_refs --group toy
    python -m scripts.make_refs --group benchmark
    python -m scripts.make_refs --group all

Cần Java và tool/spmf.jar. Ref ghi vào data/output/ref/<tên>_<minsup>.txt
(tên file phải khớp với test_correctness.py và test_benchmark.py).
"""
import argparse
import os
import subprocess
import sys

SPMF_JAR = "tool/spmf.jar"
REF_DIR = "data/output/ref"

# (tên, file input, minsup tương đối)
TOY = [
    ("test1", "data/toy/toy_test1.txt", 0.6),
    ("test2", "data/toy/toy_test2.txt", 0.5),
    ("test2", "data/toy/toy_test2.txt", 0.375),
    ("test3", "data/toy/toy_test3.txt", 0.5),
    ("test3", "data/toy/toy_test3.txt", 0.33),
    ("test4", "data/toy/toy_test4.txt", 0.3),
    ("test4", "data/toy/toy_test4.txt", 0.2),
]

BENCHMARK = [
    ("mushroom", "data/benchmark/mushroom.txt", 0.2),
    ("mushroom", "data/benchmark/mushroom.txt", 0.1),
    ("mushroom", "data/benchmark/mushroom.txt", 0.05),
    ("chess", "data/benchmark/chess.txt", 0.7),
    ("chess", "data/benchmark/chess.txt", 0.65),
    ("chess", "data/benchmark/chess.txt", 0.55),
    ("chess", "data/benchmark/chess.txt", 0.5),
]


def run_one(name, path, minsup):
    if not os.path.exists(path):
        print(f"[bỏ qua] thiếu dữ liệu: {path}")
        return False
    out = f"{REF_DIR}/{name}_{minsup}.txt"
    percent = f"{minsup * 100:g}%"      # 0.375 -> "37.5%", 0.6 -> "60%"
    cmd = ["java", "-jar", SPMF_JAR, "run", "FPGrowth_itemsets", path, out, percent]
    print(f"[chạy] {name} minsup={minsup} ({percent}) -> {out}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(out):
        print("  LỖI:", (result.stdout + result.stderr).strip())
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Sinh file tham chiếu bằng SPMF")
    parser.add_argument("--group", choices=["toy", "benchmark", "all"], default="toy")
    args = parser.parse_args()

    if not os.path.exists(SPMF_JAR):
        sys.exit(f"Không thấy {SPMF_JAR}. Tải spmf.jar ở trang SPMF và đặt vào thư mục tool/.")

    os.makedirs(REF_DIR, exist_ok=True)
    cases = {"toy": TOY, "benchmark": BENCHMARK, "all": TOY + BENCHMARK}[args.group]

    ok = sum(run_one(*c) for c in cases)
    print(f"Xong: {ok}/{len(cases)} file ref.")


if __name__ == "__main__":
    main()
