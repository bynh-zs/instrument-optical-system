# Changelog

## 2026-11-26

初始化。

- `src/bam_build_scene.py`：课程作业里的 Blender 建模脚本整理为仓库版——输出路径改为仓库相对（`assets/`、`docs/images/`），去掉个人信息键，中文字体按平台回退并打包，内嵌脚本改为嵌入自身。
- `src/bam_model.py`：单层膜特征矩阵反射率、对比度/消光比判据、分辨率链、对准对焦、十因素扫描整理为 CLI（`--figdir/--datadir`），输出文件名英文化，字体跨平台。
- `src/make_film_figure.py`：三层膜模型示意图独立成脚本。
- `tools/blender_audit.py`：56 项只读自检，报告默认写 `docs/verification.md`（可用 `-- --report` 覆盖），改为与 `src/bam_build_scene.py` 比对。
- `docs/`：需求与约束、系统设计、物理模型、因素与误差传递、仿真约定、核实台账；自检报告由脚本生成。
- `assets/bam_optical_path.blend`：按清洗后脚本重建（119 对象、6 集合、字体已打包、56/56 PASS）。
- `data/`：4 份扫描 CSV + 结果摘要（中英各一份）。
- `scripts/sync.ps1`：从本地作业目录同步最新成果并提交。
