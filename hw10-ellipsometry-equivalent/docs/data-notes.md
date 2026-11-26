# 数据来源与复现

## 一、目录内容

| 文件 | 行数 | 来源与含义 |
|---|---|---|
| `software_fresnel_coeffs.csv` | 24 | 从 Fresnel Effects Calculator 的 Tables 抄下的 TE/TM 复 Fresnel 系数：0° 入射 20 个波长点（200/210/220/230/240/250/300/320/…/1000 nm 等），75° 入射 4 点（300/532/800/1000 nm）。振幅、相位（rad）与由此换算的实部、虚部都保留，便于互相校验。 |
| `si_nk_inverted.csv` | 20 | 由上一行 0° 读数按 $N=(1-r_s)/(1+r_s)$ 反演的晶体 Si 复折射率，`n − i k`。 |
| `model_check_bare_si_75deg.csv` | 4 | 第一级校验：d = 0（裸硅）时模型与软件 75° 实测的振幅、相位对照，附差列。 |
| `psi_delta_10nm.csv` | 205 | 主结果：SiO₂ 10.0 nm，41 波长 × 5 角度（65/67.5/70/72.5/75°）= 205 组。列含 $r_s$、$r_p$ 的振幅与相位、$\|\rho\|$、Ψ、Δ。 |
| `psi_delta_10p1nm.csv` | 205 | 同上，膜厚 10.1 nm。 |
| `thickness_diff.csv` | 205 | 两个膜厚的逐点差：ΔΨ、ΔΔ（角度按 360° 周期回绕到 ±180°）。 |
| `parameters.csv` | 16 | 模型口径台账：软件版本、材料、膜层 Cauchy 系数、波长/角度扫描、ρ 约定、Δ 范围、限制。**已删除学号、姓名两行。** |
| `official_case_check.csv` | 216 | 第二级校验：官方 MISC.0096 的 Ψ、Δ 与本模型逐点对照（36 波长 × 6 角度），含两个偏差列。 |
| `official_reference_216pts.csv` | 36（+2 行注释） | **官方原始数组**：由 LightTrans MISC.0096 的 `.da` 解码而来，13 列 = 波长 + 10°–60° 的 Ψ + 10°–60° 的 Δ。前两行是说明行，`build_data.py` 从第 3 行起读。 |

## 二、读数的取法

Fresnel Effects Calculator 的 Tables 视图一次显示一个入射角下的整条波长序列，所以：

- **0° 入射**：一次扫描拿到 20 个波长点的 TE、TM 复系数（此时两偏振读数相同，取 TE 反演基底最干净）。
- **75° 入射**：再扫 4 个波长点，用于第一级退化校验。
- 没有逐点手抄 41 个波长 × 5 个角度——**Ψ、Δ 全部由本地模型算出**，软件只提供基底色散与退化校验的锚点。这是等效路径的性质，也是它的局限。

## 三、两级校验的可复现性

```bash
python src/build_data.py
# official cross-check: max |dPsi| = 0.3893 deg, max |dDelta| = 0.1969 deg, n = 216
```

- 第二级校验读 `data/official_reference_216pts.csv`，**文件缺失会直接中止**（不静默跳过），避免把 `max_dpsi` 写成 0 而与文档里的 0.389° 冲突。
- 第一级校验的振幅差最大值 `0.000657`（800 nm，TM），即 6.6×10⁻⁴；其余三点都在 1×10⁻⁴ 量级以下。
- Δ 的周期比较统一用 `(a − b + 180) % 360 − 180`，避免 0/360 跨界伪差。

## 四、1 Å 灵敏度

`thickness_diff.csv` 的 ΔΨ 落在 0.030°–0.063°，ΔΔ 落在 −0.341°–0.151°（负值出现在短波、Δ 随膜厚减小而下移的区间）。这类量级说明：要分辨 1 Å，Ψ、Δ 的读数不确定度必须优于 0.03°/0.15°，单个角度单波长的测量不够，必须多角度多波长联合拟合——这正是专用椭偏仪（以及 2023.1 之后的 Ellipsometry Analyzer）做的事。

## 五、绘图

```bash
python src/draw_results.py
```

只用 Pillow 手绘（不依赖 matplotlib），输出到 `docs/images/`：`principle_structure.png`、`workflow.png`、`psi_vs_lambda.png`、`delta_vs_lambda.png`、`sensitivity_psi.png`、`sensitivity_delta.png`、`si_nk.png`、`official_case_compare.png`、`sheet.png`（九宫格总览）。

## 六、截图

`docs/screenshots/` 的 17 张（T01–T10c）是同一次会话按序采集的界面凭证，文件名与内容的对应见原始素材目录的截图说明；`tools/capture.py` 只负责「置顶窗口 + 按矩形裁剪 + 存盘」，不改变界面状态。重采需重新启动会话（试用版每次启动消耗次数，且会话 12 h 上限）。
