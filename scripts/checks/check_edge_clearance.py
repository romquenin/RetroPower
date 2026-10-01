#!/usr/bin/env python3
"""Verificateur de clearance cuivre <-> contour de la carte (Edge.Cuts).

Categorie de regle DRC completement absente de tous les autres check_*.py
de ce projet jusqu'ici (clearance pastille-pastille, trou-a-trou,
connectivite, courtyard, silkscreen -- mais jamais "distance au contour
de la carte"). Le DRC officiel de KiCad l'appelle `copper_edge_clearance`
et exige, dans la configuration de ce PCB, 0.5mm entre TOUT cuivre
(piste, via, pastille) et le contour Edge.Cuts.

Approche : on charge tous les segments/arcs de Edge.Cuts comme des
LineString shapely, et pour chaque piste/via/pastille en cuivre, on
calcule la distance minimale (bord a bord, pas centre a centre) a
n'importe quel segment du contour."""
import pcbnew
from shapely.geometry import Point, LineString, box
from shapely.affinity import rotate, translate

MIN_EDGE_CLEARANCE_MM = 0.5
RECT_SHAPES = {pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_TRAPEZOID,
               pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_CHAMFERED_RECT}

import sys
board = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "RetroPower_Compact_v3.kicad_pcb")

def to_mm(nm):
    return nm / 1e6

def pad_geom(p):
    pos = p.GetPosition()
    x, y = to_mm(pos.x), to_mm(pos.y)
    size = p.GetSize()
    w, h = to_mm(size.x), to_mm(size.y)
    if p.GetShape() in RECT_SHAPES:
        rect = box(-w / 2.0, -h / 2.0, w / 2.0, h / 2.0)
        angle_deg = p.GetOrientation().AsDegrees()
        rect = rotate(rect, angle_deg, origin=(0, 0))
        return translate(rect, x, y)
    r = max(w, h) / 2.0
    return Point(x, y).buffer(r)

# 1) contour Edge.Cuts -> liste de LineString
edge_lines = []
for dwg in board.GetDrawings():
    if dwg.GetLayerName() != "Edge.Cuts":
        continue
    cls = dwg.GetClass()
    if cls == "PCB_SHAPE":
        shape = dwg.GetShape()
        if shape == pcbnew.SHAPE_T_SEGMENT:
            s, e = dwg.GetStart(), dwg.GetEnd()
            edge_lines.append(LineString([(to_mm(s.x), to_mm(s.y)), (to_mm(e.x), to_mm(e.y))]))
        elif shape == pcbnew.SHAPE_T_RECT:
            s, e = dwg.GetStart(), dwg.GetEnd()
            x1, y1, x2, y2 = to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y)
            edge_lines.append(LineString([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]))
        else:
            # arc / cercle / polygone -- approxime via la polyline convertie par KiCad
            poly = dwg.GetPolyShape()
            for oc in range(poly.OutlineCount()):
                outline = poly.Outline(oc)
                pts = [(to_mm(outline.CPoint(i).x), to_mm(outline.CPoint(i).y))
                       for i in range(outline.PointCount())]
                if len(pts) >= 2:
                    edge_lines.append(LineString(pts))

assert edge_lines, "Aucun segment Edge.Cuts trouve !"

def dist_to_edge(geom):
    return min(geom.distance(line) for line in edge_lines)

violations = []

# 2) pastilles
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        g = pad_geom(p)
        d = dist_to_edge(g)
        if d < MIN_EDGE_CLEARANCE_MM:
            violations.append((d, f"Pastille {ref}.{p.GetPadName()} [{p.GetNetname()}]"))

# 3) pistes et vias
for t in board.GetTracks():
    net = t.GetNetname()
    cls = t.GetClass()
    if cls == "PCB_VIA":
        pos = t.GetPosition()
        r = to_mm(t.GetWidth()) / 2.0
        g = Point(to_mm(pos.x), to_mm(pos.y)).buffer(r)
        d = dist_to_edge(g)
        if d < MIN_EDGE_CLEARANCE_MM:
            violations.append((d, f"Via [{net}] @({to_mm(pos.x):.3f},{to_mm(pos.y):.3f})"))
    else:
        s, e = t.GetStart(), t.GetEnd()
        w = to_mm(t.GetWidth()) / 2.0
        g = LineString([(to_mm(s.x), to_mm(s.y)), (to_mm(e.x), to_mm(e.y))]).buffer(w)
        d = dist_to_edge(g)
        if d < MIN_EDGE_CLEARANCE_MM:
            violations.append((d, f"Piste [{net}] @({to_mm(s.x):.3f},{to_mm(s.y):.3f})->"
                                   f"({to_mm(e.x):.3f},{to_mm(e.y):.3f})"))

violations.sort()
print(f"Contour : {len(edge_lines)} segments Edge.Cuts, seuil = {MIN_EDGE_CLEARANCE_MM}mm")
print(f"{len(violations)} violation(s) copper_edge_clearance :")
for d, desc in violations:
    print(f"  {desc} : distance reelle {d:.4f}mm (< {MIN_EDGE_CLEARANCE_MM}mm)")
if not violations:
    print("  (aucune)")
