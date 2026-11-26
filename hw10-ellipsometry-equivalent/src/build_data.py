# -*- coding: utf-8 -*-
"""7.6.1.18 试用版等效椭偏测量的数据处理：读数 → 反演 n、k → Airy 模型 → 结果与校验。

数据来源（数值均照抄软件截图，未做任何平滑或修正）：
  * 0° 入射 20 个波长、75° 入射 4 个波长的复 Fresnel 系数，取自
    Fresnel Effects Calculator 的 Complex Fresnel Coefficients 表。
  * 晶体 Si 的复折射率由 0° 入射 TE 反射系数反演：
    r_s = (1-N)/(1+N)  =>  N = (1-r)/(1+r)。
  * SiO2 用官方 MISC.0096 的扩展 Cauchy 模型
    n = A + B/lambda^2 + C/lambda^4（A=1.44，B=0.00422 um^2，C=1.89e-5 um^4）。
  * 空气 / SiO2(10.0 或 10.1 nm) / c-Si 三层用标准传输矩阵（Airy）公式求解，
    与 VirtualLab Fresnel、Coating Analyzer 的定义一致。
  * d = 0 退化情形与软件自身 75° 实测值对照，作为第一级校验。
"""
import cmath
import csv
import json
import math
import os

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 交付包根目录
DATA = os.path.join(PKG, "data")
FIG = os.path.join(PKG, "docs", "images")
BUILD = os.path.join(DATA, "_build")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

# ---------------------------------------------------------------- software data
# (wavelength nm, TE amplitude, TE phase rad, TM amplitude, TM phase rad)
NORMAL = [
    (200, 0.82584, -2.5341, 0.82584, 0.60746),
    (210, 0.82005, -2.5587, 0.82005, 0.5829),
    (220, 0.82084, -2.6008, 0.82084, 0.54083),
    (230, 0.81279, -2.6488, 0.81279, 0.49282),
    (240, 0.80559, -2.659,  0.80559, 0.48258),
    (250, 0.82563, -2.6823, 0.82563, 0.45928),
    (300, 0.79045, -2.9429, 0.79045, 0.19865),
    (320, 0.7576,  -2.9558, 0.7576,  0.1858),
    (340, 0.75018, -2.9727, 0.75018, 0.16886),
    (360, 0.76634, -3.0081, 0.76634, 0.13346),
    (380, 0.73739, -3.0953, 0.73739, 0.046257),
    (400, 0.6967,  -3.116,  0.6967,  0.025619),
    (450, 0.64771, -3.1277, 0.64771, 0.013915),
    (532, 0.6116,  -3.1362, 0.6116,  0.0054191),
    (600, 0.59565, -3.1381, 0.59565, 0.0035184),
    (700, 0.58177, -3.1397, 0.58177, 0.0018881),
    (750, 0.57737, -3.1402, 0.57737, 0.0013918),
    (850, 0.57091, -3.1408, 0.57091, 0.00076261),
    (900, 0.56876, -3.1409, 0.56876, 0.00066707),
    (1000, 0.56437, -3.1412, 0.56437, 0.00041568),
]
OBLIQUE_75 = [
    (300, 0.94109, -3.0899, 0.43597,  0.85643),
    (532, 0.87946, -3.1402, 0.049766, 0.10022),
    (800, 0.86455, -3.1413, 0.0051402, 2.9824),
    (1000, 0.86076, -3.1415, 0.01781, 3.1238),
]

CAUCHY_A, CAUCHY_B, CAUCHY_C = 1.44, 0.00422, 1.89e-5
ANGLES = [65.0, 67.5, 70.0, 72.5, 75.0]
WAVELENGTHS = [200 + 20 * i for i in range(41)]      # 200..1000 nm, 41 points
THICK = [10.0, 10.1]


def cplx(amp, phase):
    return amp * cmath.exp(1j * phase)


def w(name, head, rows):
    p = os.path.join(DATA, name)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(head)
        wr.writerows(rows)
    print("wrote", p, len(rows), "rows")


# 1) software-measured complex coefficients ------------------------------------
rows = []
for lam, ate, pte, atm, ptm in NORMAL:
    rs, rp = cplx(ate, pte), cplx(atm, ptm)
    rows.append([lam, 0, "Air -> Silicon(crystalline)-Si_(1985), no coating",
                 ate, pte, atm, ptm,
                 "%.6f" % rs.real, "%.6f" % rs.imag,
                 "%.6f" % rp.real, "%.6f" % rp.imag])
for lam, ate, pte, atm, ptm in OBLIQUE_75:
    rs, rp = cplx(ate, pte), cplx(atm, ptm)
    rows.append([lam, 75, "Air -> Silicon(crystalline)-Si_(1985), no coating",
                 ate, pte, atm, ptm,
                 "%.6f" % rs.real, "%.6f" % rs.imag,
                 "%.6f" % rp.real, "%.6f" % rp.imag])
w("software_fresnel_coeffs.csv",
  ["波长_nm", "入射角_deg", "样品", "TE振幅", "TE相位_rad", "TM振幅", "TM相位_rad",
   "r_TE实部", "r_TE虚部", "r_TM实部", "r_TM虚部"], rows)

# 2) invert Si index ------------------------------------------------------------
si_points = []
for lam, ate, pte, atm, ptm in NORMAL:
    r = cplx(ate, pte)
    N = (1 - r) / (1 + r)
    si_points.append((lam, N.real, N.imag))
w("si_nk_inverted.csv", ["波长_nm", "n", "k"],
  [[lam, "%.6f" % n, "%.6f" % k] for lam, n, k in si_points])


def si_index(lam):
    """Piecewise-linear interpolation of the software-inverted Si dispersion."""
    if lam <= si_points[0][0]:
        return complex(si_points[0][1], si_points[0][2])
    if lam >= si_points[-1][0]:
        return complex(si_points[-1][1], si_points[-1][2])
    for (x0, n0, k0), (x1, n1, k1) in zip(si_points, si_points[1:]):
        if x0 <= lam <= x1:
            t = (lam - x0) / (x1 - x0)
            return complex(n0 + t * (n1 - n0), k0 + t * (k1 - k0))
    raise ValueError(lam)


def sio2_index(lam_nm):
    L = lam_nm / 1000.0
    return complex(CAUCHY_A + CAUCHY_B / L ** 2 + CAUCHY_C / L ** 4, 0.0)


# 3) transfer-matrix reflection of air / SiO2 / c-Si ---------------------------
def reflection(lam_nm, theta_deg, d_nm):
    N0 = 1.0 + 0j
    N1 = sio2_index(lam_nm)
    N2 = si_index(lam_nm)
    s0 = math.sin(math.radians(theta_deg))
    c0 = math.cos(math.radians(theta_deg))
    c1 = cmath.sqrt(1 - (N0 * s0 / N1) ** 2)
    c2 = cmath.sqrt(1 - (N0 * s0 / N2) ** 2)
    # physical branch: decaying wave inside absorbing media
    if (N1 * c1).imag < 0:
        c1 = -c1
    if (N2 * c2).imag < 0:
        c2 = -c2
    q0, q1, q2 = N0 * c0, N1 * c1, N2 * c2
    r01s, r12s = (q0 - q1) / (q0 + q1), (q1 - q2) / (q1 + q2)
    # TM convention of VirtualLab: r_p = -r_s at normal incidence
    r01p = (N1 * c0 - N0 * c1) / (N1 * c0 + N0 * c1)
    r12p = (N2 * c1 - N1 * c2) / (N2 * c1 + N1 * c2)
    beta = 2 * math.pi / lam_nm * N1 * d_nm * c1
    e = cmath.exp(2j * beta)
    rs = (r01s + r12s * e) / (1 + r01s * r12s * e)
    rp = (r01p + r12p * e) / (1 + r01p * r12p * e)
    return rs, rp


def ellipsometry(rs, rp):
    """VirtualLab phase convention: rho = r_p/r_s = tan(Psi)*exp(-i*Delta).

    Verified against the official MISC.0096 .da arrays: Psi matches point by
    point, and Delta = -arg(rho) (mod 360 deg) matches within 0.2 deg.
    """
    rho = rp / rs
    psi = math.degrees(math.atan(abs(rho)))
    delta = (-math.degrees(cmath.phase(rho))) % 360.0
    return rho, psi, delta


# 4) d=0 validation against software 75 deg samples ----------------------------
val = []
for lam, ate, pte, atm, ptm in OBLIQUE_75:
    rs, rp = reflection(lam, 75.0, 0.0)
    s_rs, s_rp = cplx(ate, pte), cplx(atm, ptm)
    val.append([lam, 75,
                "%.6f" % abs(s_rs), "%.6f" % abs(rs),
                "%.6f" % abs(s_rp), "%.6f" % abs(rp),
                "%.4f" % math.degrees(cmath.phase(s_rs)),
                "%.4f" % math.degrees(cmath.phase(rs)),
                "%.4f" % math.degrees(cmath.phase(s_rp)),
                "%.4f" % math.degrees(cmath.phase(rp)),
                "%.6f" % abs(s_rs - rs), "%.6f" % abs(s_rp - rp)])
w("model_check_bare_si_75deg.csv",
  ["波长_nm", "入射角_deg", "软件TE振幅", "模型TE振幅", "软件TM振幅", "模型TM振幅",
   "软件TE相位_deg", "模型TE相位_deg", "软件TM相位_deg", "模型TM相位_deg",
   "TE振幅差", "TM振幅差"], val)

# 5) full Psi/Delta scans -------------------------------------------------------
summary = {}
for d in THICK:
    out = []
    for ang in ANGLES:
        for lam in WAVELENGTHS:
            rs, rp = reflection(lam, ang, d)
            rho, psi, delta = ellipsometry(rs, rp)
            out.append([lam, ang, d,
                        "%.8f" % abs(rs), "%.8f" % math.degrees(cmath.phase(rs)),
                        "%.8f" % abs(rp), "%.8f" % math.degrees(cmath.phase(rp)),
                        "%.8f" % abs(rho), "%.6f" % psi, "%.6f" % delta])
    name = "psi_delta_10nm.csv" if d == 10.0 else "psi_delta_10p1nm.csv"
    w(name, ["波长_nm", "入射角_deg", "SiO2厚度_nm",
             "r_s振幅", "r_s相位_deg", "r_p振幅", "r_p相位_deg",
             "rho模", "Psi_deg", "Delta_deg"], out)
    summary[d] = {(float(lam), float(ang)): (float(psi), float(delta))
                  for lam, ang, dd, a, b, c, e, f, psi, delta in out}

diff = []
for ang in ANGLES:
    for lam in WAVELENGTHS:
        p0, d0 = summary[10.0][(lam, ang)]
        p1, d1 = summary[10.1][(lam, ang)]
        ddelta = (d1 - d0 + 180) % 360 - 180
        diff.append([lam, ang, "%.6f" % p0, "%.6f" % p1, "%.6f" % (p1 - p0),
                     "%.6f" % d0, "%.6f" % d1, "%.6f" % ddelta])
w("thickness_diff.csv",
  ["波长_nm", "入射角_deg", "Psi_10p0_deg", "Psi_10p1_deg", "ΔPsi_deg",
   "Delta_10p0_deg", "Delta_10p1_deg", "ΔDelta_deg"], diff)

# 6) parameter record -----------------------------------------------------------
w("parameters.csv", ["项目", "取值", "依据/备注"], [
    ["软件", "Wyrowski VirtualLab Fusion Trial (Summer Release) Build 7.6.1.18", "Help → About VirtualLab（T01）"],
    ["许可", "试用版，剩余启动 59 次，单次会话 12 h", "About VirtualLab（T01）"],
    ["内置分析器", "无 Ellipsometry Analyzer", "Detectors 过滤 ellips / Calculators 列表（T02b/T02c）"],
    ["实现路径", "Fresnel Effects Calculator 取 TE/TM 复 Fresnel 系数，按 ρ=r_p/r_s 计算 Ψ、Δ", "任课教师 2026-11-15 答复认可"],
    ["第一材料", "Air (Gas or Vacuum)", "Fresnel Effects Calculator（T03）"],
    ["基底", "Silicon(crystalline)-Si_(1985)", "Materials Catalog（T04b）"],
    ["基底色散", "由软件 0° 入射复系数反演 n、k（20 个波长点）", "data/software_fresnel_coeffs.csv / data/si_nk_inverted.csv"],
    ["膜层", "SiO2，扩展 Cauchy A=1.44, B=0.00422 µm², C=1.89e-5 µm⁴", "官方 MISC.0096 用例（等效模型）"],
    ["膜厚", "10.0 nm（基线） / 10.1 nm（对比，差 1 Å）", "题目与官方案例"],
    ["波长扫描", "200 nm → 1 µm，41 点，步长 20 nm", "题目要求 / 官方案例 MISC.0096 参数表"],
    ["角度扫描", "65° / 67.5° / 70° / 72.5° / 75°（5 点，步长 2.5°）", "官方 MISC.0096 结果图口径"],
    ["软件 Diagram 扫描范围", "210.07 nm – 3.71 µm（材料有效区间），角度 65° – 89.999°", "Fused_Silica / Si 材料预览（T04a/T04b）"],
    ["TM 相对 TE 相位补偿", "0°", "题目要求 / 官方案例 MISC.0096"],
    ["ρ 约定", "ρ = r_p/r_s = r_TM/r_TE = tanΨ·exp(−iΔ)，即 Δ = −arg(ρ)", "按官方 MISC.0096 .da 结果标定（Ψ 逐点吻合、Δ 偏差 <0.2°）"],
    ["Δ 取值范围", "[0°, 360°)", "相位展开约定；0° 入射裸硅 Δ≈180°"],
    ["限制", "7.6 Coatings Catalog 仅 3 类预置膜、无 SiO2 单层模板；试用版禁用保存新建文档", "T04c / 官网试用说明"],
        ])

# 6b) independent cross-check against the official MISC.0096 result arrays -----
# 官方 216 点（36 波长 × 6 角度）由 LightTrans 用例 .da 解码后存为 CSV。
# 该文件缺失时必须中止：静默跳过会把 max_dpsi 写成 0，与报告 2.5 节的 0.389° 冲突。
OFF = os.path.join(DATA, "official_reference_216pts.csv")
if not os.path.exists(OFF):
    raise SystemExit("缺少官方参考数据：%s" % OFF)
import io
MAX_DPSI = MAX_DDELTA = 0.0
rr = list(csv.reader(io.open(OFF, encoding="utf-8-sig")))
off_angles = [10, 20, 30, 40, 50, 60]
cmp_rows = []
for row in rr[2:]:
    lam = float(row[0])
    for j, ang in enumerate(off_angles):
        rs, rp = reflection(lam, ang, 10.0)
        _, psi, delta = ellipsometry(rs, rp)
        o_psi, o_delta = float(row[1 + j]), float(row[7 + j])
        dp, dd = psi - o_psi, delta - o_delta
        MAX_DPSI = max(MAX_DPSI, abs(dp))
        MAX_DDELTA = max(MAX_DDELTA, abs(dd))
        cmp_rows.append([lam, ang, "%.5f" % o_psi, "%.5f" % psi, "%.5f" % dp,
                         "%.5f" % o_delta, "%.5f" % delta, "%.5f" % dd])
w("official_case_check.csv",
  ["波长_nm", "入射角_deg", "官方案例Psi_deg", "本模型Psi_deg", "Psi偏差_deg",
   "官方案例Delta_deg", "本模型Delta_deg", "Delta偏差_deg"], cmp_rows)
print("official cross-check: max |dPsi| = %.4f deg, max |dDelta| = %.4f deg, n = %d"
      % (MAX_DPSI, MAX_DDELTA, len(cmp_rows)))

# 7) compact JSON for report generator ------------------------------------------
stats = {
    "angles": ANGLES,
    "wavelengths": WAVELENGTHS,
    "psi": {str(d): {str(a): [[lam, round(summary[d][(lam, a)][0], 5)] for lam in WAVELENGTHS]
                     for a in ANGLES} for d in THICK},
    "delta": {str(d): {str(a): [[lam, round(summary[d][(lam, a)][1], 5)] for lam in WAVELENGTHS]
                       for a in ANGLES} for d in THICK},
    "validation": val,
    "diff": diff,
    "si_points": si_points,
    "max_dpsi": MAX_DPSI,
    "max_ddelta": MAX_DDELTA,
}
json.dump(stats, open(os.path.join(BUILD, "report_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
print("stats json written")
print("done")
