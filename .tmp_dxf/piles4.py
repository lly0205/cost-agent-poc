# -*- coding: utf-8 -*-
import ezdxf, sys, collections
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S4": (-223372, -139272), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None

# count pile-symbol INSERTs by bbox center, per sheet
cnt = collections.Counter()
pos = []
for e in msp.query("INSERT"):
    if e.dxf.name != "sdfsdfsdfsfdsf": continue
    ext = bbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (X0 <= cx <= X1): continue
    b = band(cy)
    cnt[b] += 1
    if b == "S2": pos.append((cx, cy))
print("pile-symbol INSERT count per sheet:", dict(cnt))

# dedupe overlapping piles (same position within 100mm)
pos.sort()
ded = []
for p in pos:
    if any(abs(p[0]-q[0]) < 100 and abs(p[1]-q[1]) < 100 for q in ded):
        continue
    ded.append(p)
print("S2 piles after position-dedupe:", len(ded))

# check big block 'dfgdfgdfgdgf' content for nested piles
blk = doc.blocks.get("dfgdfgdfgdgf")
inner = collections.Counter()
for e in blk:
    inner[(e.dxftype(), e.dxf.layer, e.dxf.name if e.dxftype()=="INSERT" else "")] += 1
print("\n=== block dfgdfgdfgdgf content ===")
for k, v in sorted(inner.items(), key=lambda kv: -kv[1])[:25]:
    print(" ", k, v)

# block definition of pile symbol
blk2 = doc.blocks.get("sdfsdfsdfsfdsf")
print("\n=== pile symbol block content ===")
for e in blk2:
    print(" ", e.dxftype(), e.dxf.layer)
