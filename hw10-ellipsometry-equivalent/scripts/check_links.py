# 检查文档里的图片与相对链接是否都存在
# 用法：python scripts/check_links.py [要检查的目录，默认本作业目录]
import os, re, sys

HW = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.abspath(HW)
bad = []
md_files = []
for root, dirs, files in os.walk(HW):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
    for f in files:
        if f.endswith(".md"):
            md_files.append(os.path.join(root, f))

for md in md_files:
    rel = os.path.relpath(md, HW)
    text = open(md, encoding="utf-8").read()
    # 图片
    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", text):
        p = m.group(1)
        if p.startswith("http"):
            continue
        tgt = os.path.normpath(os.path.join(os.path.dirname(md), p))
        if not os.path.exists(tgt):
            bad.append("%s -> image %s" % (rel, p))
    # 相对链接（非 http、非锚点）
    for m in re.finditer(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", text):
        p = m.group(1)
        if p.startswith("http") or p.startswith("#") or p.startswith("mailto:"):
            continue
        tgt = os.path.normpath(os.path.join(os.path.dirname(md), p))
        if not os.path.exists(tgt):
            bad.append("%s -> link %s" % (rel, p))

print("md files: %d" % len(md_files))
if bad:
    print("BAD")
    for b in bad:
        print("  " + b)
    sys.exit(1)
print("BAD none")
