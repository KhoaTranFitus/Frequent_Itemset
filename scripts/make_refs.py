"""Sinh file tham chiếu bằng SPMF (FPGrowth_itemsets) cho các CSDL dùng trong test.

Chạy từ thư mục gốc repo:
    python -m scripts.make_refs --group toy
    python -m scripts.make_refs --group benchmark
    python -m scripts.make_refs --group all
    python -m scripts.make_refs --group benchmark --dataset retail

Cần Java và tool/spmf.jar. Ref ghi vào data/output/ref/<tên>_<minsup>.txt
(tên file phải khớp với test_correctness.py và test_benchmark.py).

Danh sách CSDL và minsup lấy từ src/config.py, không khai báo lại ở đây.
"""
import argparse
import os
import subprocess
import sys

from src.config import (JAVA_BIN, REF_DIR, SPMF_JAR, cases, ref_path,
                        use_utf8_stdout)


def run_one(name, path, minsup, skip_existing=True):
    """Chạy SPMF cho một ca. Trả về True nếu có file ref sau khi chạy."""
    if not os.path.exists(path):
        print(f"[bỏ qua] thiếu dữ liệu: {path}")
        return False

    out = ref_path(name, minsup)
    if skip_existing and os.path.exists(out):
        print(f"[có rồi] {out}")
        return True

    percent = f"{minsup * 100:g}%"      # 0.375 -> "37.5%", 0.008 -> "0.8%"
    cmd = [JAVA_BIN, "-jar", SPMF_JAR, "run", "FPGrowth_itemsets", path, out, percent]
    print(f"[chạy] {name} minsup={minsup} ({percent}) -> {out}", flush=True)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(out):
        print("  LỖI:", (result.stdout + result.stderr).strip())
        return False
    return True


def main():
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description="Sinh file tham chiếu bằng SPMF")
    parser.add_argument("--group", choices=["toy", "benchmark", "all"], default="toy")
    parser.add_argument("--dataset", help="chỉ sinh ref cho một CSDL, ví dụ retail")
    parser.add_argument("--force", action="store_true",
                        help="chạy lại cả những ca đã có file ref")
    args = parser.parse_args()

    if not os.path.exists(SPMF_JAR):
        sys.exit(f"Không thấy {SPMF_JAR}. Tải spmf.jar ở trang SPMF và đặt vào thư mục tool/.")

    todo = cases(args.group)
    if args.dataset:
        todo = [c for c in todo if c[0] == args.dataset]
        if not todo:
            sys.exit(f"Không có ca nào cho CSDL '{args.dataset}' trong nhóm '{args.group}'.")

    os.makedirs(REF_DIR, exist_ok=True)
    ok = sum(run_one(*c, skip_existing=not args.force) for c in todo)
    print(f"Xong: {ok}/{len(todo)} file ref.")


if __name__ == "__main__":
    main()
