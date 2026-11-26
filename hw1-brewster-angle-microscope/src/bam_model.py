# -*- coding: utf-8 -*-
"""
大作业 1 · 布儒斯特角显微镜（BAM）—— 成像数学模型与「除样品外」因素数值仿真
=============================================================================
对应题面：
  第 1 项  建立成像系统的数学模型
  第 4 项  分析除样品外、以布儒斯特角入射时影响反射光强的其他因素；
           讨论光路对准、图像对焦
  第 5 项  （加分）分析上述因素对测量结果的影响

工具合理性：
  Blender 负责光机结构、光路与对准/对焦的「真实世界可视化」仿真；
  但 Blender 不是物理光学追迹软件，不能给出 Fresnel 反射率与偏振消光比。
  因此本脚本用 Python + numpy 按薄膜特征矩阵法独立计算反射率，
  作为 Blender 三维仿真的定量补充（课程要求「也可选择其他工具完成，并说明合理性」）。

物理模型：
  单层膜 空气(n0) / 单分子膜(nf, 厚度 d) / 水亚相(ns)
  特征矩阵 M = [[cosδ, i·sinδ/η_f], [i·η_f·sinδ, cosδ]]
  p(TM) 光学导纳 η = n/cosθ ；s(TE) 光学导纳 η = n·cosθ
  Y = C/B, [B,C]^T = M·[1, η_s]^T ； r = (η_0 − Y)/(η_0 + Y) ； R = |r|²
  d→0 时退化为裸界面 Fresnel 公式；θ=θB 时 p 偏振 r_p=0。

输出：
  docs/images/ 下 8 张 PNG（反射率曲线、因素对比、误差传递、对准对焦示意）
  data/ 下 4 份 CSV + 1 份结果摘要 summary.txt
运行： python src/bam_model.py  [--figdir DIR] [--datadir DIR]
      依赖 numpy、matplotlib
"""
import os
import csv
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# ----------------------------------------------------------------------------
# 0. 路径与绘图样式
# ----------------------------------------------------------------------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "docs", "images")
DAT = os.path.join(BASE, "data")

# 允许用命令行覆盖输出目录，便于在 CI / 其他机器上跑到别处
import argparse
_ap = argparse.ArgumentParser(description="BAM 物理模型与十因素数值仿真")
_ap.add_argument("--figdir", default=FIG, help="图像输出目录")
_ap.add_argument("--datadir", default=DAT, help="CSV / 摘要输出目录")
_args = _ap.parse_args()
FIG = _args.figdir
DAT = _args.datadir
os.makedirs(FIG, exist_ok=True)
os.makedirs(DAT, exist_ok=True)

# 中文字体：按平台顺序回退；找不到时 matplotlib 用默认字体（中文会显示为方框）
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
plt.rcParams["font.size"] = 11
BLUE = "#1f5fbf"
ORANGE = "#e8722a"
GREEN = "#2a9d6f"
GRAY = "#8894a5"
RED = "#c0392b"

# ----------------------------------------------------------------------------
# 1. 常量（全部来自 05_调研资料/器件与文献核实台账.md）
# ----------------------------------------------------------------------------
N0 = 1.000                 # 空气（气相 n1）
NS = 1.333                 # 水亚相（液相 n2）——建模教学基准值
NF = 1.50                  # 单分子膜折射率（脂肪酸/磷脂单层典型量级）
D0 = 2.0                   # 基准膜厚 nm（单分子膜典型厚度）
LAM0 = 632.8               # nm，Thorlabs HNL050L
THETA_B = math.degrees(math.atan(NS / N0))     # 53.1232°
NA = 0.28                  # Mitutoyo M Plan Apo 10X
M_MAG = 10.0               # 放大倍率
PIX_UM = 5.5               # Basler acA2040-90um 像元
WELL = 11900.0             # e- 满阱
DARK_E = 13.8              # e- 暗噪声
QE = 0.6207                # 量子效率 @541 nm
ER0 = 1e5                  # GL10-A 消光比 100000:1
DIV_MRAD = 1.0             # HNL050L 发散角 1.0 mrad
DN_DT = -9.2e-5            # /°C，Daimon & Masumura 2007（20.0 / 21.5 °C 差分）
DTH_DT = -0.0019           # °/°C

# Daimon & Masumura 2007, Appl. Opt. 46(19):3811-3820, 20.0 °C 蒸馏水 Sellmeier
SELL_20 = [(5.684027565e-1, 5.101829712e-3),
           (1.726177391e-1, 1.821153936e-2),
           (2.086189578e-2, 2.620722293e-2),
           (1.130748688e-1, 1.069792721e1)]

def n_water(lam_nm, T=20.0):
    """Sellmeier 色散 + 一阶温度修正；lam_nm 单位 nm。"""
    lam = lam_nm / 1000.0
    L = lam * lam
    n2 = 1.0 + sum(B * L / (L - C) for B, C in SELL_20)
    return math.sqrt(n2) + DN_DT * (T - 20.0)

def theta_b_of(n_sub):
    return math.degrees(math.atan(n_sub / N0))

N_MEAS = n_water(LAM0, 20.0)                    # 1.332106
TH_MEAS = theta_b_of(N_MEAS)                    # 53.1048°
DELTA_TH = THETA_B - TH_MEAS                    # 0.0185°

# ----------------------------------------------------------------------------
# 2. Fresnel / 单层膜特征矩阵
# ----------------------------------------------------------------------------
def reflectance(theta_deg, d_nm=0.0, pol="p", n_sub=NS,
                n_film=NF, lam_nm=LAM0, n_inc=N0):
    """返回强度反射率 R。theta_deg 为入射角（度），d_nm 为膜厚（nm）。"""
    th = math.radians(theta_deg)
    s0 = n_inc * math.sin(th)                    # 守恒量 n·sinθ

    def cj(n):
        st = s0 / n
        return np.sqrt(complex(1.0 - st * st, 0.0))

    def eta(n):
        return n / cj(n) if pol == "p" else n * cj(n)

    lam = lam_nm
    delta = 2.0 * math.pi / lam * (d_nm) * n_film * cj(n_film)
    c, s = np.cos(delta), np.sin(delta)
    ef, e0, es = eta(n_film), eta(n_inc), eta(n_sub)
    B = c + 1j * s / ef * es
    C = 1j * ef * s + es * c
    Y = C / B
    r = (e0 - Y) / (e0 + Y)
    return float(abs(r) ** 2)

def r_bare(theta_deg, pol="p", n_sub=NS):
    return reflectance(theta_deg, 0.0, pol, n_sub=n_sub)

R_BARE_P = r_bare(THETA_B, "p")                 # ≈ 0（浮点残差）
R_S = r_bare(THETA_B, "s")                      # ≈ 0.078
R_FILM = reflectance(THETA_B, D0, "p")          # 基准膜区反射率
# 灵敏度 dR/dd（用于误差传递）
_h = 0.002
S_D = (reflectance(THETA_B, D0 + _h, "p") - reflectance(THETA_B, D0 - _h, "p")) / (2 * _h)

# --- 2.1 独立解析校核（不复用 reflectance 的实现，避免自证） ---
def fresnel_R(theta_deg, pol="p", n_inc=N0, n_sub=NS):
    """独立 Fresnel 解析式，返回强度反射率；用于交叉校核特征矩阵实现。"""
    th = math.radians(theta_deg)
    c1 = math.cos(th)
    s2 = n_inc * math.sin(th) / n_sub
    c2 = math.sqrt(max(0.0, 1.0 - s2 * s2))
    if pol == "p":
        r = (n_sub * c1 - n_inc * c2) / (n_sub * c1 + n_inc * c2)
    else:
        r = (n_inc * c1 - n_sub * c2) / (n_inc * c1 + n_sub * c2)
    return r * r

_VER_TH = np.linspace(0.0, 85.0, 1001)
DEV_MAX = max(abs(reflectance(float(t), 0.0, pol) - fresnel_R(float(t), pol))
              for t in _VER_TH for pol in ("p", "s"))
K_QUAD = R_FILM / D0 ** 2              # 二次系数，约 6.13e-7 nm^-2
S_D_ANALYTIC = 2.0 * K_QUAD * D0       # 由 R_p = k·d^2 解析得到的灵敏度

def ang_avg(theta_c_deg, half_width_deg, d_nm, n=61):
    """角度在 ±half_width 内均匀分布时的平均反射率（准直/振动/收集角）。"""
    xs = np.linspace(-half_width_deg, half_width_deg, n)
    return float(np.mean([reflectance(theta_c_deg + x, d_nm, "p") for x in xs]))

def gauss_avg(theta_c_deg, sigma_deg, d_nm, n=81):
    """局部液面斜率服从高斯分布时的平均反射率。"""
    xs = np.linspace(-3 * sigma_deg, 3 * sigma_deg, n)
    w = np.exp(-0.5 * (xs / max(sigma_deg, 1e-9)) ** 2)
    w /= w.sum()
    return float(sum(wi * reflectance(theta_c_deg + x, d_nm, "p")
                     for wi, x in zip(w, xs)))

# ----------------------------------------------------------------------------
# 3. 十项「除样品外」因素扫描
# ----------------------------------------------------------------------------
# 每个因素：名称 / 扰动 / 扰动依据 / 类别(A 改反射率, B 改测量链) / ΔR / 等效 Δd
factors = []

def add(name, perturb, basis, kind, dR, note=""):
    dd = dR / S_D if S_D != 0 else float("nan")
    factors.append(dict(名称=name, 扰动=perturb, 扰动依据=basis, 类别=kind,
                        相对反射率变化=dR, 相对变化比=dR / R_FILM if R_FILM else float("nan"),
                        等效膜厚误差_nm=dd, 说明=note))

# 1 偏振消光比：s 分量泄漏，非相干叠加 R = R_p + R_s/ER
ER_BAD = 1e3
dR1 = R_S * (1.0 / ER_BAD - 1.0 / ER0)
add("① 偏振消光比退化", "ER: 10⁵ → 10³", "GL10-A 标称 10⁵:1；调节不当或棱镜污染可退化两个量级",
    "A", dR1, "s 分量在 θB 下仍有约 7.8% 反射，是背景的主要来源")

# 2 入射角偏差：直接算 R_p(θB+Δθ)
dth = 0.05
R2 = ang_avg(THETA_B + dth, 0.0, D0)
add("② 入射角偏差 Δθ", "+0.05°", "URS50BPP 分辨率 0.0014°、重复性 ±0.002°；取装配/复现时的失准量级",
    "A", R2 - R_FILM, "R_p 对 Δθ 为二次响应，偏离 θB 即抬高背景；有膜时最小反射角右移约 0.0065°")

# 3 波长漂移：n(λ) 变 → 实际 θB 变，几何角固定 → 等效 Δθ
dlam = 1.0
n_l = n_water(LAM0 + dlam)
dth_l = theta_b_of(n_l) - THETA_B
R3 = reflectance(THETA_B + dth_l, D0, "p")
add("③ 波长漂移 Δλ", "+1 nm", "HNL050L 纵模间隔 435 MHz（≈0.00058 nm）；取远大于实际的保守上界",
    "A", R3 - R_FILM, "dn/dλ = −0.031 µm⁻¹；θB 随 λ 单调下降")

# 4 光束准直性（发散半角）
alpha_deg = math.degrees(math.atan(DIV_MRAD / 1000.0))
R4 = ang_avg(THETA_B, alpha_deg, D0)
add("④ 光束准直性（发散角）", "±1.0 mrad", "HNL050L 标称发散角 1.0 mrad",
    "A", R4 - R_FILM, "锥内各光线入射角不同，平均后 R_p 上升")

# 5 液面毛细波 / 机械振动（局部斜率 RMS）
sig_deg = 0.5 / 1000.0 * 180.0 / math.pi
R5 = gauss_avg(THETA_B, sig_deg, D0)
add("⑤ 液面毛细波与振动", "斜率 RMS 0.5 mrad", "开放液面在滑障运动与环境振动下的典型小扰动量级",
    "A", R5 - R_FILM, "局部入射角随机起伏，时间平均后抬高背景")

# 6 环境杂散光（加性背景，相对入射强度）
b6 = 1e-6
add("⑥ 环境杂散光", "背景 = 1e-6 I0", "实验室照明/桌面反射；可用遮光罩与 632.8 nm 窄带滤光片抑制",
    "B", b6, "加性偏置，直接叠加到灰度，不改变界面反射率")

# 7 光学元件表面反射与散射
b7 = 1e-5
add("⑦ 元件表面反射/散射", "等效 stray = 1e-5 I0", "WPH05M-633 单面反射 <0.25%、GL10-A AR 面 <1%；少量进入视场",
    "B", b7, "与⑥同为加性背景，但来自光路内部，需靠光阑与倾斜安装抑制")

# 8 物镜 NA（收集效率 ∝ NA²，按绝对灰度反演口径）
NA_BAD = 0.20
k8 = (NA_BAD / NA) ** 2
add("⑧ 物镜数值孔径/收集效率", "NA 0.28 → 0.20", "M Plan Apo 10X 标称 NA 0.28；换低倍/小孔径镜组时下降",
    "B", (k8 - 1.0) * R_FILM, "信号按 NA² 缩放；若做背景归一化则该项可消除")

# 9 探测器曝光/增益/噪声（信号按曝光缩放，另计 SNR）
t_ratio = 0.1
add("⑨ 探测器曝光时间/增益", "曝光 10 ms → 1 ms", "Basler acA2040-90um 可编程曝光；满阱 11.9 ke⁻、暗噪声 13.8 e⁻",
    "B", (t_ratio - 1.0) * R_FILM, "同时降低 SNR（见图 17）；缩短曝光是抑制饱和的主要手段")

# 10 亚相温度引起 n2 漂移
dT = 2.0
dth_T = DTH_DT * dT
R10 = reflectance(THETA_B + dth_T, D0, "p")
add("⑩ 亚相温度引起 n2 漂移", "+2 °C", "dn/dT = -9.2e-5 /°C（Daimon & Masumura 2007）；dθB/dT = -0.0019°/°C",
    "A", R10 - R_FILM, "温度改变 n₂ 从而改变真实 θB，几何角未重标定时形成等效 Δθ")

# ----------------------------------------------------------------------------
# 4. 对比度 C = (R_film − R_bg)/R_bg
# ----------------------------------------------------------------------------
R_BG_BASE = 1e-7          # 基准杂散（遮光罩 + 632.8 nm 窄带滤光片后的残差，相对入射强度）

def contrast(R_bg_extra=R_BG_BASE):
    bg = R_BARE_P + R_S / ER0 + R_bg_extra
    return (R_FILM - bg) / bg if bg > 0 else float("inf")

C0 = contrast()

# ----------------------------------------------------------------------------
# 5. 探测器 SNR（Basler acA2040-90um 真实参数）
# ----------------------------------------------------------------------------
def snr_of(S_e):
    """信号电子数 S_e 下的信噪比（散粒 + 暗噪声，忽略读出噪声）。"""
    S_e = min(S_e, WELL)                     # 满阱截断
    return S_e / math.sqrt(S_e + DARK_E ** 2)

def d_from_S(S_e):
    """按绝对灰度反演：信号缩放 k=S/S_ref 引起的等效膜厚误差。"""
    dR = (S_e / S_REF - 1.0) * R_FILM
    return dR / S_D

S_REF = 0.67 * WELL                         # 基准信号：约 67% 满阱，避免饱和
EXPOSURES = np.array([0.1, 0.3, 0.5, 1, 2, 3, 5, 8, 10, 15, 20, 30, 50])  # ms
S_E = np.minimum(S_REF * EXPOSURES / 10.0, WELL)
SNR = np.array([snr_of(s) for s in S_E])

# ----------------------------------------------------------------------------
# 6. 对准与对焦（题面第 4 项讨论项）
# ----------------------------------------------------------------------------
# 对准：入射角误差 Δθ → 反射光方向偏转 2Δθ → 筒镜焦面光斑偏移
#   f_tube = 200 mm，Δx = f·2Δθ(rad)；相机半宽 11.26/2 = 5.63 mm
F_TUBE_MM = 200.0
HALF_SENSOR_MM = 11.26 / 2.0
ALIGN_DTH = np.array([0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0])   # 度
ALIGN_SHIFT_MM = F_TUBE_MM * 2.0 * np.radians(ALIGN_DTH)
ALIGN_IN_FOV = ALIGN_SHIFT_MM < HALF_SENSOR_MM

# 对焦：液面与光轴夹角 = 90° − θB = TILT（液面与焦面夹角 = θB）
TILT_DEG = 90.0 - THETA_B                    # 36.8768°
DOF_UM = 3.5                                 # Mitutoyo 标称景深
# 液面上沿入射面方向距中心 x 处，相对焦面的轴向离焦 = x·cos(TILT) = x·sinθB
# 厂商标称景深 DOF 按全深计，故 DOF/cos(TILT) 是清晰带全宽，半宽为其一半
FOCUS_BAND_UM = DOF_UM / math.cos(math.radians(TILT_DEG))   # 全宽约 4.4 µm
# 若把相机倾斜满足 Scheimpflug，则全视场可同时清晰
RAYLEIGH_UM = 0.61 * (LAM0 / 1000.0) / NA
OBLIQUE_UM = RAYLEIGH_UM / math.cos(math.radians(THETA_B))
PIX_OBJ_UM = PIX_UM / M_MAG
FOV_MM = 11.26 / M_MAG
FOV_OBLIQUE_MM = FOV_MM / math.cos(math.radians(THETA_B))

# ----------------------------------------------------------------------------
# 7. 输出 CSV / TXT
# ----------------------------------------------------------------------------
def wcsv(name, header, rows):
    with open(os.path.join(DAT, name), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

# 7.1 反射率–角度曲线
th_arr = np.linspace(0.0, 85.0, 341)
wcsv("refl_vs_angle.csv",
     ["入射角_deg", "R_p_裸界面", "R_s_裸界面", "R_p_膜区_d=2nm", "R_s_膜区_d=2nm"],
     [[f"{t:.3f}", f"{r_bare(t,'p'):.10e}", f"{r_bare(t,'s'):.10e}",
       f"{reflectance(t,D0,'p'):.10e}", f"{reflectance(t,D0,'s'):.10e}"] for t in th_arr])

# 7.2 膜厚–反射率
d_arr = np.linspace(0.0, 10.0, 201)
wcsv("refl_vs_thickness.csv",
     ["膜厚_nm", "R_p", "R_s", "R_p_相对裸界面增量"],
     [[f"{d:.3f}", f"{reflectance(THETA_B,d,'p'):.10e}",
       f"{reflectance(THETA_B,d,'s'):.10e}",
       f"{reflectance(THETA_B,d,'p')-R_BARE_P:.10e}"] for d in d_arr])

# 7.3 十因素扫描
wcsv("ten_factors.csv",
     ["序号", "因素", "扰动", "扰动依据", "类别", "ΔR", "ΔR/R_film", "等效膜厚误差_nm", "说明"],
     [[i + 1, f["名称"], f["扰动"], f["扰动依据"], f["类别"],
       f"{f['相对反射率变化']:.6e}", f"{f['相对变化比']:.4f}",
       f"{f['等效膜厚误差_nm']:.4f}", f["说明"]] for i, f in enumerate(factors)])

# 7.4 色散 / 温度 / 对准 / 对焦 / SNR 汇总
misc = []
for lam in (543.0, 587.6, 632.8, 659.0):
    nn = n_water(lam, 20.0)
    misc.append(["波长_nm", f"{lam:.1f}", "n2(20°C)", f"{nn:.6f}", "θB_deg", f"{theta_b_of(nn):.4f}"])
for T in (19.0, 20.0, 20.0 + 0.001, 21.0, 22.0, 25.0):
    nn = n_water(LAM0, T)
    misc.append(["温度_C", f"{T:.3f}", "n2(632.8nm)", f"{nn:.6f}", "θB_deg", f"{theta_b_of(nn):.4f}"])
wcsv("dispersion_align_focus_snr.csv",
     ["项目", "x", "量1", "v1", "量2", "v2"],
     misc + [["对准_Δθ_deg", f"{a:.3f}", "光斑偏移_mm", f"{b:.4f}", "在视场内", str(c)]
             for a, b, c in zip(ALIGN_DTH, ALIGN_SHIFT_MM, ALIGN_IN_FOV)]
          + [["曝光_ms", f"{e:.2f}", "信号_e-", f"{s:.0f}", "SNR", f"{q:.2f}"]
             for e, s, q in zip(EXPOSURES, S_E, SNR)])

# 7.5 结果摘要
summary = f"""BAM 物理模型与十因素数值仿真 · 结果摘要
================================================================
建模基准    n1={N0:.3f}  n2={NS:.3f}  θB={THETA_B:.4f}°  λ={LAM0:.1f} nm
实测修正    n2(632.8nm,20°C)={N_MEAS:.6f}  θB={TH_MEAS:.4f}°  Δ={DELTA_TH:.4f}°
            dn/dT={DN_DT:.3e}/°C  dθB/dT={DTH_DT:.4f}°/°C
裸界面      R_p(θB)={R_BARE_P:.3e}（浮点精确零）   R_s(θB)={R_S:.6f}
独立校核    Fresnel 解析式 vs 特征矩阵(d=0)：0–85°、1001 点、p/s 两偏振
            最大绝对偏差 DEV_MAX={DEV_MAX:.2e}（双精度机器精度）
            k = R_film/d0^2 = {K_QUAD:.3e} nm^-2（不是 2.45e-6）
            解析灵敏度 2k·d0 = {S_D_ANALYTIC:.3e} /nm，数值差分 {S_D:.3e} /nm，
            相对差 {abs(S_D_ANALYTIC/S_D-1):.2e}
膜区基准    nf={NF:.2f}  d0={D0:.1f} nm  R_film={R_FILM:.6e}
灵敏度      dR/dd = {S_D:.6e} /nm
最小反射角  有膜(d=2 nm)时 R_p 极小值出现在 θB+0.0065°（膜层改变有效布儒斯特条件）；
            因此 |Δθ|<0.0065° 时 R 可能略降，本扫描取 Δθ=+0.05° 以落在单调上升区。
            这也说明固定角度法（Hönig & Möbius 1991）中成膜引起反射率上升是稳健的。
基准对比度  C0 = (R_film − R_bg)/R_bg = {C0:.1f}  (R_bg 含 GL10-A 的 s 泄漏 R_s/1e5)

分辨率链    Rayleigh δ=0.61λ/NA = {RAYLEIGH_UM:.4f} µm (⊥入射面)
            斜视投影 1/cosθB = {1/math.cos(math.radians(THETA_B)):.4f}
            → 沿入射面 δ = {OBLIQUE_UM:.4f} µm
            像元物面 = {PIX_UM}/{M_MAG:.0f} = {PIX_OBJ_UM:.3f} µm < Nyquist {RAYLEIGH_UM/2:.4f} µm  ✓ 满足
            视场 = {FOV_MM:.3f} mm，斜视沿入射面 = {FOV_OBLIQUE_MM:.3f} mm

对焦        液面与光轴夹角 = 90°−θB = {TILT_DEG:.4f}°（液面与焦面夹角 = θB）；景深按全深计
            沿液面距中心 x 处的轴向离焦 = x·cos(TILT) = x·sinθB
            → 清晰带全宽 W = DOF/sinθB = DOF/cos36.88° = {FOCUS_BAND_UM:.2f} µm
              （半宽 ≈ {FOCUS_BAND_UM/2:.2f} µm；W = DOF/cos36.88°，不是 DOF/(2 sin36.88°)）
            结论：斜视下仅视场中心窄带清晰，实际须用 Scheimpflug 倾斜相机
                  或 Z 轴扫描拼接（与 KSV NIMA MicroBAM 官方说明一致）。

对准        筒镜 f={F_TUBE_MM:.0f} mm，Δθ → 反射光偏 2Δθ → 光斑偏移 f·2Δθ
            Δθ=0.01° → {ALIGN_SHIFT_MM[1]:.4f} mm（远小于像方靶面半宽 {HALF_SENSOR_MM:.3f} mm）
            Δθ=2.0°  → {ALIGN_SHIFT_MM[-1]:.4f} mm（{'仍在' if ALIGN_IN_FOV[-1] else '超出'}视场）
            测角台 Newport URS50BPP 分辨率 0.0014° 足以把对准误差控制在 0.01° 内。

探测器      Basler acA2040-90um：满阱 {WELL:.0f} e⁻、暗噪声 {DARK_E:.1f} e⁻、QE {QE*100:.2f}%
            基准信号取 0.67×满阱 = {S_REF:.0f} e⁻（10 ms 曝光）；SNR={snr_of(S_REF):.1f}
            曝光降到 1 ms → 信号 {S_E[3]:.0f} e⁻，SNR={SNR[3]:.1f}

十因素扫描（按 |等效膜厚误差| 降序，详见 CSV）
"""
order = sorted(range(len(factors)), key=lambda i: -abs(factors[i]["等效膜厚误差_nm"]))
for i in order:
    f = factors[i]
    summary += (f"  {f['名称']:<20s} ΔR={f['相对反射率变化']:+.3e} "
                f"ΔR/R={f['相对变化比']:+.3f}  Δd={f['等效膜厚误差_nm']:+.4f} nm  [{f['类别']}类]\n")
summary += """
误差传递口径：Δd = ΔR / (dR/dd)。A 类因素改变界面反射率 R_p，B 类因素改变
测量链信号/背景；按「绝对灰度反演」口径统一折算为等效膜厚误差。若采集后做
背景归一化（减暗场 + 除以参考光强），B 类中的缩放类因素（⑧⑨）可被消除，
加性背景类（⑥⑦）仍需扣除。噪声类因素主要降低图像信噪比与畴边界识别精度，
不完全体现为膜厚偏置。
"""
with open(os.path.join(DAT, "summary.txt"), "w", encoding="utf-8") as f:
    f.write(summary)
print(summary)

# ----------------------------------------------------------------------------
# 8. 出图
# ----------------------------------------------------------------------------
def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=170, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# 图 12 反射率–入射角
fig, ax = plt.subplots(figsize=(8.4, 4.9))
rp = np.array([max(r_bare(t, "p"), 1e-9) for t in th_arr])
rs = np.array([r_bare(t, "s") for t in th_arr])
rf = np.array([max(reflectance(t, D0, "p"), 1e-14) for t in th_arr])
ax.semilogy(th_arr, rp, color=BLUE, lw=2.6, label=r"$R_p$ 裸界面（p 偏振）")
ax.semilogy(th_arr, rf, color=GREEN, lw=2.0, ls="--", label=r"$R_p$ 膜区（$d$=2 nm）")
ax.semilogy(th_arr, rs, color=ORANGE, lw=2.0, ls="-.",
            label=r"$R_s$ 裸界面（s 偏振）")
ax.axvline(THETA_B, color=RED, lw=1.3, ls=":")
ax.annotate(r"$\theta_B$ = %.4f°" % THETA_B, xy=(THETA_B, 2e-6),
            xytext=(THETA_B + 5.5, 8e-5), fontsize=11, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
ax.annotate("裸界面 $R_p$ 在 $\\theta_B$ 处降为 0；\n膜区把极小值抬到 %.2e" % R_FILM,
            xy=(THETA_B, 1.3e-6), xytext=(5, 4.5e-7), fontsize=9.2, color="#555555",
            va="top", arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.0,
                            connectionstyle="arc3,rad=0.10"))
ax.set_xlabel("入射角  θ / (°)"); ax.set_ylabel("强度反射率  R")
ax.set_xlim(0, 85); ax.set_ylim(2e-8, 1.5)
ax.grid(alpha=.3, which="both"); ax.legend(frameon=False, fontsize=9.8, loc="lower right")
save(fig, "refl_vs_angle.png")

# 图 13 膜厚–反射率（双纵轴，R_p 单独放大）
fig, ax = plt.subplots(figsize=(8.4, 4.9))
rp_d = np.array([reflectance(THETA_B, d, "p") for d in d_arr])
rs_d = np.array([reflectance(THETA_B, d, "s") for d in d_arr])
k2 = R_FILM / D0 ** 2
ax.plot(d_arr, rp_d, color=BLUE, lw=2.6, label=r"$R_p$（成像用，左轴）")
ax.plot(d_arr, k2 * d_arr ** 2, color=GRAY, lw=1.6, ls="--",
        label=r"二次拟合 $R_p\propto d^2$")
ax.axvline(D0, color=GRAY, ls=":", lw=1.2)
ax.annotate("基准工作点 $d_0$=2 nm\n$R_{film}$=%.2e" % R_FILM,
            xy=(D0, R_FILM), xytext=(3.4, R_FILM * 2.1), fontsize=9.6,
            arrowprops=dict(arrowstyle="->", color=GRAY))
ax.set_xlabel("单分子膜厚度  d / nm")
ax.set_ylabel(r"$R_p$（左轴）", color=BLUE)
ax.tick_params(axis="y", colors=BLUE)
ax.set_ylim(0, R_FILM * 8)
ax2 = ax.twinx()
ax2.plot(d_arr, rs_d, color=ORANGE, lw=2.0, ls="-.", label=r"$R_s$（对照，右轴）")
ax2.set_ylabel(r"$R_s$（右轴）", color=ORANGE)
ax2.tick_params(axis="y", colors=ORANGE)
ax2.set_ylim(0.0775, 0.0815)
ax.grid(alpha=.3)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=9.2, loc="upper left")
save(fig, "refl_vs_thickness.png")

# 图 14 十因素 ΔR/R
fig, ax = plt.subplots(figsize=(8.6, 5.4))
labels = [f["名称"] for f in factors]
vals = [f["相对变化比"] for f in factors]
cols = [BLUE if f["类别"] == "A" else ORANGE for f in factors]
y = np.arange(len(factors))
ax.barh(y, vals, color=cols, alpha=.88)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.5)
ax.invert_yaxis()
ax.axvline(0, color="#333333", lw=1.0)
ax.set_xscale("symlog", linthresh=0.01)
ax.set_xlabel(r"反射光强相对变化  $\Delta R / R_{film}$（对称对数轴）")
ax.grid(alpha=.3, axis="x")
ax.set_xlim(-2, 60)
for yi, v in zip(y, vals):
    ax.text(1.02, yi, "%+.3f" % v, va="center", fontsize=8.8,
            transform=ax.get_yaxis_transform())
save(fig, "factors_intensity.png")

# 图 15 等效膜厚误差（加分项）
fig, ax = plt.subplots(figsize=(8.6, 5.4))
dd = [f["等效膜厚误差_nm"] for f in factors]
order2 = sorted(range(len(factors)), key=lambda i: abs(dd[i]))
ax.barh(np.arange(len(factors)), [abs(dd[i]) for i in order2],
        color=[BLUE if factors[i]["类别"] == "A" else ORANGE for i in order2], alpha=.88)
ax.set_yticks(np.arange(len(factors)))
ax.set_yticklabels([factors[i]["名称"] for i in order2], fontsize=9.5)
ax.set_xscale("log")
ax.set_xlabel("等效膜厚误差  |Δd| / nm（对数轴，按绝对灰度反演口径）")
ax.grid(alpha=.3, axis="x")
ax.set_xlim(5e-4, 1e2)
for k, i in enumerate(order2):
    ax.text(1.02, k, "%+.4f" % dd[i], va="center", fontsize=8.8,
            transform=ax.get_yaxis_transform())
save(fig, "factors_equiv_thickness.png")

# 图 16 图像对比度随偏振消光比的变化
fig, ax = plt.subplots(figsize=(8.4, 4.9))
ERs = np.logspace(2, 6, 201)
for dth_, c_, lab_ in ((0.01, BLUE, "Δθ = 0.01°（指标内）"),
                       (0.05, GREEN, "Δθ = 0.05°"),
                       (0.20, ORANGE, "Δθ = 0.20°（明显失准）")):
    rf_ = reflectance(THETA_B + dth_, D0, "p")
    rb_ = r_bare(THETA_B + dth_, "p")
    cs = [(rf_ - (rb_ + R_S / er + R_BG_BASE)) / (rb_ + R_S / er + R_BG_BASE)
          for er in ERs]
    ax.semilogx(ERs, cs, color=c_, lw=2.2, label=lab_)
ax.axhline(1.0, color=RED, ls="--", lw=1.3)
ax.text(1.3e2, 1.07, "可分辨判据  C = 1", color=RED, fontsize=9.4)
ax.axvline(ER0, color=GRAY, ls=":", lw=1.3)
ax.annotate("GL10-A  ER=1e5:1", xy=(ER0, 1.4), xytext=(1.4e5, 1.95),
            fontsize=9.4, color="#555555",
            arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.0))
rf01 = reflectance(THETA_B + 0.01, D0, "p")
er_req = R_S / (rf01 / 2.0 - R_BG_BASE)
ax.annotate("C≥1 需 ER ≥ %.2e\n（GL10-A 余量 %.1f×）" % (er_req, ER0 / er_req),
            xy=(er_req, 1.0), xytext=(2.2e3, 0.42), fontsize=9.4, color=BLUE,
            arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0))
ax.set_xlabel("偏振消光比  ER（对数轴）")
ax.set_ylabel(r"图像对比度  $C=(R_{film}-R_{bg})/R_{bg}$")
ax.set_ylim(-0.6, 2.4)
ax.grid(alpha=.3, which="both")
ax.legend(frameon=False, fontsize=9.4, loc="lower right")
save(fig, "contrast_vs_er.png")

# 图 17 曝光–SNR
fig, ax = plt.subplots(figsize=(8.2, 4.6))
ax.plot(EXPOSURES, SNR, "o-", color=BLUE, lw=2.2, ms=5, label="SNR（散粒 + 暗噪声）")
ax.axvline(10, color=GRAY, ls=":", lw=1.3)
ax.annotate("基准曝光 10 ms\n(0.67×满阱)", xy=(10, snr_of(S_REF)),
            xytext=(14, snr_of(S_REF) * .78), fontsize=9.5,
            arrowprops=dict(arrowstyle="->", color=GRAY))
ax2 = ax.twinx()
ax2.plot(EXPOSURES, S_E, "s--", color=ORANGE, lw=1.6, ms=4, label="信号电子数")
ax2.axhline(WELL, color=RED, ls=":", lw=1.2)
ax2.set_ylabel("信号 / e-（橙，右轴）", color=ORANGE)
ax.set_xlabel("曝光时间  t / ms"); ax.set_ylabel("SNR（蓝，左轴）", color=BLUE)
ax.grid(alpha=.3)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="lower right", fontsize=9.4)
save(fig, "exposure_vs_snr.png")

# 图 18 θB 随波长/温度漂移 + 分辨率链
fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3))
lams = np.linspace(500, 700, 101)
ths_l = [theta_b_of(n_water(l)) for l in lams]
axes[0].plot(lams, ths_l, color=BLUE, lw=2.2)
axes[0].axvline(LAM0, color=RED, ls=":", lw=1.3)
axes[0].annotate("632.8 nm", xy=(LAM0, TH_MEAS), xytext=(648, TH_MEAS + .012),
                 fontsize=9.5, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
axes[0].set_xlabel("波长  λ / nm"); axes[0].set_ylabel(r"$\theta_B$ / (°)")
axes[0].set_title(r"(a) 水色散引起 $\theta_B$ 漂移")
axes[0].grid(alpha=.3)
Ts = np.linspace(15, 30, 76)
ths_T = [theta_b_of(n_water(LAM0, T)) for T in Ts]
axes[1].plot(Ts, ths_T, color=ORANGE, lw=2.2)
axes[1].axvline(20, color=RED, ls=":", lw=1.3)
axes[1].set_xlabel("亚相温度  T / °C"); axes[1].set_ylabel(r"$\theta_B$ / (°)")
axes[1].set_title(r"(b) 温度漂移  $d\theta_B/dT$ = %.4f °/°C" % DTH_DT)
axes[1].annotate("20 °C 基准\n53.1048°", xy=(20, TH_MEAS), xytext=(21.2, TH_MEAS - 0.012),
                 fontsize=9.0, color=RED,
                 arrowprops=dict(arrowstyle="->", color=RED, lw=1.0))
axes[1].grid(alpha=.3)
save(fig, "theta_b_drift.png")

# 图 19 对准 + 对焦几何示意
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
# (a) 对准：入射角误差 Δθ 使反射光偏 2Δθ
ax = axes[0]
th = math.radians(THETA_B)
L = 4.0
d_ang = math.radians(3.0)          # 示意取 3°，则反射偏 6°，视觉可辨
ax.axhline(0, color=BLUE, lw=2.6)
ax.plot([0, 0], [-0.2, 5.7], color=GRAY, ls="--", lw=1.2)
ax.annotate("", xy=(0, 0), xytext=(-L * math.sin(th), L * math.cos(th)),
            arrowprops=dict(arrowstyle="-|>", lw=2.4, color=ORANGE, mutation_scale=15))
ax.annotate("", xy=(L * math.sin(th), L * math.cos(th)), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", lw=2.4, color=ORANGE, mutation_scale=15))
ax.annotate("", xy=(L * math.sin(th + 2 * d_ang), L * math.cos(th + 2 * d_ang)),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", lw=2.0, color=RED,
                            ls="--", mutation_scale=14))
arc = np.linspace(th, math.pi / 2, 40)
ax.plot(1.45 * np.cos(arc), 1.45 * np.sin(arc), color=GRAY, lw=1.2)
ax.text(0.92, 1.40, r"$\theta_B$", color=GRAY, fontsize=11)
arc2 = np.linspace(th, th + 2 * d_ang, 24)
ax.plot(3.05 * np.cos(arc2), 3.05 * np.sin(arc2), color=RED, lw=1.5)
ax.text(3.02 * math.cos(th + d_ang) + 0.10, 3.02 * math.sin(th + d_ang), "2Δθ",
        color=RED, fontsize=10)
ax.text(-4.05, 3.30, "入射光", color=ORANGE, fontsize=10.5)
ax.text(1.95, 2.85, "反射光（对准）", color=ORANGE, fontsize=10)
ax.text(1.55, 4.45, "反射光（失准）", color=RED, fontsize=10)
ax.text(-0.75, 5.25, "法线", color=GRAY, fontsize=10)
ax.text(-4.35, -0.68, "液面 / 单分子膜", color=BLUE, fontsize=10.5)
ax.set_xlim(-4.7, 4.7); ax.set_ylim(-1.0, 6.0); ax.set_aspect("equal")
ax.axis("off")
ax.set_title("(a) 光路对准：入射角误差 Δθ → 反射光偏 2Δθ")

# (b) 对焦：液面与焦面斜交（夹角 θB），只有交点附近落在景深内
ax = axes[1]
xx = np.linspace(-4, 4, 300)
slope = -math.tan(math.radians(TILT_DEG))
ax.plot(xx, slope * xx, color=BLUE, lw=2.6,
        label="液面（示意；与光轴夹角 %.2f°）" % TILT_DEG)
ax.axhline(0, color=ORANGE, lw=2.0, ls="--", label="物镜理想焦面")
ax.plot([-0.18, 0.18], [-0.18 * slope, 0.18 * slope], color=GREEN, lw=8, alpha=.92,
        solid_capstyle="round",
        label="清晰带（全宽约 %.1f µm，图中放大）" % FOCUS_BAND_UM)
ax.plot([0, 0], [-1.35, 1.35], color=GRAY, ls=":", lw=1.1)
ax.annotate("仅交点附近清晰", xy=(0.07, -0.05), xytext=(1.05, 1.55), fontsize=10,
            arrowprops=dict(arrowstyle="->", color=GRAY))
ax.text(-3.95, 2.35, "远离中心：离焦圆扩大、对比度下降",
        fontsize=9.0, color="#555555")
ax.set_xlim(-4.2, 4.2); ax.set_ylim(-3.6, 2.9); ax.set_aspect("equal")
ax.set_xlabel("视场内沿入射面方向 / mm（示意）"); ax.set_ylabel("轴向离焦 / mm（示意）")
ax.legend(frameon=False, fontsize=8.0, loc="lower left")
ax.set_title("(b) 图像对焦：斜视下焦面与液面只在中心相交")
save(fig, "alignment_focus.png")

print("FIGURES_OK", len([f for f in os.listdir(FIG) if f.endswith(".png")]), "张图已生成")
print("DATA_OK", DAT)
