#!/usr/bin/env python3
"""
Silkscreen and courtyard clean-up on the routed board, then DRC.

- the SMD parts sit UNDER the D1 mini on purpose: U1's full-body courtyard
  is replaced by two strips around its pin columns;
- USB-A silk shortened so it stops before the board edge;
- values hidden, references and labels placed where they do not touch pads.
"""
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = f"{HERE}/RetroPower_USB_Switch.kicad_pcb"
RPT = os.path.join(HERE, "build", "drc.rpt")
os.makedirs(os.path.dirname(RPT), exist_ok=True)
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))

b = pcbnew.LoadBoard(PCB)
bb = b.GetBoardEdgesBoundingBox()
W, H = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
fps = {f.GetReference(): f for f in b.GetFootprints()}


def text(s, x, y, size=1.0, rot=0, layer=pcbnew.F_SilkS, bold=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(V(size, size)); t.SetTextThickness(MM(size * (0.2 if bold else 0.15)))
    if rot:
        t.SetTextAngleDegrees(rot)
    b.Add(t)


def seg(x1, y1, x2, y2, layer=pcbnew.F_SilkS, w=0.12):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    s.SetLayer(layer); s.SetWidth(MM(w))
    b.Add(s)


def drop_graphics(fp, layers):
    for g in list(fp.GraphicalItems()):
        if isinstance(g, pcbnew.FP_SHAPE) and g.GetLayer() in layers:
            fp.Remove(g)


# ---- values off everywhere
for f in b.GetFootprints():
    f.Value().SetVisible(False)

# ---- USB-A: silk side lines stop 0.6 mm before the opening
for ref in ("J1", "J2", "J3", "J4", "J5", "J6"):
    f = fps[ref]
    for g in f.GraphicalItems():
        if isinstance(g, pcbnew.FP_SHAPE) and g.GetLayer() == pcbnew.F_SilkS:
            for getter, setter in ((g.GetStart0, g.SetStart0), (g.GetEnd0, g.SetEnd0)):
                p = getter()
                if abs(pcbnew.ToMM(p.y) - 11.55) < 0.01:
                    setter(pcbnew.VECTOR2I(p.x, MM(10.9)))
                elif abs(pcbnew.ToMM(p.y) + 0.2) < 0.01:
                    setter(pcbnew.VECTOR2I(p.x, MM(-1.0)))
            g.SetDrawCoord()
    f.Reference().SetVisible(False)

labels = {"J3": ("A1", "console 1"), "J4": ("B1", "console 1"),
          "J5": ("A2", "console 2"), "J6": ("B2", "console 2"),
          "J1": ("A", "disque"), "J2": ("B", "disque")}
for ref, (big, small) in labels.items():
    f = fps[ref]
    x = pcbnew.ToMM(f.GetPosition().x)
    top = f.GetOrientationDegrees() in (180, -180)
    yb, ys = (3.6, 6.4) if top else (H - 6.4, H - 3.6)
    text(big, x, yb, 1.6, bold=True)
    text(f"{ref} · {small}", x, ys, 0.9)

# ---- relays
for ref, lab in (("K1", "K1 D+/D-"), ("K2", "K2 5V")):
    f = fps[ref]
    f.Reference().SetVisible(False)
    x = pcbnew.ToMM(f.GetPosition().x) + 3.81
    text(lab, x, 25.2, 0.9, rot=90)

# ---- D1 mini: courtyard = two pin strips, own silk outline inside the board
U1 = fps["U1"]
drop_graphics(U1, (pcbnew.F_CrtYd, pcbnew.F_SilkS))
ux, uy = pcbnew.ToMM(U1.GetPosition().x), pcbnew.ToMM(U1.GetPosition().y)
for cx in (ux, ux + 22.86):
    r = pcbnew.FP_SHAPE(U1, pcbnew.SHAPE_T_RECT)
    r.SetLayer(pcbnew.F_CrtYd); r.SetWidth(MM(0.05))
    r.SetStart(V(cx - 1.3, uy - 1.1)); r.SetEnd(V(cx + 1.3, uy + 17.78 + 1.1))
    r.SetLocalCoord()
    U1.Add(r)
x0, x1 = ux - 1.37 + 0.15, min(ux + 24.23 - 0.15, W - 0.25)
y0, y1 = uy - 8.21 + 0.15, H - 0.25
for a in ((x0, y0, x1, y0), (x0, y0, x0, uy - 1.2), (x1, y0, x1, uy - 1.2),
          (x0, uy + 18.9, x0, y1), (x0, y1, ux + 7.5, y1), (ux + 15.4, y1, x1, y1)):
    seg(*a)
U1.Reference().SetVisible(False)
text("U1 · D1 mini", ux + 11.43, uy - 5.6, 1.0, bold=True)
text("antenne : pas de cuivre", ux + 11.43, uy - 3.6, 0.8)
text("micro-USB", ux + 11.43, H - 1.4, 0.8)
text("CMS : souder AVANT le D1 mini", ux + 11.43, uy + 19.7, 0.8)

# ---- SMD references next to their part
offs = {"D1": (0, -1.55), "D2": (0, -1.55), "D3": (0, 2.2), "D4": (0, 2.2),
        "Q1": (-2.3, 0), "Q2": (-2.3, 0), "R1": (0, -1.45), "R2": (0, 1.45),
        "R3": (0, -1.45), "R4": (0, 1.45), "C2": (0, 1.45), "C1": (-4.6, 0)}
for ref, (dx, dy) in offs.items():
    f = fps[ref]
    t = f.Reference()
    t.SetTextSize(V(0.8, 0.8)); t.SetTextThickness(MM(0.12))
    t.SetTextAngleDegrees(0)
    p = f.GetPosition()
    t.SetPosition(pcbnew.VECTOR2I(p.x + MM(dx), p.y + MM(dy)))

for ref in ("H1", "H2"):
    fps[ref].Reference().SetVisible(False)

# ---- title
text("RetroPower", 39.0, 26.6, 1.0, rot=90, bold=True)
text("USB Switch v1", 40.4, 26.6, 0.8, rot=90)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
pcbnew.WriteDRCReport(b, RPT, pcbnew.EDA_UNITS_MILLIMETRES, True)
print("saved; DRC ->", RPT)
