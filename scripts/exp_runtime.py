"""Thực nghiệm 1: thời gian chạy, số itemset và tính đúng đắn theo minsup.

Một lần chạy cho ra số liệu của ba thực nghiệm trong đề:
  - kiểm tra tính đúng đắn (cột match_pct),
  - thời gian chạy theo minsup (cột t_basic_s, t_opt_s, t_spmf_s),
  - số lượng frequent itemset theo minsup (cột itemsets).

Chạy từ thư mục gốc repo:
    python -m scripts.exp_runtime                        # toàn bộ CSDL benchmark
    python -m scripts.exp_runtime --dataset retail       # một CSDL
    python -m scripts.exp_runtime --group toy --runs 1   # chạy thử cho nhanh
    python -m scripts.exp_runtime --skip-basic           # bỏ bản cơ bản
    python -m scripts.exp_runtime --force                # chạy lại ca đã có trong CSV

Máy có nhiều bản Java thì chỉ rõ bản chạy SPMF bằng biến JAVA (xem src/config.py):
    JAVA="C:/Program Files/Java/jdk-25.0.5.0.3/bin/java.exe" python -m scripts.exp_runtime

Kết quả ghi vào data/output/exp/runtime.csv, cộng dồn theo từng ca nên dừng giữa
đường rồi chạy lại không mất phần đã làm (ca đã có trong CSV bị bỏ qua, trừ khi
có --force).

Thời gian của SPMF lấy từ dòng "Total time" do chính SPMF in ra, không phải thời
gian của cả tiến trình java, vì tính cả thời gian khởi động JVM thì so sánh không
còn công bằng. Thời gian của nhóm cũng chỉ tính phần thuật toán, không tính đọc
file. Đây là lựa chọn phải ghi rõ trong báo cáo.
"""
import argparse
import csv
import os
import re
import statistics
import subprocess
import time

from src.algorithm.fpgrowth import fpgrowth as fp_opt
from src.algorithm.fpgrowth_basic import fpgrowth as fp_basic
from src.config import (EXP_DIR, JAVA_BIN, MINE_DIR, REF_DIR, SPMF_JAR, cases,
                        ref_path, to_min_count, use_utf8_stdout)
from src.utils import compare, read_result, read_transactions, write_result

CSV_PATH = f"{EXP_DIR}/runtime.csv"
COLUMNS = ["dataset", "minsup", "min_count", "itemsets",
           "t_basic_s", "t_opt_s", "t_spmf_s", "match_pct"]

# SPMF in ra ví dụ: " Total time ~ 125 ms"
SPMF_TIME = re.compile(r"Total time ~?\s*([\d.]+)\s*ms", re.IGNORECASE)

# Java báo phiên bản bằng class file version: 52 là Java 8, 69 là Java 25
CLASS_NEEDED = re.compile(r"class file version (\d+)\.")
CLASS_HAVE = re.compile(r"class file versions up to (\d+)\.")

# Lý do đã tắt SPMF cho cả lần chạy; None là vẫn còn thử.
# Tắt sớm để không phải khởi động JVM lỗi ở cả 28 ca.
spmf_off = None


def java_version_hint(err):
    """Dịch UnsupportedClassVersionError sang câu dễ hiểu."""
    needed = CLASS_NEEDED.search(err)
    have = CLASS_HAVE.search(err)
    if needed and have:
        return (f"spmf.jar biên dịch cho Java {int(needed.group(1)) - 44}, "
                f"máy đang chạy Java {int(have.group(1)) - 44}")
    return "spmf.jar không chạy được với Java trên máy"


def median_time(fn, data, min_count, runs):
    """Chạy fn nhiều lần, trả về (kết quả, thời gian trung vị)."""
    times = []
    result = None
    for _ in range(runs):
        start = time.perf_counter()
        result = fn(data, min_count)
        times.append(time.perf_counter() - start)
    return result, statistics.median(times)


def run_spmf(name, path, minsup, runs):
    """Chạy SPMF, ghi kết quả vào file ref, trả về thời gian trung vị (giây).

    Trả về None nếu không chạy được (thiếu jar, thiếu Java, SPMF báo lỗi). Lần
    đầu không chạy được thì tắt SPMF cho cả lần chạy, vì 28 ca cùng lỗi như nhau.
    """
    global spmf_off

    if spmf_off:
        return None
    if not os.path.exists(SPMF_JAR):
        spmf_off = f"thiếu {SPMF_JAR}"
        print(f"  [SPMF] {spmf_off}, hai cột SPMF sẽ để trống")
        return None

    out = ref_path(name, minsup)
    percent = f"{minsup * 100:g}%"
    cmd = [JAVA_BIN, "-jar", SPMF_JAR, "run", "FPGrowth_itemsets", path, out, percent]

    times = []
    for _ in range(runs):
        try:
            done = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as err:          # không có java trong PATH
            spmf_off = f"không gọi được java: {err}"
            print(f"  [SPMF] {spmf_off}, hai cột SPMF sẽ để trống")
            return None

        if done.returncode != 0:
            err = (done.stdout + done.stderr).strip()
            if "UnsupportedClassVersionError" in err:
                spmf_off = java_version_hint(err)
            else:
                spmf_off = f"SPMF báo lỗi: {err[:200]}"
            print(f"  [SPMF] {spmf_off}, hai cột SPMF sẽ để trống")
            return None

        found = SPMF_TIME.search(done.stdout)
        if not found:
            spmf_off = "không đọc được dòng Total time trong output của SPMF"
            print(f"  [SPMF] {spmf_off}, hai cột SPMF sẽ để trống")
            return None
        times.append(float(found.group(1)) / 1000.0)

    return statistics.median(times)


def match_percent(mine, name, minsup):
    """Tỉ lệ itemset khớp hoàn toàn với ref của SPMF, None nếu chưa có ref."""
    path = ref_path(name, minsup)
    if not os.path.exists(path):
        return None

    ref = read_result(path)
    if not ref:
        return None

    matched, mismatched, extra, missing = compare(mine, ref)
    if mismatched or extra or missing:
        print(f"  [LỆCH] lệch support {len(mismatched)}, "
              f"thừa {len(extra)}, thiếu {len(missing)}")
    return len(matched) / len(ref) * 100


def done_cases():
    """Các ca đã có trong CSV, để chạy lại không làm lại từ đầu."""
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return {(row["dataset"], row["minsup"]) for row in csv.DictReader(f)}


def append_row(row):
    os.makedirs(EXP_DIR, exist_ok=True)
    new_file = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(COLUMNS)
        writer.writerow(row)


def fmt(value):
    """Số thực ghi 4 chữ số thập phân, thiếu số liệu thì để trống."""
    return "" if value is None else f"{value:.4f}"


def run_case(name, path, minsup, args):
    if not os.path.exists(path):
        print(f"[bỏ qua] thiếu dữ liệu: {path}")
        return

    data = read_transactions(path)
    min_count = to_min_count(minsup, len(data))
    print(f"[chạy] {name} minsup={minsup} min_count={min_count} "
          f"({len(data)} giao dịch)", flush=True)

    result, t_opt = median_time(fp_opt, data, min_count, args.runs)

    t_basic = None
    if not args.skip_basic:
        result_basic, t_basic = median_time(fp_basic, data, min_count, args.runs)
        if result_basic != result:
            raise AssertionError(f"{name} minsup={minsup}: bản tối ưu khác bản cơ bản")

    os.makedirs(MINE_DIR, exist_ok=True)
    write_result(result, f"{MINE_DIR}/{name}_{minsup}.txt")

    t_spmf = None
    if not args.skip_spmf:
        os.makedirs(REF_DIR, exist_ok=True)
        t_spmf = run_spmf(name, path, minsup, args.runs)

    pct = match_percent(result, name, minsup)

    speedup = f" | x{t_basic / t_opt:.2f}" if t_basic else ""
    print(f"  {len(result)} tập | opt {t_opt:.3f}s"
          f"{f' | basic {t_basic:.3f}s' if t_basic else ''}"
          f"{f' | spmf {t_spmf:.3f}s' if t_spmf else ''}{speedup}"
          f" | khớp SPMF {'chưa có ref' if pct is None else f'{pct:.2f}%'}", flush=True)

    append_row([name, minsup, min_count, len(result),
                fmt(t_basic), fmt(t_opt), fmt(t_spmf),
                "" if pct is None else f"{pct:.2f}"])


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Đo thời gian, số itemset và tính đúng đắn theo minsup")
    parser.add_argument("--group", choices=["toy", "benchmark", "all"],
                        default="benchmark")
    parser.add_argument("--dataset", help="chỉ chạy một CSDL, ví dụ retail")
    parser.add_argument("--runs", type=int, default=3,
                        help="số lần đo, lấy trung vị (mặc định 3)")
    parser.add_argument("--skip-basic", action="store_true",
                        help="không đo bản cơ bản")
    parser.add_argument("--skip-spmf", action="store_true",
                        help="không chạy SPMF (vẫn so khớp nếu đã có ref)")
    parser.add_argument("--force", action="store_true",
                        help="chạy lại cả những ca đã có trong CSV")
    args = parser.parse_args()

    todo = cases(args.group)
    if args.dataset:
        todo = [c for c in todo if c[0] == args.dataset]
        if not todo:
            raise SystemExit(f"Không có ca nào cho CSDL '{args.dataset}'.")

    if not args.force:
        already = done_cases()
        before = len(todo)
        todo = [c for c in todo if (c[0], str(c[2])) not in already]
        if before != len(todo):
            print(f"Bỏ qua {before - len(todo)} ca đã có trong {CSV_PATH}.")

    for case in todo:
        run_case(*case, args=args)

    print(f"Xong {len(todo)} ca, số liệu trong {CSV_PATH}.")
    if spmf_off:
        print(f"Hai cột t_spmf_s và match_pct để trống vì {spmf_off}.")
        print("Khắc phục rồi thì chạy lại với --force để điền hai cột đó.")


if __name__ == "__main__":
    main()
