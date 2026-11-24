# -*- coding: utf-8 -*-
"""按指定相机渲染 .blend 的若干帧，用于批量出图。

用法：
    blender -b scene.blend --python tools/render_camera.py -- \
        --scene 02_沟槽互反射 --cam T4_相机_12mm --frames 48 --samples 128 \
        --res 1600x1200 --out out/render/reflection.png

参数说明：
    --scene   场景名（不填则用当前场景）
    --cam     相机对象名（不填则用场景已有相机）
    --frames  逗号分隔的帧号，或 "1-96" 区间
    --out     输出路径；多帧时按 _f{帧号} 自动加后缀
"""
import argparse
import os
import sys
import time

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default=None)
    ap.add_argument("--cam", default=None)
    ap.add_argument("--frames", default="48")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--res", default="1600x1200")
    ap.add_argument("--out", required=True)
    return ap.parse_args(argv)


def parse_frames(s):
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(v) for v in s.split(",") if v.strip()]


def main():
    a = parse_args()
    sc = bpy.data.scenes[a.scene] if a.scene else bpy.context.scene
    if a.cam:
        sc.camera = bpy.data.objects[a.cam]
    rx, ry = (int(v) for v in a.res.lower().split("x"))
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = 100
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"

    frames = parse_frames(a.frames)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        path = a.out if len(frames) == 1 else a.out.replace(".png", f"_f{f}.png")
        sc.render.filepath = path
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print("OK", path, "%.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
