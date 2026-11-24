# -*- coding: utf-8 -*-
"""Blender 场景参数审计：把 .blend 的关键参数打印成一份可核对的清单。

用法（命令行、无界面）：
    blender -b scene.blend --python tools/blender_audit.py

输出：每个场景的对象数、帧率与帧范围、分辨率、引擎与采样、相机（名称/倾角/焦距/靶面）、
      灯光数量与逐条线光源参数、材质数量、以及光片类对象是否参与渲染。
"""
import math

import bpy


def main():
    print("=" * 72)
    print("Blender", bpy.app.version_string, "| 场景数", len(bpy.data.scenes), "| 材质数", len(bpy.data.materials))
    for sc in bpy.data.scenes:
        r, c = sc.render, sc.cycles
        print("-" * 72)
        print(f"[场景] {sc.name}  对象 {len(sc.objects)}  帧 {sc.frame_start}-{sc.frame_end} @ {r.fps} fps")
        print(f"       分辨率 {r.resolution_x}x{r.resolution_y} ({r.resolution_percentage}%)  引擎 {r.engine}  采样 {c.samples}  降噪 {c.use_denoising}")
        vs = sc.view_settings
        print(f"       色彩管理 {vs.view_transform} / Look {vs.look} / 曝光 {vs.exposure} / Gamma {vs.gamma}")
        cams = [o for o in sc.objects if o.type == "CAMERA"]
        for o in cams:
            print(f"       [相机] {o.name}  位置 {tuple(round(v, 3) for v in o.location)}  "
                  f"绕Y {math.degrees(o.rotation_euler[1]):.2f}°  焦距 {o.data.lens:g} mm  靶面 {o.data.sensor_width:g} mm "
                  f"适配 {o.data.sensor_fit}")
        lights = [o for o in sc.objects if o.type == "LIGHT"]
        print(f"       [灯光] 共 {len(lights)} 盏")
        for o in lights:
            d = o.data
            extra = ""
            if d.type == "AREA":
                extra = f" shape={d.shape} size={d.size:g}/{getattr(d, 'size_y', 0):g} spread={d.spread:.5f}"
            print(f"           {o.name:<18} {d.type:<6} energy={d.energy:g}{extra}")
        plates = [o for o in sc.objects if o.name.startswith("光片")]
        if plates:
            print(f"       [光片] {len(plates)} 个，hide_render="
                  f"{sorted({o.hide_render for o in plates})}（True 表示只用于视口展示、不参与渲染）")


if __name__ == "__main__":
    main()
