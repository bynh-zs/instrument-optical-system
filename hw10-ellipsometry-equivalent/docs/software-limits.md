# 试用版限制与「等效实现」路径

## 一、事实

题目配图指向 VirtualLab 的 **Ellipsometry Analyzer**。本机安装的是 **Wyrowski VirtualLab Fusion Trial 7.6.1.18**（Summer Release），其中**没有**这个分析器——该功能在 **2023.1（Build 1.556）** 才加入。

这不是推断，有三条界面级证据（截图在 `docs/screenshots/`）：

1. **版本**：Help → About 显示 `7.6.1.18 (Trial)`（`T01.png`）。
2. **Detectors 目录过滤为空**：Catalogs → Detectors 中输入 `ellips`，只剩 `Phase View (with Polarization Ellipses)`（`T02b.png`），没有任何椭偏分析器条目。
3. **Calculators 列表无该项**：Start → Calculators 共 11 个计算器，含 `Fresnel Effects Calculator`，无椭偏专用项（`T02c.png`）。

另有两条辅助证据：

- 安装手册（889 页）全文检索：`ellipsometry` 与 `Ellipsometry Analyzer` 均 **0 命中**；`Fresnel Effects Calculator` 命中 8 次（页 18、724、729–731、880）。
- 试用版**禁用保存新建文档**（LightTrans 试用说明原文 "Saving functionality of created documents … is disabled."），所以本作业不提供 `.os` 工程文件，也不虚构导出界面截图。

## 二、为什么走「等效实现」

任课教师 2026-11-15 答复：**试用版没有这个器件的话，实现这个功能也行，不一定非得说这个分析器**。

据此把路径从 A（2023.1+ 专用分析器、保存 .os、全程录屏）改为 **B′：用内置 Fresnel Effects Calculator 实现椭偏测量功能**：

1. 打开 `Fresnel Effects Calculator`，第一材料 Air，第二材料 `Silicon(crystalline)-Si_(1985)`，Coating 保持 No Coating。
2. 在 Tables 里设波长与入射角，读 TE、TM 的**复 Fresnel 系数**（振幅 + 相位）。
3. 按 $\rho=r_p/r_s=\tan\Psi e^{-\mathrm{i}\Delta}$ 换算 Ψ、Δ。
4. 0° 入射 20 个波长点反演 Si 的 n、k；75° 入射 4 点做退化校验。
5. 用 Airy 三层模型算 SiO₂ 10.0 / 10.1 nm 的 Ψ、Δ，并与官方 216 点对照。

## 三、边界

- 这条路径**不提供** Ψ/Δ 的多角度多波长拟合，也**不提供**膜厚反演；膜厚是模型输入（10.0 / 10.1 nm），不是拟合输出。
- 它证明的是「软件给出的复 Fresnel 系数与三层模型、官方案例自洽」，不是「本机是一台椭偏仪」。
- 报告与文档中所有涉及 `.os` 的地方都按「试用版不可保存」处理，没有虚构工程文件。

## 四、环境事实（复现时需知道）

| 项 | 值 |
|---|---|
| 安装目录 | `C:\Program Files\Wyrowski Photonics\VirtualLab Fusion (7.5.0) Trial`（目录名沿用安装包版本，实际程序 7.6.1.18） |
| 材料库 | Fused_Silica 有效区间 210.07 nm–3.71 µm；Si_(1985) 619.9 pm–333.28 µm |
| Coatings Catalog | 仅 Optics Balzers / Standard-AR / Standard-HR 三类预置，无 SiO₂ 单层模板 |
| Diagram 扫描 | 波长 193.08–971.31 nm（横轴 0.2–0.9 µm）；角度 65°–89.999°；TM 极小约 76°，与工作角 75° 的选择一致 |
