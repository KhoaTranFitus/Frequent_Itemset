"""Ứng dụng 1: vẽ hình cho báo cáo (docs/figures/app1_curves.png).

Ba ô, đều trên Groceries và đều tính lại trực tiếp bằng fpgrowth của nhóm (dưới
1 giây), không phụ thuộc file CSV nào:
    (a) số luật theo minconf, mỗi đường một mức minsup (APP1_MINSUPS x APP1_MINCONFS)
    (b) số tập phổ biến và số luật theo minsup, tại minconf mặc định (APP1_MINCONF)
    (c) support và confidence của từng luật ở minsup 0,005 / minconf 0,2, tô màu theo lift

Chạy từ thư mục gốc repo:
    python -m scripts.app1_plot
"""
import os

import matplotlib
matplotlib.use("Agg")               # chỉ lưu ảnh, không mở cửa sổ
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from src.algorithm.fpgrowth import fpgrowth
from src.apps.basket import load_dataset
from src.config import (APP1_MINCONF, APP1_MINCONFS, APP1_MINSUPS, to_min_count,
                        use_utf8_stdout)
from src.rules import generate_rules

FIG_DIR = "docs/figures"
SCATTER = (0.005, 0.2)              # (minsup, minconf) của ô (c)
SO_THUONG = FuncFormatter(lambda v, _: f"{v:g}")


def sweep(data):
    """{minsup: (số tập phổ biến, {minconf: list luật})} trên lưới của src/config.py."""
    n = len(data)
    result = {}
    for minsup in APP1_MINSUPS:
        itemsets = fpgrowth(data, to_min_count(minsup, n))
        result[minsup] = (len(itemsets),
                          {c: generate_rules(itemsets, n, c) for c in APP1_MINCONFS})
    return result


def main():
    use_utf8_stdout()
    data, _, _ = load_dataset("groceries")
    n = len(data)
    grid = sweep(data)
    minsups = sorted(grid, reverse=True)                      # cao -> thấp
    colors = plt.get_cmap("Blues")([0.35 + 0.6 * k / (len(minsups) - 1)
                                    for k in range(len(minsups))])

    with plt.style.context("default"):
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.2))

        # (a) minconf siết số luật
        for color, minsup in zip(colors, minsups):
            counts = [len(grid[minsup][1][c]) for c in APP1_MINCONFS]
            ax1.plot(APP1_MINCONFS, counts, marker="o", color=color,
                     label=f"minsup {minsup:g}")
        ax1.set_yscale("symlog", linthresh=1)
        ax1.yaxis.set_major_formatter(SO_THUONG)
        ax1.set_title("(a) Số luật theo minconf")
        ax1.set_xlabel("minconf")
        ax1.set_ylabel("Số luật (thang symlog)")
        ax1.legend(fontsize=8)
        ax1.grid(alpha=0.3)

        # (b) số luật tăng nhanh hơn số tập phổ biến khi hạ minsup
        xs = sorted(grid)
        n_sets = [grid[m][0] for m in xs]
        n_rules = [len(grid[m][1][APP1_MINCONF]) for m in xs]
        ax2.plot(xs, n_sets, marker="o", color="tab:blue", label="tập phổ biến")
        ax2.plot(xs, n_rules, marker="s", color="tab:orange",
                 label=f"luật (minconf {APP1_MINCONF:g})")
        for x, a, b in zip(xs, n_sets, n_rules):
            up, down = (7, -13) if a >= b else (-13, 7)       # nhãn của đường trên nằm trên
            ax2.annotate(f"{a:,}".replace(",", "."), (x, a), textcoords="offset points",
                         xytext=(0, up), ha="center", fontsize=8, color="tab:blue")
            ax2.annotate(f"{b:,}".replace(",", "."), (x, b), textcoords="offset points",
                         xytext=(0, down), ha="center", fontsize=8, color="tab:orange")
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.set_xlim(max(xs) * 1.5, min(xs) / 1.5)            # minsup giảm dần sang phải
        ax2.set_ylim(min(n_rules) / 2, max(n_sets + n_rules) * 2.5)
        ax2.set_xticks(xs)
        ax2.minorticks_off()
        ax2.xaxis.set_major_formatter(SO_THUONG)
        ax2.yaxis.set_major_formatter(SO_THUONG)
        ax2.set_title("(b) Số tập phổ biến và số luật theo minsup")
        ax2.set_xlabel("minsup (giảm dần sang phải, thang log)")
        ax2.set_ylabel("Số lượng (thang log)")
        ax2.legend(fontsize=8, loc="upper left")
        ax2.grid(alpha=0.3, which="both")

        # (c) lift cao dồn về góc support thấp
        minsup, minconf = SCATTER
        rules = generate_rules(fpgrowth(data, to_min_count(minsup, n)), n, minconf)
        rules.sort(key=lambda r: r.lift)                      # điểm lift cao vẽ sau, nằm trên
        points = ax3.scatter([r.support for r in rules], [r.confidence for r in rules],
                             c=[r.lift for r in rules], cmap="viridis", s=14,
                             edgecolor="none")
        fig.colorbar(points, ax=ax3, label="lift")
        ax3.set_title(f"(c) {len(rules)} luật (minsup {minsup:g}, minconf {minconf:g})")
        ax3.set_xlabel("support")
        ax3.set_ylabel("confidence")
        ax3.grid(alpha=0.3)

        fig.tight_layout()
        os.makedirs(FIG_DIR, exist_ok=True)
        path = f"{FIG_DIR}/app1_curves.png"
        fig.savefig(path, dpi=200)
        plt.close(fig)
    print(f"Đã lưu {path}")
    for x, a, b in zip(xs, n_sets, n_rules):
        print(f"  minsup {x:<6g} {a:>6} tập phổ biến | {b:>6} luật ở minconf {APP1_MINCONF:g}")


if __name__ == "__main__":
    main()
