# -*- coding: utf-8 -*-
"""渲染给水/排水平面图区域 + 各候选图块到 PNG"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
OUT = r"D:\cc-connect\cost-agent-poc\temp"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

def render(layout, fname, xlim=None, ylim=None, size=(16, 16)):
    fig = plt.figure(figsize=size)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend).draw_layout(layout, finalize=True)
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    fig.savefig(fname, dpi=110, facecolor="black")
    plt.close(fig)
    print("saved", fname)

# 给水平面图
render(msp, OUT + r"\view_jishui_plan.png", xlim=(-465, -330), ylim=(630, 900), size=(10, 20))
# 排水平面图
render(msp, OUT + r"\view_paishui_plan.png", xlim=(200, 335), ylim=(620, 880), size=(10, 20))

# 各图块单独渲染
import ezdxf.document
names = ["$lvtry$00000200", "$lvtry$00000179", "$lvtry$00000219", "$lvtry$00000191",
         "$lvtry$00000220", "$lvtry$00000193", "$lvtry$00000206", "$lvtry$00000171", "$lvtry$00000168",
         "_LV5", "gdshwdeh", "A$C177467FC", "TOILET", "M_E6", "M_E8", "WST13",
         "$GS001_0", "$GS004_0", "$GS010_0", "$GS011_0", "$GS012_0", "$GS020_0",
         "$VA001_1", "$VA011_1", "$QC035_1", "$DGFH",
         "$PS001_0", "$PS003_0", "$PS003_1", "$PS005_2", "$PS008_2", "$PS015_2", "$PS020_1", "$PS020_2"]
import re
for n in names:
    if n not in doc.blocks:
        print("skip", n); continue
    tmp = ezdxf.new()
    tb = tmp.blocks.new(name="TB")
    blk = doc.blocks.get(n)
    ok = 0
    for e in blk:
        try:
            tb.add_foreign_entity(e.copy())
            ok += 1
        except Exception:
            pass
    tmp.modelspace().add_blockref("TB", (0, 0))
    safe = re.sub(r"[^A-Za-z0-9_]", "_", n)
    try:
        fig = plt.figure(figsize=(4, 4))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(tmp)
        backend = MatplotlibBackend(ax)
        Frontend(ctx, backend).draw_layout(tmp.modelspace(), finalize=True)
        fig.savefig(OUT + f"\\blk_{safe}.png", dpi=100, facecolor="black")
        plt.close(fig)
        print(f"saved blk_{safe}.png ({ok} ents)")
    except Exception as ex:
        print("ERR", n, ex)
