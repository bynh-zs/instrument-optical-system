# -*- coding: utf-8 -*-
"""
多线结构光在互反射条件下的光条中心提取
=====================================
输入：一张多线结构光相机图像（默认 data/groove_render.png，1600×1200）
输出：out/overlay.png、out/profile.png、out/stats.txt

算法流程（S1—S6）：
  S1 ROI 选取：按行亮度自动确定被测件所在行带，屏蔽台面与背景；
  S2 背景归一化：逐列减去行带内亮度中值，压掉环境照明与台面反光的缓变背景；
  S3 候选峰检测：沿列方向求行带平均亮度，取局部极大，得到"主光条 + 互反射副光条"候选；
  S4 结构先验选线：把 N 条等间隔光平面在像面上的成像写成一维射影（交比）模型
      u_i = (a·i + b)/(c·i + 1)，对候选组合做残差最小化，剔除偏离模型的副峰；
      相比"等欧氏间距"先验，射影模型能吸收相机斜视造成的透视压缩；
  S5 亚像素定位：对保留峰在 ±Δ 邻域内做加权灰度重心，抗饱和与噪声；
  S6 输出：中心列坐标、按已知线距自标定的比例尺、射影残差与间距统计。

用法：
    python src/line_center_extract.py
    python src/line_center_extract.py --input path/to/img.png --outdir out --pitch-mm 250 --lines 7

依赖：numpy、Pillow
"""
import argparse
import os
from itertools import combinations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(HERE, "data", "groove_render.png")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]
CENTROID_HALF = 9  # 灰度重心半窗（像素）


def load(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float64) / 255.0
    lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
    return im, lum


def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def roi_rows(lum):
    """按行亮度自动确定被测件行带。"""
    rows = lum.mean(axis=1)
    th = np.percentile(rows, 70)
    idx = np.where(rows > th)[0]
    return int(idx.min()), int(idx.max())


def column_profile(lum, r0, r1):
    band = lum[r0:r1, :]
    prof = band.mean(axis=0)
    return prof - np.median(prof)


def find_peaks(prof, th_ratio=0.18):
    """候选峰：局部极大 + 阈值，返回 [(粗位置, 峰高)]。"""
    th = prof.max() * th_ratio
    peaks = []
    for x in range(1, len(prof) - 1):
        if prof[x] >= prof[x - 1] and prof[x] > prof[x + 1] and prof[x] > th:
            peaks.append((float(x), float(prof[x])))
    return peaks


def centroid(prof, x0, half=CENTROID_HALF):
    """加权灰度重心：以 x0 为中心、±half 邻域内按亮度加权（负值截零）。"""
    lo, hi = int(max(0, x0 - half)), int(min(len(prof) - 1, x0 + half))
    xs = np.arange(lo, hi + 1)
    w = np.clip(prof[lo:hi + 1], 0, None)
    if w.sum() <= 1e-12:
        return float(x0)
    return float((xs * w).sum() / w.sum())


def fit_projective(xs):
    """一维射影模型 u_i=(a·i+b)/(c·i+1) 的最小二乘拟合，返回 (残差RMS, 参数, 预测值)。"""
    n = len(xs)
    i = np.arange(n, dtype=float)
    u = np.asarray(xs, dtype=float)
    A = np.column_stack([i, np.ones(n), -u * i])   # a·i + b - u·c·i - u = 0
    sol, *_ = np.linalg.lstsq(A, u, rcond=None)
    a, b, c = sol
    pred = (a * i + b) / (c * i + 1.0)
    return float(np.sqrt(np.mean((u - pred) ** 2))), (a, b, c), pred


def select_by_prior(peaks, n, w_intensity=0.15):
    """在候选中挑出 n 条主光条：射影残差 + 强度项 的联合代价最小。"""
    cand = sorted(sorted(peaks, key=lambda p: -p[1])[:min(len(peaks), 20)], key=lambda p: p[0])
    if len(cand) < n:
        return list(cand), [], None
    best = None
    for comb in combinations(cand, n):
        xs = [c[0] for c in comb]
        rms, _, _ = fit_projective(xs)
        cost = rms + w_intensity * (-np.mean([c[1] for c in comb]))
        if best is None or cost < best[0]:
            best = (cost, comb, rms)
    _, comb, rms = best
    rest = [q for q in peaks if q not in comb]
    return list(comb), rest, rms


def draw_overlay(im, r0, r1, xs, rejected, mean_pitch, pitch_mm, scale, n_lines):
    w, h = im.size
    pad = 30
    y0c, y1c = max(0, r0 - pad), min(h - 1, r1 + pad)
    ov = im.crop((0, y0c, w, y1c))
    dr = ImageDraw.Draw(ov)
    f20, f16 = font(20), font(16)
    yy0, yy1 = r0 - y0c, r1 - y0c
    dr.line([(0, yy0), (w - 1, yy0)], fill=(60, 200, 120), width=2)
    dr.line([(0, yy1), (w - 1, yy1)], fill=(60, 200, 120), width=2)
    for i, x in enumerate(xs):
        dr.line([(x, yy0), (x, yy1)], fill=(0, 255, 80), width=3)
        dr.text((x - 5, yy0 - 24), f"{i + 1}", fill=(0, 255, 80), font=f20)
    for (x, _) in rejected:
        dr.line([(x, yy0), (x, yy1)], fill=(255, 200, 40), width=2)
        dr.text((x - 12, yy1 + 2), "副峰", fill=(255, 200, 40), font=f16)
    bh = 112
    box = (18, ov.height - bh - 22, 468, ov.height - 22)
    dr.rounded_rectangle(box, radius=6, fill=(255, 255, 255))
    dr.text((32, box[1] + 10), f"绿线：检出主光条中心 {len(xs)}/{n_lines}", fill=(0, 120, 20), font=f16)
    dr.text((32, box[1] + 36), f"黄线：被剔除的互反射副峰 {len(rejected)} 条", fill=(170, 120, 0), font=f16)
    dr.text((32, box[1] + 62), f"平均线距 {mean_pitch:.1f} px = {pitch_mm:.0f} mm", fill=(30, 30, 30), font=f16)
    dr.text((32, box[1] + 88), f"自标定比例尺 {scale:.3f} mm/px", fill=(30, 30, 30), font=f16)
    return ov


def draw_profile(prof, xs, rejected, w):
    cw, ch = 1600, 420
    canvas = Image.new("RGB", (cw, ch), (255, 255, 255))
    dc = ImageDraw.Draw(canvas)
    f20, f16 = font(20), font(16)
    pmin, pmax = prof.min(), prof.max()
    pn = (prof - pmin) / (pmax - pmin)
    pts = [(i, int(ch - 40 - pn[i] * (ch - 90))) for i in range(w)]
    dc.line(pts, fill=(20, 20, 20), width=1)
    for x in xs:
        yv = ch - 40 - (prof[int(round(x))] - pmin) / (pmax - pmin) * (ch - 90)
        dc.line([(x, ch - 40), (x, yv)], fill=(0, 160, 60), width=3)
        dc.text((x - 6, ch - 36), f"{x:.0f}", fill=(0, 120, 20), font=f16)
    for (x, _) in rejected:
        yv = ch - 40 - (prof[int(round(x))] - pmin) / (pmax - pmin) * (ch - 90)
        dc.line([(x, ch - 40), (x, yv)], fill=(220, 160, 0), width=2)
    dc.text((10, 8), "被测件行带的列亮度曲线（背景归一化后）", fill=(0, 0, 0), font=f20)
    dc.text((10, ch - 30), "列坐标 / px", fill=(60, 60, 60), font=f16)
    dc.text((cw - 210, 8), "绿：主光条中心  黄：副峰", fill=(60, 60, 60), font=f16)
    return canvas


def run(input_path, outdir, n_lines, pitch_mm):
    os.makedirs(outdir, exist_ok=True)
    im, lum = load(input_path)
    h, w = lum.shape
    r0, r1 = roi_rows(lum)
    prof = column_profile(lum, r0, r1)
    peaks = sorted(find_peaks(prof), key=lambda p: p[0])

    chosen, rejected, _ = select_by_prior(peaks, n_lines)
    chosen.sort(key=lambda p: p[0])

    xs = np.array([centroid(prof, c[0]) for c in chosen])
    d = np.diff(xs)
    cv = float(np.std(d) / np.mean(d)) if len(d) else float("nan")
    mean_pitch = float(np.mean(d)) if len(d) else float("nan")
    scale = pitch_mm / mean_pitch
    residual_mm = np.abs(d - mean_pitch) * scale
    rms_px, params, _ = fit_projective(xs)
    rms_mm = rms_px * scale

    draw_overlay(im, r0, r1, xs, rejected, mean_pitch, pitch_mm, scale, n_lines).save(os.path.join(outdir, "overlay.png"))
    draw_profile(prof, xs, rejected, w).save(os.path.join(outdir, "profile.png"))

    lines = [
        "多线结构光光条中心提取 测试统计（v2：射影先验 + 灰度重心）",
        f"测试数据：{os.path.basename(input_path)}（{w}×{h}）",
        f"ROI 行带：{r0}–{r1} px",
        f"候选峰数量（主光条+互反射副峰）：{len(peaks)}",
        f"检出主光条：{len(chosen)} / 期望 {n_lines}",
        f"剔除副峰：{len(rejected)}",
        "各主光条中心（列坐标，亚像素 px）：" + ", ".join(f"{x:.2f}" for x in xs),
        "相邻间距（px）：" + ", ".join(f"{v:.2f}" for v in d),
        f"平均线距：{mean_pitch:.2f} px；按设计线距 {pitch_mm:.0f} mm 自标定比例尺：{scale:.4f} mm/px",
        f"原始间距变异系数 CV = {cv * 100:.2f}%，最大偏差 {residual_mm.max():.2f} mm（含透视压缩，非定位误差）",
        f"一维射影模型拟合：u_i=(a·i+b)/(c·i+1)，a={params[0]:.4f}，b={params[1]:.4f}，c={params[2]:.6f}",
        f"射影模型残差 RMS = {rms_px:.2f} px ≈ {rms_mm:.2f} mm（相对 {pitch_mm:.0f} mm 线距 {rms_mm / pitch_mm * 100:.2f}%）",
    ]
    txt = "\n".join(lines)
    with open(os.path.join(outdir, "stats.txt"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt)
    return dict(roi=(r0, r1), peaks=len(peaks), found=len(chosen), rejected=len(rejected),
                centers=xs.tolist(), mean_pitch=mean_pitch, scale=scale, cv=cv,
                rms_px=rms_px, rms_mm=rms_mm, params=params)


def main():
    ap = argparse.ArgumentParser(description="多线结构光互反射条件下的光条中心提取")
    ap.add_argument("--input", default=DEFAULT_INPUT, help="输入图像路径")
    ap.add_argument("--outdir", default=os.path.join(HERE, "out"), help="输出目录")
    ap.add_argument("--lines", type=int, default=7, help="投射器线数（先验）")
    ap.add_argument("--pitch-mm", type=float, default=250.0, help="设计线距 / mm，用于自标定")
    args = ap.parse_args()
    run(args.input, args.outdir, args.lines, args.pitch_mm)


if __name__ == "__main__":
    main()
