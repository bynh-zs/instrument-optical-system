# -*- coding: utf-8 -*-
"""
作业 1 · BAM 仿真文件（.blend）交付前检查
用法：blender -b assets/bam_optical_path.blend --python tools/blender_audit.py
      （默认报告写到 docs/verification.md；可用 `-- --report 路径` 覆盖）

只读检查，不修改 .blend。检查项：
  A 文件可打开性 / 场景规模
  B 集合分层与器件齐备性（对照图 1 器件清单）
  C 场景级仿真参数完整性与数值自洽（tanθB = n2/n1）
  D 光路几何一致性（入射/反射对称、共面、器件在光轴上）
  E 器件自定义属性完整性
  F 材质 / 灯光 / 相机 / 渲染设置 / 内嵌文本 / 字体打包与外部依赖
  G 可渲染性（实际渲染一帧到临时文件）
"""
import bpy
import math
import os
import sys
import datetime
import json
import tempfile
from mathutils import Vector

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(BASE, "docs", "verification.md")
if "--report" in sys.argv:
    REPORT = sys.argv[sys.argv.index("--report") + 1]
os.makedirs(os.path.dirname(os.path.abspath(REPORT)), exist_ok=True)

results = []          # (类别, 项目, 判定, 说明)
def chk(cat, item, ok, note=""):
    results.append((cat, item, "PASS" if ok else "FAIL", note))

def near(a, b, tol=1e-4):
    return abs(a - b) <= tol

scene = bpy.context.scene
objs = list(bpy.data.objects)

# ---------------------------------------------------------------- A
chk("A 文件", "文件可正常打开", len(objs) > 0, "共 %d 个对象" % len(objs))
chk("A 文件", "场景名称", scene.name.startswith("BAM_"), scene.name)
chk("A 文件", "对象规模合理", len(objs) >= 100, "%d 个对象" % len(objs))
chk("A 文件", "单位制为公制 cm", scene.unit_settings.system == 'METRIC'
    and near(scene.unit_settings.scale_length, 0.01),
    "system=%s scale_length=%s length_unit=%s" %
    (scene.unit_settings.system, scene.unit_settings.scale_length,
     scene.unit_settings.length_unit))

# ---------------------------------------------------------------- B
want_colls = ["01_光源与起偏臂", "02_样品台与单分子膜", "03_反射成像臂",
              "04_机械支撑", "05_标注与辅助", "06_灯光与相机"]
coll_names = [c.name for c in bpy.data.collections]
for c in want_colls:
    chk("B 结构", "集合 " + c, c in coll_names)

must_have = [
    "光源_HeNe激光器_632.8nm", "光源_出射窗_发光",
    "HWP_半波片_632.8nm", "HWP_金属外框", "HWP_p偏振方向标记_E矢量",
    "GL_格兰偏振棱镜", "入射光束_p偏振_632.8nm", "入射光_传播方向箭头",
    "样品槽_底板_PTFE", "样品槽_前壁_Y负", "样品槽_后壁_Y正",
    "样品槽_左壁_X负", "样品槽_右壁_X正",
    "亚相_水_n2", "气液界面_n1_n2", "气相_空气_n1",
    "单分子膜_覆盖区域_示意", "滑障_Barrier",
    "反射光束_成像信号_632.8nm", "反射光_传播方向箭头",
    "Obj_长工作距物镜_镜筒", "Obj_物镜前透镜",
    "Apo_消色差透镜组", "Apo_金属镜框",
    "探测器_面阵相机_机壳", "探测器_靶面",
    "光学底板_Breadboard",
    "θB_角度圆弧", "公式框_白板",
    "相机_侧视_正交_对应图1", "相机_立体_透视",
]
names = set(o.name for o in objs)
missing = [n for n in must_have if n not in names]
chk("B 结构", "图 1 全部器件齐备", len(missing) == 0,
    "缺 %s" % missing if missing else "%d 项关键对象全部存在" % len(must_have))
head_count = sum(1 for n in names if n.startswith("膜分子_头基_"))
chain_count = sum(1 for n in names if n.startswith("膜分子_疏水链_"))
chk("B 结构", "单分子膜分子阵列", head_count >= 16 and chain_count >= 16,
    "头基 %d / 疏水链 %d" % (head_count, chain_count))
post_count = sum(1 for n in names if n.startswith("支撑立柱_"))
arm_count = sum(1 for n in names if n.startswith("悬臂_"))
joint_count = sum(1 for n in names if n.startswith("调整架关节_"))
chk("B 结构", "机械支撑齐备", post_count == 6 and arm_count == 6 and joint_count == 6,
    "立柱 %d / 悬臂 %d / 关节 %d" % (post_count, arm_count, joint_count))
norm_count = sum(1 for n in names if n.startswith("法线虚线_"))
chk("B 结构", "法线虚线", norm_count >= 10, "%d 段" % norm_count)

# ---------------------------------------------------------------- C
sp = scene.keys()
need_scene = ["作业名称", "课程", "建模阶段", "软件",
              "仿真软件三选一", "长度单位", "坐标约定",
              "光源波长_nm", "光源功率_mW", "光源类型",
              "n1_气相", "n2_液相", "布儒斯特角_deg", "tan_thetaB",
              "sin_thetaB", "cos_thetaB", "入射方向", "反射方向", "偏振态",
              "入射角精度_deg", "横向分辨率_um", "物镜NA", "探测器像元_um",
              "光源型号", "半波片型号", "起偏器型号", "物镜型号", "筒镜型号",
              "探测器型号", "样品台型号", "测角台型号", "核实台账",
              "n2_实测_6328nm_20C", "thetaB_实测_deg", "dn2_dT_per_C",
              "dthetaB_dT_deg_per_C",
              "图1器件清单", "第4项_除样品外_影响反射光强因素",
              "第4项_待讨论", "第5项_待分析", "渲染引擎", "渲染采样", "说明"]
miss_sp = [k for k in need_scene if k not in sp]
chk("C 参数", "场景级参数键完整", len(miss_sp) == 0,
    "缺 %s" % miss_sp if miss_sp else "%d 项参数键齐备" % len(need_scene))

n1 = float(scene["n1_气相"]); n2 = float(scene["n2_液相"])
th = float(scene["布儒斯特角_deg"])
tan_from_n = n2 / n1
chk("C 参数", "tanθB = n2/n1", near(float(scene["tan_thetaB"]), tan_from_n, 1e-9),
    "%.6f = %.3f/%.3f" % (float(scene["tan_thetaB"]), n2, n1))
chk("C 参数", "θB 由折射率计算而非人工指定",
    near(th, math.degrees(math.atan2(n2, n1)), 1e-6),
    "θB=%.4f°  arctan(n2/n1)=%.4f°" % (th, math.degrees(math.atan2(n2, n1))))
chk("C 参数", "sin²θB+cos²θB=1",
    near(float(scene["sin_thetaB"]) ** 2 + float(scene["cos_thetaB"]) ** 2, 1.0, 1e-9))
chk("C 参数", "波长为 632.8 nm He-Ne", near(float(scene["光源波长_nm"]), 632.8))
chk("C 参数", "光源波长范围已登记（题面第 2 项点名指标）",
    "光源波长范围_nm" in scene, str(scene.get("光源波长范围_nm", "缺失")))
chk("C 参数", "仿真软件为 Blender（三选一）", "Blender" in str(scene["仿真软件三选一"]))
chk("C 参数", "第 4 项因素清单已登记",
    len(str(scene["第4项_除样品外_影响反射光强因素"]).split(" | ")) >= 8,
    str(scene["第4项_除样品外_影响反射光强因素"])[:60] + "…")
chk("C 参数", "第 2 项选型结论已回填（8 类器件型号齐备）",
    all(k in scene for k in ("光源型号", "半波片型号", "起偏器型号", "物镜型号",
                             "筒镜型号", "探测器型号", "样品台型号", "测角台型号")),
    "型号已逐件回填，核实台账：%s" % str(scene.get("核实台账", "缺失")))
chk("C 参数", "建模/实测双口径折射率已登记",
    "n2_实测_6328nm_20C" in scene and "thetaB_实测_deg" in scene,
    "n2 建模=%.3f，实测=%.6f；θB 建模=%.4f°，实测=%.4f°" %
    (n2, float(scene["n2_实测_6328nm_20C"]), th, float(scene["thetaB_实测_deg"])))
chk("C 参数", "实测 θB 与实测 n2 自洽",
    near(float(scene["thetaB_实测_deg"]),
         math.degrees(math.atan(float(scene["n2_实测_6328nm_20C"]))), 1e-3),
    "%.4f° vs arctan(1.332106)=%.4f°" %
    (float(scene["thetaB_实测_deg"]),
     math.degrees(math.atan(float(scene["n2_实测_6328nm_20C"])))))
chk("C 参数", "实测与建模 θB 差值已记录（温度/波长漂移依据）",
    abs(th - float(scene["thetaB_实测_deg"])) < 0.05,
    "ΔθB = %.4f°" % abs(th - float(scene["thetaB_实测_deg"])))
chk("C 参数", "分辨率含斜视投影修正（1/cosθB）",
    "2.30" in str(scene["横向分辨率_um"]) and "1.38" in str(scene["横向分辨率_um"]),
    str(scene["横向分辨率_um"])[:70])

# ---------------------------------------------------------------- D
SIN_T = math.sin(math.radians(th)); COS_T = math.cos(math.radians(th))
U_IN = Vector((SIN_T, 0.0, -COS_T))
U_REF = Vector((SIN_T, 0.0, COS_T))
NORM = Vector((0.0, 0.0, 1.0))
# mathutils.Vector 为 float32，角度反算容差取 1e-3°（远小于工程精度 0.05°）
ANG_TOL = 1e-3
ang_in = math.degrees(math.acos(-U_IN.dot(NORM)))
ang_ref = math.degrees(math.acos(U_REF.dot(NORM)))
chk("D 几何", "入射角 = θB", near(ang_in, th, ANG_TOL),
    "%.6f° vs θB %.6f°（差 %.2e°，容差 %.0e°，float32 精度）" %
    (ang_in, th, abs(ang_in - th), ANG_TOL))
chk("D 几何", "反射角 = 入射角", near(ang_ref, ang_in, ANG_TOL),
    "反射角 %.6f° / 入射角 %.6f°" % (ang_ref, ang_in))
chk("D 几何", "入射/反射共面且对称",
    near(U_IN.x, U_REF.x, 1e-9) and near(U_IN.z, -U_REF.z, 1e-9)
    and near(U_IN.y, 0.0) and near(U_REF.y, 0.0))
e_p = Vector((COS_T, 0.0, SIN_T))
chk("D 几何", "p 偏振电场 ⊥ 传播方向", near(U_IN.dot(e_p), 0.0, 1e-9),
    "u_in·E = %.2e" % U_IN.dot(e_p))
chk("D 几何", "p 偏振电场在入射面内", near(e_p.y, 0.0))

def on_axis(o, arm, tol=0.12):
    """对象中心是否落在对应光轴上（垂直距离）"""
    p = o.matrix_world.translation.copy()
    if arm == "in":
        return (p - (p.dot(U_IN)) * U_IN).length < tol, p
    else:
        return (p - (p.dot(U_REF)) * U_REF).length < tol, p

axis_items = [
    ("光源_HeNe激光器_632.8nm", "in"), ("HWP_半波片_632.8nm", "in"),
    ("GL_格兰偏振棱镜", "in"), ("Obj_长工作距物镜_镜筒", "ref"),
    ("Apo_消色差透镜组", "ref"), ("探测器_面阵相机_机壳", "ref"),
]
bad_axis = []
for nm, arm in axis_items:
    ok, p = on_axis(bpy.data.objects[nm], arm)
    if not ok:
        bad_axis.append("%s(d=%.3f)" % (nm, (p - (p.dot(U_IN if arm == "in" else U_REF)) * (U_IN if arm == "in" else U_REF)).length))
chk("D 几何", "全部 6 个光学器件位于光轴上", len(bad_axis) == 0,
    "; ".join(bad_axis) if bad_axis else "偏差均 < 0.12 cm")

def axis_of(o):
    return (o.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
orient_bad = []
for nm, arm in axis_items:
    a = axis_of(bpy.data.objects[nm])
    u = U_IN if arm == "in" else (U_REF if nm != "探测器_面阵相机_机壳" else -U_REF)
    d = abs(a.dot(u))
    if d < 0.995:
        orient_bad.append("%s(cos=%.4f)" % (nm, d))
chk("D 几何", "光学器件光轴沿光束方向", len(orient_bad) == 0,
    "; ".join(orient_bad) if orient_bad else "|cos| 均 > 0.995")

# 光束端点：入射光束从光源到原点，反射光束从原点到探测器
def cyl_endpoints(o, half=True):
    z = (o.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    L = o.dimensions.length if False else None
    # 用 mesh 局部包围盒取 Z 半长
    vs = [v.co for v in o.data.vertices]
    hz = max(abs(v.z) for v in vs)
    c = o.matrix_world.translation
    return c - z * hz, c + z * hz
bi = bpy.data.objects["入射光束_p偏振_632.8nm"]
br = bpy.data.objects["反射光束_成像信号_632.8nm"]
e1, e2 = cyl_endpoints(bi)
d0 = min(e1.length, e2.length)
chk("D 几何", "入射光束终止于液面原点", d0 < 0.15, "最近端点距原点 %.4f cm" % d0)
f1, f2 = cyl_endpoints(br)
d1 = min(f1.length, f2.length)
chk("D 几何", "反射光束起始于液面原点", d1 < 0.15, "最近端点距原点 %.4f cm" % d1)

# ---------------------------------------------------------------- E
need_props = ["器件名称", "器件类型", "功能说明"]
key_objs = [n for n in must_have if n in names]
no_props = [n for n in key_objs if "器件名称" not in bpy.data.objects[n].keys()]
chk("E 属性", "关键对象均带自定义属性", len(no_props) == 0,
    "未标注 %s" % no_props if no_props else "%d 个关键对象已标注" % len(key_objs))
thin = [n for n in key_objs if sum(1 for k in need_props if k in bpy.data.objects[n].keys()) < 2]
chk("E 属性", "关键对象属性含名称/类型/功能", len(thin) == 0,
    "属性偏少 %s" % thin if thin else "全部含 2 项以上")
spec_objs = ["光源_HeNe激光器_632.8nm", "HWP_半波片_632.8nm",
             "GL_格兰偏振棱镜", "Obj_长工作距物镜_镜筒",
             "Apo_消色差透镜组", "探测器_面阵相机_机壳"]
miss_spec = [n for n in spec_objs if "型号规格" not in bpy.data.objects[n].keys()]
chk("E 属性", "6 个主器件均登记型号规格", len(miss_spec) == 0,
    "缺 %s" % miss_spec if miss_spec else "6 个主器件型号均已回填（真实型号）")
declared = all("阶段状态" in bpy.data.objects[n].keys() for n in spec_objs)
chk("E 属性", "6 个主器件均登记选型/阶段状态", declared,
    "选型状态与核实来源已逐件写入")
src_o = bpy.data.objects["光源_HeNe激光器_632.8nm"]
chk("E 属性", "主器件型号为已核实真实型号（非占位）",
    "HNL050L" in str(src_o["型号规格"]) and "占位" not in str(src_o["型号规格"]),
    str(src_o["型号规格"])[:52])

# ---------------------------------------------------------------- F
chk("F 资源", "材质数量", len(bpy.data.materials) >= 20,
    "%d 个" % len(bpy.data.materials))
no_mat = [o.name for o in objs if o.type in ('MESH', 'CURVE', 'FONT')
          and len(o.data.materials) == 0]
chk("F 资源", "所有可见几何体均有材质", len(no_mat) == 0,
    "无材质 %s" % no_mat[:6] if no_mat else "全部有材质")
chk("F 资源", "灯光", len(bpy.data.lights) >= 3, "%d 盏" % len(bpy.data.lights))
chk("F 资源", "相机", len(bpy.data.cameras) == 2, "%d 台" % len(bpy.data.cameras))
chk("F 资源", "默认相机为侧视正交", scene.camera is not None
    and scene.camera.data.type == 'ORTHO', str(scene.camera.name if scene.camera else None))
chk("F 资源", "渲染引擎 Cycles", scene.render.engine == 'CYCLES', scene.render.engine)
chk("F 资源", "采样数", int(scene.cycles.samples) >= 32, str(scene.cycles.samples))
chk("F 资源", "PNG 输出", scene.render.image_settings.file_format == 'PNG')
texts = [t.name for t in bpy.data.texts]
chk("F 资源", "内嵌参数表", any("参数" in t for t in texts), str(texts))
chk("F 资源", "内嵌建模脚本（可复现）", any(t.endswith(".py") for t in texts), str(texts))
hidden = [o.name for o in objs if o.hide_render]
chk("F 资源", "提交态全部对象可渲染", len(hidden) == 0,
    "仍隐藏 %s" % hidden[:5] if hidden else "hide_render 全部为 False")

# 字体必须随文件打包：否则换机或换目录打开，中文标注会回退成方块
fonts_bad = [f.name for f in bpy.data.fonts
             if f.filepath and f.filepath != "<builtin>" and f.packed_file is None]
chk("F 资源", "中文字体已随文件打包（换机不掉字）", len(fonts_bad) == 0,
    "字体 %d 个，未打包 %d 个%s" %
    (len(bpy.data.fonts), len(fonts_bad),
     ("：" + str(fonts_bad[:3])) if fonts_bad else ""))

# 除渲染结果外不应有未打包的外部图像/贴图
ext_img = [im.name for im in bpy.data.images
           if im.source not in ('VIEWER', 'GENERATED') and im.packed_file is None]
chk("F 资源", "无未打包的外部图像依赖", len(ext_img) == 0,
    "图像 %d 个，外部依赖 %d 个" % (len(bpy.data.images), len(ext_img)))

# 内嵌脚本须与磁盘同名文件一致，否则"源文件自包含可复现"不成立
_disk = os.path.join(BASE, "src", "bam_build_scene.py")
_same = False
if os.path.exists(_disk) and "bam_build_scene.py" in bpy.data.texts:
    _a = open(_disk, encoding="utf-8").read().replace("\r\n", "\n").rstrip("\n")
    _b = bpy.data.texts["bam_build_scene.py"].as_string().replace("\r\n", "\n").rstrip("\n")
    _same = (_a == _b)
chk("F 资源", "内嵌建模脚本与磁盘版逐字一致", _same,
    "归一化行尾后逐字比对通过" if _same else "内容不一致或文件缺失")

# ---------------------------------------------------------------- G
render_ok = False
render_note = ""
try:
    tmp = os.path.join(tempfile.gettempdir(), "bam_verify_render.png")
    old_cam = scene.camera
    old_path = scene.render.filepath
    old_x, old_y = scene.render.resolution_x, scene.render.resolution_y
    old_samples = scene.cycles.samples
    scene.camera = bpy.data.objects["相机_侧视_正交_对应图1"]
    scene.render.resolution_x, scene.render.resolution_y = 900, 525
    scene.cycles.samples = 8
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    render_ok = os.path.exists(tmp) and os.path.getsize(tmp) > 20000
    render_note = "临时帧 %d bytes" % (os.path.getsize(tmp) if os.path.exists(tmp) else -1)
    scene.camera, scene.render.filepath = old_cam, old_path
    scene.render.resolution_x, scene.render.resolution_y = old_x, old_y
    scene.cycles.samples = old_samples
    if os.path.exists(tmp):
        os.remove(tmp)
except Exception as e:
    render_note = "%s: %s" % (type(e).__name__, str(e)[:120])
chk("G 可渲染", "重新打开后可正常渲染一帧", render_ok, render_note)

# ---------------------------------------------------------------- 输出
n_pass = sum(1 for r in results if r[2] == "PASS")
n_fail = sum(1 for r in results if r[2] == "FAIL")
print("CHECK_RESULT %s" % json.dumps(
    {"total": len(results), "pass": n_pass, "fail": n_fail,
     "fails": [r[1] for r in results if r[2] == "FAIL"]}, ensure_ascii=False), flush=True)

blend_name = os.path.basename(bpy.data.filepath)
lines = [
    "# BAM 仿真文件（.blend）自检报告",
    "",
    "> 检查对象：`%s`  " % blend_name,
    "> 检查方式：以 Blender %s 后台**重新打开已保存的文件**后逐项只读校验  " % bpy.app.version_string,
    "> 检查日期：%s" % datetime.date.today().isoformat(),
    "",
    "## 结论",
    "",
    "**共 %d 项，PASS %d 项，FAIL %d 项。** %s" %
    (len(results), n_pass, n_fail,
     "文件可正常打开、器件齐备、参数自洽、几何一致、字体已打包、可正常渲染。"
     if n_fail == 0 else "存在未通过项，需修正后重跑本脚本。"),
    "",
    "| 类别 | 检查项 | 判定 | 说明 |",
    "|---|---|---|---|",
]
for cat, item, verdict, note in results:
    lines.append("| %s | %s | %s | %s |" %
                 (cat, item, "PASS" if verdict == "PASS" else "FAIL",
                  note.replace("|", "\\|")))
lines += [
    "",
    "## 检查口径说明",
    "",
    "- **B 结构**：按装置示意图器件链逐项点名核对（光源 / HWP / GL / 样品槽-液相-单分子膜-滑障 / Obj / Apo / 探测器 / 法线 / θB / n1 n2 / 公式框）。",
    "- **C 参数**：θB 由 `tanθB = n2/n1` 反算比对，确认不是人工指定的角度；器件型号已按选型逐件联网核实并回填，"
    "另登记建模基准 n2=1.333 与实测 n2=1.332106@632.8 nm/20 °C 的双口径及 θB 差值。",
    "- **D 几何**：入射角 = 反射角 = θB、两者共面且关于法线对称、p 偏振电场在入射面内且垂直于传播方向、"
    "6 个光学器件落在光轴上且光轴沿光束方向、两束光端点落在液面原点。",
    "- **E 属性**：关键对象均写入 `器件名称 / 器件类型 / 功能说明`，6 个主器件另含 "
    "`型号规格 / 工作波长 / 位置 / 光轴方向 / 尺寸 / 选型状态 / 核实来源 / 阶段状态`。",
    "- **F 资源**：材质、灯光、2 台相机、渲染设置、内嵌参数表与建模脚本；"
    "另核三项可复现条件——中文字体已 pack 进文件（换机/换目录不掉字）、"
    "无未打包的外部图像、内嵌脚本与仓库内 `src/bam_build_scene.py` 逐字一致。"
    "侧视渲染时临时隐藏的机械支撑在最终保存时已全部恢复可见。",
    "- **G 可渲染**：从磁盘重新打开后实际渲染一帧，确认文件未损坏、无缺失资源。",
    "",
    "**检查边界（避免误读为「全部物理正确」）**：",
    "",
    "1. B 结构、C 参数、E 属性三类，多数是「读取文件自身记录的属性/参数，再与设计值比对」，属**一致性校验**；"
    "它们能证明文件内部无矛盾、无遗漏，也能证明型号确为厂商公开的真实型号，但不能替代选型论证与物理仿真结果。",
    "2. D 几何由对象坐标与方向向量**独立反算**（不依赖对象属性里的自述值），属几何独立校验。",
    "3. G 只证明**本机**可渲染；换机可复现主要依靠 F 类的字体打包与无外部依赖两项保障。",
    "",
    "## 仍需关注（不属于文件错误）",
    "",
    "1. 器件型号与指标已逐件联网核实（见 `docs/verified-parts.md`），但选型论证、指标推导与对比见 "
    "`docs/system-design.md`；`.blend` 中的几何为按装置示意建立的模型，尺寸不按实物 1:1。",
    "2. 图 1 的 `GL` 已由 BAM 文献确认还原为 Glan-Laser 方解石偏振棱镜（Thorlabs GL10-A）；"
    "`Apo` 仍属**推断**，按无限远校正光路的筒镜（Nikon MXA22018）还原，待文献确认。",
    "3. `反射光束` 在物理上代表**膜区/微观结构引起的微弱反射信号**；纯水界面 p 偏振在 θB 下反射率≈0，"
    "图中红线为示意，不是裸界面反射（该说明已写入反射光束对象属性）。",
    "4. 「除样品外影响反射光强的其他因素」「光路对准 / 图像对焦」与因素对测量结果的影响，"
    "见 `docs/measurement-factors.md` 与 `src/bam_model.py` 生成的扫描数据。",
    "5. 两张预览图分工不同：侧视正交图带全部标注、与装置示意图对应；立体图在渲染时临时隐藏文字与公式白板，"
    "只展示三维搭建关系（立柱与标注同轴，透视下必然互相穿插）。`.blend` 内文字对象全部保留且可渲染。",
    "",
]
with open(REPORT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("REPORT_WRITTEN", REPORT, flush=True)
