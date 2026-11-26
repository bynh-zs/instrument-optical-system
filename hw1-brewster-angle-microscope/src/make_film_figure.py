# -*- coding: utf-8 -*-
"""生成「空气 / 单分子膜 / 水」三层模型与单层膜特征矩阵示意图。

输出：docs/images/film_model.png
运行：python src/make_film_figure.py  [--out PATH]
依赖 numpy、matplotlib。
"""
import os
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DEFAULT = os.path.join(BASE, "docs", "images", "film_model.png")

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
for _fc in FONT_CANDIDATES:
    if os.path.exists(_fc):
        try:
            fm.fontManager.addfont(_fc)
            plt.rcParams["font.family"] = fm.FontProperties(fname=_fc).get_name()
            break
        except Exception:
            continue

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "stix"

BLUE = "#1f5fbf"
ORANGE = "#e8722a"
GRAY = "#8894a5"
RED = "#c0392b"

ap = argparse.ArgumentParser(description="BAM 三层膜模型示意图")
ap.add_argument("--out", default=OUT_DEFAULT, help="输出 PNG 路径")
args = ap.parse_args()
os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

fig = plt.figure(figsize=(8.9, 4.15))
ax = fig.add_axes([0.030, 0.045, 0.575, 0.90])
axf = fig.add_axes([0.628, 0.045, 0.362, 0.90])
axf.axis("off")

ax.set_xlim(-3.4, 3.4)
ax.set_ylim(-1.45, 3.05)
ax.axis("off")

# 三层介质底色
ax.axhspan(0, 3.05, color="#f6f8fc", zorder=0)
ax.axhspan(-0.50, 0, color="#cfe0f5", zorder=0)
ax.axhspan(-1.45, -0.50, color="#a9c9ee", zorder=0)
ax.plot([-3.4, 3.4], [0, 0], color=BLUE, lw=1.5, zorder=2)
ax.plot([-3.4, 3.4], [-0.50, -0.50], color=BLUE, lw=1.2, ls=(0, (5, 3)), zorder=2)
ax.plot([0, 0], [-1.18, 2.72], color=GRAY, lw=1.1, ls=(0, (4, 4)), zorder=1)

# 入射光（sinθ=0.8，θ=53.13°，正好 3-4-5 三角形）
ax.annotate("", xy=(0, 0), xytext=(-2.4, 1.8),
            arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=2.4,
                            mutation_scale=17), zorder=3)
ax.text(-3.05, 2.02, "入射光（p 偏振 / TM）", color=ORANGE, fontsize=10.5)

# 反射光
ax.annotate("", xy=(2.4, 1.8), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.9, ls="--",
                            mutation_scale=15), zorder=3)
ax.text(1.28, 1.94, "反射光（膜区信号）", color=RED, fontsize=10.5)

# 透射光
ax.annotate("", xy=(0.72, -0.96), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.7,
                            mutation_scale=14), zorder=3)
ax.text(0.84, -0.80, "透射光", color=BLUE, fontsize=9.5)

# θB 弧（反射侧，与题面图 1 一致）
arc = np.linspace(np.radians(36.87), np.radians(90.0), 40)
ax.plot(1.15 * np.cos(arc), 1.15 * np.sin(arc), color=GRAY, lw=1.4, zorder=2)
ax.text(0.60, 1.33, r"$\theta_B$", color="#4a5568", fontsize=12.5)

# 三层标注
ax.text(-3.32, 2.74, "介质 0   空气   n0 = 1.000", color="#2c3e50", fontsize=10)
ax.annotate("单分子膜  nf = 1.50，d = 2 nm", xy=(0.92, -0.26),
            xytext=(1.02, 0.46), fontsize=9.2, color="#16324d",
            bbox=dict(fc="white", ec="#b9cde4", lw=0.8, alpha=0.94, pad=2.0),
            arrowprops=dict(arrowstyle="-", color="#7f9bb8", lw=0.9,
                            connectionstyle="arc3,rad=-0.18"))
ax.text(-3.32, -1.00, "介质 2   水亚相   ns = 1.333", color="#12324f", fontsize=10)
ax.text(-3.32, -1.31, "界面 1：空气 / 膜；界面 2：膜 / 水",
        color="#5b6b7c", fontsize=8.8)

# 右侧公式面板
axf.text(0.0, 0.985, "单层膜特征矩阵模型", fontsize=10.8,
         fontweight="bold", va="top", color="#1f3b57")
body = "\n".join([
    "",
    "介质 0   空气      n0 = 1.000",
    "介质 1   单分子膜   nf = 1.50，d = 2 nm",
    "介质 2   水亚相     ns = 1.333",
    "",
    "M = [ cosδ        i·sinδ/ηf ]",
    "    [ i·ηf·sinδ   cosδ      ]",
    "δ = 2π·nf·d·cosθf / λ",
    "",
    "p 偏振：η = n / cosθ",
    "s 偏振：η = n · cosθ",
    "",
    "[B, C]T = M · [1, ηs]T ，Y = C/B",
    "r = (η0 − Y) / (η0 + Y) ，R = |r|²",
    "",
    "校核：d → 0 时退化为 Fresnel 公式",
    "      θ0 = θB 时 rp = 0",
])
axf.text(0.0, 0.905, body, fontsize=9.2, va="top", linespacing=1.58,
         color="#222222")

fig.savefig(args.out, dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("FIG_OK", args.out)
