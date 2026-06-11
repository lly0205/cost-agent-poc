# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
# type: (count_label, area m2, perim m, height m, piles)
caps = {
"CT1":  (17, 1.21, 4.42, 0.8, 1),
"CT2":  (12, 3.00, 8.00, 1.2, 2),
"CT2a": (8, 3.00, 8.00, 1.5, 2),
"CT2b": (2, 3.00, 8.00, 1.5, 2),
"CT2c": (2, 3.60, 8.80, 1.5, 2),
"CT3":  (22, 8.31, 11.54, 1.2, 3),
"CT3a": (1, 8.25, 11.50, 1.2, 3),
"CT4":  (8, 9.00, 12.00, 1.2, 4),
"CT4a": (8, 9.00, 12.00, 1.2, 4),
"CT5":  (12, 14.67, 15.32, 1.4, 5),
"CT5a": (6, 13.47, 14.98, 1.4, 5),
"CT6":  (10, 15.00, 16.00, 1.5, 6),
}
V = F = A = P = N = 0
pad = 0
for k, (n, a, p, h, np_) in caps.items():
    v = n*a*h
    f = n*p*h
    pa = n*(a + p*0.1 + 4*0.01)
    print(f"{k}: n={n} V={v:.1f} m3  F={f:.1f} m2  pad_area={pa:.1f} m2  piles={n*np_}")
    V += v; F += f; A += n*a; pad += pa; N += n*np_
print(f"\nTOTAL caps: V={V:.1f} m3, formwork(full h)={F:.1f} m2, plan area={A:.1f} m2, 垫层面积={pad:.1f} m2 (vol={pad*0.15:.1f} m3), piles={N}")

# caps in raft (polygon zone counts): CT1 2, CT2 13, CT3 24, CT3a 1, CT4 7, CT4a 7, CT5 12, CT5a 6, CT6 10
in_raft = {"CT1":2, "CT2":13, "CT3":24, "CT3a":1, "CT4":7, "CT4a":7, "CT5":12, "CT5a":6, "CT6":10}
A_in = sum(n*caps[k][1] for k, n in in_raft.items())
F_red = sum(n*caps[k][2]*0.6 for k, n in in_raft.items())
print(f"caps in raft: n={sum(in_raft.values())}, plan area={A_in:.1f} m2, formwork reduction(0.6m within raft)={F_red:.1f} m2")

raft_area = 4300.7
raft_pad = raft_area + 356.2*0.1
print(f"\nraft: V={raft_area*0.6:.1f} m3; pad area={raft_pad:.1f}, field pad area={raft_pad - A_in:.1f} m2 vol={(raft_pad-A_in)*0.15:.1f} m3")

# walls
walls = [("DWQ1", 200.1, 0.35, 6.22), ("DWQ1?300", 23.7, 0.30, 6.22), ("DWQ2", 106.7, 0.30, 4.52), ("DWQ3", 2.9, 0.30, 6.22), ("SCQ1", 45.6, 0.30, 4.52)]
WV = WF = 0
for nm, L, t, h in walls:
    v = L*t*h; f = 2*L*h
    print(f"{nm}: L={L} t={t} h={h} V={v:.1f} F={f:.1f}")
    WV += v; WF += f
print(f"walls total V={WV:.1f} m3 F={WF:.1f} m2")

# sump pits 7x 1.5x2.0 net, walls 0.3, depth 1.2, bottom 0.6
n = 7
wallv = ((1.5+0.3)+(2.0+0.3))*2*1.2*0.3
botv = (1.5+0.6)*(2.0+0.6)*0.6
fw = (1.5+2.0)*2*1.2
print(f"\nsump per pit: wall {wallv:.2f} + bottom {botv:.2f} = {wallv+botv:.2f} m3; total {n*(wallv+botv):.1f} m3; formwork inner {fw:.1f} -> total {n*fw:.1f} m2")

# slab
print(f"\nslab: 4516.3*0.18 = {4516.3*0.18:.1f} m3; 有梁板=板+梁肋 = {4516.3*0.18 + 301.6:.1f} m3")
print(f"有梁板模板 = 板底(4516.3-544.9) + 梁侧1746.4 + 梁底544.9 + 板边364.3*0.18 = {4516.3-544.9+1746.4+544.9+364.3*0.18:.1f} m2")
