# -*- coding: utf-8 -*-
"""报告插图绘制（仅用 Pillow）：蓝橙配色的原理图、流程图与 Ψ、Δ 曲线。"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 交付包根目录
DATA = os.path.join(PKG, "data")
BUILD = os.path.join(DATA, "_build")
FIG = os.path.join(PKG, "docs", "images")
os.makedirs(FIG, exist_ok=True)

S = json.load(open(os.path.join(BUILD, "report_data.json"), encoding="utf-8"))
WAVES = S["wavelengths"]
ANGLES = S["angles"]

NAVY = "#1f5fbf"
BLUE = "#4a86d8"
LIGHT = "#e8f1fc"
ORANGE = "#e8791a"
TEAL = "#2b8c8c"
PURPLE = "#7048a8"
GREEN = "#3a8b3a"
GREY = "#5a6675"
DARK = "#1b2430"
GRID = "#d8e2f0"
PALETTE = [NAVY, ORANGE, TEAL, PURPLE, GREEN]

# 图内标题与 Word 图题重复，故默认不画标题，并裁去顶部标题带
SHOW_TITLE = False
TITLE_H = 60

FONT_CANDIDATES = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                   r"C:\Windows\Fonts\simsun.ttc"]


def font(sz, bold=False):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def text(d, xy, s, size=24, color=DARK, anchor=None, bold=False):
    d.text(xy, s, fill=color, font=font(size, bold), anchor=anchor)


def chart(fname, title, xlabel, ylabel, series, ylim=None, xlim=None,
          note=None, legend_cols=None, ydec=None):
    W, H = 1500, 940
    L, R, T, B = 165, 70, 125, 135
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    if SHOW_TITLE:
        text(d, (W // 2, 34), title, 36, NAVY, anchor="mt", bold=True)
    if note:
        text(d, (W // 2, 82), note, 21, GREY, anchor="mt")
    x0 = xlim[0] if xlim else WAVES[0]
    x1 = xlim[1] if xlim else WAVES[-1]
    vals = [v for _, _, arr in series for _, v in arr]
    if ylim:
        y0, y1 = ylim
    else:
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.12 or 1
        y0, y1 = lo - pad, hi + pad

    def px(x):
        return L + (x - x0) / (x1 - x0) * (W - L - R)

    def py(y):
        return H - B - (y - y0) / (y1 - y0) * (H - T - B)

    # grid
    for i in range(6):
        y = y0 + (y1 - y0) * i / 5
        d.line([(L, py(y)), (W - R, py(y))], fill=GRID, width=2)
        tick = "%.1f" % y if ydec is None else (("%.*f" % (ydec, y)).rstrip("0").rstrip(".") or "0")
        text(d, (L - 14, py(y)), tick, 22, GREY, anchor="rm")
    nx = 5
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        d.line([(px(x), T), (px(x), H - B)], fill=GRID, width=2)
        text(d, (px(x), H - B + 12), "%g" % x, 22, GREY, anchor="mt")
    d.rectangle([L, T, W - R, H - B], outline=NAVY, width=3)
    text(d, ((L + W - R) // 2, H - 55), xlabel, 26, DARK, anchor="mt")
    d.save_rot = None
    # y label (rotated)：窄条旋转后贴到坐标框左侧，避免透明条压住网格
    yl = Image.new("RGBA", (620, 44), (255, 255, 255, 0))
    yd = ImageDraw.Draw(yl)
    yd.text((310, 22), ylabel, fill=DARK, font=font(26), anchor="mm")
    yl = yl.rotate(90, expand=True)
    im.paste(yl, (12, T + max(0, (H - T - B - yl.height) // 2)), yl)
    # curves
    for name, color, arr in series:
        pts = [(px(x), py(y)) for x, y in arr]
        d.line(pts, fill=color, width=5, joint="curve")
        for k in range(0, len(pts), 5):
            d.ellipse([pts[k][0] - 4, pts[k][1] - 4, pts[k][0] + 4, pts[k][1] + 4], fill=color)
    # legend
    cols = legend_cols or len(series)
    lx, ly = L + 22, T + 18
    for i, (name, color, arr) in enumerate(series):
        cx = lx + (i % cols) * 265
        cy = ly + (i // cols) * 42
        d.line([(cx, cy + 12), (cx + 48, cy + 12)], fill=color, width=6)
        text(d, (cx + 58, cy), name, 22, DARK)
    p = os.path.join(FIG, fname)
    if not SHOW_TITLE:
        im = im.crop((0, TITLE_H, W, H))
    im.save(p)
    print("figure:", p)
    return p


# ------------------------------------------------------------------ data curves
def series_for(key, d=10.0):
    out = []
    for a in ANGLES:
        arr = [[float(x), float(y)] for x, y in S[key][str(d)][str(a)]]
        out.append(("%g°" % a, PALETTE[ANGLES.index(a) % len(PALETTE)], arr))
    return out


chart("psi_vs_lambda.png", "图14  SiO2 10.0 nm 薄膜的 Ψ–λ 曲线（65°–75°）",
      "真空波长 λ / nm", "Ψ / (°)",
      series_for("psi"), ylim=(0, 48),
      note="空气 / SiO2 10.0 nm / 晶体 Si；ρ = r_p/r_s = tanΨ·exp(−iΔ)",
      legend_cols=5)

chart("delta_vs_lambda.png", "图15  SiO2 10.0 nm 薄膜的 Δ–λ 曲线（65°–75°）",
      "真空波长 λ / nm", "Δ / (°)",
      series_for("delta"), ylim=(40, 190),
      note="Δ = −arg(ρ)（VirtualLab 相位约定，[0°, 360°)）",
      legend_cols=5)

# thickness sensitivity at 75 deg
diff = S["diff"]
rows75 = [r for r in diff if float(r[1]) == 75.0]
psi_diff = [[float(r[0]), float(r[4])] for r in rows75]
del_diff = [[float(r[0]), float(r[7])] for r in rows75]
chart("sensitivity_psi.png", "图16  1 Å 膜厚差引起的 ΔΨ（75°）",
      "真空波长 λ / nm", "ΔΨ / (°)",
      [("Ψ(10.1 nm) − Ψ(10.0 nm)", ORANGE, psi_diff)],
      note="与常规椭偏仪 Ψ 分辨率 0.02° 比较", legend_cols=1, ydec=3)
chart("sensitivity_delta.png", "图17  1 Å 膜厚差引起的 ΔΔ（75°）",
      "真空波长 λ / nm", "ΔΔ / (°)",
      [("Δ(10.1 nm) − Δ(10.0 nm)", NAVY, del_diff)],
      note="与常规椭偏仪 Δ 分辨率 0.1° 比较", legend_cols=1)

# official cross-check
cmp_path = os.path.join(DATA, "official_case_check.csv")
import csv
rr = list(csv.reader(open(cmp_path, encoding="utf-8-sig")))[1:]
pts = [(float(r[2]), float(r[3])) for r in rr]
pts_d = [(float(r[5]), float(r[6])) for r in rr]
W2, H2 = 1500, 830
im = Image.new("RGB", (W2, H2), "white")
d = ImageDraw.Draw(im)
if SHOW_TITLE:
    text(d, (W2 // 2, 30), "图13  等效模型与官方案例 Ψ、Δ 数值对照（216 个点）", 36, NAVY, anchor="mt", bold=True)
text(d, (W2 // 2, 80), "横轴：官方案例 .da 结果；纵轴：本模型计算值；橙线为 y = x", 22, GREY, anchor="mt")
for cx, label, data, lim in ((375, "Ψ / (°)", pts, (15, 50)), (1125, "Δ / (°)", pts_d, (135, 185))):
    L, T, SZ = cx - 240, 160, 480
    d.rectangle([L, T, L + SZ, T + SZ], outline=NAVY, width=3)
    lo, hi = lim
    f = lambda v: (L + (v - lo) / (hi - lo) * SZ, T + SZ - (v - lo) / (hi - lo) * SZ)
    for i in range(5):
        v = lo + (hi - lo) * i / 4
        d.line([(L, f(v)[1]), (L + SZ, f(v)[1])], fill=GRID, width=2)
        d.line([(f(v)[0], T), (f(v)[0], T + SZ)], fill=GRID, width=2)
        text(d, (L - 10, f(v)[1]), "%g" % v, 20, GREY, anchor="rm")
        text(d, (f(v)[0], T + SZ + 8), "%g" % v, 20, GREY, anchor="mt")
    d.line([f(lo), f(hi)], fill=ORANGE, width=3)
    for a, b in data:
        x, y = f(a)[0], f(b)[1]
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=NAVY)
    text(d, (L + SZ // 2, T + SZ + 48), "官方案例  " + label, 24, DARK, anchor="mt")
    # y-axis title removed: the subtitle already states the y-axis meaning,
    # and the old label overlapped the tick numbers ("本模型2.5" / "本模型60").
text(d, (W2 // 2, 770),
     "Ψ 最大偏差 0.389°、Δ 最大偏差 0.197°（差异来自 7.6 实测色散数据的分段线性插值）",
     23, ORANGE, anchor="mt")
if not SHOW_TITLE:
    im = im.crop((0, TITLE_H - 2, W2, H2))
im.save(os.path.join(FIG, "official_case_compare.png"))
print("figure: 图13_官方案例对照.png")

# ------------------------------------------------------------------ schematic 1
W3, H3 = 1500, 900
im = Image.new("RGB", (W3, H3), "white")
d = ImageDraw.Draw(im)
if SHOW_TITLE:
    text(d, (W3 // 2, 28), "图3  椭圆偏振测量原理与三层样品结构", 36, NAVY, anchor="mt", bold=True)
# layers
d.rectangle([160, 210, 1340, 300], fill="#f4f8fe", outline=NAVY, width=3)
d.rectangle([160, 300, 1340, 420], fill=LIGHT, outline=NAVY, width=3)
d.rectangle([160, 420, 1340, 620], fill="#dfe9f7", outline=NAVY, width=3)
text(d, (1090, 250), "入射介质：空气  n0 = 1", 27, DARK, anchor="mm")
text(d, (750, 350), "SiO2 薄膜  d = 10.0 nm（对比 10.1 nm）  扩展 Cauchy", 26, DARK, anchor="mm")
text(d, (750, 520), "基底：晶体 Si  Silicon(crystalline)-Si_(1985)", 27, DARK, anchor="mm")
# rays (kept left of the medium label so no text is crossed)
d.line([(280, 145), (600, 300)], fill=ORANGE, width=6)
d.line([(600, 300), (930, 145)], fill=NAVY, width=6)
d.polygon([(600, 300), (548, 270), (554, 294)], fill=ORANGE)
d.polygon([(930, 145), (884, 162), (900, 184)], fill=NAVY)
text(d, (255, 112), "线偏振平面波 200 nm–1 µm", 24, ORANGE)
text(d, (955, 112), "反射椭圆偏振光", 24, NAVY)
text(d, (750, 670), "θ = 65°–75°（步长 2.5°）    TE (s) / TM (p)", 26, DARK, anchor="mm")
# formula box
d.rounded_rectangle([300, 720, 1200, 850], radius=16, fill="#fff4e8", outline=ORANGE, width=4)
text(d, (750, 762), "ρ = r_p / r_s = r_TM / r_TE = tanΨ · exp(−iΔ)", 30, DARK, anchor="mm", bold=True)
text(d, (750, 812), "Ψ = arctan|ρ|     Δ = −arg(ρ)", 27, ORANGE, anchor="mm")
im = im.crop((0, TITLE_H - 8, W3, H3))
im.save(os.path.join(FIG, "principle_structure.png"))
print("figure: 图3_原理与结构.png")

# ------------------------------------------------------------------ schematic 2
W4, H4 = 1400, 1500
im = Image.new("RGB", (W4, H4), "white")
d = ImageDraw.Draw(im)
if SHOW_TITLE:
    text(d, (W4 // 2, 26), "图4  7.6 试用版等效椭偏测量执行流程", 36, NAVY, anchor="mt", bold=True)
steps = [
    ("① 版本与许可核查", "About：7.6.1.18 Trial；确认无 Ellipsometry Analyzer"),
    ("② 元件与计算器复查", "Catalogs 九目录 + Detectors 过滤 ellips + Calculators 11 项"),
    ("③ 软件内取复 Fresnel 系数", "Fresnel Effects Calculator：Air / 晶体 Si，TE 与 TM"),
    ("④ 材料色散反演", "0° 入射 20 个波长点：N_Si = (1 − r_s)/(1 + r_s)"),
    ("⑤ 建立三层等效模型", "空气 / SiO2(10.0 nm) / Si，传输矩阵 Airy 公式"),
    ("⑥ 模型校验", "d = 0 与软件 75° 实测对比；与官方 .da 216 点对比"),
    ("⑦ 波长与角度扫描", "200–1000 nm / 41 点；65°–75° / 5 点"),
    ("⑧ 膜厚灵敏度", "仅改 10.0 → 10.1 nm 重算，得 ΔΨ、ΔΔ"),
    ("⑨ 结果图与数据导出", "Ψ–λ、Δ–λ、差值曲线 + CSV + 参数记录表"),
    ("⑩ 报告与提交包", "论文式 Word + PDF + 截图 + 数据 + 脚本 + 录屏"),
]
y = 115
for i, (t, sub) in enumerate(steps):
    col = ORANGE if i in (2, 5, 7) else NAVY
    d.rounded_rectangle([130, y, 1270, y + 112], radius=14,
                        fill="#fff4e8" if i in (2, 5, 7) else LIGHT,
                        outline=col, width=4)
    d.rounded_rectangle([130, y, 200, y + 112], radius=14, fill=col, outline=col, width=2)
    text(d, (165, y + 56), str(i + 1), 34, "white", anchor="mm", bold=True)
    text(d, (235, y + 32), t, 27, col, bold=True)
    text(d, (235, y + 76), sub, 22, DARK)
    if i < len(steps) - 1:
        d.line([(700, y + 112), (700, y + 140)], fill=NAVY, width=4)
        d.polygon([(700, y + 146), (688, y + 128), (712, y + 128)], fill=NAVY)
    y += 140
text(d, (W4 // 2, 82), "任课教师 2026-11-15 答复：确实没有该器件时“实现这个功能也行”", 22, GREY, anchor="mm")
im = im.crop((0, TITLE_H - 18, W4, H4))
im.save(os.path.join(FIG, "workflow.png"))
print("figure: 图4_执行流程.png")

# Si dispersion from software inversion
si = S["si_points"]
chart("si_nk.png", "图9  由软件实测反演的晶体 Si 复折射率色散",
      "真空波长 λ / nm", "n, k",
      [("n（折射率实部）", NAVY, [[x, n] for x, n, k in si]),
       ("k（消光系数）", ORANGE, [[x, k] for x, n, k in si])],
      ylim=(0, 6.5), note="来自 VirtualLab 7.6 Fresnel Effects Calculator 的 0° 入射复系数", legend_cols=2)
print("all figures done")


# ---- contact sheet covering ALL eight delivered result figures ----
def build_sheet():
    names = ["psi_vs_lambda.png", "delta_vs_lambda.png",
             "sensitivity_psi.png", "sensitivity_delta.png",
             "official_case_compare.png", "principle_structure.png",
             "workflow.png", "si_nk.png"]
    labels = ["图14  Psi-lambda", "图15  Delta-lambda",
              "图16  dPsi (1 A)", "图17  dDelta (1 A)",
              "图13  official 216-pt check", "图3  principle / stack",
              "图4  B-prime workflow", "图9  Si n,k dispersion"]
    CW, CH, GAP, HEAD = 360, 250, 12, 26
    cols, rows = 4, 2
    W = cols * (CW + GAP) + GAP
    H = rows * (CH + GAP) + GAP
    sheet = Image.new("RGB", (W, H), "#dfe6ee")
    d = ImageDraw.Draw(sheet)
    for i, (fn, lab) in enumerate(zip(names, labels)):
        x = GAP + (i % cols) * (CW + GAP)
        y = GAP + (i // cols) * (CH + GAP)
        im = Image.open(os.path.join(FIG, fn)).convert("RGB")
        box = CW - 12, CH - HEAD - 10
        r = min(box[0] / im.width, box[1] / im.height)
        im = im.resize((int(im.width * r), int(im.height * r)))
        px = x + (CW - im.width) // 2
        py = y + HEAD + (CH - HEAD - im.height) // 2
        sheet.paste(im, (px, py))
        d.rectangle([x, y, x + CW, y + CH], outline=NAVY, width=2)
        d.text((x + 8, y + 5), lab, fill=DARK, font=font(17))
    p = os.path.join(FIG, "sheet.png")
    sheet.save(p)
    print("figure:", p, sheet.size)


build_sheet()
