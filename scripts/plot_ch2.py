"""Vẽ biểu đồ cho thực nghiệm bộ nhớ và độ dài giao dịch (Chương 2, nửa B)."""
import os

import matplotlib
matplotlib.use("Agg")               # chỉ lưu ảnh, không mở cửa sổ
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import EXP_DIR, use_utf8_stdout

FIG_DIR = "docs/figures"
DENSE = ["chess", "mushroom"]
SPARSE = ["retail", "T10I4D100K"]

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
    df = pd.read_csv(f"{EXP_DIR}/memory.csv")
    x = np.arange(len(df))          # vị trí mỗi nhóm cột: 0, 1, 2, 3
    w = 0.38                        # bề rộng một cột

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - w / 2, df["peak_basic_mb"], w, label="basic")
    ax.bar(x + w / 2, df["peak_opt_mb"], w, label="tối ưu")

    ax.set_xticks(x)
    ax.set_xticklabels(df["dataset"])
    ax.set_yscale("log")           # trục log
    ax.set_ylabel("Peak memory (MB)")
    ax.legend()

    # ghi % giảm lên trên mỗi cặp cột
    for i, row in df.iterrows():
        giam = (row["peak_basic_mb"] - row["peak_opt_mb"]) / row["peak_basic_mb"] * 100
        ax.text(i, row["peak_basic_mb"] * 1.15, f"{-giam:+.1f}%", ha="center")

    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/memory.png", dpi=200)


def plot_txlen():
    df = pd.read_csv(f"{EXP_DIR}/txlen.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    ax1.plot(df["avg_len"], df["t_opt_s"], marker="o")
    ax1.set_xlabel("Độ dài giao dịch trung bình")
    ax1.set_ylabel("Thời gian (s)")
    

    # ax2: vẽ số itemset theo avg_len, trục tung dạng log
    ax2.plot(df["avg_len"], df["itemsets"], marker = "o")
    ax2.set_xlabel("Độ dài giao dịch trung bình")
    ax2.set_ylabel("So luon Itemset")
    ax2.set_yscale("log")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/txlen.png", dpi=200)


def plot_runtime():
    """Thời gian chạy theo minsup giảm dần, mỗi CSDL một ô: basic, tối ưu, SPMF."""
    df = load("runtime")
    if df is None:
        return

    datasets = DENSE + SPARSE
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, name in zip(axes.flat, datasets):
        d = df[df["dataset"] == name].sort_values("minsup", ascending=False)
        ax.plot(d["minsup"], d["t_basic_s"], marker="o", label="basic")
        ax.plot(d["minsup"], d["t_opt_s"], marker="s", label="tối ưu")
        if d["t_spmf_s"].notna().any():          # chỉ vẽ SPMF khi đã có số liệu
            ax.plot(d["minsup"], d["t_spmf_s"], marker="^", label="SPMF")

        ax.invert_xaxis()                         # minsup giảm dần từ trái sang phải
        ax.set_yscale("log")
        ax.set_title(name)
        ax.set_xlabel("minsup")
        ax.set_ylabel("Thời gian (s)")
        ax.grid(alpha=0.3)
        ax.legend()
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
        ax.set_xlabel("minsup")
        ax.set_ylabel("Số frequent itemset")
        ax.grid(alpha=0.3)
        ax.legend()
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