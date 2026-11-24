# Changelog

## 2026-11-24

初始化仓库。

- `src/line_center_extract.py`：把课程作业里的光条提取脚本整理为可复用 CLI（`--input / --outdir / --lines / --pitch-mm`），路径改为仓库相对，字体做了跨平台回退；在同目录运行即可复现 7/7 检出、剔除 2 个副峰、1.2926 mm/px、射影残差 1.11 px。
- `tools/blender_audit.py`：一次打印全部场景、相机、灯光、光片可见性等关键参数，用来核对 `.blend` 与文档是否一致。
- `tools/render_camera.py`：按场景/相机/帧/分辨率批量渲染，避免每次手改输出面板。
- `docs/`：系统设计（几何与指标）、仿真说明（Cycles 设置与六个坑）、算法说明（射影先验推导与结果）。
- `assets/multi_line_scene.blend`、`data/groove_render.png`：仿真场景与测试图像。
- `scripts/sync.ps1`：从本地作业目录同步最新算法、场景与图像并提交。
