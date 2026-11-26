# 界面截图说明（17 张）

## 一、性质

1. 17 张 PNG 全部来自**同一次** VirtualLab Fusion 7.6.1.18 试用版会话（2026-11-15 13:45 启动），由 `tools/capture.py` 抓取全屏后按固定矩形裁剪，**未人工补拍、未修改界面文字、未拼接合成**。
2. 「T序号」命名让采集脚本与文档图号解耦：本文档插图取其中 9 张，其余用于佐证核查过程与数据落地。
3. T08、T09、T10 是把交付的 CSV 用文本编辑器真实打开后的屏幕画面，只裁掉了顶部编辑器标签栏（该处显示与本作业无关的其他文件名），数据区一字未改。
4. 试用版禁用保存新建文档，不存在 `File > Export` 对话框，因此没有导出界面截图，也没有虚构该画面。

## 二、逐张

| 编号 | 内容 | 本文档用途 |
|---|---|---|
| T01 | Help → About VirtualLab：Version 7.6.1.18 (Trial)、剩余启动 59 次、会话 12 h | 版本凭证（`software-limits.md` 证据 1） |
| T02 | Catalogs 的九个目录（Boundary Responses / Coatings / Components / Detectors / Interfaces / Light Sources / Materials / Media / Stacks） | 目录结构 |
| T02b | Detectors 以 `ellips` 过滤后仅剩 `Phase View (with Polarization Ellipses)` | 无椭偏分析器（证据 2） |
| T02c | Start → Calculators 的 11 个计算器（含 Fresnel Effects Calculator，无椭偏专用项） | 无椭偏分析器（证据 3） |
| T03 | Fresnel Effects Calculator 初始界面（Air / Fused_Silica / No Coating）与 TE、TM 复系数表 | 工具入口 |
| T04a | Materials Catalog 的 Fused_Silica 预览：有效 210.07 nm – 3.71 µm | 材料区间 |
| T04b | Materials Catalog 选中 Silicon(crystalline)-Si_(1985)：有效 619.9 pm – 333.28 µm | 基底选择 |
| T04c | Coatings Catalog 仅 Optics Balzers / Standard-AR / Standard-HR 三类，无 SiO₂ 单层模板 | 限制 |
| T05 | 532 nm / 75° 实测复系数：TE 0.87946·exp(−3.1402 rad·i)、TM 0.049766·exp(0.10022 rad·i)，R = 0.77344 / 0.0024767 | 读数样本 |
| T06 | 75° 入射 TE/TM 相位–波长扫描（Diagram，Abscissa = Wavelength） | 相位色散 |
| T06b | 同上条件下的振幅–波长扫描 | 振幅色散 |
| T07 | 532 nm、65°–89.999° 的振幅–角度扫描，TM 极小约 76° | 工作角选择依据 |
| T08 | 文本编辑器打开 `data/software_fresnel_coeffs.csv`：表头 + 24 行（0° 20 点、75° 4 点） | 读数落地 |
| T09 | 打开 `data/psi_delta_10p1nm.csv`：10.1 nm 的 Ψ、Δ 与 ΔΨ、ΔΔ 逐行结果 | 结果落地 |
| T10 | 打开 `data/parameters.csv`：项目 / 取值 / 依据备注 | 口径落地 |
| T10b | 主界面与 VirtualLab Explorer：Fresnel Effects Calculator（900 nm、0°）仍打开 | 会话连续性 |
| T10c | 532 nm / 75° 读数与 Messages 面板同屏：13:45:22 启动期 NullReferenceException、13:54:56 基底材料设定记录 | 说明该异常早于全部读数、与结果无关 |

## 三、与插图的关系

`docs/images/` 的 9 张是自绘图（`principle_structure.png`、`workflow.png`、`si_nk.png`、`official_case_compare.png`、`psi_vs_lambda.png`、`delta_vs_lambda.png`、`sensitivity_psi.png`、`sensitivity_delta.png`、`sheet.png`），由 `src/draw_results.py` 用 Pillow 绘制，数据全部来自 `data/` 下的 CSV；本目录的截图只作界面凭证，不参与绘图。
