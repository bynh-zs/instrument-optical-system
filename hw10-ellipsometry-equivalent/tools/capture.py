# -*- coding: utf-8 -*-
"""软件界面截图采集（作业10 用）。

用法：
  python capture.py T01                -> 截全屏（去掉任务栏）
  python capture.py T01 x1 y1 x2 y2    -> 截取指定窗口/对话框区域
  python capture.py T01 x1 y1 x2 y2 "说明文字"

每次调用会保存：
  data/_build/_screen/raw_<tag>.png   原始全分辨率图（2560x1600）
  docs/screenshots/<tag>.png                      交付用裁剪图
并把一条记录追加到 data/_build/screenshot_index.json。
注意：运行前须先把 VirtualLab 窗口置于前台并保持窗口位置不变。
"""
import os
import sys
import json
from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 交付包根目录
BUILD = os.path.join(PKG, "data", "_build")
RAW = os.path.join(BUILD, "_screen")
SUB = os.path.join(PKG, "docs", "screenshots")
INDEX = os.path.join(BUILD, "screenshot_index.json")
os.makedirs(SUB, exist_ok=True)
os.makedirs(RAW, exist_ok=True)


def cap(tag, box=None, note=""):
    im = ImageGrab.grab(all_screens=True).convert("RGB")
    raw = os.path.join(RAW, "raw_%s.png" % tag)
    im.save(raw)
    view = im.crop(tuple(box)) if box else im.crop((0, 0, 2560, 1450))
    dst = os.path.join(SUB, tag + ".png")
    view.save(dst)
    idx = []
    if os.path.exists(INDEX):
        try:
            idx = json.load(open(INDEX, encoding="utf-8"))
        except Exception:
            idx = []
    idx.append({"tag": tag, "file": tag + ".png", "size": list(view.size),
                "crop": list(box) if box else [0, 0, 2560, 1450],
                "note": note or tag})
    json.dump(idx, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("%s -> %s  size=%s  raw=%s" % (tag, dst, view.size, raw))
    return dst


if __name__ == "__main__":
    a = sys.argv[1:]
    tag = a[0]
    if len(a) >= 5:
        box = [int(v) for v in a[1:5]]
        note = a[5] if len(a) > 5 else ""
    else:
        box = None
        note = a[1] if len(a) > 1 else ""
    cap(tag, box, note)
