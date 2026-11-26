# 仪器光学设计 · 课程产出仓库

天津大学精密仪器与光电子工程学院《仪器光学设计》课程各次作业中**可复用**的产出（算法、仿真场景、脚本、参数与说明），按作业编号组织。

| 目录 | 作业 | 内容 | 状态 |
|---|---|---|---|
| [`hw1-brewster-angle-microscope/`](hw1-brewster-angle-microscope/) | 作业 1 · 布儒斯特角显微镜 | Blender 整机光机场景（119 对象、56 项自检全过）；单层膜特征矩阵反射率模型与十因素误差传递（ER ≥ 6.96×10⁴ 判据、清晰带 4.4 µm） | 已完成 |
| [`hw4-multi-line-structured-light/`](hw4-multi-line-structured-light/) | 作业 4 · 多线结构光测量系统 | Blender/Cycles 三材质成像与沟槽互反射仿真；光条中心提取算法 v2（7/7 检出、射影残差 1.11 px） | 已完成 |
| [`hw5-mv-inspection-survey/`](hw5-mv-inspection-survey/) | 作业 5 · 机器视觉检测系统调研 | 以大视场条纹投影系统（CN110793464B）为例写光源布局、相机选型公式与七步开发流程；FPP / PMD / 光度立体的链路、边界与按表面属性分层的选型决策；31 条文献 | 已完成 |
| [`hw10-ellipsometry-equivalent/`](hw10-ellipsometry-equivalent/) | 作业 10 · 椭圆偏振测量的等效实现 | 用 Fresnel Effects Calculator 取复系数按 ρ = r_p/r_s 实现椭偏测量：反演 Si 的 n、k，Airy 三层算 Ψ/Δ，与官方 216 点对照 max\|ΔΨ\| = 0.389°、max\|ΔΔ\| = 0.197°；试用版无 Ellipsometry Analyzer 的界面与手册证据 | 已完成 |

## 组织约定

- 一份作业一个顶层目录，命名 `hwN-主题`，平铺，不互相嵌套；每份作业自带 `README.md` 说明目标、成果与复现命令。
- 只收可复用内容；课程报告正文、录屏脚本、含学号的提交包不入库。
- 每份作业内部统一为 `src/`（代码）、`tools/`（辅助脚本）、`docs/`（设计说明与图）、`assets/`（场景等大文件）、`data/`（测试数据）、`scripts/`（维护脚本）。
- 新增作业时先在本表补一行，再在 `CHANGELOG.md` 记一次变更。

## 许可

仓库内容用于学习交流，引用请注明出处；`.blend` 与图像不含第三方资产。
