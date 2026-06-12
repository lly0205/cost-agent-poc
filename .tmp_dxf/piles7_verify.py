# -*- coding: utf-8 -*-
# cross-verify pile count: spacing check + S2 vs S3 position match
import ezdxf, sys
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S2": (-55172, 28928), "S3": (-139272, -55172)}
def get(bn):
    y0, y1 = BANDS[bn]
    out = []
    for e in msp.query("INSERT"):
        if e.dxf.name != "sdfsdfsdfsfdsf": continue
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
        cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
        if X0 <= cx <= X1 and y0 <= cy <= y1:
            out.append((cx, cy))
    return out
s2 = get("S2"); s3 = get("S3")
print("S2:", len(s2), " S3:", len(s3))

# min spacing audit in S2 (pile 500x500, min 3D=1500 expected)
import math
pairs = []
s2s = sorted(s2)
for i in range(len(s2s)):
    for j in range(i+1, len(s2s)):
        if s2s[j][0]-s2s[i][0] > 1500: break
        d = math.dist(s2s[i], s2s[j])
        if d < 1400: pairs.append((d, s2s[i], s2s[j]))
pairs.sort()
print("pairs closer than 1400mm:", len(pairs))
for d, p, q in pairs[:10]:
    print(f"  d={d:.0f} at ({p[0]:.0f},{p[1]:.0f}) / ({q[0]:.0f},{q[1]:.0f})")

# S2 vs S3 alignment: anchor offset S3->S2 from memory anchors
# ANCH S3=(-4711895,-67087); S2 anchor unknown -> derive by best translation fit
# use median delta between matched sorted clouds: try offset = mean(s2)-mean(s3)
mx = sum(p[0] for p in s2)/len(s2) - sum(p[0] for p in s3)/len(s3)
my = sum(p[1] for p in s2)/len(s2) - sum(p[1] for p in s3)/len(s3)
print(f"centroid offset S3->S2: dx={mx:.0f} dy={my:.0f}")
s3t = [(p[0]+mx, p[1]+my) for p in s3]
unmatched2 = 0
for p in s2:
    if not any(abs(p[0]-q[0]) < 200 and abs(p[1]-q[1]) < 200 for q in s3t):
        unmatched2 += 1
unmatched3 = 0
for q in s3t:
    if not any(abs(p[0]-q[0]) < 200 and abs(p[1]-q[1]) < 200 for p in s2):
        unmatched3 += 1
print("S2 piles w/o S3 counterpart:", unmatched2, "| S3 piles w/o S2 counterpart:", unmatched3)
