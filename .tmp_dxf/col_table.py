# -*- coding: utf-8 -*-
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

n = 0
for e in msp.query("DIMENSION"):
    if e.dxf.layer == "柱尺寸标注" and n < 12:
        p = e.dxf.defpoint
        if -4840000 <= p.x <= -4691000 and -307472 <= p.y <= -223372:
            try:
                m = e.get_measurement()
            except Exception:
                m = None
            print(f"x={p.x:.0f} y={p.y:.0f} meas={m:.1f} text='{e.dxf.text}' dimlfac={e.dimstyle_attribs().get('dimlfac') if hasattr(e,'dimstyle_attribs') else '?'}")
            n += 1
