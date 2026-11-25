"""Ứng dụng 2, bước 4: vẽ hồ sơ vị trí và top emerging pattern.

Chạy từ thư mục gốc repo:
    python -m scripts.app2_plot
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from scripts.app2_emerging import emerging
from src.app2_bio import load_groups, position_name, read_splice
from src.config import use_utf8_stdout
from src.utils import invert_code

DATA_PATH = "data/app2/splice.data"
FIG_DIR = "docs/figures"
BASES = "ACGT"
LABELS = ["EI", "IE", "N"]


def position_profile(seqs):
    """Ma trận 4 x 60: tỉ lệ mẫu có nucleotide b tại vị trí i."""
    counts = np.zeros((4, 60))
    for seq in seqs:
        for i, base in enumerate(seq):
            if base in BASES:
                counts[BASES.index(base), i] += 1 # cộng 1 vào đúng ô (hàng của base, cột i)
    return counts / len(seqs)                        # đổi số đếm sang tỉ lệ


def plot_profile(rows):
    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    for ax, label in zip(axes, LABELS):
        seqs = [seq for lab, seq in rows if lab == label]
        prof = position_profile(seqs)

        im = ax.imshow(prof, aspect="auto", cmap="Blues", vmin=0, vmax=1)
        ax.set_yticks(range(4))
        ax.set_yticklabels(list(BASES))
        ax.set_title(f"{label} ({len(seqs)} mẫu)")
        ax.axvline(29.5, color="red", linewidth=1)   # ranh giới giữa -1 và +1

    ticks = [0, 5, 10, 15, 20, 25, 30, 34, 39, 44, 49, 54, 59]
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels([position_name(i) for i in ticks])
    axes[-1].set_xlabel("Vị trí so với ranh giới (vạch đỏ = ranh giới, giữa -1 và +1)")
    fig.suptitle("Tỉ lệ từng nucleotide tại mỗi vị trí, theo nhóm (càng đậm càng phổ biến)")
    fig.colorbar(im, ax=axes, label="Tỉ lệ mẫu")
    fig.savefig(f"{FIG_DIR}/app2_profile.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Đã lưu {FIG_DIR}/app2_profile.png")


def plot_emerging(groups, code, top_k=8, min_n=5):
    """Top emerging pattern theo growth. Thanh xám: #N < min_n, growth không ổn định."""
    name_of = invert_code(code)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    for ax, label in zip(axes, ["EI", "IE"]):
        rows = emerging(groups[label], groups["N"], 0.5)
        rows.sort(key=lambda r: (r[3], r[1]), reverse=True)
        rows = rows[:top_k][::-1]                    # đảo ngược để thanh lớn nhất nằm trên cùng

        names = [", ".join(name_of[i] for i in r[0]) for r in rows]
        growth = [r[3] for r in rows]
        mau = ["tab:blue" if r[4] >= min_n else "lightgray" for r in rows]
        ax.barh(names, growth, color=mau)
        for y, r in enumerate(rows):
            ax.text(r[3] * 1.08, y, f"{r[3]:.1f}  (#N={r[4]})", va="center", fontsize=8)

        ax.set_xscale("log")
        ax.set_xlim(right=max(growth) * 4)            # chừa chỗ cho nhãn, không bị cắt
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        ax.set_xlabel(f"Growth rate = sup({label}) / sup(N), thang log")
        ax.set_title(f"Top {top_k} emerging pattern của {label} so với N (minsup 0,5)")

    # chú thích màu dùng chung
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color="tab:blue", label=f"#N ≥ {min_n}: đáng tin"),
                        Patch(color="lightgray", label=f"#N < {min_n}: growth không ổn định")],
               loc="lower center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(f"{FIG_DIR}/app2_emerging.png", dpi=200)
    plt.close(fig)
    print(f"Đã lưu {FIG_DIR}/app2_emerging.png")


def main():
    use_utf8_stdout()
    os.makedirs(FIG_DIR, exist_ok=True)
    plot_profile(read_splice(DATA_PATH))
    groups, code = load_groups(DATA_PATH)
    plot_emerging(groups, code)


if __name__ == "__main__":
    main()