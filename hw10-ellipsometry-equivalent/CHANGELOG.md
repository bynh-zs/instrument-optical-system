# Changelog

## 2026-11-26

初始化。

- `src/build_data.py`：课程「仿真源文件/build_data.py」整理为仓库版——数据、图、截图目录改为 `data/`、`docs/images/`、`docs/screenshots/`，9 份 CSV 与结果图文件名英文化，参数台账删去学号姓名两行，官方 216 点参考缺失时中止而非静默跳过。
- `src/draw_results.py`：绘图脚本整理为仓库版——输出落到 `docs/images/`，图名英文化，只用 Pillow。
- `tools/capture.py`：界面截图采集脚本（置顶窗口 + 矩形裁剪），与 `docs/screenshots/` 的 17 张对应。
- `docs/principle.md`：ρ = r_p/r_s = tanΨ·e^{−iΔ} 的符号约定、三层 Airy、Si 的 n,k 反演、1 Å 灵敏度、两级校验。
- `docs/software-limits.md`：7.6.1.18 无 Ellipsometry Analyzer 的三条界面证据与手册检索结果、任课教师认可的口径、B′ 路径的边界。
- `docs/data-notes.md`：9 份 CSV 的来源与行数、读数取法、两级校验（0.389° / 0.197°）、重跑命令。
- `docs/references-check.md`：四条网络文献的链接核验记录（原文来自作业过程，仅做路径与措辞整理）。
- `data/`：9 份 CSV（软件读数、反演 n,k、Ψ/Δ、厚度差、参数台账、官方 216 点与对照）。
- `docs/images/`：8 张结果图 + 九宫格总览；`docs/screenshots/`：17 张界面凭证。
- `scripts/sync.ps1`：从本地作业目录同步截图与数据，并重跑 `build_data.py`。

不入库：课程报告 docx/pdf、57 MB 录屏、含学号的 `build_final_report.py`、`数据/_build/` 中间产物。
