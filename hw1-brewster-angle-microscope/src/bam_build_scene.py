# -*- coding: utf-8 -*-
"""
大作业 1 · 布儒斯特角显微镜（BAM）完整光路建模脚本
在本机 Blender 5.2.2 LTS 中以 bpy 直接构建全部器件、机械支撑、标注与仿真参数。

运行（需 Blender 4.x/5.x，脚本只用 bpy）：
  blender -b --factory-startup --python src/bam_build_scene.py

输出：
  assets/bam_optical_path.blend        场景源文件（含内嵌参数表与本脚本）
  docs/images/preview_side.png         侧视正交预览（对应装置示意图）
  docs/images/preview_3d.png           立体透视预览

坐标约定：
  液面为 XY 平面（z = 0），法线 +Z；入射面为 XZ 平面（y = 0）；
  1 Blender Unit = 1 cm（scene.unit_settings.scale_length = 0.01）。
  θ_B = arctan(n2/n1)，入射方向 u_in = (sinθ, 0, -cosθ)，
  反射方向 u_ref = (sinθ, 0, +cosθ)。

本脚本只做光路搭建，不含物理计算与文档撰写（数值模型见 src/bam_model.py）。
"""
import bpy
import math
import json
import os
from mathutils import Vector

# ----------------------------------------------------------------------------
# 0. 物理与几何常量（建模基准；选型与核实结论见 docs/verified-parts.md）
# ----------------------------------------------------------------------------
LAMBDA_NM = 632.8          # He-Ne 激光器波长
LASER_POWER_MW = 5.0       # Thorlabs HNL050L 额定功率 (mW)
N1 = 1.000                 # 气相（空气，20 °C）
N2 = 1.333                 # 液相（水亚相，20 °C @ 632.8 nm）
THETA_B = math.atan2(N2, N1)          # 布儒斯特角（弧度）
THETA_DEG = math.degrees(THETA_B)
SIN_T = math.sin(THETA_B)
COS_T = math.cos(THETA_B)
U_IN = Vector((SIN_T, 0.0, -COS_T))   # 入射传播方向（指向液面原点）
U_REF = Vector((SIN_T, 0.0, COS_T))   # 反射传播方向（离开液面原点）
NORM = Vector((0.0, 0.0, 1.0))       # 界面法线
ORIGIN = Vector((0.0, 0.0, 0.0))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets")
FIG_DIR = os.path.join(ROOT, "docs", "images")
BLEND_PATH = os.path.join(OUT_DIR, "bam_optical_path.blend")
SIDE_PNG = os.path.join(FIG_DIR, "preview_side.png")
PERSP_PNG = os.path.join(FIG_DIR, "preview_3d.png")

# 中文字体：按平台顺序回退，找不到就用 Blender 内置字体（英文可显示，中文会缺字）
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), "")

# 光路各元件距液面原点的距离（cm）
D_SOURCE = 21.0
D_HWP = 15.5
D_GL = 11.0
D_OBJ = 9.0
D_APO = 14.0
D_DET = 21.5

# ----------------------------------------------------------------------------
# 1. 清空场景与基础设置
# ----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "BAM_布儒斯特角显微镜_光路仿真"
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01
scene.unit_settings.length_unit = 'CENTIMETERS'

# 集合分层
def new_coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

C_SRC = new_coll("01_光源与起偏臂")
C_SAM = new_coll("02_样品台与单分子膜")
C_IMG = new_coll("03_反射成像臂")
C_MEC = new_coll("04_机械支撑")
C_ANN = new_coll("05_标注与辅助")
C_RIG = new_coll("06_灯光与相机")

# ----------------------------------------------------------------------------
# 2. 材质
# ----------------------------------------------------------------------------
def _bsdf_input(bs, names, val):
    for n in names:
        if n in bs.inputs:
            bs.inputs[n].default_value = val
            return True
    return False

def make_mat(name, color, metallic=0.0, rough=0.4, transmission=0.0,
             ior=1.45, alpha=1.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    if bs is None:
        return m
    bs.inputs["Base Color"].default_value = (*color, 1.0)
    _bsdf_input(bs, ["Metallic"], metallic)
    _bsdf_input(bs, ["Roughness"], rough)
    _bsdf_input(bs, ["Transmission Weight", "Transmission"], transmission)
    _bsdf_input(bs, ["IOR"], ior)
    _bsdf_input(bs, ["Alpha"], alpha)
    if emit is not None:
        _bsdf_input(bs, ["Emission Color", "Emission"], (*emit, 1.0))
        _bsdf_input(bs, ["Emission Strength"], emit_strength)
    m.diffuse_color = (*color, alpha)
    return m

def make_emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    m.diffuse_color = (*color, 1.0)
    return m

BLUE = (0.075, 0.235, 0.60)      # 课程蓝 #1f5fbf 系
BLUE_DARK = (0.045, 0.13, 0.36)
ORANGE = (0.95, 0.45, 0.08)      # 课程橙
RED = (0.90, 0.09, 0.06)

M_METAL = make_mat("金属蓝_镜筒与机壳", BLUE, metallic=0.72, rough=0.30, ior=1.45)
M_METAL_D = make_mat("深蓝灰_底板与支架", BLUE_DARK, metallic=0.45, rough=0.52)
M_GLASS = make_mat("光学玻璃_BK7_n=1.5168", (0.30, 0.58, 0.88),
                   rough=0.045, transmission=0.72, ior=1.5168, alpha=1.0)
M_GLASS_POL = make_mat("偏振晶体_方解石_n≈1.658", (0.40, 0.66, 0.92),
                       rough=0.05, transmission=0.70, ior=1.658, alpha=1.0)
M_WATER = make_mat("亚相_水_n=1.333", (0.26, 0.58, 0.84),
                   rough=0.06, transmission=0.62, ior=N2, alpha=1.0)
M_SURF = make_mat("气液界面", (0.40, 0.68, 0.90), rough=0.08,
                  transmission=0.45, ior=N2, alpha=0.55)
M_PTFE = make_mat("PTFE_样品槽", (0.70, 0.73, 0.78), rough=0.72)
M_WHITE = make_mat("探测器靶面_白", (0.96, 0.96, 0.94), rough=0.55)
M_HEAD = make_mat("单分子膜_亲水头基", ORANGE, rough=0.34)
M_CHAIN = make_mat("单分子膜_疏水链", (0.15, 0.16, 0.19), rough=0.62)
M_BARRIER = make_mat("滑障_黑色", (0.08, 0.08, 0.10), rough=0.48)
M_FILM = make_mat("单分子膜区域_示意", (0.98, 0.66, 0.22), rough=0.5,
                  transmission=0.5, alpha=0.22, ior=1.45)
M_BEAM = make_emission("激光光束_632.8nm_红光", (1.0, 0.015, 0.010), 2.2)
M_BEAM_SOFT = make_emission("激光光束_柔光", (1.0, 0.10, 0.05), 1.0)
M_ARROW = make_mat("传播方向箭头", (0.98, 0.30, 0.10), rough=0.4)
M_NORM = make_mat("法线与角度标注", (0.10, 0.42, 0.85), rough=0.5)
M_TEXT = make_mat("标注文字_深蓝", (0.045, 0.13, 0.36), rough=0.7)
M_TEXT_W = make_mat("标注文字_深蓝_副", (0.045, 0.13, 0.36), rough=0.7)
M_PANEL = make_mat("公式框_白板", (0.985, 0.985, 0.98), rough=0.62)
M_POLMARK = make_mat("偏振方向标记", (0.05, 0.80, 0.45), rough=0.42)

# ----------------------------------------------------------------------------
# 3. 几何辅助函数
# ----------------------------------------------------------------------------
def _link(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj

def orient(obj, direction):
    obj.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()

def box(name, center, size, mat, coll, direction=None, rotate=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(center))
    o = bpy.context.object
    o.name = name
    o.dimensions = tuple(size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if direction is not None:
        orient(o, direction)
    if rotate is not None:
        o.rotation_euler = rotate
    o.data.materials.append(mat)
    return _link(o, coll)

def cyl(name, center, radius, depth, mat, coll, direction=None, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=tuple(center))
    o = bpy.context.object
    o.name = name
    if direction is not None:
        orient(o, direction)
    o.data.materials.append(mat)
    return _link(o, coll)

def sph(name, center, radius, mat, coll, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=radius, location=tuple(center))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return _link(o, coll)

def cone(name, center, r1, r2, depth, mat, coll, direction=None, vertices=20):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2,
                                    depth=depth, location=tuple(center))
    o = bpy.context.object
    o.name = name
    if direction is not None:
        orient(o, direction)
    o.data.materials.append(mat)
    return _link(o, coll)

def beam(name, p0, p1, radius, mat, coll, vertices=20):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    return cyl(name, (p0 + p1) * 0.5, radius, d.length, mat, coll,
               direction=d, vertices=vertices)

def tube(name, pts, bevel, mat, coll, cyclic=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = 8
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co[0], co[1], co[2], 1.0)
    sp.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, cu)
    coll.objects.link(o)
    o.data.materials.append(mat)
    return o

_FONT_CACHE = {}


def _get_font():
    """只加载一次中文字体，避免每个文本对象各建一份 datablock。"""
    if "f" in _FONT_CACHE:
        return _FONT_CACHE["f"]
    f = None
    if not FONT_PATH:
        print("WARN font: no CJK font found, fallback to Blender builtin", flush=True)
        _FONT_CACHE["f"] = None
        return None
    try:
        f = bpy.data.fonts.load(FONT_PATH)
    except Exception as e:
        print("WARN font load:", e)
    _FONT_CACHE["f"] = f
    return f


def text_obj(name, body, loc, size, mat, coll, rot=(math.pi / 2, 0, 0),
             align='CENTER', extrude=0.006):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.extrude = extrude
    cu.bevel_depth = 0.0
    fnt = _get_font()
    if fnt is not None:
        cu.font = fnt
    o = bpy.data.objects.new(name, cu)
    coll.objects.link(o)
    o.location = tuple(loc)
    o.rotation_euler = rot
    o.data.materials.append(mat)
    return o

def props(obj, **kw):
    for k, v in kw.items():
        obj[k] = v
    return obj

def pos_in(d):
    """入射臂上距原点 d 的位置"""
    return ORIGIN - d * U_IN

def pos_ref(d):
    """反射臂上距原点 d 的位置"""
    return ORIGIN + d * U_REF

# ----------------------------------------------------------------------------
# 4. 01 光源与起偏臂
# ----------------------------------------------------------------------------
p_src = pos_in(D_SOURCE)
src = cyl("光源_HeNe激光器_632.8nm", p_src, 1.30, 7.0, M_METAL, C_SRC,
          direction=U_IN)
props(src, 器件名称="He-Ne 激光器", 器件类型="光源",
      型号规格="Thorlabs HNL050L：632.8 nm / 5.0 mW / 线偏振 500:1 / TEM00>95% / Ø0.81 mm / 1.0 mrad / RMS 噪声 0.2% / 8h 漂移 ±2.5%",
      功能说明="提供单色线偏振入射光；题面第 4 项要求仿真以所选光源为基础",
      工作波长_nm=LAMBDA_NM, 功率_mW=LASER_POWER_MW,
      位置_cm="(%.3f, 0, %.3f)" % (p_src.x, p_src.z),
      光轴方向="(%.4f, 0, %.4f)" % (U_IN.x, U_IN.z),
      尺寸_cm="Φ2.6 × 7.0（示意；实物约 Ø25 × 400.6 mm）", 材料="金属镜筒",
      选型状态="已确认（第 2 项选型）", 核实来源="台账 #1 / Thorlabs HNL050L 官方目录",
      阶段状态="选型已回填")

win = cyl("光源_出射窗_发光", pos_in(D_SOURCE - 3.55), 0.80, 0.22,
          M_BEAM_SOFT, C_SRC, direction=U_IN)
props(win, 器件名称="激光器出射窗", 器件类型="光源附件",
      功能说明="出光孔径，光束起点", 出射波长_nm=LAMBDA_NM)

hwp = cyl("HWP_半波片_632.8nm", pos_in(D_HWP), 1.15, 0.32, M_GLASS, C_SRC,
          direction=U_IN)
props(hwp, 器件名称="HWP 半波片", 器件类型="偏振调节元件",
      型号规格="Thorlabs WPH05M-633：零级复合 λ/2 @633 nm / 晶体石英 / 精度 <λ/300 / 通光 Ø10 mm / 单面反射 <0.25%",
      功能说明="旋转线偏振方向；与 GL 配合确定入射光为 p 偏振（题面第 3 项）",
      工作波长_nm=LAMBDA_NM, 相位延迟="π",
      位置_cm="(%.3f, 0, %.3f)" % (pos_in(D_HWP).x, pos_in(D_HWP).z),
      光轴方向="(%.4f, 0, %.4f)" % (U_IN.x, U_IN.z),
      尺寸_cm="Φ2.3 × 0.32（示意）", 材料折射率=1.5168,
      选型状态="已确认（第 2 项选型）", 核实来源="台账 #2 / Thorlabs WPH05M-633 官方页",
      阶段状态="选型已回填")

hwp_ring = cyl("HWP_金属外框", pos_in(D_HWP), 1.32, 0.20, M_METAL_D, C_SRC,
               direction=U_IN)
props(hwp_ring, 器件名称="半波片调整架外框", 器件类型="机械件",
      功能说明="夹持并允许绕光轴旋转半波片")

# 偏振方向标记（p 偏振：电场在入射面 XZ 内，垂直于传播方向）
e_p = Vector((COS_T, 0.0, SIN_T))   # p 偏振电场方向（与 U_IN 正交，且点乘 U_IN = 0）
mark_c = pos_in(D_HWP - 0.55)
pol_mark = beam("HWP_p偏振方向标记_E矢量", mark_c - 0.85 * e_p,
                mark_c + 0.85 * e_p, 0.055, M_POLMARK, C_SRC, vertices=12)
props(pol_mark, 器件名称="p 偏振电场方向标记", 器件类型="示意标记",
      功能说明="E 矢量位于入射面内且垂直于传播方向，即 p(TM) 偏振；对应题面第 3 项",
      电场方向="(%.4f, 0, %.4f)" % (e_p.x, e_p.z))

gl = box("GL_格兰偏振棱镜", pos_in(D_GL), (2.05, 1.65, 1.65),
         M_GLASS_POL, C_SRC, direction=U_IN)
props(gl, 器件名称="GL 起偏器（图 1 缩写；BAM 文献 [5][6] 确认还原为 Glan-Laser 方解石偏振棱镜）",
      器件类型="起偏器",
      型号规格="Thorlabs GL10-A：Glan-Laser 方解石 / 通光 Ø10 mm / AR 350–700 nm / 消光比 100000:1 / 波前 λ/4 @633 nm / 损伤阈值 500 W/cm² CW",
      功能说明="输出高纯度线偏振光；与 HWP 组合把入射光确定为 p 偏振",
      工作波长_nm=LAMBDA_NM, 消光比="100000:1",
      位置_cm="(%.3f, 0, %.3f)" % (pos_in(D_GL).x, pos_in(D_GL).z),
      光轴方向="(%.4f, 0, %.4f)" % (U_IN.x, U_IN.z),
      尺寸_cm="2.05 × 1.65 × 1.65（示意）", 材料折射率="no≈1.658 / ne≈1.486",
      选型状态="已确认（缩写还原有文献支撑）", 核实来源="台账 #3、文献 [5][6] / Thorlabs GL10-A 官方页",
      阶段状态="选型已回填")

# 入射光束（含传播方向箭头）
beam_in_0 = pos_in(D_SOURCE - 3.7)
beam("入射光束_p偏振_632.8nm", beam_in_0, ORIGIN, 0.11, M_BEAM, C_SRC)
props(bpy.data.objects.get("入射光束_p偏振_632.8nm"),
      器件名称="入射光束", 器件类型="光路",
      功能说明="以布儒斯特角 θB 入射至气液界面",
      入射角_deg=round(THETA_DEG, 4), 波长_nm=LAMBDA_NM, 偏振态="p (TM)",
      方向="(%.5f, 0, %.5f)" % (U_IN.x, U_IN.z))
arr_in = cone("入射光_传播方向箭头", pos_in(6.2), 0.34, 0.0, 0.85,
              M_ARROW, C_SRC, direction=U_IN)
props(arr_in, 器件名称="入射光传播方向箭头", 器件类型="光路辅助标记",
      功能说明="标示入射光传播方向，对应图 1 红色箭头",
      方向="(%.5f, 0, %.5f)" % (U_IN.x, U_IN.z))

# ----------------------------------------------------------------------------
# 5. 02 样品台与单分子膜
# ----------------------------------------------------------------------------
# 槽底板与四壁
box("样品槽_底板_PTFE", (0, 0, -3.05), (22.0, 14.0, 0.30), M_PTFE, C_SAM)
box("样品槽_前壁_Y负", (0, -6.85, -1.55), (22.0, 0.30, 3.00), M_PTFE, C_SAM)
box("样品槽_后壁_Y正", (0, 6.85, -1.55), (22.0, 0.30, 3.00), M_PTFE, C_SAM)
box("样品槽_左壁_X负", (-10.85, 0, -1.55), (0.30, 13.4, 3.00), M_PTFE, C_SAM)
box("样品槽_右壁_X正", (10.85, 0, -1.55), (0.30, 13.4, 3.00), M_PTFE, C_SAM)
for nm in ("样品槽_底板_PTFE", "样品槽_前壁_Y负", "样品槽_后壁_Y正",
           "样品槽_左壁_X负", "样品槽_右壁_X正"):
    props(bpy.data.objects[nm], 器件名称="Langmuir 样品槽 / 样品台", 器件类型="样品台",
          型号规格="Biolin KSV NIMA Medium (KN 2002)：PTFE 273 cm² / 364×75×4 mm / 双滑障 0.1–270 mm/min / 0–300 mN/m / 0.1 µN/m / Wilhelmy 铂板 19.62×10 mm",
          功能说明="承载液相亚相与单分子膜；题面第 1 项点名的三组件之一",
          尺寸_cm="22 × 14 × 3", 材料="PTFE",
          选型状态="已确认（第 2 项选题）", 核实来源="台账 #7 / Biolin 官方技术规格页",
          阶段状态="选型已回填")

box("亚相_水_n2", (0, 0, -1.48), (21.2, 13.2, 2.90), M_WATER, C_SAM)
props(bpy.data.objects["亚相_水_n2"], 器件名称="液相亚相（水）", 器件类型="样品介质",
      功能说明="界面下侧介质 n2，与 n1 共同决定布儒斯特角",
      折射率_n2=N2, 温度_C=20.0, 尺寸_cm="21.2 × 13.2 × 2.9")

box("气液界面_n1_n2", (0, 0, 0.0), (21.2, 13.2, 0.06), M_SURF, C_SAM)
props(bpy.data.objects["气液界面_n1_n2"], 器件名称="气液界面", 器件类型="样品界面",
      功能说明="p 偏振以 θB 入射时平整界面反射率为零，靠膜层产生反射成像",
      上侧折射率_n1=N1, 下侧折射率_n2=N2,
      布儒斯特角_deg=round(THETA_DEG, 4),
      关系式="tan(thetaB) = n2 / n1")

# 气相区域（极淡示意，不遮挡）
box("气相_空气_n1", (0, 0, 4.2), (21.2, 13.2, 8.4),
    make_mat("气相_空气_极淡", (0.90, 0.95, 1.0), rough=0.2,
             transmission=0.96, ior=N1, alpha=0.06), C_SAM)
props(bpy.data.objects["气相_空气_n1"], 器件名称="气相（空气）", 器件类型="环境介质",
      功能说明="界面上侧介质 n1", 折射率_n1=N1)

# 单分子膜区域（Langmuir 膜）
box("单分子膜_覆盖区域_示意", (0, 0, 0.055), (12.6, 4.6, 0.02), M_FILM, C_SAM)
props(bpy.data.objects["单分子膜_覆盖区域_示意"], 器件名称="单分子膜覆盖区", 器件类型="样品",
      功能说明="题面第 4 项中「样品」即此膜层；本阶段仅建模，不分析",
      膜类型="Langmuir 单分子膜", 表面压="π(A) 或 π(t)", 面积变化="ΔA（由滑障压缩）")

# 分子阵列：亲水头基（橙色球）+ 疏水链（波浪曲线）
for row, y in enumerate((-1.55, 1.55)):
    for k in range(9):
        x = -6.0 + k * 1.5
        sph("膜分子_头基_r%d_c%d" % (row, k), (x, y, 0.16), 0.21,
            M_HEAD, C_SAM, segments=14, rings=8)
        pts = []
        for j in range(9):
            t = j / 8.0
            pts.append((x + 0.13 * math.sin(t * 2.6 * math.pi + k * 0.35),
                        y, 0.28 + t * 0.92))
        tube("膜分子_疏水链_r%d_c%d" % (row, k), pts, 0.045, M_CHAIN, C_SAM)
for o in C_SAM.objects:
    if o.name.startswith("膜分子_") and "器件名称" not in o.keys():
        props(o, 器件名称="单分子膜分子示意", 器件类型="样品微观结构",
              功能说明="亲水头基位于液面、疏水链伸向气相；对应图 1 红点与波浪线")

# 滑障 barrier 与 ΔA
bar = box("滑障_Barrier", (-8.1, 0, 0.34), (0.72, 13.2, 0.62), M_BARRIER, C_SAM)
props(bar, 器件名称="滑障（Barrier）", 器件类型="样品台附件",
      功能说明="沿 x 向移动压缩膜面积 ΔA，改变表面压 π(A)/π(t)",
      位置_cm_x=-8.1, 尺寸_cm="0.72 × 13.2 × 0.62", 材料="PTFE/黑化铝")
beam("ΔA_面积变化双箭头", (-8.1, 0, 1.35), (-6.2, 0, 1.35),
     0.055, M_ARROW, C_ANN, vertices=12)
cone("ΔA_箭头右", (-6.2, 0, 1.35), 0.20, 0.0, 0.42, M_ARROW, C_ANN,
     direction=(1, 0, 0))
cone("ΔA_箭头左", (-8.1, 0, 1.35), 0.20, 0.0, 0.42, M_ARROW, C_ANN,
     direction=(-1, 0, 0))

# ----------------------------------------------------------------------------
# 6. 03 反射成像臂
# ----------------------------------------------------------------------------
beam("反射光束_成像信号_632.8nm", ORIGIN, pos_ref(D_DET - 1.1),
     0.11, M_BEAM, C_IMG)
props(bpy.data.objects["反射光束_成像信号_632.8nm"],
      器件名称="反射光束（成像信号）", 器件类型="光路",
      功能说明="携带膜层信息的反射光（膜区信号示意）；纯水界面 p 偏振在 θB 下反射率≈0，"
              "成像靠膜层/微观结构引起的反射率变化，非平整裸界面反射",
      反射角_deg=round(THETA_DEG, 4), 波长_nm=LAMBDA_NM, 偏振态="p (TM)",
      方向="(%.5f, 0, %.5f)" % (U_REF.x, U_REF.z))
arr_ref = cone("反射光_传播方向箭头", pos_ref(5.0), 0.34, 0.0, 0.85,
               M_ARROW, C_IMG, direction=U_REF)
props(arr_ref, 器件名称="反射光传播方向箭头", 器件类型="光路辅助标记",
      功能说明="标示反射光传播方向，对应图 1 红色箭头",
      方向="(%.5f, 0, %.5f)" % (U_REF.x, U_REF.z))

obj_tube = cyl("Obj_长工作距物镜_镜筒", pos_ref(D_OBJ), 1.22, 4.20,
               M_METAL, C_IMG, direction=U_REF)
props(obj_tube, 器件名称="Obj 长工作距物镜", 器件类型="成像物镜",
      型号规格="Mitutoyo M Plan Apo 10X / 378-803-3：10× / NA 0.28 / WD 34.0 mm / f=20 mm / R=1.0 µm / 景深 3.5 µm / 436–656 nm / 无限远校正",
      功能说明="斜视收集反射光并对液面成像；题面第 4 项需讨论图像对焦",
      数值孔径_NA=0.28, 放大倍率="10×", 工作距离_mm=34.0,
      位置_cm="(%.3f, 0, %.3f)" % (pos_ref(D_OBJ).x, pos_ref(D_OBJ).z),
      光轴方向="(%.4f, 0, %.4f)" % (U_REF.x, U_REF.z),
      尺寸_cm="Φ2.44 × 4.20（示意）",
      选型状态="已确认（第 2 项选型）", 核实来源="台账 #4 / Mitutoyo 官方产品表",
      阶段状态="选型已回填")
obj_lens = cyl("Obj_物镜前透镜", pos_ref(D_OBJ - 2.12), 1.08, 0.30,
               M_GLASS, C_IMG, direction=U_REF)
props(obj_lens, 器件名称="物镜前组透镜", 器件类型="成像透镜",
      功能说明="收集反射光", 材料折射率=1.5168)

apo = cyl("Apo_消色差透镜组", pos_ref(D_APO), 1.24, 0.46,
          M_GLASS, C_IMG, direction=U_REF)
props(apo, 器件名称="Apo（图 1 缩写；按无限远光路还原为筒镜 / 复消色差镜组，仍属推断）",
      器件类型="成像透镜组 / 筒镜",
      型号规格="Nikon MXA22018 筒镜 f=200 mm（按 BAM 文献 [5][6] 实际搭建还原；图 1 未给全称）",
      功能说明="位于无限远校正物镜与相机之间，把平行输出会聚到靶面；属缩写还原推断",
      焦距_mm=200.0, 位置_cm="(%.3f, 0, %.3f)" % (pos_ref(D_APO).x, pos_ref(D_APO).z),
      光轴方向="(%.4f, 0, %.4f)" % (U_REF.x, U_REF.z),
      尺寸_cm="Φ2.48 × 0.46（示意）",
      选型状态="推断（文献 [5][6] 用 MXA22018 筒镜）", 核实来源="台账 #5、文献 [5][6]",
      阶段状态="按文献还原，仍属推断")
apo_ring = cyl("Apo_金属镜框", pos_ref(D_APO), 1.44, 0.20,
               M_METAL_D, C_IMG, direction=U_REF)
props(apo_ring, 器件名称="Apo 镜框", 器件类型="机械件", 功能说明="夹持透镜")

det_c = pos_ref(D_DET)
det = box("探测器_面阵相机_机壳", det_c, (4.2, 4.2, 2.20),
          M_METAL, C_IMG, direction=-U_REF)
props(det, 器件名称="探测器（CMOS 面阵相机）", 器件类型="探测器",
      型号规格="Basler acA2040-90um：2048×2048 / 5.5 µm / ams CMV4000 全局快门 / 90 fps / 10–12 bit / QE 62.07% / 暗噪声 13.8 e⁻ / 满阱 11.9 ke⁻ / DR 58.7 dB / USB3.0",
      功能说明="接收反射光并成像；题面第 1 项点名的三组件之一；第 4 项讨论图像对焦",
      像元尺寸_um=5.5, 靶面尺寸_mm="11.26 × 11.26",
      位置_cm="(%.3f, 0, %.3f)" % (det_c.x, det_c.z),
      光轴方向="(%.4f, 0, %.4f)" % (-U_REF.x, -U_REF.z),
      尺寸_cm="4.2 × 4.2 × 2.2（示意；实物 29.3×29×29 mm）",
      选型状态="已确认（第 2 项选型）", 核实来源="台账 #6 / Basler 官方产品页",
      阶段状态="选型已回填")
target = cyl("探测器_靶面", det_c - 1.16 * U_REF, 1.12, 0.12,
             M_WHITE, C_IMG, direction=-U_REF)
props(target, 器件名称="探测器靶面", 器件类型="探测器感光面",
      功能说明="图中蓝色方框内的白色圆形区域", 尺寸_cm="Φ2.24")

# ----------------------------------------------------------------------------
# 7. 04 机械支撑（面包板 + 立柱 + 悬臂）
# ----------------------------------------------------------------------------
board = box("光学底板_Breadboard", (0, 0, -3.62), (46.0, 24.0, 0.84),
            M_METAL_D, C_MEC)
props(board, 器件名称="光学底板 / 面包板", 器件类型="光机支撑",
      功能说明="承载全部光机部件；对应课程强调的光机集成",
      尺寸_cm="46 × 24 × 0.84", 顶面_z_cm=-3.20)

supports = [
    ("光源", D_SOURCE, p_src.z, C_SRC),
    ("HWP", D_HWP, pos_in(D_HWP).z, C_SRC),
    ("GL", D_GL, pos_in(D_GL).z, C_SRC),
    ("Obj", D_OBJ, pos_ref(D_OBJ).z, C_IMG),
    ("Apo", D_APO, pos_ref(D_APO).z, C_IMG),
    ("探测器", D_DET, det_c.z, C_IMG),
]
for tag, d, z, _c in supports:
    px = (-d * U_IN.x) if tag in ("光源", "HWP", "GL") else (d * U_REF.x)
    y_post = 9.6
    post = cyl("支撑立柱_%s" % tag, (px, y_post, (-3.20 + z) / 2.0),
               0.30, z + 3.20, M_METAL_D, C_MEC, vertices=20)
    props(post, 器件名称="支撑立柱_%s" % tag, 器件类型="光机支撑",
          功能说明="把光学元件抬升到工作高度，立柱置于槽外避免遮挡光路",
          高度_cm=round(z + 3.20, 3))
    arm = cyl("悬臂_%s" % tag, (px, y_post / 2.0, z), 0.19, 9.6,
              M_METAL_D, C_MEC, direction=(0, -1, 0), vertices=16)
    props(arm, 器件名称="水平悬臂_%s" % tag, 器件类型="光机支撑",
          功能说明="沿 +Y 从槽外立柱伸入到 y=0 光路平面")
    cradle = sph("调整架关节_%s" % tag, (px, 0, z), 0.42,
                 M_METAL, C_MEC, segments=14, rings=8)
    props(cradle, 器件名称="调整架关节_%s" % tag, 器件类型="光机支撑",
          功能说明="元件与悬臂的连接/角度调整节点；对应题面第 4 项光路对准")

# ----------------------------------------------------------------------------
# 8. 05 标注与辅助：法线、θB 圆弧、文字、公式框
# ----------------------------------------------------------------------------
# 法线（蓝色虚线）
for i in range(11):
    z0 = 0.35 + i * 0.62
    cyl("法线虚线_%02d" % i, (0, 0, z0 + 0.20), 0.045, 0.40,
        M_NORM, C_ANN, vertices=10)
props(bpy.data.objects["法线虚线_00"], 器件名称="界面法线（虚线）", 器件类型="几何辅助",
      功能说明="图 1 中蓝色竖直虚线；入射角、反射角均相对法线量取")

# θB 圆弧（从法线 90° 到反射光 90°-θB，位于法线右侧，与图 1 标注位置一致）
arc_pts = []
for i in range(25):
    a = math.radians(90.0 - THETA_DEG * i / 24.0)
    arc_pts.append((3.25 * math.cos(a), 0.0, 3.25 * math.sin(a)))
arc = tube("θB_角度圆弧", arc_pts, 0.045, M_NORM, C_ANN)
props(arc, 器件名称="布儒斯特角 θB 圆弧", 器件类型="几何标注",
      功能说明="标出反射光与法线夹角 θB（入射角 = 反射角 = θB）",
      角度_deg=round(THETA_DEG, 4))

# 文字标注
# 说明：全部文字统一放在 y = -6（相机一侧）的前层，
#       侧视正交投影位置不变，立体图中不会被后方立柱或槽壁穿插遮挡。
Y_TXT = -6.0
labels = [
    # 上方标注带（z≈16），彼此水平错开
    ("标注_光源", "光源  He-Ne 632.8 nm", (-16.8, Y_TXT, 16.4), 0.86, M_TEXT),
    ("标注_探测器", "探测器", (17.2, Y_TXT, 16.6), 0.86, M_TEXT),
    # 器件近旁短标签（避免长串互相压字）
    ("标注_HWP", "HWP 半波片", (-10.8, Y_TXT, 12.4), 0.78, M_TEXT),
    ("标注_GL", "GL 起偏器", (-8.8, Y_TXT, 8.9), 0.78, M_TEXT),
    ("标注_p偏振", "p 偏振 (TM)", (-13.8, Y_TXT, 6.3), 0.68, M_TEXT),
    ("标注_Obj", "Obj 物镜", (7.2, Y_TXT, 8.1), 0.80, M_TEXT),
    ("标注_Apo", "Apo", (11.2, Y_TXT, 10.7), 0.80, M_TEXT),
    # 中部几何与样品标注
    ("标注_θB", "θB", (1.30, Y_TXT, 3.30), 0.86, M_TEXT),
    ("标注_单分子膜", "单分子膜", (-3.0, Y_TXT, 1.55), 0.80, M_TEXT_W),
    ("标注_π", "π(A) 或 π(t)", (-9.9, Y_TXT, 3.2), 0.72, M_TEXT),
    ("标注_ΔA", "ΔA", (-7.0, Y_TXT, 1.95), 0.70, M_TEXT),
    # n1 / n2 置于槽壁之外的前层，液面上方为 n1、下方为 n2
    ("标注_n1", "n1 = %.3f" % N1, (10.6, -9.5, 3.40), 0.82, M_TEXT),
    ("标注_n2", "n2 = %.3f" % N2, (10.6, -9.5, -1.90), 0.82, M_TEXT_W),
    # 下方注释带
    ("标注_样品槽", "样品槽 / 样品台", (-6.0, Y_TXT, -4.65), 0.86, M_TEXT_W),
    ("标注_标题", "图 1  布儒斯特角显微镜（BAM）装置光路", (2.0, Y_TXT, -6.35),
     1.02, M_TEXT_W),
]
for nm, body, loc, sz, mat in labels:
    o = text_obj(nm, body, loc, sz, mat, C_ANN)
    props(o, 器件名称=nm.replace("标注_", "文字标注_"), 器件类型="文字标注",
          功能说明="复现图 1 标注，便于核对器件与光路")

# 公式框
panel = box("公式框_白板", (17.6, Y_TXT, 5.6), (8.6, 0.16, 2.75),
            M_PANEL, C_ANN)
props(panel, 器件名称="tanθB 公式框", 器件类型="文字标注载体",
      功能说明="复现图 1 右上角公式框")
for nm, body, z in (("公式_1", "tan(θB) = n2 / n1", 6.15),
                    ("公式_2", "θB = %.2f°" % THETA_DEG, 5.15)):
    o = text_obj(nm, body, (17.6, Y_TXT - 0.12, z), 0.80, M_TEXT, C_ANN)
    props(o, 器件名称=nm, 器件类型="公式文字",
          功能说明="布儒斯特角定义式；θB 由 n1、n2 计算而非人工指定")

# ----------------------------------------------------------------------------
# 9. 06 灯光与相机
# ----------------------------------------------------------------------------
world = bpy.data.worlds.new("世界环境_浅灰蓝")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.77, 0.84, 1.0)
bg.inputs["Strength"].default_value = 0.85

def area_light(name, loc, energy, size, target=(0, 0, 3)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    o = bpy.data.objects.new(name, data)
    C_RIG.objects.link(o)
    o.location = tuple(loc)
    orient(o, Vector(target) - Vector(loc))
    # AREA 灯默认发光朝 -Z，orient 使 -Z 指向 target 需要反转
    o.rotation_euler = (Vector(loc) - Vector(target)).to_track_quat('Z', 'Y').to_euler()
    return o

area_light("主光_左上", (-12, -18, 26), 1900, 22)
area_light("补光_右侧", (20, -14, 18), 1050, 18)
area_light("顶光_后方", (2, 14, 24), 850, 20)

def camera(name, loc, target, lens=None, ortho=None):
    data = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, data)
    C_RIG.objects.link(o)
    o.location = tuple(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    else:
        data.lens = lens
    return o

cam_side = camera("相机_侧视_正交_对应图1", (0, -40, 5.5), (0, 0, 5.5), ortho=48.0)
cam_persp = camera("相机_立体_透视", (3.5, -50, 15.5), (0, 0, 5.0), lens=35.0)
props(cam_side, 器件名称="侧视正交相机", 器件类型="渲染相机",
      功能说明="正投影复现图 1 装置示意图，用于核对器件与角度")
props(cam_persp, 器件名称="立体透视相机", 器件类型="渲染相机",
      功能说明="三维总览，体现完整光路与光机支撑")

scene.camera = cam_side

# ----------------------------------------------------------------------------
# 10. 场景级仿真参数（自定义属性）+ .blend 内嵌参数文本
# ----------------------------------------------------------------------------
scene_props = {
    "作业名称": "布儒斯特角显微镜系统（BAM）· 光路仿真",
    "课程": "仪器光学设计",
    "建模阶段": "整机光路搭建 + 选型回填完成；配套数值模型见 src/bam_model.py",
    "软件": "Blender %s" % bpy.app.version_string,
    "仿真软件三选一": "Blender（题面第 4 项：Zemax / Blender / VirtualLab 任选其一）",
    "长度单位": "1 Blender Unit = 1 cm；METRIC / scale_length = 0.01",
    "坐标约定": "液面 z=0，法线 +Z，入射面 XZ（y=0），原点为光斑中心",
    "光源波长_nm": LAMBDA_NM,
    "光源波长范围_nm": "632.8 nm 单线（HNL050L 无调谐；纵模间隔 435 MHz ≈ 0.00058 nm；改 543/659 nm 光源时 θB 变化约 0.07°）",
    "光源功率_mW": LASER_POWER_MW,
    "光源类型": "He-Ne 激光器，TEM00，线偏振",
    "光源型号": "Thorlabs HNL050L",
    "半波片型号": "Thorlabs WPH05M-633",
    "起偏器型号": "Thorlabs GL10-A (Glan-Laser calcite)",
    "物镜型号": "Mitutoyo M Plan Apo 10X / 378-803-3",
    "筒镜型号": "Nikon MXA22018 f=200 mm（图 1 的 Apo，推断）",
    "探测器型号": "Basler acA2040-90um",
    "样品台型号": "Biolin KSV NIMA Medium / KN 2002",
    "测角台型号": "Newport URS50BPP（分辨率 0.0014°）；HWP/GL 定向 Thorlabs PRM1Z8（25 arcsec）",
    "核实台账": "docs/verified-parts.md",
    "n1_气相": N1, "n2_液相": N2,
    "n2_实测_6328nm_20C": 1.332106,
    "thetaB_实测_deg": 53.1048,
    "dn2_dT_per_C": -9.2e-5,
    "dthetaB_dT_deg_per_C": -0.0019,
    "布儒斯特角_deg": THETA_DEG,
    "tan_thetaB": N2 / N1,
    "sin_thetaB": SIN_T, "cos_thetaB": COS_T,
    "入射方向": "(%.6f, 0, %.6f)" % (U_IN.x, U_IN.z),
    "反射方向": "(%.6f, 0, %.6f)" % (U_REF.x, U_REF.z),
    "偏振态": "p (TM)，电场在入射面内；由 GL 起偏 + HWP 调向确定",
    "入射角精度_deg": "±0.01（URS50BPP 分辨率 0.0014°；须按实测亚相 n2 与温度标定，见 docs/system-design.md）",
    "横向分辨率_um": "1.38（垂直入射面，Rayleigh 0.61λ/NA）/ 2.30（沿入射面，斜视投影 1/cosθB=1.667）；像元 0.55 µm 物面满足 Nyquist",
    "物镜NA": 0.28,
    "探测器像元_um": 5.5,
    "图1器件清单": "光源 / HWP / GL / 样品槽-液相-单分子膜-滑障 / Obj / Apo / 探测器 / 法线 / θB / n1 n2 / tanθB 公式",
    "第4项_除样品外_影响反射光强因素": [
        "偏振消光比与偏振纯度", "入射角偏差 Δθ", "波长稳定性与光谱宽度",
        "光束准直性与指向漂移", "液面毛细波与机械振动",
        "环境杂散光与背景", "光学元件表面反射与散射",
        "物镜数值孔径（收集立体角）", "探测器曝光/增益/噪声",
        "温度引起 n1、n2 漂移",
    ],
    "第4项_待讨论": ["光路对准", "图像对焦"],
    "第5项_待分析": "已完成：见 docs/measurement-factors.md 与 src/bam_model.py 生成的扫描数据",
    "渲染引擎": "CYCLES / CPU",
    "渲染采样": 48,
    "说明": "型号参数已按选型逐件联网核实并回填，核实台账见 docs/verified-parts.md；几何仍以教学基准 n2=1.333 建模。",
}
for k, v in scene_props.items():
    if isinstance(v, list):
        scene[k] = " | ".join(v)
    else:
        scene[k] = v

# 参数表写入 .blend 内嵌文本（打开即可查看）
param_lines = [
    "BAM 布儒斯特角显微镜 · 仿真参数与器件位姿表",
    "=" * 62,
    "软件: %s    单位: 1 BU = 1 cm" % bpy.app.version_string,
    "",
    "[物理参数]",
    "  波长 λ            = %.1f nm (He-Ne)" % LAMBDA_NM,
    "  波长范围           = 632.8 nm 单线（He-Ne 无调谐；若改用可调光源需重算 θB）",
    "  n1 (气相/空气)     = %.3f" % N1,
    "  n2 (液相/水)       = %.3f" % N2,
    "  tan(θB) = n2/n1    = %.6f" % (N2 / N1),
    "  θB (建模基准)      = %.4f°    (n2=1.333，教学常用值)" % THETA_DEG,
    "  n2 实测 @632.8nm/20°C = 1.332106  (Daimon & Masumura 2007, Appl.Opt.46:3811)",
    "  θB (实测修正)      = 53.1048°  (与建模基准差 0.0185°，须按亚相温度标定)",
    "  dn2/dT             = -9.2e-5 /°C ;  dθB/dT = -0.0019 °/°C",
    "  Rayleigh 分辨力     = 1.38 µm (⊥入射面) ; 2.30 µm (∥入射面, 1/cosθB)",
    "  sinθB / cosθB      = %.6f / %.6f" % (SIN_T, COS_T),
    "  入射方向 u_in       = (%.6f, 0, %.6f)" % (U_IN.x, U_IN.z),
    "  反射方向 u_ref      = (%.6f, 0, %.6f)" % (U_REF.x, U_REF.z),
    "  p 偏振电场方向      = (%.6f, 0, %.6f)" % (e_p.x, e_p.z),
    "  校验 u_in·N         = %.6f  (应为 -cosθB)" % U_IN.dot(NORM),
    "  校验 u_ref·N        = %.6f  (应为 +cosθB)" % U_REF.dot(NORM),
    "  校验 u_in·e_p       = %.2e  (应为 0)" % U_IN.dot(e_p),
    "",
    "[器件位姿]  d = 沿光轴到液面原点的距离 (cm)",
]
for tag, d in (("光源", D_SOURCE), ("HWP", D_HWP), ("GL", D_GL),
               ("Obj", D_OBJ), ("Apo", D_APO), ("探测器", D_DET)):
    if tag in ("光源", "HWP", "GL"):
        p = pos_in(d)
        arm = "入射臂"
    else:
        p = pos_ref(d)
        arm = "反射臂"
    param_lines.append("  %-8s %-6s d=%5.1f  (x,z)=(%8.3f, %7.3f)" %
                       (tag, arm, d, p.x, p.z))
param_lines += [
    "",
    "[题面第 4 项：除样品外影响反射光强的其他因素（本阶段仅登记参数）]",
] + ["  - " + s for s in scene_props["第4项_除样品外_影响反射光强因素"]]
param_lines += [
    "",
    "[范围] 整机光路 + 选型回填 + 自检；数值模型见 src/bam_model.py。",
    "[注意] 型号参数已逐件联网核实并回填，台账见 docs/verified-parts.md。",
    "[口径] 几何按教学基准 n2=1.333 (θB=53.1232°)；实测 n2=1.332106 对应 53.1048°，差 0.0185°，须按亚相温度重新标定。",
]
txt = bpy.data.texts.new("BAM_仿真参数与器件位姿表.txt")
txt.write("\n".join(param_lines))

# 兜底：为所有辅助/标注对象补齐自定义属性，确保全文件无遗漏
for o in list(bpy.data.objects):
    if "器件名称" not in o.keys():
        props(o, 器件名称=o.name, 器件类型="辅助几何 / 标注 / 支撑",
              功能说明="光路示意、机械支撑或文字标注的辅助对象")

# 把建模脚本本身也嵌入 .blend，保证源文件自包含、可复现
try:
    bpy.data.texts.load(os.path.abspath(__file__))
except Exception as e:
    print("WARN embed script:", e)

# ----------------------------------------------------------------------------
# 11. 渲染设置与保存
# ----------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.filepath = SIDE_PNG

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SAVED:", BLEND_PATH, flush=True)

# 侧视（对应图 1）：隐藏机械支撑，得到干净的装置示意图
# 注意：仅设置渲染可见性，对象完整保留在 .blend 中
mec_objs = list(C_MEC.objects)
for o in mec_objs:
    o.hide_render = True
scene.camera = cam_side
scene.render.resolution_x = 1800
scene.render.resolution_y = 1050
scene.render.filepath = SIDE_PNG
bpy.ops.render.render(write_still=True)
print("RENDER_SIDE_OK", flush=True)

# 立体总览：恢复机械支撑，展示完整光机结构
# 文字标注与公式白板在立体图中临时隐藏：立柱与标注同轴，透视下必然相互穿插；
# 标注由侧视正交图承担（主图对应图 1），立体图只负责展示三维搭建关系。
for o in mec_objs:
    o.hide_render = False
_ann_hidden = [o for o in bpy.data.objects
               if o.type == "FONT" or o.name.startswith("公式框")]
for o in _ann_hidden:
    o.hide_render = True
scene.camera = cam_persp
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.filepath = PERSP_PNG
bpy.ops.render.render(write_still=True)
print("RENDER_PERSP_OK", flush=True)

# 立体图渲染完毕，恢复标注可见（提交态要求全部对象可渲染）
for o in _ann_hidden:
    o.hide_render = False

# 字体打包：把中文字体数据写入 .blend，换机/换目录打开不会掉字
_packed = 0
for _f in bpy.data.fonts:
    if _f.filepath and _f.filepath != "<builtin>" and _f.packed_file is None:
        try:
            _f.pack()
            _packed += 1
            print("FONT_PACKED", _f.name, flush=True)
        except Exception as _e:
            print("WARN font pack:", _f.name, _e, flush=True)
print("FONT_PACK_TOTAL", _packed, "fonts", len(bpy.data.fonts), flush=True)

# 恢复默认相机为侧视、全部对象可见，再保存（提交文件保持器件齐全）
for o in mec_objs:
    o.hide_render = False
scene.camera = cam_side
scene.render.resolution_x = 1800
scene.render.resolution_y = 1050
scene.render.filepath = SIDE_PNG
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

summary = {
    "objects": len(bpy.data.objects),
    "collections": len(bpy.data.collections),
    "materials": len(bpy.data.materials),
    "lamps": len(bpy.data.lights),
    "cameras": len(bpy.data.cameras),
    "theta_deg": THETA_DEG,
    "blend": BLEND_PATH,
}
print("SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)
