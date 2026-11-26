"""Vẽ toàn bộ biểu đồ Chương 2 từ các CSV trong data/output/exp/ vào docs/figures/."""
import os

import matplotlib
matplotlib.use("Agg")               # chỉ lưu ảnh, không mở cửa sổ
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
import numpy as np
import pandas as pd

from src.config import EXP_DIR, use_utf8_stdout

FIG_DIR = "docs/figures"
DENSE = ["chess", "mushroom"]
SPARSE = ["retail", "T10I4D100K"]

# trục log: ghi số thường (0.1, 1, 10) thay cho 10^-1, 4×10^0
SO_THUONG = FuncFormatter(lambda v, _: f"{v:g}")


def load(name):
    """Đọc một file CSV kết quả, trả về None nếu chưa có."""
    path = f"{EXP_DIR}/{name}.csv"
    if not os.path.exists(path):
        print(f"[bỏ qua] chưa có {path}")
        return None
    df = pd.read_csv(path)
    # phòng hờ CSV cũ có ca bị ghi hai lần: chỉ giữ lần đo sau cùng của mỗi ca
    if name == "runtime":
        df = df.drop_duplicates(["dataset", "minsup"], keep="last")
    return df


def save(fig, name):
    fig.tight_layout()
    path = f"{FIG_DIR}/{name}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Đã lưu {path}")
def plot_memory():
    """Bộ nhớ đỉnh của bản cơ bản và bản tối ưu tại minsup giữa, mỗi CSDL một ô.

    Mỗi ô có trục tung riêng, BẮT ĐẦU TỪ 0, nên chiều cao hai cột tỉ lệ đúng với số MB
    (trục log trước đây phóng đại chênh lệch, ví dụ Chess 4,27 -> 3,08 MB trông như giảm 4 lần).
    """
    df = pd.read_csv(f"{EXP_DIR}/memory.csv")
    fig, axes = plt.subplots(1, len(df), figsize=(10, 3.6))

    for ax, row in zip(axes, df.itertuples()):
        gia_tri = [row.peak_basic_mb, row.peak_opt_mb]
        ax.bar(["cơ bản", "tối ưu"], gia_tri, color=["tab:blue", "tab:orange"], width=0.6)
        for i, v in enumerate(gia_tri):
            ax.text(i, v, f"{v:g}", ha="center", va="bottom", fontsize=8)

        doi = (row.peak_opt_mb - row.peak_basic_mb) / row.peak_basic_mb * 100
        loai = "dày" if row.dataset in DENSE else "thưa"
        nhan = "≈ 0%" if abs(doi) < 0.05 else f"{doi:+.1f}%"
        ax.set_title(f"{row.dataset} ({loai})\nminsup {row.minsup}: {nhan}", fontsize=9)
        ax.set_ylim(0, max(gia_tri) * 1.18)          # trục bắt đầu từ 0, chừa chỗ ghi số
        ax.tick_params(labelsize=8)

    axes[0].set_ylabel("Bộ nhớ đỉnh (MB)")
    fig.suptitle("Bộ nhớ đỉnh: bản cơ bản và bản tối ưu (tại minsup giữa; mỗi ô một thang đo riêng)", fontsize=10)
    save(fig, "memory")

def plot_txlen():
    """Thời gian và số itemset theo độ dài giao dịch trung bình (CSDL tổng hợp)."""
    df = pd.read_csv(f"{EXP_DIR}/txlen.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    # trái: thời gian, trục thường để thấy rõ đường cong tăng phi tuyến
    ax1.plot(df["avg_len"], df["t_opt_s"], marker="o")
    for x, y in zip(df["avg_len"], df["t_opt_s"]):
        ax1.annotate(f"{y:.2f}s", (x, y), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=8)
    ax1.set_title("(a) Thời gian chạy")
    ax1.set_xlabel("Độ dài giao dịch trung bình")
    ax1.set_ylabel("Thời gian (s)")
    ax1.set_ylim(0, df["t_opt_s"].max() * 1.15)
    ax1.grid(alpha=0.3)

    # phải: số itemset, trục log vì tăng theo hàm mũ
    ax2.plot(df["avg_len"], df["itemsets"], marker="o", color="tab:orange")
    for x, y in zip(df["avg_len"], df["itemsets"]):
        ax2.annotate(f"{y:,}".replace(",", "."), (x, y), textcoords="offset points",
                     xytext=(0, 7), ha="center", fontsize=8)
    ax2.set_yscale("log")
    ax2.set_title("(b) Số frequent itemset (thang log)")
    ax2.set_xlabel("Độ dài giao dịch trung bình")
    ax2.set_ylabel("Số frequent itemset")
    ax2.set_ylim(top=df["itemsets"].max() * 3)
    ax2.grid(alpha=0.3)

    so_gd = f"{int(df['transactions'].iloc[0]):,}".replace(",", ".")   # 10000 -> 10.000
    fig.suptitle(f"Ảnh hưởng của độ dài giao dịch (CSDL tổng hợp, {so_gd} giao dịch, "
                 f"minsup {df['minsup'].iloc[0]})")
    save(fig, "txlen")


def plot_runtime():
    """Thời gian chạy theo minsup giảm dần, mỗi CSDL một ô: basic, tối ưu, SPMF."""
    df = load("runtime")
    if df is None:
        return

    datasets = DENSE + SPARSE
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, name in zip(axes.flat, datasets):
        d = df[df["dataset"] == name].sort_values("minsup", ascending=False)
        ax.plot(d["minsup"], d["t_basic_s"], marker="o", label="cơ bản")
        ax.plot(d["minsup"], d["t_opt_s"], marker="s", label="tối ưu")
        if d["t_spmf_s"].notna().any():          # chỉ vẽ SPMF khi đã có số liệu
            ax.plot(d["minsup"], d["t_spmf_s"], marker="^", label="SPMF")

        ax.invert_xaxis()                         # minsup giảm dần từ trái sang phải
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))  # mốc 0.1, 0.2, 0.5, 1, 2, 5...
        ax.yaxis.set_major_formatter(SO_THUONG)
        ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))   # bỏ nhãn phụ rối mắt
        ax.set_title(f"{name} ({'dày' if name in DENSE else 'thưa'})")
        ax.set_xlabel("minsup (giảm dần →)")
        ax.set_ylabel("Thời gian (s, thang log)")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Thời gian chạy theo minsup: bản cơ bản, bản tối ưu và SPMF")
    save(fig, "runtime")


def plot_itemsets():
    """Số frequent itemset theo minsup: dữ liệu dày một ô, dữ liệu thưa một ô."""
    df = load("runtime")
    if df is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, group, title in zip(axes, [DENSE, SPARSE], ["Dữ liệu dày", "Dữ liệu thưa"]):
        for name in group:
            d = df[df["dataset"] == name].sort_values("minsup", ascending=False)
            ax.plot(d["minsup"], d["itemsets"], marker="o", label=name)
        ax.invert_xaxis()
        ax.set_yscale("log")
        ax.set_title(title)
        ax.set_xlabel("minsup (giảm dần →)")
        ax.set_ylabel("Số frequent itemset (thang log)")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Số frequent itemset theo minsup")
    save(fig, "itemsets")


def plot_scalability():
    """Thời gian theo số giao dịch, kèm đường tuyến tính để so sánh."""
    df = load("scalability")
    if df is None:
        return
    df = df.sort_values("transactions")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["transactions"], df["t_opt_s"], marker="o", label="đo được")

    # đường tuyến tính lý tưởng: đi qua gốc tọa độ và điểm 100%
    last = df.iloc[-1]
    ax.plot([0, last["transactions"]], [0, last["t_opt_s"]],
            linestyle="--", color="gray", label="tuyến tính")

    ax.set_title(f"Khả năng mở rộng ({df['dataset'].iloc[0]}, minsup={df['minsup'].iloc[0]})")
    ax.set_xlabel("Số giao dịch")
    ax.set_ylabel("Thời gian (s)")
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, "scalability")

def main():
    use_utf8_stdout()
    os.makedirs(FIG_DIR, exist_ok=True)
    plot_runtime()
    plot_itemsets()
    plot_scalability()
    plot_memory()
    plot_txlen()


if __name__ == "__main__":
    main()